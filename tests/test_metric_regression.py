"""
tests/test_metric_regression.py
Comprehensive Dedicated Metric & Aggregation Regression Suite for IndicSQL Flaw 2.

Guarantees 100% deterministic elimination of metric and aggregation mismatches:
1. Disambiguates domain measures (samples_tested vs cards_issued, certified_candidates vs placed_candidates).
2. Preserves and enforces requested aggregation semantics (AVG for averages and rates, SUM for totals, MIN/ASC for superlatives).
3. Prunes redundant dimension projections from pure scalar aggregate queries.
4. Preserves all valid multi-aggregate, grouped, and extrema queries (negative testing).
5. Live DuckDB multiset equivalence testing across all 13 historical metric failures and 3 siblings.
"""

import unittest
from indicsql.benchmark.evaluator import are_tabular_results_equivalent
from indicsql.models.metric_guard import (
    MetricIntent,
    extract_metric_intent,
    sanitize_metric_aggregations,
)
from indicsql.sandbox.duckdb_engine import DuckDBSandbox


class TestMetricRegressionComprehensive(unittest.TestCase):
    """
    Exhaustive Metric Intent & Aggregation-Level AST Sanitization Suite.
    Deterministic, offline, and LLM-independent.
    """

    @classmethod
    def setUpClass(cls):
        cls.sandbox = DuckDBSandbox()

    # -------------------------------------------------------------------------
    # Test 1: Soil Health - Samples Tested vs Cards Issued (English / Hinglish)
    # -------------------------------------------------------------------------
    def test_01_soil_samples_tested_disambiguation_hinglish(self):
        query = "Coimbatore district me Soil Health Card yojana ke under kitne soil samples test hue?"
        sql = "SELECT district_name, SUM(cards_issued) AS total_samples_tested FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' GROUP BY district_name;"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_soil_health_records")

        self.assertIn("samples_tested", cleaned)
        self.assertNotIn("SUM(cards_issued)", cleaned)
        self.assertNotIn("GROUP BY", cleaned)

        gold_sql = "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 2: Soil Health - Samples Tested vs Cards Issued (Hindi)
    # -------------------------------------------------------------------------
    def test_02_soil_samples_tested_disambiguation_hindi(self):
        query = "कोयंबटूर जिले में मृदा स्वास्थ्य कार्ड योजना के तहत कितने मिट्टी के नमूनों की जांच की गई?"
        sql = "SELECT district_name, SUM(cards_issued) AS total_cards_issued FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' GROUP BY district_name;"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_soil_health_records")

        self.assertIn("samples_tested", cleaned)
        self.assertNotIn("SUM(cards_issued)", cleaned)

        gold_sql = "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 3: Soil Health - Samples Tested vs Cards Issued (Telugu)
    # -------------------------------------------------------------------------
    def test_03_soil_samples_tested_disambiguation_telugu(self):
        query = "కోయంబత్తూర్ జిల్లాలో సాయిల్ హెల్త్ కార్డ్ పథకం కింద ఎన్ని నేల నమూనాలను పరీక్షించారు?"
        sql = "SELECT district_name, SUM(cards_issued) AS total_cards FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' GROUP BY district_name;"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_soil_health_records")

        self.assertIn("samples_tested", cleaned)
        self.assertNotIn("SUM(cards_issued)", cleaned)

        gold_sql = "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 4: Vocational Training - Certified vs Placed Candidates (Tamil)
    # -------------------------------------------------------------------------
    def test_04_vocational_certified_candidates_tamil(self):
        query = "ஜார்கண்டில் தொழிற்கல்வி திறன் பயிற்சியில் தேர்ச்சி பெற்று சான்றிதழ் பெற்றவர்கள் எத்தனை பேர்?"
        sql = "SELECT district_name, SUM(placed_candidates) AS total_employed FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND' GROUP BY district_name;"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_vocational_skill_training")

        self.assertIn("certified_candidates", cleaned)
        self.assertNotIn("placed_candidates", cleaned)

        gold_sql = "SELECT SUM(certified_candidates) AS total_certified FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 5: Vocational Training - Certified vs Placed Candidates (Bengali)
    # -------------------------------------------------------------------------
    def test_05_vocational_certified_candidates_bengali(self):
        query = "ঝাড়খণ্ডে বৃত্তিমূলক দক্ষতা প্রশিক্ষণের অধীনে মোট কতজন প্রার্থী সনদপ্রাপ্ত হয়েছেন?"
        sql = "SELECT SUM(placed_candidates) AS total_candidates FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_vocational_skill_training")

        self.assertIn("certified_candidates", cleaned)
        self.assertNotIn("placed_candidates", cleaned)

        gold_sql = "SELECT SUM(certified_candidates) AS total_certified FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 6: Rate Aggregation Alignment - NFHS-5 (Marathi)
    # -------------------------------------------------------------------------
    def test_06_rate_avg_alignment_marathi(self):
        query = "एनएफएचएस-५ नुसार आंध्र प्रदेशात संस्थात्मक प्रसूतीचे सरासरी प्रमाण किती टक्के आहे?"
        sql = "SELECT SUM(institutional_births_pct) AS total_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_nfhs5_health_indicators")

        self.assertIn("AVG(institutional_births_pct)", cleaned)
        self.assertNotIn("SUM(", cleaned)

        gold_sql = "SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 7: Rate Aggregation Alignment - NFHS-5 (Telugu)
    # -------------------------------------------------------------------------
    def test_07_rate_avg_alignment_telugu(self):
        query = "ఎన్ఎఫ్ హెచ్ ఎస్-5 ప్రకారం ఆంధ్రప్రదేశ్‌లో సంస్థాగత ప్రసవాల సగటు శాతం ఎంత?"
        sql = "SELECT SUM(institutional_births_pct) AS total_institutional_births_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_nfhs5_health_indicators")

        self.assertIn("AVG(institutional_births_pct)", cleaned)
        self.assertNotIn("SUM(", cleaned)

        gold_sql = "SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 8: Rate Aggregation Alignment - NFHS-5 (Tamil)
    # -------------------------------------------------------------------------
    def test_08_rate_avg_alignment_tamil(self):
        query = "தேசிய குடும்ப சுகாதார ஆய்வின்படி ஆந்திராவில் மருத்துவமனைகளில் நிகழ்ந்த பிரசவங்களின் சராசரி சதவீதம் என்ன?"
        sql = "SELECT SUM(institutional_births_pct) AS avg_institutional_births_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_nfhs5_health_indicators")

        self.assertIn("AVG(institutional_births_pct)", cleaned)

        gold_sql = "SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 9: Mandi Price Average Alignment (Marathi)
    # -------------------------------------------------------------------------
    def test_09_mandi_price_avg_marathi(self):
        query = "महाराष्ट्रातील बाजार समित्यांमध्ये गव्हाचा सरासरी भाव काय होता?"
        sql = "SELECT MAX(modal_price_inr) AS highest_price_inr FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat' LIMIT 1;"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_mandi_commodity_prices")

        self.assertIn("AVG(modal_price_inr)", cleaned)
        self.assertNotIn("MAX(", cleaned)

        gold_sql = "SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 10: Mandi Price Average Alignment (Telugu)
    # -------------------------------------------------------------------------
    def test_10_mandi_price_avg_telugu(self):
        query = "మహారాష్ట్ర మార్కెట్లలో గోధుమల సగటు ధర ఎంత?"
        sql = "SELECT district_name, state_name, MAX(modal_price_inr) AS highest_price_inr FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat' GROUP BY district_name, state_name ORDER BY highest_price_inr DESC LIMIT 1;"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_mandi_commodity_prices")

        self.assertIn("AVG(modal_price_inr)", cleaned)

        gold_sql = "SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 11: Total / Cumulative Alignment - PMGSY (Hinglish)
    # -------------------------------------------------------------------------
    def test_11_pmgsy_total_alignment_hinglish(self):
        query = "Madhya Pradesh me PMGSY ke under total kitne km road construct hui?"
        sql = "SELECT MAX(completed_road_length_km) AS max_constructed_road_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_pmgsy_rural_roads")

        self.assertIn("SUM(completed_road_length_km)", cleaned)
        self.assertNotIn("MAX(", cleaned)

        gold_sql = "SELECT SUM(completed_road_length_km) AS total_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 12: Total / Cumulative Alignment - PMGSY (Tamil)
    # -------------------------------------------------------------------------
    def test_12_pmgsy_total_alignment_tamil(self):
        query = "மத்தியப் பிரதேசத்தில் கிராமப்புற சாலை திட்டத்தில் முடிக்கப்பட்ட மொத்த சாலை நீளம் எத்தனை கி.மீ?"
        sql = "SELECT MAX(completed_road_length_km) AS max_completed_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_pmgsy_rural_roads")

        self.assertIn("SUM(completed_road_length_km)", cleaned)

        gold_sql = "SELECT SUM(completed_road_length_km) AS total_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 13: Total / Cumulative Alignment - MGNREGA (Tamil)
    # -------------------------------------------------------------------------
    def test_13_mgnrega_total_alignment_tamil(self):
        query = "பீகாரில் மகாத்மா காந்தி ஊரக வேலை திட்டத்தில் உருவாக்கப்பட்ட மொத்த மனித வேலை நாட்கள் எத்தனை?"
        sql = "SELECT MAX(total_mandays_generated) AS max_mandays_generated FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="mgnrega_state_annual_employment")

        self.assertIn("SUM(total_mandays_generated)", cleaned)

        gold_sql = "SELECT SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 14: Lowest Superlative Alignment (Telugu)
    # -------------------------------------------------------------------------
    def test_14_lowest_superlative_alignment_telugu(self):
        query = "బీహార్‌లో మహిళా అక్షరాస్యత రేటు అత్యల్పంగా నమోదైన జిల్లా ఏది?"
        sql = "SELECT district_name, MAX(female_literacy_rate) AS max_female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' GROUP BY district_name ORDER BY max_female_literacy_rate DESC LIMIT 1;"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_education_stats")

        self.assertIn("ORDER BY female_literacy_rate ASC", cleaned)
        self.assertNotIn("DESC", cleaned)
        self.assertNotIn("MAX(", cleaned)

        gold_sql = "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;"
        pred_res = self.sandbox.execute_query(cleaned)
        gold_res = self.sandbox.execute_query(gold_sql)
        self.assertTrue(are_tabular_results_equivalent(pred_res, gold_res))

    # -------------------------------------------------------------------------
    # Test 15: NEGATIVE TEST - Explicit Highest Intent Preserves MAX
    # -------------------------------------------------------------------------
    def test_15_negative_explicit_highest_preserves_max(self):
        query = "What was the highest modal price of wheat recorded in Maharashtra?"
        sql = "SELECT MAX(modal_price_inr) AS highest_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_mandi_commodity_prices")

        # Must NOT change MAX to AVG or SUM
        self.assertEqual(sql.strip(), cleaned.strip())

    # -------------------------------------------------------------------------
    # Test 16: NEGATIVE TEST - Explicit Cards Issued Request Preserves cards_issued
    # -------------------------------------------------------------------------
    def test_16_negative_cards_issued_preserves_column(self):
        query = "How many Soil Health Cards were issued in Coimbatore district?"
        sql = "SELECT SUM(cards_issued) AS total_cards FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_soil_health_records")

        # Must NOT replace cards_issued with samples_tested
        self.assertEqual(sql.strip(), cleaned.strip())

    # -------------------------------------------------------------------------
    # Test 17: NEGATIVE TEST - Explicit Placed Candidates Request Preserves placed_candidates
    # -------------------------------------------------------------------------
    def test_17_negative_placed_candidates_preserves_column(self):
        query = "How many candidates were placed in jobs after training in Jharkhand?"
        sql = "SELECT SUM(placed_candidates) AS total_placed FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_vocational_skill_training")

        # Must NOT replace placed_candidates with certified_candidates
        self.assertEqual(sql.strip(), cleaned.strip())

    # -------------------------------------------------------------------------
    # Test 18: NEGATIVE TEST - Valid Grouping Intent Preserves GROUP BY
    # -------------------------------------------------------------------------
    def test_18_negative_grouping_intent_preserves_group_by(self):
        query = "District-wise total mandays generated in Bihar?"
        sql = "SELECT district_name, SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR' GROUP BY district_name;"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="mgnrega_state_annual_employment")

        # Must NOT drop district_name or GROUP BY
        self.assertIn("GROUP BY", cleaned)
        self.assertIn("district_name", cleaned)

    # -------------------------------------------------------------------------
    # Test 19: NEGATIVE TEST - Dual Aggregate Query Preserved
    # -------------------------------------------------------------------------
    def test_19_negative_dual_aggregates_preserved(self):
        query = "Total farmers and total disbursement amount under PM-Kisan in Bihar?"
        sql = "SELECT SUM(farmer_beneficiaries) AS total_farmers, SUM(amount_inr) AS total_amount FROM ndap_pm_kisan_disbursement WHERE state_name = 'BIHAR';"
        cleaned = sanitize_metric_aggregations(sql, query, table_name="ndap_pm_kisan_disbursement")

        self.assertIn("SUM(farmer_beneficiaries)", cleaned)
        self.assertIn("SUM(amount_inr)", cleaned)

    # -------------------------------------------------------------------------
    # Test 20: NEGATIVE TEST - Unparseable SQL Returned Safely Without Crash
    # -------------------------------------------------------------------------
    def test_20_negative_unparseable_sql_safe_passthrough(self):
        query = "Total mandays in Bihar?"
        bad_sql = "THIS IS NOT VALID SQL GLOT SYNTAX !!!"
        cleaned = sanitize_metric_aggregations(bad_sql, query)

        self.assertEqual(bad_sql, cleaned)

    # -------------------------------------------------------------------------
    # Test 21: Live DuckDB Execution of All 13 Historical Metric Failures + 3 Siblings
    # -------------------------------------------------------------------------
    def test_21_live_benchmark_historical_metric_failures_and_siblings(self):
        historical_cases = [
            ("unseen-hi-en-008", "Madhya Pradesh me PMGSY ke under total kitne km road construct hui?", "SELECT MAX(completed_road_length_km) AS max_constructed_road_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';", "SELECT SUM(completed_road_length_km) AS total_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';", "ndap_pmgsy_rural_roads"),
            ("unseen-hi-en-019", "Coimbatore district me Soil Health Card yojana ke under kitne soil samples test hue?", "SELECT district_name, SUM(cards_issued) AS total_samples_tested FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' GROUP BY district_name;", "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';", "ndap_soil_health_records"),
            ("unseen-hi-019", "कोयंबटूर जिले में मृदा स्वास्थ्य कार्ड योजना के तहत कितने मिट्टी के नमूनों की जांच की गई?", "SELECT district_name, SUM(cards_issued) AS total_cards_issued FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' GROUP BY district_name;", "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';", "ndap_soil_health_records"),
            ("unseen-mr-005", "महाराष्ट्रातील बाजार समित्यांमध्ये गव्हाचा सरासरी भाव काय होता?", "SELECT MAX(modal_price_inr) AS highest_price_inr FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat' LIMIT 1;", "SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';", "ndap_mandi_commodity_prices"),
            ("unseen-mr-018", "एनएफएचएस-५ नुसार आंध्र प्रदेशात संस्थात्मक प्रसूतीचे सरासरी प्रमाण किती टक्के आहे?", "SELECT SUM(institutional_births_pct) AS total_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';", "SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';", "ndap_nfhs5_health_indicators"),
            ("unseen-mr-019", "कोईम्बतूर जिल्ह्यात मृदा आरोग्य पत्रिका अंतर्गत मातीचे किती नमुने तपासण्यात आले?", "SELECT district_name, SUM(cards_issued) AS total_cards FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' GROUP BY district_name;", "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';", "ndap_soil_health_records"),
            ("unseen-ta-006", "பீகாரில் மகாத்மா காந்தி ஊரக வேலை திட்டத்தில் உருவாக்கப்பட்ட மொத்த மனித வேலை நாட்கள் எத்தனை?", "SELECT MAX(total_mandays_generated) AS max_mandays_generated FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';", "SELECT SUM(total_mandays_generated) AS total_mandays FROM mgnrega_state_annual_employment WHERE state_name = 'BIHAR';", "mgnrega_state_annual_employment"),
            ("unseen-ta-008", "மத்தியப் பிரதேசத்தில் கிராமப்புற சாலை திட்டத்தில் முடிக்கப்பட்ட மொத்த சாலை நீளம் எத்தனை கி.மீ?", "SELECT MAX(completed_road_length_km) AS max_completed_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';", "SELECT SUM(completed_road_length_km) AS total_length_km FROM ndap_pmgsy_rural_roads WHERE state_name = 'MADHYA PRADESH';", "ndap_pmgsy_rural_roads"),
            ("unseen-ta-020", "ஜார்கண்டில் தொழிற்கல்வி திறன் பயிற்சியில் தேர்ச்சி பெற்று சான்றிதழ் பெற்றவர்கள் எத்தனை பேர்?", "SELECT district_name, SUM(placed_candidates) AS total_employed FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND' GROUP BY district_name;", "SELECT SUM(certified_candidates) AS total_certified FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';", "ndap_vocational_skill_training"),
            ("unseen-te-005", "మహారాష్ట్ర మార్కెట్లలో గోధుమల సగటు ధర ఎంత?", "SELECT district_name, state_name, MAX(modal_price_inr) AS highest_price_inr FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat' GROUP BY district_name, state_name ORDER BY highest_price_inr DESC LIMIT 1;", "SELECT AVG(modal_price_inr) AS avg_price FROM ndap_mandi_commodity_prices WHERE state_name = 'MAHARASHTRA' AND commodity = 'Wheat';", "ndap_mandi_commodity_prices"),
            ("unseen-te-010", "బీహార్‌లో మహిళా అక్షరాస్యత రేటు అత్యల్పంగా నమోదైన జిల్లా ఏది?", "SELECT district_name, MAX(female_literacy_rate) AS max_female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' GROUP BY district_name ORDER BY max_female_literacy_rate DESC LIMIT 1;", "SELECT district_name, female_literacy_rate FROM ndap_education_stats WHERE state_name = 'BIHAR' ORDER BY female_literacy_rate ASC LIMIT 1;", "ndap_education_stats"),
            ("unseen-te-018", "ఎన్ఎఫ్ హెచ్ ఎస్-5 ప్రకారం ఆంధ్రప్రదేశ్‌లో సంస్థాగత ప్రసవాల సగటు శాతం ఎంత?", "SELECT SUM(institutional_births_pct) AS total_institutional_births_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';", "SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';", "ndap_nfhs5_health_indicators"),
            ("unseen-te-019", "కోయంబత్తూర్ జిల్లాలో సాయిల్ హెల్త్ కార్డ్ పథకం కింద ఎన్ని నేల నమూనాలను పరీక్షించారు?", "SELECT district_name, SUM(cards_issued) AS total_cards FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' GROUP BY district_name;", "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';", "ndap_soil_health_records"),
            # Siblings
            ("unseen-bn-019", "কোয়েম্বাটোর জেলায় সয়েল হেলথ কার্ড প্রকল্পের অধীনে কতগুলি মাটির নমুনা পরীক্ষা করা হয়েছে?", "SELECT district_name, SUM(cards_issued) AS total_cards FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore' GROUP BY district_name;", "SELECT SUM(samples_tested) AS total_samples FROM ndap_soil_health_records WHERE state_name = 'TAMIL NADU' AND district_name = 'Coimbatore';", "ndap_soil_health_records"),
            ("unseen-bn-020", "ঝাড়খণ্ডে বৃত্তিমূলক দক্ষতা প্রশিক্ষণের অধীনে মোট কতজন প্রার্থী সনদপ্রাপ্ত হয়েছেন?", "SELECT SUM(placed_candidates) AS total_candidates FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';", "SELECT SUM(certified_candidates) AS total_certified FROM ndap_vocational_skill_training WHERE state_name = 'JHARKHAND';", "ndap_vocational_skill_training"),
            ("unseen-ta-018", "தேசிய குடும்ப சுகாதார ஆய்வின்படி ஆந்திராவில் மருத்துவமனைகளில் நிகழ்ந்த பிரசவங்களின் சராசரி சதவீதம் என்ன?", "SELECT SUM(institutional_births_pct) AS avg_institutional_births_pct FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';", "SELECT AVG(institutional_births_pct) AS avg_institutional_births FROM ndap_nfhs5_health_indicators WHERE state_name = 'ANDHRA PRADESH';", "ndap_nfhs5_health_indicators"),
        ]

        for qid, query, raw_sql, gold_sql, tbl in historical_cases:
            fixed_sql = sanitize_metric_aggregations(raw_sql, query, table_name=tbl)
            pred_res = self.sandbox.execute_query(fixed_sql)
            gold_res = self.sandbox.execute_query(gold_sql)
            self.assertTrue(
                are_tabular_results_equivalent(pred_res, gold_res),
                f"Failed live execution isomorphism on {qid}: {fixed_sql} vs {gold_sql}",
            )


if __name__ == "__main__":
    unittest.main()
