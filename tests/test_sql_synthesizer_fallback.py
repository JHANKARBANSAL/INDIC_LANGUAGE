import unittest

from indicsql.agents.sql_synthesizer import _build_dynamic_fallback, extract_canonical_entities
from indicsql.models.metric_guard import sanitize_metric_aggregations


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

    def test_pm_kisan_returns_both_requested_metrics(self):
        sql = _build_dynamic_fallback(
            "ndap_pm_kisan_disbursement",
            {
                "columns": {
                    "state_name": "VARCHAR",
                    "farmer_beneficiaries": "BIGINT",
                    "amount_inr": "DOUBLE",
                }
            },
            {"state_name": "MAHARASHTRA"},
            "What are the total farmer beneficiaries and disbursement amount in Maharashtra?",
        )

        self.assertIn("SUM(farmer_beneficiaries) AS total_farmers", sql)
        self.assertIn("SUM(amount_inr) AS total_amount", sql)

    def test_pm_kisan_amount_request_is_not_mistaken_for_farmer_count(self):
        sql = _build_dynamic_fallback(
            "ndap_pm_kisan_disbursement",
            {
                "columns": {
                    "state_name": "VARCHAR",
                    "farmer_beneficiaries": "BIGINT",
                    "amount_inr": "DOUBLE",
                }
            },
            {"state_name": "BIHAR"},
            "बिहार में पीएम-किसान के तहत कुल कितनी धनराशि वितरित की गई?",
        )

        self.assertEqual(
            sql,
            "SELECT SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement "
            "WHERE state_name = 'BIHAR';",
        )

    def test_financial_year_breakdown_uses_the_schema_time_column(self):
        sql = _build_dynamic_fallback(
            "mgnrega_state_annual_employment",
            {
                "columns": {
                    "state_name": "VARCHAR",
                    "financial_year": "VARCHAR",
                    "total_mandays_generated": "BIGINT",
                }
            },
            {"state_name": "RAJASTHAN"},
            "Show mandays by financial year in Rajasthan.",
            ["total_mandays_generated"],
        )

        self.assertIn("SELECT financial_year, SUM(total_mandays_generated)", sql)
        self.assertIn("GROUP BY financial_year", sql)
        self.assertIn("ORDER BY financial_year DESC", sql)

    def test_schema_description_selects_requested_metric_over_first_numeric_column(self):
        sql = _build_dynamic_fallback(
            "ndap_ayushman_bharat_pmjay",
            {
                "columns": {
                    "state_name": "VARCHAR",
                    "cards_issued": "BIGINT - Cards issued to eligible families",
                    "empanelled_hospitals": "BIGINT - Hospitals empanelled under the scheme",
                }
            },
            {"state_name": "LADAKH"},
            "How many hospitals are empanelled in Ladakh?",
            [],
        )

        self.assertIn("SUM(empanelled_hospitals)", sql)

    def test_verified_sector_entity_is_preserved_as_a_filter(self):
        sql = _build_dynamic_fallback(
            "ndap_vocational_skill_training",
            {
                "columns": {
                    "state_name": "VARCHAR",
                    "sector_skill_council": "VARCHAR",
                    "placed_candidates": "INTEGER",
                }
            },
            {"state_name": "MAHARASHTRA", "sector_skill_council": "Automotive"},
            "How many Automotive candidates were placed in Maharashtra?",
            ["placed_candidates"],
        )

        self.assertIn("sector_skill_council = 'Automotive'", sql)

    def test_multilingual_commodity_aliases_are_canonicalized(self):
        cases = {
            "महाराष्ट्रात कांद्याचा भाव": "ONION",
            "தமிழ்நாட்டில் நிலக்கடலை உற்பத்தி": "GROUNDNUT",
            "পশ্চিমবঙ্গে আলুর দাম": "POTATO",
            "ఆంధ్రప్రదేశ్‌లో మిర్చి ధర": "CHILLI",
        }

        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(extract_canonical_entities(query)["commodity"], expected)

    def test_explicit_commodity_overrides_an_incorrect_fuzzy_match(self):
        self.assertEqual(
            extract_canonical_entities("average modal price of onion in Maharashtra")["commodity"],
            "ONION",
        )

    def test_specific_metric_description_beats_generic_programme_match(self):
        cases = (
            (
                "ndap_ayushman_bharat_pmjay",
                {"cards_issued": "BIGINT - issued cards", "empanelled_hospitals": "BIGINT - hospitals empanelled"},
                "How many hospitals are empanelled under Ayushman Bharat?",
                "empanelled_hospitals",
            ),
            (
                "ndap_pmgsy_rural_roads",
                {"completed_road_length_km": "DOUBLE - completed road length", "habitations_connected": "INTEGER - habitations connected"},
                "How many habitations were connected under PMGSY?",
                "habitations_connected",
            ),
        )
        for table, columns, query, expected in cases:
            with self.subTest(query=query):
                sql = _build_dynamic_fallback(table, {"columns": columns}, {}, query, [])
                self.assertIn(f"SUM({expected})", sql)

    def test_sector_aliases_and_generic_crop_requests_are_grounded_safely(self):
        self.assertEqual(
            extract_canonical_entities("Maharashtra me Automotive sector me candidates placed hue")[
                "sector_skill_council"
            ],
            "Automotive",
        )
        self.assertNotIn(
            "commodity",
            extract_canonical_entities("ఆంధ్రప్రదేశ్‌లో మొత్తం పంటల ఉత్పత్తి ఎన్ని టన్నులు?"),
        )

    def test_scalar_price_extremes_do_not_become_district_rankings(self):
        sql = _build_dynamic_fallback(
            "ndap_mandi_commodity_prices",
            {"columns": {"state_name": "VARCHAR", "district_name": "VARCHAR", "max_price_inr": "DOUBLE"}},
            {"state_name": "TAMIL NADU", "commodity": "ONION"},
            "தமிழ்நாட்டில் வெங்காயத்தின் அதிகபட்ச விலை என்ன?",
            ["max_price_inr"],
        )
        self.assertIn("MAX(max_price_inr)", sql)
        self.assertNotIn("GROUP BY district_name", sql)

    def test_marathi_minimum_uses_minimum_not_average(self):
        sql = _build_dynamic_fallback(
            "ndap_mandi_commodity_prices",
            {"columns": {"state_name": "VARCHAR", "min_price_inr": "DOUBLE"}},
            {"state_name": "MAHARASHTRA", "commodity": "TOMATO"},
            "महाराष्ट्रात टोमॅटोचा किमान भाव काय होता?",
            ["min_price_inr"],
        )
        self.assertIn("MIN(min_price_inr)", sql)

    def test_district_superlative_aggregates_before_ranking(self):
        sql = _build_dynamic_fallback(
            "ndap_pmay_rural_housing",
            {"columns": {"state_name": "VARCHAR", "district_name": "VARCHAR", "houses_completed": "INTEGER"}},
            {"state_name": "MADHYA PRADESH"},
            "Which district completed the highest number of houses?",
            ["houses_completed"],
        )
        self.assertIn("SUM(houses_completed)", sql)
        self.assertIn("GROUP BY district_name", sql)

    def test_hinglish_highest_district_ranking_survives_metric_guard(self):
        query = "PMAY me sabse zyada houses kis district me complete hue?"
        sql = (
            "SELECT district_name, SUM(houses_completed) AS total_houses_completed "
            "FROM ndap_pmay_rural_housing GROUP BY district_name "
            "ORDER BY total_houses_completed DESC LIMIT 1;"
        )
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_pmay_rural_housing")
        self.assertIn("GROUP BY district_name", cleaned)
        self.assertIn("ORDER BY total_houses_completed DESC", cleaned)

    def test_ratio_measure_uses_average_even_without_rate_suffix(self):
        sql = _build_dynamic_fallback(
            "ndap_maternal_child_mortality",
            {"columns": {"state_name": "VARCHAR", "maternal_mortality_ratio_mmr": "FLOAT - Maternal mortality ratio"}},
            {"state_name": "MADHYA PRADESH"},
            "What was the maternal mortality ratio in Madhya Pradesh?",
            ["maternal_mortality_ratio_mmr"],
        )
        self.assertIn("AVG(maternal_mortality_ratio_mmr)", sql)


if __name__ == "__main__":
    unittest.main()
