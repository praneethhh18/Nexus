"""
Backup export contract.

Verifies that the full-workspace backup endpoint produces a valid,
restorable archive: SQLite snapshot opens, manifest is well-formed,
ChromaDB folder is present when one exists.

Auth-gating tests live alongside the rest of the auth suite — this module
focuses on the file-level correctness of the produced zip.
"""
from __future__ import annotations

import importlib
import io
import json
import os
import sqlite3
import tempfile
import zipfile
from pathlib import Path


def _fresh(db_path: str, chroma_path: str | None = None):
    """Reload the modules that read DB_PATH / CHROMA_PATH at import time.

    `chroma_path=None` means "use whatever settings resolves" (i.e. the real
    chroma_db). Pass an explicit path to point the backup module at a sandbox
    folder for the duration of one test.
    """
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    if chroma_path is not None:
        # Override BEFORE reloading the backup module — it captures CHROMA_PATH
        # at import time via a top-level `from ... import CHROMA_PATH`.
        _s.CHROMA_PATH = chroma_path
    from api.routers import backup as _backup
    importlib.reload(_backup)
    return _backup


def _seed_db(db_path: str) -> None:
    """Drop a non-trivial SQLite file in place so VACUUM INTO has work to do."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("CREATE TABLE seed_marker (id INTEGER PRIMARY KEY, note TEXT)")
        conn.executemany(
            "INSERT INTO seed_marker (note) VALUES (?)",
            [("hello",), ("world",), ("backup",)],
        )
        conn.commit()
    finally:
        conn.close()


def test_backup_zip_contains_manifest_and_db():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "nexus.db")
        _seed_db(db_path)
        backup = _fresh(db_path)

        staging = Path(tempfile.mkdtemp(prefix="nexus_backup_test_", dir=tmp))
        zip_path = backup._build_backup_zip(staging)

        assert zip_path.exists(), "backup zip was not produced"

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = set(zf.namelist())
            assert "manifest.json" in names
            assert "nexusagent.db" in names
            assert "README.txt" in names

            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            assert manifest["format"] == "nexusagent-backup"
            assert manifest["version"] == backup.BACKUP_VERSION
            assert manifest["db"]["filename"] == "nexusagent.db"
            assert manifest["db"]["bytes"] > 0

            # The DB inside the zip must be a real, openable SQLite file.
            db_blob = zf.read("nexusagent.db")

        restored_db = staging / "restored.db"
        restored_db.write_bytes(db_blob)
        conn = sqlite3.connect(str(restored_db))
        try:
            cur = conn.execute("SELECT note FROM seed_marker ORDER BY id")
            rows = [r[0] for r in cur.fetchall()]
        finally:
            conn.close()

        assert rows == ["hello", "world", "backup"], (
            f"Restored DB lost data — got {rows!r}"
        )


def test_backup_zip_omits_chroma_when_absent():
    """If chroma_db doesn't exist, the manifest reflects that and no
    chroma_db/ entries appear in the zip."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "nexus.db")
        _seed_db(db_path)
        backup = _fresh(db_path, chroma_path=str(Path(tmp) / "definitely_not_real"))

        staging = Path(tempfile.mkdtemp(prefix="nexus_backup_test_", dir=tmp))
        zip_path = backup._build_backup_zip(staging)

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert not any(n.startswith("chroma_db/") for n in names)
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["chroma"]["included"] is False
            assert manifest["chroma"]["file_count"] == 0


def test_backup_zip_includes_chroma_when_present():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "nexus.db")
        _seed_db(db_path)

        # Build a plausible chroma_db/ folder layout.
        chroma = Path(tmp) / "chroma_db"
        (chroma / "collection-1").mkdir(parents=True)
        (chroma / "collection-1" / "data.parquet").write_bytes(b"fake-parquet" * 100)
        (chroma / "collection-1" / "index.bin").write_bytes(b"fake-index" * 50)
        (chroma / "chroma.sqlite3").write_bytes(b"fake-sqlite" * 200)

        backup = _fresh(db_path, chroma_path=str(chroma))

        staging = Path(tempfile.mkdtemp(prefix="nexus_backup_test_", dir=tmp))
        zip_path = backup._build_backup_zip(staging)

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            chroma_entries = [n for n in names if n.startswith("chroma_db/")]
            assert "chroma_db/collection-1/data.parquet" in chroma_entries
            assert "chroma_db/collection-1/index.bin" in chroma_entries
            assert "chroma_db/chroma.sqlite3" in chroma_entries

            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["chroma"]["included"] is True
            assert manifest["chroma"]["file_count"] == 3
            assert manifest["chroma"]["bytes"] > 0


def test_vacuum_snapshot_does_not_touch_source_db():
    """VACUUM INTO must NOT modify the source — we rely on this for safety
    while other connections may still be writing."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "nexus.db")
        _seed_db(db_path)
        backup = _fresh(db_path)

        before = Path(db_path).read_bytes()
        dest = Path(tmp) / "snapshot.db"
        backup._vacuum_snapshot(db_path, dest)
        after = Path(db_path).read_bytes()

        assert before == after, "VACUUM INTO must not modify the source DB"
        assert dest.exists() and dest.stat().st_size > 0
