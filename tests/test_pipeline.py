import unittest
from unittest.mock import patch

from indicsql.graph.workflow import execute_indicsql_pipeline


class TestPipeline(unittest.TestCase):
    def test_unsupported_query_fails_without_executing_default_table(self):
        state = execute_indicsql_pipeline("What is the population of Atlantis?")

        self.assertEqual(state["generated_sql"], "")
        self.assertIsNone(state["execution_result"])
        self.assertIn("No supported database schema", state["execution_error"])
        self.assertTrue(state["verbalized_response"])

    def test_explicit_postgres_schema_flows_through_pipeline(self):
        class FakePostgresSandbox:
            def __init__(self):
                self.schema_name = None

            def execute_query(self, query, schema_name):
                self.schema_name = schema_name
                return {
                    "columns": ["district_name"],
                    "rows": [["Guntur"]],
                    "row_count": 1,
                    "execution_time_ms": 1.0,
                }

        sandbox = FakePostgresSandbox()
        database_schema = {
            "dialect": "postgres",
            "tables": {
                "dim_district": {
                    "columns": {"district_name": "text"},
                    "foreign_keys": [],
                }
            },
        }
        with patch(
            "indicsql.graph.workflow.sql_synthesizer_node",
            return_value={"generated_sql": "SELECT district_name FROM dim_district;"},
        ):
            state = execute_indicsql_pipeline(
                "జిల్లాల పేర్లను జాబితా చేయండి",
                database_schema_name="INDIA_Economic_Census_Firms",
                database_schema=database_schema,
                language_override="te",
                sandbox=sandbox,
            )

        self.assertEqual(sandbox.schema_name, "INDIA_Economic_Census_Firms")
        self.assertEqual(state["detected_lang"], "te")
        self.assertEqual(state["execution_result"]["rows"], [["Guntur"]])

    def test_invalid_schema_sql_is_retried_once_before_execution(self):
        class FakePostgresSandbox:
            def __init__(self):
                self.queries = []

            def execute_query(self, query, schema_name):
                self.queries.append((query, schema_name))
                return {
                    "columns": ["district_name"],
                    "rows": [["Guntur"]],
                    "row_count": 1,
                    "execution_time_ms": 1.0,
                }

        schema = {
            "dialect": "postgres",
            "schema_name": "indicdb",
            "tables": {
                "dim_district": {
                    "columns": {"district_name": "text"},
                    "foreign_keys": [],
                },
                "fact_hidden_from_pruned_schema": {
                    "columns": {"unrelated_metric": "bigint"},
                    "foreign_keys": [],
                },
            },
        }
        sandbox = FakePostgresSandbox()
        seen_schema_tables = []

        def generate_sql(state, **_kwargs):
            seen_schema_tables.append(set(state["database_schema"]["tables"]))
            if len(seen_schema_tables) == 1:
                return "SELECT district_name FROM hallucinated_table", "test", 0.1
            return "SELECT district_name FROM dim_district", "test", 0.9

        with patch(
            "indicsql.agents.sql_synthesizer.synthesize_sql",
            side_effect=generate_sql,
        ) as synthesize:
            state = execute_indicsql_pipeline(
                "List district names",
                database_schema_name="indicdb",
                database_schema=schema,
                sandbox=sandbox,
            )

        self.assertEqual(synthesize.call_count, 2)
        self.assertEqual(seen_schema_tables[0], {"dim_district"})
        self.assertEqual(
            seen_schema_tables[1],
            {"dim_district", "fact_hidden_from_pruned_schema"},
        )
        self.assertEqual(len(sandbox.queries), 1)
        self.assertEqual(state["reflection_attempts"], 1)
        self.assertIsNone(state["schema_validation_error"])
        self.assertEqual(state["execution_result"]["rows"], [["Guntur"]])

    def test_invalid_schema_sql_stops_after_one_retry_without_execution(self):
        class FakePostgresSandbox:
            def __init__(self):
                self.queries = []

            def execute_query(self, query, schema_name):
                self.queries.append((query, schema_name))
                raise AssertionError("Invalid SQL must not reach the database.")

        schema = {
            "dialect": "postgres",
            "schema_name": "indicdb",
            "tables": {
                "dim_district": {
                    "columns": {"district_name": "text"},
                    "foreign_keys": [],
                }
            },
        }
        sandbox = FakePostgresSandbox()
        with patch(
            "indicsql.agents.sql_synthesizer.synthesize_sql",
            return_value=("SELECT district_name FROM hallucinated_table", "test", 0.1),
        ) as synthesize:
            state = execute_indicsql_pipeline(
                "List district names",
                database_schema_name="indicdb",
                database_schema=schema,
                sandbox=sandbox,
            )

        self.assertEqual(synthesize.call_count, 2)
        self.assertEqual(sandbox.queries, [])
        self.assertEqual(state["reflection_attempts"], 1)
        self.assertIn("unknown table", state["execution_error"].lower())

    def test_schema_retry_is_bounded_even_if_database_execution_still_fails(self):
        class FakePostgresSandbox:
            def __init__(self):
                self.queries = []

            def execute_query(self, query, schema_name):
                self.queries.append((query, schema_name))
                raise ValueError("Database execution failed.")

        schema = {
            "dialect": "postgres",
            "schema_name": "indicdb",
            "tables": {
                "dim_district": {
                    "columns": {"district_name": "text"},
                    "foreign_keys": [],
                }
            },
        }
        sandbox = FakePostgresSandbox()
        with patch(
            "indicsql.agents.sql_synthesizer.synthesize_sql",
            side_effect=[
                ("SELECT district_name FROM hallucinated_table", "test", 0.1),
                ("SELECT district_name FROM dim_district", "test", 0.9),
            ],
        ) as synthesize:
            state = execute_indicsql_pipeline(
                "List district names",
                database_schema_name="indicdb",
                database_schema=schema,
                sandbox=sandbox,
            )

        self.assertEqual(synthesize.call_count, 2)
        self.assertEqual(len(sandbox.queries), 1)
        self.assertEqual(state["reflection_attempts"], 1)
        self.assertIn("Database execution failed.", state["execution_error"])

    def test_marathi_pipeline_run(self):
        query = "महाराष्ट्रात गेल्या वर्षी किती शेतकऱ्यांना पीएम-किसानचा लाभ मिळाला?"
        state = execute_indicsql_pipeline(query)

        self.assertEqual(state["detected_lang"], "mr")
        self.assertEqual(state["detected_script"], "Devanagari")
        self.assertNotEqual(state["generated_sql"], "")
        self.assertIsNotNone(state["execution_result"])
        self.assertGreater(state["execution_result"]["row_count"], 0)
        self.assertTrue(
            "शेतकऱ्यांना" in state["verbalized_response"]
            or "पीएम-किसान" in state["verbalized_response"]
        )
        self.assertGreaterEqual(len(state["audit_trace"]), 4)

    def test_bihar_education_pipeline_run(self):
        query = "बिहार के किस जिले में 2023 में सबसे कम महिला साक्षरता थी?"
        state = execute_indicsql_pipeline(query)

        self.assertEqual(state["detected_lang"], "hi")
        self.assertEqual(state["detected_script"], "Devanagari")
        self.assertIn("female_literacy_rate", state["generated_sql"])
        self.assertIsNotNone(state["execution_result"])


if __name__ == "__main__":
    unittest.main()
