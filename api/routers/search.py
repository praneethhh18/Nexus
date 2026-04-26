"""
Global search — Ctrl+K omnibox. Searches across contacts, companies, deals,
tasks, invoices, documents, memory, and recent conversations. Everything
business-scoped. Returns grouped results for fast keyboard navigation.
"""
from __future__ import annotations

import sqlite3 as _sq

from fastapi import APIRouter, Depends

from api.auth import get_current_context
from config.settings import DB_PATH

router = APIRouter(tags=["search"])


@router.get("/api/search")
def global_search(q: str, limit: int = 8,
                  ctx: dict = Depends(get_current_context)):
    q = (q or "").strip()
    if len(q) < 2:
        return {"groups": []}
    limit = max(1, min(limit, 20))
    like = f"%{q}%"
    biz = ctx["business_id"]

    conn = _sq.connect(DB_PATH)
    conn.row_factory = _sq.Row
    groups: list = []

    def _g(kind, rows, key_fields, route_fn):
        items = []
        for r in rows:
            d = dict(r)
            items.append({
                "id": d.get("id") or d.get(key_fields[0]),
                "title": " ".join(str(d.get(k) or "") for k in key_fields if d.get(k)).strip() or "(untitled)",
                "subtitle": d.get("email") or d.get("company_name") or d.get("stage") or d.get("status") or "",
                "route": route_fn(d),
                "kind": kind,
            })
        if items:
            groups.append({"kind": kind, "items": items})

    try:
        # Contacts
        rows = conn.execute(
            "SELECT id, first_name, last_name, email, phone, title "
            "FROM nexus_contacts WHERE business_id = ? "
            "AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ? OR tags LIKE ?) "
            "LIMIT ?",
            (biz, like, like, like, like, limit),
        ).fetchall()
        _g("contact", rows, ["first_name", "last_name"], lambda d: "/crm")

        # Companies
        rows = conn.execute(
            "SELECT id, name, industry, website FROM nexus_companies "
            "WHERE business_id = ? AND (name LIKE ? OR industry LIKE ? OR tags LIKE ?) LIMIT ?",
            (biz, like, like, like, limit),
        ).fetchall()
        _g("company", rows, ["name"], lambda d: "/crm")

        # Deals
        rows = conn.execute(
            "SELECT id, name, stage, value, currency FROM nexus_deals "
            "WHERE business_id = ? AND (name LIKE ? OR notes LIKE ?) LIMIT ?",
            (biz, like, like, limit),
        ).fetchall()
        _g("deal", rows, ["name"], lambda d: "/crm")

        # Tasks
        rows = conn.execute(
            "SELECT id, title, status, priority, due_date FROM nexus_tasks "
            "WHERE business_id = ? AND (title LIKE ? OR description LIKE ? OR tags LIKE ?) LIMIT ?",
            (biz, like, like, like, limit),
        ).fetchall()
        _g("task", rows, ["title"], lambda d: "/tasks")

        # Invoices
        rows = conn.execute(
            "SELECT id, number, customer_name, status, total, currency FROM nexus_invoices "
            "WHERE business_id = ? AND (number LIKE ? OR customer_name LIKE ? OR customer_email LIKE ?) LIMIT ?",
            (biz, like, like, like, limit),
        ).fetchall()
        _g("invoice", rows, ["number", "customer_name"], lambda d: "/invoices")

        # Documents
        try:
            rows = conn.execute(
                "SELECT id, title, template_key, format FROM nexus_documents "
                "WHERE business_id = ? AND title LIKE ? LIMIT ?",
                (biz, like, limit),
            ).fetchall()
            _g("document", rows, ["title"], lambda d: "/documents")
        except _sq.OperationalError:
            pass

        # Memory
        try:
            rows = conn.execute(
                "SELECT id, content, kind FROM nexus_business_memory "
                "WHERE business_id = ? AND content LIKE ? LIMIT ?",
                (biz, like, limit),
            ).fetchall()
            items = [{
                "id": r["id"],
                "title": (r["content"] or "")[:80],
                "subtitle": r["kind"] or "",
                "route": "/memory",
                "kind": "memory",
            } for r in rows]
            if items:
                groups.append({"kind": "memory", "items": items})
        except _sq.OperationalError:
            pass

        # Recent conversations (title match)
        rows = conn.execute(
            "SELECT conversation_id, title, updated_at FROM nexus_conversations "
            "WHERE business_id = ? AND title LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (biz, like, limit),
        ).fetchall()
        items = [{
            "id": r["conversation_id"],
            "title": r["title"] or "(untitled chat)",
            "subtitle": (r["updated_at"] or "")[:16],
            "route": f"/chat?conv={r['conversation_id']}",
            "kind": "conversation",
        } for r in rows]
        if items:
            groups.append({"kind": "conversation", "items": items})

    finally:
        conn.close()

    return {"groups": groups, "query": q}
