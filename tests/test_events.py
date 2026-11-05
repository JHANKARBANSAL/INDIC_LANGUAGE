"""
Unit tests for EventBus and event schemas.
"""

import unittest

from indicsql.events.bus import EventBus
from indicsql.events.schemas import (
    ExecutionCompletedEvent,
    QueryInitiatedEvent,
    ReflectionTriggeredEvent,
    SchemaLinkedEvent,
    SQLSynthesizedEvent,
    VoiceSynthesisEvent,
)


class TestEventSchemas(unittest.TestCase):
    """Validate that event dataclasses construct correctly and serialize."""

    def test_base_event_defaults(self):
        evt = QueryInitiatedEvent(query_id="q1", raw_query="test", detected_lang="hi", detected_script="Devanagari")
        self.assertIsNotNone(evt.event_id)
        self.assertIsNotNone(evt.timestamp)
        self.assertEqual(evt.query_id, "q1")

    def test_schema_linked_event(self):
        evt = SchemaLinkedEvent(query_id="q2", target_table="ndap_mgnrega", matched_columns=["mandays"], confidence=0.9)
        d = evt.to_dict()
        self.assertIn("target_table", d)
        self.assertEqual(d["confidence"], 0.9)

    def test_sql_synthesized_event(self):
        evt = SQLSynthesizedEvent(
            query_id="q3",
            candidate_sql="SELECT 1;",
            method="tot_heuristic",
            utility_score=0.85,
            candidates_evaluated=3,
        )
        self.assertEqual(evt.method, "tot_heuristic")
        self.assertEqual(evt.candidates_evaluated, 3)

    def test_execution_completed_event(self):
        evt = ExecutionCompletedEvent(query_id="q4", exit_code=0, row_count=5, execution_time_ms=12.3, success=True)
        self.assertTrue(evt.success)

    def test_reflection_triggered_event(self):
        evt = ReflectionTriggeredEvent(query_id="q5", error_message="table not found", attempt_number=2)
        self.assertEqual(evt.attempt_number, 2)

    def test_voice_synthesis_event(self):
        evt = VoiceSynthesisEvent(query_id="q6", verbalized_text="Hello", char_count=5)
        self.assertEqual(evt.char_count, 5)


class TestEventBus(unittest.TestCase):
    """Validate EventBus publish/subscribe, history, and isolation."""

    def setUp(self):
        EventBus.reset()

    def test_subscribe_and_publish_sync(self):
        received = []
        EventBus.subscribe(QueryInitiatedEvent, lambda e: received.append(e))
        evt = QueryInitiatedEvent(query_id="q1")
        EventBus.publish(evt)
        self.assertEqual(len(received), 1)
        self.assertIs(received[0], evt)

    def test_no_crossfire_between_event_types(self):
        received_a, received_b = [], []
        EventBus.subscribe(QueryInitiatedEvent, lambda e: received_a.append(e))
        EventBus.subscribe(SQLSynthesizedEvent, lambda e: received_b.append(e))
        EventBus.publish(QueryInitiatedEvent(query_id="q1"))
        self.assertEqual(len(received_a), 1)
        self.assertEqual(len(received_b), 0)

    def test_get_history_all(self):
        EventBus.publish(QueryInitiatedEvent(query_id="q1"))
        EventBus.publish(SQLSynthesizedEvent(query_id="q2"))
        history = EventBus.get_history()
        self.assertEqual(len(history), 2)

    def test_get_history_filtered_by_query_id(self):
        EventBus.publish(QueryInitiatedEvent(query_id="qA"))
        EventBus.publish(SQLSynthesizedEvent(query_id="qA"))
        EventBus.publish(ExecutionCompletedEvent(query_id="qB"))
        history = EventBus.get_history(query_id="qA")
        self.assertEqual(len(history), 2)

    def test_handler_exception_does_not_crash_pipeline(self):
        def bad_handler(e):
            raise RuntimeError("intentional failure")

        EventBus.subscribe(QueryInitiatedEvent, bad_handler)
        # Should not raise
        EventBus.publish(QueryInitiatedEvent(query_id="q1"))

    def test_unsubscribe(self):
        received = []

        def handler(e):
            received.append(e)

        EventBus.subscribe(QueryInitiatedEvent, handler)
        EventBus.unsubscribe(QueryInitiatedEvent, handler)
        EventBus.publish(QueryInitiatedEvent(query_id="q1"))
        self.assertEqual(len(received), 0)

    def test_clear_history(self):
        EventBus.publish(QueryInitiatedEvent(query_id="q1"))
        EventBus.clear_history()
        self.assertEqual(len(EventBus.get_history()), 0)

    def test_reset_clears_subscribers_and_history(self):
        received = []
        EventBus.subscribe(QueryInitiatedEvent, lambda e: received.append(e))
        EventBus.publish(QueryInitiatedEvent(query_id="q1"))
        EventBus.reset()
        EventBus.publish(QueryInitiatedEvent(query_id="q2"))
        # After reset, subscriber was cleared — nothing received for q2
        self.assertEqual(len(received), 1)
        self.assertEqual(len(EventBus.get_history()), 1)


class TestToTSynthesizerEvents(unittest.TestCase):
    """Validate that the ToT synthesizer emits SQLSynthesizedEvent via pipeline."""

    def setUp(self):
        EventBus.reset()

    def test_synthesizer_emits_event(self):
        from indicsql.agents.sql_synthesizer import sql_synthesizer_node

        emitted = []
        EventBus.subscribe(SQLSynthesizedEvent, lambda e: emitted.append(e))

        state = {
            "query_id": "q-tot-1",
            "raw_query": "How many farmers in Maharashtra?",
            "target_database": "ndap_pm_kisan_disbursement",
            "reflection_attempts": 0,
            "audit_trace": [],
        }
        result = sql_synthesizer_node(state)

        self.assertEqual(len(emitted), 1)
        evt = emitted[0]
        self.assertEqual(evt.query_id, "q-tot-1")
        self.assertEqual(evt.method, "tot_heuristic")
        self.assertGreater(evt.utility_score, 0)
        self.assertGreater(evt.candidates_evaluated, 0)
        self.assertIn("generated_sql", result)
        self.assertIn("audit_trace", result)
        # The audit entry should contain tot_select metadata
        last_audit = result["audit_trace"][-1]
        self.assertEqual(last_audit["action"], "tot_select")
        self.assertIn("utility_score", last_audit)

    def test_full_pipeline_event_chain(self):
        """Smoke-test: running execute_indicsql_pipeline emits >= 4 events."""
        from indicsql.graph.workflow import execute_indicsql_pipeline

        collected = []
        for et in [QueryInitiatedEvent, SchemaLinkedEvent, SQLSynthesizedEvent, VoiceSynthesisEvent]:
            EventBus.subscribe(et, lambda e: collected.append(e))

        execute_indicsql_pipeline("How many farmers received PM-KISAN benefits in Bihar?")
        self.assertGreaterEqual(len(collected), 4)


if __name__ == "__main__":
    unittest.main()
