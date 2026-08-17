"""
SQL execution tool with comprehensive safety.
Combines: validation + cost estimation + timeout + execution.
"""
import psycopg2
import psycopg2.extras
from typing import Optional
from decimal import Decimal
from datetime import datetime, date
import structlog

from app.config import Config
from app.tools.safety import validate_query, estimate_query_cost

logger = structlog.get_logger()


def _get_connection():
    """Get connection with statement timeout."""
    conn = psycopg2.connect(Config.DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute(f"SET statement_timeout = {Config.QUERY_TIMEOUT_SECONDS * 1000}")
    conn.commit()
    return conn


def _serialize_value(value):
    """Convert PostgreSQL types to JSON-serializable."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def safe_run_sql(query: str, max_rows: Optional[int] = None) -> dict:
    """
    Execute SQL query with full safety guardrails.
    """
    logger.info("safe_sql_requested", query=query[:200])
    
    if max_rows is None:
        max_rows = Config.DEFAULT_ROWS_PER_QUERY
    max_rows = min(max_rows, Config.MAX_ROWS_PER_QUERY)
    
    # Layer 1: Validation
    validation = validate_query(query)
    if not validation["safe"]:
        logger.warning("query_rejected_by_validator", errors=validation["errors"])
        return {
            "error": "unsafe_query",
            "message": "Query rejected by safety validator",
            "details": validation["errors"],
            "hint": "Only SELECT queries are allowed",
        }
    
    safe_query = validation["sanitized_query"]
    
    # Layer 2: Cost estimation
    cost_check = estimate_query_cost(safe_query)
    if not cost_check["safe"]:
        logger.warning("query_rejected_by_cost", errors=cost_check["errors"])
        return {
            "error": "query_too_expensive",
            "message": "Query would be too expensive to execute",
            "details": cost_check["errors"],
            "estimated_cost": cost_check.get("estimated_cost"),
            "estimated_rows": cost_check.get("estimated_rows"),
            "hint": "Try adding more specific WHERE clauses or LIMIT",
        }
    
    # Layer 3: Execute with timeout
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(safe_query)
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchmany(max_rows)
            
            results = []
            for row in rows:
                serialized = {k: _serialize_value(v) for k, v in dict(row).items()}
                results.append(serialized)
            
            has_more = cursor.fetchone() is not None
            
            logger.info(
                "safe_query_completed",
                rows_returned=len(results),
                has_more=has_more,
            )
            
            return {
                "query": safe_query,
                "columns": columns,
                "rows": results,
                "row_count": len(results),
                "truncated": has_more,
                "max_rows": max_rows,
                "warnings": validation.get("warnings", []) + cost_check.get("warnings", []),
                "estimated_cost": cost_check.get("estimated_cost"),
            }
        else:
            return {
                "error": "unexpected_query_type",
                "message": "Query didn't return results",
            }
    
    except psycopg2.errors.QueryCanceled:
        logger.warning("query_timeout", timeout=Config.QUERY_TIMEOUT_SECONDS)
        return {
            "error": "query_timeout",
            "message": f"Query exceeded {Config.QUERY_TIMEOUT_SECONDS}s timeout",
            "hint": "Try adding filters or LIMIT to reduce data",
        }
    
    except psycopg2.Error as e:
        logger.error("postgresql_error", error=str(e))
        return {
            "error": "postgresql_error",
            "message": str(e),
        }
    
    except Exception as e:
        logger.error("unexpected_error", error_type=type(e).__name__, error=str(e))
        return {
            "error": "unexpected_error",
            "message": f"{type(e).__name__}: {str(e)}",
        }
    
    finally:
        if conn:
            conn.close()


# Tool schema for LLM
safe_run_sql_schema = {
    "type": "function",
    "function": {
        "name": "safe_run_sql",
        "description": (
            "Execute a READ-ONLY SQL query against the database. "
            "Only SELECT queries are allowed. Queries are validated for safety, "
            "cost is estimated, and execution is time-limited to 10 seconds. "
            "Returns query results as structured data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SELECT query (PostgreSQL syntax). Modifications not allowed."
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows to return (default: 100, max: 1000)",
                    "minimum": 1,
                    "maximum": 1000,
                }
            },
            "required": ["query"]
        }
    }
}
