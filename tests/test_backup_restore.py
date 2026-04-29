"""
Backup → restore round-trip + safety guardrails.

Coverage:
  - dry_run validates manifest + DB without touching anything live
  - real restore writes a before-restore snapshot first, then swaps
  - replaced DB has the round-tripped rows (functional round-trip)
  - corrupt zip → 400, no changes
  - bad manifest → 400, no changes
  - DB inside zip with wrong schema → 400, no changes
  - non-admin → 403
  - newer-format backup (version > BACKUP_VERSION) → rejected
"""
from __future__ import annotations

import asyncio
import importlib
import io
import json
import os
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException


def _fresh(db_path: str, chroma_path: str | None = None):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    if chroma_path is not None:
        _s.CHROMA_PATH = chroma_path
    from api.routers import backup as _backup
    importlib.reload(_backup)
    return _backup


def _seed_real_db(db_path: str) -> None:
    """Drop a NexusAgent-shaped DB in place — needs nexus_users for the
    schema verification step to pass."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("""
            CREATE TABLE nexus_users (id TEXT PRIMARY KEY, email TEXT, name TEXT);
            INSERT INTO nexus_users VALUES ('u1', 'a@example.com', 'Alice');
            INSERT INTO nexus_users VALUES ('u2', 'b@example.com', 'Bob');
            CREATE TABLE seed_marker (id INTEGER PRIMARY KEY, note TEXT);
            INSERT INTO seed_marker (note) VALUES ('hello'), ('world');
        """)
        conn.commit()
    finally:
        conn.close()


class _UploadShim:
    """Mimics FastAPI's UploadFile interface enough for our endpoint:
    awaitable .read(chunk_size=...) over an in-memory buffer.

    Reads upfront so we don't hold a Windows file lock on the zip during
    test cleanup (the temp dir teardown chokes on locked files)."""
    def __init__(self, path: Path):
        self._buf = io.BytesIO(path.read_bytes())

    async def read(self, n: int = -1) -> bytes:
        return self._buf.read(n if n and n > 0 else -1)


def _build_backup_via_module(backup_mod, tmp: Path) -> Path:
    """Use the backup module's own builder so we round-trip exactly the
    format restore expects."""
    staging = Path(tempfile.mkdtemp(prefix="nx_test_backup_", dir=tmp))
    return backup_mod._build_backup_zip(staging)


def _ctx(role="admin"):
    return {"id": "u-test", "role": role, "name": "Tester"}


# ── 1. dry_run validates without touching anything ─────────────────────────
def test_dry_run_validates_and_does_not_touch_live_db():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        _seed_real_db(db_path)
        backup = _fresh(db_path, chroma_path=str(tmp_path / "no_chroma_here"))

        zip_path = _build_backup_via_module(backup, tmp_path)
        live_db_before = Path(db_path).read_bytes()

        # Run restore in dry-run mode (default).
        result = asyncio.run(backup.restore_backup(
            file=_UploadShim(zip_path),
            dry_run=True,
            user=_ctx("admin"),
        ))

        assert result["ok"] is True
        assert result["dry_run"] is True
        assert result["user_count_in_backup"] == 2
        assert result["manifest"]["format"] == "nexusagent-backup"
        # Live DB byte-identical → nothing got swapped.
        assert Path(db_path).read_bytes() == live_db_before


# ── 2. Round-trip: real restore replaces DB and saves safety snapshot ──────
def test_real_restore_replaces_db_and_writes_safety_snapshot():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        # Original DB: alice + bob.
        _seed_real_db(db_path)
        backup = _fresh(db_path, chroma_path=str(tmp_path / "no_chroma_here"))
        zip_path = _build_backup_via_module(backup, tmp_path)

        # Now mutate the live DB AFTER the backup so we can prove the
        # restore reverted us to the backup's state.
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("INSERT INTO nexus_users VALUES ('u3', 'c@example.com', 'Carol')")
            conn.commit()
        finally:
            conn.close()

        # Run real restore.
        result = asyncio.run(backup.restore_backup(
            file=_UploadShim(zip_path),
            dry_run=False,
            user=_ctx("admin"),
        ))

        assert result["ok"] is True
        assert result["dry_run"] is False
        # Carol is gone; we're back to alice + bob.
        conn = sqlite3.connect(db_path)
        try:
            rows = [r[0] for r in conn.execute("SELECT email FROM nexus_users ORDER BY id").fetchall()]
        finally:
            conn.close()
        assert rows == ["a@example.com", "b@example.com"]

        # Safety snapshot exists and is openable.
        snap = Path(result["safety_snapshot_db"])
        assert snap.exists()
        snap_conn = sqlite3.connect(str(snap))
        try:
            snap_rows = [r[0] for r in snap_conn.execute("SELECT email FROM nexus_users ORDER BY id").fetchall()]
        finally:
            snap_conn.close()
        # The pre-restore snapshot has Carol.
        assert "c@example.com" in snap_rows


# ── 3. Bad zip → 400, no changes ───────────────────────────────────────────
def test_corrupt_zip_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        _seed_real_db(db_path)
        backup = _fresh(db_path, chroma_path=str(tmp_path / "x"))

        bad = tmp_path / "garbage.zip"
        bad.write_bytes(b"this is not a zip file at all")
        before = Path(db_path).read_bytes()

        with pytest.raises(HTTPException) as exc:
            asyncio.run(backup.restore_backup(
                file=_UploadShim(bad), dry_run=False, user=_ctx("admin"),
            ))
        assert exc.value.status_code == 400
        assert Path(db_path).read_bytes() == before


# ── 4. Manifest claims wrong format → rejected ─────────────────────────────
def test_zip_with_wrong_manifest_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        _seed_real_db(db_path)
        backup = _fresh(db_path, chroma_path=str(tmp_path / "x"))

        bad = tmp_path / "fake.zip"
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("manifest.json", json.dumps({"format": "some-other-tool", "version": 1}))
            zf.writestr("nexusagent.db", b"not a real db")

        with pytest.raises(HTTPException) as exc:
            asyncio.run(backup.restore_backup(
                file=_UploadShim(bad), dry_run=True, user=_ctx("admin"),
            ))
        assert exc.value.status_code == 400


# ── 5. Newer-format backup → rejected ──────────────────────────────────────
def test_newer_format_backup_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        _seed_real_db(db_path)
        backup = _fresh(db_path, chroma_path=str(tmp_path / "x"))

        bad = tmp_path / "futuristic.zip"
        with zipfile.ZipFile(bad, "w") as zf:
            zf.writestr("manifest.json", json.dumps({
                "format": "nexusagent-backup",
                "version": 999,  # way newer than the runtime
            }))
            zf.writestr("nexusagent.db", b"x")

        with pytest.raises(HTTPException) as exc:
            asyncio.run(backup.restore_backup(
                file=_UploadShim(bad), dry_run=True, user=_ctx("admin"),
            ))
        assert exc.value.status_code == 400
        assert "newer" in exc.value.detail.lower()


# ── 6. DB inside zip with wrong schema → rejected ──────────────────────────
def test_zip_db_with_wrong_schema_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        _seed_real_db(db_path)
        backup = _fresh(db_path, chroma_path=str(tmp_path / "x"))

        # Build a valid manifest but a DB with a totally different schema.
        bogus_db = tmp_path / "bogus.db"
        c = sqlite3.connect(str(bogus_db))
        c.execute("CREATE TABLE not_nexus (id INTEGER)")
        c.commit(); c.close()

        bad_zip = tmp_path / "bad-schema.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("manifest.json", json.dumps({
                "format": "nexusagent-backup", "version": 1,
            }))
            zf.write(str(bogus_db), "nexusagent.db")

        with pytest.raises(HTTPException) as exc:
            asyncio.run(backup.restore_backup(
                file=_UploadShim(bad_zip), dry_run=True, user=_ctx("admin"),
            ))
        assert exc.value.status_code == 400


# ── 7. Non-admin → 403 ─────────────────────────────────────────────────────
def test_non_admin_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = str(tmp_path / "nexus.db")
        _seed_real_db(db_path)
        backup = _fresh(db_path, chroma_path=str(tmp_path / "x"))
        zip_path = _build_backup_via_module(backup, tmp_path)

        with pytest.raises(HTTPException) as exc:
            asyncio.run(backup.restore_backup(
                file=_UploadShim(zip_path), dry_run=True,
                user=_ctx("user"),  # not admin/owner
            ))
        assert exc.value.status_code == 403
