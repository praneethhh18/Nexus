"""
Security primitives for NexusAgent:
  - TOTP 2FA enrollment, verification, disable, recovery codes
  - Session tracking (JWT jti → session record) with revoke

Storage:
  nexus_user_2fa        — one row per user who has 2FA enrolled
  nexus_sessions        — one row per issued access token (jti, device, ip, etc.)
  nexus_recovery_codes  — one-time backup codes, hashed

All secrets (TOTP seed, recovery codes) are obfuscated at rest using the same
per-install key pattern we use for calendar/email creds — it's not a KMS,
but stops casual dump-and-read attacks on the DB file.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import datetime
from typing import List, Dict, Any

import pyotp
from fastapi import HTTPException
from loguru import logger

from config.db import get_conn
from utils.timez import now_iso, now_utc_naive

TWOFA_TABLE = "nexus_user_2fa"
RECOVERY_TABLE = "nexus_recovery_codes"
SESSIONS_TABLE = "nexus_sessions"

RECOVERY_CODE_COUNT = 10
RECOVERY_CODE_LEN = 10  # characters


# ── Obfuscation (same scheme as calendar.py / email_triage.py) ───────────────
def _obfuscate_key() -> bytes:
    from api.auth import SECRET_KEY
    return hashlib.sha256(SECRET_KEY.encode() + b"|2fa").digest()


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


def _hash_code(code: str) -> str:
    """One-way hash for recovery codes. Fast SHA-256 is fine — they're random 60 bits."""
    return hashlib.sha256(code.upper().encode()).hexdigest()


# ── Tables ───────────────────────────────────────────────────────────────────
def _get_conn():
    conn = get_conn()
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {TWOFA_TABLE} (
        user_id TEXT PRIMARY KEY,
        secret_enc TEXT NOT NULL,
        enabled INTEGER DEFAULT 0,
        created_at TEXT,
        enabled_at TEXT
    )""")
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {RECOVERY_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        code_hash TEXT NOT NULL UNIQUE,
        used_at TEXT,
        created_at TEXT NOT NULL
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_recovery_user ON {RECOVERY_TABLE}(user_id, used_at)")
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {SESSIONS_TABLE} (
        jti TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        user_agent TEXT DEFAULT '',
        ip TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        last_seen_at TEXT,
        expires_at TEXT NOT NULL,
        revoked_at TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_sessions_user ON {SESSIONS_TABLE}(user_id, revoked_at)")
    conn.commit()
    return conn


def _now() -> str:
    return now_iso()


# ═══════════════════════════════════════════════════════════════════════════════
#  2FA — TOTP
# ═══════════════════════════════════════════════════════════════════════════════
def get_2fa_state(user_id: str) -> Dict[str, Any]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT enabled, created_at, enabled_at FROM {TWOFA_TABLE} WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        # Count unused recovery codes
        cnt_row = conn.execute(
            f"SELECT COUNT(*) FROM {RECOVERY_TABLE} WHERE user_id = ? AND used_at IS NULL",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"enabled": False, "enrolled": False}
    return {
        "enrolled": True,
        "enabled": bool(row["enabled"]),
        "created_at": row["created_at"],
        "enabled_at": row["enabled_at"],
        "recovery_codes_remaining": int(cnt_row[0] or 0),
    }


def start_2fa_enrollment(user_id: str, user_email: str) -> Dict[str, Any]:
    """
    Generate a fresh TOTP secret (pending) and return the provisioning URI
    + QR-code data URL. The secret is stored as *disabled* until the user
    verifies a code from their authenticator.
    """
    secret = pyotp.random_base32()
    now = _now()
    conn = _get_conn()
    try:
        row = conn.execute(f"SELECT enabled FROM {TWOFA_TABLE} WHERE user_id = ?", (user_id,)).fetchone()
        if row and row[0]:
            raise HTTPException(400, "2FA is already enabled — disable it first to regenerate")
        if row:
            conn.execute(
                f"UPDATE {TWOFA_TABLE} SET secret_enc = ?, enabled = 0, created_at = ?, enabled_at = NULL WHERE user_id = ?",
                (_pack(secret), now, user_id),
            )
        else:
            conn.execute(
                f"INSERT INTO {TWOFA_TABLE} (user_id, secret_enc, enabled, created_at) VALUES (?,?,0,?)",
                (user_id, _pack(secret), now),
            )
        conn.commit()
    finally:
        conn.close()

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user_email, issuer_name="NexusAgent")
    qr_data_url = _qr_data_url(uri)
    return {
        "secret": secret,
        "otpauth_url": uri,
        "qr_data_url": qr_data_url,
        "message": "Scan the QR in Google Authenticator / Authy / 1Password, then verify with the 6-digit code.",
    }


def _qr_data_url(text: str) -> str:
    """Render a QR code as a data URL using a tiny pure-Python QR library if available."""
    try:
        import qrcode
        import io
        img = qrcode.make(text)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        # qrcode not installed — return empty string, UI can fall back to showing the URL
        return ""


def verify_and_enable_2fa(user_id: str, code: str) -> List[str]:
    """
    Called after the user types a code from their authenticator. If it checks
    out, 2FA becomes active for real and we generate + return recovery codes.
    Recovery codes are shown ONCE.
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT secret_enc, enabled FROM {TWOFA_TABLE} WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            raise HTTPException(400, "Start enrollment first")
        secret = _unpack(row["secret_enc"])
        if not secret or not pyotp.TOTP(secret).verify(code.strip(), valid_window=1):
            raise HTTPException(400, "Invalid code — try again")

        # Mark enabled
        conn.execute(
            f"UPDATE {TWOFA_TABLE} SET enabled = 1, enabled_at = ? WHERE user_id = ?",
            (_now(), user_id),
        )
        # Wipe old recovery codes + generate fresh
        conn.execute(f"DELETE FROM {RECOVERY_TABLE} WHERE user_id = ?", (user_id,))
        codes = _generate_recovery_codes(user_id, conn)
        conn.commit()
    finally:
        conn.close()
    return codes


