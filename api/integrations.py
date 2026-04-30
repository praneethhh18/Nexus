"""
Integration framework — the plumbing that every future 3rd-party connector
will ride on.

Each integration is declared in `PROVIDERS` below with its metadata (name,
category, auth type, docs URL, connect hints) and an availability flag. A
connected integration stores encrypted-at-rest config JSON in
`nexus_integrations` alongside a health status + last-checked timestamp.

Design principles:
  * Provider availability is shipped — whether a provider is "real" (OAuth
    app registered, adapter implemented) or "stub" is baked into the
    registry. Stubs still let users see what's coming and reserve a row.
  * Config is opaque to the framework — adapters read/write their own keys
    inside config_json. This module only owns storage + CRUD.
  * Webhooks land on `/api/webhooks/{provider}` and are dispatched by name
    so adapters stay decoupled. Signature verification is the adapter's job.

The secrets inside config_json are left unencrypted at rest on local-first
deployments; a future hardening pass can swap the getter/setter with a
symmetric encrypt/decrypt under an env-supplied key.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


from config.db import get_conn
from utils.timez import now_iso

TABLE = "nexus_integrations"

# ── Provider catalog ────────────────────────────────────────────────────────
# Each entry is metadata only. Adapters (read/send/sync logic) live in their
# own modules under integrations/<provider>.py — out of scope for this file.
# `status`:
#   "available"    — adapter implemented + can be connected today
#   "needs_oauth"  — requires the user-provided OAuth app client ID/secret
#   "coming_soon"  — metadata listed but no adapter yet
PROVIDERS: Dict[str, Dict] = {
    # Communication
    "gmail": {
        "name": "Gmail",
        "category": "communication",
        "description": "Read, label and send Gmail messages; Iris triages your inbox automatically.",
        "auth_type": "oauth2",
        "docs_url": "https://developers.google.com/gmail/api",
        "icon": "📧",
        "status": "needs_oauth",
    },
    "outlook": {
        "name": "Outlook / Microsoft 365",
        "category": "communication",
        "description": "Read + send Outlook mail and pull calendar events.",
        "auth_type": "oauth2",
        "docs_url": "https://learn.microsoft.com/en-us/graph/auth/",
        "icon": "📮",
        "status": "needs_oauth",
    },
    "slack": {
        "name": "Slack",
        "category": "communication",
        "description": "Two-way: post agent outputs, receive messages, approve drafts from Slack.",
        "auth_type": "oauth2",
        "docs_url": "https://api.slack.com/authentication",
        "icon": "💬",
        "status": "needs_oauth",
    },
    "whatsapp_business": {
        "name": "WhatsApp Business",
        "category": "communication",
        "description": "Receive and reply to WhatsApp messages from your inbox.",
        "auth_type": "api_key",
        "docs_url": "https://developers.facebook.com/docs/whatsapp",
        "icon": "🟢",
        "status": "needs_oauth",
    },
    "telegram": {
        "name": "Telegram Bot",
        "category": "communication",
        "description": "NexusAgent as a Telegram bot for mobile access.",
        "auth_type": "bot_token",
        "docs_url": "https://core.telegram.org/bots",
        "icon": "✈️",
        "status": "available",
    },
    "discord": {
        "name": "Discord",
        "category": "communication",
        "description": "Post agent alerts and reports to a Discord channel via webhook.",
        "auth_type": "webhook",
        "docs_url": "https://discord.com/developers/docs/resources/webhook",
        "icon": "🎮",
        "status": "available",
    },

    # Calendar
    "google_calendar": {
        "name": "Google Calendar",
        "category": "calendar",
        "description": "Sage uses your events for meeting prep; tasks can become calendar entries.",
        "auth_type": "oauth2",
        "docs_url": "https://developers.google.com/calendar",
        "icon": "📅",
        "status": "needs_oauth",
    },
    "outlook_calendar": {
        "name": "Outlook Calendar",
        "category": "calendar",
        "description": "Same as Google Calendar, for Microsoft 365 users.",
        "auth_type": "oauth2",
        "docs_url": "https://learn.microsoft.com/en-us/graph/api/resources/calendar",
        "icon": "🗓️",
        "status": "needs_oauth",
    },
    "calendly": {
        "name": "Calendly",
        "category": "calendar",
        "description": "Booked meetings auto-create a contact + deal in your CRM.",
        "auth_type": "api_key",
        "docs_url": "https://developer.calendly.com/",
        "icon": "🔖",
        "status": "coming_soon",
    },

    # Business tools
    "zoho_crm": {
        "name": "Zoho CRM",
        "category": "business",
        "description": "Two-way sync of contacts and deals.",
        "auth_type": "oauth2",
        "docs_url": "https://www.zoho.com/crm/developer/",
        "icon": "🟠",
        "status": "needs_oauth",
    },
    "tally": {
        "name": "Tally",
        "category": "business",
        "description": "Indian accounting sync — push invoices to Tally books.",
        "auth_type": "api_key",
        "docs_url": "https://tallysolutions.com/developers/",
        "icon": "🧾",
        "status": "coming_soon",
    },
    "razorpay": {
        "name": "Razorpay",
        "category": "business",
        "description": "See payment status on invoices automatically.",
        "auth_type": "api_key",
        "docs_url": "https://razorpay.com/docs/api/",
        "icon": "💳",
        "status": "needs_oauth",
    },
    "shopify": {
        "name": "Shopify",
        "category": "business",
        "description": "Import orders as sales data for analytics.",
        "auth_type": "oauth2",
        "docs_url": "https://shopify.dev/docs/api",
        "icon": "🛍️",
        "status": "coming_soon",
    },
    "google_sheets": {
        "name": "Google Sheets",
        "category": "business",
        "description": "Two-way sync for any data table.",
        "auth_type": "oauth2",
        "docs_url": "https://developers.google.com/sheets/api",
        "icon": "📊",
        "status": "needs_oauth",
    },
    "notion": {
        "name": "Notion",
        "category": "business",
        "description": "Sync tasks and documents with Notion.",
        "auth_type": "oauth2",
        "docs_url": "https://developers.notion.com/",
        "icon": "📝",
        "status": "needs_oauth",
    },

    # Pipes
    "webhook_inbound": {
        "name": "Inbound Webhook",
        "category": "pipes",
        "description": "Accept any event from any service via a shared-secret URL.",
        "auth_type": "shared_secret",
        "docs_url": "",
        "icon": "🪝",
        "status": "available",
    },
    "zapier": {
        "name": "Zapier / Make",
        "category": "pipes",
        "description": "Connect to 5,000+ apps through Zapier or Make.",
        "auth_type": "webhook",
        "docs_url": "https://zapier.com/apps",
        "icon": "⚡",
        "status": "available",
    },
}


CATEGORY_LABELS: Dict[str, str] = {
    "communication": "Communication",
    "calendar":      "Calendar",
    "business":      "Business tools",
    "pipes":         "Automation / webhooks",
}

# ── Storage ─────────────────────────────────────────────────────────────────
def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id                TEXT PRIMARY KEY,
            business_id       TEXT NOT NULL,
            provider          TEXT NOT NULL,
            status            TEXT NOT NULL DEFAULT 'pending',
            config_json       TEXT NOT NULL DEFAULT '{{}}',
            last_health_at    TEXT,
            last_health_ok    INTEGER,
            last_health_error TEXT,
            connected_at      TEXT NOT NULL,
            updated_at        TEXT NOT NULL,
            UNIQUE (business_id, provider)
        )
    """)
    conn.commit()
    return conn


