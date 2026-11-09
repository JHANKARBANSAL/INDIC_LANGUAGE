"""
tests/test_verbalization.py
Comprehensive Multilingual Verbalization Tests for all 7 Supported Languages:
- Hindi (hi)
- Marathi (mr)
- Tamil (ta)
- Telugu (te)
- Bengali (bn)
- Hinglish (hi-en)
- English (en)

Covers:
1. Language-specific Indian number formatting (Crores / Lakhs) across regional scripts
2. Native-language purity & script isolation (verifying no cross-script leakage)
3. Mathematical precision matching between raw DuckDB results and verbalized prose
"""

import re
import unittest
from indicsql.agents.response_verbalizer import (
    format_indian_currency_number,
    verbalize_tabular_result,
    response_verbalizer_node,
)
from indicsql.core.state import IndicSQLState


class TestMultilingualNumberFormatting(unittest.TestCase):
    """Tests localized Indian number formatting across all 7 supported languages."""

    def test_crores_formatting_all_languages(self):
        val = 14_623_899  # 1.46 Crores

        # Hindi
        hi_fmt = format_indian_currency_number(val, lang="hi")
        self.assertIn("1.46", hi_fmt)
        self.assertIn("कोटी", hi_fmt)

        # Marathi
        mr_fmt = format_indian_currency_number(val, lang="mr")
        self.assertIn("1.46", mr_fmt)
        self.assertIn("कोटी", mr_fmt)

        # Tamil
        ta_fmt = format_indian_currency_number(val, lang="ta")
        self.assertIn("1.46", ta_fmt)
        self.assertIn("கோடி", ta_fmt)

        # Telugu
        te_fmt = format_indian_currency_number(val, lang="te")
        self.assertIn("1.46", te_fmt)
        self.assertIn("కోట్లు", te_fmt)

        # Bengali
        bn_fmt = format_indian_currency_number(val, lang="bn")
        self.assertIn("1.46", bn_fmt)
        self.assertIn("কোটি", bn_fmt)

        # English
        en_fmt = format_indian_currency_number(val, lang="en")
        self.assertIn("1.46", en_fmt)
        self.assertIn("Crores", en_fmt)
        self.assertNotIn("कोटी", en_fmt)

        # Hinglish
        hien_fmt = format_indian_currency_number(val, lang="hi-en")
        self.assertIn("1.46", hien_fmt)
        self.assertIn("Crores", hien_fmt)

    def test_lakhs_formatting_all_languages(self):
        val = 450_000  # 4.50 Lakhs

        self.assertIn("4.50", format_indian_currency_number(val, lang="hi"))
        self.assertIn("लाख", format_indian_currency_number(val, lang="hi"))

        self.assertIn("4.50", format_indian_currency_number(val, lang="mr"))
        self.assertIn("लाख", format_indian_currency_number(val, lang="mr"))

        self.assertIn("4.50", format_indian_currency_number(val, lang="ta"))
        self.assertIn("இலட்சம்", format_indian_currency_number(val, lang="ta"))

        self.assertIn("4.50", format_indian_currency_number(val, lang="te"))
        self.assertIn("లక్షలు", format_indian_currency_number(val, lang="te"))

        self.assertIn("4.50", format_indian_currency_number(val, lang="bn"))
        self.assertIn("লাখ", format_indian_currency_number(val, lang="bn"))

        self.assertIn("4.50", format_indian_currency_number(val, lang="en"))
        self.assertIn("Lakhs", format_indian_currency_number(val, lang="en"))

        self.assertIn("4.50", format_indian_currency_number(val, lang="hi-en"))
        self.assertIn("Lakhs", format_indian_currency_number(val, lang="hi-en"))

    def test_thousands_and_edge_cases(self):
        self.assertEqual(format_indian_currency_number(1_250, lang="en"), "1,250")
        self.assertEqual(format_indian_currency_number(0, lang="hi"), "0")
        self.assertEqual(format_indian_currency_number(None, lang="ta"), "0")
        self.assertEqual(format_indian_currency_number("not_a_num", lang="te"), "not_a_num")


