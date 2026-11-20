"""
FastAPI Server Gateway for IndicSQL Swarm.
Exposes endpoints for natural language queries, schema inspection, and benchmark execution.
"""

import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from indicsql import __version__
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.models.sarvam_client import SarvamAPIError, SarvamClient
from indicsql.schema.catalog import NDAPCatalog
from indicsql.agents.verified_recommender import verified_alternative_queries
from indicsql.agents.sandbox_executor import _sandbox
from indicsql.sandbox.validator import validate_and_limit_sql

app = FastAPI(
    title="IndicSQL API Gateway",
    description="Cross-Lingual Text-to-SQL Swarm for Indian Languages (NDAP Benchmark)",
    version=__version__,
)

# Enable CORS for local frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question in Indic language or Hinglish")
    session_id: Optional[str] = Field(
        default=None, description="Optional persistent session identifier"
    )


class VerifiedSuggestion(BaseModel):
    query: str
    token: str
    table: str
    sample_row_count: int


class SuggestedExecutionRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=128)


_SUGGESTION_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_LOCK = threading.RLock()
_SANDBOX_LOCK = threading.RLock()
_SUGGESTION_TTL_SECONDS = 300


def _store_verified_suggestions(records: List[Dict[str, Any]]) -> List[VerifiedSuggestion]:
    now = time.monotonic()
    offered = []
    with _CACHE_LOCK:
        expired = [key for key, item in _SUGGESTION_CACHE.items() if item["expires"] <= now]
        for key in expired:
            _SUGGESTION_CACHE.pop(key, None)
        # Constrain cache growth in a long-running process.
        if len(_SUGGESTION_CACHE) > 500:
            _SUGGESTION_CACHE.clear()
        for item in records:
            token = secrets.token_urlsafe(24)
            _SUGGESTION_CACHE[token] = {**item, "expires": now + _SUGGESTION_TTL_SECONDS}
            offered.append(VerifiedSuggestion(
                query=item["query"], token=token,
                table=item["table"], sample_row_count=item["sample_row_count"],
            ))
    return offered


class QueryResponse(BaseModel):
    query_id: str
    raw_query: str
    detected_language: str
    detected_script: str
    generated_sql: str
    execution_status: Literal["success", "failed"]
    verbalized_response: str
    execution_error: Optional[str] = None
    suggested_queries: List[str] = Field(default_factory=list)
    verified_suggestions: List[VerifiedSuggestion] = Field(default_factory=list)
    applied_defaults: List[str] = Field(default_factory=list)
    raw_stochastic_sql: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    audit_trace: List[Dict[str, Any]] = Field(default_factory=list)