def _scrub_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Remove obvious secret-looking keys when returning rows to the UI."""
    if not isinstance(config, dict):
        return {}
    SECRET_HINTS = ("secret", "token", "key", "password")
    out: Dict[str, Any] = {}
    for k, v in config.items():
        if any(h in k.lower() for h in SECRET_HINTS):
            out[k] = "********" if v else ""
        else:
            out[k] = v
    return out


def _row_to_dict(row: sqlite3.Row, *, scrub: bool = True) -> Dict:
    d = dict(row)
    try:
        d["config"] = json.loads(d.pop("config_json") or "{}")
    except Exception:
        d["config"] = {}
    if scrub:
        d["config"] = _scrub_config(d["config"])
    d["provider_meta"] = PROVIDERS.get(d["provider"], {
        "name": d["provider"], "category": "other", "status": "coming_soon",
    })
    return d


# ── Public API ──────────────────────────────────────────────────────────────
def list_providers() -> List[Dict]:
    """The marketplace catalog — independent of which are connected."""
    out = []
    for key, meta in PROVIDERS.items():
        out.append({"key": key, **meta})
    return out


def list_connections(business_id: str) -> List[Dict]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ? ORDER BY updated_at DESC",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(r) for r in rows]


def get_connection(business_id: str, provider: str, *, scrub: bool = True) -> Optional[Dict]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ? AND provider = ?",
            (business_id, provider),
        ).fetchone()
    finally:
        conn.close()
    return _row_to_dict(row, scrub=scrub) if row else None


def connect(business_id: str, provider: str, config: Dict[str, Any]) -> Dict:
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    if PROVIDERS[provider].get("status") == "coming_soon":
        raise ValueError(f"{PROVIDERS[provider]['name']} is not yet available")

    now = now_iso()
    conn = _conn()
    try:
        existing = conn.execute(
            f"SELECT id FROM {TABLE} WHERE business_id = ? AND provider = ?",
            (business_id, provider),
        ).fetchone()
        if existing:
            conn.execute(
                f"UPDATE {TABLE} SET config_json = ?, status = 'connected', "
                f"updated_at = ? WHERE id = ?",
                (json.dumps(config or {}), now, existing[0]),
            )
            cid = existing[0]
        else:
            cid = f"int-{uuid.uuid4().hex[:10]}"
            conn.execute(
                f"INSERT INTO {TABLE} (id, business_id, provider, status, "
                f"config_json, connected_at, updated_at) "
                f"VALUES (?, ?, ?, 'connected', ?, ?, ?)",
                (cid, business_id, provider, json.dumps(config or {}), now, now),
            )
        conn.commit()
    finally:
        conn.close()
    return get_connection(business_id, provider)


def disconnect(business_id: str, provider: str) -> None:
    conn = _conn()
    try:
        conn.execute(
            f"DELETE FROM {TABLE} WHERE business_id = ? AND provider = ?",
            (business_id, provider),
        )
        conn.commit()
    finally:
        conn.close()


def record_health(business_id: str, provider: str, ok: bool, error: str = "") -> None:
    """Called by adapters + the ping endpoint to refresh health status."""
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET last_health_at = ?, last_health_ok = ?, "
            f"last_health_error = ?, updated_at = ? "
            f"WHERE business_id = ? AND provider = ?",
            (now_iso(), 1 if ok else 0,
             (error or "")[:400], now_iso(),
             business_id, provider),
        )
        conn.commit()
    finally:
        conn.close()


def ping(business_id: str, provider: str) -> Dict[str, Any]:
    """
    Basic reachability check. Provider-specific adapters can register richer
    ping functions below; otherwise we just verify the row exists.
    """
    row = get_connection(business_id, provider, scrub=False)
    if not row:
        return {"ok": False, "error": "Not connected"}
    fn = _PING_ADAPTERS.get(provider)
    if not fn:
        record_health(business_id, provider, ok=True, error="")
        return {"ok": True, "note": "No custom ping registered; row exists."}
    try:
        result = fn(row.get("config") or {})
        ok = bool(result.get("ok", False))
        record_health(business_id, provider, ok=ok, error=result.get("error", ""))
        return result
    except Exception as e:
        record_health(business_id, provider, ok=False, error=str(e))
        return {"ok": False, "error": str(e)}


# ── Adapter registration ────────────────────────────────────────────────────
# Adapters call `register_ping("slack", fn)` from their own module; the ping
# fn receives the stored config and returns {ok: bool, error?: str, ...}.
_PING_ADAPTERS: Dict[str, Callable[[Dict], Dict]] = {}


def register_ping(provider: str, fn: Callable[[Dict], Dict]) -> None:
    _PING_ADAPTERS[provider] = fn


# ── Webhook signature verification ──────────────────────────────────────────
def verify_webhook_signature(secret: str, payload: bytes, signature: str,
                             scheme: str = "sha256") -> bool:
    """Generic HMAC verification helper — used by the shared webhook route."""
    if not secret or not signature:
        return False
    try:
        expected = hmac.new(secret.encode("utf-8"), payload,
                            getattr(hashlib, scheme)).hexdigest()
    except Exception:
        return False
    # Constant-time compare
    return hmac.compare_digest(expected, signature.strip().lower())
