"""Tests for the self-hosted setup wizard (9.3)."""
from __future__ import annotations

import importlib
import os
import tempfile
from unittest.mock import patch


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import setup_wizard as _sw
    importlib.reload(_sw)
    return _sw


def _mock_ollama_online(models=None):
    class R:
        status_code = 200
        def json(self): return {"models": [{"name": m} for m in (models or [])]}
    return patch("api.setup_wizard.requests.get", return_value=R())


def _mock_ollama_offline():
    def _raise(*a, **k):
        raise ConnectionError("connection refused")
    return patch("api.setup_wizard.requests.get", side_effect=_raise)


# ── Initial state ──────────────────────────────────────────────────────────
def test_status_initial_not_complete():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_offline():
            s = sw.status()
        assert s["completed"] is False
        assert s["ollama"]["online"] is False
        assert s["can_finish"] is False


def test_status_includes_platform_info():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_offline():
            s = sw.status()
        assert "os" in s["platform"]
        assert "arch" in s["platform"]
        assert "python" in s["platform"]


def test_status_shows_recommended_models():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_offline():
            s = sw.status()
        names = [m["name"] for m in s["models"]["suitable"]]
        assert "llama3.1:8b-instruct-q4_K_M" in names
        # Recommended flag is set on the balanced model
        rec = next(m for m in s["models"]["suitable"] if m["name"] == "llama3.1:8b-instruct-q4_K_M")
        assert rec.get("recommended") is True


# ── Installed detection ────────────────────────────────────────────────────
def test_installed_models_marked_when_present():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_online(models=["llama3.1:8b-instruct-q4_K_M"]):
            s = sw.status()
        rec = next(m for m in s["models"]["suitable"] if m["name"] == "llama3.1:8b-instruct-q4_K_M")
        assert rec["installed"] is True


def test_installed_matches_model_family_variant():
    """If ollama has the same family at a different quantisation, it still counts."""
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_online(models=["llama3.1:8b-q8_0"]):
            s = sw.status()
        rec = next(m for m in s["models"]["suitable"] if m["name"] == "llama3.1:8b-instruct-q4_K_M")
        # Same family base should be detected as installed.
        assert rec["installed"] is True


# ── Can finish gate ────────────────────────────────────────────────────────
def test_can_finish_requires_ollama_and_model():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_online(models=[]):
            s = sw.status()
        assert s["can_finish"] is False      # no models pulled yet

        with _mock_ollama_online(models=["llama3.1:8b-instruct-q4_K_M"]):
            s = sw.status()
        assert s["can_finish"] is True


# ── Model choice ───────────────────────────────────────────────────────────
def test_choose_model_persists():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_online():
            sw.choose_model("qwen2.5:3b-instruct-q4_K_M")
            s = sw.status()
        assert s["models"]["chosen"] == "qwen2.5:3b-instruct-q4_K_M"
        # Env var is synced so the running process picks it up.
        assert os.environ.get("OLLAMA_MODEL") == "qwen2.5:3b-instruct-q4_K_M"


def test_choose_model_rejects_empty():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            sw.choose_model("")


# ── Pull model ─────────────────────────────────────────────────────────────
def test_pull_model_rejects_nameless_ref():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            sw.pull_model("llama3")        # no tag


def test_pull_model_handles_http_failure():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with patch("api.setup_wizard.requests.post",
                   side_effect=ConnectionError("daemon down")):
            r = sw.pull_model("llama3.1:8b-instruct-q4_K_M")
        assert r["ok"] is False
        assert "daemon down" in r["error"]


# ── Complete / reset ───────────────────────────────────────────────────────
def test_complete_marks_done():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_online(models=["llama3.1:8b-instruct-q4_K_M"]):
            s = sw.complete()
        assert s["completed"] is True
        assert s["completed_at"] is not None
        assert sw.is_complete() is True


def test_reset_flips_back_to_incomplete():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        with _mock_ollama_online():
            sw.complete()
            s = sw.reset()
        assert s["completed"] is False
        assert sw.is_complete() is False


def test_is_complete_starts_false():
    with tempfile.TemporaryDirectory() as tmp:
        sw = _fresh(os.path.join(tmp, "nexus.db"))
        assert sw.is_complete() is False