@app.get("/")
@app.get("/ui")
@app.get("/app")
def serve_frontend_ui():
    """Serves the interactive frontend web application matching the design mockup."""
    frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {
        "service": "IndicSQL Agent Swarm",
        "version": __version__,
        "status": "healthy",
        "supported_languages": ["hi", "bn", "ta", "te", "mr", "hi-en", "en"],
        "ui_url": "/ui",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/schemas")
def list_schemas():
    """Returns the list of available NDAP benchmark schemas."""
    tables = NDAPCatalog.list_tables()
    return {
        "count": len(tables),
        "tables": {t: NDAPCatalog.get_table_schema(t) for t in tables},
    }


@app.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    """
    Submits a natural language query through the multi-agent pipeline:
    Normalization -> Schema Linking -> SQL Synthesis -> AST Linter -> DuckDB Sandbox -> Verbalizer.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result_state = execute_indicsql_pipeline(
        request.query,
        interactive_defaults=True,
    )

    # Do not expose schema-only guesses as verified recommendations.
    verified = []
    schema_error = result_state.get("schema_linking_error") or result_state.get("schema_validation_error")
    error_text = str(result_state.get("execution_error") or "").casefold()
    if result_state.get("execution_result") is None and (
        schema_error or "binder error" in error_text or "catalog error" in error_text
    ):
        with _SANDBOX_LOCK:
            candidates = verified_alternative_queries(
                request.query,
                sandbox=_sandbox,
                language=result_state.get("detected_lang", "en"),
                preferred_table=result_state.get("target_database") or None,
                limit=5,
            )
        verified = _store_verified_suggestions(candidates)
    suggestions = [item.query for item in verified]

    return QueryResponse(
        query_id=result_state.get("query_id", ""),
        raw_query=result_state.get("raw_query", ""),
        detected_language=result_state.get("detected_lang", "unknown"),
        detected_script=result_state.get("detected_script", "unknown"),
        generated_sql=result_state.get("generated_sql", ""),
        execution_status=(
            "success" if result_state.get("execution_result") is not None else "failed"
        ),
        execution_error=result_state.get("execution_error"),
        suggested_queries=suggestions,
        verified_suggestions=verified,
        applied_defaults=result_state.get("applied_defaults", []),
        raw_stochastic_sql=result_state.get("raw_stochastic_sql", ""),
        verbalized_response=result_state.get("verbalized_response", ""),
        execution_result=result_state.get("execution_result"),
        audit_trace=result_state.get("audit_trace", []),
    )


@app.post("/suggestions/execute", response_model=QueryResponse)
def execute_verified_suggestion(request: SuggestedExecutionRequest):
    """Execute ONLY SQL previously generated and verified by this server.

    The client supplies a random reference, never SQL. An expired reference
    cannot trigger a query. The server rechecks actual database execution.
    """
    with _CACHE_LOCK:
        candidate = _SUGGESTION_CACHE.get(request.token)
        if candidate is None or candidate["expires"] <= time.monotonic():
            _SUGGESTION_CACHE.pop(request.token, None)
            raise HTTPException(status_code=410, detail="Suggestion expired; run the original question again.")
        candidate = dict(candidate)

    valid, safe_sql = validate_and_limit_sql(candidate["sql"], default_limit=25)
    if not valid:
        raise HTTPException(status_code=422, detail="Suggestion failed the SQL safety check.")
    # Generated SQL uses only cataloged identifiers, and was pre-executed.
    try:
        with _SANDBOX_LOCK:
            result = _sandbox.execute_query(safe_sql)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Suggestion is no longer executable against the database.") from exc
    if int(result.get("row_count", 0)) <= 0:
        raise HTTPException(status_code=409, detail="Suggestion no longer has available matching records.")

    count = result["row_count"]
    return QueryResponse(
        query_id="suggest-" + secrets.token_hex(6),
        raw_query=candidate["query"],
        detected_language="schema-grounded",
        detected_script="derived",
        generated_sql=safe_sql,
        execution_status="success",
        verbalized_response=(
            f"Verified database query returned {count} row(s) from "
            f"{candidate['table']}. Showing available {candidate['metric']} "
            f"values by {candidate['dimension']} (maximum 25 rows)."
        ),
        execution_result=result,
        audit_trace=[{
            "step": 1, "agent": "VerifiedAlternativeQuery",
            "action": "reexecuted_prevalidated_schema_query",
            "matched_table": candidate["table"],
            "row_count": count, "status": "success",
        }],
    )


class VoiceSynthesisRequest(BaseModel):
    text: str = Field(..., description="Vernacular text to synthesize into speech")
    language_code: str = Field(
        default="hi-IN",
        description="Target language BCP-47 code (e.g. hi-IN, mr-IN, bn-IN, ta-IN, te-IN)",
    )
    speaker: str = Field(default="meera", description="Speaker voice identifier")


@app.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes audio using Sarvam Saaras model with automatic language detection.
    """
    client = SarvamClient()
    if not client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Sarvam API is not configured. Please set SARVAM_API_KEY in your .env file.",
        )
    content = await file.read()
    try:
        return client.speech_to_text(content, filename=file.filename or "audio.wav")
    except SarvamAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/voice/synthesize")
def synthesize_speech(request: VoiceSynthesisRequest):
    """
    Synthesizes vernacular audio using Sarvam Bulbul model.
    """
    client = SarvamClient()
    if not client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Sarvam API is not configured. Please set SARVAM_API_KEY in your .env file.",
        )
    try:
        return client.text_to_speech(
            text=request.text,
            target_language_code=request.language_code,
            speaker=request.speaker,
        )
    except SarvamAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
