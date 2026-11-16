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
from indicsql.sandbox.validator import (
    validate_and_limit_sql,
    validate_postgres_readonly_sql,
    validate_postgres_schema_sql,
)

# Reusable global sandbox instance for development
_sandbox: DuckDBSandbox = DuckDBSandbox()


def sandbox_executor_node(
    state: IndicSQLState, sandbox: Any = None
) -> Dict[str, Any]:
    """
    Executes the generated SQL query in the DuckDB sandbox.
    Handles AST safety checks and runtime execution errors.
    Emits ExecutionCompletedEvent on the EventBus.
    """
    raw_sql = state.get("generated_sql", "")
    dialect = state.get("database_dialect", "duckdb")
    if dialect == "postgres":
        is_valid, sanitized_sql_or_err = validate_postgres_readonly_sql(raw_sql)
    else:
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
            "schema_validation_error": None,
        }

    if dialect == "postgres":
        schema_valid, schema_sql_or_err = validate_postgres_schema_sql(
            sanitized_sql_or_err,
            state.get("database_schema_full", state.get("database_schema", {})),
        )
        if not schema_valid:
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
                "action": "postgres_schema_validation",
                "status": "error",
                "error": schema_sql_or_err,
            }
            current_trace = list(state.get("audit_trace", []))
            current_trace.append(audit_entry)
            return {
                "syntax_valid": True,
                "execution_error": schema_sql_or_err,
                "execution_result": None,
                "schema_validation_error": schema_sql_or_err,
                "audit_trace": current_trace,
            }

    try:
        execution_sandbox = sandbox or _sandbox
        if dialect == "postgres":
            result = execution_sandbox.execute_query(
                sanitized_sql_or_err,
                schema_name=state.get("database_schema_name", ""),
            )
        else:
            result = execution_sandbox.execute_query(sanitized_sql_or_err)

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
            "action": "postgres_readonly_run" if dialect == "postgres" else "duckdb_in_memory_run",
            "execution_time_ms": result["execution_time_ms"],
            "row_count": result["row_count"],
            "status": "success",
        }
        current_trace = list(state.get("audit_trace", []))
        current_trace.append(audit_entry)

        return {
            "execution_result": result,
            "execution_error": None,
            "schema_validation_error": None,
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
            "schema_validation_error": None,
            "audit_trace": current_trace,
        }
