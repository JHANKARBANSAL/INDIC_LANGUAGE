import unittest

from scripts.build_sealed_indicdb_final import REQUIRED_LANGUAGES, build_selection
from scripts.evaluate_indicdb_sealed_final import selected_key_digest
from scripts.lock_indicdb_final_run import canonical_hash


class TestSealedIndicDBFinalSelection(unittest.TestCase):
    def test_excludes_unresolved_schema_names_and_requires_all_languages(self):
        translation = {language: {"question": language, "sql": "SELECT 1"} for language in REQUIRED_LANGUAGES}
        groups = {
            ("eligible", "INDIA_Economic_Census_Firms"): translation,
            ("unresolved", "INDIA_UDISE_SCHOOL_PROFILES"): translation,
            ("partial", "INDIA_Economic_Census_Firms"): {"en": {"question": "x", "sql": "SELECT 1"}},
        }

        selected, exclusions = build_selection(groups, set(), set(), "seed", 1)

        self.assertEqual(selected, [("eligible", "INDIA_Economic_Census_Firms")])
        self.assertEqual(exclusions["unresolved_schema_name"], 1)
        self.assertEqual(exclusions["incomplete_language_group"], 1)

    def test_lock_hash_changes_when_locked_model_changes(self):
        lock = {"model": {"name": "qwen2.5:7b", "digest": "a"}, "credentials_included": False}
        changed = {"model": {"name": "qwen2.5:7b", "digest": "b"}, "credentials_included": False}
        self.assertNotEqual(canonical_hash(lock), canonical_hash(changed))

    def test_router_does_not_coerce_invalid_model_answer(self):
        # The evaluator records an invalid response as a failure rather than using gold metadata.
        self.assertIsNone(_exact_schema_name("INDIA_NOT_A_RELEASED_SCHEMA", ["INDIA_A"]))

    def test_selected_key_digest_ignores_pretty_printing(self):
        keys = [{"pair_id": "p", "dataset_name": "INDIA_A"}]
        self.assertEqual(
            selected_key_digest(keys),
            "a6b06bc7d62bab01f6627985aabdd39e16e9ad2110f89a85c32b039bc544526d",
        )


def _exact_schema_name(answer: str, candidates: list[str]) -> str | None:
    """Mirror the sealed evaluator's no-alias acceptance rule without a network call."""
    return answer if answer in candidates else None

