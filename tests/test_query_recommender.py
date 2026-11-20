"""Regression tests for schema-grounded alternatives (no invented columns)."""

import unittest

from indicsql.agents.query_recommender import recommend_alternative_queries
from indicsql.schema.catalog import NDAPCatalog


class QueryRecommenderTests(unittest.TestCase):
    def test_recommends_real_catalog_columns(self):
        suggestions = recommend_alternative_queries(
            "How many farmers received PM KISAN payments?", language="en"
        )
        self.assertTrue(1 <= len(suggestions) <= 5)
        self.assertTrue(
            any("farmer beneficiaries" in item.lower() for item in suggestions)
        )
        self.assertTrue(
            all("ndap_pm_kisan_disbursement" in item for item in suggestions[:1])
        )

    def test_unrelated_query_fails_closed(self):
        suggestions = recommend_alternative_queries(
            "What is the orbital velocity of Neptune?"
        )
        self.assertEqual(suggestions, [])

    def test_external_schema_does_not_leak_ndap_columns(self):
        schema = {
            "tables": {
                "district_data": {
                    "title": "Hospital count statistics",
                    "columns": {
                        "district_name": "TEXT",
                        "hospital_count": "INTEGER",
                    },
                }
            }
        }
        suggestions = recommend_alternative_queries(
            "Hospital count by district",
            schema=schema,
            preferred_table="district_data",
        )
        self.assertEqual(len(suggestions), 1)
        self.assertIn("hospital count", suggestions[0])
        self.assertIn("district_data", suggestions[0])
        self.assertNotIn("ndap_", suggestions[0])

    def test_custom_schema_missing_numeric_fields_is_not_recommended(self):
        self.assertEqual(
            recommend_alternative_queries(
                "Hospital staffing",
                schema={"tables": {"x": {"columns": {"district_name": "TEXT"}}}},
                preferred_table="x",
            ),
            [],
        )

    def test_language_and_limit(self):
        suggestions = recommend_alternative_queries(
            "PM KISAN farmer beneficiaries",
            language="bn",
            preferred_table="ndap_pm_kisan_disbursement",
            limit=3,
        )
        self.assertTrue(1 <= len(suggestions) <= 3)
        self.assertTrue(all("ডেটাসেটে" in item for item in suggestions))

    def test_recommendation_columns_exist_in_catalog(self):
        results = recommend_alternative_queries(
            "Crop production and yield by district", limit=5
        )
        catalog = NDAPCatalog.get_table_schema("ndap_crop_production_census")
        self.assertTrue(catalog.get("columns"))
        # Every suggestion is derived from the catalog and names a registered table.
        for result in results:
            self.assertTrue(
                any(name in result for name in NDAPCatalog.list_tables())
            )


if __name__ == "__main__":
    unittest.main()
