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
from indicsql.models.interactive_query_policy import apply_interactive_query_defaults
from indicsql.models.metric_guard import sanitize_metric_aggregations
from indicsql.models.ollama_client import OllamaClient
from indicsql.models.temporal_guard import prune_unrequested_temporal_filters
from indicsql.sandbox.validator import repair_missing_foreign_key_join
from indicsql.schema.catalog import NDAPCatalog
from indicsql.schema.entity_grounder import dynamic_entity_grounder
from indicsql.schema.multilingual_index import NDAP_MULTILINGUAL_INDEX
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
    (["गेहूं", "गहू", "गव्हाचा", "গম", "wheat", "godhumai"], "WHEAT"),
    (["चावल", "धान", "వరి", "நெல்", "rice", "চাল"], "RICE"),
    (["कापूस", "कापसाचे", "cotton", "பருத்தி", "कपास"], "COTTON"),
    (["गन्ना", "ऊस", "sugarcane", "கరும்பு"], "SUGARCANE"),
    (["सोयाबीन", "soybean"], "SOYBEAN"),
    (["मक्का", "maize", "corn"], "MAIZE"),
    (["सरसों", "mustard"], "MUSTARD"),
    (["मूंगफली", "भुईमूग", "भुईमुगाचे", "groundnut", "peanut", "நிலக்கடலை"], "GROUNDNUT"),
    (["डीएपी", "డీఏపీ", "dap"], "DAP"),
    (["यूरिया", "युरिया", "ইউরিয়া", "யூரியா", "urea"], "UREA"),
    (["onion", "कांदा", "कांद", "प्याज", "পেঁয়াজ", "வெங்காயம்", "வெங்காய"], "ONION"),
    (["tomato", "टोमॅटो", "टमाटर"], "TOMATO"),
    (["potato", "आलू", "আলু"], "POTATO"),
    (["chilli", "chili", "मिरची", "మిర్చి"], "CHILLI"),
]

_SECTOR_LEXICON: List[Tuple[List[str], str]] = [
    (["agriculture", "कृषि क्षेत्र", "விவசாய திறன்", "কৃষি সংক্রান্ত"], "Agriculture"),
    (["automotive", "ऑटोमोटिव्ह"], "Automotive"),
    (["healthcare", "आरोग्य सेवा क्षेत्र", "स्वास्थ्य सेवा क्षेत्र"], "Healthcare"),
    (["it-ites", "it sector", "आईटी क्षेत्र", "ఐటీ రంగం"], "IT-ITeS"),
]

_EXPLICIT_METRIC_MARKERS = {
    "claim_amount_settled_inr": ("claim amount", "claim settled", "क्लेम रक्कम", "क्लेम राशि", "క్లెయిమ్", "సొమ్ము"),
    "women_mandays_pct": ("women's share", "women share", "women percentage", "பெண்களின் பங்கு", "சதவீதம்"),
    "doctors_at_phc": ("doctors", "doctors at phc", "వైద్యుల"),
    "requirement_tonnes": ("requirement", "आवश्यकता", "தேவை", "అవసరం"),
}


def extract_canonical_entities(raw_query: str) -> Dict[str, str]:
    """
    Extracts standardized uppercase entities from vernacular queries.
    Prioritizes DynamicEntityGrounder for pan-India relational integrity,
    falling back to static lexicons with strict word boundaries for short tokens.
    """
    entities: Dict[str, str] = {}
    lower = raw_query.lower()

    # 1. Dynamic In-Memory Grounder First (Precise, relational integrity, word boundaries)
    try:
        dynamic_hints = dynamic_entity_grounder.ground_entities(raw_query)
        for k, v in dynamic_hints.items():
            if v:
                entities[k] = v
    except Exception as e:
        logger.debug(f"Dynamic grounding error: {e}")

    # 2. Static Lexicon fallback (with word boundary check for short tokens <= 3 chars)
    for keywords, state_name in _STATE_LEXICON:
        if any(
            re.search(r'\b' + re.escape(k) + r'\b', lower)
            if k.isascii() and len(k) <= 3
            else k in lower or k in raw_query
            for k in keywords
        ):
            entities["state_name"] = state_name
            break

    # A fuzzy district guess must agree with an explicit state literal.
    district = entities.get("district_name")
    state = entities.get("state_name")
    if district and state and dynamic_entity_grounder.district_to_state.get(district) != state:
        entities.pop("district_name")

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

    # A literal commodity mention is stronger evidence than a fuzzy dynamic
    # match.  In particular, do not retain an inferred commodity when the
    # question explicitly says another one (for example ``onion``).
    for keywords, commodity in _COMMODITY_LEXICON:
        if any(
            re.search(r'\b' + re.escape(k) + r'\b', lower)
            if k.isascii()
            else k in raw_query
            for k in keywords
        ):
            entities["commodity"] = commodity
            break

    # A generic crop-production request must not inherit a commodity from
    # transliteration heuristics.  Filtering by a crop is valid only after an
    # explicit crop mention; otherwise it silently turns a total into a subset.
    generic_crop_markers = ("crop production", "पंटों का उत्पादन", "పంటల ఉత్పత్తి")
    if "commodity" in entities and any(marker in raw_query.casefold() for marker in generic_crop_markers):
        explicit_commodity = any(
            keyword in lower or keyword in raw_query
            for keywords, _ in _COMMODITY_LEXICON
            for keyword in keywords
        )
        if not explicit_commodity:
            entities.pop("commodity")

    if "sector_skill_council" not in entities:
        for keywords, sector in _SECTOR_LEXICON:
            if any(keyword in lower or keyword in raw_query for keyword in keywords):
                entities["sector_skill_council"] = sector
                break

    return entities


