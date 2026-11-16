"""
SQL AST Validator and Sanitizer.
Uses SQLGlot (or fallback tokenizer) to enforce read-only semantics and enforce LIMIT bounds.
"""

import re
from typing import Tuple

import sqlglot
from sqlglot import exp
from sqlglot.errors import OptimizeError, SqlglotError
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope


def validate_and_limit_sql(sql: str, default_limit: int = 1000) -> Tuple[bool, str]:
    """
    Validates that the SQL is a SELECT statement and ensures a safe LIMIT clause exists.
    Returns:
        (is_valid, modified_or_error_sql)
    """
    cleaned = sql.strip().rstrip(";")
    upper = cleaned.upper()

    # Block data modifying statements
    prohibited = ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE ", "CREATE "]
    for word in prohibited:
        if word in upper:
            return False, f"Prohibited mutation clause detected: {word.strip()}"

    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        return False, "Only SELECT or WITH queries are permitted in the execution sandbox."

    # Enforce LIMIT if not present
    if "LIMIT " not in upper:
        cleaned += f" LIMIT {default_limit}"

    return True, cleaned + ";"


def validate_postgres_readonly_sql(sql: str) -> Tuple[bool, str]:
    """Accept exactly one read-only PostgreSQL query and return normalized SQL."""
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except Exception as exc:
        return False, f"Invalid PostgreSQL SQL: {exc}"

    if len(statements) != 1 or statements[0] is None:
        return False, "Exactly one SQL statement is permitted."

    statement = statements[0]
    if not isinstance(statement, (exp.Select, exp.Union)):
        return False, "Only SELECT or WITH queries are permitted."

    prohibited = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Command)
    if any(isinstance(node, prohibited) for node in statement.walk()):
        return False, "Only read-only SQL is permitted."

    return True, statement.sql(dialect="postgres")


def validate_postgres_schema_sql(sql: str, schema: dict) -> Tuple[bool, str]:
    """Validate referenced PostgreSQL tables and columns against a supplied schema."""
    valid, normalized_sql = validate_postgres_readonly_sql(sql)
    if not valid:
        return False, normalized_sql

    tables = schema.get("tables", {})
    if not tables:
        return False, "Schema validation failed: no table metadata is available."

    tables_by_name = {name.lower(): (name, metadata) for name, metadata in tables.items()}
    try:
        statement = sqlglot.parse_one(normalized_sql, read="postgres")
    except SqlglotError as exc:
        return False, f"Schema validation failed: invalid SQL: {exc}"

    referenced_tables: set[str] = set()
    expected_schema = schema.get("schema_name")
    for scope in traverse_scope(statement):
        for source in scope.sources.values():
            if not isinstance(source, exp.Table):
                continue
            identifier = source.this
            table_name = source.name
            lookup_name = (
                table_name
                if isinstance(identifier, exp.Identifier) and identifier.args.get("quoted")
                else table_name.lower()
            )
            table_entry = tables_by_name.get(lookup_name.lower())
            if table_entry is None or (
                isinstance(identifier, exp.Identifier)
                and identifier.args.get("quoted")
                and lookup_name not in tables
            ):
                allowed = ", ".join(sorted(tables))
                return (
                    False,
                    f"Schema validation failed: unknown table {table_name!r}. "
                    f"Allowed tables: {allowed}.",
                )
            if source.db and expected_schema and source.db.casefold() != expected_schema.casefold():
                return (
                    False,
                    f"Schema validation failed: table {table_name!r} uses schema "
                    f"{source.db!r}; expected {expected_schema!r}.",
                )
            referenced_tables.add(table_entry[0])

    sqlglot_schema = {
        table_name: {column.lower(): "UNKNOWN" for column in metadata.get("columns", {})}
        for table_name, metadata in tables.items()
    }
    try:
        qualify(
            statement.copy(),
            dialect="postgres",
            schema=sqlglot_schema,
            validate_qualify_columns=True,
            expand_stars=False,
            quote_identifiers=False,
            identify=False,
        )
    except (OptimizeError, SqlglotError, ValueError) as exc:
        message = str(exc)
        unresolved = re.search(
            r"Column ['\"](?P<column>[^'\"]+)['\"] could not be resolved",
            message,
            re.IGNORECASE,
        )
        if unresolved:
            column_name = unresolved.group("column").lower()
            candidates = [
                f"{table}.{column_name}"
                for table in sorted(referenced_tables)
                if column_name
                in {column.lower() for column in tables[table].get("columns", {})}
            ]
            if len(candidates) > 1:
                message = (
                    f"Ambiguous unqualified column {column_name!r}; qualify it as one "
                    f"of: {', '.join(candidates)}."
                )
        allowed_columns = "; ".join(
            f"{table}: {', '.join(tables[table].get('columns', {}))}"
            for table in sorted(referenced_tables)
        )
        return (
            False,
            f"Schema validation failed: {message}. "
            f"Allowed columns in referenced tables: {allowed_columns}.",
        )

    return True, normalized_sql


def repair_missing_foreign_key_join(sql: str, schema: dict) -> tuple[str, list[str]]:
    """Add an unambiguous FK join when a query references a parent-only column."""
    try:
        statement = sqlglot.parse_one(sql, read="postgres")
    except Exception:
        return sql, []
    if not isinstance(statement, exp.Select) or statement.args.get("joins"):
        return sql, []

    from_clause = statement.args.get("from_")
    base_table = from_clause.this if from_clause else None
    if not isinstance(base_table, exp.Table):
        return sql, []

    tables = schema.get("tables", {})
    base_name = base_table.name.lower()
    base_metadata = tables.get(base_name)
    if not base_metadata:
        return sql, []

    base_columns = {column.lower() for column in base_metadata.get("columns", {})}
    columns_to_tables: dict[str, list[str]] = {}
    for table_name, metadata in tables.items():
        for column_name in metadata.get("columns", {}):
            columns_to_tables.setdefault(column_name.lower(), []).append(table_name)

    fixes: dict[str, tuple[str, str, str]] = {}
    for column in statement.find_all(exp.Column):
        column_name = column.name.lower()
        if column.table or column_name in base_columns:
            continue
        candidates = columns_to_tables.get(column_name, [])
        if len(candidates) != 1:
            continue
        target_table = candidates[0]
        for relationship in base_metadata.get("foreign_keys", []):
            try:
                child_ref, parent_ref = relationship.split(" references ", 1)
                child_column = child_ref.split()[0].lower()
                parent_table, parent_column = parent_ref.split(".", 1)
            except ValueError:
                continue
            if parent_table.lower() == target_table:
                fixes[column_name] = (target_table, child_column, parent_column.lower())
                break

    if not fixes:
        return sql, []

    base_alias = base_table.alias_or_name
    joined: set[str] = set()
    repairs = []
    for column_name, (target_table, child_column, parent_column) in fixes.items():
        if target_table not in joined:
            join_table = exp.Table(this=exp.to_identifier(target_table))
            join_condition = exp.EQ(
                this=exp.column(child_column, table=base_alias),
                expression=exp.column(parent_column, table=target_table),
            )
            statement = statement.join(join_table, on=join_condition)
            joined.add(target_table)
        for column in statement.find_all(exp.Column):
            if not column.table and column.name.lower() == column_name:
                column.set("table", exp.to_identifier(target_table))
        repairs.append(
            f"Joined {base_name}.{child_column} to {target_table}.{parent_column} "
            f"for column {column_name}."
        )

    return statement.sql(dialect="postgres"), repairs
