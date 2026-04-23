"""
NexusAgent Auth — JWT-based authentication with bcrypt password hashing.
Supports signup, login, token refresh, and role-based access control.

Security notes:
- JWT_SECRET must be set in .env for production. If missing, a persistent random
  secret is generated once and stored at data/.jwt_secret (never committed).
- Login attempts are throttled per (email, ip) to slow down brute force.
"""
from __future__ import annotations

import os
import re
import secrets
import sqlite3
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

import bcrypt
import hashlib
import jwt
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from config.settings import DB_PATH

# ── JWT secret — persisted so tokens survive restarts ─────────────────────────
def _load_or_create_secret() -> str:
    env_secret = os.getenv("JWT_SECRET", "").strip()
    if env_secret and len(env_secret) >= 32:
        return env_secret
    if env_secret:
        logger.warning("[Auth] JWT_SECRET is shorter than 32 chars — using a generated secret instead")

    secret_path = Path(DB_PATH).parent / ".jwt_secret"
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    if secret_path.exists():
        return secret_path.read_text(encoding="utf-8").strip()
    secret = secrets.token_urlsafe(48)
    secret_path.write_text(secret, encoding="utf-8")
    try:
        os.chmod(secret_path, 0o600)
    except OSError:
        pass  # Windows may not support chmod
    logger.warning(
        "[Auth] No JWT_SECRET set in .env — generated one at data/.jwt_secret. "
        "For production, set JWT_SECRET in your .env."
    )
    return secret


SECRET_KEY = _load_or_create_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Brute-force throttle: max 8 failed attempts per (email, ip) in 15 min
_FAILED_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
_THROTTLE_WINDOW_SEC = 15 * 60
_THROTTLE_MAX = 8

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MIN_PASSWORD_LEN = 8

security = HTTPBearer(auto_error=False)


