"""
Per-tenant SMTP configuration store.

Each business workspace can connect its own outbound mail account (Gmail
app password, Mailgun, SendGrid, custom SMTP server, etc.). Configuration
is stored on `nexus_workspace_smtp` and the password is encrypted at rest
using Fernet, with the key derived from a server-level secret.

Why per-tenant: a multi-tenant deployment can't use a single global Gmail
account — you'd be sending all customer emails from `you@yourdomain` and
they'd land in spam. Each customer plugs in their own SMTP creds.

Security notes:
  - Password is never returned to the API; only "configured: true/false".
  - The fernet key is derived from `NEXUS_SECRET_KEY` (env var) so a DB
    snapshot alone is not enough to recover passwords. If the env var
    isn't set, we generate one and persist it to a local key file with
    600 perms so single-machine installs Just Work — but with a clear
    server log warning.
  - SMTP test path uses a short-lived connection; we never log the
    password or full message body.
"""
from __future__ import annotations

import base64
import hashlib
import os
import smtplib
import sqlite3
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger

from config.settings import DB_PATH

SMTP_TABLE = "nexus_workspace_smtp"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Fernet key handling ─────────────────────────────────────────────────────
def _derive_fernet_key(secret: str) -> bytes:
    """Fernet expects a 32-byte url-safe base64-encoded key. We hash an
    arbitrary-length secret to 32 bytes deterministically."""
    h = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(h)


def _resolve_secret() -> str:
    """Resolve the server-level secret. Preference order:
       1. `NEXUS_SECRET_KEY` env var (production / explicit config)
       2. A persistent file at `data/.nexus_smtp_secret` (single-machine
          installs — generated on first use, logged loudly)
    """
    env_secret = os.environ.get("NEXUS_SECRET_KEY", "").strip()
    if env_secret:
        return env_secret

    key_path = Path(DB_PATH).parent / ".nexus_smtp_secret"
    if key_path.exists():
        try:
            return key_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.warning(f"[smtp] couldn't read local secret file: {e}")

    # First-run generation. We log a clear warning so production deployments
    # remember to set NEXUS_SECRET_KEY explicitly (otherwise restoring a
    # backup to a different host would lose access to encrypted creds).
    new_secret = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_text(new_secret, encoding="utf-8")
        try:
            os.chmod(key_path, 0o600)
        except Exception:
            # chmod is a no-op on Windows; that's expected.
            pass
        logger.warning(
            "[smtp] NEXUS_SECRET_KEY env var not set — generated a local "
            f"secret at {key_path}. For production, set NEXUS_SECRET_KEY "
            "explicitly so SMTP creds survive a backup restore."
        )
    except Exception as e:
        logger.error(f"[smtp] couldn't persist generated secret: {e}")
    return new_secret


def _fernet() -> Fernet:
    return Fernet(_derive_fernet_key(_resolve_secret()))


