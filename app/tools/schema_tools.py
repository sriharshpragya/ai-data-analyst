"""
Schema exploration tools for SQL agent.
Uses PostgreSQL information_schema (SQL standard, portable).
"""
import psycopg2
import psycopg2.extras
from typing import Optional
import structlog

from app.config import Config

logger = structlog.get_logger()


def _get_connection():
    return psycopg2.connect(Config.DATABASE_URL)


def list_tables(schema: str = "public") -> dict:
    """List all tables in the database schema."""
    logger.info("list_tables_requested", schema=schema)
    
    query = """
        SELECT 
            table_name,
            table_type,
            (SELECT COUNT(*) 
             FROM information_schema.columns 
             WHERE table_name = t.table_name 
             AND table_schema = t.table_schema) as column_count
        FROM information_schema.tables t
        WHERE table_schema = %s
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, (schema,))
        tables = [dict(row) for row in cursor.fetchall()]
        
        return {
            "schema": schema,
            "table_count": len(tables),
            "tables": tables,
        }
    except Exception as e:
        logger.error("list_tables_error", error=str(e))
        return {"error": "list_tables_failed", "message": str(e)}
    finally:
        if conn:
            conn.close()


def describe_table(table_name: str) -> dict:
    """Get detailed structure of a specific table."""
    logger.info("describe_table_requested", table_name=table_name)
    
    columns_query = """
        SELECT 
            column_name, data_type, character_maximum_length,
            numeric_precision, numeric_scale, is_nullable,
            column_default, ordinal_position
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position
    """
    
    pk_query = """
        SELECT column_name
        FROM information_schema.key_column_usage kcu
        JOIN information_schema.table_constraints tc 
            ON kcu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
        AND tc.table_name = %s AND tc.table_schema = 'public'
    """
    
    fk_query = """
        SELECT kcu.column_name,
               ccu.table_name AS references_table,
               ccu.column_name AS references_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = %s AND tc.table_schema = 'public'
    """
    
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = %s AND table_schema = 'public'",
            (table_name,)
        )
        if not cursor.fetchone():
            return {
                "error": "table_not_found",
                "message": f"Table '{table_name}' does not exist",
                "hint": "Use list_tables to see available tables",
            }
        
        cursor.execute(columns_query, (table_name,))
        columns = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute(pk_query, (table_name,))
        primary_keys = [row['column_name'] for row in cursor.fetchall()]
        
        cursor.execute(fk_query, (table_name,))
        foreign_keys = [dict(row) for row in cursor.fetchall()]
        
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = cursor.fetchone()['count']
        except:
            row_count = None
        
        formatted_columns = []
        for col in columns:
            col_info = {
                "name": col['column_name'],
                "type": col['data_type'],
                "nullable": col['is_nullable'] == 'YES',
                "default": col['column_default'],
            }
            if col['character_maximum_length']:
                col_info['max_length'] = col['character_maximum_length']
            if col['numeric_precision']:
                col_info['precision'] = col['numeric_precision']
            if col['column_name'] in primary_keys:
                col_info['is_primary_key'] = True
            fk = next((f for f in foreign_keys if f['column_name'] == col['column_name']), None)
            if fk:
                col_info['references'] = f"{fk['references_table']}.{fk['references_column']}"
            formatted_columns.append(col_info)
        
        return {
            "table_name": table_name,
            "row_count": row_count,
            "columns": formatted_columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
        }
    
    except Exception as e:
        logger.error("describe_table_error", error=str(e))
        return {"error": "describe_table_failed", "message": str(e)}
    finally:
        if conn:
            conn.close()


def get_relationships(table_name: Optional[str] = None) -> dict:
    """Get foreign key relationships between tables."""
    logger.info("get_relationships_requested", table_name=table_name)
    
    base_query = """
        SELECT
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
    """
    
    if table_name:
        query = base_query + " AND (tc.table_name = %s OR ccu.table_name = %s) ORDER BY tc.table_name, kcu.column_name"
        params = (table_name, table_name)
    else:
        query = base_query + " ORDER BY tc.table_name, kcu.column_name"
        params = ()
    
    conn = None
    try:
        conn = _get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params)
        relationships = [dict(row) for row in cursor.fetchall()]
        
        return {
            "table_filter": table_name,
            "relationship_count": len(relationships),
            "relationships": relationships,
        }
    except Exception as e:
        logger.error("get_relationships_error", error=str(e))
        return {"error": "get_relationships_failed", "message": str(e)}
    finally:
        if conn:
            conn.close()


# Tool schemas for LLM

list_tables_schema = {
    "type": "function",
    "function": {
        "name": "list_tables",
        "description": "List all tables in the database. Use to discover what tables exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "schema": {
                    "type": "string",
                    "description": "Database schema to search (default: public)",
                }
            },
            "required": []
        }
    }
}

describe_table_schema = {
    "type": "function",
    "function": {
        "name": "describe_table",
        "description": "Get detailed structure of a specific table including columns, types, primary keys, and foreign keys.",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to describe"
                }
            },
            "required": ["table_name"]
        }
    }
}

get_relationships_schema = {
    "type": "function",
    "function": {
        "name": "get_relationships",
        "description": "Get foreign key relationships between tables. Useful for understanding how to JOIN tables.",
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Optional - filter to relationships involving this table"
                }
            },
            "required": []
        }
    }
}