def _generate_recovery_codes(user_id: str, conn: sqlite3.Connection) -> List[str]:
    """Generate fresh codes, store their hashes, return the plaintexts ONCE."""
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    codes = []
    for _ in range(RECOVERY_CODE_COUNT):
        code = "-".join(
            "".join(secrets.choice(alphabet) for _ in range(5)) for _ in range(2)
        )  # e.g. ABCDE-12345
        codes.append(code)
        conn.execute(
            f"INSERT INTO {RECOVERY_TABLE} (user_id, code_hash, created_at) VALUES (?,?,?)",
            (user_id, _hash_code(code), _now()),
        )
    return codes


def verify_login_factor(user_id: str, code: str) -> bool:
    """
    Called at login. Accepts either a TOTP code OR an unused recovery code.
    Recovery codes are consumed on use.
    """
    if not code:
        return False
    code = code.strip().upper().replace(" ", "")

    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT secret_enc, enabled FROM {TWOFA_TABLE} WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row or not row["enabled"]:
            return True  # 2FA not enabled — no factor needed

        # Try TOTP first
        if len(code) == 6 and code.isdigit():
            secret = _unpack(row["secret_enc"])
            if secret and pyotp.TOTP(secret).verify(code, valid_window=1):
                return True

        # Try recovery code
        normalized = code if "-" in code else code  # accept with or without dash
        h = _hash_code(normalized)
        rec = conn.execute(
            f"SELECT id FROM {RECOVERY_TABLE} WHERE user_id = ? AND code_hash = ? AND used_at IS NULL",
            (user_id, h),
        ).fetchone()
        if rec:
            conn.execute(
                f"UPDATE {RECOVERY_TABLE} SET used_at = ? WHERE id = ?",
                (_now(), rec["id"]),
            )
            conn.commit()
            logger.warning(f"[2FA] Recovery code used for user {user_id}")
            return True
    finally:
        conn.close()
    return False


