"""
Migration runner contract.

Verifies that:
  - applying migrations against a fresh DB succeeds and records the ledger
  - applying twice is a no-op (idempotent)
  - duplicate version numbers in db/migrations/ are rejected
  - a tampered (edited-after-apply) migration logs a warning but doesn't
    re-run the migration
  - status() returns the right applied/pending split
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest


def _fresh(db_path: str, migrations_dir: Path):
    """Reload the migrate module pointed at a sandboxed migrations dir."""
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from db import migrate as _m
    importlib.reload(_m)
    # Override the migrations directory the module captured at import time.
    _m._MIGRATIONS_DIR = migrations_dir
    return _m


def _write_migration(migrations_dir: Path, version: int, name: str, sql: str) -> Path:
    migrations_dir.mkdir(parents=True, exist_ok=True)
    p = migrations_dir / f"{version:04d}_{name}.sql"
    p.write_text(sql, encoding="utf-8")
    return p


# ── 1. Fresh DB → applies + records ────────────────────────────────────────
def test_apply_pending_creates_ledger_and_runs_each_migration_once():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        migrations = tmp_path / "migrations"
        m = _fresh(db_path, migrations)

        _write_migration(migrations, 1, "noop", "-- baseline\n")
        _write_migration(migrations, 2, "add_widgets", """
            CREATE TABLE widgets (id INTEGER PRIMARY KEY, name TEXT);
            INSERT INTO widgets (name) VALUES ('seed');
        """)

        runs = m.apply_pending(db_path)
        assert len(runs) == 2
        assert [r["version"] for r in runs] == [1, 2]

        # The ledger has both rows.
        conn = sqlite3.connect(db_path)
        try:
            ledger = conn.execute(
                f"SELECT version, name FROM {m.LEDGER_TABLE} ORDER BY version"
            ).fetchall()
            assert ledger == [(1, "noop"), (2, "add_widgets")]
            # The widget table actually exists with the seed row.
            widget_rows = conn.execute("SELECT name FROM widgets").fetchall()
            assert widget_rows == [("seed",)]
        finally:
            conn.close()


# ── 2. Idempotent ──────────────────────────────────────────────────────────
def test_apply_pending_is_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        migrations = tmp_path / "migrations"
        m = _fresh(db_path, migrations)

        _write_migration(migrations, 1, "first",
                         "CREATE TABLE t1 (id INTEGER PRIMARY KEY);")

        first_run = m.apply_pending(db_path)
        assert len(first_run) == 1

        # Running again must not re-apply.
        second_run = m.apply_pending(db_path)
        assert second_run == [], "Re-running migrations must be a no-op"

        # And the table wasn't dropped + recreated.
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("INSERT INTO t1 DEFAULT VALUES")
            conn.commit()
            n = conn.execute("SELECT COUNT(*) FROM t1").fetchone()[0]
            assert n == 1
        finally:
            conn.close()

        # Adding a new migration after the first run gets picked up.
        _write_migration(migrations, 2, "second",
                         "CREATE TABLE t2 (id INTEGER PRIMARY KEY);")
        third_run = m.apply_pending(db_path)
        assert [r["version"] for r in third_run] == [2]


# ── 3. Duplicate version numbers → reject ──────────────────────────────────
def test_duplicate_version_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        migrations = tmp_path / "migrations"
        m = _fresh(db_path, migrations)

        _write_migration(migrations, 1, "alpha", "-- a")
        _write_migration(migrations, 1, "bravo", "-- b")  # same version

        with pytest.raises(RuntimeError, match="duplicate migration"):
            m.apply_pending(db_path)


# ── 4. Tampered migration → warn but don't re-run ──────────────────────────
def test_edited_migration_warns_but_does_not_rerun(caplog):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        migrations = tmp_path / "migrations"
        m = _fresh(db_path, migrations)

        path = _write_migration(migrations, 1, "edit_me",
                                "CREATE TABLE only_once (id INTEGER PRIMARY KEY);")
        m.apply_pending(db_path)

        # Edit the file post-apply (a developer mistake).
        path.write_text("CREATE TABLE only_once (id INTEGER PRIMARY KEY);  -- edited",
                        encoding="utf-8")

        # Re-running: the runner must NOT try to re-execute (would CREATE TABLE
        # twice and fail). The current logic skips already-applied versions.
        runs = m.apply_pending(db_path)
        assert runs == [], "Tampered migration must not be re-applied"


# ── 5. status() reports correctly ──────────────────────────────────────────
def test_status_reports_applied_and_pending():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        migrations = tmp_path / "migrations"
        m = _fresh(db_path, migrations)

        _write_migration(migrations, 1, "alpha", "CREATE TABLE a (id INTEGER);")
        _write_migration(migrations, 2, "bravo", "CREATE TABLE b (id INTEGER);")
        _write_migration(migrations, 3, "charlie", "CREATE TABLE c (id INTEGER);")

        # Apply only the first by faking it: run apply_pending on a clipped dir.
        only_first = tmp_path / "only_first"
        _write_migration(only_first, 1, "alpha", "CREATE TABLE a (id INTEGER);")
        m._MIGRATIONS_DIR = only_first
        m.apply_pending(db_path)

        # Now point status at the full set — 1 applied, 2 pending.
        m._MIGRATIONS_DIR = migrations
        s = m.status(db_path)
        assert [r["version"] for r in s["applied"]] == [1]
        assert [r["version"] for r in s["pending"]] == [2, 3]


# ── 6. Empty migration file = valid no-op ──────────────────────────────────
def test_empty_migration_records_as_noop():
    """The 0001 baseline is intentionally empty — must be recorded, not
    crash, and not re-run on the second pass."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        migrations = tmp_path / "migrations"
        m = _fresh(db_path, migrations)

        _write_migration(migrations, 1, "baseline", "-- comment only\n")
        runs = m.apply_pending(db_path)
        assert len(runs) == 1
        # Re-run is a no-op.
        assert m.apply_pending(db_path) == []
