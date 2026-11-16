import unittest

from indicsql.agents.sql_synthesizer import _build_dynamic_fallback


class TestDynamicSqlFallback(unittest.TestCase):
    def test_builds_aggregate_query_when_ollama_is_unavailable(self):
        sql = _build_dynamic_fallback(
            "ndap_pm_kisan_disbursement",
            {
                "columns": {
                    "state_name": "VARCHAR",
                    "farmer_beneficiaries": "BIGINT",
                }
            },
            {"state_name": "MAHARASHTRA"},
            "How many farmers benefited in Maharashtra?",
            ["farmer_beneficiaries"],
        )

        self.assertIn("SUM(farmer_beneficiaries)", sql)
        self.assertIn("state_name = 'MAHARASHTRA'", sql)

    def test_builds_top_n_query_without_failing_before_query_analysis(self):
        sql = _build_dynamic_fallback(
            "ndap_pmgsy_rural_roads",
            {
                "columns": {
                    "state_name": "VARCHAR",
                    "district_name": "VARCHAR",
                    "completed_road_length_km": "DOUBLE",
                }
            },
            {"state_name": "MAHARASHTRA"},
            "Show the top 5 districts in Maharashtra by completed road length",
            ["completed_road_length_km"],
        )

        self.assertIn("GROUP BY district_name", sql)
        self.assertIn("ORDER BY total_completed_road_length_km DESC LIMIT 5", sql)


if __name__ == "__main__":
    unittest.main()
