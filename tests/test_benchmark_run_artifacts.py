import unittest

from indicsql.benchmark.evaluator import are_tabular_results_equivalent
from scripts.evaluate_unseen_140 import (
    _expected_entities_from_gold,
    _failure_category_counts,
    _wilson_interval,
    verify_verbalization_quality,
)


class TestBenchmarkRunArtifacts(unittest.TestCase):
    def test_gold_sql_entity_filters_cover_multiple_entity_types(self):
        entities = _expected_entities_from_gold(
            "SELECT SUM(production_tonnes) FROM ndap_crop_production_census "
            "WHERE state_name = 'WEST BENGAL' AND district_name = 'Kolkata' "
            "AND crop_name = 'RICE';"
        )

        self.assertEqual(
            entities,
            {
                "state_name": "WEST BENGAL",
                "district_name": "Kolkata",
                "commodity": "RICE",
            },
        )

    def test_empty_prediction_does_not_match_nonempty_gold_result(self):
        self.assertFalse(
            are_tabular_results_equivalent(
                {"rows": [], "row_count": 0},
                {"rows": [[0]], "row_count": 1},
            )
        )

    def test_equal_empty_results_are_still_execution_equivalent(self):
        self.assertTrue(
            are_tabular_results_equivalent(
                {"rows": [], "row_count": 0},
                {"rows": [], "row_count": 0},
            )
        )

    def test_wilson_interval_is_bounded_for_small_samples(self):
        low, high = _wilson_interval(20, 20)

        self.assertGreaterEqual(low, 0)
        self.assertLess(low, 1)
        self.assertLessEqual(high, 1)
        self.assertLess(low, high)

    def test_english_script_check_allows_rupee_currency_symbol(self):
        passed, reason = verify_verbalization_quality(
            "The average price was ₹500.",
            "en",
            {"rows": [[500]]},
        )

        self.assertTrue(passed)
        self.assertEqual("PASSED", reason)

    def test_english_script_check_still_rejects_indic_letters(self):
        passed, reason = verify_verbalization_quality(
            "The total was 500 रुपये.",
            "en",
            {"rows": [[500]]},
        )

        self.assertFalse(passed)
        self.assertEqual("SCRIPT_POLLUTION_INDIC_IN_EN", reason)

    def test_failure_categories_include_verbalization_only_failures(self):
        counts = _failure_category_counts(
            [
                {
                    "execution_match": True,
                    "failure_categories": ["VERBALIZATION_SCRIPT_POLLUTION"],
                },
                {
                    "execution_match": False,
                    "failure_categories": ["RESULT_MISMATCH"],
                },
            ]
        )

        self.assertEqual(
            {
                "VERBALIZATION_SCRIPT_POLLUTION": 1,
                "RESULT_MISMATCH": 1,
            },
            counts,
        )


if __name__ == "__main__":
    unittest.main()
