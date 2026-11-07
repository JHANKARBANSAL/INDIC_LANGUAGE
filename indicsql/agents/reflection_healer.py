"""
Reflective Self-Correction Node.
Parses runtime execution errors, formulates targeted diagnostic feedback,
and passes remediation guidance to the SQL Synthesizer for neural healing.
"""

from typing import Any, Dict

from indicsql.core.state import IndicSQLState
from indicsql.events.bus import EventBus
from indicsql.events.schemas import ReflectionTriggeredEvent


def reflection_healer_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Diagnoses DuckDB execution error and constructs actionable feedback
    for the SQL Synthesizer to self-heal the query.
    Emits ReflectionTriggeredEvent on the EventBus.
    """
    attempts = state.get("reflection_attempts", 0) + 1
    current_sql = state.get("generated_sql", "")
    err = state.get("execution_error", "") or ""

    EventBus.publish(
        ReflectionTriggeredEvent(
            query_id=state.get("query_id"),
            error_message=err,
            attempt_number=attempts,
        )
    )

    feedback = f"Query execution failed: {err}."
    if "does not exist" in err.lower():
        feedback += " Please ensure all referenced table and column names exist in the schema DDL."
    elif "syntax error" in err.lower():
        feedback += " Please ensure standard DuckDB SQL syntax and remove any non-SQL tokens."

    audit_entry = {
        "step": 4.5,
        "agent": "ReflectionHealerNode",
        "action": "self_heal_sql",
        "attempt": attempts,
        "error_diagnosed": err,
        "feedback_generated": feedback,
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    return {
        "reflection_feedback": feedback,
        "reflection_attempts": attempts,
        "execution_error": None,
        "audit_trace": current_trace,
    }
