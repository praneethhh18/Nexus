"""
Saved queries + reusable query templates for the SQL agent.

Saved queries are user-authored — give a natural-language question a name
so it can be re-run with one click. Templates are shipped with the product
— "revenue by month", "top customers", "overdue invoices" etc — and get
materialised as saved queries when the user clicks Clone.

Stored in `nexus_saved_queries` per business. The generated SQL is cached
alongside the NL question so re-runs skip re-generation unless the user
asks for a rewrite.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Dict, List

from fastapi import HTTPException

from config.settings import DB_PATH
from utils.timez import now_iso

TABLE = "nexus_saved_queries"


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id              TEXT PRIMARY KEY,
            business_id     TEXT NOT NULL,
            name            TEXT NOT NULL,
            question        TEXT NOT NULL,
            generated_sql   TEXT,
            description     TEXT DEFAULT '',
            chart_type      TEXT DEFAULT 'auto',
            template_key    TEXT,
            created_at      TEXT NOT NULL,
            last_run_at     TEXT,
            run_count       INTEGER DEFAULT 0,
            UNIQUE (business_id, name COLLATE NOCASE)
        )
    """)
    conn.commit()
    return conn


def _validate_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Query name cannot be empty")
    if len(name) > 80:
        raise ValueError("Query name too long (max 80 chars)")
    return name


VALID_CHART_TYPES = ("auto", "bar", "line", "pie", "table", "none")


# ── CRUD ────────────────────────────────────────────────────────────────────
def list_queries(business_id: str) -> List[Dict]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ? "
            f"ORDER BY last_run_at DESC NULLS LAST, created_at DESC",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def create_query(business_id: str, data: Dict) -> Dict:
    name = _validate_name(data.get("name", ""))
    question = (data.get("question") or "").strip()
    if not question:
        raise ValueError("Query question is required")
    if len(question) > 2000:
        raise ValueError("Query question too long (max 2000 chars)")
    chart = (data.get("chart_type") or "auto").lower()
    if chart not in VALID_CHART_TYPES:
        raise ValueError(f"Invalid chart_type. Must be one of: {', '.join(VALID_CHART_TYPES)}")

    qid = f"sq-{uuid.uuid4().hex[:10]}"
    now = now_iso()
    conn = _conn()
    try:
        try:
            conn.execute(
                f"INSERT INTO {TABLE} (id, business_id, name, question, generated_sql, "
                f"description, chart_type, template_key, created_at) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (qid, business_id, name, question,
                 data.get("generated_sql") or None,
                 (data.get("description") or "")[:500],
                 chart, data.get("template_key"),
                 now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"A saved query named '{name}' already exists")
    finally:
        conn.close()
    return get_query(business_id, qid)


def get_query(business_id: str, query_id: str) -> Dict:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE id = ? AND business_id = ?",
            (query_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        # 404 covers both "doesn't exist" and "exists in another tenant" so
        # the API never reveals cross-tenant id ownership.
        raise HTTPException(404, "Saved query not found")
    return dict(row)


def update_query(business_id: str, query_id: str, updates: Dict) -> Dict:
    get_query(business_id, query_id)
    fields: Dict = {}
    if "name" in updates:
        fields["name"] = _validate_name(updates["name"])
    if "question" in updates:
        q = (updates["question"] or "").strip()
        if not q:
            raise ValueError("Query question cannot be empty")
        fields["question"] = q[:2000]
    if "description" in updates:
        fields["description"] = (updates["description"] or "")[:500]
    if "chart_type" in updates:
        ct = (updates["chart_type"] or "auto").lower()
        if ct not in VALID_CHART_TYPES:
            raise ValueError("Invalid chart_type")
        fields["chart_type"] = ct
    if "generated_sql" in updates:
        fields["generated_sql"] = updates["generated_sql"]
    if not fields:
        return get_query(business_id, query_id)

    sets = ", ".join(f"{k} = ?" for k in fields.keys())
    params = list(fields.values()) + [query_id, business_id]
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET {sets} WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()
    return get_query(business_id, query_id)


def delete_query(business_id: str, query_id: str) -> None:
    conn = _conn()
    try:
        cur = conn.execute(
            f"DELETE FROM {TABLE} WHERE id = ? AND business_id = ?",
            (query_id, business_id),
        )
        deleted = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    if deleted == 0:
        # Same 404 as get/update so cross-tenant ownership stays opaque.
        raise HTTPException(404, "Saved query not found")


def record_run(business_id: str, query_id: str) -> None:
    """Bump run_count + last_run_at. Called by the SQL executor."""
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET run_count = run_count + 1, last_run_at = ? "
            f"WHERE id = ? AND business_id = ?",
            (now_iso(), query_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()


# ── Templates ───────────────────────────────────────────────────────────────
# Curated starter queries. Users clone one and get a saved query they can
# rename / edit / run. The NL question is deliberately generic so it works
# without knowing the exact schema — the NL→SQL agent figures it out.
TEMPLATES: List[Dict] = [
    {
        "key":         "revenue_by_month",
        "name":        "Revenue by month",
        "question":    "Show total revenue from paid invoices grouped by month for the last 12 months.",
        "description": "Time-series of paid invoice totals, grouped by month.",
        "chart_type":  "line",
    },
    {
        "key":         "top_customers",
        "name":        "Top customers",
        "question":    "Show the top 10 customers by total invoiced amount.",
        "description": "Biggest accounts by lifetime invoice volume.",
        "chart_type":  "bar",
    },
    {
        "key":         "overdue_invoices",
        "name":        "Overdue invoices",
        "question":    "List all invoices with status 'sent' whose due_date is before today, ordered oldest first.",
        "description": "Everything Kira would chase today.",
        "chart_type":  "table",
    },
    {
        "key":         "open_tasks_by_assignee",
        "name":        "Open tasks by assignee",
        "question":    "Count of open and in_progress tasks grouped by assignee_id.",
        "description": "Who has the most on their plate right now.",
        "chart_type":  "bar",
    },
    {
        "key":         "pipeline_by_stage",
        "name":        "Pipeline by stage",
        "question":    "Sum of deal values grouped by stage.",
        "description": "Pipeline health snapshot.",
        "chart_type":  "bar",
    },
    {
        "key":         "contacts_by_company",
        "name":        "Contacts by company",
        "question":    "Count of contacts per company name, top 10.",
        "description": "Which companies you're most connected into.",
        "chart_type":  "bar",
    },
]


def list_templates() -> List[Dict]:
    return list(TEMPLATES)


def create_from_template(business_id: str, template_key: str) -> Dict:
    tpl = next((t for t in TEMPLATES if t["key"] == template_key), None)
    if not tpl:
        raise ValueError(f"Unknown template: {template_key}")
    data = dict(tpl)
    data["template_key"] = template_key
    return create_query(business_id, data)
