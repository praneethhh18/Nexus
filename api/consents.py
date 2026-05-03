"""
Consent ledger — append-only audit trail of consent grants and revocations.

One row per (contact, consent_type, grant or revocation event). The current
state (active / revoked) is derived by reading the latest row per
(contact, consent_type). The denormalized `is_callable` and
`consent_revoked_at` columns on `nexus_contacts` mirror the latest
`voice_call` consent state so the hot path (Vox dial check) doesn't need a
join.

Privacy / legal note: this is the legal evidence trail. NEVER delete rows —
record revocations as new rows, never mutate or remove existing ones.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from typing import Optional, List, Dict

from config.db import get_conn
from utils.timez import now_iso

CONSENTS_TABLE = "nexus_contact_consents"

VALID_CONSENT_TYPES = ("voice_call", "sms", "email_marketing")
VALID_GRANT_SOURCES = (
    "manual",          # user clicked "record consent" in the UI
    "lead_form",       # consent box ticked on a public lead-capture form
    "imported_csv",    # CRM import where uploader attests prior consent
    "inbound_call",    # they called us; consent implied by their initiation
    "reply_yes",       # SMS / email opt-in via "YES" reply
    "double_opt_in",   # confirmed via second-channel verification
)
VALID_REVOKE_REASONS = (
    "dnc_request",     # callee said "do not call again"
    "manual",          # user clicked "revoke" in the UI
    "do_not_contact",  # general broad opt-out across all channels
    "wrong_number",    # phone belongs to someone else
    "deceased",
)


def _conn():
    conn = get_conn()
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {CONSENTS_TABLE} (
        id              TEXT PRIMARY KEY,
        business_id     TEXT NOT NULL,
        contact_id      TEXT NOT NULL,
        consent_type    TEXT NOT NULL,
        granted_at      TEXT,
        granted_via     TEXT,
        evidence_url    TEXT,
        revoked_at      TEXT,
        revoked_reason  TEXT,
        created_by      TEXT,
        created_at      TEXT NOT NULL
    )""")
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_consents_contact "
        f"ON {CONSENTS_TABLE}(contact_id, consent_type, created_at)"
    )
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_consents_biz "
        f"ON {CONSENTS_TABLE}(business_id, consent_type)"
    )
    conn.commit()
    return conn


def grant_consent(
    business_id: str,
    contact_id: str,
    consent_type: str,
    granted_via: str,
    *,
    evidence_url: str = "",
    created_by: str = "system",
) -> Dict:
    """Record a consent grant. Mirrors denormalized state on the contact row
    so the dial hot-path doesn't need a join."""
    if consent_type not in VALID_CONSENT_TYPES:
        raise ValueError(f"Invalid consent_type: {consent_type}")
    if granted_via not in VALID_GRANT_SOURCES:
        raise ValueError(f"Invalid granted_via: {granted_via}")

    cid = f"con-{uuid.uuid4().hex[:10]}"
    now = now_iso()
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {CONSENTS_TABLE} "
            f"(id, business_id, contact_id, consent_type, granted_at, "
            f"granted_via, evidence_url, created_by, created_at) "
            f"VALUES (?,?,?,?,?,?,?,?,?)",
            (cid, business_id, contact_id, consent_type, now,
             granted_via, evidence_url, created_by, now),
        )
        # Mirror denormalized state on contacts (voice_call only — other
        # channels can add their own fast-path columns when wired).
        if consent_type == "voice_call":
            conn.execute(
                "UPDATE nexus_contacts SET is_callable = 1, "
                "consent_revoked_at = NULL "
                "WHERE id = ? AND business_id = ?",
                (contact_id, business_id),
            )
        conn.commit()
    finally:
        conn.close()
    return get_active_consent(business_id, contact_id, consent_type) or {"id": cid}


def revoke_consent(
    business_id: str,
    contact_id: str,
    consent_type: str,
    reason: str,
    *,
    created_by: str = "system",
) -> None:
    """Record a revocation. Auto-flips contact.is_callable = 0 for voice.
    Idempotent — calling twice with the same outcome just appends another
    revocation record (intended; the audit trail wants to know we tried)."""
    if reason not in VALID_REVOKE_REASONS:
        raise ValueError(f"Invalid reason: {reason}")
    cid = f"con-{uuid.uuid4().hex[:10]}"
    now = now_iso()
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {CONSENTS_TABLE} "
            f"(id, business_id, contact_id, consent_type, revoked_at, "
            f"revoked_reason, created_by, created_at) "
            f"VALUES (?,?,?,?,?,?,?,?)",
            (cid, business_id, contact_id, consent_type, now,
             reason, created_by, now),
        )
        if consent_type == "voice_call":
            conn.execute(
                "UPDATE nexus_contacts SET is_callable = 0, "
                "consent_revoked_at = ? "
                "WHERE id = ? AND business_id = ?",
                (now, contact_id, business_id),
            )
        conn.commit()
    finally:
        conn.close()


def get_active_consent(
    business_id: str,
    contact_id: str,
    consent_type: str,
) -> Optional[Dict]:
    """Latest consent record for this (contact, type). None if no record OR
    if the latest row is a revocation."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {CONSENTS_TABLE} "
            f"WHERE business_id = ? AND contact_id = ? AND consent_type = ? "
            f"ORDER BY created_at DESC, id DESC LIMIT 1",
            (business_id, contact_id, consent_type),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    d = dict(row)
    return d if d.get("granted_at") and not d.get("revoked_at") else None


def get_consent_history(
    business_id: str,
    contact_id: str,
) -> List[Dict]:
    """Full history of consent changes for a contact — for audit display."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT * FROM {CONSENTS_TABLE} "
            f"WHERE business_id = ? AND contact_id = ? "
            f"ORDER BY created_at ASC, id ASC",
            (business_id, contact_id),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
