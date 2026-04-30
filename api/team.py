"""
Team collaboration — invite flow, @mentions, and activity feed.

Invite flow:
    1. Owner/admin of a business creates an invite for an email + role.
    2. Backend emails an accept link with a signed token.
    3. Recipient clicks link → logs in (or signs up) → POST /accept.
    4. User becomes a member of the business with the given role.

Mentions:
    `@name` or `@id` in a task description or interaction summary triggers
    an in-app notification to that user.

Activity feed:
    Unified stream combining audit log entries, approvals, and notifications
    into one timeline per business. Read-only.
"""
from __future__ import annotations

import os
import re
import secrets
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import HTTPException
from loguru import logger

from config.db import get_conn
from utils.timez import now_iso, now_utc_naive

INVITES_TABLE = "nexus_business_invites"

VALID_ROLES = {"viewer", "member", "admin"}

INVITE_TTL_DAYS = 7


def _get_conn():
    conn = get_conn()
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {INVITES_TABLE} (
        token TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        email TEXT NOT NULL,
        role TEXT NOT NULL,
        invited_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        accepted_at TEXT,
        accepted_by TEXT,
        revoked_at TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_invites_biz ON {INVITES_TABLE}(business_id, accepted_at)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_invites_email ON {INVITES_TABLE}(LOWER(email))")
    conn.commit()
    return conn


def _now() -> str:
    return now_iso()


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, f"Invalid email: {email}")
    return email


