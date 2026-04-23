"""
NL-to-SQL Generator — converts natural language questions to SQL using local LLM.
Includes improved prompts with examples, better validation, and intent detection.
"""
from __future__ import annotations

import re
from typing import Dict, Any
from loguru import logger

from config.llm_provider import invoke as llm_invoke
from sql_agent.schema_reader import get_schema_string

INTENT_TYPES = ["aggregation", "trend", "comparison", "lookup", "mixed"]

# ── SQL query cache (avoids re-generating identical queries) ──────────────────
_query_cache: dict[str, dict] = {}
_CACHE_MAX_SIZE = 100


def _extract_sql(llm_response: str) -> str:
    """Strip markdown fences and prose from LLM output, return bare SQL."""
    # Try to find ```sql ... ``` block
    match = re.search(r"```(?:sql)?\s*([\s\S]+?)```", llm_response, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Look for SELECT/WITH statement
    match = re.search(
        r"((?:WITH|SELECT)\s+[\s\S]+?;?)\s*$",
        llm_response,
        re.IGNORECASE | re.MULTILINE,
    )
    if match:
        return match.group(1).strip()

    # Last resort: return everything after "SQL:" if present
    if "SQL:" in llm_response.upper():
        return llm_response[llm_response.upper().index("SQL:") + 4:].strip()

    return llm_response.strip()


def _validate_sql(sql: str) -> bool:
    """Validate SQL for safety and syntactic plausibility."""
    if not sql:
        return False
    upper = sql.upper().strip()

    # Must start with a read-only keyword
    allowed_starts = ("SELECT", "WITH", "EXPLAIN")
    if not any(upper.startswith(k) for k in allowed_starts):
        return False

    # Block destructive statements
    destructive = ("DROP ", "DELETE ", "INSERT ", "UPDATE ", "TRUNCATE ", "ALTER ", "CREATE ", "REPLACE ")
    if any(k in upper for k in destructive):
        return False

    # Block system commands
    if any(k in upper for k in ("ATTACH ", "DETACH ", "PRAGMA ", ".IMPORT", ".SHELL")):
        return False

    # Must contain at least a FROM clause (basic structure check)
    if "FROM" not in upper and "SELECT 1" not in upper:
        return False

    return True


def _detect_intent(question: str, sql: str) -> str:
    """Heuristic intent classification based on question and generated SQL."""
    q_lower = question.lower()
    sql_lower = sql.lower()

    if any(w in q_lower for w in ["trend", "over time", "month", "week", "daily", "historical", "growth"]):
        return "trend"
    if any(w in q_lower for w in ["compare", "vs", "versus", "difference", "between"]):
        return "comparison"
    if any(w in sql_lower for w in ["sum(", "avg(", "count(", "max(", "min(", "group by"]):
        return "aggregation"
    if any(w in q_lower for w in ["find", "show me", "what is", "who is", "list", "which"]):
        return "lookup"
    return "mixed"


def _normalize_question(question: str) -> str:
    """Normalize a question for cache key purposes."""
    return " ".join(question.lower().split())


def generate_sql(question: str, schema: str = None) -> Dict[str, Any]:
    """
    Convert a natural language question to SQL.

    Returns:
        {sql, intent_type, confidence, raw_response, error}
    """
    # Check cache
    cache_key = _normalize_question(question)
    if cache_key in _query_cache:
        logger.info(f"[QueryGen] Cache hit for: '{question[:50]}'")
        return _query_cache[cache_key]

    if schema is None:
        schema = get_schema_string()

    prompt = f"""Write a SQLite query to answer this question. Output ONLY the SQL in ```sql``` fences.

Rules: SELECT only, use aliases, LIMIT 50, ROUND monetary values, ORDER BY meaningfully.

SCHEMA:
{schema}

QUESTION: {question}

```sql"""

    try:
        response = llm_invoke(prompt, max_tokens=512)
        sql = _extract_sql(response)

        if not _validate_sql(sql):
            logger.warning(f"[QueryGen] Invalid SQL generated for: '{question}'")
            return {
                "sql": "",
                "intent_type": "unknown",
                "confidence": 0.0,
                "raw_response": response,
                "error": "Generated SQL failed validation (may contain unsafe operations)",
            }

        intent = _detect_intent(question, sql)
        logger.info(f"[QueryGen] Question: '{question[:60]}' -> intent: {intent}")
        logger.debug(f"[QueryGen] SQL: {sql[:200]}")

        result = {
            "sql": sql,
            "intent_type": intent,
            "confidence": 0.85,
            "raw_response": response,
            "error": None,
        }

        # Cache the result
        if len(_query_cache) >= _CACHE_MAX_SIZE:
            # Evict oldest entry
            oldest_key = next(iter(_query_cache))
            del _query_cache[oldest_key]
        _query_cache[cache_key] = result

        return result

    except Exception as e:
        logger.error(f"[QueryGen] LLM call failed: {e}")
        return {
            "sql": "",
            "intent_type": "unknown",
            "confidence": 0.0,
            "raw_response": "",
            "error": str(e),
        }


def clear_cache():
    """Clear the SQL query cache."""
    _query_cache.clear()
    logger.info("[QueryGen] Cache cleared.")
