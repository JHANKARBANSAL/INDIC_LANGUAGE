import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pyarrow as pa
import pyarrow.parquet as pq

from indicsql.benchmark.indicdb import INDICDB_LANGUAGE_FILES
from indicsql.benchmark.indicdb_schema_router import (
    SchemaRoutingError,
    select_schema,
)
from scripts.evaluate_indicdb_sealed import (
    _key_payload_sha256,
    _load_selected_keys,
    _query_record,
    load_selected_queries,
)


class TestIndicDBSchemaRouter(unittest.TestCase):
    def test_selects_only_an_exact_candidate_and_uses_locked_sampling(self):
        response = Mock()
        response.json.return_value = {"response": '{"schema_name":"india_schema_a"}'}
        contexts = {
            "india_schema_a": {
                "description": "Agriculture",
                "tables": {
                    "fact_crop": {
                        "description": "Crop production",
                        "columns": {"crop_name": "text"},
                    }
                },
            },
            "india_schema_b": {"description": "Health", "tables": {}},
        }

        with patch(
            "indicsql.benchmark.indicdb_schema_router.httpx.post", return_value=response
        ) as post:
            selected = select_schema(
                "Which crops were produced?",
                contexts,
                model_name="qwen2.5:3b",
                ollama_url="http://127.0.0.1:11434",
            )

        self.assertEqual(selected, "india_schema_a")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["options"]["temperature"], 0.05)
        self.assertEqual(payload["options"]["seed"], 42)
        self.assertEqual(payload["format"], "json")

    def test_rejects_schema_not_in_candidates(self):
        response = Mock()
        response.json.return_value = {"response": '{"schema_name":"not_a_candidate"}'}
        with patch("indicsql.benchmark.indicdb_schema_router.httpx.post", return_value=response):
            with self.assertRaises(SchemaRoutingError):
                select_schema(
                    "Question",
                    {"india_schema_a": {"tables": {}}},
                    model_name="qwen2.5:3b",
                    ollama_url="http://127.0.0.1:11434",
                )


class TestIndicDBSealedEvaluator(unittest.TestCase):
    def test_reads_only_selected_keys_and_keeps_raw_text_out_of_report_record(self):
        key_payload = [{"pair_id": "selected", "dataset_name": "SCHEMA_A"}]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for language, filename in INDICDB_LANGUAGE_FILES.items():
                pq.write_table(
                    pa.Table.from_pylist(
                        [
                            {
                                "pair_id": "selected",
                                "dataset_name": "SCHEMA_A",
                                "question": f"selected {language}",
                                "sql": "SELECT 1",
                            },
                            {
                                "pair_id": "not-selected",
                                "dataset_name": "SCHEMA_A",
                                "question": f"unselected {language}",
                                "sql": "SELECT 2",
                            },
                        ]
                    ),
                    root / filename,
                )

            keys_path = root / "keys.json"
            keys_path.write_text(json.dumps(key_payload), encoding="utf-8")
            keys = _load_selected_keys(
                keys_path,
                _key_payload_sha256(key_payload),
                expected_count=1,
            )
            groups = load_selected_queries(root, keys)

        self.assertEqual(set(groups), {("selected", "SCHEMA_A")})
        self.assertEqual(
            set(groups[("selected", "SCHEMA_A")]),
            set(INDICDB_LANGUAGE_FILES),
        )
        query = groups[("selected", "SCHEMA_A")]["en"]
        record = _query_record(
            query=query,
            expected_schema="india_schema_a",
            selected_schema="india_schema_a",
            generated_sql="SELECT 1",
            sql_valid=True,
            prediction_error=None,
            prediction_result={"rows": [[1]], "row_count": 1},
            gold_error=None,
            gold_result={"rows": [[1]], "row_count": 1},
            latency_ms=1.0,
        )
        self.assertNotIn("question", record)
        self.assertNotIn("gold_sql", record)
        self.assertEqual(record["execution_match"], True)


if __name__ == "__main__":
    unittest.main()
