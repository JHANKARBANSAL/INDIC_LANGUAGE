"""Execution-verified, fail-closed alternative question recommendations.

The catalog supplies candidate column names; actual sandbox queries determine whether
those columns and non-null rows exist. Only verified records are returned. No LLM
guesses, simulated rows, or client-provided SQL are used.
"""

import re
from typing import Any, Dict, List, Optional

from indicsql.agents.query_recommender import (
    _DIMENSIONS,
    _TEXT,
    _numeric_metrics,
    _terms,
)
from indicsql.schema.catalog import NDAPCatalog
from indicsql.schema.phonetic import normalize_indic_phonetics, transliterate_indic_to_latin

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _quote_identifier(identifier: str) -> str:
    """Reject non-identifier catalog names rather than treating them as SQL."""
    if not _IDENTIFIER.fullmatch(identifier):
        raise ValueError("Unsafe or unsupported SQL identifier")
    return '"' + identifier + '"'


def verified_alternative_queries(
    query: str,
    *,
    sandbox: Any,
    language: str = "en",
    preferred_table: Optional[str] = None,
    limit: int = 5,
    max_probes: int = 35,
) -> List[Dict[str, Any]]:
    """Offer up to five genuinely executable, nonempty schema-backed queries.

    A suggestion is admitted only if a read-only probe executes against the actual
    sandbox with at least one row containing non-null values for its displayed columns.
    Queries select raw metric and grouping values; no unsupported aggregation is
    implied. If the active DB cannot support any candidate, return an empty list.
    """
    if not query.strip() or limit <= 0 or max_probes <= 0:
        return []
    normalized = " ".join((
        query,
        normalize_indic_phonetics(query),
        transliterate_indic_to_latin(query),
    ))
    query_terms = _terms(normalized)
    candidates = []
    for table in NDAPCatalog.list_tables():
        info = NDAPCatalog.get_table_schema(table)
        columns = info.get("columns", {})
        if not isinstance(columns, dict):
            continue
        dimension = next((d for d in _DIMENSIONS if d in columns), None)
        metrics = _numeric_metrics(columns)
        if not dimension or not metrics:
            continue

        topical_text = " ".join((
            table, str(info.get("title", "")),
            str(info.get("description", "")), *columns.keys(),
        ))
        overlap = query_terms & _terms(topical_text)
        # No unrelated 'default' suggestions for unknown topics.
        if not overlap and table != preferred_table:
            continue
        for metric in metrics:
            metric_overlap = query_terms & _terms(metric + " " + str(columns[metric]))
            score = (len(overlap) * 3 + len(metric_overlap) * 4
                     + (8 if table == preferred_table else 0))
            candidates.append((-score, table, dimension, metric))

    candidates.sort()
    results: List[Dict[str, Any]] = []
    probed = 0
    template = _TEXT.get(language, _TEXT["en"])
    for _, table, dimension, metric in candidates:
        if probed >= max_probes or len(results) >= min(5, limit):
            break
        try:
            t = _quote_identifier(table)
            d = _quote_identifier(dimension)
            m = _quote_identifier(metric)
        except ValueError:
            continue
        # Only references physically cataloged table and columns. All data is
        # read from live sandbox; an absent physical table fails closed.
        base = (
            f"SELECT {d}, {m} FROM {t} "
            f"WHERE {d} IS NOT NULL AND {m} IS NOT NULL"
        )
        probe_sql = base + " LIMIT 1;"
        executed_sql = base + " LIMIT 25;"
        probed += 1
        try:
            sample = sandbox.execute_query(probe_sql)
            if not sample or int(sample.get("row_count", 0)) < 1:
                continue
            # Also test the exact SQL that the user will trigger.
            verified = sandbox.execute_query(executed_sql)
            if not verified or int(verified.get("row_count", 0)) < 1:
                continue
        except Exception:
            continue

        question = template.format(
            metric=metric.replace("_", " "),
            dimension=dimension.replace("_", " "),
            dataset=table,
        )
        results.append({
            "query": question,
            "sql": executed_sql,
            "table": table,
            "metric": metric,
            "dimension": dimension,
            "sample_row_count": int(verified["row_count"]),
        })
    return results
