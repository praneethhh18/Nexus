"""
Cloud budget — contract tests for the spend brake.

Behavior under test (`config/cloud_budget.py`):

  1. `record_usage` writes a row, `get_today_usage` aggregates correctly.
  2. `should_allow_cloud` returns True under the cap, False over it.
  3. Per-business isolation — business A's spend doesn't trip business B.
  4. Active-business contextvar flows through `record_usage` defaults.
  5. Cap of 0 disables the brake (returns True regardless of spend).
"""
from __future__ import annotations

import importlib
import os
import tempfile

import pytest


@pytest.fixture
def cb(monkeypatch, tmp_path):
    """Fresh budget module pointing at a per-test SQLite file."""
    db = str(tmp_path / "nexus.db")
    monkeypatch.setenv("DB_PATH", db)
    monkeypatch.setenv("CLOUD_TOKEN_DAILY_CAP", "10000")  # tight cap for tests
    from config import settings as _s
    importlib.reload(_s)
    from config import cloud_budget as _cb
    importlib.reload(_cb)
    return _cb


def test_record_and_aggregate(cb):
    cb.record_usage("biz-a", "bedrock", "amazon.nova-pro-v1:0", 1000, 500)
    cb.record_usage("biz-a", "bedrock", "amazon.nova-pro-v1:0", 2000, 1500)
    u = cb.get_today_usage("biz-a")
    assert u["tokens_in"]    == 3000
    assert u["tokens_out"]   == 2000
    assert u["tokens_total"] == 5000
    assert u["calls"] == 2
    assert u["est_cost_usd"] > 0  # Nova Pro priced > 0
    assert u["over_budget"] is False
    assert u["cap"] == 10000


def test_should_allow_cloud_under_cap(cb):
    cb.record_usage("biz-a", "bedrock", "amazon.nova-pro-v1:0", 100, 100)
    assert cb.should_allow_cloud("biz-a") is True


def test_should_block_cloud_over_cap(cb):
    cb.record_usage("biz-a", "bedrock", "amazon.nova-pro-v1:0", 6000, 6000)
    # 12k total > 10k cap
    assert cb.should_allow_cloud("biz-a") is False
    u = cb.get_today_usage("biz-a")
    assert u["over_budget"] is True


def test_per_business_isolation(cb):
    """Business A maxing out doesn't lock out business B."""
    cb.record_usage("biz-a", "bedrock", "amazon.nova-pro-v1:0", 6000, 6000)
    assert cb.should_allow_cloud("biz-a") is False
    assert cb.should_allow_cloud("biz-b") is True
    cb.record_usage("biz-b", "bedrock", "amazon.nova-pro-v1:0", 100, 100)
    u_b = cb.get_today_usage("biz-b")
    assert u_b["tokens_total"] == 200
    assert u_b["over_budget"] is False


def test_active_business_contextvar_default(cb):
    token = cb.set_active_business("biz-ctx")
    try:
        cb.record_usage(None, "bedrock", "amazon.nova-pro-v1:0", 50, 25)
    finally:
        cb.reset_active_business(token)
    u = cb.get_today_usage("biz-ctx")
    assert u["tokens_total"] == 75


def test_zero_cap_disables_brake(cb, monkeypatch):
    monkeypatch.setattr(cb, "DEFAULT_DAILY_CAP", 0)
    cb.record_usage("biz-a", "bedrock", "amazon.nova-pro-v1:0", 50_000, 50_000)
    # Way over what would normally be the cap, but cap=0 means no brake.
    assert cb.should_allow_cloud("biz-a") is True
