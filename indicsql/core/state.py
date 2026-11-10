"""
TypedDict State Definitions for IndicSQL's LangGraph multi-agent architecture.
Matches the formal specification in Section 13 of PLAN.md.
"""

from typing import Any, Dict, List, Optional, TypedDict


class SchemaElement(TypedDict, total=False):
    """Represents a matched database table or column linked from the natural language query."""

    table_name: str
    column_name: str
    data_type: str
    indic_synonyms: List[str]
    is_foreign_key: bool
    foreign_target: Optional[str]


class TabularResult(TypedDict, total=False):
    """Structured tabular output returned by the sandboxed relational execution engine."""

    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time_ms: float


class IndicSQLState(TypedDict, total=False):
    """
    Unified Blackboard State mutated across the LangGraph multi-agent swarm.
    Preserves audit traces, error reflections, and generated artifacts.
    """

    # 1. Input & Normalization
    query_id: str
    raw_query: str
    detected_lang: str  # 'hi', 'bn', 'ta', 'te', 'mr', 'hi-en', 'en'
    detected_script: str  # 'Devanagari', 'Tamil', 'Telugu', 'Bengali', 'Latin'
    canonical_query: str  # Transliterated / Normalized text
    target_database: str  # Name of target NDAP database

    # 2. Schema-Linking Substrate
    pruned_schema: List[SchemaElement]

    # 3. SQL Synthesis & AST Verification
    generated_sql: str
    raw_stochastic_sql: Optional[str]
    syntax_valid: bool

    # 4. Sandbox Execution & Self-Healing Reflection
    execution_result: Optional[TabularResult]
    execution_error: Optional[str]
    reflection_attempts: int

    # 5. Presentation & Localization
    verbalized_response: str  # Mother-tongue natural language answer
    audit_trace: List[Dict[str, Any]]
