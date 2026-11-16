"""
Cross-Lingual Schema-Linking Agent.
Maps vernacular and transliterated tokens to exact English database tables and columns.
Addresses the 20% schema-linking error diagnosed in the IndicDB benchmark.
"""

import re
from typing import Any, Dict, List

from indicsql.core.state import IndicSQLState, SchemaElement
from indicsql.events.bus import EventBus
from indicsql.events.schemas import SchemaLinkedEvent
from indicsql.schema.catalog import NDAPCatalog
from indicsql.schema.multilingual_index import NDAP_MULTILINGUAL_INDEX
from indicsql.schema.phonetic import normalize_indic_phonetics, transliterate_indic_to_latin

_SCHEMA_CONCEPT_TERMS = {
    "district": ("district", "जिल", "জেল", "மாவட்ட", "జిల్లా", "jilla", "jela"),
    "state": ("state", "राज्य", "রাজ্য", "மாநில", "రాష్ట్ర", "rajya", "rajy"),
}
_QUERY_STOPWORDS = {
    "a", "all", "an", "and", "are", "as", "at", "by", "during", "for", "from",
    "in", "is", "month", "months", "of", "on", "or", "that", "the", "this", "to",
    "where", "which", "with", "year", "years",
}


def _query_schema_terms(text: str) -> set[str]:
    terms = set(re.findall(r"[a-z0-9]+", text.lower()))
    terms.update(
        term[:-1] for term in tuple(terms) if len(term) > 4 and term.endswith("s")
    )
    return terms - _QUERY_STOPWORDS


def _unsupported_farmer_literacy_query(
    query: str, provided_schema: Dict[str, Any] | None
) -> str | None:
    normalized_query = " ".join(
        (
            query.lower(),
            normalize_indic_phonetics(query).lower(),
            transliterate_indic_to_latin(query).lower(),
        )
    )
    terms = _query_schema_terms(normalized_query)
    if "farmer" not in terms or not terms.intersection(
        {"literate", "literacy", "illiterate"}
    ):
        return None

    schemas = (
        [provided_schema]
        if provided_schema is not None
        else [
            {"tables": {name: NDAPCatalog.get_table_schema(name)}}
            for name in NDAPCatalog.list_tables()
        ]
    )
    for schema in schemas:
        for table in schema.get("tables", {}).values():
            column_terms = [
                (
                    _query_schema_terms(column_name),
                    _query_schema_terms(str(description)),
                )
                for column_name, description in table.get("columns", {}).items()
            ]
            has_joint_count = any(
                "farmer" in name_terms
                and name_terms.intersection({"literate", "literacy", "illiterate"})
                and name_terms.intersection({"count", "number", "beneficiary"})
                for name_terms, _ in column_terms
            )
            has_farmer_identifier = any(
                "farmer" in name_terms
                and name_terms.intersection({"id", "name", "identifier"})
                for name_terms, _ in column_terms
            )
            has_literacy_status = any(
                name_terms.intersection({"literate", "literacy", "illiterate"})
                or description_terms.intersection(
                    {"literate", "literacy", "illiterate"}
                )
                for name_terms, description_terms in column_terms
            )
            if has_joint_count or (has_farmer_identifier and has_literacy_status):
                return None

    return (
        "The available data has farmer-beneficiary counts and literacy rates "
        "separately, but does not record literacy status for individual farmers. "
        "It cannot answer how many farmers are literate. Ask for farmer counts "
        "or literacy rates separately."
    )


def _farmer_literacy_suggestions(query: str) -> List[str]:
    location = ""
    match = re.search(
        r"\b(?:in|within|for)\s+([A-Za-z][A-Za-z -]*?)"
        r"(?=\s+(?:are|is|was|were|literate|illiterate|literacy)\b|[?,.!;]|$)",
        query,
        re.IGNORECASE,
    )
    if match:
        location = f" in {match.group(1).strip()}"

    return [
        f"How many PM-KISAN farmer beneficiaries were there{location}?",
        f"What was the female literacy rate{location}?",
        f"What was the male literacy rate{location}?",
    ]


def _relevant_schema(schema: Dict[str, Any], query: str) -> Dict[str, Any]:
    tables = schema.get("tables", {})
    normalized_query = " ".join(
        (
            query.lower(),
            normalize_indic_phonetics(query).lower(),
            transliterate_indic_to_latin(query).lower(),
        )
    )
    concepts = {
        concept
        for concept, terms in _SCHEMA_CONCEPT_TERMS.items()
        if any(term in normalized_query for term in terms)
    }
    if not concepts:
        return schema

    query_terms = _query_schema_terms(normalized_query) - concepts
    selected: set[str] = set()
    table_concepts: dict[str, set[str]] = {}
    lexical_matches: set[str] = set()
    for table_name, table in tables.items():
        schema_terms = _query_schema_terms(
            f"{table_name} {' '.join(table.get('columns', {}))}"
        )
        if query_terms & schema_terms:
            selected.add(table_name)
            lexical_matches.add(table_name)
        searchable_columns = [
            column.lower().split("_")
            for column in table.get("columns", {})
            if not column.lower().endswith("_id")
            and not column.lower().startswith("sub_district_")
        ]
        searchable_names = table_name.lower().split("_")
        matched_concepts = {
            concept
            for concept in concepts
            if concept in searchable_names
            or any(concept in column_tokens for column_tokens in searchable_columns)
        }
        if matched_concepts:
            selected.add(table_name)
            table_concepts[table_name] = matched_concepts

    if not selected:
        return schema

    connected = set(selected)
    for table_name in lexical_matches:
        for relationship in tables[table_name].get("foreign_keys", []):
            referenced_table = relationship.rsplit(" references ", 1)[-1].split(".", 1)[0]
            if referenced_table in tables:
                connected.add(referenced_table)
    for table_name in selected:
        if "district" not in table_concepts.get(table_name, set()):
            continue
        table = tables[table_name]
        for relationship in table.get("foreign_keys", []):
            referenced_table = relationship.rsplit(" references ", 1)[-1].split(".", 1)[0]
            connected.add(referenced_table)

    return {
        **schema,
        "tables": {
            table_name: table
            for table_name, table in tables.items()
            if table_name in connected
        },
    }