class TestMultilingualPurityAndNaturalOutput(unittest.TestCase):
    """
    Validates natural output and script purity for all 7 languages.
    Ensures non-English responses use authentic regional scripts and terms without cross-script corruption.
    """

    def test_hindi_verbalization(self):
        state: IndicSQLState = {
            "query_id": "test-hi",
            "detected_lang": "hi",
            "execution_result": {"columns": ["total_farmers"], "rows": [[14_623_899]]},
        }
        res = verbalize_tabular_result(state)
        self.assertIn("पीएम-किसान योजना के तहत कुल", res)
        self.assertIn("1.46 कोटी", res)
        self.assertIn("किसानों को लाभ प्राप्त हुआ", res)
        # Verify no Tamil or Telugu script
        self.assertFalse(any(0x0B80 <= ord(c) <= 0x0BFF for c in res))
        self.assertFalse(any(0x0C00 <= ord(c) <= 0x0C7F for c in res))

    def test_marathi_verbalization(self):
        state: IndicSQLState = {
            "query_id": "test-mr",
            "detected_lang": "mr",
            "execution_result": {"columns": ["total_farmers"], "rows": [[15_981_882]]},
        }
        res = verbalize_tabular_result(state)
        self.assertIn("पीएम-किसान योजनेअंतर्गत एकूण", res)
        self.assertIn("1.60 कोटी", res)
        self.assertIn("शेतकऱ्यांना लाभ मिळाला", res)
        # Marathi specific terms
        self.assertNotIn("किसानों", res)

    def test_tamil_verbalization_purity(self):
        state: IndicSQLState = {
            "query_id": "test-ta",
            "detected_lang": "ta",
            "execution_result": {"columns": ["total_farmers"], "rows": [[12_542_755]]},
        }
        res = verbalize_tabular_result(state)
        self.assertIn("பிஎம்-கிசான் திட்டத்தின் கீழ் மொத்தம்", res)
        self.assertIn("1.25 கோடி", res)
        self.assertIn("விவசாயிகள் பயனடைந்துள்ளனர்", res)
        # Assert absolute Devanagari purity (NO Hindi/Marathi Devanagari characters)
        self.assertFalse(any(0x0900 <= ord(c) <= 0x097F for c in res))

    def test_telugu_verbalization_purity(self):
        state: IndicSQLState = {
            "query_id": "test-te",
            "detected_lang": "te",
            "execution_result": {"columns": ["total_farmers"], "rows": [[10_256_870]]},
        }
        res = verbalize_tabular_result(state)
        self.assertIn("పీఎం-కిసాన్ పథకం కింద మొత్తం", res)
        self.assertIn("1.03 కోట్లు", res)
        self.assertIn("రైతులకు లబ్ధి చేకూరింది", res)
        # Assert absolute Devanagari letter purity (excluding universal Indic danda U+0964)
        self.assertFalse(any(0x0900 <= ord(c) <= 0x0963 or 0x0966 <= ord(c) <= 0x097F for c in res))

    def test_bengali_verbalization_purity(self):
        state: IndicSQLState = {
            "query_id": "test-bn",
            "detected_lang": "bn",
            "execution_result": {"columns": ["total_farmers"], "rows": [[12_912_117]]},
        }
        res = verbalize_tabular_result(state)
        self.assertIn("পিএম-কিষান প্রকল্পের অধীনে মোট", res)
        self.assertIn("1.29 কোটি", res)
        self.assertIn("জন কৃষক উপকৃত হয়েছেন", res)
        # Assert absolute Devanagari letter purity (excluding universal Indic danda U+0964)
        self.assertFalse(any(0x0900 <= ord(c) <= 0x0963 or 0x0966 <= ord(c) <= 0x097F for c in res))

    def test_english_verbalization_purity(self):
        state: IndicSQLState = {
            "query_id": "test-en",
            "detected_lang": "en",
            "execution_result": {"columns": ["total_farmers"], "rows": [[15_981_882]]},
        }
        res = verbalize_tabular_result(state)
        self.assertIn("Under PM-KISAN, a total of 1.60 Crores farmers received direct benefit transfers.", res)
        # Assert NO Indic script characters (pure ASCII / English)
        self.assertFalse(any(ord(c) >= 0x0900 for c in res))

    def test_hinglish_verbalization_purity(self):
        state: IndicSQLState = {
            "query_id": "test-hien",
            "detected_lang": "hi-en",
            "execution_result": {"columns": ["total_farmers"], "rows": [[14_623_899]]},
        }
        res = verbalize_tabular_result(state)
        self.assertIn("PM-KISAN yojana ke tahat total 1.46 Crores farmers ko labh mila.", res)
        # Assert NO Devanagari characters
        self.assertFalse(any(ord(c) >= 0x0900 for c in res))


