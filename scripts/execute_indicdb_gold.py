#!/usr/bin/env python3
# ruff: noqa: I001
"""Execute pinned IndicDB gold SQL against a restored official dump.

This is an execution audit, not an answer-correctness proof.  It only maps the
two 2005 IHDS benchmark names whose sole difference from the archive config is
a trailing underscore; the archive paths, config names, DDL tables, and dump
catalog all identify the same source.  The UDISE school-profiles name remains
unmapped intentionally.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd
import psycopg2
from psycopg2 import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.preflight_indicdb_benchmark import _archive_schema_tables, _parse_sql
from scripts.verify_indicdb_sources import MANIFEST_PATH, verify_indicdb_sources


DIRECT_SCHEMA_MAPPINGS = {
    "INDIA_IHDS_2005_HOUSEHOLD_SURVEY_": "INDIA_IHDS_2005_HOUSEHOLD_SURVEY",
    "INDIA_IHDS_2005_INDIVIDUAL_SURVEY_": "INDIA_IHDS_2005_INDIVIDUAL_SURVEY",
}


def build_schema_mapping(archive_path: Path) -> dict[str, dict[str, str]]:
    """Return only archive-backed benchmark-to-PostgreSQL schema mappings."""
    archive_tables = _archive_schema_tables(archive_path)
    mappings = {
        name: {
            "archive_schema_name": name,
            "postgres_schema_name": name.lower(),
            "mapping_kind": "exact_archive_config_name",
        }
        for name in archive_tables
    }
    for benchmark_name, archive_name in DIRECT_SCHEMA_MAPPINGS.items():
        if archive_name not in archive_tables:
            raise ValueError(f"Required IHDS archive schema is absent: {archive_name}")
        mappings[benchmark_name] = {
            "archive_schema_name": archive_name,
            "postgres_schema_name": archive_name.lower(),
            "mapping_kind": "trailing_underscore_verified_against_archive_and_dump",
        }
    return mappings


def _parquet_path(parquet_root: Path, relative_name: str) -> Path:
    nested = parquet_root / relative_name
    if nested.is_file():
        return nested
    flat = parquet_root / Path(relative_name).name
    if flat.is_file():
        return flat
    raise FileNotFoundError(f"IndicDB Parquet not found below {parquet_root}: {relative_name}")


def _catalog_tables(connection: Any) -> dict[str, set[str]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE' AND table_schema LIKE 'india_%'
            ORDER BY table_schema, table_name
            """
        )
        result: dict[str, set[str]] = defaultdict(set)
        for schema_name, table_name in cursor.fetchall():
            result[schema_name].add(table_name)
        return dict(result)


