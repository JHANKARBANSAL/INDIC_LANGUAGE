"""
tests/test_regression.py
Automated Regression Tests for IndicSQL Bug Fixes and Reliability Guarantees.

Covers:
1. False District Collision Regression: Ensures generic words ('कुल', 'Uttar', 'mandi', 'ton', etc.)
   never collide with districts ('Kullu', 'Tura', 'Mandi', 'Thane', 'Indore', 'Bengaluru Urban').
2. State Detection Integrity: Guarantees 100% correct state mapping without hallucinating districts.
3. Genuine District Detection: Verifies true district queries (Lucknow, Varanasi, Pune, Kurnool) are extracted accurately.
4. Database Execution Regression: Verifies exact DuckDB multiset results for canonical Pan-India benchmark queries.
"""

import unittest
from indicsql.schema.entity_grounder import dynamic_entity_grounder
from indicsql.sandbox.duckdb_engine import DuckDBSandbox
from indicsql.benchmark.dataset import BenchmarkQuery
from indicsql.benchmark.evaluator import are_tabular_results_equivalent


class TestFalseDistrictCollisionRegression(unittest.TestCase):
    """
    Regression Suite for Bug A:
    Validates that high-frequency vernacular and English terms do NOT collide
    with geographically distinct districts via phonetic consonant skeleton matching.
    """

    def test_hindi_kul_does_not_match_kullu(self):
        queries = [
            "उत्तर प्रदेश में कुल कितने किसानों को पीएम-किसान का लाभ मिला?",
            "बिहार में पीएम-किसान के तहत कुल कितनी धनराशि वितरित की गई?",
            "पंजाब में गेहूं का कुल उत्पादन कितने टन हुआ?",
            "मध्य प्रदेश में कुल कितने प्राथमिक स्वास्थ्य केंद्र हैं?",
            "हरियाणा में कुल कितने स्कूल हैं?",
        ]
        for q in queries:
            grounded = dynamic_entity_grounder.ground_entities(q)
            self.assertNotEqual(
                grounded.get("district_name"),
                "Kullu",
                f"Regression failure: 'कुल' matched district 'Kullu' in query: '{q}'",
            )
            self.assertIsNone(
                grounded.get("district_name"),
                f"Unexpected district '{grounded.get('district_name')}' found in state query: '{q}'",
            )

    def test_english_uttar_does_not_match_tura(self):
        query = "What is the total amount disbursed under PM-KISAN in Uttar Pradesh?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("state_name"), "UTTAR PRADESH")
        self.assertNotEqual(
            grounded.get("district_name"),
            "Tura",
            "Regression failure: 'Uttar' matched district 'Tura' (Meghalaya)",
        )
        self.assertIsNone(grounded.get("district_name"))

    def test_mandi_word_does_not_match_district_mandi(self):
        query = "उत्तर प्रदेश की मंडियों में गेहूं का औसत मॉडल मूल्य क्या रहा?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("state_name"), "UTTAR PRADESH")
        self.assertNotEqual(
            grounded.get("district_name"),
            "Mandi",
            "Regression failure: Agricultural market 'मंडी' matched district 'Mandi' (HP)",
        )
        self.assertIsNone(grounded.get("district_name"))

    def test_ton_and_tana_do_not_match_thane(self):
        queries = [
            "पंजाब में गेहूं का कुल उत्पादन कितने टन हुआ?",
            "हरियाणा में यूरिया खाद की कुल बिक्री कितने टन हुई?",
        ]
        for q in queries:
            grounded = dynamic_entity_grounder.ground_entities(q)
            self.assertNotEqual(
                grounded.get("district_name"),
                "Thane",
                f"Regression failure: Unit 'टन' matched district 'Thane' in: '{q}'",
            )
            self.assertIsNone(grounded.get("district_name"))

    def test_telugu_andhra_does_not_match_indore(self):
        query = "ఆంధ్రప్రదేశ్ లో మొత్తం ఎంతమంది రైతులకు లబ్ధి చేకూరింది?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("state_name"), "ANDHRA PRADESH")
        self.assertNotEqual(
            grounded.get("district_name"),
            "Indore",
            "Regression failure: 'ఆంధ్రప్రదేశ్' prefix skeleton matched district 'Indore' (MP)",
        )
        self.assertIsNone(grounded.get("district_name"))

    def test_bengali_paschim_banga_does_not_match_bengaluru(self):
        query = "পশ্চিমবঙ্গে মোট কতজন কৃষক পিএম-কিষানের সুবিধা পেয়েছেন?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("state_name"), "WEST BENGAL")
        self.assertNotEqual(
            grounded.get("district_name"),
            "Bengaluru Urban",
            "Regression failure: 'পশ্চিমবঙ্গ' prefix skeleton matched district 'Bengaluru Urban'",
        )
        self.assertIsNone(grounded.get("district_name"))

    def test_tamil_modal_price_does_not_match_madurai(self):
        query = "தமிழ்நாடு சந்தைகளில் நெல்லின் சராசரி மாதிரி விலை என்ன?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("state_name"), "TAMIL NADU")
        self.assertNotEqual(
            grounded.get("district_name"),
            "Madurai",
            "Regression failure: Tamil 'மாதிரி' (modal price) matched district 'Madurai'",
        )
        self.assertIsNone(grounded.get("district_name"))


