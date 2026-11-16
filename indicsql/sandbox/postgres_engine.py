"""Read-only PostgreSQL execution for schema-aware IndicDB evaluation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from time import perf_counter
from typing import Any

from indicsql.sandbox.validator import validate_postgres_readonly_sql


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


class PostgresSandbox:
    """Execute one read-only query at a time in a selected PostgreSQL schema."""

    def __init__(self, dsn: str, statement_timeout_ms: int = 30_000):
        try:
            import psycopg2
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL support is optional; install the 'indicdb' project extra."
            ) from exc

        self._psycopg2 = psycopg2
        self._connection = psycopg2.connect(dsn)
        self._connection.set_session(readonly=True, autocommit=False)
        self._statement_timeout_ms = statement_timeout_ms

    def get_schema_context(self, schema_name: str) -> dict[str, Any]:
        """Return table, column, and foreign-key metadata for a schema."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position
                """,
                (schema_name,),
            )
            table_rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.constraint_schema = kcu.constraint_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.constraint_schema = tc.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = %s
                ORDER BY tc.table_name, kcu.ordinal_position
                """,
                (schema_name,),
            )
            foreign_keys = cursor.fetchall()
        self._connection.rollback()

        tables: dict[str, dict[str, Any]] = {}
        for table_name, column_name, data_type, is_nullable in table_rows:
            table = tables.setdefault(
                table_name,
                {"description": "", "columns": {}, "foreign_keys": [], "sample_values": {}},
            )
            nullable = " nullable" if is_nullable == "YES" else " not null"
            table["columns"][column_name] = f"{data_type}{nullable}"
        for table_name, column_name, ref_table, ref_column in foreign_keys:
            tables[table_name]["foreign_keys"].append(
                f"{column_name} references {ref_table}.{ref_column}"
            )

        from psycopg2 import sql

        for table_name, table in tables.items():
            if not table_name.startswith("dim_"):
                continue
            for column_name, data_type in table["columns"].items():
                if column_name not in {
                    "state",
                    "state_name",
                    "district",
                    "district_name",
                    "country_name",
                } or not data_type.startswith(("character varying", "character", "text")):
                    continue
                limit = 50 if "state" in column_name else 10
                statement = sql.SQL(
                    "SELECT DISTINCT {column} FROM {schema}.{table} "
                    "WHERE {column} IS NOT NULL ORDER BY {column} LIMIT {limit}"
                ).format(
                    column=sql.Identifier(column_name),
                    schema=sql.Identifier(schema_name),
                    table=sql.Identifier(table_name),
                    limit=sql.Literal(limit),
                )
                with self._connection.cursor() as cursor:
                    cursor.execute(statement)
                    table["sample_values"][column_name] = [
                        str(row[0]) for row in cursor.fetchall()
                    ]
                self._connection.rollback()

        if not tables:
            raise ValueError(f"No tables found in PostgreSQL schema {schema_name!r}.")
        return {
            "dialect": "postgres",
            "schema_name": schema_name,
            "description": f"IndicDB schema {schema_name}",
            "tables": tables,
        }

    def execute_query(self, query: str, schema_name: str) -> dict[str, Any]:
        is_valid, normalized_sql = validate_postgres_readonly_sql(query)
        if not is_valid:
            raise ValueError(normalized_sql)

        from psycopg2 import sql

        started = perf_counter()
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SET LOCAL search_path TO {}, pg_catalog").format(
                        sql.Identifier(schema_name)
                    )
                )
                cursor.execute(
                    "SELECT set_config('statement_timeout', %s, true)",
                    (str(self._statement_timeout_ms),),
                )
                cursor.execute(normalized_sql)
                columns = [description.name for description in cursor.description or []]
                rows = [
                    [_json_safe(value) for value in row] for row in cursor.fetchall()
                ]
        except Exception:
            self._connection.rollback()
            raise

        elapsed_ms = (perf_counter() - started) * 1000
        self._connection.rollback()
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": elapsed_ms,
        }

    def close(self) -> None:
        self._connection.close()
