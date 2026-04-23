"""
Email triage agent — per-business IMAP inbox poller.

For each unread message:
  1. Fetch subject + sender + plain-text body (truncated).
  2. Ask the LLM to classify (lead | invoice | support | internal | noise)
     and extract key fields (sender intent, urgency, suggested action).
  3. Auto-log a CRM interaction if the sender matches a known contact.
  4. If classification suggests a reply, draft one and queue it on the
     approval queue (NEVER auto-send).
  5. Mark the message as Seen so we don't re-process it.

Security:
- Credentials (IMAP host + user + app password) are stored per business in
  the nexus_email_accounts table. The password is obfuscated at rest with the
  per-install key (same approach as calendar refresh tokens).
- Opt-in per business. Disabled by default.
- The LLM only sees the subject, sender, and first ~2000 chars of the body.
"""
from __future__ import annotations

import base64
import email
import hashlib
import imaplib
import json
import re
import sqlite3
from datetime import datetime, timezone
from email.header import decode_header
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from loguru import logger

from config.settings import DB_PATH

ACCOUNTS_TABLE = "nexus_email_accounts"
LOG_TABLE = "nexus_email_triage_log"

MAX_BODY_CHARS = 2000
MAX_MESSAGES_PER_RUN = 20


# ── Obfuscation (reuse the calendar approach) ────────────────────────────────
def _obfuscate_key() -> bytes:
    from api.auth import SECRET_KEY
    return hashlib.sha256(SECRET_KEY.encode() + b"|email").digest()


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _pack(secret: str) -> str:
    if not secret:
        return ""
    return base64.b64encode(_xor(secret.encode(), _obfuscate_key())).decode()


def _unpack(stored: str) -> str:
    if not stored:
        return ""
    try:
        return _xor(base64.b64decode(stored), _obfuscate_key()).decode()
    except Exception:
        return ""


# ── Database ─────────────────────────────────────────────────────────────────
def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {ACCOUNTS_TABLE} (
        business_id TEXT PRIMARY KEY,
        imap_host TEXT,
        imap_port INTEGER DEFAULT 993,
        username TEXT,
        password_enc TEXT,
        folder TEXT DEFAULT 'INBOX',
        enabled INTEGER DEFAULT 0,
        auto_draft_reply INTEGER DEFAULT 1,
        connected_at TEXT,
        updated_at TEXT
    )""")
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        message_uid TEXT,
        sender TEXT,
        subject TEXT,
        classification TEXT,
        urgency TEXT,
        summary TEXT,
        suggested_action TEXT,
        interaction_id TEXT,
        approval_id TEXT,
        processed_at TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_email_log_biz ON {LOG_TABLE}(business_id, processed_at)")
    conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_email_uid ON {LOG_TABLE}(business_id, message_uid)")
    conn.commit()
    return conn


# ── Account management ──────────────────────────────────────────────────────
def save_account(business_id: str, imap_host: str, username: str,
                 password: str, imap_port: int = 993, folder: str = "INBOX",
                 enabled: bool = True, auto_draft_reply: bool = True) -> Dict[str, Any]:
    if not imap_host or not username or not password:
        raise HTTPException(400, "imap_host, username, password are all required")
    now = datetime.utcnow().isoformat()
    conn = _get_conn()
    try:
        row = conn.execute(f"SELECT business_id FROM {ACCOUNTS_TABLE} WHERE business_id = ?",
                           (business_id,)).fetchone()
        enc = _pack(password)
        if row:
            conn.execute(
                f"UPDATE {ACCOUNTS_TABLE} SET imap_host=?, imap_port=?, username=?, password_enc=?, "
                f"folder=?, enabled=?, auto_draft_reply=?, updated_at=? WHERE business_id=?",
                (imap_host, imap_port, username, enc, folder, int(enabled), int(auto_draft_reply), now, business_id),
            )
        else:
            conn.execute(
                f"INSERT INTO {ACCOUNTS_TABLE} "
                f"(business_id, imap_host, imap_port, username, password_enc, folder, enabled, "
                f"auto_draft_reply, connected_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (business_id, imap_host, imap_port, username, enc, folder, int(enabled),
                 int(auto_draft_reply), now, now),
            )
        conn.commit()
    finally:
        conn.close()
    return get_account(business_id) or {}


def get_account(business_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT business_id, imap_host, imap_port, username, folder, enabled, "
            f"auto_draft_reply, connected_at, updated_at FROM {ACCOUNTS_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def _load_full_account(business_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {ACCOUNTS_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    d = dict(row)
    d["password"] = _unpack(d.pop("password_enc") or "")
    return d


def disconnect_account(business_id: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(f"DELETE FROM {ACCOUNTS_TABLE} WHERE business_id = ?", (business_id,))
        conn.commit()
    finally:
        conn.close()


# ── IMAP fetch ───────────────────────────────────────────────────────────────
def _decode(s) -> str:
    if not s:
        return ""
    try:
        parts = decode_header(s)
        out = []
        for text, charset in parts:
            if isinstance(text, bytes):
                try:
                    out.append(text.decode(charset or "utf-8", errors="replace"))
                except Exception:
                    out.append(text.decode("utf-8", errors="replace"))
            else:
                out.append(str(text))
        return "".join(out)
    except Exception:
        return str(s)


def _extract_body(msg) -> str:
    """Pick the best plain-text body from the message."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ctype == "text/plain" and "attachment" not in disp.lower():
                try:
                    charset = part.get_content_charset() or "utf-8"
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    continue
    else:
        try:
            charset = msg.get_content_charset() or "utf-8"
            return msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception:
            return ""
    return ""


