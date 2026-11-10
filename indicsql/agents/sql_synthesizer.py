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
from indicsql.models.ollama_client import OllamaClient, prune_unrequested_temporal_filters
from indicsql.models.metric_guard import sanitize_metric_aggregations
from indicsql.schema.catalog import NDAPCatalog
from indicsql.schema.entity_grounder import dynamic_entity_grounder
from indicsql.schema.phonetic import transliterate_indic_to_latin

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
    """
    Extracts standardized uppercase entities from vernacular queries.
    Prioritizes DynamicEntityGrounder for pan-India relational integrity,
    falling back to static lexicons with strict word boundaries for short tokens.
    """
    entities: Dict[str, str] = {}

    # 1. Dynamic In-Memory Grounder First (Precise, relational integrity, word boundaries)
    try:
        dynamic_hints = dynamic_entity_grounder.ground_entities(raw_query)
        for k, v in dynamic_hints.items():
            if v:
                entities[k] = v
    except Exception as e:
        logger.debug(f"Dynamic grounding error: {e}")

    lower = raw_query.lower()

    # 2. Static Lexicon fallback (with word boundary check for short tokens <= 3 chars)
    if "state_name" not in entities:
        for keywords, state_name in _STATE_LEXICON:
            for k in keywords:
                if len(k) <= 3:
                    if re.search(r'\b' + re.escape(k) + r'\b', lower):
                        entities["state_name"] = state_name
                        break
                elif k in lower or k in raw_query:
                    entities["state_name"] = state_name
                    break
            if "state_name" in entities:
                break

    if "district_name" not in entities:
        for keywords, district_name in _DISTRICT_LEXICON:
            for k in keywords:
                if len(k) <= 3:
                    if re.search(r'\b' + re.escape(k) + r'\b', lower):
                        entities["district_name"] = district_name
                        break
                elif k in lower or k in raw_query:
                    entities["district_name"] = district_name
                    break
            if "district_name" in entities:
                break

    if "commodity" not in entities:
        for keywords, commodity in _COMMODITY_LEXICON:
            for k in keywords:
                if len(k) <= 3:
                    if re.search(r'\b' + re.escape(k) + r'\b', lower):
                        entities["commodity"] = commodity
                        break
                elif k in lower or k in raw_query:
                    entities["commodity"] = commodity
                    break
            if "commodity" in entities:
                break

    return entities


