"""Tests for config/privacy.py — the data-leakage guard for cloud LLM calls."""
from __future__ import annotations

import importlib
import os
from pathlib import Path


def _fresh_privacy(**env):
    """Reload privacy with a fresh env so module-level flags pick up the override."""
    for k, v in env.items():
        os.environ[k] = v
    from config import privacy
    return importlib.reload(privacy)


def test_redact_replaces_common_pii():
    privacy = _fresh_privacy(REDACT_PII="true")
    original = "Contact john.doe@acme.com or call +91 98765 43210. Card 4111 1111 1111 1111."
    redacted, mapping = privacy.redact(original)
    assert "john.doe@acme.com" not in redacted
    assert "4111 1111 1111 1111" not in redacted
    assert "[EMAIL_1]" in redacted
    assert mapping["[EMAIL_1]"] == "john.doe@acme.com"


def test_redact_is_reversible():
    privacy = _fresh_privacy(REDACT_PII="true")
    original = "Email me at a@b.com about order 1234-5678-9012-3456."
    redacted, mapping = privacy.redact(original)
    restored = privacy.restore(redacted, mapping)
    assert restored == original


def test_same_value_gets_same_token():
    """Repeated PII values must map to the same token so the LLM can reason about them."""
    privacy = _fresh_privacy(REDACT_PII="true")
    text = "Ping a@b.com, then a@b.com again, and c@d.com."
    redacted, mapping = privacy.redact(text)
    # a@b.com appears twice with the same token; c@d.com gets a different one
    assert redacted.count("[EMAIL_1]") == 2
    assert "[EMAIL_2]" in redacted
    assert len(mapping) == 2


def test_secrets_are_redacted():
    privacy = _fresh_privacy(REDACT_PII="true")
    text = "api_key=sk-abcdef1234567890ABCDEF please"
    redacted, mapping = privacy.redact(text)
    assert "sk-abcdef" not in redacted
    assert any(t.startswith("[SECRET") for t in mapping)


def test_redact_disabled_returns_original():
    privacy = _fresh_privacy(REDACT_PII="false")
    text = "leak@example.com"
    redacted, mapping = privacy.redact(text)
    assert redacted == text
    assert mapping == {}


def test_should_use_cloud_respects_kill_switch():
    privacy = _fresh_privacy(ALLOW_CLOUD_LLM="false")
    assert privacy.should_use_cloud(sensitive=False, cloud_available=True) is False


def test_should_use_cloud_blocks_sensitive():
    privacy = _fresh_privacy(ALLOW_CLOUD_LLM="true")
    assert privacy.should_use_cloud(sensitive=True, cloud_available=True) is False
    assert privacy.should_use_cloud(sensitive=False, cloud_available=True) is True


def test_should_use_cloud_falls_back_when_unavailable():
    privacy = _fresh_privacy(ALLOW_CLOUD_LLM="true")
    assert privacy.should_use_cloud(sensitive=False, cloud_available=False) is False


def test_audit_log_never_contains_raw_prompt(tmp_path, monkeypatch):
    privacy = _fresh_privacy(AUDIT_CLOUD_CALLS="true")
    audit_path = tmp_path / "cloud_audit.jsonl"
    monkeypatch.setattr(privacy, "_AUDIT_PATH", audit_path)

    secret_prompt = "THIS_STRING_MUST_NOT_APPEAR_IN_LOG"
    privacy.audit_cloud_call("claude", "test-model", secret_prompt, redactions=0)

    assert audit_path.exists()
    logged = audit_path.read_text(encoding="utf-8")
    assert secret_prompt not in logged
    assert "prompt_sha256" in logged
