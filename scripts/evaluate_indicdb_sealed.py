#!/usr/bin/env python3
# ruff: noqa: E402
"""Run the locked IndicDB sealed test once, with automatic schema selection."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from functools import reduce
from operator import or_
from pathlib import Path
from time import perf_counter
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indicsql.agents.sql_synthesizer import _ollama_client
from indicsql.benchmark.indicdb import (
    INDICDB_LANGUAGE_FILES,
    IndicDBQuery,
    enrich_schema_context,
    load_schema_config,
)
from indicsql.benchmark.indicdb_schema_router import (
    INFERENCE_SEED,
    INFERENCE_TEMPERATURE,
    select_schema,
)
from indicsql.graph.workflow import execute_indicsql_pipeline
from indicsql.sandbox.postgres_engine import PostgresSandbox
from scripts.execute_indicdb_gold import build_schema_mapping
from scripts.lock_indicdb_final_run import validate_final_run_lock


def _key_payload_sha256(payload: list[dict[str, Any]]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _load_selected_keys(
    key_path: Path, expected_digest: str, expected_count: int
) -> list[dict[str, str]]:
    payload = json.loads(key_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or len(payload) != expected_count:
        raise ValueError("Selected-key file has an unexpected shape or group count.")
    if _key_payload_sha256(payload) != expected_digest:
        raise ValueError("Selected-key file does not match the sealed manifest hash.")
    keys: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in payload:
        if (
            not isinstance(item, dict)
            or set(item) != {"pair_id", "dataset_name"}
            or not isinstance(item["pair_id"], str)
            or not isinstance(item["dataset_name"], str)
        ):
            raise ValueError("Selected-key file contains invalid entries.")
        key = (item["pair_id"], item["dataset_name"])
        if key in seen:
            raise ValueError("Selected-key file contains duplicate entries.")
        seen.add(key)
        keys.append({"pair_id": key[0], "dataset_name": key[1]})
    return keys


def load_selected_queries(
    parquet_dir: Path, selected_keys: list[dict[str, str]]
) -> dict[tuple[str, str], dict[str, IndicDBQuery]]:
    """Read only rows selected by the sealed key list from each Parquet file."""
    import pyarrow.dataset as arrow_dataset

    selected = {(item["pair_id"], item["dataset_name"]) for item in selected_keys}
    expressions = [
        (arrow_dataset.field("pair_id") == pair_id)
        & (arrow_dataset.field("dataset_name") == dataset_name)
        for pair_id, dataset_name in sorted(selected)
    ]
    filter_expression = reduce(or_, expressions)
    groups: dict[tuple[str, str], dict[str, IndicDBQuery]] = {key: {} for key in selected}

    for language, filename in INDICDB_LANGUAGE_FILES.items():
        path = parquet_dir / filename
        table = arrow_dataset.dataset(path, format="parquet").to_table(
            columns=["question", "sql", "pair_id", "dataset_name"],
            filter=filter_expression,
        )
        for row in table.to_pylist():
            key = (str(row["pair_id"]).strip(), str(row["dataset_name"]).strip())
            if key not in selected:
                raise ValueError("Parquet filter returned a row outside the sealed key list.")
            if language in groups[key]:
                raise ValueError(f"Duplicate selected row for {key!r} in {language}.")
            question = row["question"]
            gold_sql = row["sql"]
            if not isinstance(question, str) or not question.strip():
                raise ValueError(f"Selected {language} row has no question.")
            if not isinstance(gold_sql, str) or not gold_sql.strip():
                raise ValueError(f"Selected {language} row has no gold SQL.")
            groups[key][language] = IndicDBQuery(
                language=language,
                pair_id=key[0],
                question=question.strip(),
                gold_sql=gold_sql.strip(),
                dataset_name=key[1],
            )

    for key, languages in groups.items():
        if set(languages) != set(INDICDB_LANGUAGE_FILES):
            raise ValueError(f"Selected key {key!r} is not present in all seven languages.")
        if len({query.gold_sql for query in languages.values()}) != 1:
            raise ValueError(f"Selected key {key!r} has nonidentical gold SQL.")
    return groups


def load_schema_catalog(
    dsn: str, archive_path: Path
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Load all released IndicDB schema metadata without exposing benchmark labels."""
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("Install the indicdb project extra before evaluation.") from exc

    schema_mappings = build_schema_mapping(archive_path)
    config_by_postgres_name = {
        mapping["postgres_schema_name"]: load_schema_config(
            archive_path, mapping["archive_schema_name"]
        )
        for mapping in schema_mappings.values()
    }
    connection = psycopg2.connect(dsn)
    try:
        connection.set_session(readonly=True, autocommit=False)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_schema, table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema LIKE 'india_%'
                ORDER BY table_schema, table_name, ordinal_position
                """
            )
            rows = cursor.fetchall()
        connection.rollback()
    finally:
        connection.close()

    contexts: dict[str, dict[str, Any]] = {}
    for schema_name, table_name, column_name, data_type, is_nullable in rows:
        schema = contexts.setdefault(
            schema_name,
            {
                "dialect": "postgres",
                "schema_name": schema_name,
                "description": f"IndicDB schema {schema_name}",
                "tables": {},
            },
        )
        table = schema["tables"].setdefault(
            table_name,
            {"description": "", "columns": {}, "foreign_keys": [], "sample_values": {}},
        )
        nullable = " nullable" if is_nullable == "YES" else " not null"
        table["columns"][column_name] = f"{data_type}{nullable}"

    if set(contexts) != set(config_by_postgres_name):
        raise ValueError("Restored IndicDB schemas do not match released archive schemas.")
    enriched = {
        schema_name: enrich_schema_context(schema, config_by_postgres_name[schema_name])
        for schema_name, schema in contexts.items()
    }
    return enriched, schema_mappings


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


def _query_record(
    *,
    query: IndicDBQuery,
    expected_schema: str,
    selected_schema: str | None,
    generated_sql: str,
    sql_valid: bool,
    prediction_error: str | None,
    prediction_result: dict[str, Any] | None,
    gold_error: str | None,
    gold_result: dict[str, Any] | None,
    latency_ms: float,
) -> dict[str, Any]:
    execution_match = None
    if gold_result is not None and prediction_result is not None:
        execution_match = _normalized_rows(gold_result["rows"]) == _normalized_rows(
            prediction_result["rows"]
        )
    return {
        "language": query.language,
        "pair_id": query.pair_id,
        "benchmark_dataset_name": query.dataset_name,
        "expected_postgres_schema": expected_schema,
        "selected_postgres_schema": selected_schema,
        "schema_selection_correct": (
            selected_schema == expected_schema if selected_schema is not None else False
        ),
        "generated_sql": generated_sql,
        "sql_valid": sql_valid,
        "gold_error": gold_error,
        "prediction_error": prediction_error,
        "prediction_execution_success": (
            prediction_result is not None and prediction_error is None
        ),
        "gold_row_count": gold_result["row_count"] if gold_result is not None else None,
        "prediction_row_count": (
            prediction_result["row_count"] if prediction_result is not None else None
        ),
        "gold_empty": bool(gold_result is not None and not gold_result["rows"]),
        "prediction_empty": bool(prediction_result is not None and not prediction_result["rows"]),
        "execution_match": execution_match,
        "pipeline_latency_ms": round(latency_ms, 3),
    }


def evaluate_sealed_set(
    *,
    parquet_dir: Path,
    archive_path: Path,
    selected_keys: list[dict[str, str]],
    sandbox: PostgresSandbox,
    dsn: str,
    ollama_url: str,
    model_name: str,
    lock: dict[str, Any],
) -> dict[str, Any]:
    schema_contexts, mappings = load_schema_catalog(dsn, archive_path)
    # Keep one full context per schema for synthesis, separate from the metadata
    # catalog supplied to the automatic schema router.
    full_contexts: dict[str, dict[str, Any]] = {}
    config_by_postgres_name = {
        mapping["postgres_schema_name"]: load_schema_config(
            archive_path, mapping["archive_schema_name"]
        )
        for mapping in mappings.values()
    }
    groups = load_selected_queries(parquet_dir, selected_keys)
    records: list[dict[str, Any]] = []
    gold_results: dict[tuple[str, str], tuple[dict[str, Any] | None, str | None]] = {}

    for key, language_queries in groups.items():
        pair_id, benchmark_schema = key
        schema_mapping = mappings.get(benchmark_schema)
        if schema_mapping is None:
            raise ValueError(f"Selected schema {benchmark_schema!r} has no verified mapping.")
        expected_schema = schema_mapping["postgres_schema_name"]
        reference_query = language_queries[next(iter(INDICDB_LANGUAGE_FILES))]
        try:
            gold_result = sandbox.execute_query(reference_query.gold_sql, expected_schema)
            gold_error = None
        except Exception as exc:
            gold_result = None
            gold_error = f"{type(exc).__name__}: {exc}"
        gold_results[key] = (gold_result, gold_error)

        for language in INDICDB_LANGUAGE_FILES:
            query = language_queries[language]
            started = perf_counter()
            selected_schema: str | None = None
            generated_sql = ""
            sql_valid = False
            prediction_error: str | None = None
            prediction_result: dict[str, Any] | None = None
            try:
                selected_schema = select_schema(
                    query.question,
                    schema_contexts,
                    model_name=model_name,
                    ollama_url=ollama_url,
                )
                if selected_schema not in full_contexts:
                    full_contexts[selected_schema] = enrich_schema_context(
                        sandbox.get_schema_context(selected_schema),
                        config_by_postgres_name[selected_schema],
                    )
                state = execute_indicsql_pipeline(
                    query.question,
                    query_id=f"indicdb-sealed-{language}-{pair_id}",
                    database_schema_name=selected_schema,
                    database_schema=full_contexts[selected_schema],
                    database_schema_source="automatic_model_schema_router",
                    language_override=language,
                    sandbox=sandbox,
                )
                generated_sql = state.get("generated_sql", "")
                sql_valid = bool(state.get("syntax_valid")) and bool(generated_sql)
                prediction_error = state.get("execution_error") or state.get("schema_linking_error")
                prediction_result = state.get("execution_result")
            except Exception as exc:
                prediction_error = f"{type(exc).__name__}: {exc}"
            elapsed_ms = (perf_counter() - started) * 1000
            gold_result, gold_error = gold_results[key]
            records.append(
                _query_record(
                    query=query,
                    expected_schema=expected_schema,
                    selected_schema=selected_schema,
                    generated_sql=generated_sql,
                    sql_valid=sql_valid,
                    prediction_error=prediction_error,
                    prediction_result=prediction_result,
                    gold_error=gold_error,
                    gold_result=gold_result,
                    latency_ms=elapsed_ms,
                )
            )

    languages = list(INDICDB_LANGUAGE_FILES)
    language_metrics: dict[str, dict[str, Any]] = {}
    for language in languages:
        language_rows = [row for row in records if row["language"] == language]
        comparable = [row for row in language_rows if row["execution_match"] is not None]
        count = len(language_rows)
        language_metrics[language] = {
            "queries": count,
            "schema_selection_accuracy": (
                sum(row["schema_selection_correct"] for row in language_rows) / count
                if count
                else None
            ),
            "sql_validity_rate": (
                sum(row["sql_valid"] for row in language_rows) / count if count else None
            ),
            "prediction_execution_success_rate": (
                sum(row["prediction_execution_success"] for row in language_rows) / count
                if count
                else None
            ),
            "comparable_queries": len(comparable),
            "execution_accuracy": (
                sum(row["execution_match"] is True for row in comparable) / len(comparable)
                if comparable
                else None
            ),
            "mean_pipeline_latency_ms": (
                sum(row["pipeline_latency_ms"] for row in language_rows) / count if count else None
            ),
        }

    sealed_manifest = json.loads(Path(lock["sealed_manifest"]["path"]).read_text(encoding="utf-8"))
    return {
        "artifact_type": "IndicDB sealed final prediction audit",
        "official_benchmark_result": False,
        "benchmark_source": "Official IndicDB pinned revision",
        "evaluation_scope": "Sealed mapped-schema subset; unresolved schemas are excluded.",
        "final_run_lock_sha256": hashlib.sha256(
            json.dumps(lock, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest(),
        "benchmark_revision": lock["sealed_manifest"]["benchmark_revision"],
        "schema_selection_mode": "automatic_model_router",
        "benchmark_schema_label_exposed_to_predictor": False,
        "model": lock["runtime"]["model"],
        "sampling": {
            "temperature": INFERENCE_TEMPERATURE,
            "seed": INFERENCE_SEED,
        },
        "postgresql": lock["runtime"]["postgresql"],
        "selected_groups": len(selected_keys),
        "selected_questions": len(records),
        "languages": languages,
        "excluded_unresolved_schema_names": sealed_manifest.get(
            "excluded_unresolved_schema_names", []
        ),
        "eligible_group_exclusions": sealed_manifest.get("eligible_group_exclusions", {}),
        "language_metrics": language_metrics,
        "gold_execution_error_count": sum(error is not None for _, error in gold_results.values()),
        "records": records,
        "records_include_original_question_or_gold_sql": False,
        "result_equivalence": (
            "Order-independent comparison of normalized result rows; numeric values rounded to 6 decimals."
        ),
        "limitations": [
            "Execution equivalence is not a native-speaker semantic or gold-SQL correctness review.",
            "Unresolved schema names remain excluded as stated in the sealed manifest.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--parquet-dir", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument(
        "--sealed-manifest",
        type=Path,
        default=REPO_ROOT / "data/benchmarks/indicdb_final_sealed_manifest.json",
    )
    parser.add_argument("--sealed-key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dsn-env", default="INDICDB_DSN")
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--container", default="indicdb-official-audit-20261117")
    args = parser.parse_args()

    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        parser.error(f"Set {args.dsn_env} to the private read-only PostgreSQL DSN.")
    lock = validate_final_run_lock(
        lock_path=args.lock,
        parquet_dir=args.parquet_dir,
        archive_path=args.archive,
        sealed_manifest_path=args.sealed_manifest,
        dsn=dsn,
        model_name=args.model,
        ollama_url=args.ollama_url,
        container_name=args.container,
    )
    if _ollama_client.model_name != args.model or not _ollama_client.is_available:
        raise RuntimeError("The locked Ollama model is not active in the SQL synthesizer.")
    if _ollama_client.base_url.rstrip("/") != args.ollama_url.rstrip("/"):
        raise RuntimeError("The SQL synthesizer endpoint differs from the locked Ollama endpoint.")

    # The sealed key file is deliberately opened only after the lock validates.
    selected_keys = _load_selected_keys(
        args.sealed_key_file,
        lock["sealed_manifest"]["selected_key_sha256"],
        lock["sealed_manifest"]["group_count"],
    )
    sandbox = PostgresSandbox(dsn, statement_timeout_ms=30000)
    try:
        report = evaluate_sealed_set(
            parquet_dir=args.parquet_dir,
            archive_path=args.archive,
            selected_keys=selected_keys,
            sandbox=sandbox,
            dsn=dsn,
            ollama_url=args.ollama_url,
            model_name=args.model,
            lock=lock,
        )
    finally:
        sandbox.close()

    if report["selected_questions"] != lock["sealed_manifest"]["question_count"]:
        raise ValueError(
            "Evaluation did not produce the sealed manifest's expected question count."
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_output.replace(args.output)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "selected_groups": report["selected_groups"],
                "selected_questions": report["selected_questions"],
                "language_metrics": report["language_metrics"],
                "gold_execution_error_count": report["gold_execution_error_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
