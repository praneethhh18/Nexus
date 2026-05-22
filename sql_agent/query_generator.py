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


def _focused_business_schema() -> str:
    """A hand-curated schema describing the 6 business tables a report
    or chat query is realistically going to touch. The full 78-table
    dump is ~80 KB and confuses the LLM into hallucinating column
    names like 'contact_id' on invoices (the real column is
    'customer_contact_id'). This shorter, accurate cheat-sheet keeps
    SQL generation on rails."""
    return """TABLE nexus_contacts (a CUSTOMER / lead / person)
  id (text PK), business_id (text), first_name, last_name, email, phone,
  title, company_name, source, lifecycle_stage, owner_id, created_at

TABLE nexus_companies (an ACCOUNT / company / org)
  id (text PK), business_id, name, industry, website, owner_id, created_at

TABLE nexus_deals (a sales opportunity)
  id (text PK), business_id, name, stage, value (numeric), currency,
  contact_id (FK to nexus_contacts.id), company_id (FK to nexus_companies.id),
  expected_close_date, created_at

TABLE nexus_invoices (a billing record)
  id (text PK), business_id, number, status (draft|sent|paid|overdue),
  customer_contact_id (FK to nexus_contacts.id, OFTEN NULL),
  customer_company_id (FK to nexus_companies.id, OFTEN NULL),
  customer_name (text, ALWAYS populated, denormalized customer label),
  currency, issue_date, due_date, paid_at,
  subtotal, tax_amount, total (numeric) -- the line-item total per invoice,
  line_items (text, JSON)
  IMPORTANT: To group invoices by customer, use customer_name directly --
  do NOT join to nexus_contacts (customer_contact_id is usually NULL on
  B2B invoices). customer_name is the source of truth on the invoice row.

TABLE nexus_tasks (a todo)
  id (text PK), business_id, title, description, status (open|in_progress|done|cancelled),
  priority, due_date, contact_id, company_id, deal_id, assignee_id, created_at

TABLE nexus_interactions (a logged touchpoint: email/call/meeting/note)
  id (text PK), business_id, type, subject, summary, contact_id, company_id,
  deal_id, created_at, created_by

USEFUL SHORTHAND:
- "customer" = a row in nexus_contacts. Their "name" = first_name || ' ' || last_name (or use nexus_invoices.customer_name for invoice-side labelling).
- "revenue", "billed amount", "total invoiced" = SUM(nexus_invoices.total).
- "won revenue" = SUM(nexus_deals.value) WHERE stage = 'won'.
- "top N customers by revenue / by invoice amount / by spend" = SELECT customer_name, SUM(total) AS total FROM nexus_invoices WHERE business_id = '...' GROUP BY customer_name ORDER BY total DESC LIMIT N. (No join needed.) Do NOT filter by status unless the user explicitly says 'paid only', 'overdue', etc., because draft/sent invoices still count toward 'invoice amount' totals.
"""


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

    # Prefer the curated 6-table cheat-sheet over the 80 KB dump for
    # business questions. The full schema is only used if the caller
    # explicitly passes one (e.g. the dev SQL editor).
    if schema is None:
        schema = _focused_business_schema()

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
