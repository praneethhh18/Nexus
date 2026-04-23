"""
Google Calendar integration — per-user OAuth2 flow and read-only event listing.

Security / isolation:
- Each user has at most one connection. Tokens are stored per user_id, and
  every event listing is scoped to the connected user (not the business).
- Refresh tokens are obfuscated at rest with a local key (not strong
  encryption, but avoids casual leaks). For production, replace _obfuscate
  with a proper KMS-backed encryption.
- The OAuth `state` parameter is a signed JWT that includes the user_id so we
  can't be tricked into binding another user's Google account to ours.

To enable:
1. Create an OAuth 2.0 Client ID in Google Cloud Console (Web application).
2. Authorized redirect URI: http://localhost:8000/api/calendar/oauth/callback
   (and whatever matches APP deployments).
3. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET in .env.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import HTTPException
from loguru import logger

from config.settings import DB_PATH

CAL_TABLE = "nexus_calendar_connections"

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_EVENTS_URL_TMPL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "email",
    "profile",
]

# ── State-token signing (HMAC) ───────────────────────────────────────────────
def _state_secret() -> bytes:
    from api.auth import SECRET_KEY
    return SECRET_KEY.encode()


def _sign_state(user_id: str) -> str:
    nonce = secrets.token_urlsafe(12)
    payload = f"{user_id}|{int(time.time())}|{nonce}"
    sig = hmac.new(_state_secret(), payload.encode(), hashlib.sha256).hexdigest()[:20]
    raw = f"{payload}|{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _verify_state(state: str, max_age_seconds: int = 900) -> str:
    try:
        padding = "=" * (-len(state) % 4)
        raw = base64.urlsafe_b64decode(state + padding).decode()
        user_id, ts_str, nonce, sig = raw.rsplit("|", 3)
        ts = int(ts_str)
    except Exception:
        raise HTTPException(400, "Invalid OAuth state")
    payload = f"{user_id}|{ts}|{nonce}"
    expected = hmac.new(_state_secret(), payload.encode(), hashlib.sha256).hexdigest()[:20]
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(400, "OAuth state signature mismatch")
    if time.time() - ts > max_age_seconds:
        raise HTTPException(400, "OAuth state expired")
    return user_id


# ── Refresh-token obfuscation at rest ────────────────────────────────────────
def _obfuscate_key() -> bytes:
    """Derive a per-install key from the JWT secret. Deterministic and fast."""
    from api.auth import SECRET_KEY
    return hashlib.sha256(SECRET_KEY.encode() + b"|calendar").digest()


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _pack_token(refresh_token: str) -> str:
    if not refresh_token:
        return ""
    return base64.b64encode(_xor(refresh_token.encode(), _obfuscate_key())).decode()


def _unpack_token(stored: str) -> str:
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
    CREATE TABLE IF NOT EXISTS {CAL_TABLE} (
        user_id TEXT PRIMARY KEY,
        provider TEXT DEFAULT 'google',
        account_email TEXT,
        refresh_token_enc TEXT,
        access_token TEXT,
        access_token_expires_at TEXT,
        connected_at TEXT,
        updated_at TEXT
    )""")
    conn.commit()
    return conn


def _creds_or_raise() -> tuple[str, str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "http://localhost:8000/api/calendar/oauth/callback",
    ).strip()
    if not client_id or not client_secret:
        raise HTTPException(
            501,
            "Google Calendar is not configured. Set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET in .env to enable.",
        )
    return client_id, client_secret, redirect_uri


# ── OAuth flow ───────────────────────────────────────────────────────────────
def build_authorize_url(user_id: str) -> str:
    from urllib.parse import urlencode
    client_id, _, redirect_uri = _creds_or_raise()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",  # ensures refresh_token is returned
        "state": _sign_state(user_id),
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
    import requests
    client_id, client_secret, _ = _creds_or_raise()
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=10)
    if resp.status_code != 200:
        logger.warning(f"[Calendar] Token exchange failed: {resp.status_code} {resp.text[:200]}")
        raise HTTPException(400, f"Google token exchange failed: {resp.text[:200]}")
    return resp.json()


def _fetch_account_email(access_token: str) -> str:
    import requests
    try:
        r = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("email", "") or ""
    except Exception:
        pass
    return ""


