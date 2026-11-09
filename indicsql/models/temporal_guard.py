"""
indicsql/models/temporal_guard.py
AST-Based Predicate-Level Temporal Intent Validator & Rewriter for IndicSQL.

Eliminates Flaw 3 (Temporal Filter Hallucination) by:
1. Extracting fine-grained multilingual temporal intent from citizen queries across 7 Indian languages.
2. Inspecting every SQL temporal predicate individually at AST level using SQLGlot.
3. Preserving explicitly requested years, academic/financial years, ranges, dates, and relative time expressions.
4. Stripping unrequested / hallucinated temporal predicates cleanly while preserving all non-temporal WHERE conditions.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import sqlglot
from sqlglot import exp

logger = logging.getLogger(__name__)

# Authoritative set of temporal column names across all NDAP & Relational tables
TEMPORAL_COLUMN_NAMES: Set[str] = {
    "financial_year",
    "crop_year",
    "year",
    "reporting_year",
    "academic_year",
    "survey_year",
    "census_year",
    "cycle_year",
    "arrival_date",
    "time_id",
}

# Table metadata mapping authoritative temporal columns and known dataset ranges
TABLE_TEMPORAL_METADATA: Dict[str, Dict[str, Any]] = {
    "ndap_pm_kisan_disbursement": {"col": "financial_year", "type": "financial_year", "latest": "2024-25", "previous": "2023-24", "years": [2021, 2022, 2023, 2024, 2025]},
    "ndap_crop_production_census": {"col": "crop_year", "type": "year", "latest": 2024, "previous": 2023, "years": [2021, 2022, 2023, 2024]},
    "ndap_fertilizer_distribution": {"col": "financial_year", "type": "financial_year", "latest": "2024-25", "previous": "2023-24", "years": [2021, 2022, 2023, 2024, 2025]},
    "ndap_soil_health_records": {"col": "cycle_year", "type": "year", "latest": 2024, "previous": 2023, "years": [2022, 2023, 2024]},
    "ndap_education_stats": {"col": "census_year", "type": "year", "latest": 2024, "previous": 2023, "years": [2022, 2023, 2024]},
    "ndap_school_infrastructure": {"col": "academic_year", "type": "academic_year", "latest": "2023-24", "previous": "2022-23", "years": [2022, 2023, 2024]},
    "ndap_higher_education_aishe": {"col": "survey_year", "type": "survey_year", "latest": "2023-24", "previous": "2022-23", "years": [2021, 2022, 2023, 2024]},
    "ndap_midday_meal_scheme": {"col": "financial_year", "type": "financial_year", "latest": "2022-23", "previous": "2021-22", "years": [2021, 2022, 2023]},
    "ndap_vocational_skill_training": {"col": "financial_year", "type": "financial_year", "latest": "2023-24", "previous": "2022-23", "years": [2022, 2023, 2024]},
    "ndap_rural_health_infrastructure": {"col": "reporting_year", "type": "year", "latest": 2024, "previous": 2023, "years": [2022, 2023, 2024]},
    "ndap_maternal_child_mortality": {"col": "survey_year", "type": "year", "latest": 2023, "previous": 2022, "years": [2021, 2022, 2023]},
    "ndap_ayushman_bharat_pmjay": {"col": "financial_year", "type": "financial_year", "latest": "2023-24", "previous": "2022-23", "years": [2022, 2023, 2024]},
    "ndap_national_tuberculosis_portal": {"col": "reporting_year", "type": "year", "latest": 2023, "previous": 2022, "years": [2022, 2023]},
    "mgnrega_state_annual_employment": {"col": "financial_year", "type": "financial_year", "latest": "2024-25", "previous": "2023-24", "years": [2021, 2022, 2023, 2024, 2025]},
    "ndap_pmgsy_rural_roads": {"col": "financial_year", "type": "financial_year", "latest": "2022-23", "previous": "2021-22", "years": [2021, 2022, 2023]},
    "ndap_pmay_rural_housing": {"col": "financial_year", "type": "financial_year", "latest": "2024-25", "previous": "2023-24", "years": [2021, 2022, 2023, 2024, 2025]},
    "ndap_gram_panchayat_finance": {"col": "financial_year", "type": "financial_year", "latest": "2023-24", "previous": "2022-23", "years": [2022, 2023, 2024]},
}


@dataclass
class TemporalIntent:
    """Represents fine-grained temporal constraints extracted from citizen query."""
    has_intent: bool = False
    years: Set[int] = field(default_factory=set)
    financial_years: Set[str] = field(default_factory=set)
    year_ranges: List[Tuple[int, int]] = field(default_factory=list)
    dates: Set[str] = field(default_factory=set)
    relative_type: Optional[str] = None  # 'latest', 'previous', 'current', 'last_n_years'
    last_n_years_count: Optional[int] = None
    is_cumulative: bool = False


def normalize_indic_digits(text: str) -> str:
    """Translates Devanagari, Bengali, Telugu, and Tamil script numerals to ASCII digits."""
    digit_maps = {
        # Devanagari (Hindi, Marathi)
        '०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
        # Bengali
        '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9',
        # Telugu
        '౦': '0', '౧': '1', '౨': '2', '౩': '3', '౪': '4', '౫': '5', '౬': '6', '౭': '7', '౮': '8', '౯': '9',
        # Tamil
        '௦': '0', '௧': '1', '௨': '2', '௩': '3', '௪': '4', '௫': '5', '௬': '6', '௭': '7', '௮': '8', '௯': '9',
        # Gujarati
        '૦': '0', '૧': '1', '૨': '2', '૩': '3', '૪': '4', '૫': '5', '૬': '6', '૭': '7', '૮': '8', '૯': '9',
        # Gurmukhi
        '੦': '0', '੧': '1', '੨': '2', '੩': '3', '੪': '4', '੫': '5', '੬': '6', '੭': '7', '੮': '8', '੯': '9',
        # Kannada
        '೦': '0', '೧': '1', '೨': '2', '೩': '3', '೪': '4', '೫': '5', '೬': '6', '೭': '7', '೮': '8', '೯': '9',
    }
    return "".join(digit_maps.get(c, c) for c in text)


def extract_temporal_intent(query: str) -> TemporalIntent:
    """
    Extracts structured temporal intent across English, Hinglish, Hindi, Marathi,
    Bengali, Tamil, and Telugu without falsely classifying scheme names (like '100 days work')
    or arbitrary numeric quantities as years.
    """
    if not query or not query.strip():
        return TemporalIntent()

    # Strip phonetic transliteration bridge if appended to query
    clean_q = query.split("\n")[0].strip()
    norm_q = normalize_indic_digits(clean_q)
    intent = TemporalIntent()

    # 1. Detect cumulative / lifetime intent keywords
    cumulative_patterns = [
        r'\b(?:total|cumulative|lifetime|all-time|overall|ever|overall\s+total)\b',
        r'कुल', r'समग्र', r'सुरुवातीपासून', r'एकूण', r'মোট', r'সর্বমোট',
        r'மொத்த', r'మొత్తం',
    ]
    if any(re.search(p, norm_q, re.IGNORECASE) for p in cumulative_patterns):
        intent.is_cumulative = True

    # 2. Specific calendar dates (YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY)
    for m in re.finditer(r'\b((?:19|20)\d{2}[-/]\d{2}[-/]\d{2})\b', norm_q):
        val = m.group(1).replace('/', '-')
        intent.dates.add(val)
    for m in re.finditer(r'\b(\d{2}[-/]\d{2}[-/](?:19|20)\d{2})\b', norm_q):
        parts = re.split(r'[-/]', m.group(1))
        intent.dates.add(f"{parts[2]}-{parts[1]}-{parts[0]}")

    # 3. Financial & Academic Years (e.g., 2023-24, 2022-2023, FY23, FY 2023)
    for m in re.finditer(r'\b((?:19|20)\d{2}[-/]\d{2,4})\b', norm_q):
        raw_fy = m.group(1).replace('/', '-')
        parts = raw_fy.split('-')
        start_y = int(parts[0])
        end_part = parts[1]
        if len(end_part) == 4:
            end_short = end_part[2:]
        else:
            end_short = end_part
        std_fy = f"{start_y}-{end_short}"
        intent.financial_years.add(std_fy)
        intent.years.add(start_y)
        if len(end_part) == 4:
            intent.years.add(int(end_part))
        elif len(end_part) == 2:
            intent.years.add(int(str(start_y)[:2] + end_part))

    for m in re.finditer(r'\bFY\s*[-/]?\s*(20\d{2}|\d{2})\b', norm_q, re.IGNORECASE):
        y_str = m.group(1)
        y_int = 2000 + int(y_str) if len(y_str) == 2 else int(y_str)
        intent.years.add(y_int)
        intent.financial_years.add(f"{y_int - 1}-{str(y_int)[2:]}")

    # 4. Explicit Year Ranges (e.g. 2020 to 2022, 2020-2022, 2020 se 2022, 2020 theke 2022)
    range_regex = r'\b((?:19|20)\d{2})\s*(?:to|-|se|tak|uthun|theke|lerundhu|nunchi|varai|వరకు|నుండి|থেকে|ते|पासून)\s*((?:19|20)\d{2})\b'
    for m in re.finditer(range_regex, norm_q, re.IGNORECASE):
        y1, y2 = int(m.group(1)), int(m.group(2))
        if y1 > y2:
            y1, y2 = y2, y1
        intent.year_ranges.append((y1, y2))
        for yr in range(y1, y2 + 1):
            intent.years.add(yr)

    # 5. Explicit 4-digit years (1900 - 2099)
    # Guard: Avoid numbers that are part of scheme names (e.g. MGNREGA 100 days)
    for m in re.finditer(r'\b((?:19|20)\d{2})\b', norm_q):
        val = int(m.group(1))
        # Ensure it is not preceded by 'INR' or followed by currency/measure unit tokens
        intent.years.add(val)

    # 6. Relative time expressions
    # Latest / recent / current state
    latest_patterns = [
        r'\b(?:latest|most\s+recent|recent|currently|current\s+status|at\s+present)\b',
        r'नवीनतम', r'ताजा', r'हालिया', r'सध्याचे', r'সর্বশেষ', r'সাম্প্রতিক',
        r'சமீபத்திய', r'தற்போதைய', r'ఇటీవలి', r'తాజా', r'ప్రస్తుత', r'ಇತ್ತೀಚಿನ',
    ]
    if any(re.search(p, norm_q, re.IGNORECASE) for p in latest_patterns):
        intent.relative_type = "latest"

    # Previous calendar year / last year
    previous_patterns = [
        r'\b(?:last\s+year|previous\s+year|past\s+year)\b',
        r'पिछले\s*साल', r'गत\s*वर्ष', r'बीते\s*वर्ष', r'मागील\s*वर्षी', r'गेल्या\s*वर्षी',
        r'গত\s*বছর', r'আগের\s*বছর', r'கடந்த\s*ஆண்டு', r'சென்ற\s*ஆண்டு',
        r'గత\s*సంవత్సరం', r'పోయిన\s*సంవత్సరం', r'ಹಿಂದಿನ\s*ವರ್ಷ', r'ಕಳೆದ\s*ವರ್ಷ',
    ]
    if any(re.search(p, norm_q, re.IGNORECASE) for p in previous_patterns):
        intent.relative_type = "previous"

    # Current year / this year
    current_patterns = [
        r'\b(?:current\s+year|this\s+year)\b',
        r'चालू\s*वर्ष', r'इस\s*वर्ष', r'चालू\s*वर्षी', r'या\s*वर्षी',
        r'চলতি\s*বছর', r'এই\s*বছর', r'நடப்பு\s*ஆண்டு', r'இந்த\s*ஆண்டு',
        r'ప్రస్తుత\s*సంవత్సరం', r'ఈ\s*సంవత్సరం', r'ಪ್ರಸ್ತುತ\s*ವರ್ಷ', r'ಈ\s*ವರ್ಷ',
    ]
    if any(re.search(p, norm_q, re.IGNORECASE) for p in current_patterns):
        intent.relative_type = "current"

    # Last N years (e.g. last 3 years, पिछले 3 साल)
    last_n_match = re.search(
        r'\b(?:last|past|previous|पिछले|गेल्या|गत|கடந்த|గత|ಕಳೆದ)\s*(\d+)\s*(?:years|साल|वर्षात|বছরে|ஆண்டுகளில்|సంవత్సరాలలో|ವರ್ಷಗಳಲ್ಲಿ)\b',
        norm_q,
        re.IGNORECASE,
    )
    if last_n_match:
        intent.relative_type = "last_n_years"
        intent.last_n_years_count = int(last_n_match.group(1))

    # General temporal markers
    general_temporal_markers = [
        r'\b(?:year|years|annual|annually|financial\s+year|fiscal|academic\s+year|survey\s+year|census\s+year|reporting\s+year|crop\s+year|saal|varsh)\b',
        r'वर्ष', r'वर्षात', r'वर्षातील', r'सालातील', r'वार्षिक', r'सालाना', r'आर्थिक\s*वर्ष', r'शैक्षणिक\s*वर्ष',
        r'বছর', r'বছরে', r'বছরের', r'বার্ষিক', r'আর্থিক\s*বছর', r'শিক্ষাবর্ষ', r'সালে',
        r'ஆண்டு', r'ஆண்டில்', r'ஆண்டின்', r'வருடம்', r'வருடத்தில்', r'வருடாந்திர', r'நிதியாண்டு', r'கல்வியாண்டு',
        r'సంవత్సరం', r'సంవత్సరంలో', r'సంవత్సరానికి', r'ఏడాది', r'ఏడాదిలో', r'వార్షిక', r'ఆర్థిక\s*సంవత్సరం', r'విద్యా\s*సంవత్సరం',
        r'ವರ್ಷ', r'ವರ್ಷದಲ್ಲಿ', r'ವರ್ಷದ', r'ವಾರ್ಷಿಕ',
    ]
    has_general_marker = any(re.search(p, norm_q, re.IGNORECASE) for p in general_temporal_markers)

    # Determine overall temporal intent
    intent.has_intent = bool(
        intent.years
        or intent.financial_years
        or intent.year_ranges
        or intent.dates
        or intent.relative_type
        or has_general_marker
    )

    return intent


def _extract_literal_val(node: exp.Expression) -> Any:
    """Extracts raw Python value (int, float, str) from a SQLGlot expression node."""
    if isinstance(node, exp.Literal):
        val = node.this
        if node.is_string:
            return str(val)
        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                return val
    return None


def is_temporal_predicate_supported(
    pred: exp.Expression,
    col_name: str,
    intent: TemporalIntent,
    table_name: Optional[str] = None,
) -> bool:
    """
    Validates whether a specific AST temporal predicate is semantically supported
    by the citizen's query intent.
    """
    # Rule 1: No temporal intent requested -> reject all temporal predicates
    if not intent.has_intent:
        return False

    meta = TABLE_TEMPORAL_METADATA.get(table_name or "", {})

    # Rule 2: Equality comparisons (col = val or val = col)
    if isinstance(pred, exp.EQ):
        other = pred.right if isinstance(pred.left, exp.Column) and pred.left.name.lower() == col_name else pred.left
        val = _extract_literal_val(other)

        # Check subquery (e.g., col = (SELECT MAX(col) FROM ...))
        if isinstance(other, (exp.Select, exp.Subquery)):
            if intent.relative_type == "latest":
                return True
            return False

        if val is not None:
            # Integer year matching (e.g. reporting_year = 2022)
            if isinstance(val, int) and val in intent.years:
                return True

            # Financial/academic year string matching (e.g. academic_year = '2023-24')
            if isinstance(val, str):
                val_clean = val.replace("/", "-")
                if val_clean in intent.financial_years:
                    return True
                # Check if any explicit year requested is contained in the string
                for y in intent.years:
                    if str(y) in val_clean:
                        return True
                if val_clean in intent.dates:
                    return True

            # Relative resolution using table metadata
            if intent.relative_type == "latest" and meta.get("latest"):
                if val == meta["latest"] or (isinstance(val, int) and val == max(meta.get("years", [val]))):
                    return True

            if intent.relative_type == "previous" and meta.get("previous"):
                if val == meta["previous"] or (isinstance(val, int) and val == (max(meta.get("years", [val])) - 1)):
                    return True

            if intent.relative_type == "current" and meta.get("latest"):
                if val == meta["latest"]:
                    return True

        return False

    # Rule 3: Range conditions (col BETWEEN low AND high)
    if isinstance(pred, exp.Between):
        low_val = _extract_literal_val(pred.args.get("low"))
        high_val = _extract_literal_val(pred.args.get("high"))

        # Explicit year ranges
        if isinstance(low_val, int) and isinstance(high_val, int):
            for r_low, r_high in intent.year_ranges:
                if low_val >= r_low and high_val <= r_high:
                    return True
            if low_val in intent.years and high_val in intent.years:
                return True

        # String-based financial year ranges
        if isinstance(low_val, str) and isinstance(high_val, str):
            for r_low, r_high in intent.year_ranges:
                if str(r_low) in low_val and str(r_high) in high_val:
                    return True

        return False

    # Rule 4: Set membership conditions (col IN (val1, val2, ...))
    if isinstance(pred, exp.In):
        # Subquery in IN clause (e.g. col IN (SELECT MAX(col)...))
        if pred.args.get("query") and intent.relative_type == "latest":
            return True

        for item in pred.expressions:
            val = _extract_literal_val(item)
            if isinstance(val, int) and val in intent.years:
                return True
            if isinstance(val, str):
                val_clean = val.replace("/", "-")
                if val_clean in intent.financial_years or any(str(y) in val_clean for y in intent.years):
                    return True

        return False

    # Rule 5: Greater Than / Less Than bounds (e.g. year >= 2022 for last 3 years)
    if isinstance(pred, (exp.GTE, exp.GT)):
        val = _extract_literal_val(pred.expression)
        if intent.relative_type == "last_n_years" and intent.last_n_years_count and meta.get("latest"):
            latest_y = max(meta.get("years", [2024]))
            expected_start = latest_y - intent.last_n_years_count + 1
            if val is not None and isinstance(val, int) and val >= expected_start:
                return True
        for r_low, _ in intent.year_ranges:
            if val is not None and isinstance(val, int) and val >= r_low:
                return True
        return False

    if isinstance(pred, (exp.LTE, exp.LT)):
        val = _extract_literal_val(pred.expression)
        for _, r_high in intent.year_ranges:
            if val is not None and isinstance(val, int) and val <= r_high:
                return True
        return False

    return False


def _find_enclosing_predicate(col: exp.Column) -> Optional[exp.Expression]:
    """Finds the root predicate node (EQ, Between, In, GTE, etc.) enclosing a Column AST node."""
    curr = col.parent
    pred = col
    while curr:
        if isinstance(curr, (exp.Where, exp.And, exp.Or, exp.Paren, exp.Select, exp.From, exp.Join)):
            break
        pred = curr
        curr = curr.parent
    if pred is not col:
        return pred
    return None


def _detach_predicate(node: exp.Expression) -> None:
    """
    Safely detaches an unsupported predicate from the AST, correctly updating
    its parent connector (And, Or, Paren, Where) without corrupting SQL syntax.
    """
    curr = node
    parent = node.parent

    # Unwrap enclosing non-connector parentheses
    while isinstance(parent, exp.Paren) and not isinstance(parent.this, (exp.And, exp.Or)):
        curr = parent
        parent = parent.parent

    # If the predicate is the sole condition in the WHERE clause, drop WHERE entirely
    if isinstance(parent, exp.Where):
        select_node = parent.parent
        if select_node:
            select_node.set("where", None)
        return

    # If joined by AND / OR, substitute the connector with the sibling branch
    if isinstance(parent, (exp.And, exp.Or)):
        other = parent.left if parent.right is curr else parent.right
        while isinstance(other, exp.Paren) and not isinstance(other.this, (exp.And, exp.Or)):
            other = other.this
        parent.replace(other)
        return

    # Fallback: Replace node with true literal
    node.replace(exp.true())


def sanitize_temporal_predicates(
    sql: str,
    query: str,
    table_name: Optional[str] = None,
) -> str:
    """
    Inspects SQL AST, verifies each temporal predicate against citizen intent,
    and returns a rewritten, syntactically pristine DuckDB query.
    """
    if not sql or not sql.strip():
        return sql

    intent = extract_temporal_intent(query)

    try:
        tree = sqlglot.parse_one(sql.strip(), read="duckdb")
        if not tree:
            return sql
    except Exception as e:
        logger.warning("SQLGlot failed to parse query (%s). Maintaining original query: %s", e, sql)
        return sql

    # Find all column nodes corresponding to temporal attributes
    temporal_predicates: List[Tuple[exp.Expression, str]] = []
    seen_pred_ids = set()

    for col in tree.find_all(exp.Column):
        col_name = col.name.lower()
        if col_name in TEMPORAL_COLUMN_NAMES:
            # Ensure this column is actually in a filter condition (WHERE or HAVING),
            # NOT in a projection or aggregate (like SELECT MAX(reporting_year))
            in_filter = False
            curr = col.parent
            while curr:
                if isinstance(curr, (exp.Where, exp.Having)):
                    in_filter = True
                    break
                if isinstance(curr, exp.Select):
                    break
                curr = curr.parent

            if not in_filter:
                continue

            pred = _find_enclosing_predicate(col)
            if pred and id(pred) not in seen_pred_ids:
                seen_pred_ids.add(id(pred))
                temporal_predicates.append((pred, col_name))

    # Evaluate each predicate against user temporal intent
    modified = False
    for pred, col_name in temporal_predicates:
        supported = is_temporal_predicate_supported(pred, col_name, intent, table_name=table_name)
        if not supported:
            logger.info("Detaching unrequested/contradictory temporal predicate: %s", pred.sql("duckdb"))
            _detach_predicate(pred)
            modified = True

    if not modified:
        return sql

    out_sql = tree.sql("duckdb")
    if not out_sql.endswith(";"):
        out_sql += ";"

    return out_sql


def has_temporal_intent(query: str) -> bool:
    """Returns True if the query exhibits any temporal constraint intent."""
    return extract_temporal_intent(query).has_intent


def prune_unrequested_temporal_filters(
    sql: str,
    query: str,
    table_name: Optional[str] = None,
) -> str:
    """Backwards-compatible alias for sanitize_temporal_predicates."""
    return sanitize_temporal_predicates(sql, query, table_name=table_name)

