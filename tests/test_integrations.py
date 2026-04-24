"""Tests for the integration framework + webhook signature + voice language."""
from __future__ import annotations

import hashlib
import hmac
import importlib
import os
import tempfile


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import integrations as _int
    importlib.reload(_int)
    return _int


# ── Provider catalog ────────────────────────────────────────────────────────
def test_provider_catalog_has_expected_keys():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        keys = {p["key"] for p in ints.list_providers()}
        assert "gmail" in keys
        assert "slack" in keys
        assert "google_calendar" in keys
        assert "razorpay" in keys
        assert "webhook_inbound" in keys


def test_provider_catalog_includes_status():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        providers = ints.list_providers()
        statuses = {p["status"] for p in providers}
        # Catalog must contain at least one of each so the UI can test every branch
        assert "available" in statuses
        assert "needs_oauth" in statuses


# ── Connect / disconnect ────────────────────────────────────────────────────
def test_connect_persists_config():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        row = ints.connect("biz-1", "slack", {"bot_token": "xoxb-test"})
        assert row["provider"] == "slack"
        assert row["status"] == "connected"
        # Secret should be scrubbed in default listing
        conns = ints.list_connections("biz-1")
        assert len(conns) == 1
        assert conns[0]["config"].get("bot_token") == "********"


def test_unknown_provider_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            ints.connect("biz-1", "totally_fake", {})


def test_coming_soon_provider_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        # shopify is currently 'coming_soon'
        import pytest
        with pytest.raises(ValueError):
            ints.connect("biz-1", "shopify", {})


def test_reconnect_updates_in_place():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        a = ints.connect("biz-1", "discord", {"webhook_url": "a"})
        b = ints.connect("biz-1", "discord", {"webhook_url": "b"})
        assert a["id"] == b["id"]
        unscrubbed = ints.get_connection("biz-1", "discord", scrub=False)
        assert unscrubbed["config"]["webhook_url"] == "b"


def test_disconnect_removes_row():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        ints.connect("biz-1", "telegram", {"bot_token": "t"})
        ints.disconnect("biz-1", "telegram")
        assert ints.get_connection("biz-1", "telegram") is None


def test_connections_scoped_per_business():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        ints.connect("biz-a", "slack", {"bot_token": "A"})
        ints.connect("biz-b", "slack", {"bot_token": "B"})
        assert len(ints.list_connections("biz-a")) == 1
        assert len(ints.list_connections("biz-b")) == 1


# ── Health ──────────────────────────────────────────────────────────────────
def test_record_health_updates_row():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        ints.connect("biz-1", "discord", {"webhook_url": "x"})
        ints.record_health("biz-1", "discord", ok=False, error="nope")
        row = ints.get_connection("biz-1", "discord")
        assert row["last_health_ok"] == 0
        assert "nope" in (row["last_health_error"] or "")


def test_ping_unconnected_returns_not_connected():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        r = ints.ping("biz-1", "slack")
        assert r["ok"] is False
        assert "Not connected" in r["error"]


def test_ping_with_custom_adapter_fires():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        ints.connect("biz-1", "telegram", {"bot_token": "t"})
        called = {}
        def fake(config):
            called["config"] = config
            return {"ok": True}
        ints.register_ping("telegram", fake)
        r = ints.ping("biz-1", "telegram")
        assert r["ok"] is True
        assert called["config"]["bot_token"] == "t"


# ── Webhook signature verification ──────────────────────────────────────────
def test_webhook_signature_valid():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        secret = "s3cret"
        payload = b'{"event": "test"}'
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert ints.verify_webhook_signature(secret, payload, sig) is True


def test_webhook_signature_invalid():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        secret = "s3cret"
        payload = b'{"event": "test"}'
        assert ints.verify_webhook_signature(secret, payload, "wrong") is False
        assert ints.verify_webhook_signature(secret, payload, "") is False
        assert ints.verify_webhook_signature("", payload, "abc") is False


def test_webhook_signature_is_case_insensitive_to_hex_padding():
    with tempfile.TemporaryDirectory() as tmp:
        ints = _fresh(os.path.join(tmp, "nexus.db"))
        secret = "s"
        payload = b"ping"
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        # Whitespace around the hex shouldn't break the compare
        assert ints.verify_webhook_signature(secret, payload, f"  {sig}  ") is True


# ── Voice language param ────────────────────────────────────────────────────
def test_voice_transcribe_accepts_language_param():
    """
    Smoke-check the signature of the underlying transcribe function so we
    don't silently regress its keyword args. We don't run the model here.
    """
    from voice import listener
    import inspect
    sig = inspect.signature(listener._transcribe)
    params = list(sig.parameters.keys())
    assert "wav_path" in params
    assert "language" in params
    # Supported languages registry exists
    assert "hi" in listener.SUPPORTED_LANGUAGES
    assert "en" in listener.SUPPORTED_LANGUAGES
