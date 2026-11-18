import unittest

from indicsql.benchmark.evaluator import are_tabular_results_equivalent
from indicsql.models.interactive_query_policy import apply_interactive_query_defaults
from indicsql.sandbox.duckdb_engine import DuckDBSandbox


class TestInteractiveQueryPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox = DuckDBSandbox()

    def test_farmer_count_defaults_to_latest_financial_year(self):
        sql, defaults = apply_interactive_query_defaults(
            "SELECT SUM(farmer_beneficiaries) AS total_farmers "
            "FROM ndap_pm_kisan_disbursement WHERE state_name = 'BIHAR';",
            "How many farmers in Bihar?",
            "ndap_pm_kisan_disbursement",
        )

        self.assertIn("financial_year = '2024-25'", sql)
        self.assertEqual(len(defaults), 1)

        actual = self.sandbox.execute_query(sql)
        expected = self.sandbox.execute_query(
            "SELECT SUM(farmer_beneficiaries) AS total_farmers "
            "FROM ndap_pm_kisan_disbursement "
            "WHERE state_name = 'BIHAR' AND financial_year = '2024-25';"
        )
        self.assertTrue(are_tabular_results_equivalent(actual, expected))
        self.assertEqual(actual["rows"][0][0], 3296028)

    def test_explicit_farmer_financial_year_is_preserved(self):
        sql = (
            "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement "
            "WHERE state_name = 'BIHAR' AND financial_year = '2022-23';"
        )

        result, defaults = apply_interactive_query_defaults(
            sql,
            "How many farmers in Bihar in financial year 2022-23?",
            "ndap_pm_kisan_disbursement",
        )

        self.assertIn("financial_year = '2022-23'", result)
        self.assertNotIn("2024-25", result)
        self.assertEqual(defaults, [])

    def test_farmer_year_breakdown_groups_by_financial_year(self):
        sql, defaults = apply_interactive_query_defaults(
            "SELECT SUM(farmer_beneficiaries) AS total_farmers "
            "FROM ndap_pm_kisan_disbursement WHERE state_name = 'BIHAR';",
            "How many farmers in Bihar by year?",
            "ndap_pm_kisan_disbursement",
        )

        self.assertIn("GROUP BY financial_year", sql)
        self.assertIn("financial_year", sql.split("FROM")[0])
        self.assertNotIn("2024-25", sql)
        self.assertTrue(any("year-by-year" in item for item in defaults))

        result = self.sandbox.execute_query(sql)
        self.assertEqual(result["row_count"], 4)

    def test_period_defaults_do_not_change_unapproved_metrics_or_tables(self):
        cases = (
            (
                "SELECT SUM(amount_inr) FROM ndap_pm_kisan_disbursement "
                "WHERE state_name = 'BIHAR';",
                "What is the total amount disbursed in Bihar?",
                "ndap_pm_kisan_disbursement",
            ),
            (
                "SELECT SUM(person_days) FROM mgnrega_state_annual_employment "
                "WHERE state_name = 'BIHAR';",
                "What is the employment total in Bihar?",
                "mgnrega_state_annual_employment",
            ),
            (
                "SELECT SUM(student_count) FROM ndap_education_stats "
                "WHERE state_name = 'BIHAR';",
                "How many students are in Bihar?",
                "ndap_education_stats",
            ),
        )

        for sql, query, table_name in cases:
            with self.subTest(table_name=table_name, query=query):
                result, defaults = apply_interactive_query_defaults(
                    sql, query, table_name
                )
                self.assertEqual(result, sql)
                self.assertEqual(defaults, [])

    def test_state_female_literacy_returns_latest_district_rates(self):
        sql, defaults = apply_interactive_query_defaults(
            "SELECT AVG(female_literacy_rate) AS average_rate "
            "FROM ndap_education_stats WHERE state_name = 'BIHAR';",
            "What was the female literacy rate in Bihar?",
            "ndap_education_stats",
        )

        self.assertIn("census_year = 2024", sql)
        self.assertIn("district_name", sql)
        self.assertIn("female_literacy_rate", sql)
        self.assertNotIn("AVG(", sql)
        self.assertNotIn(", male_literacy_rate", sql)
        self.assertEqual(len(defaults), 2)

        result = self.sandbox.execute_query(sql)
        self.assertEqual(result["row_count"], 7)
        self.assertTrue(all(row[1] == 2024 for row in result["rows"]))

    def test_unspecified_literacy_gender_returns_both_rates_by_district(self):
        sql, _ = apply_interactive_query_defaults(
            "SELECT AVG(female_literacy_rate) AS average_rate "
            "FROM ndap_education_stats WHERE state_name = 'BIHAR';",
            "What was the literacy rate in Bihar?",
            "ndap_education_stats",
        )

        self.assertIn("female_literacy_rate", sql)
        self.assertIn("male_literacy_rate", sql)
        self.assertNotIn("AVG(", sql)

    def test_explicit_state_average_is_unweighted_and_includes_unspecified_genders(self):
        sql, defaults = apply_interactive_query_defaults(
            "SELECT AVG(female_literacy_rate) AS average_rate "
            "FROM ndap_education_stats WHERE state_name = 'BIHAR';",
            "What was the average literacy rate in Bihar?",
            "ndap_education_stats",
        )

        self.assertIn("AVG(female_literacy_rate)", sql)
        self.assertIn("AVG(male_literacy_rate)", sql)
        self.assertIn("census_year = 2024", sql)
        self.assertTrue(any("unweighted mean" in item for item in defaults))

    def test_hindi_female_literacy_query_uses_district_rates(self):
        sql, _ = apply_interactive_query_defaults(
            "SELECT AVG(female_literacy_rate) AS average_rate "
            "FROM ndap_education_stats WHERE state_name = 'BIHAR';",
            "बिहार में महिला साक्षरता दर क्या है?",
            "ndap_education_stats",
        )

        self.assertIn("district_name", sql)
        self.assertIn("female_literacy_rate", sql)
        self.assertNotIn(", male_literacy_rate", sql)

    def test_district_query_keeps_its_requested_granularity(self):
        sql, defaults = apply_interactive_query_defaults(
            "SELECT AVG(female_literacy_rate) AS average_rate "
            "FROM ndap_education_stats "
            "WHERE state_name = 'BIHAR' AND district_name = 'Patna';",
            "What was female literacy in Patna, Bihar?",
            "ndap_education_stats",
        )

        self.assertIn("district_name = 'Patna'", sql)
        self.assertIn("census_year = 2024", sql)
        self.assertIn("AVG(female_literacy_rate)", sql)
        self.assertEqual(len(defaults), 1)


if __name__ == "__main__":
    unittest.main()
