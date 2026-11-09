"""
FastAPI Server Gateway for IndicSQL Swarm.
Exposes endpoints for natural language queries, schema inspection, and benchmark execution.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pathlib import Path

from indicsql import __version__
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.models.sarvam_client import SarvamAPIError, SarvamClient
from indicsql.schema.catalog import NDAPCatalog

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


class QueryResponse(BaseModel):
    query_id: str
    raw_query: str
    detected_language: str
    detected_script: str
    generated_sql: str
    verbalized_response: str
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

    result_state = execute_indicsql_pipeline(request.query)

    return QueryResponse(
        query_id=result_state.get("query_id", ""),
        raw_query=result_state.get("raw_query", ""),
        detected_language=result_state.get("detected_lang", "unknown"),
        detected_script=result_state.get("detected_script", "unknown"),
        generated_sql=result_state.get("generated_sql", ""),
        verbalized_response=result_state.get("verbalized_response", ""),
        execution_result=result_state.get("execution_result"),
        audit_trace=result_state.get("audit_trace", []),
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
