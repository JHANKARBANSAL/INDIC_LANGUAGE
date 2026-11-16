#!/usr/bin/env python3
"""Evaluate aligned IndicDBBench questions through the schema-aware pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indicsql.agents.sql_synthesizer import _ollama_client
from indicsql.benchmark.indicdb import (
    INDICDB_LANGUAGE_FILES,
    IndicDBQuery,
    enrich_schema_context,
    load_aligned_indicdb_queries,
    load_schema_config,
)
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.sandbox.postgres_engine import PostgresSandbox


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_rows(rows: list[list[Any]]) -> list[str]:
    def normalize(value: Any) -> Any:
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, (int, float)):
            return round(float(value), 6)
        return value

    return sorted(
        json.dumps([normalize(value) for value in row], ensure_ascii=False, sort_keys=True)
        for row in rows
    )


def _evaluate_query(
    query: IndicDBQuery,
    schema_context: dict[str, Any],
    sandbox: PostgresSandbox,
) -> dict[str, Any]:
    started = perf_counter()
    gold_result = None
    gold_error = None
    try:
        gold_result = sandbox.execute_query(query.gold_sql, query.dataset_name)
    except Exception as exc:
        gold_error = str(exc)

    state = execute_indicsql_pipeline(
        query.question,
        query_id=(
            f"indicdb-{query.language}-{query.pair_id}-{query.dataset_name}"
        ),
        database_schema_name=query.dataset_name,
        database_schema=schema_context,
        database_schema_source="benchmark_dataset_name",
        language_override=query.language,
        sandbox=sandbox,
    )
    prediction = state.get("execution_result")
    execution_match = None
    if gold_result is not None and prediction is not None:
        execution_match = _normalized_rows(gold_result["rows"]) == _normalized_rows(
            prediction["rows"]
        )

    elapsed_ms = (perf_counter() - started) * 1000
    return {
        "language": query.language,
        "pair_id": query.pair_id,
        "dataset_name": query.dataset_name,
        "question": query.question,
        "gold_sql": query.gold_sql,
        "generated_sql": state.get("generated_sql", ""),
        "gold_error": gold_error,
        "prediction_error": state.get("execution_error"),
        "gold_row_count": gold_result["row_count"] if gold_result is not None else None,
        "prediction_row_count": prediction["row_count"] if prediction is not None else None,
        "gold_empty": bool(gold_result is not None and not gold_result["rows"]),
        "execution_match": execution_match,
        "pipeline_latency_ms": elapsed_ms,
        "verbalized_response": state.get("verbalized_response", ""),
        "schema_source": query.dataset_name,
        "schema_selection_mode": "benchmark_dataset_name_oracle",
        "audit_trace": state.get("audit_trace", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", required=True, type=Path)
    parser.add_argument("--archive", type=Path, help="Defaults to indicDB.zip in --parquet-dir.")
    parser.add_argument(
        "--dsn",
        default=os.environ.get("INDICDB_DSN"),
        help="PostgreSQL DSN; defaults to INDICDB_DSN.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark_results/indicdb_all_languages.json"),
    )
    parser.add_argument("--limit", type=int, help="Evaluate only the first N aligned pairs per language.")
    parser.add_argument("--pair-id", help="Evaluate one aligned pair across all languages.")
    parser.add_argument("--dataset-name", help="Disambiguate a reused pair ID across schemas.")
    parser.add_argument(
        "--languages",
        nargs="+",
        choices=list(INDICDB_LANGUAGE_FILES),
        default=list(INDICDB_LANGUAGE_FILES),
    )
    args = parser.parse_args()
    if not args.dsn:
        parser.error("Provide --dsn or set INDICDB_DSN.")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive.")

    aligned, query_keys = load_aligned_indicdb_queries(args.parquet_dir)
    if args.pair_id:
        matches = [
            key
            for key in query_keys
            if key[0] == args.pair_id
            and (not args.dataset_name or key[1] == args.dataset_name)
        ]
        if len(matches) != 1:
            parser.error(
                f"Pair ID {args.pair_id!r} has {len(matches)} aligned matches; "
                "specify a unique --dataset-name."
            )
        selected_keys = matches
    else:
        selected_keys = query_keys[: args.limit] if args.limit else query_keys

    sandbox = PostgresSandbox(args.dsn)
    schemas: dict[str, dict[str, Any]] = {}
    archive_path = args.archive or (args.parquet_dir / "indicDB.zip")
    records: list[dict[str, Any]] = []
    try:
        for language in args.languages:
            by_key = {
                (query.pair_id, query.dataset_name): query for query in aligned[language]
            }
            for query_key in selected_keys:
                query = by_key[query_key]
                if query.dataset_name not in schemas:
                    schemas[query.dataset_name] = enrich_schema_context(
                        sandbox.get_schema_context(query.dataset_name),
                        load_schema_config(archive_path, query.dataset_name),
                    )
                records.append(
                    _evaluate_query(query, schemas[query.dataset_name], sandbox)
                )
    finally:
        sandbox.close()

    metrics: dict[str, dict[str, Any]] = {}
    for language in args.languages:
        language_records = [row for row in records if row["language"] == language]
        matched = [row for row in language_records if row["execution_match"] is not None]
        metrics[language] = {
            "queries": len(language_records),
            "execution_successes": sum(
                row["prediction_error"] is None and row["prediction_row_count"] is not None
                for row in language_records
            ),
            "gold_empty_results": sum(row["gold_empty"] for row in language_records),
            "comparable_queries": len(matched),
            "execution_accuracy": (
                sum(row["execution_match"] is True for row in matched) / len(matched)
                if matched
                else None
            ),
            "mean_pipeline_latency_ms": (
                sum(row["pipeline_latency_ms"] for row in language_records)
                / len(language_records)
                if language_records
                else None
            ),
        }

    hashes = {
        language: _sha256_file(args.parquet_dir / filename)
        for language, filename in INDICDB_LANGUAGE_FILES.items()
    }
    result = {
        "artifact_type": "IndicDBBench evaluation on reconstructed IndicDB variant",
        "official_benchmark_result": False,
        "database_variant": "Reconstructed from supplied archive; not the unmodified official database.",
        "schema_selection_mode": (
            "The benchmark dataset_name column supplies the expected schema (oracle); "
            "this run does not measure automatic database selection."
        ),
        "model": _ollama_client.model_name,
        "languages": args.languages,
        "aligned_pairs_available": len(query_keys),
        "query_keys_evaluated": [
            {"pair_id": pair_id, "dataset_name": dataset_name}
            for pair_id, dataset_name in selected_keys
        ],
        "language_metrics": metrics,
        "parquet_sha256": hashes,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "language_metrics": metrics}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
