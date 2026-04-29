"""
Per-record activity feed — one timeline per CRM contact / company / deal /
invoice showing everything the system did that touched it.

Pulls from four sources and merges by timestamp, newest-first:

    * nexus_tag_assignments  — "tag X added"
    * nexus_tasks            — "task Y created / completed"
    * nexus_invoices         — "invoice N issued / paid"
    * nexus_audit_log        — tool calls that mention the entity in args

Events are shaped consistently:
    {
      kind:        'tag_added' | 'task_created' | 'task_completed'
                   | 'invoice_created' | 'invoice_paid' | 'tool_call',
      ts:          ISO timestamp,
      title:       short line rendered in the timeline,
      detail:      optional longer context,
      meta:        free-form (tag color, status, amounts, ...)
    }

Callers: `/api/activity/{entity_type}/{entity_id}` — server.py.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List

from loguru import logger

from config.settings import DB_PATH

# Which tables we inspect for each entity type. Each entry is
# (table, columns_that_reference_the_entity).
_REF_COLUMNS: Dict[str, Dict[str, List[str]]] = {
    "contact": {
        "nexus_tasks":    ["contact_id"],
        "nexus_invoices": ["customer_contact_id"],
    },
    "company": {
        "nexus_tasks":    ["company_id"],
        "nexus_invoices": ["customer_company_id"],
        # Contacts don't emit events themselves but their company binding counts
        # as 'added to this company'.
        "nexus_contacts": ["company_id"],
    },
    "deal": {
        "nexus_tasks": ["deal_id"],
    },
    "invoice": {
        # invoice events are on the invoice row itself — see `_invoice_self`
    },
}

VALID_ENTITY_TYPES = {"contact", "company", "deal", "invoice"}


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_fetch(conn: sqlite3.Connection, sql: str, params: tuple) -> List[sqlite3.Row]:
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.Error as e:
        logger.debug(f"[ActivityFeed] query failed ({e}): {sql}")
        return []


def _tag_events(conn, business_id: str, entity_type: str, entity_id: str) -> List[Dict]:
    rows = _safe_fetch(conn, """
        SELECT a.created_at, t.name, t.color
          FROM nexus_tag_assignments a
          JOIN nexus_tags t ON t.id = a.tag_id
         WHERE t.business_id = ?
           AND a.entity_type = ?
           AND a.entity_id = ?
         ORDER BY a.created_at DESC
    """, (business_id, entity_type, entity_id))
    return [{
        "kind":   "tag_added",
        "ts":     r["created_at"],
        "title":  f"Tagged #{r['name']}",
        "meta":   {"color": r["color"]},
    } for r in rows]


def _task_events(conn, business_id: str, entity_type: str, entity_id: str) -> List[Dict]:
    cols = _REF_COLUMNS.get(entity_type, {}).get("nexus_tasks", [])
    events: List[Dict] = []
    for col in cols:
        rows = _safe_fetch(conn, f"""
            SELECT id, title, status, created_at, completed_at, priority
              FROM nexus_tasks
             WHERE business_id = ? AND {col} = ?
        """, (business_id, entity_id))
        for r in rows:
            events.append({
                "kind":  "task_created",
                "ts":    r["created_at"],
                "title": f"Task created: {r['title']}",
                "meta":  {"task_id": r["id"], "priority": r["priority"], "status": r["status"]},
            })
            if r["completed_at"]:
                events.append({
                    "kind":   "task_completed",
                    "ts":     r["completed_at"],
                    "title":  f"Task completed: {r['title']}",
                    "meta":   {"task_id": r["id"]},
                })
    return events


def _invoice_events(conn, business_id: str, entity_type: str, entity_id: str) -> List[Dict]:
    events: List[Dict] = []

    if entity_type == "invoice":
        rows = _safe_fetch(conn, """
            SELECT id, number, status, customer_name, total, currency,
                   created_at, paid_at
              FROM nexus_invoices
             WHERE business_id = ? AND id = ?
        """, (business_id, entity_id))
    else:
        cols = _REF_COLUMNS.get(entity_type, {}).get("nexus_invoices", [])
        rows = []
        for col in cols:
            rows.extend(_safe_fetch(conn, f"""
                SELECT id, number, status, customer_name, total, currency,
                       created_at, paid_at
                  FROM nexus_invoices
                 WHERE business_id = ? AND {col} = ?
            """, (business_id, entity_id)))

    for r in rows:
        events.append({
            "kind":   "invoice_created",
            "ts":     r["created_at"],
            "title":  f"Invoice {r['number']} drafted · {r['currency']} {r['total']:.2f}",
            "meta":   {"invoice_id": r["id"], "status": r["status"]},
        })
        if r["paid_at"]:
            events.append({
                "kind":  "invoice_paid",
                "ts":    r["paid_at"],
                "title": f"Invoice {r['number']} paid",
                "meta":  {"invoice_id": r["id"], "amount": r["total"], "currency": r["currency"]},
            })
    return events


def _contact_company_events(conn, business_id: str, company_id: str) -> List[Dict]:
    """For a company, surface contacts being linked/unlinked."""
    rows = _safe_fetch(conn, """
        SELECT id, first_name, last_name, created_at
          FROM nexus_contacts
         WHERE business_id = ? AND company_id = ?
    """, (business_id, company_id))
    return [{
        "kind":   "contact_linked",
        "ts":     r["created_at"],
        "title":  f"Contact added: {(r['first_name'] or '').strip()} {(r['last_name'] or '').strip()}".rstrip(),
        "meta":   {"contact_id": r["id"]},
    } for r in rows]


def _audit_events(conn, business_id: str, entity_id: str) -> List[Dict]:
    """
    Grep the audit log for rows whose input_summary mentions the entity id.
    Coarse on purpose — a deeper join per-tool is a future refinement.
    """
    like = f"%{entity_id}%"
    rows = _safe_fetch(conn, """
        SELECT timestamp, event_type, tool_name, input_summary, output_summary, success
          FROM nexus_audit_log
         WHERE business_id = ?
           AND (input_summary LIKE ? OR output_summary LIKE ?)
         ORDER BY timestamp DESC
         LIMIT 40
    """, (business_id, like, like))
    return [{
        "kind":   "tool_call",
        "ts":     r["timestamp"],
        "title":  f"{r['tool_name']} — {r['event_type']}",
        "detail": (r["input_summary"] or "")[:200],
        "meta":   {"success": bool(r["success"])},
    } for r in rows]


# ── Public API ──────────────────────────────────────────────────────────────
def timeline(business_id: str, entity_type: str, entity_id: str,
             limit: int = 200) -> List[Dict]:
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(f"Unknown entity_type '{entity_type}'")
    conn = _conn()
    events: List[Dict] = []
    try:
        events.extend(_tag_events(conn, business_id, entity_type, entity_id))
        events.extend(_task_events(conn, business_id, entity_type, entity_id))
        events.extend(_invoice_events(conn, business_id, entity_type, entity_id))
        if entity_type == "company":
            events.extend(_contact_company_events(conn, business_id, entity_id))
        events.extend(_audit_events(conn, business_id, entity_id))
    finally:
        conn.close()
    # Drop events with no timestamp, then sort newest-first
    events = [e for e in events if e.get("ts")]
    events.sort(key=lambda e: e["ts"], reverse=True)
    return events[:limit]
