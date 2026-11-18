import json
import unittest
from pathlib import Path

from scripts.build_development_partition import build_partition

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestBenchmarkPartitions(unittest.TestCase):
    def test_development_candidate_has_no_exact_frozen_question_or_sql(self):
        frozen = json.loads(
            (REPO_ROOT / "data/benchmarks/indicdb_eval_suite_pan_india_280.json").read_text()
        )
        development = json.loads(
            (REPO_ROOT / "data/benchmarks/indicdb_development_candidate.json").read_text()
        )

        self.assertEqual(
            development,
            build_partition(
                json.loads(
                    (REPO_ROOT / "data/benchmarks/indicdb_eval_suite_expanded.json").read_text()
                ),
                frozen,
            ),
        )
        self.assertEqual(
            {item["language"] for item in development},
            {"en", "hi-en", "hi", "mr", "bn", "ta", "te"},
        )
        frozen_questions = {item["query"].casefold().strip() for item in frozen}
        frozen_sql = {item["gold_sql"].casefold().strip() for item in frozen}
        self.assertFalse(
            frozen_questions & {item["query"].casefold().strip() for item in development}
        )
        self.assertFalse(
            frozen_sql & {item["gold_sql"].casefold().strip() for item in development}
        )
