import unittest
from unittest.mock import Mock, patch

from indicsql.models.ollama_client import OllamaClient


class TestOllamaClient(unittest.TestCase):
    @patch("indicsql.models.ollama_client.httpx.post")
    def test_sql_generation_uses_fixed_sampling_seed(self, mock_post):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "response": (
                "SELECT SUM(farmer_beneficiaries) "
                "FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';"
            )
        }
        mock_post.return_value = response
        client = OllamaClient()

        client.generate_sql(
            query="How many farmers benefited in Maharashtra?",
            table_name="ndap_pm_kisan_disbursement",
            table_schema={
                "columns": {
                    "state_name": "VARCHAR",
                    "farmer_beneficiaries": "BIGINT",
                }
            },
            canonical_entities={"state_name": "MAHARASHTRA"},
        )

        options = mock_post.call_args.kwargs["json"]["options"]
        self.assertEqual(options["temperature"], 0.05)
        self.assertEqual(options["seed"], 42)

    @patch("indicsql.models.ollama_client.httpx.post")
    def test_dynamic_schema_uses_postgres_prompt_and_supplied_tables(self, mock_post):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"response": "SELECT district_name FROM dim_district;"}
        mock_post.return_value = response
        client = OllamaClient()

        client.generate_sql(
            query="List districts",
            table_name="INDIA_Economic_Census_Firms",
            table_schema={
                "dialect": "postgres",
                "description": "Economic census",
                "tables": {
                    "dim_district": {
                        "columns": {"district_name": "text", "state_id": "bigint"},
                        "foreign_keys": ["state_id references dim_state.state_id"],
                    },
                    "dim_state": {
                        "columns": {"state_id": "bigint", "state_name": "text"},
                        "foreign_keys": [],
                    },
                },
            },
        )

        prompt = mock_post.call_args.kwargs["json"]["prompt"]
        self.assertIn("read-only PostgreSQL", prompt)
        self.assertIn("TABLE dim_district", prompt)
        self.assertIn("state_id: dim_district.state_id, dim_state.state_id", prompt)
        self.assertIn("SHARED COLUMN NAMES (always qualify these)", prompt)
        self.assertIn("dim_state.state_id", prompt)
        self.assertIn("Do not self-join or repeat a table", prompt)
        self.assertIn("Do not add COLLATE clauses", prompt)


if __name__ == "__main__":
    unittest.main()
