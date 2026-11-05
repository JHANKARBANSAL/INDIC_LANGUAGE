"""
Sandbox Execution Agent.
Executes candidate SQL inside an isolated, in-memory DuckDB sandbox;
catches runtime errors (syntax, column not found, typing) and reports execution metrics.
"""

from typing import Any, Dict

from indicsql.core.state import IndicSQLState
from indicsql.events.bus import EventBus
from indicsql.events.schemas import ExecutionCompletedEvent
from indicsql.sandbox.duckdb_engine import DuckDBSandbox
from indicsql.sandbox.validator import validate_and_limit_sql

# Reusable global sandbox instance for development
_sandbox: DuckDBSandbox = DuckDBSandbox()


def sandbox_executor_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Executes the generated SQL query in the DuckDB sandbox.
    Handles AST safety checks and runtime execution errors.
    Emits ExecutionCompletedEvent on the EventBus.
    """
    raw_sql = state.get("generated_sql", "")
    is_valid, sanitized_sql_or_err = validate_and_limit_sql(raw_sql)

    if not is_valid:
        EventBus.publish(
            ExecutionCompletedEvent(
                query_id=state.get("query_id"),
                exit_code=1,
                row_count=0,
                execution_time_ms=0.0,
                success=False,
            )
        )
        return {
            "syntax_valid": False,
            "execution_error": sanitized_sql_or_err,
            "execution_result": None,
        }

    try:
        result = _sandbox.execute_query(sanitized_sql_or_err)

        EventBus.publish(
            ExecutionCompletedEvent(
                query_id=state.get("query_id"),
                exit_code=0,
                row_count=result["row_count"],
                execution_time_ms=result["execution_time_ms"],
                success=True,
            )
        )

        audit_entry = {
            "step": 4,
            "agent": "SandboxExecutionAgent",
            "action": "duckdb_in_memory_run",
            "execution_time_ms": result["execution_time_ms"],
            "row_count": result["row_count"],
            "status": "success",
        }
        current_trace = list(state.get("audit_trace", []))
        current_trace.append(audit_entry)

        return {
            "execution_result": result,
            "execution_error": None,
            "audit_trace": current_trace,
        }
    except Exception as exc:
        err_msg = str(exc)

        EventBus.publish(
            ExecutionCompletedEvent(
                query_id=state.get("query_id"),
                exit_code=1,
                row_count=0,
                execution_time_ms=0.0,
                success=False,
            )
        )

        audit_entry = {
            "step": 4,
            "agent": "SandboxExecutionAgent",
            "action": "duckdb_in_memory_run",
            "status": "error",
            "error": err_msg,
        }
        current_trace = list(state.get("audit_trace", []))
        current_trace.append(audit_entry)

        return {
            "execution_result": None,
            "execution_error": err_msg,
            "audit_trace": current_trace,
        }
