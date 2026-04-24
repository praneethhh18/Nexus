"""Tests for the client error receiver router."""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    # Re-import the router module against the fresh DB.
    from api.routers import errors as _err
    importlib.reload(_err)
    return _err


def test_submit_error_persists_row():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        err = _fresh(db)
        err.submit_error({
            "name": "TypeError",
            "message": "Cannot read properties of undefined",
            "url": "http://localhost/agents",
            "userAgent": "Chrome/test",
            "release": "dev",
            "stack": "at renderAgents:123",
            "context": {"componentStack": "<Agents>"},
            "user_id": "u-1",
            "business_id": "biz-1",
        })
        conn = sqlite3.connect(db)
        rows = conn.execute(f"SELECT name, message, business_id FROM {err.TABLE}").fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0][0] == "TypeError"
        assert "Cannot read" in rows[0][1]
        assert rows[0][2] == "biz-1"


def test_submit_error_swallows_bad_input():
    with tempfile.TemporaryDirectory() as tmp:
        err = _fresh(os.path.join(tmp, "nexus.db"))
        # Returns 200-shaped dict even for garbage input.
        result = err.submit_error({"message": None, "stack": {"nested": "allowed"}})
        assert result == {"ok": True}


def test_long_fields_are_trimmed():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        err = _fresh(db)
        err.submit_error({
            "message": "x" * 10000,
            "stack":   "y" * 10000,
        })
        conn = sqlite3.connect(db)
        row = conn.execute(f"SELECT LENGTH(message), LENGTH(stack) FROM {err.TABLE}").fetchone()
        conn.close()
        assert row[0] <= err._MAX_FIELD_CHARS
        assert row[1] <= err._MAX_FIELD_CHARS


def test_recent_orders_newest_first():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        err = _fresh(db)
        for i in range(3):
            err.submit_error({"message": f"err-{i}"})
        # Call `recent` directly with a fake ctx (the function expects a dict)
        rows = err.recent(limit=10, ctx={"business_role": "owner", "user": {"id": "u"}, "business_id": "b"})
        assert len(rows) == 3
        # Newest-first: last inserted appears first
        assert rows[0]["message"] == "err-2"
        assert rows[-1]["message"] == "err-0"


def test_recent_blocks_non_admin():
    with tempfile.TemporaryDirectory() as tmp:
        err = _fresh(os.path.join(tmp, "nexus.db"))
        from fastapi import HTTPException
        import pytest
        with pytest.raises(HTTPException) as exc:
            err.recent(limit=5, ctx={"business_role": "member", "user": {"id": "u"}, "business_id": "b"})
        assert exc.value.status_code == 403