def _fetch_unread(account: Dict[str, Any], max_messages: int) -> List[Dict[str, Any]]:
    host = account["imap_host"]
    port = int(account.get("imap_port", 993))
    username = account["username"]
    password = account["password"]
    folder = account.get("folder", "INBOX")

    conn = imaplib.IMAP4_SSL(host, port)
    try:
        conn.login(username, password)
        conn.select(folder)
        typ, data = conn.search(None, "UNSEEN")
        if typ != "OK":
            return []
        ids = data[0].split()
        ids = ids[-max_messages:]  # most recent first-in / last-out
        messages = []
        for mid in ids:
            typ, msg_data = conn.fetch(mid, "(RFC822 UID)")
            if typ != "OK":
                continue
            uid = None
            raw = None
            for part in msg_data:
                if isinstance(part, tuple):
                    raw = part[1]
                    # Parse UID from the first element string
                    first = part[0].decode(errors="replace") if isinstance(part[0], bytes) else str(part[0])
                    m = re.search(r"UID (\d+)", first)
                    if m:
                        uid = m.group(1)
            if not raw:
                continue
            try:
                msg = email.message_from_bytes(raw)
            except Exception:
                continue
            messages.append({
                "uid": uid or mid.decode(errors="replace"),
                "from": _decode(msg.get("From", "")),
                "subject": _decode(msg.get("Subject", "")),
                "date": msg.get("Date", ""),
                "body": _extract_body(msg)[:MAX_BODY_CHARS],
                "message_id": msg.get("Message-ID", ""),
            })
    finally:
        try: conn.close()
        except Exception: pass
        try: conn.logout()
        except Exception: pass
    return messages


# ── Classification via LLM ──────────────────────────────────────────────────
_CLASSIFY_PROMPT = """You are classifying incoming emails for a business. \
Return JSON only.

Email:
FROM: {sender}
SUBJECT: {subject}
BODY:
{body}

Return exactly one JSON object with these fields:
  "classification": one of "lead", "invoice", "support", "internal", "noise"
  "urgency": one of "low", "medium", "high"
  "summary": one sentence
  "suggested_action": one of "reply", "schedule_call", "log_only", "ignore"
  "draft_reply": if suggested_action=="reply", a polite professional reply (max 120 words); else ""

Be concise and accurate. Return ONLY the JSON object, no fences."""


