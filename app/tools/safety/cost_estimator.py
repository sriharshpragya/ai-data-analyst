"""
Query cost estimation using PostgreSQL EXPLAIN.
Prevents runaway queries before execution.
"""
import psycopg2
import psycopg2.extras
import structlog

from app.config import Config

logger = structlog.get_logger()


def _get_connection():
    return psycopg2.connect(Config.DATABASE_URL)


def estimate_query_cost(query: str) -> dict:
    """
    Estimate query cost using EXPLAIN. Does NOT execute the query.
    
    Returns:
        dict with cost estimates and safety verdict
    """
    logger.info("estimating_query_cost", query=query[:100])
    
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        explain_query = f"EXPLAIN (FORMAT JSON) {query}"
        cursor.execute(explain_query)
        
        result = cursor.fetchone()
        plan_data = result['QUERY PLAN'][0]
        plan = plan_data['Plan']
        
        startup_cost = plan.get('Startup Cost', 0)
        total_cost = plan.get('Total Cost', 0)
        estimated_rows = plan.get('Plan Rows', 0)
        estimated_width = plan.get('Plan Width', 0)
        
        estimated_bytes = estimated_rows * estimated_width
        estimated_mb = estimated_bytes / (1024 * 1024)
        
        is_safe = True
        warnings = []
        errors = []
        
        if total_cost > Config.MAX_QUERY_COST:
            is_safe = False
            errors.append(f"Query too expensive: {total_cost:.0f} > {Config.MAX_QUERY_COST}")
        
        if estimated_rows > 100000:
            is_safe = False
            errors.append(f"Query returns too many rows: {estimated_rows:,}")
        
        if estimated_mb > 100:
            warnings.append(f"Large result size: {estimated_mb:.1f}MB")
        
        node_type = plan.get('Node Type', '')
        if 'Seq Scan' in str(plan):
            warnings.append("Sequential scan detected (consider adding index)")
        
        logger.info(
            "query_cost_estimated",
            total_cost=total_cost,
            estimated_rows=estimated_rows,
            is_safe=is_safe,
        )
        
        return {
            "safe": is_safe,
            "errors": errors,
            "warnings": warnings,
            "estimated_cost": total_cost,
            "estimated_rows": estimated_rows,
            "estimated_size_mb": round(estimated_mb, 2),
            "node_type": node_type,
        }
    
    except psycopg2.errors.SyntaxError as e:
        return {
            "safe": False,
            "errors": [f"SQL syntax error: {str(e)}"],
            "warnings": [],
        }
    
    except Exception as e:
        logger.error("cost_estimation_error", error=str(e))
        return {
            "safe": False,
            "errors": [f"Cost estimation failed: {str(e)}"],
            "warnings": [],
        }
    
    finally:
        if conn:
            conn.close()
