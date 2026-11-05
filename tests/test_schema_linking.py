"""
Unit tests for Cross-Lingual Schema-Linking & Transliteration Normalization.
Validates linking across 7 Indic languages (Hindi, Marathi, Bengali, Tamil, Telugu, Hinglish, English)
and across multiple NDAP domains.
"""

import unittest

from indicsql.agents.schema_linker import link_schema_elements, schema_linker_node
from indicsql.schema.phonetic import normalize_indic_phonetics


class TestSchemaLinking(unittest.TestCase):
    def test_phonetic_normalization_latin(self):
        # Hinglish / Latin administrative terms
        normalized = normalize_indic_phonetics(
            "Maharashtra mein kisano ko kitna labh mila", target_lang="hi"
        )
        self.assertIn("farmer", normalized)

        # Marathi code-mixed
        normalized_mr = normalize_indic_phonetics("shatkari yojana", target_lang="mr")
        self.assertIn("farmer", normalized_mr)

    def test_cross_lingual_dravidian_linking(self):
        # Tamil linking for MGNREGA
        ta_elements = link_schema_elements(
            "தமிழ்நாட்டில் மகாத்மா காந்தி ஊரக வேலை உறுதித் திட்டத்தின் கீழ் மனித வேலை நாட்கள்", lang="ta"
        )
        self.assertTrue(len(ta_elements) > 0)
        self.assertEqual(ta_elements[0]["table_name"], "mgnrega_state_annual_employment")

        # Telugu linking for PM-KISAN
        te_elements = link_schema_elements(
            "ఆంధ్రప్రదేశ్ రాష్ట్రంలో పీఎం-కిసాన్ పథకం ద్వారా ఎంత మొత్తం నిధులు విడుదలయ్యాయి?", lang="te"
        )
        self.assertTrue(len(te_elements) > 0)
        self.assertEqual(te_elements[0]["table_name"], "ndap_pm_kisan_disbursement")

    def test_bengali_and_marathi_linking(self):
        # Bengali linking for Mid-day meal
        bn_elements = link_schema_elements(
            "মুর্শিদাবাদ জেলায় মিড-ডে মিলের মাধ্যমে কতজন শিক্ষার্থী উপকৃত হয়েছে?", lang="bn"
        )
        self.assertTrue(len(bn_elements) > 0)
        self.assertEqual(bn_elements[0]["table_name"], "ndap_midday_meal_scheme")

        # Marathi linking for school computer infrastructure
        mr_elements = link_schema_elements(
            "पुणे जिल्ह्यातील शाळांमध्ये संगणक प्रयोगशाळा किती आहेत?", lang="mr"
        )
        self.assertTrue(len(mr_elements) > 0)
        self.assertEqual(mr_elements[0]["table_name"], "ndap_school_infrastructure")

    def test_schema_linker_node_state_integration(self):
        state = {
            "raw_query": "उत्तर प्रदेश में यूरिया उर्वरक की कुल बिक्री कितनी रही?",
            "canonical_query": "उत्तर प्रदेश में यूरिया उर्वरक की कुल बिक्री कितनी रही?",
            "detected_lang": "hi",
            "audit_trace": [],
        }
        res = schema_linker_node(state)
        self.assertEqual(res["target_database"], "ndap_fertilizer_distribution")
        self.assertIn("step", res["audit_trace"][-1])


if __name__ == "__main__":
    unittest.main()
