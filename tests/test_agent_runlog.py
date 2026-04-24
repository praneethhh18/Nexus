"""Tests for agents/run_log.py + privacy per-request stats surfacing."""
from __future__ import annotations

import importlib
import os
import tempfile


def _fresh_modules(db_path: str):
    """Reload settings + run_log + privacy pointing at a throwaway DB."""
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from agents import run_log as _rl
    importlib.reload(_rl)
    from config import privacy as _p
    importlib.reload(_p)
    return _rl, _p


def test_run_log_start_and_finish_success():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        run_log, _ = _fresh_modules(db)

        rid = run_log.start("biz-1", "invoice_reminder", trigger="scheduler")
        assert isinstance(rid, str) and len(rid) == 32
        run_log.finish(rid, status="success", items_produced=3)

        last = run_log.last_run("biz-1", "invoice_reminder")
        assert last is not None
        assert last["status"] == "success"
        assert last["items_produced"] == 3
        assert last["trigger"] == "scheduler"
        assert last["finished_at"] is not None


def test_run_log_records_errors_with_trimmed_message():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        run_log, _ = _fresh_modules(db)

        rid = run_log.start("biz-1", "email_triage")
        long_err = "x" * 2000
        run_log.finish(rid, status="error", error=long_err)

        last = run_log.last_run("biz-1", "email_triage")
        assert last["status"] == "error"
        # Error must be trimmed — stops one agent from blowing up the DB.
        assert len(last["error"]) <= 800


def test_run_log_summary_counts_last_24h():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        run_log, _ = _fresh_modules(db)

        for _ in range(2):
            r = run_log.start("biz-1", "morning_briefing")
            run_log.finish(r, status="success", items_produced=1)
        r = run_log.start("biz-1", "morning_briefing")
        run_log.finish(r, status="error", error="boom")

        summary = run_log.summary("biz-1", hours=24)
        assert summary["morning_briefing"]["success"] == 2
        assert summary["morning_briefing"]["error"] == 1


def test_privacy_stats_reset_and_record():
    """reset_stats + note_call should give chat endpoints a clean per-request counter."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, privacy = _fresh_modules(db)

        privacy.reset_stats()
        privacy.note_call("ollama", cloud=False, redactions=0)
        privacy.note_call("claude", cloud=True, redactions=2,
                          kinds={"EMAIL": 1, "PHONE": 1})

        stats = privacy.get_stats()
        assert stats["local_calls"] == 1
        assert stats["cloud_calls"] == 1
        assert stats["redactions"] == 2
        assert stats["by_kind"] == {"EMAIL": 1, "PHONE": 1}
        assert stats["provider"] == "claude"


def test_privacy_kind_counts_from_mapping():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, privacy = _fresh_modules(db)

        mapping = {
            "[EMAIL_1]": "a@b.com",
            "[EMAIL_2]": "c@d.com",
            "[PHONE_1]": "+91-98-00",
        }
        counts = privacy.kind_counts(mapping)
        assert counts == {"EMAIL": 2, "PHONE": 1}


def test_privacy_should_use_cloud_flags_forced_local():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, privacy = _fresh_modules(db)

        privacy.reset_stats()
        # sensitive request while cloud is available ⇒ force local + flag it
        decision = privacy.should_use_cloud(sensitive=True, cloud_available=True)
        assert decision is False
        stats = privacy.get_stats()
        assert stats["sensitive_forced_local"] is True


def test_run_log_list_runs_newest_first():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        run_log, _ = _fresh_modules(db)

        ids = []
        for i in range(3):
            rid = run_log.start("biz-1", "stale_deal_watcher")
            run_log.finish(rid, status="success", items_produced=i)
            ids.append(rid)

        runs = run_log.list_runs("biz-1", agent_key="stale_deal_watcher")
        assert len(runs) == 3
        # Newest first
        assert runs[0]["id"] == ids[-1]
        assert runs[-1]["id"] == ids[0]
