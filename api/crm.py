"""
CRM module — contacts, companies, deals, interactions.

All records are strictly scoped to a business_id. The API layer assumes the
caller has already verified business membership (via get_current_context), so
functions here trust the business_id they receive.
"""
from __future__ import annotations

import re
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import HTTPException

from config.db import get_conn, list_columns

CONTACTS_TABLE = "nexus_contacts"
COMPANIES_TABLE = "nexus_companies"
DEALS_TABLE = "nexus_deals"
INTERACTIONS_TABLE = "nexus_interactions"

DEAL_STAGES = ("lead", "qualified", "proposal", "negotiation", "won", "lost")
INTERACTION_TYPES = ("call", "email", "meeting", "note")

DEAL_STAGE_EVENTS_TABLE = "nexus_deal_stage_events"

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _get_conn():
    conn = get_conn()
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {COMPANIES_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        name TEXT NOT NULL,
        industry TEXT DEFAULT '',
        website TEXT DEFAULT '',
        size TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        created_at TEXT,
        updated_at TEXT,
        created_by TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_companies_biz ON {COMPANIES_TABLE}(business_id, name)")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {CONTACTS_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        first_name TEXT DEFAULT '',
        last_name TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        title TEXT DEFAULT '',
        company_id TEXT,
        notes TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        created_at TEXT,
        updated_at TEXT,
        created_by TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_contacts_biz ON {CONTACTS_TABLE}(business_id, last_name)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_contacts_company ON {CONTACTS_TABLE}(company_id)")

    # Additive: `source` records where this lead came from. Added later for
    # lead-gen attribution. See db/migrations/0002 + docs/AI_LEAD_GENERATION.md.
    _contact_cols = set(list_columns(conn, CONTACTS_TABLE))
    if "source" not in _contact_cols:
        conn.execute(f"ALTER TABLE {CONTACTS_TABLE} ADD COLUMN source TEXT DEFAULT 'manual'")
    # Additive: AI-driven lead scoring against the workspace ICP (migration 0003).
    if "lead_score" not in _contact_cols:
        conn.execute(f"ALTER TABLE {CONTACTS_TABLE} ADD COLUMN lead_score INTEGER")
    if "lead_score_reason" not in _contact_cols:
        conn.execute(f"ALTER TABLE {CONTACTS_TABLE} ADD COLUMN lead_score_reason TEXT DEFAULT ''")
    if "lead_scored_at" not in _contact_cols:
        conn.execute(f"ALTER TABLE {CONTACTS_TABLE} ADD COLUMN lead_scored_at TEXT")
    # Additive: BANT extraction (budget/authority/need/timing) blob.
    if "bant_signals" not in _contact_cols:
        conn.execute(f"ALTER TABLE {CONTACTS_TABLE} ADD COLUMN bant_signals TEXT DEFAULT ''")
    if "bant_extracted_at" not in _contact_cols:
        conn.execute(f"ALTER TABLE {CONTACTS_TABLE} ADD COLUMN bant_extracted_at TEXT")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {DEALS_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        name TEXT NOT NULL,
        value REAL DEFAULT 0,
        currency TEXT DEFAULT 'USD',
        stage TEXT DEFAULT 'lead',
        probability_pct INTEGER DEFAULT 20,
        contact_id TEXT,
        company_id TEXT,
        notes TEXT DEFAULT '',
        expected_close TEXT,
        created_at TEXT,
        updated_at TEXT,
        created_by TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_deals_biz ON {DEALS_TABLE}(business_id, stage)")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {INTERACTIONS_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        contact_id TEXT,
        company_id TEXT,
        deal_id TEXT,
        type TEXT DEFAULT 'note',
        subject TEXT DEFAULT '',
        summary TEXT DEFAULT '',
        occurred_at TEXT,
        created_at TEXT,
        created_by TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_interactions_biz ON {INTERACTIONS_TABLE}(business_id, occurred_at)")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {DEAL_STAGE_EVENTS_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id TEXT NOT NULL,
        deal_id TEXT NOT NULL,
        from_stage TEXT,
        to_stage TEXT NOT NULL,
        at TEXT NOT NULL
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_stage_events_biz ON {DEAL_STAGE_EVENTS_TABLE}(business_id, deal_id, at)")

    conn.commit()
    return conn


def _log_stage_event(business_id: str, deal_id: str, from_stage: Optional[str], to_stage: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {DEAL_STAGE_EVENTS_TABLE} (business_id, deal_id, from_stage, to_stage, at) "
            f"VALUES (?,?,?,?,?)",
            (business_id, deal_id, from_stage, to_stage, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def _validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if email and not _EMAIL_RE.match(email):
        raise HTTPException(400, f"Invalid email: {email}")
    return email


def _validate_text(val: str, field: str, max_len: int = 200) -> str:
    val = (val or "").strip()
    if len(val) > max_len:
        raise HTTPException(400, f"{field} too long (max {max_len} chars)")
    return val


def _now() -> str:
    return datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPANIES
# ═══════════════════════════════════════════════════════════════════════════════
def create_company(business_id: str, user_id: str, data: Dict[str, Any]) -> Dict:
    name = _validate_text(data.get("name", ""), "Company name", 200)
    if not name:
        raise HTTPException(400, "Company name is required")
    cid = f"co-{uuid.uuid4().hex[:10]}"
    row = (
        cid, business_id,
        name,
        _validate_text(data.get("industry", ""), "Industry", 80),
        _validate_text(data.get("website", ""), "Website", 250),
        _validate_text(data.get("size", ""), "Size", 40),
        _validate_text(data.get("notes", ""), "Notes", 2000),
        _validate_text(data.get("tags", ""), "Tags", 300),
        _now(), _now(), user_id,
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {COMPANIES_TABLE} "
            f"(id, business_id, name, industry, website, size, notes, tags, created_at, updated_at, created_by) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?)", row,
        )
        conn.commit()
    finally:
        conn.close()
    return get_company(business_id, cid)


def list_companies(business_id: str, search: Optional[str] = None, limit: int = 100) -> List[Dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        if search:
            rows = conn.execute(
                f"SELECT * FROM {COMPANIES_TABLE} WHERE business_id = ? AND "
                f"(name LIKE ? OR industry LIKE ? OR tags LIKE ?) "
                f"ORDER BY name ASC LIMIT ?",
                (business_id, f"%{search}%", f"%{search}%", f"%{search}%", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM {COMPANIES_TABLE} WHERE business_id = ? ORDER BY name ASC LIMIT ?",
                (business_id, limit),
            ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_company(business_id: str, company_id: str) -> Dict:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {COMPANIES_TABLE} WHERE id = ? AND business_id = ?",
            (company_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Company not found")
    return dict(row)


def update_company(business_id: str, company_id: str, updates: Dict[str, Any]) -> Dict:
    get_company(business_id, company_id)  # existence + ownership check
    allowed = {"name", "industry", "website", "size", "notes", "tags"}
    fields = {k: v for k, v in updates.items() if k in allowed and v is not None}
    if not fields:
        raise HTTPException(400, "No editable fields provided")
    if "name" in fields:
        fields["name"] = _validate_text(fields["name"], "Company name", 200)
    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [_now(), company_id, business_id]
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {COMPANIES_TABLE} SET {sets}, updated_at = ? WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()
    return get_company(business_id, company_id)


def delete_company(business_id: str, company_id: str) -> None:
    get_company(business_id, company_id)
    conn = _get_conn()
    try:
        # Detach contacts/deals rather than cascade-deleting
        conn.execute(f"UPDATE {CONTACTS_TABLE} SET company_id = NULL WHERE company_id = ? AND business_id = ?", (company_id, business_id))
        conn.execute(f"UPDATE {DEALS_TABLE} SET company_id = NULL WHERE company_id = ? AND business_id = ?", (company_id, business_id))
        conn.execute(f"DELETE FROM {COMPANIES_TABLE} WHERE id = ? AND business_id = ?", (company_id, business_id))
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTACTS
# ═══════════════════════════════════════════════════════════════════════════════
def create_contact(business_id: str, user_id: str, data: Dict[str, Any]) -> Dict:
    first = _validate_text(data.get("first_name", ""), "First name", 80)
    last = _validate_text(data.get("last_name", ""), "Last name", 80)
    if not first and not last:
        raise HTTPException(400, "At least one of first_name or last_name is required")
    email = _validate_email(data.get("email", ""))
    company_id = data.get("company_id") or None
    if company_id:
        get_company(business_id, company_id)  # verify ownership

    cid = f"ct-{uuid.uuid4().hex[:10]}"
    row = (
        cid, business_id, first, last, email,
        _validate_text(data.get("phone", ""), "Phone", 40),
        _validate_text(data.get("title", ""), "Title", 120),
        company_id,
        _validate_text(data.get("notes", ""), "Notes", 2000),
        _validate_text(data.get("tags", ""), "Tags", 300),
        _now(), _now(), user_id,
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {CONTACTS_TABLE} "
            f"(id, business_id, first_name, last_name, email, phone, title, company_id, notes, tags, created_at, updated_at, created_by) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", row,
        )
        conn.commit()
    finally:
        conn.close()
    return get_contact(business_id, cid)


def list_contacts(business_id: str, search: Optional[str] = None, company_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        sql = f"""
            SELECT c.*, co.name AS company_name
            FROM {CONTACTS_TABLE} c
            LEFT JOIN {COMPANIES_TABLE} co ON co.id = c.company_id AND co.business_id = c.business_id
            WHERE c.business_id = ?
        """
        params: list = [business_id]
        if search:
            sql += " AND (c.first_name LIKE ? OR c.last_name LIKE ? OR c.email LIKE ? OR c.tags LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s, s])
        if company_id:
            sql += " AND c.company_id = ?"
            params.append(company_id)
        sql += " ORDER BY c.last_name ASC, c.first_name ASC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_contact(business_id: str, contact_id: str) -> Dict:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"""SELECT c.*, co.name AS company_name
                FROM {CONTACTS_TABLE} c
                LEFT JOIN {COMPANIES_TABLE} co ON co.id = c.company_id AND co.business_id = c.business_id
                WHERE c.id = ? AND c.business_id = ?""",
            (contact_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Contact not found")
    return dict(row)


def update_contact(business_id: str, contact_id: str, updates: Dict[str, Any]) -> Dict:
    get_contact(business_id, contact_id)
    allowed = {"first_name", "last_name", "email", "phone", "title", "company_id", "notes", "tags"}
    fields = {k: v for k, v in updates.items() if k in allowed and v is not None}
    if not fields:
        raise HTTPException(400, "No editable fields provided")
    if "email" in fields:
        fields["email"] = _validate_email(fields["email"])
    if "company_id" in fields and fields["company_id"]:
        get_company(business_id, fields["company_id"])
    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [_now(), contact_id, business_id]
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {CONTACTS_TABLE} SET {sets}, updated_at = ? WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()
    return get_contact(business_id, contact_id)


def delete_contact(business_id: str, contact_id: str) -> None:
    get_contact(business_id, contact_id)
    conn = _get_conn()
    try:
        conn.execute(f"UPDATE {DEALS_TABLE} SET contact_id = NULL WHERE contact_id = ? AND business_id = ?", (contact_id, business_id))
        conn.execute(f"UPDATE {INTERACTIONS_TABLE} SET contact_id = NULL WHERE contact_id = ? AND business_id = ?", (contact_id, business_id))
        conn.execute(f"DELETE FROM {CONTACTS_TABLE} WHERE id = ? AND business_id = ?", (contact_id, business_id))
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  DEALS
# ═══════════════════════════════════════════════════════════════════════════════
def create_deal(business_id: str, user_id: str, data: Dict[str, Any]) -> Dict:
    name = _validate_text(data.get("name", ""), "Deal name", 200)
    if not name:
        raise HTTPException(400, "Deal name is required")

    stage = data.get("stage", "lead")
    if stage not in DEAL_STAGES:
        raise HTTPException(400, f"Invalid stage. Must be one of: {', '.join(DEAL_STAGES)}")

    try:
        value = float(data.get("value", 0) or 0)
    except (TypeError, ValueError):
        raise HTTPException(400, "Deal value must be a number")
    if value < 0 or value > 1e12:
        raise HTTPException(400, "Deal value out of range")

    try:
        prob = int(data.get("probability_pct", 20) or 0)
    except (TypeError, ValueError):
        prob = 20
    prob = max(0, min(100, prob))

    contact_id = data.get("contact_id") or None
    company_id = data.get("company_id") or None
    if contact_id:
        get_contact(business_id, contact_id)
    if company_id:
        get_company(business_id, company_id)

    did = f"dl-{uuid.uuid4().hex[:10]}"
    row = (
        did, business_id, name,
        value,
        _validate_text(data.get("currency", "USD"), "Currency", 8) or "USD",
        stage, prob,
        contact_id, company_id,
        _validate_text(data.get("notes", ""), "Notes", 2000),
        _validate_text(data.get("expected_close", ""), "Expected close", 30),
        _now(), _now(), user_id,
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {DEALS_TABLE} "
            f"(id, business_id, name, value, currency, stage, probability_pct, contact_id, company_id, "
            f"notes, expected_close, created_at, updated_at, created_by) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row,
        )
        conn.commit()
    finally:
        conn.close()
    # Initial stage event so analytics has a floor
    _log_stage_event(business_id, did, None, stage)
    return get_deal(business_id, did)


def list_deals(business_id: str, stage: Optional[str] = None, search: Optional[str] = None, limit: int = 200) -> List[Dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        sql = f"""
            SELECT d.*,
                   co.name AS company_name,
                   (ct.first_name || ' ' || ct.last_name) AS contact_name
            FROM {DEALS_TABLE} d
            LEFT JOIN {COMPANIES_TABLE} co ON co.id = d.company_id AND co.business_id = d.business_id
            LEFT JOIN {CONTACTS_TABLE} ct ON ct.id = d.contact_id AND ct.business_id = d.business_id
            WHERE d.business_id = ?
        """
        params: list = [business_id]
        if stage:
            if stage not in DEAL_STAGES:
                raise HTTPException(400, f"Invalid stage: {stage}")
            sql += " AND d.stage = ?"
            params.append(stage)
        if search:
            sql += " AND (d.name LIKE ? OR d.notes LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        sql += " ORDER BY d.updated_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_deal(business_id: str, deal_id: str) -> Dict:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"""SELECT d.*,
                       co.name AS company_name,
                       (ct.first_name || ' ' || ct.last_name) AS contact_name
                FROM {DEALS_TABLE} d
                LEFT JOIN {COMPANIES_TABLE} co ON co.id = d.company_id AND co.business_id = d.business_id
                LEFT JOIN {CONTACTS_TABLE} ct ON ct.id = d.contact_id AND ct.business_id = d.business_id
                WHERE d.id = ? AND d.business_id = ?""",
            (deal_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Deal not found")
    return dict(row)


def update_deal(business_id: str, deal_id: str, updates: Dict[str, Any]) -> Dict:
    current = get_deal(business_id, deal_id)
    allowed = {"name", "value", "currency", "stage", "probability_pct",
               "contact_id", "company_id", "notes", "expected_close"}
    fields = {k: v for k, v in updates.items() if k in allowed and v is not None}
    if not fields:
        raise HTTPException(400, "No editable fields provided")

    if "stage" in fields and fields["stage"] not in DEAL_STAGES:
        raise HTTPException(400, f"Invalid stage. Must be one of: {', '.join(DEAL_STAGES)}")
    if "value" in fields:
        try:
            fields["value"] = float(fields["value"])
        except (TypeError, ValueError):
            raise HTTPException(400, "Deal value must be a number")
    if "probability_pct" in fields:
        try:
            fields["probability_pct"] = max(0, min(100, int(fields["probability_pct"])))
        except (TypeError, ValueError):
            fields["probability_pct"] = 20
    if "contact_id" in fields and fields["contact_id"]:
        get_contact(business_id, fields["contact_id"])
    if "company_id" in fields and fields["company_id"]:
        get_company(business_id, fields["company_id"])

    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [_now(), deal_id, business_id]
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {DEALS_TABLE} SET {sets}, updated_at = ? WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()

    # Track stage transitions so analytics can compute time-in-stage
    if "stage" in fields and fields["stage"] != current.get("stage"):
        _log_stage_event(business_id, deal_id, current.get("stage"), fields["stage"])

    return get_deal(business_id, deal_id)


def delete_deal(business_id: str, deal_id: str) -> None:
    get_deal(business_id, deal_id)
    conn = _get_conn()
    try:
        conn.execute(f"UPDATE {INTERACTIONS_TABLE} SET deal_id = NULL WHERE deal_id = ? AND business_id = ?", (deal_id, business_id))
        conn.execute(f"DELETE FROM {DEALS_TABLE} WHERE id = ? AND business_id = ?", (deal_id, business_id))
        conn.commit()
    finally:
        conn.close()


def deal_pipeline_stats(business_id: str) -> Dict[str, Any]:
    """Return counts and values grouped by stage for a business."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT stage, COUNT(*) AS cnt, COALESCE(SUM(value), 0) AS total "
            f"FROM {DEALS_TABLE} WHERE business_id = ? GROUP BY stage",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    by_stage = {s: {"count": 0, "total": 0.0} for s in DEAL_STAGES}
    for r in rows:
        if r["stage"] in by_stage:
            by_stage[r["stage"]] = {"count": r["cnt"], "total": float(r["total"] or 0)}
    return {"stages": DEAL_STAGES, "by_stage": by_stage}


# ═══════════════════════════════════════════════════════════════════════════════
#  INTERACTIONS (activity log)
# ═══════════════════════════════════════════════════════════════════════════════
def create_interaction(business_id: str, user_id: str, data: Dict[str, Any]) -> Dict:
    itype = data.get("type", "note")
    if itype not in INTERACTION_TYPES:
        raise HTTPException(400, f"Invalid interaction type. Must be one of: {', '.join(INTERACTION_TYPES)}")

    contact_id = data.get("contact_id") or None
    company_id = data.get("company_id") or None
    deal_id = data.get("deal_id") or None
    if contact_id:
        get_contact(business_id, contact_id)
    if company_id:
        get_company(business_id, company_id)
    if deal_id:
        get_deal(business_id, deal_id)

    iid = f"ix-{uuid.uuid4().hex[:10]}"
    row = (
        iid, business_id, contact_id, company_id, deal_id, itype,
        _validate_text(data.get("subject", ""), "Subject", 200),
        _validate_text(data.get("summary", ""), "Summary", 4000),
        data.get("occurred_at") or _now(),
        _now(), user_id,
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {INTERACTIONS_TABLE} "
            f"(id, business_id, contact_id, company_id, deal_id, type, subject, summary, occurred_at, created_at, created_by) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?)", row,
        )
        conn.commit()
    finally:
        conn.close()

    # @mentions in interaction summaries notify the mentioned teammates
    try:
        from api.team import process_mentions
        process_mentions(
            business_id=business_id, author_id=user_id,
            text=f"{data.get('subject', '')}\n{data.get('summary', '')}",
            context_label=f"{data.get('type', 'interaction')} note",
        )
    except Exception:
        pass

    return get_interaction(business_id, iid)


def get_interaction(business_id: str, interaction_id: str) -> Dict:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {INTERACTIONS_TABLE} WHERE id = ? AND business_id = ?",
            (interaction_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Interaction not found")
    return dict(row)


def list_interactions(
    business_id: str,
    contact_id: Optional[str] = None,
    company_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        sql = f"SELECT * FROM {INTERACTIONS_TABLE} WHERE business_id = ?"
        params: list = [business_id]
        if contact_id:
            sql += " AND contact_id = ?"; params.append(contact_id)
        if company_id:
            sql += " AND company_id = ?"; params.append(company_id)
        if deal_id:
            sql += " AND deal_id = ?"; params.append(deal_id)
        sql += " ORDER BY occurred_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def delete_interaction(business_id: str, interaction_id: str) -> None:
    get_interaction(business_id, interaction_id)
    conn = _get_conn()
    try:
        conn.execute(f"DELETE FROM {INTERACTIONS_TABLE} WHERE id = ? AND business_id = ?", (interaction_id, business_id))
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  SUMMARY / DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def crm_overview(business_id: str) -> Dict[str, Any]:
    """Return quick stats for the CRM dashboard widget."""
    conn = _get_conn()
    try:
        contacts = conn.execute(
            f"SELECT COUNT(*) FROM {CONTACTS_TABLE} WHERE business_id = ?", (business_id,)
        ).fetchone()[0]
        companies = conn.execute(
            f"SELECT COUNT(*) FROM {COMPANIES_TABLE} WHERE business_id = ?", (business_id,)
        ).fetchone()[0]
        deals = conn.execute(
            f"SELECT COUNT(*), COALESCE(SUM(value), 0) FROM {DEALS_TABLE} "
            f"WHERE business_id = ? AND stage NOT IN ('won','lost')", (business_id,)
        ).fetchone()
        won_this_month = conn.execute(
            f"SELECT COALESCE(SUM(value), 0) FROM {DEALS_TABLE} "
            f"WHERE business_id = ? AND stage = 'won' AND updated_at >= ?",
            (business_id, datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()),
        ).fetchone()[0]
    finally:
        conn.close()
    return {
        "contacts": contacts,
        "companies": companies,
        "open_deals_count": deals[0],
        "open_deals_value": float(deals[1] or 0),
        "won_this_month": float(won_this_month or 0),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Bulk helpers — list pages call these from the selection action bar
# ═══════════════════════════════════════════════════════════════════════════════
def _bulk_delete(table: str, business_id: str, ids: List[str]) -> int:
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    conn = _get_conn()
    try:
        cur = conn.execute(
            f"DELETE FROM {table} WHERE business_id = ? AND id IN ({placeholders})",
            [business_id, *ids],
        )
        conn.commit()
        return cur.rowcount or 0
    finally:
        conn.close()


def bulk_delete_contacts(business_id: str, ids: List[str]) -> int:
    return _bulk_delete(CONTACTS_TABLE, business_id, ids)


def bulk_delete_companies(business_id: str, ids: List[str]) -> int:
    """Delete companies and null out their FKs on contacts / deals first."""
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {CONTACTS_TABLE} SET company_id = NULL "
            f"WHERE business_id = ? AND company_id IN ({placeholders})",
            [business_id, *ids],
        )
        conn.execute(
            f"UPDATE {DEALS_TABLE} SET company_id = NULL "
            f"WHERE business_id = ? AND company_id IN ({placeholders})",
            [business_id, *ids],
        )
        cur = conn.execute(
            f"DELETE FROM {COMPANIES_TABLE} WHERE business_id = ? AND id IN ({placeholders})",
            [business_id, *ids],
        )
        conn.commit()
        return cur.rowcount or 0
    finally:
        conn.close()


def bulk_delete_deals(business_id: str, ids: List[str]) -> int:
    return _bulk_delete(DEALS_TABLE, business_id, ids)


def bulk_update_deal_stage(business_id: str, ids: List[str], stage: str) -> int:
    """Move many deals to a new stage in one call."""
    if stage not in DEAL_STAGES:
        raise HTTPException(400, f"Invalid stage. Must be one of: {', '.join(DEAL_STAGES)}")
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    conn = _get_conn()
    try:
        cur = conn.execute(
            f"UPDATE {DEALS_TABLE} SET stage = ?, updated_at = ? "
            f"WHERE business_id = ? AND id IN ({placeholders})",
            [stage, datetime.now().isoformat(), business_id, *ids],
        )
        conn.commit()
        return cur.rowcount or 0
    finally:
        conn.close()