class TestCorrectStateDetection(unittest.TestCase):
    """Validates that native script state names are reliably detected across all 7 benchmark languages."""

    def test_state_detection_across_queries(self):
        cases = [
            ("उत्तर प्रदेश में कुल कितने किसान हैं?", "UTTAR PRADESH"),
            ("बिहार में पीएम-किसान का लाभ", "BIHAR"),
            ("पंजाब में गेहूं का कुल उत्पादन", "PUNJAB"),
            ("मध्य प्रदेश में कुल कितने कॉलेज हैं?", "MADHYA PRADESH"),
            ("राजस्थान में डीएपी खाद की आवश्यकता", "RAJASTHAN"),
            ("हरियाणा में यूरिया खाद की बिक्री", "HARYANA"),
            ("ఆంధ్రప్రదేశ్ లో పీఎం-కిసాన్ లబ్ధిదారులు", "ANDHRA PRADESH"),
            ("తెలంగాణలో పీఎం-కిసాన్ పథకం", "TELANGANA"),
            ("தமிழ்நாட்டில் பிஎம்-கிசான் பயனாளிகள்", "TAMIL NADU"),
            ("পশ্চিমবঙ্গে মোট ধান উৎপাদন", "WEST BENGAL"),
            ("महाराष्ट्रात एकूण किती शेतकरी आहेत?", "MAHARASHTRA"),
            ("गुजरातमध्ये भुईमुगाचे उत्पादन", "GUJARAT"),
        ]
        for query_text, expected_state in cases:
            grounded = dynamic_entity_grounder.ground_entities(query_text)
            self.assertEqual(
                grounded.get("state_name"),
                expected_state,
                f"Failed state grounding for query: '{query_text}'",
            )
            # Ensure none of these pure-state queries hallucinated a district
            self.assertIsNone(
                grounded.get("district_name"),
                f"False district detected in pure state query: '{query_text}'",
            )


