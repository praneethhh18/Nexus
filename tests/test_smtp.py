"""
SMTP credentials store + send path — contract tests.

The actual SMTP server is mocked. Coverage:
  - Round-trip: save + read returns config without password
  - Password is encrypted at rest (raw plaintext never appears in DB)
  - Update-without-password preserves the existing one
  - Decryption tolerates a rotated fernet key (returns empty, no crash)
  - Multi-tenant: biz-a's config can't be read from biz-b
  - Send path raises SmtpSendError when no config exists
  - Test connection wraps auth failures into a clean message
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
from unittest.mock import MagicMock, patch

import pytest


def _fresh(db_path: str, secret: str = "test-secret-do-not-use-in-prod"):
    os.environ["DB_PATH"] = db_path
    os.environ["NEXUS_SECRET_KEY"] = secret
    from config import settings as _s
    importlib.reload(_s)
    from api import smtp_credentials as _sc
    importlib.reload(_sc)
    return _sc


def _payload(**over):
    base = {
        "host": "smtp.example.com", "port": 587,
        "username": "outbound@example.com", "password": "super-secret",
        "from_email": "hello@example.com", "from_name": "Nexus Demo",
        "use_tls": True,
    }
    base.update(over)
    return base


# ── Round-trip ──────────────────────────────────────────────────────────────
def test_save_then_read_excludes_password():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        sc.save_config("biz-a", "u-1", **_payload())

        cfg = sc.get_config("biz-a")
        assert cfg is not None
        assert cfg["host"] == "smtp.example.com"
        assert cfg["from_email"] == "hello@example.com"
        assert cfg["use_tls"] is True
        assert "password" not in cfg
        assert "password_enc" not in cfg


def test_password_encrypted_at_rest():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        sc.save_config("biz-a", "u-1", **_payload(password="plaintext-canary"))

        # Verify the raw plaintext doesn't appear in the DB.
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT password_enc FROM nexus_workspace_smtp WHERE business_id = ?",
                ("biz-a",),
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert "plaintext-canary" not in row[0]
        assert len(row[0]) > 30  # fernet tokens are nontrivially long

        # And include_password decrypts back to original.
        cfg = sc.get_config("biz-a", include_password=True)
        assert cfg["password"] == "plaintext-canary"


def test_update_without_password_preserves_existing():
    """A common UX pattern: edit host/port without re-typing the password."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        sc.save_config("biz-a", "u-1", **_payload(password="orig-pw"))

        # Update with empty password.
        sc.save_config("biz-a", "u-1", **_payload(password="", host="smtp.new.example.com"))

        cfg = sc.get_config("biz-a", include_password=True)
        assert cfg["host"] == "smtp.new.example.com"
        assert cfg["password"] == "orig-pw"


def test_first_save_requires_password():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        with pytest.raises(ValueError):
            sc.save_config("biz-a", "u-1", **_payload(password=""))


def test_rotated_fernet_key_tolerated():
    """If NEXUS_SECRET_KEY changes (e.g. backup restored to a new host),
    decryption must fail gracefully — empty password, no exception."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db, secret="key-one")
        sc.save_config("biz-a", "u-1", **_payload(password="will-be-lost"))

        # Reload with a different secret to simulate rotation.
        sc2 = _fresh(db, secret="key-two")
        cfg = sc2.get_config("biz-a", include_password=True)
        assert cfg is not None
        assert cfg["password"] == ""  # honest empty, no crash


# ── Multi-tenant isolation ──────────────────────────────────────────────────
def test_tenant_a_cannot_read_tenant_b():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        sc.save_config("biz-a", "u-a", **_payload(host="smtp.a.example.com"))
        sc.save_config("biz-b", "u-b", **_payload(host="smtp.b.example.com"))

        a = sc.get_config("biz-a")
        b = sc.get_config("biz-b")
        assert a["host"] == "smtp.a.example.com"
        assert b["host"] == "smtp.b.example.com"
        assert sc.get_config("biz-c") is None


def test_delete_removes_only_this_tenant():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        sc.save_config("biz-a", "u-a", **_payload())
        sc.save_config("biz-b", "u-b", **_payload())

        assert sc.delete_config("biz-a") is True
        assert sc.get_config("biz-a") is None
        assert sc.get_config("biz-b") is not None


# ── Send path ───────────────────────────────────────────────────────────────
def test_send_without_config_raises():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        with pytest.raises(sc.SmtpSendError):
            sc.send_email("biz-a", to="x@example.com", subject="hi", body="msg")


def test_send_uses_stored_credentials():
    """sendmail is called with the from/to/body we stored. Mock the SMTP
    server so we don't actually talk to anything."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        sc.save_config("biz-a", "u-a", **_payload(
            from_email="hello@example.com", username="outbound@example.com",
            password="abc123",
        ))

        fake_server = MagicMock()
        # Make the context-manager work.
        fake_server.__enter__ = lambda self: self
        fake_server.__exit__ = lambda self, *a: False

        with patch.object(sc, "_connect", return_value=fake_server):
            r = sc.send_email("biz-a", to="dest@example.com",
                              subject="hello", body="body text")

        assert r["ok"] is True
        fake_server.login.assert_called_once_with("outbound@example.com", "abc123")
        sendmail_args = fake_server.sendmail.call_args
        assert sendmail_args.args[0] == "hello@example.com"
        assert sendmail_args.args[1] == ["dest@example.com"]
        assert "hello" in sendmail_args.args[2]


def test_send_auth_error_is_clean():
    """SMTPAuthenticationError must surface as a user-facing message —
    no traceback, no credentials."""
    import smtplib

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)
        sc.save_config("biz-a", "u-a", **_payload())

        fake_server = MagicMock()
        fake_server.__enter__ = lambda self: self
        fake_server.__exit__ = lambda self, *a: False
        fake_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad creds")

        with patch.object(sc, "_connect", return_value=fake_server):
            with pytest.raises(sc.SmtpSendError) as exc:
                sc.send_email("biz-a", to="d@example.com", subject="s", body="b")

        msg = str(exc.value).lower()
        assert "authentication" in msg
        assert "super-secret" not in msg  # password mustn't leak


# ── Test connection ─────────────────────────────────────────────────────────
def test_test_connection_returns_clean_error_on_auth_fail():
    import smtplib

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sc = _fresh(db)

        fake_server = MagicMock()
        fake_server.__enter__ = lambda self: self
        fake_server.__exit__ = lambda self, *a: False
        fake_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"nope")

        with patch.object(sc, "_connect", return_value=fake_server):
            r = sc.test_connection({
                "host": "smtp.example.com", "port": 587,
                "username": "u", "password": "p", "use_tls": True,
            })
        assert r["ok"] is False
        assert "authentication" in r["error"].lower()
