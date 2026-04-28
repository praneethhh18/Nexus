"""
Full-workspace backup — disaster-recovery snapshot.

Differs from `/api/export/all` (CSV portability) in two ways:
  1. Includes the raw SQLite database via SQLite's `VACUUM INTO` so the
     snapshot is self-consistent even if other connections are writing.
  2. Includes the ChromaDB vector store so RAG embeddings survive a
     restore — re-ingesting documents would otherwise be required.

The result is a single ZIP that captures everything needed to spin up
this exact workspace on a new machine. Restore is a follow-up endpoint
(needs careful handling — locking the app, version checks, transactional
file swap) — for v1, export-only is the correct shipping unit.

Auth: owner/admin only — the backup contains every business in the DB,
which crosses tenant boundaries. The endpoint is therefore gated on the
caller's *user-level* admin role, not the business role.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from api.auth import get_current_user
from config.settings import DB_PATH, CHROMA_PATH

router = APIRouter(tags=["backup"])

# Backup format version. Bump when the layout / file names change so a
# future restore endpoint knows whether it can read the archive.
BACKUP_VERSION = 1


def _safe_unlink(path: str) -> None:
    """Best-effort cleanup of the staged backup file after streaming."""
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except Exception as e:
        logger.warning(f"[Backup] could not delete temp file {path}: {e}")


def _vacuum_snapshot(db_path: str, dest: Path) -> int:
    """
    SQLite's VACUUM INTO produces a clean, defragmented copy without holding
    a write lock against other connections. Returns the bytes written.
    """
    conn = sqlite3.connect(db_path)
    try:
        # VACUUM INTO requires the destination not to exist yet.
        if dest.exists():
            dest.unlink()
        conn.execute(f"VACUUM INTO '{str(dest).replace(chr(39), chr(39) * 2)}'")
    finally:
        conn.close()
    return dest.stat().st_size if dest.exists() else 0


def _build_backup_zip(staging: Path) -> Path:
    """
    Build the backup zip in a staging dir. Returns the zip path.

    Layout inside the zip:
        manifest.json
        nexusagent.db          (VACUUM INTO snapshot)
        chroma_db/...          (verbatim copy, omitted if folder doesn't exist)
        README.txt             (one-paragraph "what this is")
    """
    snapshot_path = staging / "nexusagent.db"
    snapshot_size = _vacuum_snapshot(DB_PATH, snapshot_path)

    chroma_dir = Path(CHROMA_PATH)
    chroma_files: list = []
    if chroma_dir.exists() and chroma_dir.is_dir():
        for p in chroma_dir.rglob("*"):
            if p.is_file():
                chroma_files.append(p)

    chroma_total = sum(p.stat().st_size for p in chroma_files)

    manifest = {
        "format": "nexusagent-backup",
        "version": BACKUP_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "host": os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME", ""),
        "db": {
            "filename": "nexusagent.db",
            "bytes":    snapshot_size,
        },
        "chroma": {
            "included":  bool(chroma_files),
            "file_count": len(chroma_files),
            "bytes":     chroma_total,
        },
        "notes": (
            "Disaster-recovery snapshot. Restore on a fresh install by "
            "stopping the server, replacing data/nexusagent.db with the "
            "bundled copy, and replacing the chroma_db/ folder. A guided "
            "restore endpoint is on the roadmap."
        ),
    }

    readme = (
        "NexusAgent — Full Backup\n"
        f"Created: {manifest['created_at']}\n"
        f"DB: {snapshot_size:,} bytes  ·  Chroma: {chroma_total:,} bytes "
        f"({len(chroma_files)} files)\n\n"
        "What's inside:\n"
        "  manifest.json   — version + sizes + creation time\n"
        "  nexusagent.db   — SQLite database (clean VACUUM INTO snapshot)\n"
        "  chroma_db/      — vector store for the RAG knowledge base\n\n"
        "How to restore (manual, until the restore endpoint ships):\n"
        "  1. Stop the NexusAgent server (uvicorn / start.bat).\n"
        "  2. Back up your existing data/ and chroma_db/ folders.\n"
        "  3. Replace data/nexusagent.db with the file from this zip.\n"
        "  4. Replace the chroma_db/ folder with the one from this zip.\n"
        "  5. Restart. Login should work with your previous credentials.\n"
    )

    zip_path = staging / "nexus_backup.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("README.txt", readme)
        zf.write(snapshot_path, "nexusagent.db")
        for p in chroma_files:
            arcname = "chroma_db/" + str(p.relative_to(chroma_dir)).replace(os.sep, "/")
            zf.write(p, arcname)

    # Drop the staged DB snapshot now that it's in the zip.
    try:
        snapshot_path.unlink()
    except Exception:
        pass

    return zip_path


@router.post("/api/admin/backup")
def create_backup(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """
    Build and stream a full-workspace backup ZIP.

    Owner/admin only — the backup spans every business in the DB.
    """
    if user["role"] not in ("admin", "owner"):
        raise HTTPException(403, "Only admins / owners can create a full backup")

    # Stage in a temp dir so we can clean it up after streaming. Using
    # a real file (not BytesIO) keeps memory bounded for ~GB workspaces.
    staging = Path(tempfile.mkdtemp(prefix="nexus_backup_"))
    try:
        zip_path = _build_backup_zip(staging)
    except Exception as e:
        # Cleanup before propagating
        try: shutil.rmtree(staging, ignore_errors=True)
        except Exception: pass
        logger.exception("[Backup] build failed")
        raise HTTPException(500, f"Backup failed: {e}")

    # Best-effort cleanup of the staging dir AFTER the response is fully sent.
    background_tasks.add_task(shutil.rmtree, str(staging), ignore_errors=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"nexus-backup-{stamp}.zip",
    )


@router.get("/api/admin/backup/info")
def backup_info(user: dict = Depends(get_current_user)):
    """
    Estimate the backup size without actually creating it. Useful for the
    Settings UI to warn users about a multi-gigabyte download.
    """
    if user["role"] not in ("admin", "owner"):
        raise HTTPException(403, "Only admins / owners can inspect backup state")

    db_bytes = 0
    try:
        if Path(DB_PATH).exists():
            db_bytes = Path(DB_PATH).stat().st_size
    except Exception:
        pass

    chroma_bytes = 0
    chroma_files = 0
    chroma_dir = Path(CHROMA_PATH)
    if chroma_dir.exists() and chroma_dir.is_dir():
        for p in chroma_dir.rglob("*"):
            if p.is_file():
                chroma_files += 1
                try: chroma_bytes += p.stat().st_size
                except Exception: pass

    return {
        "version": BACKUP_VERSION,
        "db_bytes": db_bytes,
        "chroma_bytes": chroma_bytes,
        "chroma_files": chroma_files,
        # Compressed estimate — DB and parquet compress ~30%, conservative.
        "estimated_zip_bytes": int(0.7 * (db_bytes + chroma_bytes)),
    }
