"""Tests for new workflow control nodes + AI suggestions engine."""
from __future__ import annotations

import importlib
import os
import tempfile


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import crm as _crm
    importlib.reload(_crm)
    from api import invoices as _inv
    importlib.reload(_inv)
    from api import tasks as _tasks
    importlib.reload(_tasks)
    from api import suggestions as _sg
    importlib.reload(_sg)
    from workflows.nodes import control_nodes
    importlib.reload(control_nodes)
    # Make sure the upstream tables exist — suggestion rules read across
    # contacts/tasks/invoices and skip rules silently when a table is missing.
    _crm._get_conn().close()
    _tasks._get_conn().close()
    _inv._get_conn().close()
    return _crm, _inv, _tasks, _sg, control_nodes


# ── for_each_node ──────────────────────────────────────────────────────────
def test_for_each_iterates_over_list():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        ctx = {"output": ["a", "b", "c"], "_business_id": "biz-1"}
        out = cn.run_for_each_node({
            "source_field": "output",
            "action_type": "http_request",  # real node, will fail safely without URL
            "action_config": {"url": "http://localhost:1/nowhere", "method": "GET"},
        }, ctx)
        # Should report 3 iterations (all failed but loop counted them)
        assert "for_each ran http_request on 3 item" in out["output"]
        # Errors captured, not thrown
        assert "_for_each_errors" in out


def test_for_each_handles_missing_list():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        out = cn.run_for_each_node({
            "source_field": "missing.key",
            "action_type": "desktop_notify",
            "action_config": {},
        }, {"output": "not a list"})
        assert "no iterable found" in out["output"]


def test_for_each_max_items_caps_loop():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        # 100 items, cap at 5
        ctx = {"output": list(range(100)), "_business_id": "biz-1"}
        out = cn.run_for_each_node({
            "source_field": "output",
            "action_type": "desktop_notify",
            "action_config": {"title": "x", "message": "y"},
            "max_items": 5,
        }, ctx)
        assert "on 5 item(s)" in out["output"]


def test_for_each_parses_json_string():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        ctx = {"output": '["x", "y"]', "_business_id": "biz-1"}
        out = cn.run_for_each_node({
            "source_field": "output",
            "action_type": "desktop_notify",
            "action_config": {"title": "x"},
        }, ctx)
        assert "on 2 item(s)" in out["output"]


# ── error_handler ──────────────────────────────────────────────────────────
def test_error_handler_success_path():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        # desktop_notify can't fail even without plyer — it just prints.
        out = cn.run_error_handler({
            "action_type": "desktop_notify",
            "action_config": {"title": "hi", "message": "there"},
            "fallback_type": "desktop_notify",
            "fallback_config": {},
        }, {"_business_id": "biz-1"})
        assert out["_error_handler_branch"] == "success"


def test_error_handler_rejects_missing_action():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        out = cn.run_error_handler({}, {})
        assert "no action_type configured" in out["output"]


def test_error_handler_falls_back_on_failure():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        # Force first action to fail by pointing to unknown node type
        out = cn.run_error_handler({
            "action_type": "not_a_real_node",
            "action_config": {},
            "fallback_type": "desktop_notify",
            "fallback_config": {"title": "fb", "message": "!"},
        }, {"_business_id": "biz-1"})
        assert out["_error_handler_branch"] == "fallback"
        assert "_error_message" in out


# ── trigger_agent ──────────────────────────────────────────────────────────
def test_trigger_agent_builtin_unknown_key_fails_gracefully():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        out = cn.run_trigger_agent({
            "agent_type": "builtin",
            "agent_key":  "this_does_not_exist",
        }, {"_business_id": "biz-1"})
        # run_trigger_agent catches + returns, doesn't raise
        assert "trigger_agent failed" in out["output"]


def test_trigger_agent_custom_requires_id():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, cn = _fresh(os.path.join(tmp, "nexus.db"))
        out = cn.run_trigger_agent({
            "agent_type": "custom",
            "custom_agent_id": "",
        }, {"_business_id": "biz-1"})
        assert "trigger_agent failed" in out["output"]


