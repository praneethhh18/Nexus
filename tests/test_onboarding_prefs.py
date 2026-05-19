"""Tests for api/onboarding.py + api/notification_prefs.py."""
from __future__ import annotations

import importlib
import os
import tempfile


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import onboarding as _onb
    importlib.reload(_onb)
    from api import notification_prefs as _np
    importlib.reload(_np)
    return _onb, _np


def test_onboarding_initial_state_all_pending():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        onb, _ = _fresh(db)

        state = onb.get_state("biz-1", "user-1")
        assert len(state["steps"]) == 6
        assert all(not s["done"] for s in state["steps"])
        assert state["all_done"] is False
        assert state["celebrated"] is False


def test_onboarding_complete_step_persists():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        onb, _ = _fresh(db)

        onb.complete_step("biz-1", "user-1", "profile")
        state = onb.get_state("biz-1", "user-1")
        by_key = {s["key"]: s for s in state["steps"]}
        assert by_key["profile"]["done"] is True
        assert by_key["agents"]["done"] is False


def test_onboarding_profile_autodetect_requires_industry():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        onb, _ = _fresh(db)

        from api.businesses import create_business, update_business

        biz = create_business("Acme", owner_id="owner-1")
        state = onb.get_state(biz["id"], "owner-1")
        by_key = {s["key"]: s for s in state["steps"]}
        assert by_key["profile"]["done"] is False

        update_business(biz["id"], "owner-1", {"industry": "SaaS"})
        state = onb.get_state(biz["id"], "owner-1")
        by_key = {s["key"]: s for s in state["steps"]}
        assert by_key["profile"]["done"] is False

        update_business(biz["id"], "owner-1", {
            "description": "Business type: Startup\nCompany size: 6-20\nPrimary goal: Sales and CRM",
        })
        state = onb.get_state(biz["id"], "owner-1")
        by_key = {s["key"]: s for s in state["steps"]}
        assert by_key["profile"]["done"] is True


def test_industry_setup_applies_workspace_defaults_idempotently():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _fresh(db)

        from api.businesses import create_business
        from api.industry_setup import apply_industry_setup
        from agents.personas import list_personas
        from api.agent_schedule import get_overrides
        from api.email_templates import list_templates

        biz = create_business("Acme SaaS", owner_id="owner-1", industry="SaaS")
        first = apply_industry_setup(biz["id"], "owner-1")
        second = apply_industry_setup(biz["id"], "owner-1")

        assert first["industry"] == "SaaS"
        assert "stale_deal_watcher" in first["priority_agents"]
        assert first["schedules"]["email_triage"] == 15
        assert get_overrides(biz["id"])["email_triage"] == 15
        assert all(p["enabled"] is True for p in list_personas(biz["id"]))

        names = [t["name"] for t in list_templates(biz["id"])]
        assert "Demo follow-up" in names
        assert "Renewal check-in" in names
        assert second["created_templates"] == []
        assert names.count("Demo follow-up") == 1


def test_onboarding_all_done_sets_completed_at():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        onb, _ = _fresh(db)

        for key in ["profile", "agents", "data_source", "document", "first_run", "celebrated"]:
            onb.complete_step("biz-1", "user-1", key)
        state = onb.get_state("biz-1", "user-1")
        assert state["all_done"] is True
        assert state["completed_at"] is not None


def test_onboarding_unknown_step_raises():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        onb, _ = _fresh(db)

        import pytest
        with pytest.raises(ValueError):
            onb.complete_step("biz-1", "user-1", "not_a_real_step")


def test_onboarding_skip_then_reopen():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        onb, _ = _fresh(db)

        onb.skip_all("biz-1", "user-1")
        assert onb.get_state("biz-1", "user-1")["skipped"] is True
        onb.reopen("biz-1", "user-1")
        assert onb.get_state("biz-1", "user-1")["skipped"] is False


def test_onboarding_is_isolated_per_user():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        onb, _ = _fresh(db)

        onb.complete_step("biz-1", "alice", "profile")
        bob_state = onb.get_state("biz-1", "bob")
        by_key = {s["key"]: s for s in bob_state["steps"]}
        assert by_key["profile"]["done"] is False


def test_notification_prefs_defaults_returned_without_row():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, np = _fresh(db)

        prefs = np.get_prefs("alice")
        # Every known event is present and matches the shipped defaults.
        for key, default in np.DEFAULTS.items():
            assert prefs[key] == default


def test_notification_prefs_partial_update_merges():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, np = _fresh(db)

        out = np.set_prefs("alice", {"email_sent": True, "unknown_key": True})
        # email_sent flipped from False to True
        assert out["email_sent"] is True
        # Defaults still apply for everything else
        assert out["approval_waiting"] is np.DEFAULTS["approval_waiting"]
        # Unknown keys are ignored, not stored
        assert "unknown_key" not in out


def test_notification_prefs_should_send_honors_toggle():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, np = _fresh(db)

        np.set_prefs("alice", {"approval_waiting": False})
        assert np.should_send("alice", "approval_waiting") is False
        # Unaffected event still sends
        assert np.should_send("alice", "invoice_overdue") is True
