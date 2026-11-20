"""Deterministic regression tests for IndicSQL's execution-verified suggestions."""

import unittest

from indicsql.agents.verified_recommender import verified_alternative_queries


class FakeSandbox:
    """No live DB is needed to verify control flow and SQL construction."""

    def __init__(self, *, reject_all=False, empty_all=False):
        self.statements = []
        self.reject_all = reject_all
        self.empty_all = empty_all

    def execute_query(self, sql):
        self.statements.append(sql)
        assert sql.startswith("SELECT ")
        assert " WHERE " in sql and " IS NOT NULL" in sql
        assert " LIMIT " in sql
        if self.reject_all:
            raise RuntimeError("Catalog Error: table does not exist")
        if self.empty_all:
            return {"columns": [], "rows": [], "row_count": 0}
        return {"columns": ["district_name", "farmer_beneficiaries"],
                "rows": [["TEST", 3]], "row_count": 1}


class VerifiedAlternativeTests(unittest.TestCase):
    def test_recommend_only_after_actual_successful_probes(self):
        sandbox = FakeSandbox()
        found = verified_alternative_queries(
            "How many farmers in Bihar are literate?",
            sandbox=sandbox, language="en",
        )
        self.assertTrue(1 <= len(found) <= 5)
        self.assertGreaterEqual(len(sandbox.statements), 2 * len(found))
        self.assertTrue(all(item["sample_row_count"] > 0 for item in found))
        self.assertTrue(all(item["sql"].startswith("SELECT ") for item in found))
        self.assertTrue(all("LIMIT 25" in item["sql"] for item in found))

    def test_missing_physical_tables_never_produce_suggestions(self):
        sandbox = FakeSandbox(reject_all=True)
        found = verified_alternative_queries(
            "PM KISAN farmer payment beneficiaries",
            sandbox=sandbox, max_probes=5
        )
        self.assertEqual(found, [])
        self.assertLessEqual(len(sandbox.statements), 5)

    def test_empty_table_is_not_claimed_answerable(self):
        sandbox = FakeSandbox(empty_all=True)
        found = verified_alternative_queries(
            "How many farmers in Bihar are literate?",
            sandbox=sandbox
        )
        self.assertEqual(found, [])

    def test_irrelevant_questions_do_not_get_random_suggestions(self):
        sandbox = FakeSandbox()
        found = verified_alternative_queries(
            "What is the orbital velocity of Neptune?",
            sandbox=sandbox
        )
        self.assertEqual(found, [])
        self.assertEqual(sandbox.statements, [])

    def test_caps(self):
        sandbox = FakeSandbox()
        found = verified_alternative_queries(
            "PM KISAN farmers benefited",
            sandbox=sandbox, limit=3, max_probes=6
        )
        self.assertLessEqual(len(found), 3)
        self.assertLessEqual(len(sandbox.statements), 12)

    def test_bengali_labels(self):
        sandbox = FakeSandbox()
        found = verified_alternative_queries(
            "PM KISAN farmer beneficiaries",
            sandbox=sandbox, language="bn", limit=2,
        )
        self.assertTrue(found)
        self.assertIn("ডেটাসেটে", found[0]["query"])


if __name__ == "__main__":
    unittest.main()
