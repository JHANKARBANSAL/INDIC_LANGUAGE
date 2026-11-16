import tempfile
import unittest
from pathlib import Path

import pandas as pd

from indicsql.benchmark.indicdb import (
    INDICDB_LANGUAGE_FILES,
    enrich_schema_context,
    load_aligned_indicdb_queries,
)


class TestIndicDBLanguageLoader(unittest.TestCase):
    def test_schema_metadata_adds_descriptions_and_declared_foreign_keys(self):
        context = {
            "tables": {
                "dim_state": {
                    "columns": {"state_id": "bigint", "state_name": "text"},
                    "foreign_keys": [],
                },
                "dim_district": {
                    "columns": {"district_id": "bigint", "state_id": "bigint"},
                    "foreign_keys": [],
                },
            }
        }
        config = {
            "table_descriptions": {"DIM_STATE": "State reference data"},
            "dimension_tables": {
                "DIM_STATE": {"key_column": "STATE_ID", "foreign_keys": []},
                "DIM_DISTRICT": {
                    "key_column": "DISTRICT_ID",
                    "foreign_keys": [
                        {"column": "STATE_ID", "references": "DIM_STATE"}
                    ],
                },
            },
            "fact_tables": {},
        }

        enriched = enrich_schema_context(context, config)

        self.assertEqual(
            enriched["tables"]["dim_state"]["description"], "State reference data"
        )
        self.assertEqual(enriched["tables"]["dim_state"]["primary_key"], "state_id")
        self.assertIn(
            "state_id references dim_state.state_id",
            enriched["tables"]["dim_district"]["foreign_keys"],
        )

    def test_loads_shared_pairs_and_uses_only_the_sql_column(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for language, filename in INDICDB_LANGUAGE_FILES.items():
                rows = [
                    {
                        "question": f"Question A in {language}",
                        "sql": "SELECT 1",
                        "pair_id": "pair-a",
                        "dataset_name": "DB_A",
                        "gold_sql": "SELECT 999",
                    },
                    {
                        "question": f"Question A in {language}",
                        "sql": "SELECT 3",
                        "pair_id": "pair-a",
                        "dataset_name": "DB_B",
                        "gold_sql": "SELECT 999",
                    },
                    {
                        "question": f"Question A in {language}",
                        "sql": "SELECT 1",
                        "pair_id": "pair-a",
                        "dataset_name": "DB_A",
                        "gold_sql": "SELECT 999",
                    },
                    {
                        "question": f"Question B in {language}",
                        "sql": "" if language == "en" else "SELECT 2",
                        "pair_id": "pair-b",
                        "dataset_name": "DB_B",
                        "gold_sql": "SELECT 999",
                    },
                ]
                pd.DataFrame(rows).to_parquet(root / filename, index=False)

            queries, pair_ids = load_aligned_indicdb_queries(root)

        self.assertEqual(pair_ids, [("pair-a", "DB_A"), ("pair-a", "DB_B")])
        self.assertEqual(set(queries), set(INDICDB_LANGUAGE_FILES))
        for language, language_queries in queries.items():
            self.assertEqual(len(language_queries), 2)
            self.assertEqual(language_queries[0].gold_sql, "SELECT 1")
            self.assertEqual(language_queries[0].language, language)

    def test_rejects_pair_ids_with_conflicting_gold_sql(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for language, filename in INDICDB_LANGUAGE_FILES.items():
                rows = [
                    {
                        "question": f"Question in {language}",
                        "sql": sql,
                        "pair_id": "pair-a",
                        "dataset_name": "DB_A",
                    }
                    for sql in ("SELECT 1", "SELECT 2")
                ]
                pd.DataFrame(rows).to_parquet(root / filename, index=False)

            with self.assertRaisesRegex(ValueError, "conflicting gold SQL"):
                load_aligned_indicdb_queries(root)


if __name__ == "__main__":
    unittest.main()
