"""
SQL Verification Critic Node.
Validates SQL using SQLGlot AST parsing against deterministic security and correctness rules:
Enforces strictly read-only analytical statements (SELECT / WITH / UNION),
blocks destructive mutations (DROP, DELETE, UPDATE, INSERT, ALTER),
and prevents false-positive rejections when keywords like 'DROP' or 'GRANT'
appear legitimately inside string literals.
"""

import logging
from typing import Any, Dict

import sqlglot
from sqlglot import exp

from indicsql.core.state import IndicSQLState

logger = logging.getLogger(__name__)

FORBIDDEN_EXPRESSION_TYPES = (
    exp.Drop,
    exp.Delete,
    exp.Update,
    exp.Insert,
    exp.Alter,
    exp.Command,
)


def validate_sql_security(sql: str) -> bool:
    """
    Parses SQL AST using SQLGlot to ensure strict read-only execution.
    Inspects expression node types rather than naive substring matching.
    """
    if not sql or not sql.strip():
        return False

    try:
        parsed = sqlglot.parse_one(sql.strip(), read="duckdb")
        if not parsed:
            return False

        # Only SELECT, UNION, or CTE (WITH expressions) are allowed as root statements
        if not isinstance(parsed, (exp.Select, exp.Union)):
            return False

        # Ensure no mutation statement is embedded anywhere in the AST tree
        for node in parsed.walk():
            if isinstance(node, FORBIDDEN_EXPRESSION_TYPES):
                logger.warning("Dangerous SQL mutation node blocked by Critic AST parser: %s", type(node).__name__)
                return False

        return True
    except Exception as exc:
        logger.debug("SQLGlot failed to parse query (%s), falling back to safe check", exc)
        cleaned = sql.strip().upper()
        if not cleaned.startswith("SELECT") and not cleaned.startswith("WITH"):
            return False
        for forbidden in ["DROP TABLE", "DELETE FROM", "UPDATE ", "INSERT INTO", "ALTER TABLE", "TRUNCATE "]:
            if forbidden in cleaned:
                return False
        return True


def critic_node(state: IndicSQLState) -> Dict[str, Any]:
    """
    Critic Node: Analyzes candidate SQL and blocks security violations.
    """
    sql = state.get("generated_sql", "")
    is_safe = validate_sql_security(sql)

    audit_entry = {
        "step": 3.5,
        "agent": "CriticNode",
        "action": "ast_security_validation",
        "is_safe": is_safe,
    }

    current_trace = list(state.get("audit_trace", []))
    current_trace.append(audit_entry)

    if not is_safe:
        return {
            "syntax_valid": False,
            "execution_error": "Security Exception: Non-SELECT mutation detected in candidate query.",
            "audit_trace": current_trace,
        }

    return {
        "syntax_valid": True,
        "audit_trace": current_trace,
    }
