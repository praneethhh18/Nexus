"""Regression tests for expired trial gating."""
from __future__ import annotations


def test_get_plan_treats_expired_trial_as_free(monkeypatch):
    from api import subscriptions

    monkeypatch.setattr(
        subscriptions,
        "get_subscription",
        lambda business_id: {
            "business_id": business_id,
            "plan": "pro",
            "status": "trial",
            "trial_active": False,
        },
    )

    assert subscriptions.get_plan("biz-expired") == "free"


def test_plan_summary_uses_free_limits_for_expired_trial(monkeypatch):
    from api import plan_gate

    expired_sub = {
        "business_id": "biz-expired",
        "plan": "pro",
        "status": "trial",
        "started_at": None,
        "current_period_end": None,
        "trial_started_at": "2026-01-01T00:00:00+00:00",
        "trial_ends_at": "2026-01-15T00:00:00+00:00",
        "trial_days_remaining": 0,
        "trial_active": False,
    }
    monkeypatch.setattr(plan_gate, "get_subscription", lambda business_id: expired_sub)
    monkeypatch.setattr(plan_gate, "get_plan", lambda business_id: "free")

    summary = plan_gate.plan_summary("biz-expired")

    assert summary["plan_key"] == "free"
    assert summary["is_trial"] is False
    assert summary["trial_expired"] is True
    assert summary["limits"]["agents"] == 2
