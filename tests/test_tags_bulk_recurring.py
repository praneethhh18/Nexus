"""Tests for tags, bulk task actions, recurring tasks, and workspace export."""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
import zipfile
import io


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import tags as _tags
    importlib.reload(_tags)
    from api import data_export as _export
    importlib.reload(_export)
    # tasks imports from the settings module lazily; keep a handle
    from api import tasks as _tasks
    importlib.reload(_tasks)
    return _tags, _tasks, _export


# ── Tags ────────────────────────────────────────────────────────────────────
def test_create_and_list_tag():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        tags, _, _ = _fresh(db)

        t = tags.create_tag("biz-1", "Priority")
        assert t["name"] == "Priority"
        assert t["color"].startswith("#")
        listed = tags.list_tags("biz-1")
        assert len(listed) == 1
        assert listed[0]["name"] == "Priority"
        assert listed[0]["usage_count"] == 0


def test_duplicate_tag_returns_existing():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        tags, _, _ = _fresh(db)

        t1 = tags.create_tag("biz-1", "VIP")
        t2 = tags.create_tag("biz-1", "vip")  # case-insensitive match
        assert t1["id"] == t2["id"]


def test_tag_assignment_lifecycle():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        tags, _, _ = _fresh(db)

        t = tags.create_tag("biz-1", "Urgent")
        tags.assign("biz-1", t["id"], "task", "task-1")
        assigned = tags.tags_for("biz-1", "task", "task-1")
        assert len(assigned) == 1
        assert assigned[0]["name"] == "Urgent"

        tags.unassign("biz-1", t["id"], "task", "task-1")
        assert tags.tags_for("biz-1", "task", "task-1") == []


def test_set_tags_replaces_full_set():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        tags, _, _ = _fresh(db)

        a = tags.create_tag("biz-1", "A")
        b = tags.create_tag("biz-1", "B")
        c = tags.create_tag("biz-1", "C")
        tags.set_tags("biz-1", "contact", "c-1", [a["id"], b["id"]])
        current = {t["name"] for t in tags.tags_for("biz-1", "contact", "c-1")}
        assert current == {"A", "B"}

        tags.set_tags("biz-1", "contact", "c-1", [c["id"]])
        current = {t["name"] for t in tags.tags_for("biz-1", "contact", "c-1")}
        assert current == {"C"}


def test_tags_isolated_per_business():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        tags, _, _ = _fresh(db)

        a = tags.create_tag("biz-a", "Shared")
        b = tags.create_tag("biz-b", "Shared")
        assert a["id"] != b["id"]
        # Cross-tenant assignment must be refused
        import pytest
        with pytest.raises(ValueError):
            tags.assign("biz-b", a["id"], "task", "t1")


def test_invalid_entity_type_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        tags, _, _ = _fresh(db)
        import pytest
        with pytest.raises(ValueError):
            tags.tags_for("biz-1", "badtype", "x")


def test_bulk_tags_for():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        tags, _, _ = _fresh(db)

        a = tags.create_tag("biz-1", "A")
        b = tags.create_tag("biz-1", "B")
        tags.assign("biz-1", a["id"], "task", "t1")
        tags.assign("biz-1", b["id"], "task", "t1")
        tags.assign("biz-1", a["id"], "task", "t2")

        out = tags.bulk_tags_for("biz-1", "task", ["t1", "t2", "t3"])
        assert len(out["t1"]) == 2
        assert len(out["t2"]) == 1
        assert out["t3"] == []


# ── Recurring tasks ─────────────────────────────────────────────────────────
def test_recurring_task_spawns_next_occurrence():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, _ = _fresh(db)

        t = tasks.create_task("biz-1", "user-1", {
            "title": "Weekly standup notes",
            "recurrence": "weekly",
            "due_date": "2026-01-05",
        })
        # Mark done — should spawn next occurrence
        tasks.update_task("biz-1", t["id"], {"status": "done"})
        # List all tasks for biz
        all_tasks = tasks.list_tasks("biz-1", limit=100)
        # Original + next = 2
        assert len(all_tasks) == 2
        open_one = [x for x in all_tasks if x["status"] == "open"][0]
        assert open_one["recurrence"] == "weekly"
        assert open_one["due_date"] == "2026-01-12"  # +7 days