def _classify(sender: str, subject: str, body: str) -> Dict[str, Any]:
    from config.llm_provider import invoke as llm_invoke
    prompt = _CLASSIFY_PROMPT.format(sender=sender[:200], subject=subject[:200], body=body[:MAX_BODY_CHARS])
    try:
        # Email bodies contain sender PII and confidential content — stay local.
        raw = llm_invoke(prompt, system="You classify business emails.",
                         max_tokens=500, temperature=0.0, fast=True, sensitive=True)
    except Exception as e:
        return {"classification": "noise", "urgency": "low", "summary": f"LLM error: {e}",
                "suggested_action": "ignore", "draft_reply": ""}

    # Extract JSON
    try:
        stripped = raw.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?|```$", "", stripped, flags=re.MULTILINE).strip()
        data = json.loads(stripped)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return {"classification": "noise", "urgency": "low", "summary": raw[:200],
                    "suggested_action": "ignore", "draft_reply": ""}
        try:
            data = json.loads(m.group(0))
        except Exception:
            return {"classification": "noise", "urgency": "low", "summary": raw[:200],
                    "suggested_action": "ignore", "draft_reply": ""}

    # Clamp + default
    return {
        "classification": data.get("classification", "noise"),
        "urgency": data.get("urgency", "low"),
        "summary": (data.get("summary") or "")[:500],
        "suggested_action": data.get("suggested_action", "ignore"),
        "draft_reply": (data.get("draft_reply") or "")[:2000],
    }


def _sender_email(raw_from: str) -> str:
    m = re.search(r"<([^>]+)>", raw_from)
    if m:
        return m.group(1).strip().lower()
    return raw_from.strip().lower()


# ── Main run ─────────────────────────────────────────────────────────────────
def run_for_business(business_id: str) -> Dict[str, Any]:
    account = _load_full_account(business_id)
    if not account:
        return {"skipped": "no_account", "processed": 0}
    if not account.get("enabled"):
        return {"skipped": "disabled", "processed": 0}

    try:
        messages = _fetch_unread(account, MAX_MESSAGES_PER_RUN)
    except imaplib.IMAP4.error as e:
        logger.warning(f"[EmailTriage] IMAP auth/fetch failed for {business_id}: {e}")
        return {"error": f"IMAP error: {e}", "processed": 0}
    except Exception as e:
        logger.warning(f"[EmailTriage] Fetch failed for {business_id}: {e}")
        return {"error": str(e), "processed": 0}

    if not messages:
        return {"processed": 0, "messages": []}

    from api import crm as _crm
    from agents import approval_queue
    import uuid as _uuid

    processed_records = []
    conn = _get_conn()
    try:
        for m in messages:
            uid = str(m.get("uid") or m.get("message_id") or _uuid.uuid4().hex)
            # Dedup — skip if we already processed this UID
            existing = conn.execute(
                f"SELECT id FROM {LOG_TABLE} WHERE business_id = ? AND message_uid = ?",
                (business_id, uid),
            ).fetchone()
            if existing:
                continue

            sender = m.get("from", "")
            subject = m.get("subject", "")
            body = m.get("body", "")
            sender_email = _sender_email(sender)

            classification = _classify(sender, subject, body)

            # Find CRM contact by email (business-scoped)
            interaction_id = None
            if sender_email:
                try:
                    matches = _crm.list_contacts(business_id, search=sender_email, limit=3)
                    for c in matches:
                        if (c.get("email") or "").strip().lower() == sender_email:
                            try:
                                inter = _crm.create_interaction(business_id, account["username"], {
                                    "type": "email",
                                    "subject": subject[:200],
                                    "summary": f"[{classification['classification']}/{classification['urgency']}] "
                                               f"{classification['summary']}\n\n{body[:500]}",
                                    "contact_id": c["id"],
                                    "company_id": c.get("company_id"),
                                })
                                interaction_id = inter["id"]
                            except Exception:
                                pass
                            break
                except Exception:
                    pass

            # Draft reply if recommended and user opted in
            approval_id = None
            if (classification["suggested_action"] == "reply"
                and classification.get("draft_reply")
                and account.get("auto_draft_reply")
                and sender_email):
                try:
                    action = approval_queue.queue_action(
                        business_id=business_id,
                        user_id=account["username"],
                        tool_name="send_email",
                        summary=f"Reply draft to {sender_email}: {subject[:80]}",
                        args={
                            "to": sender_email,
                            "subject": f"Re: {subject}" if not subject.lower().startswith("re:") else subject,
                            "body": classification["draft_reply"],
                        },
                        ttl_hours=72,
                    )
                    approval_id = action["id"]
                except Exception as e:
                    logger.warning(f"[EmailTriage] Could not queue reply: {e}")

            conn.execute(
                f"INSERT INTO {LOG_TABLE} "
                f"(id, business_id, message_uid, sender, subject, classification, urgency, "
                f"summary, suggested_action, interaction_id, approval_id, processed_at) "
                f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    f"et-{_uuid.uuid4().hex[:10]}", business_id, uid,
                    sender[:200], subject[:300],
                    classification["classification"], classification["urgency"],
                    classification["summary"], classification["suggested_action"],
                    interaction_id, approval_id, datetime.utcnow().isoformat(),
                ),
            )
            processed_records.append({
                "uid": uid, "sender": sender, "subject": subject,
                **classification,
                "interaction_id": interaction_id, "approval_id": approval_id,
            })
        conn.commit()
    finally:
        conn.close()

    # In-app notification summary
    try:
        from api import notifications as _notifs
        pending_replies = sum(1 for r in processed_records if r.get("approval_id"))
        if processed_records:
            _notifs.push(
                title=f"Triaged {len(processed_records)} email{'s' if len(processed_records) != 1 else ''}",
                message=(f"{pending_replies} draft repl{'ies' if pending_replies != 1 else 'y'} waiting "
                         f"for approval." if pending_replies else "No replies needed."),
                severity="info",
                type="email-triage",
                business_id=business_id,
            )
    except Exception:
        pass

    return {"processed": len(processed_records), "messages": processed_records}


def get_recent_log(business_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT * FROM {LOG_TABLE} WHERE business_id = ? "
            f"ORDER BY processed_at DESC LIMIT ?",
            (business_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
