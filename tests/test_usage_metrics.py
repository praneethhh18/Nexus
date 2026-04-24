"""Tests for usage metrics counter + dashboard aggregation (11.1)."""
from __future__ import annotations

import importlib
import os
import tempfile
from datetime import date, timedelta


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import usage_metrics as _um
    importlib.reload(_um)
    return _um


# ── Recording ──────────────────────────────────────────────────────────────
def test_record_bumps_counter():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-1", "api_call", user_id="alice")
        um.record("biz-1", "api_call", user_id="alice")
        um.record("biz-1", "api_call", user_id="bob")
        t = um.totals("biz-1", days=1)
        assert t["api_call"] == 3


def test_record_handles_count_argument():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-1", "agent_run", count=5)
        um.record("biz-1", "agent_run", count=2)
        t = um.totals("biz-1")
        assert t["agent_run"] == 7


def test_record_swallows_errors_silently():
    """Metrics failure must never surface to the caller."""
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        # Illegal negative day — just shouldn't throw.
        um.record("biz-1", "api_call", day="not-a-date")


# ── Scoping ────────────────────────────────────────────────────────────────
def test_totals_scoped_per_business():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-a", "api_call")
        um.record("biz-a", "api_call")
        um.record("biz-b", "api_call")
        assert um.totals("biz-a")["api_call"] == 2
        assert um.totals("biz-b")["api_call"] == 1
        # Global (no business_id) sums both
        assert um.totals(None)["api_call"] == 3


def test_totals_respects_window():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        old = (date.today() - timedelta(days=40)).isoformat()
        um.record("biz-1", "api_call", day=old)
        um.record("biz-1", "api_call")   # today
        # 7-day window excludes the 40-day-old entry
        assert um.totals("biz-1", days=7)["api_call"] == 1
        # 90-day window sees both
        assert um.totals("biz-1", days=90)["api_call"] == 2


# ── Series ─────────────────────────────────────────────────────────────────
def test_series_fills_missing_days_with_zero():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-1", "api_call")
        s = um.series("api_call", days=7, business_id="biz-1")
        assert len(s) == 7
        assert sum(d["count"] for d in s) == 1
        # Days are returned in ascending order (chart-friendly)
        assert all(s[i]["day"] <= s[i + 1]["day"] for i in range(len(s) - 1))


def test_series_isolates_event():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-1", "api_call")
        um.record("biz-1", "agent_run", count=5)
        s_api = um.series("api_call", days=3, business_id="biz-1")
        s_run = um.series("agent_run", days=3, business_id="biz-1")
        assert sum(d["count"] for d in s_api) == 1
        assert sum(d["count"] for d in s_run) == 5


# ── Active users / businesses ──────────────────────────────────────────────
def test_active_users_counts_distinct_non_system():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-1", "api_call", user_id="alice")
        um.record("biz-1", "api_call", user_id="alice")
        um.record("biz-1", "api_call", user_id="bob")
        um.record("biz-1", "api_call", user_id="system")   # excluded
        assert um.active_users(days=1, business_id="biz-1") == 2


def test_active_businesses_counts_distinct_tenants():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-a", "api_call")
        um.record("biz-b", "api_call")
        um.record("biz-b", "agent_run")
        assert um.active_businesses(days=30) == 2


# ── Top tenants ────────────────────────────────────────────────────────────
def test_top_tenants_ranked_by_count():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-a", "api_call", count=10)
        um.record("biz-b", "api_call", count=3)
        um.record("biz-c", "api_call", count=7)
        top = um.top_tenants(event="api_call", days=30, limit=10)
        assert [t["business_id"] for t in top] == ["biz-a", "biz-c", "biz-b"]
        assert top[0]["count"] == 10


def test_top_tenants_respects_limit():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        for i in range(5):
            um.record(f"biz-{i}", "api_call", count=i + 1)
        top = um.top_tenants(limit=2)
        assert len(top) == 2


# ── Dashboard ──────────────────────────────────────────────────────────────
def test_dashboard_global_shape():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-1", "api_call", user_id="alice")
        um.record("biz-2", "agent_run")
        d = um.dashboard(business_id=None, days=7)
        assert d["scope"] == "global"
        assert d["business_id"] is None
        assert "totals" in d
        assert "api_series" in d and len(d["api_series"]) == 7
        assert "top_tenants" in d
        assert d["active_businesses"] >= 1


def test_dashboard_tenant_hides_top_tenants():
    with tempfile.TemporaryDirectory() as tmp:
        um = _fresh(os.path.join(tmp, "nexus.db"))
        um.record("biz-1", "api_call")
        d = um.dashboard(business_id="biz-1", days=7)
        assert d["scope"] == "tenant"
        assert d["business_id"] == "biz-1"
        assert d["top_tenants"] == []
