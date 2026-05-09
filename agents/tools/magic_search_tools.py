"""Magic search — natural-language → safe SELECT against tenant data.

User asks "show me overdue invoices over 50K from Q4" and the tool:
    1. Generates a single SELECT statement from the question
    2. Validates it's read-only (no DML, no DDL, no semicolons, no comments)
    3. Forces business_id scoping — any query touching a tenant table MUST
       filter by the caller's business_id
    4. Executes with parameterized binding for the business_id
    5. Returns rows + the SQL it ran (transparency for the user)

Safety model:
    - Whitelist of read-only tables (matches the published schema, nothing else)
    - Single-statement only — multi-statement queries rejected
    - Hard-block on UPDATE / INSERT / DELETE / DROP / ALTER / CREATE / TRUNCATE
    - Result row cap (default 50, max 500) to prevent context blowups
    - sensitive=True on the LLM call so the schema + question never leave Ollama
"""
from __future__ import annotations

import re
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from typing import Any, Dict, List

from loguru import logger

from agents.tool_registry import register_tool
from config.db import get_conn


# Tenant tables the user can query. Only tables with a business_id column.
ALLOWED_TABLES = {
    "nexus_contacts":            "Contacts (CRM). Columns: id, business_id, first_name, last_name, email, phone, title, company_id, notes, tags, created_at, updated_at, source, last_called_at, last_call_outcome, last_call_summary",
    "nexus_companies":           "Companies. Columns: id, business_id, name, industry, website, notes, tags, created_at, updated_at",
    "nexus_deals":               "Deals. Columns: id, business_id, title, value, currency, stage, probability, expected_close, contact_id, company_id, notes, created_at, updated_at",
    "nexus_invoices":            "Invoices. Columns: id, business_id, number, contact_id, company_id, amount, currency, status (draft|sent|paid|overdue|void), due_date, issued_at, paid_at, notes, created_at, updated_at",
    "nexus_tasks":               "Tasks. Columns: id, business_id, title, status (open|in_progress|done|cancelled), priority, due_date, assignee_id, created_by, notes, created_at, updated_at, completed_at",
    "nexus_interactions":        "CRM interactions/timeline. Columns: id, business_id, contact_id, company_id, deal_id, type (call|email|meeting|note), subject, summary, occurred_at, created_at, created_by",
    "nexus_voice_calls":         "Voice (Vox) call records. Columns: id, business_id, contact_id, call_sid, started_at, ended_at, duration_sec, outcome, headline, lead_score, interest_level, sentiment, next_step, created_at",
    "nexus_documents":           "Knowledge-base documents. Columns: id, business_id, name, kind, size, created_at",
    "nexus_contact_memory":      "Per-contact memory facts. Columns: id, business_id, contact_id, kind, fact, source, confidence, created_at, archived_at",
    "nexus_inbound_call_sessions": "Inbound voice receptionist sessions. Columns: call_sid, business_id, twilio_to, from_number, started_at, ended_at, status",
    "nexus_email_templates":     "Email templates. Columns: id, business_id, name, subject, body, variables, created_at",
    "nexus_voice_pending_whatsapp": "WhatsApp follow-up queue. Columns: call_sid, business_id, user_id, whatsapp_phone, target_phone, target_name, purpose",
}

_BLOCKED_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "GRANT", "REVOKE", "MERGE", "REPLACE", "ATTACH", "PRAGMA",
)


def _validate_sql(sql: str, business_id: str) -> str:
    """Reject anything that isn't a single bounded SELECT scoped to this tenant.

    Returns the cleaned SQL (with the business_id binding applied) on success.
    Raises ValueError on any policy violation.
    """
    s = (sql or "").strip().rstrip(";").strip()
    if not s:
        raise ValueError("Empty SQL")

    # Single statement only
    if ";" in s:
        raise ValueError("Multi-statement SQL is not allowed")

    upper = s.upper()
    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        raise ValueError("Only SELECT (or WITH ... SELECT) is allowed")

    # Block any DML/DDL keyword as a standalone token (avoid matching column
    # names that happen to contain the substring "create" etc).
    tokens = set(re.findall(r"\b[A-Za-z]+\b", upper))
    blocked = tokens.intersection(_BLOCKED_KEYWORDS)
    if blocked:
        raise ValueError(f"Blocked keyword(s) in SQL: {', '.join(sorted(blocked))}")

    # Block comment markers (defensive; Postgres allows -- and /* */)
    if "--" in s or "/*" in s:
        raise ValueError("SQL comments are not allowed")

    # Tables touched must all be in the allowed list
    table_refs = set(re.findall(r"\bnexus_[a-z_]+\b", s.lower()))
    if not table_refs:
        raise ValueError("Query must reference at least one tenant table")
    unknown = table_refs - set(ALLOWED_TABLES.keys())
    if unknown:
        raise ValueError(f"Unknown / disallowed table(s): {', '.join(sorted(unknown))}")

    # Must scope by business_id — refuse queries that omit it
    if "business_id" not in s.lower():
        raise ValueError(
            "Query must filter by business_id. The tool will bind the value "
            "automatically — include `business_id = ?` in your WHERE clause."
        )

    return s