def _requested_time_grouping_column(raw_query: str, columns: Dict[str, Any]) -> Optional[str]:
    """Return a physical time dimension only when the question asks for a breakdown."""
    grouping_markers = (
        "by financial year",
        "by academic year",
        "by survey year",
        "by reporting year",
        "year-wise",
        "financial-year-wise",
        "वित्तीय वर्ष के अनुसार",
        "वित्तीय वर्षवार",
        "आर्थिक वर्षानुसार",
        "आर्थिक वर्ष के अनुसार",
        "financial year ke",
        "வருட வாரியாக",
        "நிதியாண்டு வாரியாக",
        "ఆర్థిక సంవత్సరం వారీగా",
        "ఆర్థిక సంవత్సరం ప్రకారం",
        "অর্থবছর অনুযায়ী",
        "অর্থবছর অনুসারে",
    )
    normalized = raw_query.casefold()
    if not any(marker in normalized for marker in grouping_markers):
        return None
    for column in (
        "financial_year",
        "academic_year",
        "survey_year",
        "reporting_year",
        "crop_year",
        "census_year",
        "cycle_year",
    ):
        if column in columns:
            return column
    return None


def _select_metric_column(
    numeric_columns: List[str],
    columns: Dict[str, Any],
    raw_query: str,
    matched_columns: Optional[List[str]],
) -> str:
    """Rank numeric columns using linker evidence and documented schema terms.

    The fallback must never choose a metric merely because it is physically the
    first numeric column in a table.  Linker evidence works for Indic-language
    terms; DDL descriptions provide an additional deterministic signal for
    English and Hinglish wording.
    """
    query_terms = set(re.findall(r"[a-z]{4,}", raw_query.casefold()))
    query_terms.update(re.findall(r"\b(?:tap|mmr|imr|phc|chc)\b", raw_query.casefold()))
    query_terms.update(term[:-1] for term in tuple(query_terms) if term.endswith("s"))
    query_terms.update(term[:-1] for term in tuple(query_terms) if term.endswith("ed"))
    def matched_index_evidence(column: str) -> int:
        """Return the strongest exact multilingual metric phrase for a column."""
        strongest = 0
        normalized_query = raw_query.casefold()
        for entry in NDAP_MULTILINGUAL_INDEX.values():
            if entry["column"] != column:
                continue
            for synonym in entry["synonyms"]:
                candidate = synonym.casefold()
                if not candidate or candidate not in normalized_query:
                    continue
                if candidate.isascii() and candidate.replace(" ", "").isalnum():
                    if not re.search(
                        rf"(?<![a-z0-9]){re.escape(candidate)}(?![a-z0-9])",
                        normalized_query,
                    ):
                        continue
                strongest = max(strongest, len(candidate))
        return strongest

    def score(column: str) -> tuple[int, int]:
        # Direct overlap with a metric's physical name/description is more
        # trustworthy than a generic programme synonym.  Linked-column order
        # is intentionally only a tie-breaker: generic "Ayushman", "PMGSY",
        # or "schools" evidence must not select cards, road length, or labs.
        value = 12 * matched_index_evidence(column)
        schema_text = f"{column} {columns[column]}".casefold()
        schema_terms = set(re.findall(r"[a-z]{4,}", schema_text))
        schema_terms.update(re.findall(r"\b(?:tap|mmr|imr|phc|chc)\b", schema_text))
        schema_terms.update(term[:-1] for term in tuple(schema_terms) if term.endswith("s"))
        schema_terms.update(term[:-1] for term in tuple(schema_terms) if term.endswith("ed"))
        value += 100 * len(query_terms & schema_terms)
        if any(marker in raw_query.casefold() for marker in _EXPLICIT_METRIC_MARKERS.get(column, ())):
            value += 10_000
        # Retain catalog order only as a stable final tie-breaker.
        return value, -numeric_columns.index(column)

    return max(numeric_columns, key=score)


