"""
SQL Safety Validator.
Multi-layer defense against destructive queries.
"""
import re
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML, DDL
from typing import Tuple, List
import structlog

from app.config import Config

logger = structlog.get_logger()


# ============================================
# CONFIGURATION
# ============================================

ALLOWED_STATEMENT_TYPES = {
    'SELECT', 'EXPLAIN', 'SHOW', 'DESCRIBE', 'DESC', 'WITH',
}

BLOCKED_KEYWORDS = {
    'DROP', 'TRUNCATE', 'DELETE',
    'INSERT', 'UPDATE', 'MERGE', 'UPSERT', 'REPLACE',
    'ALTER', 'CREATE', 'RENAME',
    'GRANT', 'REVOKE',
    'COMMIT', 'ROLLBACK', 'BEGIN', 'START',
    'SAVEPOINT', 'RELEASE',
    'LOCK', 'UNLOCK',
    'SET',
    'COPY',
    'EXECUTE', 'EXEC', 'CALL',
    'SHUTDOWN', 'KILL',
}

DANGEROUS_PATTERNS = [
    r"'\s*OR\s*'?\d+'?\s*=\s*'?\d+",
    r"'\s*OR\s*'.*'\s*=\s*'",
    r";\s*DROP\s+",
    r";\s*DELETE\s+",
    r";\s*INSERT\s+",
    r";\s*UPDATE\s+",
    r"--\s*$",
    r"/\*.*\*/",
    r"pg_catalog\.",
    r"pg_shadow",
    r"pg_user",
    r"information_schema\.role",
    r"pg_authid",
    r"pg_read_file",
    r"pg_ls_dir",
    r"pg_read_server_files",
    r"pg_write_server_files",
    r"COPY\s+.*\s+FROM\s+PROGRAM",
    r"COPY\s+.*\s+TO\s+PROGRAM",
    r"pg_sleep\s*\(",
]

MAX_STATEMENT_COUNT = 1


def _has_dangerous_patterns(query: str) -> Tuple[bool, str]:
    for pattern in DANGEROUS_PATTERNS:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return True, f"Dangerous pattern detected: {match.group()}"
    return False, ""


def _get_statement_type(statement: Statement) -> str:
    for token in statement.tokens:
        if token.ttype is DDL or token.ttype is DML or token.ttype is Keyword:
            return token.value.upper()
        if hasattr(token, 'value'):
            first_word = token.value.strip().split()[0].upper() if token.value.strip() else ""
            if first_word in ALLOWED_STATEMENT_TYPES or first_word in BLOCKED_KEYWORDS:
                return first_word
    return "UNKNOWN"


def _check_blocked_keywords(query: str) -> Tuple[bool, List[str]]:
    query_upper = query.upper()
    found_keywords = []
    
    for keyword in BLOCKED_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_upper):
            found_keywords.append(keyword)
    
    return len(found_keywords) > 0, found_keywords


def _count_statements(query: str) -> int:
    parsed = sqlparse.parse(query)
    real_statements = [s for s in parsed if s.tokens and str(s).strip()]
    return len(real_statements)


def _ensure_limit(query: str, max_limit: int = None) -> str:
    if max_limit is None:
        max_limit = Config.DEFAULT_ROWS_PER_QUERY
    
    limit_pattern = re.compile(r'\bLIMIT\s+(\d+)\b', re.IGNORECASE)
    match = limit_pattern.search(query)
    
    if match:
        current_limit = int(match.group(1))
        if current_limit > Config.MAX_ROWS_PER_QUERY:
            return limit_pattern.sub(f'LIMIT {Config.MAX_ROWS_PER_QUERY}', query)
        return query
    else:
        query = query.rstrip().rstrip(';')
        return f"{query} LIMIT {max_limit}"


def validate_query(query: str) -> dict:
    """
    Comprehensive SQL safety validation.
    
    Returns:
        dict with 'safe': bool, 'errors': list, 'warnings': list, 'sanitized_query': str
    """
    errors = []
    warnings = []
    
    if not query or not query.strip():
        return {
            "safe": False,
            "errors": ["Query is empty"],
            "warnings": [],
            "sanitized_query": None,
        }
    
    if len(query) > Config.MAX_QUERY_LENGTH:
        errors.append(f"Query too long ({len(query)} chars, max {Config.MAX_QUERY_LENGTH})")
    
    try:
        parsed = sqlparse.parse(query)
    except Exception as e:
        return {
            "safe": False,
            "errors": [f"Could not parse SQL: {str(e)}"],
            "warnings": [],
            "sanitized_query": None,
        }
    
    statement_count = _count_statements(query)
    if statement_count > MAX_STATEMENT_COUNT:
        errors.append(f"Multiple statements not allowed (found {statement_count})")
    
    if not parsed or not parsed[0].tokens:
        errors.append("Empty or invalid SQL")
    
    if errors:
        return {
            "safe": False,
            "errors": errors,
            "warnings": warnings,
            "sanitized_query": None,
        }
    
    statement = parsed[0]
    statement_type = _get_statement_type(statement)
    
    if statement_type not in ALLOWED_STATEMENT_TYPES:
        errors.append(f"Statement type '{statement_type}' not allowed. Only SELECT queries permitted.")
    
    has_blocked, blocked_keywords = _check_blocked_keywords(query)
    if has_blocked:
        errors.append(f"Blocked keywords found: {', '.join(blocked_keywords)}")
    
    has_dangerous, danger_msg = _has_dangerous_patterns(query)
    if has_dangerous:
        errors.append(danger_msg)
    
    if errors:
        return {
            "safe": False,
            "errors": errors,
            "warnings": warnings,
            "sanitized_query": None,
        }
    
    sanitized = _ensure_limit(query)
    
    if sanitized != query:
        warnings.append("Query was modified: LIMIT enforced")
    
    return {
        "safe": True,
        "errors": [],
        "warnings": warnings,
        "sanitized_query": sanitized,
        "statement_type": statement_type,
    }
