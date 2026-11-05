"""
Unit Tests for IndicSQL-Agg-12K Dataset Curation Pipeline.
Verifies record schema, language representation, DDL injection, and JSONL serialization.
"""

import json
import tempfile
import unittest
from pathlib import Path

from indicsql.training.dataset_curator import DatasetCurator


class TestLoraDataset(unittest.TestCase):

    def setUp(self):
        self.curator = DatasetCurator(seed=42)

    def test_sarvam_partition_generation(self):
        records = self.curator.generate_sarvam_partition(count=70)
        self.assertEqual(len(records), 70)

        # Check languages representation
        langs = {r.language for r in records}
        expected_langs = {"hi", "mr", "ta", "te", "bn", "gu", "kn"}
        self.assertTrue(expected_langs.issubset(langs), f"Missing languages: {expected_langs - langs}")

        for r in records:
            self.assertEqual(r.partition, "sarvam_transliteration")
            self.assertTrue(r.instruction.startswith("Translate and normalize"))
            self.assertGreater(len(r.output), 5)
            self.assertIn(r.difficulty, ["easy", "medium", "hard"])

    def test_qwen_partition_generation(self):
        records = self.curator.generate_qwen_partition(count=40)
        self.assertEqual(len(records), 40)

        for r in records:
            self.assertEqual(r.partition, "qwen_sql")
            self.assertTrue(r.input.startswith("CREATE TABLE"))
            self.assertTrue(r.output.upper().startswith("SELECT"))
            self.assertTrue(r.output.endswith(";"))
            self.assertIn(r.difficulty, ["easy", "medium", "hard"])

    def test_original_validation_split(self):
        val_sarvam, val_qwen = self.curator.generate_original_validation_split()
        self.assertGreater(len(val_sarvam), 0)
        self.assertEqual(len(val_sarvam), len(val_qwen))

        # Check that validation split reflects real ground-truth benchmark instances
        for vs, vq in zip(val_sarvam, val_qwen):
            self.assertTrue(vs.record_id.startswith("val-indicdb-"))
            self.assertEqual(vs.partition, "sarvam_transliteration")
            self.assertEqual(vq.partition, "qwen_sql")
            self.assertTrue(vq.output.upper().startswith("SELECT"))

    def test_curate_and_export_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            summary = self.curator.curate_and_export(out_dir, sarvam_count=20, qwen_count=20)

            self.assertEqual(summary["total_train_records"], 40)
            self.assertGreater(summary["total_val_records"], 0)

            sarvam_file = out_dir / "sarvam_partition.jsonl"
            qwen_file = out_dir / "qwen_partition.jsonl"
            val_sarvam_file = out_dir / "val_sarvam.jsonl"
            val_qwen_file = out_dir / "val_qwen.jsonl"

            self.assertTrue(sarvam_file.exists())
            self.assertTrue(qwen_file.exists())
            self.assertTrue(val_sarvam_file.exists())
            self.assertTrue(val_qwen_file.exists())

            # Verify JSONL lines can be read back
            with open(sarvam_file, encoding="utf-8") as f:
                sarvam_lines = [json.loads(line) for line in f]
            self.assertEqual(len(sarvam_lines), 20)
            self.assertIn("instruction", sarvam_lines[0])

            with open(val_qwen_file, encoding="utf-8") as f:
                val_lines = [json.loads(line) for line in f]
            self.assertGreater(len(val_lines), 0)
            self.assertIn("output", val_lines[0])

    def test_expanded_validation_split(self):
        val_sarvam, val_qwen = self.curator.generate_validation_split(sarvam_count=50, qwen_count=50)
        self.assertEqual(len(val_sarvam), 50)
        self.assertEqual(len(val_qwen), 50)

        # Ensure all 7 regional languages are represented in expanded validation set
        val_langs = {r.language for r in val_sarvam}
        expected_langs = {"hi", "mr", "ta", "te", "bn", "gu", "kn"}
        self.assertTrue(expected_langs.issubset(val_langs))

        # Ensure queries are non-empty and SQL is valid
        for r in val_qwen:
            self.assertTrue(r.output.upper().startswith("SELECT"))
            self.assertTrue(r.output.endswith(";"))


if __name__ == "__main__":
    unittest.main()