# ── Suggestions: contacts ──────────────────────────────────────────────────
def test_contact_followup_overdue_fires_when_no_recent_task():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, _, sg, _ = _fresh(os.path.join(tmp, "nexus.db"))
        c = crm.create_contact("biz-1", "u", {"first_name": "Alice"})
        out = sg.for_entity("biz-1", "contact", c["id"])
        keys = [s["rule_key"] for s in out]
        assert "contact_followup_overdue" in keys


def test_contact_followup_does_not_fire_when_task_recent():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, tasks, sg, _ = _fresh(os.path.join(tmp, "nexus.db"))
        c = crm.create_contact("biz-1", "u", {"first_name": "Alice"})
        tasks.create_task("biz-1", "u", {"title": "Call Alice", "contact_id": c["id"]})
        out = sg.for_entity("biz-1", "contact", c["id"])
        keys = [s["rule_key"] for s in out]
        assert "contact_followup_overdue" not in keys


def test_contact_with_overdue_invoice_raises_suggestion():
    with tempfile.TemporaryDirectory() as tmp:
        crm, inv, tasks, sg, _ = _fresh(os.path.join(tmp, "nexus.db"))
        c = crm.create_contact("biz-1", "u", {"first_name": "Alice", "email": "a@x.com"})
        # Create a recent task so follow-up rule doesn't fire — isolate overdue rule.
        tasks.create_task("biz-1", "u", {"title": "Chat", "contact_id": c["id"]})
        i = inv.create_invoice("biz-1", "u", {
            "customer_name": "Alice", "customer_contact_id": c["id"],
            "due_date": "2020-01-01",    # long past
        })
        inv.update_invoice("biz-1", i["id"], {"status": "sent"})
        out = sg.for_entity("biz-1", "contact", c["id"])
        keys = [s["rule_key"] for s in out]
        assert "contact_has_overdue_invoice" in keys


# ── Suggestions: invoices ──────────────────────────────────────────────────
def test_overdue_invoice_raises_overdue_rule():
    with tempfile.TemporaryDirectory() as tmp:
        _, inv, _, sg, _ = _fresh(os.path.join(tmp, "nexus.db"))
        i = inv.create_invoice("biz-1", "u", {
            "customer_name": "X", "due_date": "2020-01-01",
        })
        inv.update_invoice("biz-1", i["id"], {"status": "sent"})
        out = sg.for_entity("biz-1", "invoice", i["id"])
        keys = [s["rule_key"] for s in out]
        assert "invoice_overdue_now" in keys


# ── Suggestions: tasks ─────────────────────────────────────────────────────
def test_large_task_suggestion_fires():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, tasks, sg, _ = _fresh(os.path.join(tmp, "nexus.db"))
        t = tasks.create_task("biz-1", "u", {
            "title": "Big thing",
            "description": "x" * 800,
        })
        out = sg.for_entity("biz-1", "task", t["id"])
        keys = [s["rule_key"] for s in out]
        assert "task_large" in keys


def test_high_priority_overdue_task_fires():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, tasks, sg, _ = _fresh(os.path.join(tmp, "nexus.db"))
        t = tasks.create_task("biz-1", "u", {
            "title": "Ship it",
            "priority": "high",
            "due_date": "2020-01-01",
        })
        out = sg.for_entity("biz-1", "task", t["id"])
        keys = [s["rule_key"] for s in out]
        assert "task_overdue_high_priority" in keys


# ── Dismissal ──────────────────────────────────────────────────────────────
def test_dismiss_hides_suggestion():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, _, sg, _ = _fresh(os.path.join(tmp, "nexus.db"))
        c = crm.create_contact("biz-1", "u", {"first_name": "Alice"})
        first = sg.for_entity("biz-1", "contact", c["id"])
        assert len(first) >= 1
        sid = first[0]["id"]
        sg.dismiss("biz-1", sid)
        second = sg.for_entity("biz-1", "contact", c["id"])
        assert all(s["id"] != sid for s in second)


def test_invalid_entity_type_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, sg, _ = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            sg.for_entity("biz-1", "unknown", "x")
