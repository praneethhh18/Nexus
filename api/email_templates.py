"""Email templates — reusable subject/body presets with {{variable}} substitution.

A user/business defines a template once (e.g. "invoice_reminder") and the
agent or operator fills in {{first_name}} / {{amount}} / {{due_date}} per
recipient at send time. Used by:
    - The agent's `send_email_from_template` tool (bulk-send + per-contact
      outreach without re-drafting copy each run).
    - The Email Templates UI page (CRUD).

Storage: `nexus_email_templates`, one row per template, scoped by business_id.
Variable extraction: any token matching {{name}} in the subject/body is auto-
collected at create/update time so the UI can render input fields and the
agent can validate at send time.
"""
from __future__ import annotations

import json
import re
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from config.db import get_conn
from utils.timez import now_iso

TABLE = "nexus_email_templates"

# Match {{var_name}} or {{ var_name }} placeholders. Names are alnum + underscore.
_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id          TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            name        TEXT NOT NULL,
            subject     TEXT NOT NULL,
            body        TEXT NOT NULL,
            variables   TEXT NOT NULL DEFAULT '[]',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            created_by  TEXT
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_biz ON {TABLE}(business_id, name)"
    )
    conn.commit()
    return conn


def _row_to_dict(row) -> Dict[str, Any]:
    d = dict(row)
    try:
        d["variables"] = json.loads(d.get("variables") or "[]")
    except Exception:
        d["variables"] = []
    return d


def _extract_variables(subject: str, body: str) -> List[str]:
    """Collect distinct {{var}} tokens from subject + body, in first-seen order."""
    seen: List[str] = []
    for source in (subject or "", body or ""):
        for m in _VAR_RE.finditer(source):
            v = m.group(1)
            if v not in seen:
                seen.append(v)
    return seen


def _validate(name: str, subject: str, body: str) -> None:
    if not name or not name.strip():
        raise ValueError("name is required")
    if len(name) > 80:
        raise ValueError("name too long (max 80 chars)")
    if not subject or not subject.strip():
        raise ValueError("subject is required")
    if len(subject) > 200:
        raise ValueError("subject too long (max 200 chars)")
    if not body or not body.strip():
        raise ValueError("body is required")
    if len(body) > 10000:
        raise ValueError("body too long (max 10000 chars)")


# ── CRUD ────────────────────────────────────────────────────────────────────
def create_template(business_id: str, user_id: str, data: Dict[str, Any]) -> Dict:
    name    = (data.get("name") or "").strip()
    subject = (data.get("subject") or "").strip()
    body    = (data.get("body") or "").strip()
    _validate(name, subject, body)

    variables = _extract_variables(subject, body)
    tid = f"et-{uuid.uuid4().hex[:10]}"
    now = now_iso()
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {TABLE} (id, business_id, name, subject, body, variables, "
            f"created_at, updated_at, created_by) VALUES (?,?,?,?,?,?,?,?,?)",
            (tid, business_id, name, subject, body, json.dumps(variables),
             now, now, user_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_template(business_id, tid)


def get_template(business_id: str, template_id: str) -> Dict:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE id = ? AND business_id = ?",
            (template_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        # Same 404 for "doesn't exist" + "exists in another tenant" — don't
        # leak which tenant owns an id.
        raise HTTPException(404, f"Email template not found: {template_id}")
    return _row_to_dict(row)


def list_templates(business_id: str) -> List[Dict]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ? ORDER BY name ASC",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(r) for r in rows]


def update_template(business_id: str, template_id: str,
                     updates: Dict[str, Any]) -> Dict:
    existing = get_template(business_id, template_id)  # 404 + scope check
    name    = (updates.get("name", existing["name"]) or "").strip()
    subject = (updates.get("subject", existing["subject"]) or "").strip()
    body    = (updates.get("body", existing["body"]) or "").strip()
    _validate(name, subject, body)

    variables = _extract_variables(subject, body)
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET name = ?, subject = ?, body = ?, "
            f"variables = ?, updated_at = ? WHERE id = ? AND business_id = ?",
            (name, subject, body, json.dumps(variables), now_iso(),
             template_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_template(business_id, template_id)


def delete_template(business_id: str, template_id: str) -> None:
    conn = _conn()
    try:
        cur = conn.execute(
            f"DELETE FROM {TABLE} WHERE id = ? AND business_id = ?",
            (template_id, business_id),
        )
        deleted = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    if deleted == 0:
        raise HTTPException(404, f"Email template not found: {template_id}")


# ── Rendering ───────────────────────────────────────────────────────────────
def render_template(business_id: str, template_id: str,
                     variables: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Substitute {{var}} tokens in the template with provided values.

    Missing variables are left as-is (so the user sees what's still unfilled
    rather than an empty string they might miss). Returns {"subject", "body"}.
    """
    tpl = get_template(business_id, template_id)
    vars_ = variables or {}

    def _sub(text: str) -> str:
        def repl(m: re.Match) -> str:
            key = m.group(1)
            v = vars_.get(key)
            return str(v) if v is not None else m.group(0)
        return _VAR_RE.sub(repl, text)

    return {
        "subject": _sub(tpl["subject"]),
        "body":    _sub(tpl["body"]),
    }


def list_required_variables(business_id: str, template_id: str) -> List[str]:
    """Return the variable names a caller must (or should) provide. Convenience
    helper used by the agent tool when the LLM needs to know what to fill."""
    return get_template(business_id, template_id).get("variables", [])
