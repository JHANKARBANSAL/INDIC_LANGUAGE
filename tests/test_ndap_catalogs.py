"""
Unit tests for the 20 NDAP database catalogs and parquet stores.
"""

import unittest
from pathlib import Path

from indicsql.sandbox.duckdb_engine import DuckDBSandbox
from indicsql.schema.catalog import NDAPCatalog

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PARQUET_DIR = DATA_DIR / "parquet_stores"
CATALOG_DIR = DATA_DIR / "ndap_catalogs"


class TestNDAPCatalogs(unittest.TestCase):
    def test_twenty_databases_registered(self):
        tables = NDAPCatalog.list_tables()
        self.assertEqual(
            len(tables), 20, "NDAP Catalog must contain exactly 20 benchmark databases."
        )

    def test_four_core_domains_present(self):
        domains = NDAPCatalog.list_domains()
        expected_domains = ["Agriculture", "Education", "Healthcare", "Rural Development"]
        self.assertEqual(sorted(domains), sorted(expected_domains))

        for domain in expected_domains:
            domain_tables = NDAPCatalog.get_tables_by_domain(domain)
            self.assertEqual(
                len(domain_tables),
                5,
                f"Domain '{domain}' must have exactly 5 registered databases.",
            )

    def test_parquet_stores_exist_and_readable(self):
        self.assertTrue(PARQUET_DIR.exists(), "Parquet stores directory must exist.")
        parquet_files = list(PARQUET_DIR.glob("*.parquet"))
        self.assertEqual(
            len(parquet_files), 20, "All 20 NDAP databases must have an exported .parquet file."
        )

    def test_duckdb_sandbox_parquet_mounting(self):
        sandbox = DuckDBSandbox()
        # Test querying a newly mounted parquet table
        res = sandbox.execute_query(
            "SELECT state_name, COUNT(*) AS cnt FROM ndap_pm_kisan_disbursement GROUP BY state_name;"
        )
        self.assertIsNotNone(res)
        self.assertGreater(res["row_count"], 0)
        self.assertIn("state_name", res["columns"])
        self.assertIn("cnt", res["columns"])

    def test_ddl_and_metadata_catalog_files(self):
        metadata_file = CATALOG_DIR / "catalog_metadata.json"
        self.assertTrue(
            metadata_file.exists(), "catalog_metadata.json must exist in ndap_catalogs."
        )
        sql_files = list(CATALOG_DIR.glob("*.sql"))
        self.assertEqual(
            len(sql_files),
            20,
            "Each of the 20 NDAP databases must have a corresponding .sql DDL file.",
        )


if __name__ == "__main__":
    unittest.main()
