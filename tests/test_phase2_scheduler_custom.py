"""Tests for agent schedule prefs + custom agents + templates."""
from __future__ import annotations

import importlib
import os
import tempfile


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import agent_schedule as _as
    importlib.reload(_as)
    # custom_agents reloads tag_registry lazily; safe to reload here too.
    from api import custom_agents as _ca
    importlib.reload(_ca)
    return _as, _ca


# ── Schedule prefs ──────────────────────────────────────────────────────────
def test_default_interval_returned_without_override():
    with tempfile.TemporaryDirectory() as tmp:
        sch, _ = _fresh(os.path.join(tmp, "nexus.db"))
        assert sch.effective_interval("biz-1", "email_triage") == sch.DEFAULT_INTERVALS_MIN["email_triage"]


def test_set_interval_persists_and_is_custom_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        sch, _ = _fresh(os.path.join(tmp, "nexus.db"))
        r = sch.set_interval("biz-1", "email_triage", 60)
        assert r["interval_minutes"] == 60
        assert r["is_custom"] is True
        assert sch.effective_interval("biz-1", "email_triage") == 60


def test_reset_interval_drops_override():
    with tempfile.TemporaryDirectory() as tmp:
        sch, _ = _fresh(os.path.join(tmp, "nexus.db"))
        sch.set_interval("biz-1", "email_triage", 60)
        r = sch.reset_interval("biz-1", "email_triage")
        assert r["is_custom"] is False
        assert sch.effective_interval("biz-1", "email_triage") == sch.DEFAULT_INTERVALS_MIN["email_triage"]


def test_interval_clamped_to_valid_range():
    with tempfile.TemporaryDirectory() as tmp:
        sch, _ = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            sch.set_interval("biz-1", "email_triage", 1)        # too short
        with pytest.raises(ValueError):
            sch.set_interval("biz-1", "email_triage", 999999)   # too long


def test_unknown_agent_key_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        sch, _ = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            sch.set_interval("biz-1", "not_real", 60)
        with pytest.raises(ValueError):
            sch.effective_interval("biz-1", "not_real")


def test_schedule_isolated_per_business():
    with tempfile.TemporaryDirectory() as tmp:
        sch, _ = _fresh(os.path.join(tmp, "nexus.db"))
        sch.set_interval("biz-a", "email_triage", 30)
        assert sch.effective_interval("biz-a", "email_triage") == 30
        # Other business is untouched
        assert sch.effective_interval("biz-b", "email_triage") == sch.DEFAULT_INTERVALS_MIN["email_triage"]


def test_list_schedule_returns_one_row_per_agent():
    with tempfile.TemporaryDirectory() as tmp:
        sch, _ = _fresh(os.path.join(tmp, "nexus.db"))
        rows = sch.list_schedule("biz-1")
        assert len(rows) == len(sch.DEFAULT_INTERVALS_MIN)
        keys = {r["agent_key"] for r in rows}
        assert keys == set(sch.DEFAULT_INTERVALS_MIN.keys())


def test_human_label_formats_well_known_values():
    from api import agent_schedule as sch
    assert sch.human_label(60) == "Hourly"
    assert sch.human_label(1440) == "Daily"
    assert sch.human_label(10080) == "Weekly"
    assert sch.human_label(15) == "Every 15 min"


# ── Custom agents CRUD ──────────────────────────────────────────────────────
def test_create_custom_agent_requires_name_and_goal():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            ca.create_agent("biz-1", "u", {"goal": "do stuff"})
        with pytest.raises(ValueError):
            ca.create_agent("biz-1", "u", {"name": "Foo"})


def test_create_custom_agent_persists_and_is_scoped():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        agent = ca.create_agent("biz-1", "user-1", {
            "name": "Test",
            "goal": "Summarize something useful.",
            "tool_whitelist": [],
            "interval_minutes": 60,
            "output_target": "inbox",
        })
        assert agent["name"] == "Test"
        assert agent["enabled"] is True
        # List filters by business
        assert len(ca.list_agents("biz-1")) == 1
        assert len(ca.list_agents("biz-other")) == 0


def test_update_custom_agent_merges_fields():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        a = ca.create_agent("biz-1", "u", {"name": "A", "goal": "g"})
        updated = ca.update_agent("biz-1", a["id"], {"name": "B", "enabled": False})
        assert updated["name"] == "B"
        assert updated["enabled"] is False
        # goal untouched
        assert updated["goal"] == "g"


def test_update_unknown_agent_raises():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(KeyError):
            ca.update_agent("biz-1", "ca-missing", {"name": "X"})


def test_invalid_output_target_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            ca.create_agent("biz-1", "u", {
                "name": "A", "goal": "g", "output_target": "pigeon",
            })


def test_invalid_interval_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            ca.create_agent("biz-1", "u", {
                "name": "A", "goal": "g", "interval_minutes": 1,
            })


def test_list_all_enabled_filters_correctly():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        a = ca.create_agent("biz-1", "u", {"name": "A", "goal": "g"})
        b = ca.create_agent("biz-2", "u", {"name": "B", "goal": "g"})
        ca.update_agent("biz-1", a["id"], {"enabled": False})
        enabled = ca.list_all_enabled()
        ids = {x["id"] for x in enabled}
        assert b["id"] in ids
        assert a["id"] not in ids


def test_delete_custom_agent_is_scoped():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        a = ca.create_agent("biz-a", "u", {"name": "A", "goal": "g"})
        # Deleting with wrong business is a no-op
        ca.delete_agent("biz-b", a["id"])
        assert ca.get_agent("biz-a", a["id"])["id"] == a["id"]
        ca.delete_agent("biz-a", a["id"])
        import pytest
        with pytest.raises(KeyError):
            ca.get_agent("biz-a", a["id"])


# ── Templates ───────────────────────────────────────────────────────────────
def test_templates_catalog_exists_and_has_keys():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        tpls = ca.list_templates()
        assert len(tpls) >= 5
        keys = {t["key"] for t in tpls}
        assert "competitor_price_watcher" in keys
        assert "weekly_team_digest" in keys


def test_create_from_template_copies_fields():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        agent = ca.create_from_template("biz-1", "u", "weekly_team_digest")
        assert agent["template_key"] == "weekly_team_digest"
        assert agent["name"] == "Weekly Team Digest"
        assert agent["interval_minutes"] == 10080


def test_create_from_unknown_template_raises():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            ca.create_from_template("biz-1", "u", "does-not-exist")


def test_create_from_template_applies_overrides():
    with tempfile.TemporaryDirectory() as tmp:
        _, ca = _fresh(os.path.join(tmp, "nexus.db"))
        agent = ca.create_from_template("biz-1", "u", "lead_scorer", overrides={
            "name": "My Custom Lead Scorer",
            "interval_minutes": 720,
        })
        assert agent["name"] == "My Custom Lead Scorer"
        assert agent["interval_minutes"] == 720
        # tool_whitelist is validated strictly=False for templates — may be empty
        # if none of the referenced tool names exist in the registry yet.
        assert isinstance(agent["tool_whitelist"], list)