# ── Database ──────────────────────────────────────────────────────────────────
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS nexus_users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TEXT,
        last_login TEXT,
        is_active INTEGER DEFAULT 1
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS nexus_password_resets (
        token_hash TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used_at TEXT
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pw_reset_user ON nexus_password_resets(user_id)")
    conn.commit()
    return conn


def _hash_token(token: str) -> str:
    """Hash a reset token with SHA-256 — we never store the raw token."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Password Hashing ─────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


# ── Input validation ─────────────────────────────────────────────────────────
def _validate_email(email: str) -> str:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Invalid email format")
    if len(email) > 200:
        raise HTTPException(400, "Email too long")
    return email


def _validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LEN:
        raise HTTPException(400, f"Password must be at least {MIN_PASSWORD_LEN} characters")
    if len(password) > 256:
        raise HTTPException(400, "Password too long")


def _validate_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise HTTPException(400, "Name is required")
    if len(name) > 80:
        raise HTTPException(400, "Name too long (max 80 chars)")
    return name


# ── JWT Tokens ────────────────────────────────────────────────────────────────
def create_access_token(user_id: str, email: str, role: str) -> str:
    jti = uuid.uuid4().hex
    exp = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": exp,
        "iat": datetime.utcnow(),
        "jti": jti,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


# ── Brute-force throttle ─────────────────────────────────────────────────────
def _throttle_key(email: str, request: Optional[Request]) -> str:
    ip = "unknown"
    if request and request.client:
        ip = request.client.host
    return f"{email.lower()}::{ip}"


def _check_throttle(email: str, request: Optional[Request]) -> None:
    key = _throttle_key(email, request)
    now = time.time()
    attempts = [t for t in _FAILED_ATTEMPTS[key] if now - t < _THROTTLE_WINDOW_SEC]
    _FAILED_ATTEMPTS[key] = attempts
    if len(attempts) >= _THROTTLE_MAX:
        raise HTTPException(
            429,
            f"Too many failed attempts. Try again in {_THROTTLE_WINDOW_SEC // 60} minutes.",
        )


def _record_failure(email: str, request: Optional[Request]) -> None:
    key = _throttle_key(email, request)
    _FAILED_ATTEMPTS[key].append(time.time())


def _clear_failures(email: str, request: Optional[Request]) -> None:
    key = _throttle_key(email, request)
    _FAILED_ATTEMPTS.pop(key, None)


# ── User CRUD ─────────────────────────────────────────────────────────────────
def create_user(email: str, name: str, password: str, role: str = "user") -> dict:
    email = _validate_email(email)
    name = _validate_name(name)
    _validate_password(password)

    conn = _get_conn()
    try:
        existing = conn.execute("SELECT id FROM nexus_users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(409, "Email already registered")

        user_id = str(uuid.uuid4())[:12]
        pw_hash = hash_password(password)
        now = datetime.now().isoformat()

        conn.execute(
            "INSERT INTO nexus_users (id, email, name, password_hash, role, created_at) VALUES (?,?,?,?,?,?)",
            (user_id, email, name, pw_hash, role, now),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(f"[Auth] User created: {email} ({role})")
    return {"id": user_id, "email": email, "name": name, "role": role}


def authenticate_user(email: str, password: str, request: Optional[Request] = None) -> Optional[dict]:
    email = email.strip().lower()
    _check_throttle(email, request)

    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM nexus_users WHERE email = ? AND is_active = 1", (email,)
        ).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            _record_failure(email, request)
            return None

        conn.execute(
            "UPDATE nexus_users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), row["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    _clear_failures(email, request)
    return {"id": row["id"], "email": row["email"], "name": row["name"], "role": row["role"]}


def request_password_reset(email: str) -> Optional[tuple[str, dict]]:
    """
    Create a one-time password reset token for this email.
    Returns (raw_token, user_dict) if the email matches a user, else None.
    Callers should treat a None return as "email not found" but NEVER reveal
    that to the requester (to avoid email enumeration).
    """
    email = email.strip().lower()
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT id, email, name FROM nexus_users WHERE email = ? AND is_active = 1",
            (email,),
        ).fetchone()
        if not row:
            return None

        token = secrets.token_urlsafe(32)
        token_hash = _hash_token(token)
        now = datetime.utcnow()
        expires = now + timedelta(hours=1)

        # Invalidate any previous unused tokens for this user
        conn.execute(
            "UPDATE nexus_password_resets SET used_at = ? WHERE user_id = ? AND used_at IS NULL",
            (now.isoformat(), row["id"]),
        )
        conn.execute(
            "INSERT INTO nexus_password_resets (token_hash, user_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token_hash, row["id"], now.isoformat(), expires.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(f"[Auth] Password reset token issued for {email}")
    return token, {"id": row["id"], "email": row["email"], "name": row["name"]}


def consume_password_reset(token: str, new_password: str) -> None:
    """Verify the token, set the new password, and mark the token used."""
    _validate_password(new_password)
    token_hash = _hash_token(token)

    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT user_id, expires_at, used_at FROM nexus_password_resets WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        if not row:
            raise HTTPException(400, "Invalid or expired reset link")
        if row["used_at"]:
            raise HTTPException(400, "This reset link has already been used")
        try:
            expires = datetime.fromisoformat(row["expires_at"])
        except Exception:
            expires = datetime.utcnow()
        if datetime.utcnow() > expires:
            raise HTTPException(400, "This reset link has expired")

        new_hash = hash_password(new_password)
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE nexus_users SET password_hash = ? WHERE id = ?",
            (new_hash, row["user_id"]),
        )
        conn.execute(
            "UPDATE nexus_password_resets SET used_at = ? WHERE token_hash = ?",
            (now, token_hash),
        )
        # Also invalidate any other outstanding reset tokens for this user
        conn.execute(
            "UPDATE nexus_password_resets SET used_at = ? "
            "WHERE user_id = ? AND used_at IS NULL",
            (now, row["user_id"]),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(f"[Auth] Password reset for user {row['user_id']}")


def change_password(user_id: str, current_password: str, new_password: str) -> None:
    """Change a user's password after verifying the current one."""
    _validate_password(new_password)
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT password_hash FROM nexus_users WHERE id = ? AND is_active = 1",
            (user_id,),
        ).fetchone()
        if not row or not verify_password(current_password, row["password_hash"]):
            raise HTTPException(401, "Current password is incorrect")
        new_hash = hash_password(new_password)
        conn.execute(
            "UPDATE nexus_users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info(f"[Auth] Password changed for user {user_id}")


def get_user_by_id(user_id: str) -> Optional[dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT id, email, name, role, created_at, last_login FROM nexus_users WHERE id = ? AND is_active = 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def list_users() -> list:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, email, name, role, created_at, last_login, is_active FROM nexus_users ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


# ── Auth Dependencies ─────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI dependency — extracts and validates the user from the JWT."""
    if not credentials:
        raise HTTPException(401, "Authentication required")

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token type")

    # Session revocation check (only if the token carries a jti — legacy tokens
    # issued before session tracking still work)
    jti = payload.get("jti")
    if jti:
        try:
            from api.security import is_session_valid, touch_session
            if not is_session_valid(jti):
                raise HTTPException(401, "Session has been revoked")
            touch_session(jti)
        except HTTPException:
            raise
        except Exception:
            # Don't block auth if the session table itself has a problem
            pass

    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(401, "User not found or deactivated")
    user["_jti"] = jti  # expose to downstream endpoints that want to revoke-other
    return user


async def get_current_context(
    request: Request,
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Full request context: resolves the user AND the active business.

    Business is selected via the X-Business-Id header. If absent, falls back
    to the user's first business. The server verifies membership every time.
    """
    from api.businesses import (
        assert_member,
        list_user_businesses,
        ensure_business_for_user,
    )

    business_id = request.headers.get("X-Business-Id", "").strip()
    if not business_id:
        businesses = list_user_businesses(user["id"])
        if not businesses:
            # Lazy-create a default business for this user
            business_id = ensure_business_for_user(user["id"], user["name"])
        else:
            business_id = businesses[0]["id"]

    role = assert_member(business_id, user["id"])
    return {
        "user": user,
        "business_id": business_id,
        "business_role": role,
    }


def require_role(role: str):
    """Dependency factory — require a specific global user role (e.g. 'admin')."""
    async def check(user: dict = Depends(get_current_user)):
        if user["role"] not in (role, "admin"):
            raise HTTPException(403, f"Requires '{role}' role")
        return user
    return check


def require_business_role(*roles: str):
    """Dependency factory — require a specific role within the current business."""
    async def check(ctx: dict = Depends(get_current_context)):
        if ctx["business_role"] not in roles and ctx["business_role"] != "owner":
            raise HTTPException(403, f"Requires one of: {', '.join(roles)}")
        return ctx
    return check


# ── Bootstrap ─────────────────────────────────────────────────────────────────
def ensure_default_admin():
    """
    Create a default admin account if no users exist, and ensure at least one business.
    """
    conn = _get_conn()
    try:
        count = conn.execute("SELECT COUNT(*) FROM nexus_users").fetchone()[0]
    finally:
        conn.close()

    if count == 0:
        admin = create_user(
            email="admin@nexusagent.local",
            name="Admin",
            password="admin1234",  # min length satisfied; user should change immediately
            role="admin",
        )
        logger.warning(
            "[Auth] Default admin created: admin@nexusagent.local / admin1234 — "
            "CHANGE THIS PASSWORD IMMEDIATELY in production."
        )
        # Give the admin a starter business
        from api.businesses import ensure_business_for_user
        ensure_business_for_user(admin["id"], admin["name"])