# ═══════════════════════════════════════════════════════════════════════════════
#  INVITES
# ═══════════════════════════════════════════════════════════════════════════════
def create_invite(business_id: str, inviter_id: str, email: str, role: str = "member") -> Dict[str, Any]:
    role = (role or "member").strip().lower()
    if role not in VALID_ROLES:
        raise HTTPException(400, f"Invalid role. Must be one of: {sorted(VALID_ROLES)}")

    # Inviter must be owner/admin
    from api.businesses import get_member_role
    inviter_role = get_member_role(business_id, inviter_id)
    if inviter_role not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can send invites")

    email = _validate_email(email)

    token = secrets.token_urlsafe(28)
    now = now_utc_naive()
    expires = now + timedelta(days=INVITE_TTL_DAYS)

    conn = _get_conn()
    try:
        # Invalidate any prior pending invites for (business, email)
        conn.execute(
            f"UPDATE {INVITES_TABLE} SET revoked_at = ? "
            f"WHERE business_id = ? AND LOWER(email) = ? AND accepted_at IS NULL AND revoked_at IS NULL",
            (now.isoformat(), business_id, email),
        )
        conn.execute(
            f"INSERT INTO {INVITES_TABLE} "
            f"(token, business_id, email, role, invited_by, created_at, expires_at) "
            f"VALUES (?,?,?,?,?,?,?)",
            (token, business_id, email, role, inviter_id, now.isoformat(), expires.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    # Try to deliver via email. If SMTP isn't configured, log the link so the
    # owner can forward it manually.
    from api.businesses import get_business
    biz = get_business(business_id) or {}
    invite_record = _get_invite_by_token(token)

    link = _invite_link(token)
    _send_invite_email(email, biz.get("name", "a business"), link)

    invite_record["link"] = link
    return invite_record


def _invite_link(token: str) -> str:
    base = os.getenv("APP_BASE_URL", "http://localhost:5173").rstrip("/")
    return f"{base}/accept-invite?token={token}"


def _send_invite_email(to: str, business_name: str, link: str) -> None:
    from config.settings import EMAIL_ENABLED, GMAIL_USER, GMAIL_APP_PASSWORD
    if not EMAIL_ENABLED:
        logger.warning(f"[Team] EMAIL not configured. Invite link for {to}: {link}")
        return
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        body = (
            f"Hi,\n\n"
            f"You've been invited to collaborate on {business_name} in NexusAgent.\n\n"
            f"Accept the invite: {link}\n\n"
            f"The link expires in {INVITE_TTL_DAYS} days. If you don't have "
            f"an account, you'll be able to create one when you accept.\n\n"
            f"— NexusAgent"
        )
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to
        msg["Subject"] = f"You're invited to {business_name} on NexusAgent"
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"[Team] Invite email sent to {to}")
    except Exception as e:
        logger.warning(f"[Team] Invite email failed for {to}: {e}. Link: {link}")


def _get_invite_by_token(token: str) -> Dict[str, Any]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(f"SELECT * FROM {INVITES_TABLE} WHERE token = ?", (token,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Invite not found")
    return dict(row)


def get_invite_preview(token: str) -> Dict[str, Any]:
    """Public endpoint — shows minimal info so the recipient knows what they're joining."""
    inv = _get_invite_by_token(token)
    if inv.get("accepted_at"):
        return {"status": "accepted", "email": inv["email"]}
    if inv.get("revoked_at"):
        return {"status": "revoked"}
    try:
        if now_utc_naive() > datetime.fromisoformat(inv["expires_at"]):
            return {"status": "expired"}
    except Exception:
        return {"status": "expired"}

    from api.businesses import get_business
    biz = get_business(inv["business_id"]) or {}
    return {
        "status": "pending",
        "email": inv["email"],
        "role": inv["role"],
        "business_id": inv["business_id"],
        "business_name": biz.get("name"),
    }


def accept_invite(token: str, user_id: str, user_email: str) -> Dict[str, Any]:
    """Mark invite as accepted and add the user as a business member."""
    inv = _get_invite_by_token(token)
    if inv.get("accepted_at"):
        raise HTTPException(400, "Invite already accepted")
    if inv.get("revoked_at"):
        raise HTTPException(400, "Invite has been revoked")
    try:
        if now_utc_naive() > datetime.fromisoformat(inv["expires_at"]):
            raise HTTPException(400, "Invite has expired")
    except Exception:
        raise HTTPException(400, "Invite has expired")

    # Email on the token must match the accepting user
    if (inv["email"] or "").lower() != (user_email or "").lower():
        raise HTTPException(403, "This invite is for a different email address")

    # Add membership (owner is a protected role — invites can't grant ownership)
    from api.businesses import _get_conn as _biz_conn, MEMBERS_TABLE
    conn = _biz_conn()
    try:
        # Portable upsert — re-accepting an invite refreshes role + joined_at.
        conn.execute(
            f"INSERT INTO {MEMBERS_TABLE} (business_id, user_id, role, joined_at) "
            f"VALUES (?,?,?,?) "
            f"ON CONFLICT (business_id, user_id) DO UPDATE SET "
            f"  role = EXCLUDED.role, joined_at = EXCLUDED.joined_at",
            (inv["business_id"], user_id, inv["role"], _now()),
        )
        conn.commit()
    finally:
        conn.close()

    # Mark invite consumed
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {INVITES_TABLE} SET accepted_at = ?, accepted_by = ? WHERE token = ?",
            (_now(), user_id, token),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(f"[Team] {user_id} joined {inv['business_id']} as {inv['role']}")
    return {"ok": True, "business_id": inv["business_id"], "role": inv["role"]}


def list_invites(business_id: str, include_accepted: bool = False) -> List[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        if include_accepted:
            rows = conn.execute(
                f"SELECT * FROM {INVITES_TABLE} WHERE business_id = ? ORDER BY created_at DESC",
                (business_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM {INVITES_TABLE} WHERE business_id = ? "
                f"AND accepted_at IS NULL AND revoked_at IS NULL ORDER BY created_at DESC",
                (business_id,),
            ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def revoke_invite(business_id: str, actor_user_id: str, token: str) -> None:
    from api.businesses import get_member_role
    if get_member_role(business_id, actor_user_id) not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can revoke invites")
    inv = _get_invite_by_token(token)
    if inv["business_id"] != business_id:
        raise HTTPException(404, "Invite not found for this business")
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {INVITES_TABLE} SET revoked_at = ? WHERE token = ?",
            (_now(), token),
        )
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  MENTIONS
# ═══════════════════════════════════════════════════════════════════════════════
_MENTION_RE = re.compile(r"@([A-Za-z0-9._-]{2,60})")


def process_mentions(business_id: str, author_id: str, text: str,
                     context_label: str = "", link_hint: str = "") -> List[str]:
    """
    Parse @mentions from `text`, map them to business members (by name or
    email prefix), and push an in-app notification to each.
    Returns the list of notified user_ids.
    """
    if not text:
        return []

    matches = {m.lower() for m in _MENTION_RE.findall(text)}
    if not matches:
        return []

    from api.businesses import list_members
    members = list_members(business_id)

    notified: List[str] = []
    for member in members:
        uid = member.get("user_id")
        if not uid or uid == author_id:
            continue
        name = (member.get("name") or "").lower()
        email = (member.get("email") or "").lower()
        email_prefix = email.split("@")[0] if email else ""
        name_first = name.split()[0] if name else ""
        if any(m in (name, email, email_prefix, name_first) for m in matches) or any(
            name_first and name_first.startswith(m) for m in matches
        ):
            try:
                from api import notifications as _notifs
                _notifs.push(
                    title="You were mentioned" + (f" in {context_label}" if context_label else ""),
                    message=(text[:400] + ("…" if len(text) > 400 else "")),
                    severity="info",
                    type="mention",
                    user_id=uid,
                    business_id=business_id,
                    metadata={"link": link_hint, "by": author_id} if link_hint else {"by": author_id},
                )
                notified.append(uid)
            except Exception as e:
                logger.warning(f"[Mentions] notify failed for {uid}: {e}")
    return notified


# ═══════════════════════════════════════════════════════════════════════════════
#  ACTIVITY FEED
# ═══════════════════════════════════════════════════════════════════════════════
def activity_feed(business_id: str, limit: int = 60) -> List[Dict[str, Any]]:
    """
    Unified feed combining audit log entries, approvals, notifications,
    and CRM interactions for this business. Most recent first.
    """
    items: List[Dict[str, Any]] = []
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        # Audit log (tool calls)
        try:
            rows = conn.execute(
                "SELECT event_id, timestamp, tool_name, input_summary, output_summary, success, user_id "
                "FROM nexus_audit_log WHERE business_id = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (business_id, limit),
            ).fetchall()
            for r in rows:
                items.append({
                    "kind": "tool_call",
                    "id": r["event_id"],
                    "ts": r["timestamp"],
                    "actor_id": r["user_id"],
                    "title": r["tool_name"],
                    "summary": (r["input_summary"] or "")[:200],
                    "result": (r["output_summary"] or "")[:200],
                    "success": bool(r["success"]),
                })
        except sqlite3.OperationalError:
            pass

        # Approvals
        try:
            rows = conn.execute(
                "SELECT id, created_at, tool_name, summary, status, requested_by "
                "FROM nexus_agent_approvals WHERE business_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (business_id, limit),
            ).fetchall()
            for r in rows:
                items.append({
                    "kind": "approval",
                    "id": r["id"],
                    "ts": r["created_at"],
                    "actor_id": r["requested_by"],
                    "title": f"approval: {r['tool_name']} ({r['status']})",
                    "summary": (r["summary"] or "")[:200],
                    "success": r["status"] in ("executed", "approved"),
                })
        except sqlite3.OperationalError:
            pass

        # Interactions (CRM)
        try:
            rows = conn.execute(
                "SELECT id, created_at, type, subject, summary, created_by "
                "FROM nexus_interactions WHERE business_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (business_id, limit),
            ).fetchall()
            for r in rows:
                items.append({
                    "kind": "interaction",
                    "id": r["id"],
                    "ts": r["created_at"],
                    "actor_id": r["created_by"],
                    "title": f"{r['type']}: {r['subject'] or ''}",
                    "summary": (r["summary"] or "")[:200],
                    "success": True,
                })
        except sqlite3.OperationalError:
            pass

        # Notifications of interest (mentions, workflow completions)
        try:
            rows = conn.execute(
                "SELECT id, created_at, type, title, message, severity "
                "FROM nexus_notifications WHERE business_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (business_id, limit),
            ).fetchall()
            for r in rows:
                items.append({
                    "kind": "notification",
                    "id": r["id"],
                    "ts": r["created_at"],
                    "actor_id": None,
                    "title": r["title"],
                    "summary": (r["message"] or "")[:200],
                    "severity": r["severity"],
                    "success": r["severity"] in ("info", "success"),
                })
        except sqlite3.OperationalError:
            pass
    finally:
        conn.close()

    # Enrich with actor display name
    user_ids = {i["actor_id"] for i in items if i.get("actor_id")}
    user_cache = {}
    if user_ids:
        conn = get_conn()
        conn.row_factory = sqlite3.Row
        try:
            placeholders = ",".join("?" for _ in user_ids)
            rows = conn.execute(
                f"SELECT id, name, email FROM nexus_users WHERE id IN ({placeholders})",
                tuple(user_ids),
            ).fetchall()
            user_cache = {r["id"]: {"name": r["name"], "email": r["email"]} for r in rows}
        finally:
            conn.close()
    for it in items:
        aid = it.get("actor_id")
        if aid and aid in user_cache:
            it["actor_name"] = user_cache[aid]["name"]
        elif aid:
            it["actor_name"] = "system"

    items.sort(key=lambda x: x.get("ts") or "", reverse=True)
    return items[:limit]
