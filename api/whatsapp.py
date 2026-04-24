"""
WhatsApp integration — pairs a phone number to a NexusAgent user and routes
incoming WhatsApp messages through the agent loop.

Design:
- A small Node.js "bridge" (whatsapp_bridge/) runs Baileys, which speaks
  WhatsApp Web. It POSTs every inbound message to /api/whatsapp/inbound,
  and the backend returns a JSON reply the bridge sends back over WhatsApp.
- Phone numbers are linked to a (user, business) once, via a 6-char code
  the user generates in the web UI. Unlinked numbers get a helpful hint.
- Shared-secret auth protects /api/whatsapp/inbound so only your own bridge
  can POST messages to the backend.

Tables:
    nexus_whatsapp_accounts  — one row per (phone, user). A phone only ever
        maps to one user at a time. `active_business_id` lets the user pick
        which business this phone is "currently on" (they can switch with a
        `/business <name>` command).
    nexus_whatsapp_link_tokens — short-lived codes generated from the UI.
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from loguru import logger

from config.settings import DB_PATH
from utils.timez import now_iso, now_utc_naive

ACCOUNTS_TABLE = "nexus_whatsapp_accounts"
TOKENS_TABLE = "nexus_whatsapp_link_tokens"

# How long a link code stays valid
LINK_TOKEN_TTL_MIN = 15

# Rate limit: max messages per phone per window
MSGS_PER_WINDOW = 20
WINDOW_SECONDS = 60

# In-memory message dedup + rate-limit trackers
_DEDUP: Dict[str, float] = {}  # message_id -> timestamp
_RATE_LIMIT: Dict[str, deque] = defaultdict(deque)


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {ACCOUNTS_TABLE} (
        phone TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        active_business_id TEXT,
        linked_at TEXT,
        last_message_at TEXT,
        messages_count INTEGER DEFAULT 0
    )""")
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {TOKENS_TABLE} (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        business_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used_at TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_wa_user ON {ACCOUNTS_TABLE}(user_id)")
    conn.commit()
    return conn


def _now_iso() -> str:
    return now_iso()


# ── Shared-secret auth for the bridge ────────────────────────────────────────
def _expected_secret() -> str:
    """Persisted per-install secret the Node bridge must send in X-Nexus-Secret."""
    env = os.getenv("WHATSAPP_WEBHOOK_SECRET", "").strip()
    if env:
        return env
    # Generate once and persist
    p = Path(DB_PATH).parent / ".whatsapp_secret"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    sec = secrets.token_urlsafe(32)
    p.write_text(sec, encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    logger.warning(f"[WhatsApp] No WHATSAPP_WEBHOOK_SECRET in .env — generated one at {p}")
    return sec


def verify_bridge_secret(provided: str) -> None:
    if not provided:
        raise HTTPException(401, "Missing X-Nexus-Secret header")
    if not secrets.compare_digest(provided, _expected_secret()):
        raise HTTPException(401, "Invalid bridge secret")


def get_bridge_secret() -> str:
    """Exposed to the UI (owner only) so the user can paste it into the bridge .env."""
    return _expected_secret()


# ── Link code flow ───────────────────────────────────────────────────────────
def _new_code() -> str:
    # 6 chars: readable, no ambiguous 0/O/1/I
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def generate_link_token(user_id: str, business_id: str) -> Dict[str, Any]:
    """Issue a short-lived link code to be sent over WhatsApp to the bot."""
    code = _new_code()
    now = now_utc_naive()
    expires = now + timedelta(minutes=LINK_TOKEN_TTL_MIN)
    conn = _get_conn()
    try:
        # Invalidate previous unused codes for this user
        conn.execute(
            f"UPDATE {TOKENS_TABLE} SET used_at = ? WHERE user_id = ? AND used_at IS NULL",
            (now.isoformat(), user_id),
        )
        conn.execute(
            f"INSERT INTO {TOKENS_TABLE} (token, user_id, business_id, created_at, expires_at) "
            f"VALUES (?,?,?,?,?)",
            (code, user_id, business_id, now.isoformat(), expires.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "code": code,
        "expires_at": expires.isoformat(),
        "ttl_minutes": LINK_TOKEN_TTL_MIN,
    }


def _normalize_phone(phone: str) -> str:
    """WhatsApp JIDs look like 919876543210@s.whatsapp.net. Strip to digits."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    return digits


def _consume_link_code(phone: str, text: str) -> Optional[Dict[str, Any]]:
    """If the text looks like a link code, consume it and bind phone→user."""
    # Accept "link ABC123" or bare "ABC123"
    m = re.search(r"\b([A-HJ-NP-Z2-9]{6})\b", text.upper())
    if not m:
        return None
    code = m.group(1)

    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TOKENS_TABLE} WHERE token = ?", (code,)
        ).fetchone()
        if not row:
            return None
        if row["used_at"]:
            return {"error": "This code has already been used."}
        try:
            exp = datetime.fromisoformat(row["expires_at"])
        except Exception:
            exp = now_utc_naive() - timedelta(seconds=1)
        if now_utc_naive() > exp:
            return {"error": "This link code has expired. Generate a new one from Settings."}

        now = _now_iso()
        # Bind phone → user. If another phone was already linked to this user,
        # replace it so users can move to a new phone.
        existing = conn.execute(
            f"SELECT phone FROM {ACCOUNTS_TABLE} WHERE phone = ?",
            (phone,),
        ).fetchone()
        if existing:
            conn.execute(
                f"UPDATE {ACCOUNTS_TABLE} SET user_id = ?, active_business_id = ?, linked_at = ? "
                f"WHERE phone = ?",
                (row["user_id"], row["business_id"], now, phone),
            )
        else:
            conn.execute(
                f"INSERT INTO {ACCOUNTS_TABLE} (phone, user_id, active_business_id, linked_at, messages_count) "
                f"VALUES (?,?,?,?,0)",
                (phone, row["user_id"], row["business_id"], now),
            )
        conn.execute(
            f"UPDATE {TOKENS_TABLE} SET used_at = ? WHERE token = ?",
            (now, code),
        )
        conn.commit()
    finally:
        conn.close()
    return {"linked": True, "user_id": row["user_id"], "business_id": row["business_id"]}


# ── Account CRUD for the UI ──────────────────────────────────────────────────
def get_account_for_user(user_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {ACCOUNTS_TABLE} WHERE user_id = ? LIMIT 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def unlink_account(user_id: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(f"DELETE FROM {ACCOUNTS_TABLE} WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def _get_account_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {ACCOUNTS_TABLE} WHERE phone = ?", (phone,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def _bump_message_counter(phone: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {ACCOUNTS_TABLE} SET messages_count = messages_count + 1, last_message_at = ? "
            f"WHERE phone = ?",
            (_now_iso(), phone),
        )
        conn.commit()
    finally:
        conn.close()


# ── Rate limit + dedup ───────────────────────────────────────────────────────
def _rate_limit_ok(phone: str) -> bool:
    now = time.time()
    q = _RATE_LIMIT[phone]
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    if len(q) >= MSGS_PER_WINDOW:
        return False
    q.append(now)
    return True


def _is_duplicate(message_id: str) -> bool:
    """Drop duplicate deliveries from the bridge. Keep a small LRU."""
    if not message_id:
        return False
    now = time.time()
    # Prune entries older than 10 minutes
    for mid in list(_DEDUP.keys()):
        if now - _DEDUP[mid] > 600:
            _DEDUP.pop(mid, None)
    if message_id in _DEDUP:
        return True
    _DEDUP[message_id] = now
    return False


# ── Business-switch helper ───────────────────────────────────────────────────
def _switch_business(phone: str, user_id: str, name_query: str) -> str:
    from api.businesses import list_user_businesses
    name_query = (name_query or "").strip().lower()
    if not name_query:
        businesses = list_user_businesses(user_id)
        return ("Your businesses:\n" +
                "\n".join(f"• {b['name']}" for b in businesses) +
                "\n\nReply with `/business <name>` to switch.")
    match = None
    for b in list_user_businesses(user_id):
        if name_query in (b.get("name", "") or "").lower():
            match = b
            break
    if not match:
        return f"No business matching '{name_query}'. Text `/business` to see the list."
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {ACCOUNTS_TABLE} SET active_business_id = ? WHERE phone = ?",
            (match["id"], phone),
        )
        conn.commit()
    finally:
        conn.close()
    return f"Switched to *{match['name']}*. What do you need?"


# ── Reply formatting for WhatsApp ────────────────────────────────────────────
def _format_reply(agent_result: Dict[str, Any]) -> str:
    """Compose a WhatsApp-friendly reply text from the agent's output."""
    answer = (agent_result.get("answer") or "").strip()
    if not answer:
        answer = "(no response)"

    parts = [answer]

    tool_calls = agent_result.get("tool_calls") or []
    # Summarize any tool calls that happened
    succeeded = [tc for tc in tool_calls if not tc.get("pending_approval") and not tc.get("error")]
    queued = [tc for tc in tool_calls if tc.get("pending_approval")]
    failed = [tc for tc in tool_calls if tc.get("error")]

    if queued:
        parts.append("")
        parts.append(f"⏸ {len(queued)} action{'s' if len(queued) != 1 else ''} queued for approval on the web UI.")
    if failed:
        parts.append("")
        parts.append(f"⚠️ {len(failed)} tool call{'s' if len(failed) != 1 else ''} failed.")

    # WhatsApp messages have a 4096 char cap; stay comfortably below.
    full = "\n".join(parts).strip()
    if len(full) > 3900:
        full = full[:3850] + "\n\n…(truncated — full answer on the web UI)"
    return full


def _detect_attachments(agent_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Find file paths in tool results that should be sent as WhatsApp attachments.

    Supports: invoice PDFs, generated documents (docx/pdf), report PDFs.
    Returns a list of {path, filename, mime_type}.
    """
    attachments: List[Dict[str, str]] = []
    seen_paths: set = set()

    for tc in agent_result.get("tool_calls") or []:
        # Look in the result preview — lightweight check
        preview = (tc.get("result_preview") or "") + " " + str(tc.get("args", {}))

        # Scan for path-like strings we generated ourselves
        path_patterns = [
            r"(outputs[\\/]invoices[\\/][A-Za-z0-9_\-.]+\.pdf)",
            r"(outputs[\\/]documents[\\/][^\s'\"]+\.(?:docx|pdf))",
            r"(outputs[\\/]reports[\\/][A-Za-z0-9_\-.]+\.pdf)",
        ]
        for pat in path_patterns:
            for match in re.findall(pat, preview):
                p = match if isinstance(match, str) else match[0]
                if p in seen_paths:
                    continue
                seen_paths.add(p)
                # Resolve absolute
                from config.settings import OUTPUTS_DIR
                root = Path(OUTPUTS_DIR).parent
                absolute = (root / p).resolve() if not Path(p).is_absolute() else Path(p)
                if not absolute.is_file():
                    continue
                # Stay inside outputs/ for safety
                try:
                    absolute.relative_to(Path(OUTPUTS_DIR).resolve())
                except ValueError:
                    continue
                lower = absolute.suffix.lower()
                mime = (
                    "application/pdf" if lower == ".pdf"
                    else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    if lower == ".docx"
                    else "application/octet-stream"
                )
                attachments.append({
                    "path": str(absolute),
                    "filename": absolute.name,
                    "mime_type": mime,
                })
                if len(attachments) >= 3:  # cap
                    return attachments
    return attachments


# ── Main inbound handler ─────────────────────────────────────────────────────
def handle_inbound(phone: str, text: str, message_id: str = "") -> Dict[str, Any]:
    """
    Process a WhatsApp message and return a reply payload for the bridge.

    Reply shape: {"text": "...", "attachments": [{path, filename, mime_type}], "silent": false}
    If "silent" is true, the bridge should not send anything.
    """
    phone = _normalize_phone(phone)
    text = (text or "").strip()

    if _is_duplicate(message_id):
        return {"text": "", "attachments": [], "silent": True}
    if not phone:
        return {"text": "Couldn't identify your number — please try again.", "attachments": []}
    if not text:
        return {"text": "I got an empty message. Try `help` to see what I can do.", "attachments": []}

    if not _rate_limit_ok(phone):
        return {"text": "You're sending messages too quickly. Try again in a minute.", "attachments": []}

    account = _get_account_by_phone(phone)

    # ── Unlinked phone flow ─────────────────────────────────────────────────
    if not account:
        link = _consume_link_code(phone, text)
        if link and link.get("linked"):
            from api.auth import get_user_by_id
            from api.businesses import get_business
            user = get_user_by_id(link["user_id"])
            biz = get_business(link["business_id"]) or {}
            _bump_message_counter(phone)
            return {
                "text": (f"✅ Linked to *{user.get('name', 'your account')}* — "
                         f"business *{biz.get('name', '?')}*. "
                         f"Ask me anything!\n\n"
                         f"Try:\n"
                         f"• `tasks today`\n"
                         f"• `generate a sales report`\n"
                         f"• `/business` to switch business"),
                "attachments": [],
            }
        if link and link.get("error"):
            return {"text": link["error"], "attachments": []}

        return {
            "text": (
                "Hi 👋 — this number isn't linked to a NexusAgent account.\n\n"
                "Open NexusAgent in your browser, go to *Settings → WhatsApp*, "
                "click *Generate link code*, then text the 6-character code back here."
            ),
            "attachments": [],
        }

    # ── Linked phone: built-in commands ────────────────────────────────────
    user_id = account["user_id"]
    active_biz = account.get("active_business_id")

    _bump_message_counter(phone)

    lowered = text.lower().strip()
    if lowered in ("help", "/help", "?"):
        return {"text": (
            "I'm your NexusAgent assistant. A few things I can do:\n\n"
            "• *tasks today* — what's on your plate\n"
            "• *pipeline* — deal stages + totals\n"
            "• *generate proposal for Acme* — creates a document\n"
            "• *send a reminder email to john@example.com about ...* — drafts it for approval\n"
            "• `/business` — list/switch businesses\n"
            "• `/unlink` — disconnect this phone\n"
        ), "attachments": []}

    if lowered == "/unlink":
        unlink_account(user_id)
        return {"text": "Unlinked. You won't get replies from me until you link again.", "attachments": []}

    if lowered.startswith("/business"):
        rest = text[len("/business"):].strip()
        return {"text": _switch_business(phone, user_id, rest), "attachments": []}

    # ── Route to the agent ────────────────────────────────────────────────
    if not active_biz:
        from api.businesses import list_user_businesses
        businesses = list_user_businesses(user_id)
        if not businesses:
            return {"text": "You don't belong to any business yet. Set one up in the web UI first.", "attachments": []}
        active_biz = businesses[0]["id"]
        conn = _get_conn()
        try:
            conn.execute(
                f"UPDATE {ACCOUNTS_TABLE} SET active_business_id = ? WHERE phone = ?",
                (active_biz, phone),
            )
            conn.commit()
        finally:
            conn.close()

    from api.auth import get_user_by_id
    from api.businesses import get_business, get_member_role
    from agents.agent_loop import run_agent

    user = get_user_by_id(user_id)
    if not user:
        return {"text": "Your linked account is no longer active. Please relink.", "attachments": []}

    biz = get_business(active_biz)
    if not biz:
        # Business got deleted while phone was linked to it; pick another
        unlink_account(user_id)
        return {"text": "The linked business no longer exists. Please relink from Settings.", "attachments": []}

    role = get_member_role(active_biz, user_id) or "member"

    try:
        result = run_agent(
            messages=[{"role": "user", "content": text}],
            business_id=active_biz,
            business_name=biz.get("name", "this business"),
            user_id=user_id,
            user_name=user.get("name") or user.get("email", "User"),
            user_role=role,
        )
    except Exception as e:
        logger.exception("[WhatsApp] Agent run failed")
        return {"text": f"Sorry — something broke while processing that: {e}", "attachments": []}

    reply_text = _format_reply(result)
    attachments = _detect_attachments(result)

    # Persist the exchange to the audit trail
    try:
        from memory.audit_logger import log_tool_call
        log_tool_call(
            tool="whatsapp.inbound",
            input_summary=text[:300],
            output_summary=reply_text[:300],
            approved=True,
            success=True,
            business_id=active_biz,
            user_id=user_id,
        )
    except Exception:
        pass

    return {"text": reply_text, "attachments": attachments}
