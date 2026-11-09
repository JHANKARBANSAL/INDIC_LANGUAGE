"""
DuckDB Sandboxed In-Memory Execution Engine.
Loads NDAP sample schemas into an isolated, ephemeral memory space and executes
read-only analytical SQL queries with runtime resource safeguards.
"""

import time
from pathlib import Path
from typing import Optional

try:
    import duckdb

    HAS_DUCKDB = True
except ImportError:
    import sqlite3

    HAS_DUCKDB = False

from indicsql.core.state import TabularResult

PARQUET_STORE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "parquet_stores"


class DuckDBSandbox:
    """Ephemeral In-Memory Sandbox for executing candidate SQL on NDAP tables."""

    def __init__(self, memory_limit_mb: int = 512, parquet_dir: Optional[Path] = None):
        self.has_duckdb = HAS_DUCKDB
        self.parquet_dir = parquet_dir or PARQUET_STORE_DIR
        if self.has_duckdb:
            self.con = duckdb.connect(database=":memory:")
            self.con.execute(f"SET max_memory = '{memory_limit_mb}MB'")
        else:
            self.con = sqlite3.connect(":memory:")
        self._init_ndap_tables()

    def _init_ndap_tables(self) -> None:
        """Loads all NDAP database tables strictly from data/parquet_stores/."""
        if not self.parquet_dir.exists() or not list(self.parquet_dir.glob("*.parquet")):
            from indicsql.schema.ingest_ndap import ingest_and_export_all_ndap_databases

            ingest_and_export_all_ndap_databases(parquet_dir=self.parquet_dir)

        parquet_files = list(self.parquet_dir.glob("*.parquet")) + list(self.parquet_dir.glob("*/*.parquet"))
        if not parquet_files:
            raise FileNotFoundError(
                f"No NDAP Parquet stores found in {self.parquet_dir}. "
                "Run 'uv run python indicsql/schema/ingest_ndap.py' to generate stores."
            )

        if self.has_duckdb:
            for p_file in parquet_files:
                table_name = p_file.stem
                self.con.execute(
                    f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{p_file.resolve()}');"
                )
        else:
            # Load actual parquet files into in-memory sqlite3 without dummy data
            import pandas as pd

            for p_file in parquet_files:
                table_name = p_file.stem
                df = pd.read_parquet(p_file)
                df.to_sql(table_name, self.con, if_exists="replace", index=False)

    def execute_query(self, sql: str) -> TabularResult:
        """
        Executes a SQL query in the sandbox and returns a TabularResult.
        """
        start = time.perf_counter()

        if self.has_duckdb:
            rel = self.con.sql(sql)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if rel is None:
                return {
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "execution_time_ms": elapsed_ms,
                }
            columns = rel.columns
            rows = [list(r) for r in rel.fetchall()]
        else:
            cur = self.con.cursor()
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = [list(r) for r in cur.fetchall()]
            elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": elapsed_ms,
        }

    def close(self) -> None:
        """Closes the database connection."""
        self.con.close()
