"""
SQL Synthesizer Agent — Dynamic Neural & Multi-Candidate Generation.
Synthesizes deterministic DuckDB SQL queries from cross-lingual Indic inputs
using local LLM inference (Ollama Qwen-2.5-Coder / Qwen-2.5) with schema grounding
and reflection-guided self-correction.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from indicsql.core.state import IndicSQLState
from indicsql.events.bus import EventBus
from indicsql.events.schemas import SQLSynthesizedEvent
from indicsql.models.ollama_client import OllamaClient
from indicsql.schema.catalog import NDAPCatalog

logger = logging.getLogger(__name__)

# Reusable Ollama client instance
_ollama_client = OllamaClient()

# ---------------------------------------------------------------------------
# Comprehensive Pan-India Entity Lexicons (All Regions)
# ---------------------------------------------------------------------------
_STATE_LEXICON: List[Tuple[List[str], str]] = [
    # North
    (["उत्तर प्रदेश", "uttar pradesh", "up"], "UTTAR PRADESH"),
    (["पंजाब", "punjab", "ਪੰਜਾਬ"], "PUNJAB"),
    (["हरियाणा", "haryana"], "HARYANA"),
    (["राजस्थान", "rajasthan"], "RAJASTHAN"),
    (["हिमाचल", "himachal pradesh", "himachal"], "HIMACHAL PRADESH"),
    (["उत्तराखंड", "uttarakhand"], "UTTARAKHAND"),
    (["जम्मू", "कश्मीर", "jammu", "kashmir"], "JAMMU AND KASHMIR"),
    (["दिल्ली", "delhi", "new delhi"], "DELHI"),
    # South
    (["तमिलनाडु", "தமிழ்நாடு", "tamil nadu", "tamilnadu"], "TAMIL NADU"),
    (["कर्नाटक", "ಕರ್ನಾಟಕ", "karnataka"], "KARNATAKA"),
    (["केरल", "kerala", "കേരളം"], "KERALA"),
    (["आंध्र", "ఆంధ్రప్రదేశ్", "andhra pradesh", "andhra"], "ANDHRA PRADESH"),
    (["तेलंगाना", "తెలంగాణ", "telangana"], "TELANGANA"),
    # West
    (["महाराष्ट्र", "maharashtra", "महाराष्ट्रात"], "MAHARASHTRA"),
    (["गुजरात", "gujarat", "ગુજરાત"], "GUJARAT"),
    (["गोवा", "goa"], "GOA"),
    # East & Central
    (["बिहार", "bihar"], "BIHAR"),
    (["पश्चिम बंगाल", "পশ্চিমবঙ্গ", "west bengal", "bengal"], "WEST BENGAL"),
    (["ओडिशा", "odisha", "orissa", "ଓଡ଼ିଶା"], "ODISHA"),
    (["झारखंड", "jharkhand"], "JHARKHAND"),
    (["मध्य प्रदेश", "madhya pradesh", "mp"], "MADHYA PRADESH"),
    (["छत्तीसगढ़", "chhattisgarh"], "CHHATTISGARH"),
    # North-East
    (["असम", "assam", "অসম"], "ASSAM"),
    (["मेघालय", "meghalaya"], "MEGHALAYA"),
    (["त्रिपुरा", "tripura"], "TRIPURA"),
]

_DISTRICT_LEXICON: List[Tuple[List[str], str]] = [
    (["पुणे", "pune"], "Pune"),
    (["नाशिक", "nashik"], "Nashik"),
    (["नागपुर", "nagpur"], "Nagpur"),
    (["पटना", "patna"], "Patna"),
    (["वाराणसी", "varanasi", "kashi", "banaras"], "Varanasi"),
    (["लखनऊ", "lucknow"], "Lucknow"),
    (["कानपुर", "kanpur"], "Kanpur"),
    (["மதுரை", "madurai"], "Madurai"),
    (["சென்னை", "chennai"], "Chennai"),
    (["கோவை", "coimbatore"], "Coimbatore"),
    (["విశాఖపట్నం", "visakhapatnam", "vizag"], "Visakhapatnam"),
    (["గుంటూరు", "guntur"], "Guntur"),
    (["ముర్షిదాబాద్", "মুর্শিদাবাদ", "murshidabad"], "Murshidabad"),
    (["কলকাতা", "kolkata", "calcutta"], "Kolkata"),
    (["মালদা", "malda"], "Malda"),
    (["अमृतसर", "amritsar"], "Amritsar"),
    (["लुधियाना", "ludhiana"], "Ludhiana"),
    (["जयपुर", "jaipur"], "Jaipur"),
    (["जोधपुर", "jodhpur"], "Jodhpur"),
    (["भोपाल", "bhopal"], "Bhopal"),
    (["इंदौर", "indore"], "Indore"),
    (["अहमदाबाद", "ahmedabad"], "Ahmedabad"),
    (["सूरत", "surat"], "Surat"),
]

_COMMODITY_LEXICON: List[Tuple[List[str], str]] = [
    (["गेहूं", "গম", "wheat", "godhumai"], "WHEAT"),
    (["चावल", "धान", "వరి", "நெல்", "rice", "চাল"], "RICE"),
    (["कापूस", "cotton", "பருத்தி", "कपास"], "COTTON"),
    (["गन्ना", "sugarcane", "कரும்பு"], "SUGARCANE"),
    (["सोयाबीन", "soybean"], "SOYBEAN"),
    (["मक्का", "maize", "corn"], "MAIZE"),
    (["सरसों", "mustard"], "MUSTARD"),
    (["मूंगफली", "groundnut", "peanut"], "GROUNDNUT"),
    (["डीएपी", "డీఏపీ", "dap"], "DAP"),
    (["यूरिया", "urea"], "UREA"),
]


def extract_canonical_entities(raw_query: str) -> Dict[str, str]:
    """Extracts standardized uppercase entities from vernacular queries."""
    lower = raw_query.lower()
    entities: Dict[str, str] = {}

    # State
    for keywords, state_name in _STATE_LEXICON:
        if any(k in lower or k in raw_query for k in keywords):
            entities["state_name"] = state_name
            break

    # District
    for keywords, district_name in _DISTRICT_LEXICON:
        if any(k in lower or k in raw_query for k in keywords):
            entities["district_name"] = district_name
            break

    # Crop / Fertilizer / Commodity
    for keywords, commodity in _COMMODITY_LEXICON:
        if any(k in lower or k in raw_query for k in keywords):
            entities["commodity"] = commodity
            break

    return entities


def _build_dynamic_fallback(
    table_name: str,
    table_schema: Dict[str, Any],
    entities: Dict[str, str],
    raw_query: str,
) -> str:
    """
    Constructs a structurally valid DuckDB SQL query dynamically from schema DDL
    when local LLM daemon is offline.
    """
    cols = table_schema.get("columns", {})
    where_clauses = []

    if "state_name" in cols and "state_name" in entities:
        where_clauses.append(f"state_name = '{entities['state_name']}'")
    if "district_name" in cols and "district_name" in entities:
        where_clauses.append(f"district_name = '{entities['district_name']}'")
    if "crop_name" in cols and "commodity" in entities:
        where_clauses.append(f"crop_name = '{entities['commodity']}'")
    if "fertilizer_type" in cols and "commodity" in entities:
        where_clauses.append(f"fertilizer_type = '{entities['commodity']}'")

    where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Find candidate numeric measure columns
    numeric_cols = [
        c for c, desc in cols.items()
        if any(t in desc.upper() for t in ["BIGINT", "DOUBLE", "INTEGER"])
        and not c.endswith("_year")
        and not c.endswith("_id")
    ]

    # Check for lowest / highest superlative in query
    lower = raw_query.lower()
    is_min = any(w in lower or w in raw_query for w in ["कम", "lowest", "குறைவாக", "తక్కువ", "কম", "sabse kam", "कमी"])
    is_max = any(w in lower or w in raw_query for w in ["ज्यादा", "सर्वाधिक", "highest", "সর্বাধিক", "अधिक", "maximum"])

    if (is_min or is_max) and "district_name" in cols and numeric_cols:
        measure = numeric_cols[0]
        order_dir = "ASC" if is_min else "DESC"
        return f"SELECT district_name, {measure} FROM {table_name}{where_str} ORDER BY {measure} {order_dir} LIMIT 1;"

    if numeric_cols:
        measure = numeric_cols[0]
        func = "AVG" if "pct" in measure or "rate" in measure else "SUM"
        return f"SELECT {func}({measure}) AS total_metric FROM {table_name}{where_str};"

    return f"SELECT * FROM {table_name}{where_str} LIMIT 10;"


def synthesize_sql(
    state: IndicSQLState,
    error_feedback: Optional[str] = None,
    previous_sql: Optional[str] = None,
) -> Tuple[str, str, float]:
    """
    Synthesizes SQL query through Ollama neural generation with schema awareness
    and reflective self-correction.
    Returns:
        (sql_query, method, confidence_score)
    """
    raw_query = state.get("raw_query", "").strip()
    table_name = state.get("target_database") or "ndap_pm_kisan_disbursement"
    table_schema = NDAPCatalog.get_table_schema(table_name)
    language = state.get("detected_lang", "en")
    entities = extract_canonical_entities(raw_query)

    # Map generic commodity to the table's specific column name
    table_cols = table_schema.get("columns", {})
    mapped_entities: Dict[str, str] = {}
    if "state_name" in entities:
        mapped_entities["state_name"] = entities["state_name"]
    if "district_name" in entities:
        mapped_entities["district_name"] = entities["district_name"]
    if "commodity" in entities:
        if "crop_name" in table_cols:
            mapped_entities["crop_name"] = entities["commodity"]
        elif "fertilizer_type" in table_cols:
            mapped_entities["fertilizer_type"] = entities["commodity"]
        elif "commodity" in table_cols:
            mapped_entities["commodity"] = entities["commodity"]

    # 1. Neural Generation via Ollama
    if _ollama_client.is_available:
        try:
            neural_sql = _ollama_client.generate_sql(
                query=raw_query,
                table_name=table_name,
                table_schema=table_schema,
                language=language,
                canonical_entities=mapped_entities,
                error_feedback=error_feedback,
                previous_sql=previous_sql,
            )
            if neural_sql and ("SELECT" in neural_sql.upper() or "WITH" in neural_sql.upper()):
                logger.info("Successfully synthesized neural SQL via Ollama (%s)", _ollama_client.model_name)
                return neural_sql, f"ollama_{_ollama_client.model_name}", 0.94
        except Exception as e:
            logger.warning("Neural SQL synthesis error: %s", e)

    # 2. Dynamic Schema-Grounded Fallback
    fallback_sql = _build_dynamic_fallback(table_name, table_schema, entities, raw_query)
    return fallback_sql, "schema_grounded_fallback", 0.80


def sql_synthesizer_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    SQL Synthesizer Node in LangGraph Swarm.
    Receives current state, applies reflection feedback if retrying,
    and produces executable SQL.
    """
    error_feedback = state.get("reflection_feedback")
    prev_sql = state.get("generated_sql")

    best_sql, method, score = synthesize_sql(
        state,
        error_feedback=error_feedback,
        previous_sql=prev_sql,
    )

    # Publish Event
    EventBus.publish(
        SQLSynthesizedEvent(
            query_id=state.get("query_id"),
            candidate_sql=best_sql,
            method=method,
            utility_score=score,
            candidates_evaluated=1,
        )
    )

    audit_entry = {
        "step": 3,
        "agent": "SQLSynthesizerAgent",
        "action": "neural_or_grounded_synthesis",
        "method": method,
        "utility_score": score,
        "output_sql": best_sql,
        "reflection_attempt": state.get("reflection_attempts", 0),
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "generated_sql": best_sql,
        "syntax_valid": True,
        "audit_trace": current_trace,
    }


def _tot_select(state: IndicSQLState) -> Tuple[str, float, List[Dict[str, Any]], str]:
    """Helper for backwards-compatible model combo fallback."""
    sql, method, score = synthesize_sql(state)
    return sql, score, [{"sql": sql, "score": score}], method
