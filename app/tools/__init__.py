"""Tool registry for the AI Data Analyst Agent."""

from app.tools.sql_tools import safe_run_sql, safe_run_sql_schema
from app.tools.schema_tools import (
    list_tables, list_tables_schema,
    describe_table, describe_table_schema,
    get_relationships, get_relationships_schema,
)
from app.tools.chart_tools import create_chart, create_chart_schema


def get_all_tools():
    """Return list of (schema, function) tuples for all tools."""
    return [
        (safe_run_sql_schema, safe_run_sql),
        (list_tables_schema, list_tables),
        (describe_table_schema, describe_table),
        (get_relationships_schema, get_relationships),
        (create_chart_schema, create_chart),
    ]


def register_all_tools(agent):
    """Register all tools with an agent."""
    for schema, function in get_all_tools():
        agent.register_tool(schema, function)


__all__ = [
    "safe_run_sql", "safe_run_sql_schema",
    "list_tables", "list_tables_schema",
    "describe_table", "describe_table_schema",
    "get_relationships", "get_relationships_schema",
    "create_chart", "create_chart_schema",
    "get_all_tools", "register_all_tools",
]