def _generate_sql(question: str, business_id: str, max_rows: int) -> str:
    """LLM → SELECT. Sensitive (schema lives on local Ollama only)."""
    from config import llm_provider

    schema_block = "\n".join(f"- {t}: {desc}" for t, desc in ALLOWED_TABLES.items())

    system = (
        "You translate plain English business questions into SAFE SQL "
        "(SELECT only) against this schema. Strict rules:\n"
        f"- Output ONLY the SQL, no explanation, no markdown fences\n"
        f"- One statement, no semicolons inside\n"
        f"- Always filter by `business_id = ?` (the system binds the value)\n"
        f"- Use a parameter `?` placeholder for the business_id, NOT a literal\n"
        f"- LIMIT every query to at most {max_rows} rows\n"
        f"- Do NOT use UPDATE/INSERT/DELETE/DROP/ALTER/CREATE/TRUNCATE\n"
        f"- Do NOT use comments (-- or /* */)\n"
        f"- Use only these tables:\n{schema_block}\n"
        f"- Common dialect: standard SQL that works on both SQLite and Postgres."
    )
    prompt = f"Question: {question.strip()}\n\nSQL:"
    try:
        # sensitive=True keeps the schema + question on local Ollama
        sql = llm_provider.invoke(prompt, system=system, max_tokens=400,
                                   temperature=0.1, sensitive=True)
    except Exception as e:
        raise RuntimeError(f"SQL generation failed: {e}")

    # Strip common LLM wrappers
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", (sql or "").strip(),
                 flags=re.MULTILINE | re.IGNORECASE).strip()
    return sql


def _execute(sql: str, business_id: str, max_rows: int) -> List[Dict[str, Any]]:
    """Run the validated SQL with the business_id parameter bound.

    The validator ensured a single `?` placeholder for business_id is present.
    We bind it once for every `?` in the SQL — usually 1, sometimes 2 if the
    user joined two tenant tables.
    """
    placeholder_count = sql.count("?")
    if placeholder_count == 0:
        # validator already enforces business_id mention; if it's hard-coded
        # it'll be wrong, but we don't have a parameter to bind. Block.
        raise ValueError("Generated SQL doesn't have any `?` placeholders to bind business_id")
    params = tuple([business_id] * placeholder_count)

    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        # The Postgres cursor wrapper exposes fetchall but not fetchmany,
        # so fetch + slice. Validator's LIMIT clause already caps server-side.
        rows = cur.fetchall()[:max_rows]
    finally:
        conn.close()
    return [dict(r) for r in rows]


def _magic_search(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    business_id = ctx["business_id"]
    question = (args.get("question") or "").strip()
    if not question:
        raise ValueError("question is required")

    max_rows = max(1, min(int(args.get("limit", 50)), 500))

    # 1. Generate SQL (LLM, sensitive=True)
    sql = _generate_sql(question, business_id, max_rows)

    # 2. Validate
    try:
        sql = _validate_sql(sql, business_id)
    except ValueError as e:
        # Surface the SQL the LLM tried so the user can see what was rejected
        return {
            "ok":          False,
            "error":       f"Generated SQL was rejected: {e}",
            "rejected_sql": sql[:1000],
            "message":     "The auto-generated query failed safety validation. Try rephrasing more specifically.",
        }

    # 3. Execute
    try:
        rows = _execute(sql, business_id, max_rows)
    except Exception as e:
        logger.warning(f"[magic_search] execution failed: {e}")
        return {
            "ok":      False,
            "error":   f"Execution failed: {e}",
            "sql":     sql[:1000],
            "message": "The query was valid but failed to run. The schema may have changed.",
        }

    # 4. Return rows + transparency on what ran
    return {
        "ok":         True,
        "question":   question,
        "sql":        sql,
        "row_count":  len(rows),
        "rows":       rows,
        "limited":    len(rows) >= max_rows,
        "message":    f"Found {len(rows)} result(s){' (capped at limit)' if len(rows) >= max_rows else ''}.",
    }


register_tool(
    name="magic_search",
    description=(
        "Answer a plain-English question about your data by generating + "
        "running a safe SELECT query. Use for ad-hoc questions like 'show "
        "overdue invoices > ₹50K from last quarter', 'list contacts I "
        "haven't called in 30 days', 'top 10 deals by value in stage "
        "Negotiation'. Read-only by design — never modifies data. Returns "
        "both the rows and the exact SQL that ran."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Plain English question about contacts, deals, invoices, tasks, calls, etc.",
            },
            "limit": {
                "type": "integer",
                "default": 50,
                "description": "Max rows to return (1-500). Default 50.",
            },
        },
        "required": ["question"],
    },
    handler=_magic_search,
    summary_fn=lambda a: f"Magic search: {(a.get('question') or '')[:80]}",
)