def is_2fa_required(user_id: str) -> bool:
    conn = _get_conn()
    try:
        row = conn.execute(
            f"SELECT enabled FROM {TWOFA_TABLE} WHERE user_id = ?", (user_id,),
        ).fetchone()
    finally:
        conn.close()
    return bool(row and row[0])


def disable_2fa(user_id: str, current_code: str) -> None:
    """Disabling requires a valid TOTP or recovery code — proves possession."""
    if not verify_login_factor(user_id, current_code):
        raise HTTPException(400, "Invalid code")
    conn = _get_conn()
    try:
        conn.execute(f"DELETE FROM {TWOFA_TABLE} WHERE user_id = ?", (user_id,))
        conn.execute(f"DELETE FROM {RECOVERY_TABLE} WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()
    logger.info(f"[2FA] Disabled for user {user_id}")


def regenerate_recovery_codes(user_id: str, current_code: str) -> List[str]:
    if not verify_login_factor(user_id, current_code):
        raise HTTPException(400, "Invalid code")
    conn = _get_conn()
    try:
        conn.execute(f"DELETE FROM {RECOVERY_TABLE} WHERE user_id = ?", (user_id,))
        codes = _generate_recovery_codes(user_id, conn)
        conn.commit()
    finally:
        conn.close()
    return codes


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSIONS
# ═══════════════════════════════════════════════════════════════════════════════
def record_session(
    jti: str, user_id: str, user_agent: str, ip: str, expires_at: datetime,
) -> None:
    conn = _get_conn()
    try:
        # Portable upsert: ON CONFLICT works on SQLite 3.24+ and Postgres.
        # jti is the primary key — collisions are vanishingly rare but possible
        # if a token is re-issued; refreshing the row is the right behavior.
        conn.execute(
            f"INSERT INTO {SESSIONS_TABLE} "
            f"(jti, user_id, user_agent, ip, created_at, last_seen_at, expires_at) "
            f"VALUES (?,?,?,?,?,?,?) "
            f"ON CONFLICT (jti) DO UPDATE SET "
            f"  user_id = EXCLUDED.user_id, user_agent = EXCLUDED.user_agent, "
            f"  ip = EXCLUDED.ip, last_seen_at = EXCLUDED.last_seen_at, "
            f"  expires_at = EXCLUDED.expires_at",
            (jti, user_id, (user_agent or "")[:300], (ip or "")[:60],
             _now(), _now(), expires_at.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def touch_session(jti: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {SESSIONS_TABLE} SET last_seen_at = ? WHERE jti = ? AND revoked_at IS NULL",
            (_now(), jti),
        )
        conn.commit()
    finally:
        conn.close()


def is_session_valid(jti: str) -> bool:
    """Used by auth middleware to reject revoked JWTs even if they're not expired yet."""
    if not jti:
        return True  # legacy tokens without jti still work (backwards compat)
    conn = _get_conn()
    try:
        row = conn.execute(
            f"SELECT revoked_at, expires_at FROM {SESSIONS_TABLE} WHERE jti = ?",
            (jti,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return True  # no record (e.g. session created before sessions table existed)
    revoked, expires = row[0], row[1]
    if revoked:
        return False
    try:
        if now_utc_naive() > datetime.fromisoformat(expires):
            return False
    except Exception:
        pass
    return True


def list_sessions(user_id: str) -> List[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT jti, user_agent, ip, created_at, last_seen_at, expires_at, revoked_at "
            f"FROM {SESSIONS_TABLE} WHERE user_id = ? ORDER BY last_seen_at DESC LIMIT 50",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def revoke_session(user_id: str, jti: str) -> None:
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {SESSIONS_TABLE} SET revoked_at = ? "
            f"WHERE jti = ? AND user_id = ? AND revoked_at IS NULL",
            (_now(), jti, user_id),
        )
        conn.commit()
    finally:
        conn.close()


def revoke_all_other_sessions(user_id: str, current_jti: str) -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            f"UPDATE {SESSIONS_TABLE} SET revoked_at = ? "
            f"WHERE user_id = ? AND jti != ? AND revoked_at IS NULL",
            (_now(), user_id, current_jti),
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