def test_non_recurring_task_does_not_spawn():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, _ = _fresh(db)

        t = tasks.create_task("biz-1", "user-1", {
            "title": "One-off",
            "recurrence": "none",
            "due_date": "2026-01-05",
        })
        tasks.update_task("biz-1", t["id"], {"status": "done"})
        all_tasks = tasks.list_tasks("biz-1", limit=100)
        assert len(all_tasks) == 1


def test_recurring_spawn_is_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, _ = _fresh(db)

        t = tasks.create_task("biz-1", "user-1", {
            "title": "Daily status",
            "recurrence": "daily",
            "due_date": "2026-01-05",
        })
        tasks.update_task("biz-1", t["id"], {"status": "done"})
        # Calling spawn explicitly shouldn't create a second pending task
        tasks.spawn_next_if_recurring("biz-1", t["id"])
        all_tasks = tasks.list_tasks("biz-1", limit=100)
        assert len(all_tasks) == 2  # original + one next, not three


# ── Bulk task actions ───────────────────────────────────────────────────────
def test_bulk_delete_tasks():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, _ = _fresh(db)

        ids = []
        for i in range(3):
            ids.append(tasks.create_task("biz-1", "u", {"title": f"T{i}"})["id"])

        n = tasks.bulk_delete("biz-1", ids[:2])
        assert n == 2
        left = tasks.list_tasks("biz-1", limit=100)
        assert len(left) == 1


def test_bulk_update_status():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, _ = _fresh(db)

        ids = [tasks.create_task("biz-1", "u", {"title": f"T{i}"})["id"] for i in range(3)]
        n = tasks.bulk_update_status("biz-1", ids, "done")
        assert n == 3
        for tid in ids:
            assert tasks.get_task("biz-1", tid)["status"] == "done"


def test_bulk_update_status_rejects_invalid():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, _ = _fresh(db)
        import pytest
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            tasks.bulk_update_status("biz-1", ["x"], "invalid-status")


def test_bulk_delete_scoped_to_business():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, _ = _fresh(db)

        t_a = tasks.create_task("biz-a", "u", {"title": "A"})
        t_b = tasks.create_task("biz-b", "u", {"title": "B"})
        # Deleting from biz-a with biz-b id should be a no-op
        n = tasks.bulk_delete("biz-a", [t_b["id"]])
        assert n == 0
        assert tasks.get_task("biz-b", t_b["id"])["title"] == "B"


# ── Workspace export ────────────────────────────────────────────────────────
def test_export_zip_has_readme_and_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, export = _fresh(db)

        tasks.create_task("biz-1", "u", {"title": "Export me"})
        blob = export.build_export_zip("biz-1")
        zf = zipfile.ZipFile(io.BytesIO(blob))
        names = zf.namelist()
        assert "README.txt" in names
        assert "manifest.csv" in names
        # Tasks table should be in the archive
        assert "nexus_tasks.csv" in names
        contents = zf.read("nexus_tasks.csv").decode()
        assert "Export me" in contents


def test_export_excludes_other_business_data():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, tasks, export = _fresh(db)

        tasks.create_task("biz-a", "u", {"title": "Mine"})
        tasks.create_task("biz-b", "u", {"title": "Theirs"})
        blob = export.build_export_zip("biz-a")
        zf = zipfile.ZipFile(io.BytesIO(blob))
        csv_contents = zf.read("nexus_tasks.csv").decode()
        assert "Mine" in csv_contents
        assert "Theirs" not in csv_contents