class TestGenuineDistrictDetection(unittest.TestCase):
    """Validates that real district mentions in citizen queries are extracted with 100% precision."""

    def test_genuine_lucknow_district(self):
        query = "लखनऊ जिले में कुल कितने स्कूल हैं?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("district_name"), "Lucknow")
        self.assertEqual(grounded.get("state_name"), "UTTAR PRADESH")

    def test_genuine_varanasi_district(self):
        query = "वाराणसी में कुल कितने किसानों को पीएम-किसान का लाभ मिला?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("district_name"), "Varanasi")
        self.assertEqual(grounded.get("state_name"), "UTTAR PRADESH")

    def test_genuine_pune_district_marathi(self):
        query = "पुणे जिल्ह्यातील शाळांमध्ये संगणक प्रयोगशाळा किती आहेत?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("district_name"), "Pune")
        self.assertEqual(grounded.get("state_name"), "MAHARASHTRA")

    def test_genuine_kurnool_district_telugu(self):
        query = "కర్నూలు జిల్లాలో ఎంతమంది రైతులకు లబ్ధి చేకూరింది?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("district_name"), "Kurnool")
        self.assertEqual(grounded.get("state_name"), "ANDHRA PRADESH")

    def test_genuine_coimbatore_district_tamil(self):
        query = "கோயம்புத்தூர் மாவட்டத்தில் ஆய்வு செய்யப்பட்ட மண் மாதிரிகள் எத்தனை?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("district_name"), "Coimbatore")
        self.assertEqual(grounded.get("state_name"), "TAMIL NADU")

    def test_genuine_darjeeling_district_bengali(self):
        query = "দার্জিলিং জেলায় বিদ্যুৎ सुविधा থাকা স্কুলের সংখ্যা কত?"
        grounded = dynamic_entity_grounder.ground_entities(query)
        self.assertEqual(grounded.get("district_name"), "Darjeeling")
        self.assertEqual(grounded.get("state_name"), "WEST BENGAL")


class TestSQLExecutionRegression(unittest.TestCase):
    """
    Executes actual SQL queries on DuckDB Parquet stores to verify
    exact execution results and ensure no row discrepancies.
    """

    def setUp(self):
        self.sandbox = DuckDBSandbox()

    def test_up_pm_kisan_sql_execution(self):
        # Ground truth PM-Kisan total for Uttar Pradesh
        sql = "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'UTTAR PRADESH';"
        res = self.sandbox.execute_query(sql)
        self.assertIsNotNone(res)
        rows = res.get("rows") if isinstance(res, dict) else res.rows
        self.assertEqual(rows[0][0], 14_623_899)

    def test_maharashtra_pm_kisan_sql_execution(self):
        # Ground truth PM-Kisan total for Maharashtra
        sql = "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'MAHARASHTRA';"
        res = self.sandbox.execute_query(sql)
        self.assertIsNotNone(res)
        rows = res.get("rows") if isinstance(res, dict) else res.rows
        self.assertEqual(rows[0][0], 15_981_882)

    def test_tamil_nadu_pm_kisan_sql_execution(self):
        # Ground truth PM-Kisan total for Tamil Nadu
        sql = "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'TAMIL NADU';"
        res = self.sandbox.execute_query(sql)
        self.assertIsNotNone(res)
        rows = res.get("rows") if isinstance(res, dict) else res.rows
        self.assertEqual(rows[0][0], 12_542_755)

    def test_west_bengal_pm_kisan_sql_execution(self):
        # Ground truth PM-Kisan total for West Bengal
        sql = "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'WEST BENGAL';"
        res = self.sandbox.execute_query(sql)
        self.assertIsNotNone(res)
        rows = res.get("rows") if isinstance(res, dict) else res.rows
        self.assertEqual(rows[0][0], 12_912_117)

    def test_andhra_pradesh_pm_kisan_sql_execution(self):
        # Ground truth PM-Kisan total for Andhra Pradesh
        sql = "SELECT SUM(farmer_beneficiaries) AS total_farmers FROM ndap_pm_kisan_disbursement WHERE state_name = 'ANDHRA PRADESH';"
        res = self.sandbox.execute_query(sql)
        self.assertIsNotNone(res)
        rows = res.get("rows") if isinstance(res, dict) else res.rows
        self.assertEqual(rows[0][0], 10_256_870)


if __name__ == "__main__":
    unittest.main()

