"""Tests for rate limiter, deep health snapshot, and index migration."""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
import time


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import reliability as _rel
    importlib.reload(_rel)
    from api import db_indexes as _ix
    importlib.reload(_ix)
    return _rel, _ix


# ── Rate limiter bucket key resolution ──────────────────────────────────────
def test_bucket_key_default_limit():
    with tempfile.TemporaryDirectory() as tmp:
        rel, _ = _fresh(os.path.join(tmp, "nexus.db"))
        key, limit = rel._bucket_key("/api/tasks", "1.2.3.4")
        assert limit == rel._DEFAULT_LIMIT
        assert "tasks" in key


def test_bucket_key_voice_is_tighter():
    with tempfile.TemporaryDirectory() as tmp:
        rel, _ = _fresh(os.path.join(tmp, "nexus.db"))
        _, limit = rel._bucket_key("/api/voice/transcribe", "1.2.3.4")
        assert limit <= 30


def test_bucket_key_longest_prefix_wins():
    with tempfile.TemporaryDirectory() as tmp:
        rel, _ = _fresh(os.path.join(tmp, "nexus.db"))
        # "voice/memo-to-task" has a more specific override than "voice/"
        _, limit_generic = rel._bucket_key("/api/voice/transcribe", "x")
        _, limit_memo    = rel._bucket_key("/api/voice/memo-to-task", "x")
        assert limit_memo <= limit_generic


def test_bucket_key_non_api_paths_ignored_later():
    """Non-/api paths are allowed through because the middleware early-returns."""
    with tempfile.TemporaryDirectory() as tmp:
        rel, _ = _fresh(os.path.join(tmp, "nexus.db"))
        key, limit = rel._bucket_key("/health", "1.2.3.4")
        # Still produces a bucket key — middleware is the gatekeeper, not this.
        assert key


# ── Rate-limit stats ────────────────────────────────────────────────────────
def test_rate_limit_stats_shape():
    with tempfile.TemporaryDirectory() as tmp:
        rel, _ = _fresh(os.path.join(tmp, "nexus.db"))
        s = rel.rate_limit_stats()
        assert "buckets_tracked" in s
        assert "default_limit" in s
        assert "window_seconds" in s
        assert "overrides" in s
        assert isinstance(s["overrides"], dict)


# ── Deep health snapshot ────────────────────────────────────────────────────
def test_deep_health_reports_database_ok():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        # Seed a minimal table so the DB file exists
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE foo (id INTEGER)")
        conn.commit()
        conn.close()
        rel, _ = _fresh(db)
        h = rel.deep_health()
        assert h["checks"]["database"]["ok"] is True
        assert h["checks"]["database"]["tables"] >= 1
        assert "timestamp" in h
        assert "rate_limiter" in h["checks"]


def test_deep_health_includes_disk_and_scheduler_keys():
    with tempfile.TemporaryDirectory() as tmp:
        rel, _ = _fresh(os.path.join(tmp, "nexus.db"))
        h = rel.deep_health()
        assert "disk" in h["checks"]
        assert "scheduler" in h["checks"]


# ── Index migration ────────────────────────────────────────────────────────
def test_apply_indexes_on_empty_db_is_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ix = _fresh(db)
        first = ix.apply_indexes()
        second = ix.apply_indexes()
        # Nothing to index yet because no tenant tables exist
        assert first["applied"] == 0
        assert second["applied"] == 0


def test_apply_indexes_creates_indexes_on_existing_tables():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        # Manually create a couple of tables the migration knows about.
        conn = sqlite3.connect(db)
        conn.execute("""
            CREATE TABLE nexus_tasks (
                id TEXT, business_id TEXT, status TEXT, due_date TEXT,
                assignee_id TEXT, contact_id TEXT,
                recurrence TEXT, recurrence_parent_id TEXT
            )""")
        conn.execute("""
            CREATE TABLE nexus_invoices (
                id TEXT, business_id TEXT, status TEXT, due_date TEXT,
                customer_contact_id TEXT, customer_company_id TEXT
            )""")
        conn.commit()
        conn.close()

        _, ix = _fresh(db)
        result = ix.apply_indexes()
        assert result["applied"] >= 4
        assert result["errors"] == []

        # Verify indexes exist by name
        conn = sqlite3.connect(db)
        names = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        conn.close()
        assert "idx_tasks_biz_status_due" in names
        assert "idx_invoices_biz_status_due" in names


def test_apply_indexes_skips_missing_columns():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        # Create nexus_tasks without the recurrence columns
        conn = sqlite3.connect(db)
        conn.execute("""
            CREATE TABLE nexus_tasks (
                id TEXT, business_id TEXT, status TEXT, due_date TEXT,
                assignee_id TEXT, contact_id TEXT
            )""")
        conn.commit()
        conn.close()

        _, ix = _fresh(db)
        result = ix.apply_indexes()
        # idx_tasks_biz_recur requires columns we didn't create — must be skipped, not errored
        assert result["errors"] == []
        conn = sqlite3.connect(db)
        names = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        conn.close()
        assert "idx_tasks_biz_recur" not in names


# ── Async timeout helper ────────────────────────────────────────────────────
def test_with_timeout_raises_on_slow_coro():
    with tempfile.TemporaryDirectory() as tmp:
        rel, _ = _fresh(os.path.join(tmp, "nexus.db"))
        import asyncio
        from fastapi import HTTPException

        async def slow():
            await asyncio.sleep(2)

        import pytest
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(rel.with_timeout(slow(), seconds=0.05, label="test"))
        assert exc_info.value.status_code == 504
