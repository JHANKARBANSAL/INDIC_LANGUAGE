"""Safe default policies for interactive NDAP queries."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

import sqlglot
from sqlglot import exp

from indicsql.models.temporal_guard import (
    TABLE_TEMPORAL_METADATA,
    extract_temporal_intent,
)
from indicsql.schema.phonetic import transliterate_indic_to_latin

_YEAR_BREAKDOWN_PATTERNS = (
    r"\b(?:by|per|each|every)\s+(?:financial\s+)?years?\b",
    r"\b(?:year[- ]wise|yearly|year by year|annual\s+trend|trend\s+over\s+time)\b",
    r"वर्षवार|हर\s*साल|દર\s*વર્ષે|বছরভিত্তিক|প্রতি\s*বছর|ஆண்டு\s*வாரியாக|ప్రతి\s*సంవత్సరం",
)
_LITERACY_TERMS = (
    "literacy",
    "literate",
    "साक्षर",
    "எழுத்தறிவு",
    "கல்வியறிவு",
    "అక్షరాస్యత",
    "সাক্ষর",
    "saksharta",
)
_FEMALE_TERMS = (
    "female",
    "women",
    "woman",
    "महिला",
    "स्त्री",
    "பெண்",
    "స్త్రీ",
    "మహిళా",
    "নারী",
)
_MALE_TERMS = ("male", "men", "पुरुष", "ஆண்", "పురుష", "পুরুষ")
_AVERAGE_PATTERNS = (
    r"\b(?:average|mean|avg)\b",
    r"औसत|सरासरी|গড়|சராசரி|సగటు",
)
_RANKING_PATTERNS = (
    r"\b(?:top|bottom|highest|lowest|maximum|minimum|rank|ranking)\b",
    r"सबसे\s*(?:कम|ज्यादा|अधिक)|सर्वाधिक|सर्वात\s*(?:कमी|जास्त)",
    r"সবচেয়ে\s*(?:কম|বেশি)|மிகக்\s*(?:குறைந்த|அதிக)|అత్యంత\s*(?:తక్కువ|ఎక్కువ)",
)


def _query_has_any(query: str, terms: Tuple[str, ...]) -> bool:
    lowered = f"{query} {transliterate_indic_to_latin(query)}".lower()
    for term in terms:
        if re.fullmatch(r"[a-z ]+", term):
            if re.search(
                rf"(?<![a-z]){re.escape(term)}(?![a-z])",
                lowered,
            ):
                return True
        elif term in lowered:
            return True
    return False


def _query_requests_year_breakdown(query: str) -> bool:
    transliterated = transliterate_indic_to_latin(query)
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in _YEAR_BREAKDOWN_PATTERNS
        for text in (query, transliterated)
    )


def _requested_period(query: str, table_name: str) -> Optional[object]:
    intent = extract_temporal_intent(query)
    if intent.years or intent.financial_years or intent.year_ranges or intent.dates:
        return None

    metadata = TABLE_TEMPORAL_METADATA.get(table_name, {})
    if intent.relative_type == "previous":
        return metadata.get("previous")
    if intent.relative_type in {"latest", "current"}:
        return metadata.get("latest")
    if intent.relative_type == "last_n_years" or _query_requests_year_breakdown(query):
        return None

    return metadata.get("latest")


def _where_columns(tree: exp.Expression) -> set[str]:
    where = tree.args.get("where")
    if not where:
        return set()
    return {column.name.lower() for column in where.find_all(exp.Column)}


def _selected_columns(tree: exp.Expression) -> set[str]:
    return {
        column.name.lower()
        for projection in tree.expressions
        for column in projection.find_all(exp.Column)
    }


def _can_default_period(tree: exp.Expression, query: str, table_name: str) -> bool:
    if table_name == "ndap_pm_kisan_disbursement":
        return "farmer_beneficiaries" in _selected_columns(tree)
    if table_name == "ndap_education_stats":
        return _query_has_any(query, _LITERACY_TERMS)
    return False


def _add_period_filter(
    tree: exp.Expression, column_name: str, period: object
) -> bool:
    if column_name.lower() in _where_columns(tree):
        return False

    value = (
        exp.Literal.string(str(period))
        if isinstance(period, str)
        else exp.Literal.number(str(period))
    )
    predicate = exp.EQ(this=exp.column(column_name), expression=value)
    where = tree.args.get("where")
    if where:
        tree.set("where", exp.Where(this=exp.and_(where.this.copy(), predicate)))
    else:
        tree.set("where", exp.Where(this=predicate))
    return True


def _enforce_year_breakdown(
    tree: exp.Expression, query: str, table_name: str
) -> bool:
    if (
        table_name != "ndap_pm_kisan_disbursement"
        or not _query_requests_year_breakdown(query)
    ):
        return False

    period_column = TABLE_TEMPORAL_METADATA[table_name]["col"]
    projections = list(tree.expressions)
    changed = False
    if period_column.lower() not in _selected_columns(tree):
        projections.append(exp.column(period_column))
        tree.set("expressions", projections)
        changed = True

    group = tree.args.get("group")
    group_expressions = list(group.expressions) if group else []
    group_has_period = any(
        column.name.lower() == period_column.lower()
        for expression in group_expressions
        for column in expression.find_all(exp.Column)
    )
    has_aggregate = any(
        expression.find(exp.AggFunc) is not None for expression in projections
    )
    if has_aggregate and not group_has_period:
        group_expressions.append(exp.column(period_column))
        tree.set("group", exp.Group(expressions=group_expressions))
        changed = True

    return changed


def _rewrite_state_literacy_as_district_rates(
    tree: exp.Expression, query: str
) -> bool:
    if not _query_has_any(query, _LITERACY_TERMS):
        return False
    where_columns = _where_columns(tree)
    if "state_name" not in where_columns or "district_name" in where_columns:
        return False
    if any(re.search(pattern, query, re.IGNORECASE) for pattern in _AVERAGE_PATTERNS):
        return False
    if any(re.search(pattern, query, re.IGNORECASE) for pattern in _RANKING_PATTERNS):
        return False

    rate_columns = _requested_literacy_columns(query)
    projections = [
        exp.column("district_name"),
        exp.column("census_year"),
        *(exp.column(column) for column in rate_columns),
    ]
    tree.set("expressions", projections)
    tree.set("group", None)
    tree.set("having", None)
    tree.set("order", sqlglot.parse_one("SELECT 1 ORDER BY district_name").args["order"])
    tree.set("limit", None)
    tree.set("distinct", None)
    return True


def _rewrite_state_literacy_average(
    tree: exp.Expression, query: str
) -> bool:
    if not _query_has_any(query, _LITERACY_TERMS):
        return False
    where_columns = _where_columns(tree)
    if "state_name" not in where_columns or "district_name" in where_columns:
        return False
    if not any(re.search(pattern, query, re.IGNORECASE) for pattern in _AVERAGE_PATTERNS):
        return False
    if any(re.search(pattern, query, re.IGNORECASE) for pattern in _RANKING_PATTERNS):
        return False

    projections = []
    for column in _requested_literacy_columns(query):
        alias = f"unweighted_average_{column}"
        projections.append(
            exp.Alias(
                this=exp.Avg(this=exp.column(column)),
                alias=exp.to_identifier(alias),
            )
        )
    tree.set("expressions", projections)
    tree.set("group", None)
    tree.set("having", None)
    tree.set("order", None)
    tree.set("limit", None)
    tree.set("distinct", None)
    return True


def _requested_literacy_columns(query: str) -> List[str]:
    female = _query_has_any(query, _FEMALE_TERMS)
    male = _query_has_any(query, _MALE_TERMS)
    columns = []
    if female or not male:
        columns.append("female_literacy_rate")
    if male or not female:
        columns.append("male_literacy_rate")
    return columns


def apply_interactive_query_defaults(
    sql: str, query: str, table_name: Optional[str]
) -> Tuple[str, List[str]]:
    """Apply non-misleading time and aggregation defaults to interactive NDAP SQL."""
    if not sql or not table_name:
        return sql, []

    try:
        tree = sqlglot.parse_one(sql.strip(), read="duckdb")
    except sqlglot.errors.ParseError:
        return sql, []
    if not isinstance(tree, exp.Select):
        return sql, []

    applied_defaults: List[str] = []
    metadata = TABLE_TEMPORAL_METADATA.get(table_name, {})
    if _can_default_period(tree, query, table_name):
        period = _requested_period(query, table_name)
    else:
        period = None
    if period is not None and metadata.get("col"):
        period_column = metadata["col"]
        if _add_period_filter(tree, period_column, period):
            applied_defaults.append(
                f"Using the latest available {period_column} ({period}) because no period was specified."
                if extract_temporal_intent(query).relative_type is None
                else f"Using {period_column} ({period}) based on the requested relative period."
            )

    if _enforce_year_breakdown(tree, query, table_name):
        applied_defaults.append(
            f"Grouping results by {metadata['col']} to show the requested year-by-year breakdown."
        )

    if table_name == "ndap_education_stats":
        if _rewrite_state_literacy_as_district_rates(tree, query):
            applied_defaults.append(
                "Showing district literacy rates; the available data has no population weights "
                "for a valid state-wide literacy rate."
            )
        elif _rewrite_state_literacy_average(tree, query):
            applied_defaults.append(
                "Reporting an unweighted mean of district literacy rates; no adult-population "
                "denominator is available for a weighted state-wide rate."
            )

    if not applied_defaults:
        return sql, []

    output = tree.sql("duckdb")
    return (output if output.endswith(";") else f"{output};"), applied_defaults
