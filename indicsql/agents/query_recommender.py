"""Schema-grounded, deterministic suggestions for questions the system cannot answer.

Suggestions describe columns that exist in the active schema. They are not proof
that the database has matching rows or that a generated SQL query is correct.
No LLM text is used to invent columns or statistical answers.
"""

import re
from typing import Any, Dict, List, Optional

from indicsql.schema.catalog import NDAPCatalog
from indicsql.schema.phonetic import normalize_indic_phonetics, transliterate_indic_to_latin

_STOP = {
    "how", "what", "which", "where", "when", "many", "much", "the", "this",
    "that", "there", "have", "has", "are", "was", "were", "from", "with",
    "about", "show", "list", "give", "tell", "data", "number", "count",
    "total", "state", "district", "year", "india", "indian", "all", "for",
    "and", "does", "did", "can", "please", "me", "in", "of", "on", "to",
}

_DIMENSIONS = (
    "district_name", "state_name", "district", "state", "crop_name",
    "commodity", "market_name", "financial_year", "census_year",
    "academic_year", "survey_year", "crop_year", "year",
)

_TEXT = {
    "en": "Show {metric} by {dimension} from {dataset}.",
    "hi": "{dataset} डेटासेट में {dimension} के अनुसार {metric} दिखाएं।",
    "mr": "{dataset} डेटासेटमध्ये {dimension} नुसार {metric} दाखवा.",
    "bn": "{dataset} ডেটাসেটে {dimension} অনুযায়ী {metric} দেখাও।",
    "ta": "{dataset} தரவுத்தொகுப்பில் {dimension} வாரியாக {metric} காட்டு.",
    "te": "{dataset} డేటాసెట్‌లో {dimension} వారీగా {metric} చూపించండి.",
    "hi-en": "{dataset} dataset mein {dimension} ke hisaab se {metric} dikhao.",
}


def _terms(value: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-z0-9]+", value.casefold().replace("_", " "))
        if len(word) > 2 and word not in _STOP
    }


def _numeric_metrics(columns: Dict[str, Any]) -> List[str]:
    result = []
    for name, description in columns.items():
        lower = name.casefold()
        if (
            lower in _DIMENSIONS
            or lower.endswith("_id")
            or lower in {"id", "geo_id", "time_id", "fact_id"}
            or lower.endswith("_year")
        ):
            continue
        data_type = str(description).upper().split(" - ", 1)[0]
        if any(dtype in data_type for dtype in ("INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC", "REAL")):
            result.append(name)
    return result


def recommend_alternative_queries(
    query: str,
    *,
    schema: Optional[Dict[str, Any]] = None,
    language: str = "en",
    preferred_table: Optional[str] = None,
    limit: int = 5,
) -> List[str]:
    """Return up to `limit` distinct questions based on documented numeric columns.

    When no topical overlap is found, fail closed with an empty suggestion list.
    For externally provided schemas, search *only* that schema, never the NDAP catalog.
    """
    if not query.strip() or limit < 1:
        return []

    if schema is not None:
        tables = schema.get("tables", {})
    else:
        tables = {
            name: NDAPCatalog.get_table_schema(name)
            for name in NDAPCatalog.list_tables()
        }
    if not isinstance(tables, dict):
        return []

    search_text = " ".join((
        query,
        normalize_indic_phonetics(query),
        transliterate_indic_to_latin(query),
    ))
    query_terms = _terms(search_text)
    ranked = []
    for name, info in tables.items():
        if not isinstance(info, dict):
            continue
        columns = info.get("columns", {})
        if not isinstance(columns, dict):
            continue
        metrics = _numeric_metrics(columns)
        if not metrics:
            continue
        topic_terms = _terms(" ".join((
            name, str(info.get("title", "")), str(info.get("description", "")),
            *columns.keys(),
        )))
        overlap = query_terms & topic_terms
        # Do not suggest irrelevant datasets merely to fill 3-5 slots.
        if not overlap and name != preferred_table:
            continue
        relevance = len(overlap) + (3 if name == preferred_table else 0)
        ranked.append((relevance, name, info, metrics))

    ranked.sort(key=lambda entry: (-entry[0], entry[1]))
    suggestions: List[str] = []
    template = _TEXT.get(language, _TEXT["en"])
    for _, table_name, info, metrics in ranked:
        columns = info["columns"]
        dimension = next((dim for dim in _DIMENSIONS if dim in columns), None)
        # Do not generate a query requiring a join or a missing dimension.
        if dimension is None:
            continue
        ranked_metrics = sorted(
            metrics,
            key=lambda column: (
                -len(_terms(column + " " + str(columns[column])) & query_terms),
                column,
            ),
        )
        for metric in ranked_metrics:
            suggestion = template.format(
                metric=metric.replace("_", " "),
                dimension=dimension.replace("_", " "),
                dataset=table_name,
            )
            if suggestion not in suggestions:
                suggestions.append(suggestion)
            if len(suggestions) >= min(limit, 5):
                return suggestions
    return suggestions
