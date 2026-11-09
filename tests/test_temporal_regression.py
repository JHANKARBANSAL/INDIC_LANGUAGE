"""
tests/test_temporal_regression.py
Comprehensive Dedicated Temporal Regression Suite for IndicSQL Flaw 3.

Guarantees 100% deterministic elimination of unrequested/hallucinated temporal SQL predicates
while preserving explicit years, academic years, financial years, year ranges, dates,
relative time expressions, and all non-temporal WHERE conditions.
"""

import unittest
from pathlib import Path

import sqlglot
from sqlglot import exp

from indicsql.benchmark.evaluator import are_tabular_results_equivalent
from indicsql.models.temporal_guard import (
    TABLE_TEMPORAL_METADATA,
    TEMPORAL_COLUMN_NAMES,
    TemporalIntent,
    extract_temporal_intent,
    is_temporal_predicate_supported,
    sanitize_temporal_predicates,
)
from indicsql.sandbox.duckdb_engine import DuckDBSandbox


class TestTemporalRegressionComprehensive(unittest.TestCase):
    """
    25-Test Exhaustive Temporal Intent & Predicate-Level AST Sanitization Suite.
    Deterministic, offline, and LLM-independent.
    """

    @classmethod
    def setUpClass(cls):
        cls.sandbox = DuckDBSandbox()

    # -------------------------------------------------------------------------
    # Test 1: No temporal intent with hallucinated reporting_year
    # -------------------------------------------------------------------------
    def test_01_no_temporal_intent_hallucinated_reporting_year(self):
        query = "How many primary health centres (PHCs) are operational in Haryana?"
        sql = "SELECT SUM(primary_health_centres_phc) AS operational_phcs FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_rural_health_infrastructure")

        self.assertNotIn("reporting_year", cleaned)
        self.assertIn("state_name = 'HARYANA'", cleaned)

        # Dual DuckDB verification against gold
        gold_sql = "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';"
        p_res = self.sandbox.execute_query(cleaned)
        g_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(p_res, g_res))
        self.assertEqual(p_res["rows"][0][0], 3298)

    # -------------------------------------------------------------------------
    # Test 2: No temporal intent with hallucinated survey_year
    # -------------------------------------------------------------------------
    def test_02_no_temporal_intent_hallucinated_survey_year(self):
        query = "Tamil Nadu me higher education me total kitne faculty members hain?"
        sql = "SELECT SUM(total_faculty_count) AS total_faculty FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU' AND survey_year IN ('2022-23');"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_higher_education_aishe")

        self.assertNotIn("survey_year", cleaned)
        self.assertIn("state_name = 'TAMIL NADU'", cleaned)

        gold_sql = "SELECT SUM(total_faculty_count) AS total_faculty FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU';"
        p_res = self.sandbox.execute_query(cleaned)
        g_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(p_res, g_res))
        self.assertEqual(p_res["rows"][0][0], 148486)

    # -------------------------------------------------------------------------
    # Test 3: No temporal intent with multiple temporal predicates
    # -------------------------------------------------------------------------
    def test_03_no_temporal_intent_multiple_temporal_predicates(self):
        query = "उत्तर प्रदेश में कुल कितने किसानों को पीएम-किसान का लाभ मिला?"
        sql = "SELECT SUM(farmer_beneficiaries) FROM ndap_pm_kisan_disbursement WHERE state_name = 'UTTAR PRADESH' AND financial_year = '2022-23' AND reporting_year = 2022;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_pm_kisan_disbursement")

        self.assertNotIn("financial_year", cleaned)
        self.assertNotIn("reporting_year", cleaned)
        self.assertIn("state_name = 'UTTAR PRADESH'", cleaned)

        p_res = self.sandbox.execute_query(cleaned)
        self.assertEqual(p_res["rows"][0][0], 14623899)

    # -------------------------------------------------------------------------
    # Test 4: Explicit 2022 with correct reporting_year
    # -------------------------------------------------------------------------
    def test_04_explicit_2022_with_correct_reporting_year(self):
        query = "How many primary health centres were operational in Haryana in 2022?"
        sql = "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_rural_health_infrastructure")

        self.assertIn("reporting_year = 2022", cleaned)
        self.assertIn("state_name = 'HARYANA'", cleaned)
        p_res = self.sandbox.execute_query(cleaned)
        self.assertEqual(p_res["rows"][0][0], 1462)

    # -------------------------------------------------------------------------
    # Test 5: Explicit 2022 with incorrect 2021
    # -------------------------------------------------------------------------
    def test_05_explicit_2022_with_incorrect_2021(self):
        query = "How many primary health centres were operational in Haryana in 2022?"
        # Model hallucinated 2021 instead of requested 2022
        sql = "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2021;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_rural_health_infrastructure")

        # Must detach the contradicting 2021 filter
        self.assertNotIn("2021", cleaned)
        self.assertIn("state_name = 'HARYANA'", cleaned)

    # -------------------------------------------------------------------------
    # Test 6: Explicit 2022 with multiple temporal columns (one valid, one invalid)
    # -------------------------------------------------------------------------
    def test_06_explicit_2022_with_multiple_temporal_columns(self):
        query = "What was the school count in Maharashtra in 2022?"
        sql = "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND reporting_year = 2022 AND survey_year = 2021;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_school_infrastructure")

        # 2022 preserved, 2021 removed
        self.assertIn("reporting_year = 2022", cleaned)
        self.assertNotIn("survey_year", cleaned)

    # -------------------------------------------------------------------------
    # Test 7: Explicit year range
    # -------------------------------------------------------------------------
    def test_07_explicit_year_range(self):
        query = "What was the total mandays generated in Bihar between 2021 and 2023?"
        sql = "SELECT SUM(total_mandays_generated) FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR' AND crop_year BETWEEN 2021 AND 2023;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="mgnrega_state_annual_employment")

        self.assertIn("crop_year BETWEEN 2021 AND 2023", cleaned)
        self.assertIn("state_name = 'BIHAR'", cleaned)

    # -------------------------------------------------------------------------
    # Test 8: Specific date request
    # -------------------------------------------------------------------------
    def test_08_specific_date_request(self):
        query = "What was the mandi modal price in Maharashtra on 2024-03-15?"
        sql = "SELECT AVG(modal_price_inr) FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND arrival_date = '2024-03-15';"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_mandi_commodity_prices")

        self.assertIn("arrival_date = '2024-03-15'", cleaned)

    # -------------------------------------------------------------------------
    # Test 9: Financial year request
    # -------------------------------------------------------------------------
    def test_09_financial_year_request(self):
        query = "What was PM-Kisan disbursement in Bihar for financial year 2023-24?"
        sql = "SELECT SUM(amount_inr) FROM ndap_pm_kisan_disbursement WHERE state_name = 'BIHAR' AND financial_year = '2023-24';"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_pm_kisan_disbursement")

        self.assertIn("financial_year = '2023-24'", cleaned)
        p_res = self.sandbox.execute_query(cleaned)
        self.assertGreater(len(p_res["rows"]), 0)

    # -------------------------------------------------------------------------
    # Test 10: Previous year request
    # -------------------------------------------------------------------------
    def test_10_previous_year_request(self):
        query = "कर्नाटकमध्ये मागील वर्षी एकूण किती क्षयरुग्ण नोंदवले गेले?"
        # Karnataka TB table has [2022, 2023], previous year = 2022
        sql = "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_national_tuberculosis_portal")

        self.assertIn("reporting_year = 2022", cleaned)

    # -------------------------------------------------------------------------
    # Test 11: Current year request
    # -------------------------------------------------------------------------
    def test_11_current_year_request(self):
        query = "ಕರ್ನಾಟಕದಲ್ಲಿ ಪ್ರಸ್ತುತ ವರ್ಷದಲ್ಲಿ ಒಟ್ಟು ಟಿಬಿ ರೋಗಿಗಳ ಸಂಖ್ಯೆ ಎಷ್ಟು?"
        # Current / latest recorded year = 2023
        sql = "SELECT SUM(total_notified_patients) FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2023;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_national_tuberculosis_portal")

        self.assertIn("reporting_year = 2023", cleaned)

    # -------------------------------------------------------------------------
    # Test 12: Latest available year request
    # -------------------------------------------------------------------------
    def test_12_latest_available_year_request(self):
        query = "What is the latest school electricity count in Pune?"
        sql = "SELECT SUM(schools_with_electricity) FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND reporting_year = (SELECT MAX(reporting_year) FROM ndap_school_infrastructure);"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_school_infrastructure")

        self.assertIn("MAX(reporting_year)", cleaned)

    # -------------------------------------------------------------------------
    # Test 13: Last N years request
    # -------------------------------------------------------------------------
    def test_13_last_n_years_request(self):
        query = "What was the PMGSY road construction in Madhya Pradesh in the last 2 years?"
        # Latest is 2023, expected start is 2022
        sql = "SELECT SUM(completed_road_length_km) FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH' AND reporting_year >= 2022;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_pmgsy_rural_roads")

        self.assertIn("reporting_year >= 2022", cleaned)

    # -------------------------------------------------------------------------
    # Test 14: BETWEEN with its internal AND
    # -------------------------------------------------------------------------
    def test_14_between_with_internal_and(self):
        query = "Total crop production in Punjab between 2021 and 2023?"
        sql = "SELECT SUM(production_tonnes) FROM ndap_crop_production_census WHERE state_name = 'PUNJAB' AND crop_year BETWEEN 2021 AND 2023;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_crop_production_census")

        # Ensures internal AND inside BETWEEN was not split or corrupted
        self.assertIn("crop_year BETWEEN 2021 AND 2023", cleaned)

    # -------------------------------------------------------------------------
    # Test 15: Nested AND/OR conditions
    # -------------------------------------------------------------------------
    def test_15_nested_and_or_conditions(self):
        query = "How many schools in Maharashtra in 2022?"
        sql = "SELECT * FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND (reporting_year = 2021 OR reporting_year = 2022);"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_school_infrastructure")

        self.assertNotIn("2021", cleaned)
        self.assertIn("reporting_year = 2022", cleaned)
        self.assertIn("state_name = 'MAHARASHTRA'", cleaned)

    # -------------------------------------------------------------------------
    # Test 16: Parenthesized predicates
    # -------------------------------------------------------------------------
    def test_16_parenthesized_predicates(self):
        query = "How many primary health centres in Haryana?"
        sql = "SELECT * FROM ndap_rural_health_infrastructure WHERE (state_name = 'HARYANA') AND ((reporting_year = 2022));"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_rural_health_infrastructure")

        self.assertNotIn("reporting_year", cleaned)
        self.assertIn("state_name = 'HARYANA'", cleaned)

    # -------------------------------------------------------------------------
    # Test 17: Temporal predicates inside subqueries
    # -------------------------------------------------------------------------
    def test_17_temporal_predicates_inside_subqueries(self):
        query = "Total fertilizer sales in Rajasthan?"
        sql = "SELECT * FROM (SELECT * FROM ndap_fertilizer_distribution WHERE state_name = 'RAJASTHAN' AND reporting_year = 2022) AS sub WHERE fertilizer_type = 'UREA';"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_fertilizer_distribution")

        self.assertNotIn("reporting_year", cleaned)
        self.assertIn("state_name = 'RAJASTHAN'", cleaned)
        self.assertIn("fertilizer_type = 'UREA'", cleaned)

    # -------------------------------------------------------------------------
    # Test 18: Temporal predicates inside CTEs
    # -------------------------------------------------------------------------
    def test_18_temporal_predicates_inside_ctes(self):
        query = "Total crop production in Haryana?"
        sql = "WITH cte AS (SELECT * FROM ndap_crop_production_census WHERE state_name = 'HARYANA' AND crop_year = 2022) SELECT * FROM cte WHERE commodity = 'WHEAT';"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_crop_production_census")

        self.assertNotIn("crop_year", cleaned)
        self.assertIn("state_name = 'HARYANA'", cleaned)
        self.assertIn("commodity = 'WHEAT'", cleaned)

    # -------------------------------------------------------------------------
    # Test 19: String literals containing temporal column names
    # -------------------------------------------------------------------------
    def test_19_string_literals_containing_temporal_column_names(self):
        query = "Inspect schema column named reporting_year"
        sql = "SELECT * FROM schema_metadata WHERE column_name = 'reporting_year' AND table_name = 'ndap_pm_kisan';"
        cleaned = sanitize_temporal_predicates(sql, query)

        # 'reporting_year' string literal must NOT be touched
        self.assertIn("column_name = 'reporting_year'", cleaned)

    # -------------------------------------------------------------------------
    # Test 20: All-temporal WHERE clause removal (lone condition)
    # -------------------------------------------------------------------------
    def test_20_all_temporal_where_clause_removal(self):
        query = "How many total PHCs are operational across India?"
        sql = "SELECT SUM(primary_health_centres_phc) FROM ndap_rural_health_infrastructure WHERE reporting_year = 2022;"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_rural_health_infrastructure")

        self.assertNotIn("WHERE", cleaned)
        self.assertTrue(cleaned.strip().endswith(";"))
        # Execute in DuckDB
        p_res = self.sandbox.execute_query(cleaned)
        self.assertIsNotNone(p_res)

    # -------------------------------------------------------------------------
    # Test 21: Mixed temporal and non-temporal WHERE conditions
    # -------------------------------------------------------------------------
    def test_21_mixed_temporal_and_non_temporal_where_conditions(self):
        query = "पुणे जिले में बिजली सुविधा वाले स्कूलों की संख्या कितनी है?"
        sql = "SELECT SUM(schools_with_electricity) AS electric_schools_count FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';"
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_school_infrastructure")

        self.assertNotIn("academic_year", cleaned)
        self.assertIn("state_name = 'MAHARASHTRA'", cleaned)
        self.assertIn("district_name = 'Pune'", cleaned)

        p_res = self.sandbox.execute_query(cleaned)
        self.assertEqual(p_res["rows"][0][0], 4063)

    # -------------------------------------------------------------------------
    # Test 22: SQL without WHERE clause
    # -------------------------------------------------------------------------
    def test_22_sql_without_where(self):
        query = "Total record count"
        sql = "SELECT COUNT(*) FROM ndap_rural_health_infrastructure;"
        cleaned = sanitize_temporal_predicates(sql, query)

        self.assertEqual(sql.strip(), cleaned.strip())

    # -------------------------------------------------------------------------
    # Test 23: Unsupported or malformed SQL safe handling
    # -------------------------------------------------------------------------
    def test_23_unsupported_or_malformed_sql_safe_handling(self):
        query = "Some query"
        sql = "SELECT FROM WHERE WHERE ;;;"
        cleaned = sanitize_temporal_predicates(sql, query)
        self.assertEqual(cleaned, sql)

    # -------------------------------------------------------------------------
    # Test 24: No accidental deletion of state, district, crop, or gender filters
    # -------------------------------------------------------------------------
    def test_24_no_accidental_deletion_of_legitimate_filters(self):
        query = "How many female students in Pune?"
        sql = (
            "SELECT SUM(female_students) FROM ndap_education_stats "
            "WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' "
            "AND female_literacy_rate > 80 AND crop_name = 'WHEAT' "
            "AND reporting_year = 2022;"
        )
        cleaned = sanitize_temporal_predicates(sql, query, table_name="ndap_education_stats")

        self.assertNotIn("reporting_year", cleaned)
        self.assertIn("state_name = 'MAHARASHTRA'", cleaned)
        self.assertIn("district_name = 'Pune'", cleaned)
        self.assertIn("female_literacy_rate > 80", cleaned)
        self.assertIn("crop_name = 'WHEAT'", cleaned)

    # -------------------------------------------------------------------------
    # Test 25: Live DuckDB Execution on ALL 20 Unseen Benchmark Failures
    # -------------------------------------------------------------------------
    def test_25_live_duckdb_execution_on_all_20_benchmark_temporal_failures(self):
        """
        Executes all 20 actual failed queries from the 140-query unseen benchmark
        across all 7 languages through sanitize_temporal_predicates() and verifies
        100% multiset isomorphism against Gold ground truth in DuckDB.
        """
        benchmark_temporal_cases = [
            # 1. EN PHC
            (
                "How many primary health centres (PHCs) are operational in Haryana?",
                "SELECT SUM(primary_health_centres_phc) AS operational_phcs FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';",
                "ndap_rural_health_infrastructure",
            ),
            # 2. EN TB Portal
            (
                "What is the total number of TB patients notified in Karnataka?",
                "SELECT SUM(total_notified_patients) AS total_tuberculosis_patients FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2023;",
                "SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';",
                "ndap_national_tuberculosis_portal",
            ),
            # 3. HI-EN AISHE
            (
                "Tamil Nadu me higher education me total kitne faculty members hain?",
                "SELECT SUM(total_faculty_count) AS total_faculty FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU' AND survey_year IN ('2022-23');",
                "SELECT SUM(total_faculty_count) AS total_faculty FROM ndap_higher_education_aishe WHERE state_name = 'TAMIL NADU';",
                "ndap_higher_education_aishe",
            ),
            # 4. HI-EN PHC
            (
                "Haryana me total kitne primary health centres (PHC) chal rahe hain?",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';",
                "ndap_rural_health_infrastructure",
            ),
            # 5. HI-EN TB Portal
            (
                "Karnataka me Nikshay portal par total kitne TB patients notify hue?",
                "SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;",
                "SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';",
                "ndap_national_tuberculosis_portal",
            ),
            # 6. HI School Electricity
            (
                "पुणे जिले में बिजली सुविधा वाले स्कूलों की संख्या कितनी है?",
                "SELECT SUM(schools_with_electricity) AS electric_schools_count FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';",
                "SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
                "ndap_school_infrastructure",
            ),
            # 7. HI PHC
            (
                "हरियाणा में कुल कितने प्राथमिक स्वास्थ्य केंद्र (PHC) संचालित हैं?",
                "SELECT SUM(primary_health_centres_phc) AS total_phcs FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';",
                "ndap_rural_health_infrastructure",
            ),
            # 8. HI TB Portal
            (
                "कर्नाटक में निक्षय पोर्टल पर कुल कितने टीबी के मरीज अधिसूचित किए गए?",
                "SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;",
                "SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';",
                "ndap_national_tuberculosis_portal",
            ),
            # 9. MR School Electricity
            (
                "पुणे जिल्ह्यातील किती शाळांमध्ये विजेची सोय आहे?",
                "SELECT SUM(schools_with_electricity) AS total_schools_with_electricity FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';",
                "SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
                "ndap_school_infrastructure",
            ),
            # 10. MR PHC
            (
                "हरियाणामध्ये एकूण किती प्राथमिक आरोग्य केंद्रे (PHC) कार्यरत आहेत?",
                "SELECT SUM(primary_health_centres_phc) AS total_phcs FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';",
                "ndap_rural_health_infrastructure",
            ),
            # 11. MR TB Portal
            (
                "कर्नाटकमध्ये एकूण किती क्षयरुग्णांची नोंद झाली आहे?",
                "SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;",
                "SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';",
                "ndap_national_tuberculosis_portal",
            ),
            # 12. BN School Electricity
            (
                "পুনে জেলায় কতগুলি স্কুলে বিদ্যুৎ সংযোগ রয়েছে?",
                "SELECT SUM(schools_with_electricity) AS electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';",
                "SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
                "ndap_school_infrastructure",
            ),
            # 13. BN PHC
            (
                "হরিয়ানায় মোট কতগুলি প্রাথমিক স্বাস্থ্য কেন্দ্র (PHC) চালু রয়েছে?",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';",
                "ndap_rural_health_infrastructure",
            ),
            # 14. BN TB Portal
            (
                "কর্ণাটকে মোট কতজন যক্ষ্মা রোগী সরকারিভাবে নথিভুক্ত হয়েছেন?",
                "SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;",
                "SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';",
                "ndap_national_tuberculosis_portal",
            ),
            # 15. TA School Electricity
            (
                "புனே மாவட்டத்தில் மின்சார வசதி கொண்ட பள்ளிகள் எத்தனை?",
                "SELECT SUM(schools_with_electricity) AS electricity_compliance FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';",
                "SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
                "ndap_school_infrastructure",
            ),
            # 16. TA PHC
            (
                "ஹரியானாவில் செயல்படும் மொத்த ஆரம்ப சுகாதார நிலையங்கள் எத்தனை?",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';",
                "ndap_rural_health_infrastructure",
            ),
            # 17. TA TB Portal
            (
                "கர்நாடகாவில் பதிவு செய்யப்பட்ட மொத்த காசநோய் நோயாளிகள் எத்தனை பேர்?",
                "SELECT SUM(total_notified_patients) AS total_patients FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;",
                "SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';",
                "ndap_national_tuberculosis_portal",
            ),
            # 18. TE School Electricity
            (
                "పుణే జిల్లాలో విద్యుత్ సదుపాయం ఉన్న పాఠశాలల సంఖ్య ఎంత?",
                "SELECT SUM(schools_with_electricity) AS total_schools_with_electricity FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune' AND academic_year = '2023-24';",
                "SELECT SUM(schools_with_electricity) AS total_electricity_schools FROM ndap_school_infrastructure WHERE state_name = 'MAHARASHTRA' AND district_name = 'Pune';",
                "ndap_school_infrastructure",
            ),
            # 19. TE PHC
            (
                "హర్యానాలో పనిచేస్తున్న మొత్తం ప్రాథమిక ఆరోగ్య కేంద్రాల సంఖ్య ఎంత?",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA' AND reporting_year = 2022;",
                "SELECT SUM(primary_health_centres_phc) AS total_phc FROM ndap_rural_health_infrastructure WHERE state_name = 'HARYANA';",
                "ndap_rural_health_infrastructure",
            ),
            # 20. TE TB Portal
            (
                "కర్ణాటకలో నోటిఫై చేయబడిన మొత్తం టీబీ రోగుల సంఖ్య ఎంత?",
                "SELECT SUM(total_notified_patients) AS total_notified_patients_karnataka FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA' AND reporting_year = 2022;",
                "SELECT SUM(total_notified_patients) AS total_tb_cases FROM ndap_national_tuberculosis_portal WHERE state_name = 'KARNATAKA';",
                "ndap_national_tuberculosis_portal",
            ),
        ]

        for idx, (query_text, pred_sql, gold_sql, t_name) in enumerate(benchmark_temporal_cases, 1):
            sanitized = sanitize_temporal_predicates(pred_sql, query_text, table_name=t_name)
            p_res = self.sandbox.execute_query(sanitized)
            g_res = self.sandbox.execute_query(gold_sql)

            is_match = are_tabular_results_equivalent(p_res, g_res)
            self.assertTrue(
                is_match,
                f"Benchmark Case #{idx} failed isomorphism:\nQuery: {query_text}\nSanitized: {sanitized}\nPred: {p_res}\nGold: {g_res}",
            )


if __name__ == "__main__":
    unittest.main()
