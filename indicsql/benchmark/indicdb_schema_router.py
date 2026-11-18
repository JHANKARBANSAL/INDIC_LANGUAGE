"""Model-based schema selection for the sealed IndicDB evaluation."""

from __future__ import annotations

import json
from typing import Any

import httpx

SCHEMA_ROUTER_PROMPT_VERSION = "indicdb-schema-router-v1"
INFERENCE_TEMPERATURE = 0.05
INFERENCE_SEED = 42


class SchemaRoutingError(ValueError):
    """Raised when the model does not return one of the available schemas."""


def _schema_summary(schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
    tables = []
    for table_name, table in sorted(schema.get("tables", {}).items()):
        tables.append(
            {
                "table": table_name,
                "description": table.get("description", ""),
                "columns": sorted(table.get("columns", {})),
            }
        )
    return {
        "schema_name": schema_name,
        "description": schema.get("description", ""),
        "tables": tables,
    }


def select_schema(
    query: str,
    schema_contexts: dict[str, dict[str, Any]],
    *,
    model_name: str,
    ollama_url: str,
    timeout_seconds: float = 90.0,
) -> str:
    """Select a schema from metadata alone; the benchmark label is not an input."""
    if not schema_contexts:
        raise SchemaRoutingError("No PostgreSQL schemas are available for routing.")

    candidates = [
        _schema_summary(name, context) for name, context in sorted(schema_contexts.items())
    ]
    prompt = (
        "Select the single PostgreSQL schema whose tables best answer the user's "
        "question. Use only the schema metadata below. Do not write SQL. Return "
        'strict JSON with exactly one field: {"schema_name":"<exact candidate name>"}.\n'
        f"Question:\n{query}\n"
        "Candidate schemas:\n" + json.dumps(candidates, ensure_ascii=False, separators=(",", ":"))
    )
    response = httpx.post(
        f"{ollama_url.rstrip('/')}/api/generate",
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": INFERENCE_TEMPERATURE,
                "seed": INFERENCE_SEED,
            },
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    result = response.json().get("response")
    if not isinstance(result, str):
        raise SchemaRoutingError("Ollama returned no JSON schema-selection response.")
    try:
        payload = json.loads(result)
    except json.JSONDecodeError as exc:
        raise SchemaRoutingError("Ollama returned invalid JSON for schema selection.") from exc

    selected = payload.get("schema_name") if isinstance(payload, dict) else None
    if not isinstance(selected, str) or selected not in schema_contexts:
        raise SchemaRoutingError("Ollama selected a schema that is not in the PostgreSQL catalog.")
    return selected