def _build_dynamic_fallback(
    table_name: str,
    table_schema: Dict[str, Any],
    entities: Dict[str, str],
    raw_query: str,
    matched_cols: Optional[List[str]] = None,
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
        where_clauses.append(f"crop_name = '{entities['commodity'].upper()}'")
    if "fertilizer_type" in cols and "commodity" in entities:
        where_clauses.append(f"fertilizer_type = '{entities['commodity'].upper()}'")
    if "commodity" in cols and "commodity" in entities:
        where_clauses.append(f"commodity = '{entities['commodity'].capitalize()}'")

    where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Find candidate numeric measure columns
    numeric_cols = [
        c for c, desc in cols.items()
        if any(t in desc.upper() for t in ["BIGINT", "DOUBLE", "INTEGER", "FLOAT"])
        and not c.endswith("_year")
        and not c.endswith("_id")
    ]

    # Check for top N / bottom N ranking
    top_match = re.search(r'\b(?:top|first|best|शीर्ष|सर्वोच्च)\s*(\d+)\b', lower)
    bottom_match = re.search(r'\b(?:bottom|lowest|least)\s*(\d+)\b', lower)
    if (top_match or bottom_match) and "district_name" in cols and numeric_cols:
        limit_n = int(top_match.group(1)) if top_match else int(bottom_match.group(1))
        order_dir = "DESC" if top_match else "ASC"
        target_measure = "farmer_beneficiaries" if table_name == "ndap_pm_kisan_disbursement" and "amount" not in lower else (
            next((c for c in (matched_cols or []) if c in numeric_cols), numeric_cols[0])
        )
        is_avg = "pct" in target_measure or "_rate" in target_measure
        func = "AVG" if is_avg else "SUM"
        alias = f"avg_{target_measure}" if is_avg else f"total_{target_measure}"
        return f"SELECT district_name, {func}({target_measure}) AS {alias} FROM {table_name}{where_str} GROUP BY district_name ORDER BY {alias} {order_dir} LIMIT {limit_n};"

    # Check for lowest / highest superlative in query with script boundaries
    lower = raw_query.lower()
    is_min = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in ['lowest', 'min', 'minimum', 'sabse kam']) or any(
        re.search(r'(?:^|[^\w\u0900-\u0D7F])' + re.escape(w) + r'(?:[^\w\u0900-\u0D7F]|$)', raw_query)
        for w in ['कम', 'குறைவாக', 'తక్కువ', 'అత్యల్పంగా', 'কম', 'कमी']
    )
    is_max = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in ['highest', 'max', 'maximum', 'sabse zyada']) or any(
        re.search(r'(?:^|[^\w\u0900-\u0D7F])' + re.escape(w) + r'(?:[^\w\u0900-\u0D7F]|$)', raw_query)
        for w in ['ज्यादा', 'सर्वाधिक', 'सर्वাধিক', 'अधिक', 'అత్యధిక']
    )

    if (is_min or is_max) and "district_name" in cols and numeric_cols:
        target_measure = next((c for c in (matched_cols or []) if c in numeric_cols), numeric_cols[0])
        order_dir = "ASC" if is_min else "DESC"
        return f"SELECT district_name, {target_measure} FROM {table_name}{where_str} ORDER BY {target_measure} {order_dir} LIMIT 1;"

    if numeric_cols:
        target_measure = next((c for c in (matched_cols or []) if c in numeric_cols), numeric_cols[0])
        is_avg = (
            "pct" in target_measure
            or "_rate" in target_measure
            or target_measure.startswith("rate_")
            or "price" in target_measure
            or "avg" in lower
            or "average" in lower
            or "औसत" in raw_query
            or "सरासरी" in raw_query
            or "சராசரி" in raw_query
            or "సగటు" in raw_query
            or "গড়" in raw_query
        )
        func = "AVG" if is_avg else "SUM"
        return f"SELECT {func}({target_measure}) AS total_metric FROM {table_name}{where_str};"

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

    matched_cols = [el.get("column_name") for el in state.get("pruned_schema", [])]

    # 1. Neural Generation via Ollama
    if _ollama_client.is_available:
        try:
            transliterated = transliterate_indic_to_latin(raw_query)
            effective_query = (
                f"{raw_query}\n(Phonetic Romanization: {transliterated})"
                if transliterated and transliterated != raw_query
                else raw_query
            )
            neural_sql = _ollama_client.generate_sql(
                query=effective_query,
                table_name=table_name,
                table_schema=table_schema,
                language=language,
                canonical_entities=mapped_entities,
                target_columns=matched_cols,
                error_feedback=error_feedback,
                previous_sql=previous_sql,
            )
            if neural_sql and ("SELECT" in neural_sql.upper() or "WITH" in neural_sql.upper()):
                logger.info("Successfully synthesized neural SQL via Ollama (%s)", _ollama_client.model_name)
                return neural_sql, f"ollama_{_ollama_client.model_name}", 0.94
        except Exception as e:
            logger.warning("Neural SQL synthesis error: %s", e)

    # 2. Dynamic Schema-Grounded Fallback
    matched_cols = [el.get("column_name") for el in state.get("pruned_schema", [])]
    fallback_sql = _build_dynamic_fallback(
        table_name, table_schema, entities, raw_query, matched_cols=matched_cols
    )
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

    # Final defense-in-depth: Ensure unrequested temporal filters are pruned and metrics are aligned
    raw_query = state.get("raw_query", "")
    target_table = state.get("target_database")
    raw_stochastic_draft = best_sql
    best_sql = prune_unrequested_temporal_filters(best_sql, raw_query, table_name=target_table)
    best_sql = sanitize_metric_aggregations(best_sql, raw_query, table_name=target_table)

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "generated_sql": best_sql,
        "raw_stochastic_sql": raw_stochastic_draft,
        "syntax_valid": True,
        "grounded_entities": extract_canonical_entities(raw_query),
        "audit_trace": current_trace,
    }


def _tot_select(state: IndicSQLState) -> Tuple[str, float, List[Dict[str, Any]], str]:
    """Helper for backwards-compatible model combo fallback."""
    sql, method, score = synthesize_sql(state)
    return sql, score, [{"sql": sql, "score": score}], method
