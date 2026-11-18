import unittest

from scripts.export_vocabulary_review_queue import build_review_rows


class TestVocabularyReviewQueue(unittest.TestCase):
    def test_exports_only_routing_or_entity_grounding_failures(self):
        report = {
            "query_results": [
                {
                    "query_id": "keep",
                    "language": "te",
                    "target_table": "example_table",
                    "target_columns": ["metric"],
                    "query": "Example",
                    "failure_categories": ["TABLE_ROUTING_FAILURE"],
                },
                {
                    "query_id": "skip",
                    "language": "en",
                    "target_table": "example_table",
                    "target_columns": ["metric"],
                    "query": "Example",
                    "failure_categories": ["RESULT_MISMATCH"],
                },
            ]
        }

        rows = build_review_rows(report)

        self.assertEqual([row["query_id"] for row in rows], ["keep"])
        self.assertEqual(rows[0]["review_status"], "pending")