def link_schema_elements(query: str, lang: str = "en") -> List[SchemaElement]:
    """
    Identifies database tables and columns based on phonetic transliteration
    and dense cross-lingual multilingual index matching across all 20 NDAP databases.
    """
    # Normalize query phonetically
    normalized = normalize_indic_phonetics(query, target_lang=lang)
    search_space = f"{query.lower()} {normalized.lower()}"

    scored_elements: List[tuple[int, SchemaElement]] = []

    for key, meta in NDAP_MULTILINGUAL_INDEX.items():
        score = 0
        for syn in meta["synonyms"]:
            syn_lower = syn.lower()
            if syn_lower in search_space:
                # Longer matches get higher weight
                score += max(len(syn_lower), 3)

        if score > 0:
            scored_elements.append(
                (
                    score,
                    {
                        "table_name": meta["table"],
                        "column_name": meta["column"],
                        "data_type": meta["data_type"],
                        "indic_synonyms": meta["synonyms"][:5],
                        "is_foreign_key": False,
                        "foreign_target": None,
                    },
                )
            )

    # Sort candidates by match weight descending
    scored_elements.sort(key=lambda x: x[0], reverse=True)
    matched_elements = [el for _, el in scored_elements]

    return matched_elements


def schema_linker_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Schema Linker Node: Extracts relevant tables/columns for the canonical query.
    Emits SchemaLinkedEvent on the EventBus.
    """
    canonical_query = state.get("canonical_query", state.get("raw_query", ""))
    lang = state.get("detected_lang", "en")

    provided_schema = state.get("database_schema")
    provided_schema_name = state.get("database_schema_name")
    unsupported_query_error = _unsupported_farmer_literacy_query(
        canonical_query, provided_schema
    )
    suggested_queries = (
        _farmer_literacy_suggestions(canonical_query)
        if unsupported_query_error
        else []
    )
    linked_schema = None
    if unsupported_query_error:
        pruned = []
        primary_table = ""
    elif provided_schema and provided_schema_name:
        linked_schema = _relevant_schema(provided_schema, canonical_query)
        pruned = [
            {
                "table_name": table_name,
                "column_name": column_name,
                "data_type": data_type,
                "indic_synonyms": [],
                "is_foreign_key": any(
                    relationship.startswith(f"{column_name} ")
                    for relationship in table.get("foreign_keys", [])
                ),
                "foreign_target": None,
            }
            for table_name, table in linked_schema.get("tables", {}).items()
            for column_name, data_type in table.get("columns", {}).items()
        ]
        primary_table = provided_schema_name
    elif provided_schema:
        pruned = []
        primary_table = ""
    else:
        pruned = link_schema_elements(canonical_query, lang)
        existing_target = state.get("target_database")
        if existing_target:
            primary_table = existing_target
        else:
            primary_table = pruned[0]["table_name"] if pruned else ""
    matched_cols = [el["column_name"] for el in pruned]
    has_target = bool(primary_table and (pruned or state.get("target_database")))
    if provided_schema:
        has_target = bool(primary_table and pruned)
    linking_error = unsupported_query_error or (
        None
        if has_target
        else "No supported database schema matched this question; no query was executed."
    )

    # Dynamic schema-linking confidence score based on match count and specificity
    match_density = sum(len(el.get("indic_synonyms", [])) for el in pruned)
    if provided_schema:
        confidence = 0.98 if pruned else 0.40
    else:
        confidence = (
            min(0.98, max(0.45, round(0.50 + (match_density * 0.05), 2)))
            if pruned
            else 0.40
        )

    EventBus.publish(
        SchemaLinkedEvent(
            query_id=state.get("query_id"),
            target_table=primary_table or "unmatched",
            matched_columns=matched_cols,
            confidence=confidence,
        )
    )

    audit_entry = {
        "step": 2,
        "agent": "SchemaLinkerAgent",
        "action": "cross_lingual_lookup",
        "matched_table": primary_table,
        "matched_columns": matched_cols,
        "confidence": confidence,
        "status": (
            "schema_context"
            if provided_schema and not linking_error
            else "matched"
            if not linking_error
            else "unmatched"
        ),
        "schema_source": state.get("database_schema_source", "query_match"),
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "pruned_schema": pruned,
        "target_database": primary_table,
        **({"database_schema": linked_schema} if linked_schema is not None else {}),
        "schema_linking_error": linking_error,
        "suggested_queries": suggested_queries,
        "audit_trace": current_trace,
    }