def _table_row_counts(connection: Any, catalog: dict[str, set[str]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    with connection.cursor() as cursor:
        for schema_name, tables in catalog.items():
            counts[schema_name] = {}
            for table_name in sorted(tables):
                cursor.execute(
                    sql.SQL("SELECT count(*) FROM {}.{}").format(
                        sql.Identifier(schema_name), sql.Identifier(table_name)
                    )
                )
                counts[schema_name][table_name] = int(cursor.fetchone()[0])
    return counts


def execute_gold_sql(
    *,
    parquet_root: Path,
    archive_path: Path,
    dsn: str,
    statement_timeout_ms: int,
    manifest_path: Path = MANIFEST_PATH,
) -> dict[str, Any]:
    """Run each parse-valid, archive-mapped gold query in a read-only transaction."""
    source_audit = verify_indicdb_sources(
        parquet_dir=parquet_root,
        download=False,
        archive_path=archive_path,
        manifest_path=manifest_path,
    )
    if not source_audit["source_artifacts_verified"]:
        raise ValueError("Source verification failed; refusing gold SQL execution.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive_tables = _archive_schema_tables(archive_path)
    mappings = build_schema_mapping(archive_path)
    connection = psycopg2.connect(dsn)
    try:
        catalog = _catalog_tables(connection)
        mapped_catalog_checks: dict[str, dict[str, Any]] = {}
        for benchmark_name, mapping in mappings.items():
            archive_name = mapping["archive_schema_name"]
            postgres_name = mapping["postgres_schema_name"]
            expected = archive_tables[archive_name]
            actual = catalog.get(postgres_name, set())
            mapped_catalog_checks[benchmark_name] = {
                **mapping,
                "archive_ddl_tables": len(expected),
                "restored_catalog_tables": len(actual),
                "missing_from_restored_catalog": sorted(expected - actual),
                "unexpected_in_restored_catalog": sorted(actual - expected),
            }
        bad_catalogs = [
            name
            for name, check in mapped_catalog_checks.items()
            if check["missing_from_restored_catalog"]
            or check["unexpected_in_restored_catalog"]
        ]
        if bad_catalogs:
            raise ValueError(
                "Restored catalog does not match archive DDL for: " + ", ".join(bad_catalogs)
            )

        table_rows = _table_row_counts(connection, catalog)
        connection.commit()
        records: list[dict[str, Any]] = []
        schema_metrics: dict[str, Counter[str]] = defaultdict(Counter)
        unmapped_rows: Counter[str] = Counter()
        for language, file_spec in manifest["benchmark"]["files"].items():
            frame = pd.read_parquet(
                _parquet_path(parquet_root, file_spec["path"]),
                columns=["sql", "pair_id", "dataset_name"],
            )
            for row in frame.fillna("").itertuples(index=False):
                query_text, pair_id, benchmark_schema = map(lambda value: str(value).strip(), row)
                if not query_text:
                    continue
                _tree, parse_error = _parse_sql(query_text)
                if parse_error:
                    raise ValueError(f"Pinned gold SQL unexpectedly failed parsing: {parse_error}")
                mapping = mappings.get(benchmark_schema)
                if mapping is None:
                    unmapped_rows[benchmark_schema] += 1
                    continue
                postgres_schema = mapping["postgres_schema_name"]
                started = perf_counter()
                error = None
                row_count = None
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SET TRANSACTION READ ONLY")
                        cursor.execute("SET LOCAL statement_timeout = %s", (statement_timeout_ms,))
                        cursor.execute(
                            sql.SQL("SET LOCAL search_path TO {}").format(
                                sql.Identifier(postgres_schema)
                            )
                        )
                        cursor.execute(query_text)
                        row_count = len(cursor.fetchall())
                    connection.rollback()
                except Exception as exc:  # Individual benchmark errors are audit results.
                    connection.rollback()
                    error = f"{type(exc).__name__}: {exc}"
                elapsed_ms = round((perf_counter() - started) * 1000, 3)
                records.append(
                    {
                        "language": language,
                        "pair_id": pair_id,
                        "benchmark_schema_name": benchmark_schema,
                        "postgres_schema_name": postgres_schema,
                        "gold_sql": query_text,
                        "row_count": row_count,
                        "empty_result": row_count == 0 if row_count is not None else False,
                        "error": error,
                        "elapsed_ms": elapsed_ms,
                    }
                )
                metric = schema_metrics[benchmark_schema]
                metric["queries_attempted"] += 1
                if error:
                    metric["execution_errors"] += 1
                else:
                    metric["execution_successes"] += 1
                    metric["empty_results"] += row_count == 0
                    metric["result_rows"] += row_count or 0

        errors = [record for record in records if record["error"]]
        empty_results = [record for record in records if record["empty_result"]]
        return {
            "artifact_type": "IndicDB pinned gold SQL execution audit",
            "official_benchmark_result": False,
            "gold_sql_execution_verified": not errors,
            "semantic_correctness_verified": False,
            "statement_timeout_ms": statement_timeout_ms,
            "source_artifacts_verified": source_audit["source_artifacts_verified"],
            "restored_database": {
                "catalog_schema_count": len(catalog),
                "catalog_table_count": sum(map(len, catalog.values())),
                "table_row_counts": table_rows,
                "total_table_rows": sum(
                    count for tables in table_rows.values() for count in tables.values()
                ),
            },
            "schema_mappings": mapped_catalog_checks,
            "unresolved_benchmark_schema_rows": dict(sorted(unmapped_rows.items())),
            "schema_coverage": {
                name: dict(metrics) for name, metrics in sorted(schema_metrics.items())
            },
            "queries_attempted": len(records),
            "execution_error_count": len(errors),
            "empty_result_count": len(empty_results),
            "execution_errors": errors,
            "empty_results": empty_results,
            "records": records,
            "limitations": [
                "Successful execution does not prove a gold query is semantically correct.",
                "INDIA_UDISE_SCHOOL_PROFILES remains unmapped because no direct archive identity was demonstrated.",
                "The exact IndicDB benchmark license subtype remains unresolved.",
            ],
        }
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--statement-timeout-ms", type=int, default=5000)
    args = parser.parse_args()
    if args.statement_timeout_ms < 1:
        parser.error("--statement-timeout-ms must be positive.")
    report = execute_gold_sql(
        parquet_root=args.parquet_dir,
        archive_path=args.archive,
        dsn=args.dsn,
        statement_timeout_ms=args.statement_timeout_ms,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "queries_attempted": report["queries_attempted"],
                "execution_error_count": report["execution_error_count"],
                "empty_result_count": report["empty_result_count"],
                "unresolved_benchmark_schema_rows": report["unresolved_benchmark_schema_rows"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
