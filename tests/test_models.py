"""
Unit and Integration Tests for Model Adapters and Tri-Combo Benchmark Engine.
Verifies lazy loading, graceful fallback, combo comparison, and Arena execution.
"""

import unittest
from pathlib import Path

from indicsql.core.state import IndicSQLState
from indicsql.models.adapter import ModelAdapter, ModelUnavailableError, QwenAdapter, SarvamAdapter
from indicsql.models.combo import ComboResult, TriComboEngine


class TestModelsAndCombos(unittest.TestCase):

    def setUp(self):
        self.state: IndicSQLState = {
            "raw_query": "बिहार में कुल कितने किसान लाभार्थी हैं?",
            "language": "hi",
            "detected_script": "Devanagari",
            "target_table": "ndap_pm_kisan_disbursement",
            "query_id": "test-combo-001",
            "canonical_query": "Total farmer beneficiaries in Bihar",
            "selected_columns": ["farmer_beneficiaries", "amount_inr", "state_name"],
            "schema_confidence": 0.95,
            "join_path": [],
            "generated_sql": "",
            "syntax_valid": False,
            "execution_result": None,
            "row_count": 0,
            "execution_error": None,
            "execution_time_ms": 0.0,
            "reflection_attempts": 0,
            "error_category": None,
            "remediation_applied": None,
            "audit_trace": [],
            "final_response": "",
            "audio_input_bytes": None,
            "audio_output_bytes": None,
            "voice_gender": "female",
            "transcribed_text": None,
            "hands_free_mode": False,
            "audio_turn_count": 0,
            "voice_latency_ms": 0.0,
        }

    def test_model_adapter_unavailability_handling(self):
        non_existent_path = Path("/tmp/non_existent_lora_dir_12345")
        adapter = ModelAdapter("test/model", lora_path=non_existent_path)
        self.assertFalse(adapter.is_available)

        with self.assertRaises(ModelUnavailableError):
            adapter.generate("Hello")

    def test_sarvam_and_qwen_adapters_default_paths(self):
        sarvam = SarvamAdapter()
        qwen = QwenAdapter()
        self.assertTrue(
            "sarvam_transliteration" in str(sarvam.lora_path) or "sarvam_adapter" in str(sarvam.lora_path)
        )
        self.assertTrue(
            "qwen_3b_sql" in str(qwen.lora_path) or "qwen_adapter" in str(qwen.lora_path)
        )
        # If weights are present on disk, verify is_available is True
        if (sarvam.lora_path / "adapter_model.safetensors").exists():
            self.assertTrue(sarvam.is_available)
        if (qwen.lora_path / "adapter_model.safetensors").exists():
            self.assertTrue(qwen.is_available)

    def test_tri_combo_fallback_execution(self):
        engine = TriComboEngine()
        results = engine.run_all(self.state)

        self.assertEqual(len(results), 3)
        combos = [r.combo for r in results]
        self.assertEqual(combos, ["hybrid", "sarvam_pure", "qwen_pure"])

        for r in results:
            self.assertIsInstance(r, ComboResult)
            self.assertEqual(r.method, "tot_heuristic")
            self.assertTrue(r.generated_sql.upper().startswith("SELECT"))
            self.assertGreater(r.utility_score, 0.0)
            self.assertGreaterEqual(r.latency_ms, 0.0)

    def test_synthesizer_node_incorporates_method(self):
        from indicsql.agents.sql_synthesizer import sql_synthesizer_node

        res = sql_synthesizer_node(self.state)
        self.assertTrue(res["syntax_valid"])
        self.assertTrue(res["generated_sql"].upper().startswith("SELECT"))

        trace = res["audit_trace"]
        self.assertTrue(len(trace) > 0)
        self.assertEqual(trace[-1]["method"], "tot_heuristic")


if __name__ == "__main__":
    unittest.main()
