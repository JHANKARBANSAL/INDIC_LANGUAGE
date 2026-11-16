import unittest

from indicsql.sandbox.validator import (
    repair_missing_foreign_key_join,
    validate_postgres_readonly_sql,
    validate_postgres_schema_sql,
)


class TestPostgresReadonlyValidation(unittest.TestCase):
    def test_accepts_single_select_and_with_queries(self):
        for query in (
            "SELECT district_name FROM dim_district",
            "WITH districts AS (SELECT district_name FROM dim_district) "
            "SELECT district_name FROM districts",
        ):
            with self.subTest(query=query):
                valid, normalized = validate_postgres_readonly_sql(query)
                self.assertTrue(valid)
                self.assertTrue(normalized.upper().startswith(("SELECT", "WITH")))

    def test_rejects_mutations_and_multiple_statements(self):
        for query in (
            "DELETE FROM dim_district",
            "SELECT 1; SELECT 2",
            "SELECT 1; DROP TABLE dim_district",
        ):
            with self.subTest(query=query):
                valid, error = validate_postgres_readonly_sql(query)
                self.assertFalse(valid)
                self.assertTrue(error)

    def test_repairs_parent_column_reference_using_declared_foreign_key(self):
        query = (
            "SELECT district_name FROM dim_district "
            "WHERE state_name = 'Andhra Pradesh' ORDER BY district_name"
        )
        schema = {
            "tables": {
                "dim_district": {
                    "columns": {"district_id": "bigint", "district_name": "text", "state_id": "bigint"},
                    "foreign_keys": ["state_id references dim_state.state_id"],
                },
                "dim_state": {
                    "columns": {"state_id": "bigint", "state_name": "text"},
                    "foreign_keys": [],
                },
            }
        }

        repaired, repairs = repair_missing_foreign_key_join(query, schema)

        self.assertIn("JOIN dim_state", repaired)
        self.assertIn("dim_state.state_name", repaired)
        self.assertEqual(len(repairs), 1)
        self.assertTrue(validate_postgres_readonly_sql(repaired)[0])

    def test_schema_validation_accepts_aliases_joins_and_ctes(self):
        query = (
            "WITH selected_state AS ("
            "SELECT s.state_id FROM dim_state AS s WHERE s.state_name = 'Andhra Pradesh'"
            ") SELECT d.district_name FROM dim_district AS d "
            "JOIN selected_state AS s ON d.state_id = s.state_id"
        )
        schema = {
            "schema_name": "indicdb",
            "tables": {
                "dim_district": {
                    "columns": {"district_name": "text", "state_id": "bigint"},
                },
                "dim_state": {
                    "columns": {"state_id": "bigint", "state_name": "text"},
                },
            },
        }

        valid, result = validate_postgres_schema_sql(query, schema)

        self.assertTrue(valid, result)

    def test_schema_validation_rejects_unknown_table_without_execution(self):
        schema = {
            "tables": {
                "dim_geography": {
                    "columns": {"sub_district": "text"},
                }
            }
        }

        valid, error = validate_postgres_schema_sql(
            "SELECT sub_district FROM INDIA_HMIS_Sub_District_Report_Facility_wise",
            schema,
        )

        self.assertFalse(valid)
        self.assertIn("unknown table", error.lower())
        self.assertIn("dim_geography", error)

    def test_schema_validation_rejects_unknown_aliased_column(self):
        schema = {
            "tables": {
                "fact_person_core": {
                    "columns": {"age": "integer", "household_id": "bigint"},
                },
                "fact_household_core": {
                    "columns": {"household_id": "bigint", "new_household_split_number": "integer"},
                },
            }
        }

        valid, error = validate_postgres_schema_sql(
            "SELECT p.new_household_split_number FROM fact_person_core AS p",
            schema,
        )

        self.assertFalse(valid)
        self.assertIn("new_household_split_number", error)
        self.assertIn("Allowed columns", error)

    def test_schema_validation_rejects_ambiguous_unqualified_column(self):
        schema = {
            "tables": {
                "dim_district": {
                    "columns": {"state_id": "bigint", "district_name": "text"},
                },
                "dim_state": {
                    "columns": {"state_id": "bigint", "state_name": "text"},
                },
            }
        }

        valid, error = validate_postgres_schema_sql(
            "SELECT state_id FROM dim_district JOIN dim_state "
            "ON dim_district.state_id = dim_state.state_id",
            schema,
        )

        self.assertFalse(valid)
        self.assertIn("ambiguous unqualified column", error.lower())
        self.assertIn("dim_district.state_id", error)
        self.assertIn("dim_state.state_id", error)


if __name__ == "__main__":
    unittest.main()