class TestMultilingualDomainVerbalization(unittest.TestCase):
    """Tests literacy, employment, and error handling across multiple languages."""

    def test_mgnrega_mandays_tamil_and_telugu(self):
        ta_state: IndicSQLState = {
            "query_id": "test-ta-mg",
            "detected_lang": "ta",
            "execution_result": {"columns": ["total_mandays_generated"], "rows": [[85_000_000]]},
        }
        ta_res = verbalize_tabular_result(ta_state)
        self.assertIn("மனித வேலை நாட்கள்", ta_res)
        self.assertIn("8.50 கோடி", ta_res)

        te_state: IndicSQLState = {
            "query_id": "test-te-mg",
            "detected_lang": "te",
            "execution_result": {"columns": ["total_mandays_generated"], "rows": [[92_000_000]]},
        }
        te_res = verbalize_tabular_result(te_state)
        self.assertIn("పనిదినాలు", te_res)
        self.assertIn("9.20 కోట్లు", te_res)

    def test_female_literacy_bengali_and_marathi(self):
        bn_state: IndicSQLState = {
            "query_id": "test-bn-lit",
            "detected_lang": "bn",
            "execution_result": {"columns": ["district_name", "female_literacy_rate"], "rows": [["Darjeeling", 78.4]]},
        }
        bn_res = verbalize_tabular_result(bn_state)
        self.assertIn("Darjeeling", bn_res)
        self.assertIn("মহিলা সাক্ষরতার হার 78.4%", bn_res)

        mr_state: IndicSQLState = {
            "query_id": "test-mr-lit",
            "detected_lang": "mr",
            "execution_result": {"columns": ["district_name", "female_literacy_rate"], "rows": [["Pune", 84.1]]},
        }
        mr_res = verbalize_tabular_result(mr_state)
        self.assertIn("Pune", mr_res)
        self.assertIn("महिला साक्षरता प्रमाण 84.1%", mr_res)

    def test_graceful_multilingual_error_messages(self):
        languages = ["hi", "mr", "ta", "te", "bn", "hi-en", "en"]
        for l in languages:
            state: IndicSQLState = {
                "query_id": f"test-err-{l}",
                "detected_lang": l,
                "execution_result": None,
                "execution_error": "Connection reset",
            }
            msg = verbalize_tabular_result(state)
            self.assertIsNotNone(msg)
            self.assertGreater(len(msg), 10)


class TestVerbalizedNumbersMatchExecution(unittest.TestCase):
    """Verifies strict numerical alignment between DuckDB query results and verbalized prose."""

    def test_verbalized_number_equals_sql_result_in_crores(self):
        raw_db_value = 14_623_899
        state: IndicSQLState = {
            "query_id": "test-num-match-1",
            "detected_lang": "hi",
            "execution_result": {"columns": ["farmer_beneficiaries"], "rows": [[raw_db_value]]},
            "execution_error": None,
        }
        verbalized = verbalize_tabular_result(state)
        expected_str = f"{raw_db_value / 10_000_000:.2f}"
        self.assertIn(expected_str, verbalized)

    def test_verbalized_number_equals_sql_result_in_lakhs(self):
        raw_db_value = 785_400
        state: IndicSQLState = {
            "query_id": "test-num-match-2",
            "detected_lang": "hi",
            "execution_result": {"columns": ["farmer_beneficiaries"], "rows": [[raw_db_value]]},
            "execution_error": None,
        }
        verbalized = verbalize_tabular_result(state)
        expected_str = f"{raw_db_value / 100_000:.2f}"
        self.assertIn(expected_str, verbalized)

    def test_response_verbalizer_node_audit_trace(self):
        state: IndicSQLState = {
            "query_id": "test-node-trace",
            "detected_lang": "ta",
            "execution_result": {"columns": ["farmer_beneficiaries"], "rows": [[12_542_755]]},
            "execution_error": None,
            "audit_trace": [],
        }
        output = response_verbalizer_node(state)
        self.assertIn("verbalized_response", output)
        self.assertIn("audit_trace", output)
        last_audit = output["audit_trace"][-1]
        self.assertEqual(last_audit["agent"], "ResponseVerbalizerAgent")
        self.assertEqual(last_audit["action"], "verbalize_indic_prose")
        self.assertGreater(last_audit["output_length"], 0)


if __name__ == "__main__":
    unittest.main()
