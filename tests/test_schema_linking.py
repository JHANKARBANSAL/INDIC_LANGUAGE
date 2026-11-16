"""
Unit tests for Cross-Lingual Schema-Linking & Transliteration Normalization.
Validates linking across 7 Indic languages (Hindi, Marathi, Bengali, Tamil, Telugu, Hinglish, English)
and across multiple NDAP domains.
"""

import unittest

from indicsql.agents.schema_linker import link_schema_elements, schema_linker_node
from indicsql.schema.catalog import NDAPCatalog
from indicsql.schema.multilingual_index import NDAP_MULTILINGUAL_INDEX
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

    def test_all_catalog_synonyms_link_to_their_declared_columns(self):
        indexed_tables = {
            entry["table"] for entry in NDAP_MULTILINGUAL_INDEX.values()
        }
        self.assertEqual(set(NDAPCatalog.list_tables()), indexed_tables)

        for concept, entry in NDAP_MULTILINGUAL_INDEX.items():
            expected = (entry["table"], entry["column"])
            for synonym in entry["synonyms"]:
                with self.subTest(concept=concept, synonym=synonym):
                    matches = link_schema_elements(synonym)
                    self.assertIn(
                        expected,
                        {
                            (match["table_name"], match["column_name"])
                            for match in matches
                        },
                    )

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

    def test_unknown_schema_does_not_fall_back_to_pm_kisan(self):
        state = {
            "raw_query": "What is the population of Atlantis?",
            "canonical_query": "What is the population of Atlantis?",
            "detected_lang": "en",
            "audit_trace": [],
        }

        self.assertEqual(link_schema_elements(state["raw_query"]), [])
        result = schema_linker_node(state)

        self.assertEqual(result["target_database"], "")
        self.assertIn("No supported database schema", result["schema_linking_error"])

    def test_farmer_literacy_query_fails_closed_without_changing_farmer_counts(self):
        unsupported = "How many farmers in Bihar are literate?"
        result = schema_linker_node(
            {
                "raw_query": unsupported,
                "canonical_query": unsupported,
                "detected_lang": "en",
                "audit_trace": [],
            }
        )

        self.assertEqual(result["target_database"], "")
        self.assertIn("does not record literacy status", result["schema_linking_error"])
        self.assertEqual(
            result["suggested_queries"],
            [
                "How many PM-KISAN farmer beneficiaries were there in Bihar?",
                "What was the female literacy rate in Bihar?",
                "What was the male literacy rate in Bihar?",
            ],
        )
        expected_targets = [
            ("ndap_pm_kisan_disbursement", "farmer_beneficiaries"),
            ("ndap_education_stats", "female_literacy_rate"),
            ("ndap_education_stats", "male_literacy_rate"),
        ]
        for suggestion, expected in zip(
            result["suggested_queries"], expected_targets, strict=True
        ):
            matches = link_schema_elements(suggestion)
            self.assertIn(
                expected,
                {(match["table_name"], match["column_name"]) for match in matches},
            )

        supported = "How many farmers in Bihar?"
        result = schema_linker_node(
            {
                "raw_query": supported,
                "canonical_query": supported,
                "detected_lang": "en",
                "audit_trace": [],
            }
        )

        self.assertEqual(result["target_database"], "ndap_pm_kisan_disbursement")
        self.assertIsNone(result["schema_linking_error"])

    def test_separate_farmer_and_literacy_columns_do_not_imply_joint_measure(self):
        state = {
            "raw_query": "How many farmers in Bihar are literate?",
            "canonical_query": "How many farmers in Bihar are literate?",
            "detected_lang": "en",
            "database_schema_name": "custom",
            "database_schema": {
                "tables": {
                    "farmer_stats": {
                        "columns": {
                            "farmer_count": "bigint",
                            "literacy_rate": "float",
                        },
                        "foreign_keys": [],
                    }
                }
            },
            "audit_trace": [],
        }

        result = schema_linker_node(state)

        self.assertEqual(result["target_database"], "")
        self.assertIn("does not record literacy status", result["schema_linking_error"])

    def test_joint_literate_farmer_count_in_provided_schema_is_supported(self):
        state = {
            "raw_query": "How many farmers in Bihar are literate?",
            "canonical_query": "How many farmers in Bihar are literate?",
            "detected_lang": "en",
            "database_schema_name": "custom",
            "database_schema": {
                "tables": {
                    "farmer_stats": {
                        "columns": {"literate_farmer_count": "bigint"},
                        "foreign_keys": [],
                    }
                }
            },
            "audit_trace": [],
        }

        result = schema_linker_node(state)

        self.assertEqual(result["target_database"], "custom")
        self.assertIsNone(result["schema_linking_error"])

    def test_explicit_database_schema_context_bypasses_ndap_catalog(self):
        state = {
            "raw_query": "List districts in Andhra Pradesh",
            "canonical_query": "List districts in Andhra Pradesh",
            "detected_lang": "en",
            "database_schema_name": "INDIA_Economic_Census_Firms",
            "database_schema": {
                "tables": {
                    "dim_district": {
                        "columns": {"district_name": "text"},
                        "foreign_keys": [],
                    }
                }
            },
            "audit_trace": [],
        }

        result = schema_linker_node(state)

        self.assertEqual(result["target_database"], "INDIA_Economic_Census_Firms")
        self.assertEqual(result["pruned_schema"][0]["table_name"], "dim_district")
        self.assertIsNone(result["schema_linking_error"])

    def test_relevant_indicdb_schema_is_pruned_for_all_supported_languages(self):
        questions = {
            "en": "List district names in the state",
            "hi": "राज्य के सभी जिलों के नाम सूचीबद्ध करें",
            "hi-en": "State ke saare districts ke naam dikhao",
            "mr": "राज्यातील सर्व जिल्ह्यांची नावे यादी करा",
            "ta": "மாநிலத்தில் உள்ள அனைத்து மாவட்டங்களின் பெயர்களை பட்டியலிடுக",
            "te": "రాష్ట్రంలోని అన్ని జిల్లాల పేర్లను జాబితా చేయండి",
            "bn": "রাজ্যের সব জেলাগুলোর নাম তালিকাভুক্ত করুন",
        }
        schema = {
            "tables": {
                "dim_district": {
                    "columns": {"district_name": "text", "state_id": "bigint"},
                    "foreign_keys": ["state_id references dim_state.state_id"],
                },
                "dim_state": {
                    "columns": {"state_id": "bigint", "state_name": "text"},
                    "foreign_keys": [],
                },
                "fact_establishments": {
                    "columns": {"total_establishments": "bigint"},
                    "foreign_keys": [],
                },
            }
        }

        for language, question in questions.items():
            with self.subTest(language=language):
                result = schema_linker_node(
                    {
                        "raw_query": question,
                        "canonical_query": question,
                        "detected_lang": language,
                        "database_schema_name": "INDIA_Economic_Census_Firms",
                        "database_schema": schema,
                        "audit_trace": [],
                    }
                )
                self.assertEqual(
                    {item["table_name"] for item in result["pruned_schema"]},
                    {"dim_district", "dim_state"},
                )

    def test_relevant_schema_keeps_lexically_matched_fact_and_fk_dimensions(self):
        question = (
            "List rural sub-districts with allopathic outpatient attendance "
            "during 2022."
        )
        schema = {
            "tables": {
                "dim_geography": {
                    "columns": {
                        "geography_id": "bigint",
                        "sub_district": "text",
                        "type_of_area": "text",
                    },
                    "foreign_keys": [],
                },
                "dim_time": {
                    "columns": {"time_id": "bigint", "year": "integer"},
                    "foreign_keys": [],
                },
                "fact_outpatient_services": {
                    "columns": {
                        "geography_id": "bigint",
                        "time_id": "bigint",
                        "outpatient_attendance_allopathic": "bigint",
                    },
                    "foreign_keys": [
                        "geography_id references dim_geography.geography_id",
                        "time_id references dim_time.time_id",
                    ],
                },
                "fact_child_immunization_routine": {
                    "columns": {"bcg_vaccine": "bigint"},
                    "foreign_keys": [],
                },
            }
        }

        result = schema_linker_node(
            {
                "raw_query": question,
                "canonical_query": question,
                "detected_lang": "en",
                "database_schema_name": "INDIA_HMIS_Sub_District_Report_Facility_wise",
                "database_schema": schema,
                "audit_trace": [],
            }
        )

        self.assertEqual(
            {item["table_name"] for item in result["pruned_schema"]},
            {"dim_geography", "dim_time", "fact_outpatient_services"},
        )


if __name__ == "__main__":
    unittest.main()
