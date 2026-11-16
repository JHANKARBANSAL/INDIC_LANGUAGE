#!/usr/bin/env python3
"""Rebuild a clearly labeled IndicDB variant from the archive's raw CSVs and YAML configs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pandas as pd
import yaml

SOURCE_ROW_INDEX = -1


def _normalize_value(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_integer_value(value: Any, table_name: str, column_name: str) -> str | None:
    normalized = _normalize_value(value)
    if normalized is None:
        return None
    if re.fullmatch(r"[+-]?\d+", normalized):
        return normalized
    if re.fullmatch(r"[+-]?\d+\.0+", normalized):
        return str(int(normalized.split(".", 1)[0]))
    raise ValueError(
        f"{table_name}.{column_name} has a non-integer source value: {normalized!r}"
    )


def _transform_value(value: Any, transform: str | None) -> str | None:
    normalized = _normalize_value(value)
    if normalized is None or transform is None:
        return normalized
    if transform == "extract_year":
        match = re.search(r"(?<!\d)(?:19|20)\d{2}(?!\d)", normalized)
        if match is None:
            raise ValueError(f"Cannot extract a four-digit year from {normalized!r}")
        return match.group(0)
    raise ValueError(f"Unsupported schema transform: {transform}")


def _natural_key(row: pd.Series, source_indexes: list[int]) -> tuple[str | None, ...]:
    return tuple(
        _normalize_value(row.name if index == SOURCE_ROW_INDEX else row.iloc[index])
        for index in source_indexes
    )


def _key_frame(source: pd.DataFrame, source_indexes: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            f"key_{position}": (
                source.index.to_series(index=source.index).map(_normalize_value)
                if index == SOURCE_ROW_INDEX
                else source.iloc[:, index].map(_normalize_value)
            )
            for position, index in enumerate(source_indexes)
        },
        index=source.index,
    )


def _align_frame_to_ddl(
    table_name: str,
    frame: pd.DataFrame,
    spec: dict[str, Any],
    ddl_columns: set[str],
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    frame_columns = {column.lower() for column in frame.columns}
    missing_columns = sorted(frame_columns - ddl_columns)
    required_columns = {spec["key_column"].lower()}
    required_columns.update(
        foreign_key["column"].lower()
        for foreign_key in spec.get("foreign_keys") or []
    )
    missing_required = sorted(
        (required_columns - frame_columns) | (required_columns - ddl_columns)
    )
    if missing_required:
        raise ValueError(
            f"{table_name} config maps required key columns absent from DDL: "
            f"{missing_required}"
        )
    aligned = frame.loc[
        :, [column for column in frame.columns if column.lower() in ddl_columns]
    ].copy()
    return aligned, {
        "config_columns_absent_from_ddl": missing_columns,
        "ddl_columns_without_config_mapping": sorted(ddl_columns - frame_columns),
    }


def _effective_dimension_indexes(
    table_name: str,
    dimensions: dict[str, dict[str, Any]],
    facts: dict[str, dict[str, Any]],
    cache: dict[str, list[int]],
    visiting: set[str] | None = None,
) -> list[int]:
    if table_name in cache:
        return cache[table_name]
    if visiting is None:
        visiting = set()
    if table_name in visiting:
        raise ValueError(f"Cyclic dimension foreign keys cannot be reconstructed: {table_name}")
    visiting.add(table_name)

    spec = dimensions[table_name]
    indexes = list(spec.get("dedup_columns") or [])
    if not indexes:
        if "key_source_index" in spec:
            indexes = [spec["key_source_index"]]
        else:
            indexes = [SOURCE_ROW_INDEX]
    for foreign_key in spec.get("foreign_keys") or []:
        parent_table = foreign_key["references"]
        if parent_table == table_name:
            continue
        if parent_table in dimensions:
            indexes.extend(
                _effective_dimension_indexes(
                    parent_table, dimensions, facts, cache, visiting
                )
            )
        elif parent_table in facts:
            indexes.append(SOURCE_ROW_INDEX)
        else:
            raise ValueError(
                f"{table_name}.{foreign_key['column']} references unknown table {parent_table}"
            )

    effective_indexes = list(dict.fromkeys(indexes))
    for index in effective_indexes:
        if index != SOURCE_ROW_INDEX and index < 0:
            raise ValueError(f"{table_name} has invalid source index {index}")
    visiting.remove(table_name)
    cache[table_name] = effective_indexes
    return effective_indexes


def _ambiguous_parent_count(
    source: pd.DataFrame,
    child_indexes: list[int],
    parent_indexes: list[int],
) -> int:
    child_columns = [f"child_{index}" for index in range(len(child_indexes))]
    parent_columns = [f"parent_{index}" for index in range(len(parent_indexes))]
    key_data = _key_frame(source, child_indexes + parent_indexes)
    key_data.columns = child_columns + parent_columns
    pairs = key_data.drop_duplicates()
    counts = pairs.groupby(child_columns, dropna=False).size()
    return int((counts > 1).sum())


def build_table_frames(
    source: pd.DataFrame, config: dict[str, Any]
) -> tuple[
    dict[str, pd.DataFrame],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, list[int]],
]:
    """Build normalized table frames using the released config's declared keys."""
    source = source.reset_index(drop=True)
    dimensions: dict[str, dict[str, Any]] = config.get("dimension_tables") or {}
    facts: dict[str, dict[str, Any]] = config.get("fact_tables") or {}
    dimension_rows: dict[str, pd.DataFrame] = {}
    dimension_lookups: dict[str, dict[tuple[str | None, ...], str | None]] = {}
    dimension_keys: dict[str, list[str | None]] = {}
    unresolved_self_references: list[dict[str, Any]] = []
    ambiguous_relations: list[dict[str, Any]] = []
    fact_row_links: list[dict[str, Any]] = []
    fact_keys: dict[str, list[str | None]] = {}
    effective_dimension_indexes = {
        table_name: _effective_dimension_indexes(table_name, dimensions, facts, {})
        for table_name in dimensions
    }

    for table_name, spec in facts.items():
        if "key_source_index" in spec:
            key_index = spec["key_source_index"]
            if not 0 <= key_index < source.shape[1]:
                raise ValueError(f"{table_name} key source index {key_index} is out of range")
            keys = [
                _transform_value(value, spec.get("key_transform"))
                for value in source.iloc[:, key_index]
            ]
        else:
            keys = [str(index) for index in range(1, len(source) + 1)]
        if any(key is None for key in keys) or len(set(keys)) != len(keys):
            raise ValueError(
                f"{table_name} generated duplicate or null values for {spec['key_column']}"
            )
        fact_keys[table_name] = keys

    for table_name, spec in dimensions.items():
        dedup_indexes = effective_dimension_indexes[table_name]
        for index in dedup_indexes:
            if index != SOURCE_ROW_INDEX and not 0 <= index < source.shape[1]:
                raise ValueError(f"{table_name} dedup source index {index} is out of range")

        key_frame = _key_frame(source, dedup_indexes)
        keep = ~key_frame.duplicated(keep="first")
        representatives = source.loc[keep]
        key_column = spec["key_column"]
        if "key_source_index" in spec:
            key_index = spec["key_source_index"]
            if not 0 <= key_index < source.shape[1]:
                raise ValueError(f"{table_name} key source index {key_index} is out of range")
            keys = [
                _transform_value(value, spec.get("key_transform"))
                for value in representatives.iloc[:, key_index]
            ]
        else:
            keys = [str(index) for index in range(1, len(representatives) + 1)]
        if any(key is None for key in keys) or len(set(keys)) != len(keys):
            raise ValueError(f"{table_name} generated duplicate or null values for {key_column}")

        lookup: dict[tuple[str | None, ...], str | None] = {}
        for _, row in representatives.iterrows():
            natural_key = _natural_key(row, dedup_indexes)
            lookup[natural_key] = keys[len(lookup)]
        dimension_rows[table_name] = representatives
        dimension_lookups[table_name] = lookup
        dimension_keys[table_name] = keys

    def resolve_foreign_key(
        table_name: str,
        column: str,
        parent_table: str,
        rows: pd.DataFrame,
    ) -> list[str | None]:
        if parent_table == table_name:
            unresolved_self_references.append(
                {
                    "table": table_name,
                    "column": column,
                    "reason": "The release config provides no source mapping for this self-reference.",
                }
            )
            return [None] * len(rows)
        if parent_table in facts:
            if not any(item["parent_table"] == parent_table for item in fact_row_links):
                fact_row_links.append(
                    {
                        "parent_table": parent_table,
                        "mapping": "source-row position",
                        "reason": "The release config defines no explicit fact-to-fact source key.",
                    }
                )
            return [fact_keys[parent_table][index] for index in rows.index]
        if parent_table not in dimensions:
            raise ValueError(f"{table_name}.{column} references unknown dimension {parent_table}")

        parent_indexes = effective_dimension_indexes[parent_table]
        if not parent_indexes:
            raise ValueError(f"{parent_table} has no dedup_columns for foreign-key mapping")
        parent_lookup = dimension_lookups[parent_table]
        result: list[str | None] = []
        for natural_key in _key_frame(rows, parent_indexes).itertuples(
            index=False, name=None
        ):
            if all(value is None for value in natural_key):
                result.append(None)
                continue
            if natural_key not in parent_lookup:
                raise ValueError(
                    f"Cannot map {table_name}.{column} to {parent_table} "
                    f"for source key {natural_key!r}"
                )
            result.append(parent_lookup[natural_key])
        return result

    frames: dict[str, pd.DataFrame] = {}
    for table_name, spec in dimensions.items():
        rows = dimension_rows[table_name]
        output: dict[str, list[str | None]] = {
            spec["key_column"]: dimension_keys[table_name]
        }
        for foreign_key in spec.get("foreign_keys") or []:
            parent_table = foreign_key["references"]
            parent_indexes = effective_dimension_indexes.get(parent_table) or []
            if parent_table != table_name and parent_indexes:
                ambiguous_count = _ambiguous_parent_count(
                    source, effective_dimension_indexes[table_name], parent_indexes
                )
                if ambiguous_count:
                    ambiguous_relations.append(
                        {
                            "table": table_name,
                            "column": foreign_key["column"],
                            "parent_table": parent_table,
                            "ambiguous_child_keys": ambiguous_count,
                            "resolution": "First source row wins, matching declared deduplication order.",
                        }
                    )
            output[foreign_key["column"]] = resolve_foreign_key(
                table_name, foreign_key["column"], parent_table, rows
            )
        for column in spec.get("columns") or []:
            index = column["source_index"]
            if not 0 <= index < source.shape[1]:
                raise ValueError(f"{table_name} source index {index} is out of range")
            output[column["target_name"]] = [
                _transform_value(value, column.get("transform"))
                for value in rows.iloc[:, index]
            ]
        frame = pd.DataFrame(output)
        if frame.columns.duplicated().any():
            raise ValueError(f"{table_name} config produces duplicate target columns")
        frames[table_name] = frame

    for table_name, spec in facts.items():
        output: dict[str, list[str | None]] = {
            spec["key_column"]: [str(index) for index in range(1, len(source) + 1)]
        }
        for foreign_key in spec.get("foreign_keys") or []:
            output[foreign_key["column"]] = resolve_foreign_key(
                table_name,
                foreign_key["column"],
                foreign_key["references"],
                source,
            )
        for column in spec.get("columns") or []:
            index = column["source_index"]
            if not 0 <= index < source.shape[1]:
                raise ValueError(f"{table_name} source index {index} is out of range")
            output[column["target_name"]] = [
                _transform_value(value, column.get("transform"))
                for value in source.iloc[:, index]
            ]
        frame = pd.DataFrame(output)
        if frame.columns.duplicated().any():
            raise ValueError(f"{table_name} config produces duplicate target columns")
        frames[table_name] = frame

    return (
        frames,
        ambiguous_relations,
        unresolved_self_references,
        fact_row_links,
        effective_dimension_indexes,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_member(archive: ZipFile, member: str) -> str:
    digest = hashlib.sha256()
    with archive.open(member) as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_source_frame(archive: ZipFile, member: str) -> pd.DataFrame:
    with archive.open(member) as source:
        return pd.read_csv(
            source,
            dtype=str,
            keep_default_na=False,
            na_filter=False,
        )


def _load_database_archive(archive_path: Path, dsn: str, manifest_path: Path) -> dict[str, Any]:
    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError as error:
        raise RuntimeError(
            "PostgreSQL support is optional; install the 'indicdb' project extra."
        ) from error

    archive_digest = _sha256_file(archive_path)
    manifest: dict[str, Any] = {
        "artifact_type": "IndicDB source reconstruction; not the unmodified official database",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_sha256": archive_digest,
        "schema_count": 0,
        "table_count": 0,
        "schemas": [],
        "config_ddl_column_mismatches": [],
        "config_foreign_key_columns_added": [],
        "method_notes": [
            "Tables are regenerated from each schema_config.yaml and data/total_data.csv.",
            "Dimension IDs follow first-seen source order; keys are expanded with parent identity when declared dedup columns would lose foreign-key relationships.",
            "Foreign-key columns declared by the config but omitted from DDL are added with the referenced key's integer type and recorded; no constraint is invented.",
            "Any remaining ambiguous foreign-key mapping is recorded and uses the first source row deterministically.",
            "Fact-to-fact foreign keys without explicit source keys are mapped by source-row position and recorded.",
            "Self-referencing foreign keys without an explicit source mapping remain NULL and are recorded.",
            "This reconstructed variant is not the unmodified IndicDB release and must not be reported as an official benchmark result.",
        ],
    }

    with ZipFile(archive_path) as archive:
        config_paths = sorted(
            name for name in archive.namelist() if name.endswith("/schema_config.yaml")
        )
        if not config_paths:
            raise ValueError(f"No schema_config.yaml files found in {archive_path}")
        configs: list[tuple[str, dict[str, Any]]] = []
        for config_path in config_paths:
            config = yaml.safe_load(archive.read(config_path))
            if not isinstance(config, dict) or not config.get("database_name"):
                raise ValueError(f"Invalid database config: {config_path}")
            base_path = config_path.rsplit("/", 1)[0]
            source_path = f"{base_path}/data/{config.get('source_file', 'total_data.csv')}"
            ddl_path = f"{base_path}/DDL.csv"
            for required_path in (source_path, ddl_path):
                if required_path not in archive.namelist():
                    raise ValueError(f"Required archive member missing: {required_path}")
            configs.append((config_path, config))

        connection = psycopg2.connect(dsn)
        try:
            with connection.cursor() as cursor:
                schema_names = [config["database_name"] for _, config in configs]
                cursor.execute(
                    "SELECT nspname FROM pg_namespace WHERE nspname = ANY(%s)",
                    (schema_names,),
                )
                existing = [row[0] for row in cursor.fetchall()]
                if existing:
                    raise ValueError(
                        "Target database already contains release schemas; use a fresh empty "
                        f"database. Existing schemas: {existing}"
                    )

                for config_path, config in configs:
                    database_name = config["database_name"]
                    dimensions = config.get("dimension_tables") or {}
                    facts = config.get("fact_tables") or {}
                    base_path = config_path.rsplit("/", 1)[0]
                    source_path = f"{base_path}/data/{config.get('source_file', 'total_data.csv')}"
                    ddl_path = f"{base_path}/DDL.csv"

                    cursor.execute(
                        sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(database_name))
                    )
                    cursor.execute(
                        sql.SQL("SET search_path TO {}").format(sql.Identifier(database_name))
                    )
                    with archive.open(ddl_path) as ddl_file:
                        ddl_rows = csv.DictReader(
                            io.TextIOWrapper(ddl_file, encoding="utf-8-sig", newline="")
                        )
                        for row in ddl_rows:
                            if row.get("DDL"):
                                cursor.execute(row["DDL"])

                    source = _read_source_frame(archive, source_path)
                    (
                        frames,
                        ambiguous,
                        unresolved,
                        fact_row_links,
                        effective_keys,
                    ) = build_table_frames(source, config)
                    cursor.execute(
                        """
                        SELECT table_name, column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = %s
                        """,
                        (database_name,),
                    )
                    column_types_by_table: dict[str, dict[str, str]] = {}
                    ddl_columns_by_table: dict[str, set[str]] = {}
                    integer_columns: set[tuple[str, str]] = set()
                    for table, column, data_type in cursor.fetchall():
                        ddl_columns_by_table.setdefault(table, set()).add(column)
                        column_types_by_table.setdefault(table, {})[column] = data_type
                        if data_type in {"smallint", "integer", "bigint"}:
                            integer_columns.add((table, column))

                    supported_fk_types = {
                        "smallint": "SMALLINT",
                        "integer": "INTEGER",
                        "bigint": "BIGINT",
                    }
                    for table_name, spec in [*dimensions.items(), *facts.items()]:
                        target_table = table_name.lower()
                        for foreign_key in spec.get("foreign_keys") or []:
                            column_name = foreign_key["column"].lower()
                            if column_name in ddl_columns_by_table.get(target_table, set()):
                                continue
                            parent_table = foreign_key["references"].lower()
                            parent_spec = dimensions.get(foreign_key["references"]) or facts.get(
                                foreign_key["references"]
                            )
                            if parent_spec is None:
                                raise ValueError(
                                    f"{table_name}.{foreign_key['column']} references unknown "
                                    f"table {foreign_key['references']}"
                                )
                            parent_key = parent_spec["key_column"].lower()
                            parent_type = column_types_by_table.get(parent_table, {}).get(
                                parent_key
                            )
                            sql_type = supported_fk_types.get(parent_type or "")
                            if sql_type is None:
                                raise ValueError(
                                    f"Cannot infer an integer type for {table_name}."
                                    f"{foreign_key['column']} from {parent_table}.{parent_key}"
                                )
                            cursor.execute(
                                sql.SQL("ALTER TABLE {}.{} ADD COLUMN {} {}").format(
                                    sql.Identifier(database_name),
                                    sql.Identifier(target_table),
                                    sql.Identifier(column_name),
                                    sql.SQL(sql_type),
                                )
                            )
                            ddl_columns_by_table.setdefault(target_table, set()).add(
                                column_name
                            )
                            column_types_by_table.setdefault(target_table, {})[
                                column_name
                            ] = parent_type
                            integer_columns.add((target_table, column_name))
                            manifest["config_foreign_key_columns_added"].append(
                                {
                                    "database_name": database_name,
                                    "table": table_name,
                                    "column": foreign_key["column"],
                                    "references": foreign_key["references"],
                                    "inferred_type": parent_type,
                                    "note": "The schema config declares this foreign key, but the released DDL omits the column; no database constraint was added.",
                                }
                            )
                    table_manifest: dict[str, int] = {}
                    for table_name, frame in frames.items():
                        frame, mismatch = _align_frame_to_ddl(
                            table_name,
                            frame,
                            (
                                dimensions.get(table_name)
                                or facts.get(table_name)
                                or {}
                            ),
                            ddl_columns_by_table.get(table_name.lower(), set()),
                        )
                        if any(mismatch.values()):
                            manifest["config_ddl_column_mismatches"].append(
                                {
                                    "database_name": database_name,
                                    "table": table_name,
                                    **mismatch,
                                }
                            )
                        for column in frame.columns:
                            if (table_name.lower(), column.lower()) in integer_columns:
                                frame[column] = frame[column].map(
                                    lambda value, table=table_name, col=column: _normalize_integer_value(
                                        value, table, col
                                    )
                                )
                        columns = sql.SQL(", ").join(
                            sql.Identifier(column.lower()) for column in frame.columns
                        )
                        copy_statement = sql.SQL(
                            "COPY {}.{} ({}) FROM STDIN WITH (FORMAT CSV, NULL '')"
                        ).format(
                            sql.Identifier(database_name),
                            sql.Identifier(table_name.lower()),
                            columns,
                        )
                        payload = io.StringIO(
                            frame.to_csv(
                                index=False,
                                header=False,
                                na_rep="",
                                quoting=csv.QUOTE_MINIMAL,
                                lineterminator="\n",
                            )
                        )
                        cursor.copy_expert(copy_statement.as_string(connection), payload)
                        table_manifest[table_name] = len(frame)

                    manifest["schemas"].append(
                        {
                            "database_name": database_name,
                            "schema_config_path": config_path,
                            "schema_config_sha256": _sha256_member(archive, config_path),
                            "source_csv_path": source_path,
                            "source_csv_sha256": _sha256_member(archive, source_path),
                            "table_row_counts": table_manifest,
                            "effective_dimension_key_indexes": {
                                table: [
                                    "source_row_index"
                                    if index == SOURCE_ROW_INDEX
                                    else index
                                    for index in indexes
                                ]
                                for table, indexes in effective_keys.items()
                            },
                            "ambiguous_foreign_keys": ambiguous,
                            "unresolved_self_references": unresolved,
                            "fact_row_links": fact_row_links,
                        }
                    )
                    manifest["table_count"] += len(table_manifest)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    manifest["schema_count"] = len(manifest["schemas"])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path, help="Path to the released indicDB.zip")
    parser.add_argument("--dsn", required=True, help="DSN for a fresh, empty PostgreSQL database")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("benchmark_results/indicdb_reconstruction_manifest.json"),
        help="Path for the reconstruction provenance manifest",
    )
    args = parser.parse_args()
    manifest = _load_database_archive(args.archive, args.dsn, args.manifest)
    print(
        f"Reconstructed {manifest['schema_count']} schemas and "
        f"{manifest['table_count']} tables. Manifest: {args.manifest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
