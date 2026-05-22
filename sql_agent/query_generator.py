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


def generate_sql(question: str, schema: str = None, business_id: str = None) -> Dict[str, Any]:
    """
    Convert a natural language question to SQL.

    Returns:
        {sql, intent_type, confidence, raw_response, error}
    """
    # Cache key includes business_id so two tenants asking the same
    # question don't share results.
    cache_key = _normalize_question(question) + f"|biz={business_id or '_'}"
    if cache_key in _query_cache:
        logger.info(f"[QueryGen] Cache hit for: '{question[:50]}'")
        return _query_cache[cache_key]

    if schema is None:
        schema = get_schema_string()

    from config.db import is_postgres
    if is_postgres():
        dialect = "PostgreSQL"
        dialect_rules = (
            "Use PostgreSQL syntax. Quote identifiers with double quotes \"\" "
            "(never backticks). Use CAST(x AS NUMERIC) for casting, NOT "
            "CAST(x AS REAL). For dates use date_trunc('month', col) / EXTRACT, "
            "NOT strftime. For string concat use CONCAT() or ||. Trailing "
            "semicolons are fine but optional, never use multiple statements."
        )
    else:
        dialect = "SQLite"
        dialect_rules = (
            "Use SQLite syntax. Identifiers can be bare; if quoting use "
            "double quotes \"\". Use strftime for date formatting."
        )

    # Tenant scoping. Every business-scoped table (nexus_contacts,
    # nexus_invoices, nexus_deals, nexus_tasks, nexus_companies, etc.)
    # has a business_id column. Without this, the LLM either returns
    # cross-tenant data or no rows at all. We literally hand it the
    # filter clause so it can't forget.
    scope_rules = ""
    if business_id:
        scope_rules = (
            f"\nCRITICAL TENANT SCOPING:\n"
            f"- This user's business_id is '{business_id}'.\n"
            f"- EVERY table whose name starts with 'nexus_' has a "
            f"business_id column. You MUST add WHERE business_id = "
            f"'{business_id}' (or AND business_id = '{business_id}' "
            f"on joined tables) to every such reference, otherwise the "
            f"query returns either nothing or another tenant's data.\n"
            f"- For joins, qualify with the alias, e.g. c.business_id = "
            f"'{business_id}' AND i.business_id = '{business_id}'.\n"
        )

    prompt = f"""Write a {dialect} query to answer this question. Output ONLY the SQL in ```sql``` fences.

Rules: SELECT only, use aliases, LIMIT 50, ROUND monetary values, ORDER BY meaningfully.
{dialect_rules}
{scope_rules}
COMMON TABLE HINTS (use these names verbatim, they exist):
- nexus_contacts  (id, first_name, last_name, email, phone, business_id, ...)
- nexus_companies (id, name, industry, website, business_id, ...)
- nexus_deals     (id, name, stage, value, contact_id, business_id, ...)
- nexus_invoices  (id, number, status, total, contact_id, company_id, issue_date, business_id, ...)
- nexus_tasks     (id, title, status, due_date, contact_id, business_id, ...)
- nexus_interactions (id, type, subject, summary, contact_id, business_id, created_at, ...)
Customer = contact (in nexus_contacts). Revenue = SUM(nexus_invoices.total).

SCHEMA:
{schema}

QUESTION: {question}

```sql"""

    try:
        # Schema and question can reference internal tables — keep local.
        response = llm_invoke(prompt, max_tokens=512, sensitive=True)
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
