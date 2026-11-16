"""
LangGraph Multi-Agent Workflow Definition.
Constructs the cyclic state graph coordinating the IndicSQL agent swarm:
Supervisor -> SchemaLinker -> Synthesizer -> Critic -> SandboxExecutor -> (ReflectionLoop or Verbalizer) -> END
"""

import uuid
from typing import Any, Optional

from indicsql.agents.critic import critic_node
from indicsql.agents.reflection_healer import reflection_healer_node
from indicsql.agents.response_verbalizer import response_verbalizer_node
from indicsql.agents.sandbox_executor import sandbox_executor_node
from indicsql.agents.schema_linker import schema_linker_node
from indicsql.agents.sql_synthesizer import sql_synthesizer_node
from indicsql.agents.supervisor import supervisor_node
from indicsql.core.state import IndicSQLState


def route_after_execution(state: IndicSQLState) -> str:
    """
    Decides the next step after sandboxed execution:
    - 'success': Tabular results retrieved successfully -> Response Verbalizer
    - 'retry': Error or empty rows and attempts < 3 -> Reflection Healer
    - 'fatal_error': Max attempts exceeded -> Response Verbalizer (graceful message)
    """
    error = state.get("execution_error")
    attempts = state.get("reflection_attempts", 0)

    if not error and state.get("execution_result") is not None:
        return "success"
    if state.get("schema_validation_retry_used") and attempts >= 1:
        return "fatal_error"
    if attempts < 3:
        return "retry"
    return "fatal_error"


def create_indicsql_graph(checkpointer: Optional[Any] = None):
    """
    Compiles the LangGraph StateGraph when langgraph is available.
    """
    try:
        from langgraph.checkpoint.memory import MemorySaver  # type: ignore
        from langgraph.graph import END, StateGraph  # type: ignore

        if checkpointer is None:
            checkpointer = MemorySaver()

        workflow = StateGraph(IndicSQLState)

        # Register Swarm Nodes
        workflow.add_node("supervisor_router", supervisor_node)
        workflow.add_node("schema_linker", schema_linker_node)
        workflow.add_node("sql_synthesizer", sql_synthesizer_node)
        workflow.add_node("critic", critic_node)
        workflow.add_node("sandbox_executor", sandbox_executor_node)
        workflow.add_node("reflection_healer", reflection_healer_node)
        workflow.add_node("response_verbalizer", response_verbalizer_node)

        # Set Entry Point
        workflow.set_entry_point("supervisor_router")

        # Define Linear Edges
        workflow.add_edge("supervisor_router", "schema_linker")
        workflow.add_edge("schema_linker", "sql_synthesizer")
        workflow.add_edge("sql_synthesizer", "critic")
        workflow.add_edge("critic", "sandbox_executor")

        # Conditional Reflection Loop
        workflow.add_conditional_edges(
            "sandbox_executor",
            route_after_execution,
            {
                "success": "response_verbalizer",
                "retry": "reflection_healer",
                "fatal_error": "response_verbalizer",
            },
        )

        workflow.add_edge("reflection_healer", "sql_synthesizer")
        workflow.add_edge("response_verbalizer", END)

        return workflow.compile(checkpointer=checkpointer)
    except ImportError:
        # Fallback executor for environments where LangGraph is not yet installed
        return None


def execute_indicsql_pipeline(
    query: str,
    query_id: Optional[str] = None,
    *,
    database_schema_name: Optional[str] = None,
    database_schema: Optional[dict[str, Any]] = None,
    database_schema_source: Optional[str] = None,
    language_override: Optional[str] = None,
    sandbox: Optional[Any] = None,
) -> IndicSQLState:
    """
    Executes the multi-agent swarm for a given query, supporting both LangGraph and native execution.
    """
    if not query_id:
        query_id = f"ind-q-{uuid.uuid4().hex[:8]}"

    state: IndicSQLState = {
        "query_id": query_id,
        "raw_query": query,
        "reflection_attempts": 0,
        "audit_trace": [],
    }
    if database_schema is not None:
        state["database_schema"] = database_schema
        state["database_schema_full"] = database_schema
        state["database_schema_name"] = database_schema_name or ""
        state["database_dialect"] = database_schema.get("dialect", "postgres")
        state["database_schema_source"] = database_schema_source or "provided"

    # Step 1: Supervisor
    state.update(supervisor_node(state))
    if language_override:
        if state.get("detected_lang") != language_override:
            current_trace = list(state.get("audit_trace", []))
            current_trace.append(
                {
                    "step": 1.5,
                    "agent": "BenchmarkLanguageMetadata",
                    "action": "language_override",
                    "detected_language": language_override,
                }
            )
            state["audit_trace"] = current_trace
        state["detected_lang"] = language_override

    # Step 2: Schema Linker
    state.update(schema_linker_node(state))
    if state.get("schema_linking_error"):
        state["generated_sql"] = ""
        state["execution_result"] = None
        state["execution_time_ms"] = 0.0
        state["execution_error"] = state["schema_linking_error"]
        state.update(response_verbalizer_node(state))
        return state

    # Step 3: Loop with Reflection
    while True:
        # Synthesize SQL
        try:
            state.update(sql_synthesizer_node(state))
        except (RuntimeError, ValueError) as exc:
            state["generated_sql"] = ""
            state["execution_result"] = None
            state["execution_error"] = f"SQL synthesis failed: {exc}"
            state.update(response_verbalizer_node(state))
            return state

        # Critic security check
        state.update(critic_node(state))
        if not state.get("syntax_valid", True):
            break

        # Sandbox execution
        state.update(sandbox_executor_node(state, sandbox=sandbox))

        decision = route_after_execution(state)
        if decision == "success" or decision == "fatal_error":
            break
        elif decision == "retry":
            if state.get("schema_validation_error"):
                state["schema_validation_retry_used"] = True
            full_schema = state.get("database_schema_full")
            current_schema = state.get("database_schema", {})
            full_tables = set(full_schema.get("tables", {})) if full_schema else set()
            current_tables = set(current_schema.get("tables", {}))
            if (
                state.get("schema_validation_error")
                and full_schema
                and full_tables != current_tables
            ):
                state["database_schema"] = full_schema
                state["schema_context_broadened"] = True
                current_trace = list(state.get("audit_trace", []))
                current_trace.append(
                    {
                        "step": 4.25,
                        "agent": "SchemaValidation",
                        "action": "broadened_schema_context",
                    }
                )
                state["audit_trace"] = current_trace
            state.update(reflection_healer_node(state))

    # Step 4: Response Verbalizer
    state.update(response_verbalizer_node(state))

    return state