def _encrypt(plain: str) -> str:
    if not plain:
        return ""
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def _decrypt(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # The fernet key changed (env var rotated, secret file deleted, or
        # backup restored to a different host). Surface this as missing
        # creds rather than a server crash — user will need to re-enter.
        logger.error("[smtp] failed to decrypt stored password — fernet key changed?")
        return ""


# ── Storage ─────────────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {SMTP_TABLE} (
            business_id     TEXT PRIMARY KEY,
            host            TEXT NOT NULL,
            port            INTEGER NOT NULL,
            username        TEXT NOT NULL,
            password_enc    TEXT NOT NULL,
            from_email      TEXT NOT NULL,
            from_name       TEXT DEFAULT '',
            use_tls         INTEGER DEFAULT 1,
            updated_at      TEXT NOT NULL,
            updated_by      TEXT
        )
    """)


def get_config(business_id: str, *, include_password: bool = False) -> Optional[Dict]:
    """Return the stored config (without password by default). Returns None
    when no SMTP is configured for this workspace."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        _ensure_table(conn)
        row = conn.execute(
            f"SELECT * FROM {SMTP_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    out = dict(row)
    enc = out.pop("password_enc", "")
    if include_password:
        out["password"] = _decrypt(enc)
    out["use_tls"] = bool(out.get("use_tls", 1))
    return out


def save_config(business_id: str, user_id: str, *, host: str, port: int,
                username: str, password: str, from_email: str,
                from_name: str = "", use_tls: bool = True) -> Dict:
    """Insert or update the workspace SMTP config. Encrypts password
    before storage. Returns the config (without the password)."""
    if not host or not username or not from_email:
        raise ValueError("host, username, and from_email are required")
    if password and len(password) < 4:
        raise ValueError("password too short")
    if not (1 <= int(port) <= 65535):
        raise ValueError("port must be 1..65535")

    conn = _conn()
    try:
        _ensure_table(conn)
        # Preserve the existing password if the caller didn't pass one (UX:
        # editing the host/port without re-typing the password should work).
        existing_pw_enc = ""
        row = conn.execute(
            f"SELECT password_enc FROM {SMTP_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchone()
        if row:
            existing_pw_enc = row[0] or ""

        pw_enc = _encrypt(password) if password else existing_pw_enc
        if not pw_enc:
            raise ValueError("password is required for first-time SMTP setup")

        conn.execute(
            f"""INSERT INTO {SMTP_TABLE}
                (business_id, host, port, username, password_enc, from_email,
                 from_name, use_tls, updated_at, updated_by)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(business_id) DO UPDATE SET
                    host         = excluded.host,
                    port         = excluded.port,
                    username     = excluded.username,
                    password_enc = excluded.password_enc,
                    from_email   = excluded.from_email,
                    from_name    = excluded.from_name,
                    use_tls      = excluded.use_tls,
                    updated_at   = excluded.updated_at,
                    updated_by   = excluded.updated_by""",
            (business_id, host.strip(), int(port), username.strip(), pw_enc,
             from_email.strip(), (from_name or "").strip(),
             1 if use_tls else 0, _now(), user_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_config(business_id, include_password=False)


def delete_config(business_id: str) -> bool:
    conn = _conn()
    try:
        _ensure_table(conn)
        cur = conn.execute(
            f"DELETE FROM {SMTP_TABLE} WHERE business_id = ?",
            (business_id,),
        )
        conn.commit()
    finally:
        conn.close()
    return cur.rowcount > 0


# ── Sending + testing ───────────────────────────────────────────────────────
class SmtpSendError(Exception):
    """Raised when sending fails — the message wraps the underlying error
    in user-readable form (no credentials leak)."""


def _connect(cfg: Dict) -> smtplib.SMTP:
    """Open an SMTP connection. Picks SMTP_SSL on common SSL ports (465),
    plain SMTP + STARTTLS otherwise."""
    host = cfg["host"]
    port = int(cfg["port"])
    if port == 465:
        ctx = ssl.create_default_context()
        return smtplib.SMTP_SSL(host, port, timeout=15, context=ctx)
    server = smtplib.SMTP(host, port, timeout=15)
    server.ehlo()
    if cfg.get("use_tls"):
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
    return server


def test_connection(cfg: Dict) -> Dict:
    """Open a connection + log in, then close. Returns {ok, error}."""
    try:
        with _connect(cfg) as server:
            server.login(cfg["username"], cfg.get("password", ""))
        return {"ok": True, "error": None}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "error": "Authentication failed — check username and password (or app password)."}
    except smtplib.SMTPConnectError as e:
        return {"ok": False, "error": f"Couldn't connect: {e}"}
    except (smtplib.SMTPException, OSError) as e:
        return {"ok": False, "error": f"SMTP error: {e}"}
    except Exception as e:
        # Catchall — never leak the password or full traceback.
        logger.warning(f"[smtp] test connection failed unexpectedly: {type(e).__name__}")
        return {"ok": False, "error": f"Unexpected error: {type(e).__name__}"}


def send_email(business_id: str, *, to: str, subject: str, body: str,
               cc: Optional[str] = None, reply_to: Optional[str] = None) -> Dict:
    """Send an email via the workspace's SMTP config. Raises SmtpSendError
    on failure with a user-facing message. Never echoes the password."""
    cfg = get_config(business_id, include_password=True)
    if not cfg:
        raise SmtpSendError("No SMTP configured for this workspace. Settings → Email.")
    if not cfg.get("password"):
        raise SmtpSendError("SMTP password missing — re-enter it in Settings → Email.")

    msg = MIMEMultipart()
    sender_name = cfg.get("from_name") or ""
    msg["From"] = f"{sender_name} <{cfg['from_email']}>" if sender_name else cfg["from_email"]
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(body, "plain", "utf-8"))

    rcpts = [to] + ([cc] if cc else [])
    try:
        with _connect(cfg) as server:
            server.login(cfg["username"], cfg["password"])
            server.sendmail(cfg["from_email"], rcpts, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        raise SmtpSendError("Authentication failed — check the SMTP username/password.")
    except smtplib.SMTPRecipientsRefused:
        raise SmtpSendError(f"Recipient refused: {to}")
    except (smtplib.SMTPException, OSError) as e:
        raise SmtpSendError(f"SMTP error: {e}")
    except Exception as e:
        logger.error(f"[smtp] send failed unexpectedly: {type(e).__name__}: {e}")
        raise SmtpSendError(f"Unexpected error while sending: {type(e).__name__}")

    return {"ok": True, "to": to, "subject": subject, "sent_at": _now()}