def _is_rate_or_ratio_column(column: str, columns: Dict[str, Any]) -> bool:
    description = str(columns.get(column, "")).casefold()
    return (
        "pct" in column
        or "_rate" in column
        or "ratio" in column
        or "percentage" in description
        or " ratio" in description
        or " rate" in description
    )


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
    if "sector_skill_council" in cols and "sector_skill_council" in entities:
        where_clauses.append(
            f"sector_skill_council = '{entities['sector_skill_council']}'"
        )

    where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    lower = raw_query.lower()

    if table_name == "ndap_pm_kisan_disbursement":
        farmer_terms = (
            "farmer",
            "beneficiar",
            "शेतकर",
            "రైత",
            "কৃষক",
            "விவசாய",
        )
        amount_terms = ("amount", "disburs", "राशि", "रक्कम", "निध", "টাকা", "தொகை")
        farmer_count_phrases = ("कितने किसान", "किसानों को", "किसान लाभार्थी")
        asks_farmers = any(term in lower or term in raw_query for term in farmer_terms) or any(
            phrase in raw_query for phrase in farmer_count_phrases
        )
        asks_amount = any(term in lower or term in raw_query for term in amount_terms)
        if asks_farmers and asks_amount:
            return (
                "SELECT SUM(farmer_beneficiaries) AS total_farmers, "
                f"SUM(amount_inr) AS total_amount FROM {table_name}{where_str};"
            )
        if asks_amount and not asks_farmers:
            return f"SELECT SUM(amount_inr) AS total_amount FROM {table_name}{where_str};"
        return f"SELECT SUM(farmer_beneficiaries) AS total_farmers FROM {table_name}{where_str};"

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
        target_measure = "farmer_beneficiaries" if table_name == "ndap_pm_kisan_disbursement" and "amount" not in lower else _select_metric_column(
            numeric_cols, cols, raw_query, matched_cols
        )
        is_avg = _is_rate_or_ratio_column(target_measure, cols)
        if is_avg:
            return (
                f"SELECT district_name, {target_measure} FROM {table_name}{where_str} "
                f"ORDER BY {target_measure} {order_dir} LIMIT {limit_n};"
            )
        func = "AVG" if is_avg else "SUM"
        alias = f"avg_{target_measure}" if is_avg else f"total_{target_measure}"
        return f"SELECT district_name, {func}({target_measure}) AS {alias} FROM {table_name}{where_str} GROUP BY district_name ORDER BY {alias} {order_dir} LIMIT {limit_n};"

    # Check for lowest / highest superlative in query with script boundaries
    is_min = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in ['lowest', 'min', 'minimum', 'sabse kam']) or any(
        re.search(r'(?:^|[^\w\u0900-\u0D7F])' + re.escape(w) + r'(?:[^\w\u0900-\u0D7F]|$)', raw_query)
        for w in ['कम', 'किमान', 'குறைவாக', 'తక్కువ', 'అత్యల్పంగా', 'কম', 'कमी']
    )
    is_max = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in ['highest', 'max', 'maximum', 'sabse zyada']) or any(
        re.search(r'(?:^|[^\w\u0900-\u0D7F])' + re.escape(w) + r'(?:[^\w\u0900-\u0D7F]|$)', raw_query)
        for w in ['ज्यादा', 'अधिक', 'सर्वाधिक', 'सर्वात जास्त', 'সর্বাধিক', 'அதிக', 'அதிகமாக', 'அதிகபட்ச', 'అత్యధిక']
    )

    asks_district = any(
        marker in lower or marker in raw_query
        for marker in ("district", "जिले", "जिला", "जिल्ह", "জেলা", "மாவட்ட", "జిల్లా")
    )
    if (is_min or is_max) and asks_district and "district_name" in cols and numeric_cols:
        target_measure = _select_metric_column(numeric_cols, cols, raw_query, matched_cols)
        order_dir = "ASC" if is_min else "DESC"
        is_rate = _is_rate_or_ratio_column(target_measure, cols)
        if is_rate:
            return (
                f"SELECT district_name, {target_measure} FROM {table_name}{where_str} "
                f"ORDER BY {target_measure} {order_dir} LIMIT 1;"
            )
        func = "AVG" if is_rate else "SUM"
        alias = f"avg_{target_measure}" if is_rate else f"total_{target_measure}"
        return (
            f"SELECT district_name, {func}({target_measure}) AS {alias} FROM {table_name}{where_str} "
            f"GROUP BY district_name ORDER BY {alias} {order_dir} LIMIT 1;"
        )

    if numeric_cols:
        target_measure = _select_metric_column(numeric_cols, cols, raw_query, matched_cols)
        is_avg = (
            _is_rate_or_ratio_column(target_measure, cols)
            or "price" in target_measure
            or "avg" in lower
            or "average" in lower
            or "औसत" in raw_query
            or "सरासरी" in raw_query
            or "சராசரி" in raw_query
            or "సగటు" in raw_query
            or "গড়" in raw_query
        )
        if is_min:
            func = "MIN"
        elif is_max:
            func = "MAX"
        else:
            func = "AVG" if is_avg else "SUM"
        grouping_column = _requested_time_grouping_column(raw_query, cols)
        if grouping_column:
            return (
                f"SELECT {grouping_column}, {func}({target_measure}) AS total_metric "
                f"FROM {table_name}{where_str} GROUP BY {grouping_column} "
                f"ORDER BY {grouping_column} DESC;"
            )
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
    database_schema = state.get("database_schema")
    database_schema_name = state.get("database_schema_name")
    if database_schema:
        if not database_schema_name:
            raise ValueError("SQL synthesis requires the selected database schema name.")
        table_name = database_schema_name
        table_schema = database_schema
        table_cols = {
            column: description
            for table in database_schema.get("tables", {}).values()
            for column, description in table.get("columns", {}).items()
        }
    else:
        table_name = state.get("target_database") or state.get("target_table")
        if not table_name:
            raise ValueError("SQL synthesis requires a matched target database table.")
        table_schema = NDAPCatalog.get_table_schema(table_name)
        table_cols = table_schema.get("columns", {})
    language = state.get("detected_lang", "en")
    entities = extract_canonical_entities(raw_query)

    # Map generic commodity to the table's specific column name
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
    if "sector_skill_council" in entities and "sector_skill_council" in table_cols:
        mapped_entities["sector_skill_council"] = entities["sector_skill_council"]
    if database_schema:
        for entity, column_names in (
            ("state_name", ("state_name", "state")),
            ("district_name", ("district_name", "district")),
        ):
            canonical_value = mapped_entities.get(entity)
            if not canonical_value:
                continue
            for table in database_schema.get("tables", {}).values():
                examples = table.get("sample_values", {})
                stored_value = next(
                    (
                        value
                        for column in column_names
                        for value in examples.get(column, [])
                        if value.casefold() == canonical_value.casefold()
                    ),
                    None,
                )
                if stored_value:
                    mapped_entities[entity] = stored_value
                    break

    matched_cols = (
        []
        if database_schema
        else [
            el.get("column_name")
            for el in state.get("pruned_schema", [])
            if el.get("table_name") == table_name
        ]
    )

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
            if database_schema:
                raise RuntimeError(f"PostgreSQL SQL generation failed: {e}") from e

    if database_schema:
        raise RuntimeError(
            "The local SQL model is unavailable; no fallback is configured for PostgreSQL schemas."
        )

    # 2. Dynamic Schema-Grounded Fallback
    matched_cols = [
        el.get("column_name")
        for el in state.get("pruned_schema", [])
        if el.get("table_name") == table_name
    ]
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
    raw_stochastic_draft = best_sql
    schema_repairs: List[str] = []
    if state.get("database_schema"):
        best_sql, schema_repairs = repair_missing_foreign_key_join(
            best_sql, state["database_schema"]
        )
    raw_query = state.get("raw_query", "")

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
    if schema_repairs:
        audit_entry["raw_schema_sql"] = raw_stochastic_draft
        audit_entry["schema_repairs"] = schema_repairs

    # Final defense-in-depth: Ensure unrequested temporal filters are pruned and metrics are aligned
    applied_defaults: List[str] = []
    if not state.get("database_schema"):
        target_table = state.get("target_database")
        best_sql = prune_unrequested_temporal_filters(best_sql, raw_query, table_name=target_table)
        best_sql = sanitize_metric_aggregations(best_sql, raw_query, table_name=target_table)
        if state.get("interactive_defaults"):
            best_sql, applied_defaults = apply_interactive_query_defaults(
                best_sql, raw_query, target_table
            )

    if best_sql != audit_entry["output_sql"]:
        audit_entry["pre_policy_sql"] = audit_entry["output_sql"]
        audit_entry["output_sql"] = best_sql
    if applied_defaults:
        audit_entry["applied_defaults"] = applied_defaults

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "generated_sql": best_sql,
        "raw_stochastic_sql": raw_stochastic_draft,
        "schema_repairs": schema_repairs,
        "applied_defaults": applied_defaults,
        "syntax_valid": True,
        "grounded_entities": extract_canonical_entities(raw_query),
        "audit_trace": current_trace,
    }


def _tot_select(state: IndicSQLState) -> Tuple[str, float, List[Dict[str, Any]], str]:
    """Helper for backwards-compatible model combo fallback."""
    sql, method, score = synthesize_sql(state)
    return sql, score, [{"sql": sql, "score": score}], method
