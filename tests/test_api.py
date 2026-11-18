import unittest
from unittest.mock import patch

from indicsql.api.server import QueryRequest, run_query


class TestQueryApi(unittest.TestCase):
    @patch("indicsql.api.server.execute_indicsql_pipeline")
    def test_reports_success_for_empty_result_set(self, run_pipeline):
        run_pipeline.return_value = {
            "query_id": "query-1",
            "raw_query": "List records",
            "detected_lang": "en",
            "detected_script": "Latin",
            "generated_sql": "SELECT name FROM records",
            "execution_result": {"columns": ["name"], "rows": [], "row_count": 0},
            "execution_error": None,
            "verbalized_response": "No records found.",
            "audit_trace": [],
        }

        response = run_query(QueryRequest(query="List records"))

        run_pipeline.assert_called_once_with(
            "List records",
            interactive_defaults=True,
        )
        self.assertEqual(response.execution_status, "success")
        self.assertIsNone(response.execution_error)
        self.assertEqual(response.execution_result["row_count"], 0)
        self.assertEqual(response.applied_defaults, [])

    @patch("indicsql.api.server.execute_indicsql_pipeline")
    def test_returns_execution_failure_details(self, run_pipeline):
        run_pipeline.return_value = {
            "query_id": "query-2",
            "raw_query": "List records",
            "detected_lang": "en",
            "detected_script": "Latin",
            "generated_sql": "SELECT missing_column FROM records",
            "execution_result": None,
            "execution_error": "Schema validation failed: unknown column.",
            "suggested_queries": ["List the available columns."],
            "verbalized_response": "The query could not be executed.",
            "audit_trace": [],
        }

        response = run_query(QueryRequest(query="List records"))

        self.assertEqual(response.execution_status, "failed")
        self.assertEqual(
            response.execution_error, "Schema validation failed: unknown column."
        )
        self.assertEqual(response.suggested_queries, ["List the available columns."])
        self.assertIsNone(response.execution_result)


if __name__ == "__main__":
    unittest.main()
