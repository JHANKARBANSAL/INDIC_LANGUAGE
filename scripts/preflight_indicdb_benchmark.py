#!/usr/bin/env python3
"""Preflight the pinned IndicDB gold SQL and cross-language benchmark alignment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pandas as pd
import sqlglot
from sqlglot import exp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.verify_indicdb_sources import MANIFEST_PATH, verify_indicdb_sources


def _archive_schema_tables(archive_path: Path) -> dict[str, set[str]]:
    import yaml

    schemas: dict[str, set[str]] = {}
    with ZipFile(archive_path) as archive:
        for config_path in archive.namelist():
            if not config_path.endswith("/schema_config.yaml"):
                continue
            config = yaml.safe_load(archive.read(config_path))
            schema_name = config["database_name"]
            ddl_path = f"{config_path.rsplit('/', 1)[0]}/DDL.csv"
            if ddl_path not in archive.namelist():
                raise ValueError(f"Missing DDL.csv for schema {schema_name!r}.")
            ddl = pd.read_csv(archive.open(ddl_path), usecols=["table_name"])
            schemas[schema_name] = {
                str(table).strip().lower() for table in ddl["table_name"].dropna()
            }
    return schemas


def _parse_sql(sql: str) -> tuple[exp.Expression | None, str | None]:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        return None, str(exc).splitlines()[0]
    if len(statements) != 1 or not isinstance(statements[0], exp.Query):
        return None, "Gold SQL must contain exactly one query statement."
    return statements[0], None


def _referenced_tables(tree: exp.Expression) -> set[str]:
    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    return {
        table.name.lower()
        for table in tree.find_all(exp.Table)
        if table.name and table.name.lower() not in cte_names
    }


def build_gold_preflight(
    parquet_dir: Path,
    archive_path: Path,
    *,
    manifest_path: Path = MANIFEST_PATH,
    dump_path: Path | None = None,
) -> dict[str, Any]:
    source_audit = verify_indicdb_sources(
        parquet_dir=parquet_dir,
        download=False,
        manifest_path=manifest_path,
        archive_path=archive_path,
        dump_path=dump_path,
    )
    if not source_audit["source_artifacts_verified"]:
        raise ValueError("Source verification failed; refusing gold benchmark preflight.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schemas = _archive_schema_tables(archive_path)
    split_metrics: dict[str, dict[str, Any]] = {}
    keys_by_language: dict[str, dict[tuple[str, str], set[str]]] = {}
    original_ids_by_language: dict[str, set[tuple[str, str]]] = {}
    parse_error_examples: list[dict[str, str]] = []
    unresolved_schema_rows: list[dict[str, str]] = []
    unknown_table_examples: list[dict[str, Any]] = []
    total_rows = 0
    total_nonblank_sql = 0
    total_parse_valid = 0
    total_table_checked = 0
    total_table_valid = 0

    for language, file_spec in manifest["benchmark"]["files"].items():
        path = parquet_dir / Path(file_spec["path"]).name
        frame = pd.read_parquet(
            path,
            columns=[
                "question",
                "sql",
                "pair_id",
                "original_question_id",
                "dataset_name",
            ],
        )
        frame["sql"] = frame["sql"].fillna("").astype(str).str.strip()
        frame["pair_id"] = frame["pair_id"].fillna("").astype(str).str.strip()
        frame["dataset_name"] = (
            frame["dataset_name"].fillna("").astype(str).str.strip()
        )
        frame["original_question_id"] = (
            frame["original_question_id"].fillna("").astype(str).str.strip()
        )
        nonblank = frame["sql"].ne("")
        duplicate_mask = frame.duplicated(
            subset=["pair_id", "dataset_name"], keep="first"
        )
        language_keys: dict[tuple[str, str], set[str]] = {}
        language_original_ids: set[tuple[str, str]] = set()
        parse_valid_rows = 0
        parse_invalid_rows = 0
        table_checked_rows = 0
        table_valid_rows = 0
        unknown_table_rows = 0
        conflicting_keys = 0

        for (pair_id, schema_name), group in frame[nonblank].groupby(
            ["pair_id", "dataset_name"], sort=False
        ):
            key = (str(pair_id), str(schema_name))
            sql_values = set(group["sql"])
            language_keys[key] = sql_values
            if len(sql_values) > 1:
                conflicting_keys += 1
            for original_id in group["original_question_id"]:
                if original_id:
                    language_original_ids.add((original_id, str(schema_name)))

        for index, row in frame[nonblank].iterrows():
            tree, error = _parse_sql(row["sql"])
            if error:
                parse_invalid_rows += 1
                if len(parse_error_examples) < 20:
                    parse_error_examples.append(
                        {
                            "language": language,
                            "pair_id": row["pair_id"],
                            "dataset_name": row["dataset_name"],
                            "error": error,
                        }
                    )
                continue
            parse_valid_rows += 1
            schema_tables = schemas.get(row["dataset_name"])
            if schema_tables is None:
                if len(unresolved_schema_rows) < 20:
                    unresolved_schema_rows.append(
                        {
                            "language": language,
                            "pair_id": row["pair_id"],
                            "dataset_name": row["dataset_name"],
                        }
                    )
                continue
            table_checked_rows += 1
            referenced = _referenced_tables(tree)
            missing_tables = sorted(referenced - schema_tables)
            if missing_tables:
                unknown_table_rows += 1
                if len(unknown_table_examples) < 20:
                    unknown_table_examples.append(
                        {
                            "language": language,
                            "pair_id": row["pair_id"],
                            "dataset_name": row["dataset_name"],
                            "unknown_tables": missing_tables,
                        }
                    )
            else:
                table_valid_rows += 1

        keys_by_language[language] = language_keys
        original_ids_by_language[language] = language_original_ids
        split_metrics[language] = {
            "physical_rows": len(frame),
            "nonblank_gold_sql_rows": int(nonblank.sum()),
            "blank_gold_sql_rows": int((~nonblank).sum()),
            "distinct_pair_schema_keys_with_gold_sql": len(language_keys),
            "repeated_pair_schema_rows": int(duplicate_mask.sum()),
            "conflicting_gold_sql_keys": conflicting_keys,
            "gold_sql_parse_valid_rows": parse_valid_rows,
            "gold_sql_parse_invalid_rows": parse_invalid_rows,
            "rows_with_exact_schema_config": table_checked_rows,
            "rows_with_all_table_references_resolved": table_valid_rows,
            "rows_with_unknown_table_references": unknown_table_rows,
        }
        total_rows += len(frame)
        total_nonblank_sql += int(nonblank.sum())
        total_parse_valid += parse_valid_rows
        total_table_checked += table_checked_rows
        total_table_valid += table_valid_rows

    common_pair_schema_keys = set.intersection(
        *(set(items) for items in keys_by_language.values())
    )
    identical_gold_sql_keys = sum(
        all(len(keys_by_language[language][key]) == 1 for language in keys_by_language)
        and len(
            {
                next(iter(keys_by_language[language][key]))
                for language in keys_by_language
            }
        )
        == 1
        for key in common_pair_schema_keys
    )
    common_original_question_keys = set.intersection(
        *original_ids_by_language.values()
    )

    return {
        "artifact_type": "IndicDB pinned gold benchmark preflight",
        "benchmark_repo_id": source_audit["benchmark_repo_id"],
        "benchmark_revision": source_audit["benchmark_revision"],
        "source_artifacts_verified": source_audit["source_artifacts_verified"],
        "physical_rows": total_rows,
        "nonblank_gold_sql_rows": total_nonblank_sql,
        "gold_sql_parse_valid_rows": total_parse_valid,
        "gold_sql_parse_invalid_rows": total_nonblank_sql - total_parse_valid,
        "parse_error_examples": parse_error_examples,
        "database_schema_name_coverage": source_audit["source_archive"],
        "language_splits": split_metrics,
        "cross_language_alignment": {
            "pair_schema_keys_per_language": {
                language: len(keys) for language, keys in keys_by_language.items()
            },
            "common_pair_schema_keys_all_seven_languages": len(
                common_pair_schema_keys
            ),
            "common_keys_with_identical_gold_sql_all_languages": (
                identical_gold_sql_keys
            ),
            "common_original_question_schema_keys_all_seven_languages": len(
                common_original_question_keys
            ),
        },
        "table_reference_check": {
            "rows_checked_against_exact_schema_names": total_table_checked,
            "rows_with_all_referenced_tables_present": total_table_valid,
            "rows_with_unknown_table_references": (
                total_table_checked - total_table_valid
            ),
            "rows_skipped_due_to_schema_name_mismatch": (
                total_parse_valid - total_table_checked
            ),
            "unresolved_schema_examples": unresolved_schema_rows,
            "unknown_table_examples": unknown_table_examples,
        },
        "gold_sql_execution_verified": False,
        "human_language_review_verified": False,
        "card_reported_tasks": manifest["benchmark"]["card_claims"]["tasks"],
        "card_vs_file_row_count_matches": (
            total_rows == manifest["benchmark"]["card_claims"]["tasks"]
        ),
        "limitations": [
            "SQL parsing and table-name checks do not prove that gold SQL returns the intended answer.",
            "Gold SQL has not been executed because the PostgreSQL dump is not restored in this environment.",
            "Three benchmark schema names do not exactly match archive schema names and are not guessed or aliased.",
            "Native-speaker translation review has not been performed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet-dir", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--dump", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark_results/indicdb_gold_preflight.json"),
    )
    args = parser.parse_args()
    report = build_gold_preflight(
        args.parquet_dir,
        args.archive,
        dump_path=args.dump,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "physical_rows": report["physical_rows"],
                "gold_sql_parse_valid_rows": report["gold_sql_parse_valid_rows"],
                "gold_sql_parse_invalid_rows": report["gold_sql_parse_invalid_rows"],
                "common_pair_schema_keys_all_seven_languages": (
                    report["cross_language_alignment"][
                        "common_pair_schema_keys_all_seven_languages"
                    ]
                ),
                "rows_checked_against_exact_schema_names": (
                    report["table_reference_check"][
                        "rows_checked_against_exact_schema_names"
                    ]
                ),
                "rows_with_unknown_table_references": (
                    report["table_reference_check"][
                        "rows_with_unknown_table_references"
                    ]
                ),
                "gold_sql_execution_verified": report[
                    "gold_sql_execution_verified"
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
