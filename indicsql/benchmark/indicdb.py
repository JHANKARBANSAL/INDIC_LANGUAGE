"""Load aligned IndicDBBench questions from the downloaded language Parquets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from zipfile import ZipFile

import pandas as pd

INDICDB_LANGUAGE_FILES = {
    "en": "test_english.parquet",
    "hi": "test_hindi.parquet",
    "hi-en": "test_hinglish.parquet",
    "mr": "test_marathi.parquet",
    "ta": "test_tamil.parquet",
    "te": "test_telugu.parquet",
    "bn": "test_bengali.parquet",
}


@dataclass(frozen=True)
class IndicDBQuery:
    language: str
    pair_id: str
    question: str
    gold_sql: str
    dataset_name: str


def load_aligned_indicdb_queries(
    parquet_dir: str | Path,
) -> tuple[Dict[str, List[IndicDBQuery]], List[tuple[str, str]]]:
    """Load valid SQL rows and retain pair IDs present in all seven languages."""
    root = Path(parquet_dir)
    queries_by_language: dict[str, dict[str, IndicDBQuery]] = {}

    for language, filename in INDICDB_LANGUAGE_FILES.items():
        path = root / filename
        if not path.is_file():
            raise FileNotFoundError(f"IndicDBBench Parquet not found: {path}")

        frame = pd.read_parquet(
            path, columns=["question", "sql", "pair_id", "dataset_name"]
        )
        frame = frame.dropna(subset=["pair_id", "question", "dataset_name"])
        frame["pair_id"] = frame["pair_id"].astype(str).str.strip()
        frame["question"] = frame["question"].astype(str).str.strip()
        frame["sql"] = frame["sql"].fillna("").astype(str).str.strip()
        frame["dataset_name"] = frame["dataset_name"].astype(str).str.strip()

        language_queries: dict[tuple[str, str], IndicDBQuery] = {}
        for (pair_id, dataset_name), group in frame.groupby(
            ["pair_id", "dataset_name"], sort=False
        ):
            valid_sql = list(dict.fromkeys(sql for sql in group["sql"] if sql))
            questions = [question for question in group["question"] if question]
            if not pair_id or not dataset_name or not valid_sql or not questions:
                continue
            if len(valid_sql) != 1:
                raise ValueError(
                    f"{path.name} has conflicting gold SQL for pair "
                    f"{pair_id} in {dataset_name}."
                )
            language_queries[(pair_id, dataset_name)] = IndicDBQuery(
                language=language,
                pair_id=pair_id,
                question=questions[0],
                gold_sql=valid_sql[0],
                dataset_name=dataset_name,
            )
        queries_by_language[language] = language_queries

    common_query_keys = sorted(
        set.intersection(*(set(items) for items in queries_by_language.values()))
    )
    aligned = {
        language: [items[key] for key in common_query_keys]
        for language, items in queries_by_language.items()
    }

    for pair_id, dataset_name in common_query_keys:
        rows = [items[(pair_id, dataset_name)] for items in queries_by_language.values()]
        if len({row.gold_sql for row in rows}) != 1:
            raise ValueError(
                f"IndicDBBench pair {pair_id} in {dataset_name} has different gold SQL by language."
            )

    return aligned, common_query_keys


def load_schema_config(archive_path: str | Path, schema_name: str) -> dict:
    """Load one database's released schema metadata from the supplied archive."""
    import yaml

    with ZipFile(archive_path) as archive:
        config_paths = [
            path
            for path in archive.namelist()
            if path.endswith("/schema_config.yaml")
        ]
        for config_path in config_paths:
            config = yaml.safe_load(archive.read(config_path))
            if config.get("database_name") == schema_name:
                return config
    raise ValueError(f"No schema config for {schema_name!r} in {archive_path}.")


def enrich_schema_context(schema_context: dict, config: dict) -> dict:
    """Add released table descriptions and declared relationships to DB metadata."""
    table_specs = {
        **(config.get("dimension_tables") or {}),
        **(config.get("fact_tables") or {}),
    }
    descriptions = config.get("table_descriptions") or {}
    tables = schema_context.get("tables", {})
    for table_name, table in tables.items():
        spec = table_specs.get(table_name.upper(), {})
        table["description"] = descriptions.get(table_name.upper(), "")
        table["primary_key"] = spec.get("key_column", "").lower()
        declared = [
            f"{foreign_key['column'].lower()} references "
            f"{foreign_key['references'].lower()}."
            f"{table_specs.get(foreign_key['references'], {}).get('key_column', '').lower()}"
            for foreign_key in spec.get("foreign_keys") or []
        ]
        table["foreign_keys"] = list(dict.fromkeys(table.get("foreign_keys", []) + declared))
    return schema_context
