"""
Businesses module — multi-tenant foundation for NexusAgent.

Every piece of business data (contacts, tasks, deals, workflows, conversations,
notifications, knowledge base entries, reports) lives inside a single "business".
A user can own or belong to multiple businesses and switch between them.

Security model:
- Every API request resolves a (user, business) pair via get_current_context.
- Business access is verified server-side against the business_members table.
- The business_id comes from the X-Business-Id header, never from the request body,
  and the server checks membership on every call.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from datetime import datetime
from typing import Optional, List, Dict

from fastapi import HTTPException
from loguru import logger

from config.db import get_conn, list_columns  # list_columns drives the additive-column migration below

BUSINESSES_TABLE = "nexus_businesses"
MEMBERS_TABLE = "nexus_business_members"

# Legacy tenant ID used when we migrate rows from the pre-multi-tenant schema.
# Rows stamped with this ID are reassigned to the first real business at migration.
LEGACY_DEFAULT = "default"


def _get_conn():
    conn = get_conn()
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {BUSINESSES_TABLE} (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        industry TEXT DEFAULT '',
        description TEXT DEFAULT '',
        owner_id TEXT NOT NULL,
        created_at TEXT,
        updated_at TEXT,
        is_active INTEGER DEFAULT 1,
        settings TEXT DEFAULT '{{}}'
    )""")
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {MEMBERS_TABLE} (
        business_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT DEFAULT 'member',
        joined_at TEXT,
        PRIMARY KEY (business_id, user_id),
        FOREIGN KEY (business_id) REFERENCES {BUSINESSES_TABLE}(id) ON DELETE CASCADE
    )""")
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_members_user ON {MEMBERS_TABLE}(user_id)"
    )
    # Additive: per-business override for the voice-call recording disclosure.
    # Some businesses' legal teams want their own wording; NULL falls back to
    # the in-code default in voice/outbound/pipeline.py.
    _biz_cols = list_columns(conn, BUSINESSES_TABLE)
    if "recording_disclosure_text" not in _biz_cols:
        conn.execute(
            f"ALTER TABLE {BUSINESSES_TABLE} ADD COLUMN recording_disclosure_text TEXT"
        )
    conn.commit()
    return conn


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_business(
    name: str,
    owner_id: str,
    industry: str = "",
    description: str = "",
) -> Dict:
    """Create a new business and add the owner as a member with role=owner."""
    if not name.strip():
        raise HTTPException(400, "Business name cannot be empty")
    if len(name) > 120:
        raise HTTPException(400, "Business name too long (max 120 chars)")

    bid = f"biz-{uuid.uuid4().hex[:10]}"
    now = datetime.now().isoformat()

    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {BUSINESSES_TABLE} (id, name, industry, description, owner_id, created_at, updated_at) "
            f"VALUES (?,?,?,?,?,?,?)",
            (bid, name.strip(), industry.strip(), description.strip(), owner_id, now, now),
        )
        conn.execute(
            f"INSERT INTO {MEMBERS_TABLE} (business_id, user_id, role, joined_at) VALUES (?,?,?,?)",
            (bid, owner_id, "owner", now),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(f"[Business] Created {bid} '{name}' owner={owner_id}")
    return get_business(bid)


def get_business(business_id: str) -> Optional[Dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {BUSINESSES_TABLE} WHERE id = ? AND is_active = 1",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def list_user_businesses(user_id: str) -> List[Dict]:
    """Return all active businesses a user belongs to, with their role."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT b.*, m.role as member_role
            FROM {BUSINESSES_TABLE} b
            JOIN {MEMBERS_TABLE} m ON m.business_id = b.id
            WHERE m.user_id = ? AND b.is_active = 1
            ORDER BY b.created_at ASC
            """,
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def update_business(business_id: str, user_id: str, updates: Dict) -> Dict:
    """Update business fields. Only owner/admin can edit."""
    role = get_member_role(business_id, user_id)
    if role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can edit this business")

    allowed = {"name", "industry", "description"}
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        raise HTTPException(400, "No editable fields provided")

    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [datetime.now().isoformat(), business_id]

    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {BUSINESSES_TABLE} SET {sets}, updated_at = ? WHERE id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()
    return get_business(business_id)


def delete_business(business_id: str, user_id: str) -> None:
    """Soft-delete a business. Only the owner can do this."""
    role = get_member_role(business_id, user_id)
    if role != "owner":
        raise HTTPException(403, "Only the owner can delete this business")

    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {BUSINESSES_TABLE} SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), business_id),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info(f"[Business] Soft-deleted {business_id} by {user_id}")


# ── Membership ────────────────────────────────────────────────────────────────

def get_member_role(business_id: str, user_id: str) -> Optional[str]:
    conn = _get_conn()
    try:
        row = conn.execute(
            f"SELECT role FROM {MEMBERS_TABLE} WHERE business_id = ? AND user_id = ?",
            (business_id, user_id),
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def list_members(business_id: str) -> List[Dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT m.user_id, m.role, m.joined_at,
                   u.email, u.name
            FROM {MEMBERS_TABLE} m
            LEFT JOIN nexus_users u ON u.id = m.user_id
            WHERE m.business_id = ?
            ORDER BY m.joined_at ASC
            """,
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def add_member(
    business_id: str,
    actor_user_id: str,
    target_user_id: str,
    role: str = "member",
) -> None:
    if role not in ("owner", "admin", "member", "viewer"):
        raise HTTPException(400, f"Invalid role: {role}")
    actor_role = get_member_role(business_id, actor_user_id)
    if actor_role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can add members")
    if role == "owner":
        raise HTTPException(400, "Cannot assign owner role directly; transfer ownership instead")

    conn = _get_conn()
    try:
        # Portable upsert: re-adding an existing member updates their role.
        conn.execute(
            f"INSERT INTO {MEMBERS_TABLE} (business_id, user_id, role, joined_at) "
            f"VALUES (?,?,?,?) "
            f"ON CONFLICT (business_id, user_id) DO UPDATE SET "
            f"  role = EXCLUDED.role, joined_at = EXCLUDED.joined_at",
            (business_id, target_user_id, role, datetime.now().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info(f"[Business] {actor_user_id} added {target_user_id} to {business_id} as {role}")


def remove_member(business_id: str, actor_user_id: str, target_user_id: str) -> None:
    actor_role = get_member_role(business_id, actor_user_id)
    if actor_role not in ("owner", "admin") and actor_user_id != target_user_id:
        raise HTTPException(403, "Cannot remove other members")

    target_role = get_member_role(business_id, target_user_id)
    if target_role == "owner":
        raise HTTPException(400, "Cannot remove owner; transfer ownership first")

    conn = _get_conn()
    try:
        conn.execute(
            f"DELETE FROM {MEMBERS_TABLE} WHERE business_id = ? AND user_id = ?",
            (business_id, target_user_id),
        )
        conn.commit()
    finally:
        conn.close()


# ── Access control ────────────────────────────────────────────────────────────

def assert_member(business_id: str, user_id: str) -> str:
    """
    Raise 403 unless the user is an active member of the business.
    Returns the member role on success.
    """
    role = get_member_role(business_id, user_id)
    if not role:
        raise HTTPException(403, "You do not have access to this business")
    biz = get_business(business_id)
    if not biz:
        raise HTTPException(404, "Business not found or inactive")
    return role


def ensure_business_for_user(user_id: str, user_name: str) -> str:
    """
    Ensure a user has at least one business. Create a default one if not.
    Returns the business_id.
    """
    businesses = list_user_businesses(user_id)
    if businesses:
        return businesses[0]["id"]

    default_name = f"{user_name}'s Business" if user_name else "My Business"
    biz = create_business(default_name, owner_id=user_id)
    return biz["id"]


# ── One-time migration: legacy rows → default business ───────────────────────

def migrate_legacy_data() -> None:
    """
    Move pre-multi-tenant rows (user_id='default' or business_id='default') into
    a real business owned by the first admin. Idempotent; safe to call on every boot.
    """
    conn = _get_conn()
    try:
        # Find admin user
        admin_row = conn.execute(
            "SELECT id, name FROM nexus_users WHERE role = 'admin' ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        if not admin_row:
            return  # no users yet

        admin_id, admin_name = admin_row[0], admin_row[1]

        # Does a "Legacy Data" business already exist for this admin?
        existing = conn.execute(
            f"SELECT id FROM {BUSINESSES_TABLE} WHERE owner_id = ? AND name = 'Default Business'",
            (admin_id,),
        ).fetchone()

        if existing:
            default_biz_id = existing[0]
        else:
            # Create it — using direct SQL so we don't reenter create_business() and nest conns
            default_biz_id = f"biz-{uuid.uuid4().hex[:10]}"
            now = datetime.now().isoformat()
            conn.execute(
                f"INSERT INTO {BUSINESSES_TABLE} (id, name, industry, description, owner_id, created_at, updated_at) "
                f"VALUES (?,?,?,?,?,?,?)",
                (default_biz_id, "Default Business", "", "Migrated from pre-multi-tenant data", admin_id, now, now),
            )
            conn.execute(
                f"INSERT INTO {MEMBERS_TABLE} (business_id, user_id, role, joined_at) VALUES (?,?,?,?)",
                (default_biz_id, admin_id, "owner", now),
            )
            logger.info(f"[Business] Created Default Business {default_biz_id} for legacy data migration")

        # Remap legacy rows in each data table that has a business_id column.
        legacy_tables = [
            "nexus_conversations",
            "nexus_query_history",
            "nexus_notifications",
            "nexus_audit_log",
        ]
        for tbl in legacy_tables:
            try:
                cols = list_columns(conn, tbl)
                if "business_id" in cols:
                    conn.execute(
                        f"UPDATE {tbl} SET business_id = ? WHERE business_id IS NULL OR business_id = 'default' OR business_id = ''",
                        (default_biz_id,),
                    )
            except sqlite3.OperationalError:
                pass  # table doesn't exist yet

        conn.commit()
    finally:
        conn.close()
