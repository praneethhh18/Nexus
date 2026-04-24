"""
Database index pass — additive, idempotent migrations that add composite
indexes on columns list/filter queries hit all day long.

Called at server boot. Each index is CREATE INDEX IF NOT EXISTS so it's
safe to run every restart. Works on any existing database — it only reads
PRAGMA table_info to decide which indexes apply.

Indexes are keyed by the common query patterns:
  * business_id + some filter column (tenant-scoped list views)
  * business_id + date column (activity history, timelines)
  * foreign keys that aren't already indexed by their declaring table
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Tuple

from loguru import logger

from config.settings import DB_PATH


# Each entry: (index_name, table, column_list)
# Only applied if the table and every column exist.
_INDEXES: List[Tuple[str, str, List[str]]] = [
    # Core CRM
    ("idx_contacts_biz_email",  "nexus_contacts", ["business_id", "email"]),
    ("idx_contacts_biz_created", "nexus_contacts", ["business_id", "created_at"]),
    ("idx_companies_biz_industry", "nexus_companies", ["business_id", "industry"]),
    ("idx_deals_biz_stage",     "nexus_deals", ["business_id", "stage", "updated_at"]),
    ("idx_deals_biz_contact",   "nexus_deals", ["business_id", "contact_id"]),
    ("idx_deals_biz_company",   "nexus_deals", ["business_id", "company_id"]),

    # Tasks (list by status + due, by assignee, by deal/contact/company)
    ("idx_tasks_biz_status_due", "nexus_tasks", ["business_id", "status", "due_date"]),
    ("idx_tasks_biz_assignee",  "nexus_tasks", ["business_id", "assignee_id"]),
    ("idx_tasks_biz_contact",   "nexus_tasks", ["business_id", "contact_id"]),
    ("idx_tasks_biz_recur",     "nexus_tasks", ["business_id", "recurrence", "recurrence_parent_id"]),

    # Invoices (by status, by customer, by due date)
    ("idx_invoices_biz_status_due", "nexus_invoices", ["business_id", "status", "due_date"]),
    ("idx_invoices_biz_contact", "nexus_invoices", ["business_id", "customer_contact_id"]),
    ("idx_invoices_biz_company", "nexus_invoices", ["business_id", "customer_company_id"]),

    # Conversations / messages
    ("idx_conv_biz_updated",    "nexus_conversations", ["business_id", "updated_at"]),
    ("idx_messages_conv_ts",    "nexus_messages", ["conversation_id", "timestamp"]),

    # Audit log — timeline queries hammer (business_id, timestamp)
    ("idx_audit_biz_ts",        "nexus_audit_log", ["business_id", "timestamp"]),
    ("idx_audit_biz_tool",      "nexus_audit_log", ["business_id", "tool_name"]),

    # Notifications
    ("idx_notif_biz_read",      "nexus_notifications", ["business_id", "read", "created_at"]),

    # Agent runs (agents page queries by business + agent_key + time)
    ("idx_runs_biz_agent_ts",   "nexus_agent_runs", ["business_id", "agent_key", "started_at"]),
    ("idx_runs_biz_status",     "nexus_agent_runs", ["business_id", "status"]),

    # Documents
    ("idx_docs_biz_collection", "nexus_documents", ["business_id", "collection_id"]),
    ("idx_docs_biz_expires",    "nexus_documents", ["business_id", "expires_at"]),

    # Tag lookup — the (entity_type, entity_id) index already exists; add one
    # for (tag_id) because "list docs tagged X" queries use it directly.
    ("idx_tag_assign_tag",      "nexus_tag_assignments", ["tag_id"]),

    # Integrations (dash + webhook lookup)
    ("idx_integrations_biz_provider", "nexus_integrations", ["business_id", "provider"]),

    # Suggestions dismissals (fast existence check)
    ("idx_suggestion_dismiss_biz", "nexus_suggestion_dismissals", ["business_id", "suggestion_id"]),

    # Query history / saved queries
    ("idx_query_hist_biz_ts",   "nexus_query_history", ["business_id", "timestamp"]),
    ("idx_saved_q_biz_last_run", "nexus_saved_queries", ["business_id", "last_run_at"]),
]


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    r = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (name,),
    ).fetchone()
    return r is not None


def _columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def apply_indexes() -> dict:
    """
    Apply every index whose table + columns are present. Returns a summary
    dict {applied: N, skipped: M, errors: [(idx_name, err)]}.
    """
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    applied, skipped, errors = 0, 0, []
    try:
        for idx_name, table, cols in _INDEXES:
            if not _table_exists(conn, table):
                skipped += 1
                continue
            existing_cols = _columns(conn, table)
            if not all(c in existing_cols for c in cols):
                skipped += 1
                continue
            try:
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} "
                    f"ON {table}({', '.join(cols)})"
                )
                applied += 1
            except Exception as e:
                errors.append((idx_name, str(e)))
        # ANALYZE helps SQLite pick these indexes when the tables are small.
        try:
            conn.execute("ANALYZE")
        except Exception:
            pass
        conn.commit()
    finally:
        conn.close()
    result = {"applied": applied, "skipped": skipped, "errors": errors}
    logger.info(f"[db_indexes] {result}")
    return result