def save_connection(user_id: str, tokens: Dict[str, Any]) -> Dict[str, Any]:
    refresh_token = tokens.get("refresh_token", "")
    access_token = tokens.get("access_token", "")
    expires_in = int(tokens.get("expires_in", 3600))
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in - 30)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    account_email = _fetch_account_email(access_token)

    # If we're refreshing and Google didn't send a new refresh_token, keep the old one.
    conn = _get_conn()
    try:
        existing = conn.execute(
            f"SELECT refresh_token_enc FROM {CAL_TABLE} WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        stored_refresh = _pack_token(refresh_token) if refresh_token else (existing[0] if existing else "")
        if existing:
            conn.execute(
                f"UPDATE {CAL_TABLE} SET account_email = ?, refresh_token_enc = ?, "
                f"access_token = ?, access_token_expires_at = ?, updated_at = ? "
                f"WHERE user_id = ?",
                (account_email, stored_refresh, access_token, expires_at, now, user_id),
            )
        else:
            conn.execute(
                f"INSERT INTO {CAL_TABLE} (user_id, provider, account_email, refresh_token_enc, "
                f"access_token, access_token_expires_at, connected_at, updated_at) "
                f"VALUES (?,?,?,?,?,?,?,?)",
                (user_id, "google", account_email, stored_refresh, access_token, expires_at, now, now),
            )
        conn.commit()
    finally:
        conn.close()

    return {"account_email": account_email, "connected_at": now}


def get_connection(user_id: str) -> Optional[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT user_id, provider, account_email, access_token_expires_at, connected_at, updated_at "
            f"FROM {CAL_TABLE} WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def disconnect(user_id: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(f"DELETE FROM {CAL_TABLE} WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def _get_valid_access_token(user_id: str) -> str:
    """Return a non-expired access_token, refreshing via refresh_token if needed."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT access_token, access_token_expires_at, refresh_token_enc FROM {CAL_TABLE} WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(400, "Google Calendar is not connected for this user")

    # Still valid?
    try:
        expires = datetime.fromisoformat(row["access_token_expires_at"])
    except Exception:
        expires = datetime.now(timezone.utc) - timedelta(seconds=1)
    if row["access_token"] and expires > datetime.now(timezone.utc):
        return row["access_token"]

    # Refresh
    refresh_token = _unpack_token(row["refresh_token_enc"] or "")
    if not refresh_token:
        raise HTTPException(401, "Google refresh token unavailable; reconnect your calendar")

    import requests
    client_id, client_secret, _ = _creds_or_raise()
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    resp = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=10)
    if resp.status_code != 200:
        logger.warning(f"[Calendar] Refresh failed: {resp.status_code} {resp.text[:200]}")
        raise HTTPException(401, "Could not refresh Google token; please reconnect")
    tokens = resp.json()
    save_connection(user_id, tokens)
    return tokens.get("access_token", "")


# ── Event listing ────────────────────────────────────────────────────────────
def list_upcoming_events(user_id: str, days_ahead: int = 14, max_results: int = 20) -> List[Dict[str, Any]]:
    import requests
    access_token = _get_valid_access_token(user_id)
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=max(1, min(days_ahead, 90)))
    url = GOOGLE_EVENTS_URL_TMPL.format(calendar_id="primary")
    params = {
        "timeMin": now.isoformat(),
        "timeMax": end.isoformat(),
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": max(1, min(max_results, 100)),
    }
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
        timeout=10,
    )
    if resp.status_code != 200:
        logger.warning(f"[Calendar] Events fetch failed: {resp.status_code} {resp.text[:200]}")
        raise HTTPException(resp.status_code, f"Calendar API error: {resp.text[:200]}")

    raw_events = resp.json().get("items", [])
    result = []
    for ev in raw_events:
        start = ev.get("start", {})
        end_t = ev.get("end", {})
        result.append({
            "id": ev.get("id"),
            "summary": ev.get("summary", "(no title)"),
            "description": (ev.get("description") or "")[:500],
            "location": ev.get("location", ""),
            "start": start.get("dateTime") or start.get("date"),
            "end": end_t.get("dateTime") or end_t.get("date"),
            "all_day": bool(start.get("date") and not start.get("dateTime")),
            "hangout_link": ev.get("hangoutLink", ""),
            "html_link": ev.get("htmlLink", ""),
            "attendees_count": len(ev.get("attendees", []) or []),
            "organizer_email": (ev.get("organizer") or {}).get("email", ""),
        })
    return result
