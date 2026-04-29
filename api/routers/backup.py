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

import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Query
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


# ── RESTORE ─────────────────────────────────────────────────────────────────
# Restoring is the dangerous twin of backing up — it can wipe live data if
# misused. Three layers of safety:
#
#   1. Owner/admin gate (same as backup).
#   2. Default `dry_run=true` — validates the zip + manifest, opens the DB
#      to confirm it's a real SQLite file, but doesn't touch anything live.
#      The Settings UI uses dry-run as a "preview" step before the user
#      explicitly opts into the swap.
#   3. Even on `dry_run=false`, we always write a `before-restore` snapshot
#      of the current DB and chroma_db to neighbouring paths the response
#      reports back, so the user has a one-step revert.
#
# After a successful swap the server should be restarted — open SQLite
# handles can prevent atomic file replacement on Windows, and the running
# process holds an open ChromaDB connection. The response surfaces this
# instruction explicitly.

def _validate_zip(zip_path: Path) -> dict:
    """Open the zip, parse manifest, sanity-check the DB. Never modifies
    anything on disk outside the zip's own staging dir."""
    if not zipfile.is_zipfile(zip_path):
        raise HTTPException(400, "That file isn't a valid zip.")

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
        if "manifest.json" not in names:
            raise HTTPException(400, "Missing manifest.json — this doesn't look like a NexusAgent backup.")
        if "nexusagent.db" not in names:
            raise HTTPException(400, "Missing nexusagent.db — backup is incomplete.")

        try:
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        except Exception as e:
            raise HTTPException(400, f"manifest.json is malformed: {e}")

        if manifest.get("format") != "nexusagent-backup":
            raise HTTPException(400, "Manifest doesn't claim to be a NexusAgent backup.")
        backup_version = int(manifest.get("version") or 0)
        if backup_version > BACKUP_VERSION:
            raise HTTPException(
                400,
                f"This backup was made with a newer NexusAgent version "
                f"(format v{backup_version}). Upgrade the server before restoring."
            )

        chroma_files = [n for n in names if n.startswith("chroma_db/")]

    return {
        "manifest": manifest,
        "has_chroma": bool(chroma_files),
        "chroma_file_count": len(chroma_files),
    }


def _verify_db_blob(db_path: Path) -> int:
    """Open the staged DB and confirm it's a real SQLite file with a sane
    schema. Returns the row count of `nexus_users` as a smoke check.
    Raises HTTPException(400) on anything suspicious."""
    try:
        conn = sqlite3.connect(str(db_path))
    except Exception as e:
        raise HTTPException(400, f"Couldn't open the DB inside the zip: {e}")
    try:
        # If it's an empty DB or a wildly different schema, this either
        # raises or returns 0 — both are clear "this isn't ours" signals.
        try:
            row = conn.execute("SELECT COUNT(*) FROM nexus_users").fetchone()
        except sqlite3.DatabaseError as e:
            raise HTTPException(400, f"DB inside the zip doesn't have NexusAgent's schema: {e}")
        return int(row[0] or 0)
    finally:
        conn.close()


@router.post("/api/admin/restore")
async def restore_backup(
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="When True (default), validate only — don't replace anything."),
    user: dict = Depends(get_current_user),
):
    """
    Restore a workspace from a previously-downloaded backup zip.

    Default behaviour is `dry_run=true` — the endpoint validates the zip
    and reports what it found without touching live data. Pass
    `dry_run=false` to actually swap files. A `before-restore` snapshot
    is always saved first so the user can revert.

    Restart the server after a successful swap.
    """
    if user["role"] not in ("admin", "owner"):
        raise HTTPException(403, "Only admins / owners can restore.")

    # Stage the upload to a temp dir.
    staging = Path(tempfile.mkdtemp(prefix="nexus_restore_"))
    zip_path = staging / "upload.zip"
    try:
        bytes_written = 0
        with zip_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                bytes_written += len(chunk)
                f.write(chunk)
        if bytes_written == 0:
            raise HTTPException(400, "Empty upload.")

        info = _validate_zip(zip_path)

        # Extract and verify the DB blob lives in staging too.
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extract("nexusagent.db", staging)
        staged_db = staging / "nexusagent.db"
        user_count = _verify_db_blob(staged_db)

        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "manifest": info["manifest"],
                "has_chroma": info["has_chroma"],
                "chroma_file_count": info["chroma_file_count"],
                "user_count_in_backup": user_count,
                "message": (
                    "Validation passed. Re-submit with dry_run=false to perform "
                    "the actual swap. The server will need a restart afterwards."
                ),
            }

        # ── Real restore — save safety snapshots, then swap ─────────────
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        db_safety_path = Path(DB_PATH).with_name(f"{Path(DB_PATH).name}.before-restore.{stamp}")
        chroma_safety_path = None

        # Snapshot current DB. Use VACUUM INTO so we get a clean copy that
        # isn't a partial WAL state, even if other connections are writing.
        try:
            _vacuum_snapshot(DB_PATH, db_safety_path)
        except Exception as e:
            raise HTTPException(500, f"Couldn't save before-restore DB snapshot: {e}")

        # Replace the live DB. On Windows, an open file handle from a
        # running process can prevent shutil.copy/move; we use Path.replace
        # which is atomic on POSIX and best-effort on Windows.
        try:
            # copy first then atomic-rename onto live path
            tmp_dest = Path(DB_PATH).with_suffix(Path(DB_PATH).suffix + ".incoming")
            shutil.copy2(staged_db, tmp_dest)
            tmp_dest.replace(Path(DB_PATH))
        except PermissionError:
            raise HTTPException(
                503,
                "Couldn't replace the live DB — Windows is holding the file open. "
                f"Stop the server, manually copy {staged_db} over {DB_PATH}, then restart."
            )
        except Exception as e:
            raise HTTPException(500, f"DB swap failed: {e}")

        # ChromaDB folder if present.
        if info["has_chroma"]:
            chroma_dir = Path(CHROMA_PATH)
            if chroma_dir.exists():
                chroma_safety_path = chroma_dir.with_name(f"{chroma_dir.name}.before-restore.{stamp}")
                try:
                    shutil.move(str(chroma_dir), str(chroma_safety_path))
                except Exception as e:
                    logger.warning(f"[Restore] couldn't move existing chroma dir aside: {e}")

            chroma_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for name in zf.namelist():
                    if not name.startswith("chroma_db/"):
                        continue
                    relative = name[len("chroma_db/"):]
                    if not relative:
                        continue
                    dest = chroma_dir / relative
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if name.endswith("/"):
                        continue
                    with zf.open(name) as src, dest.open("wb") as out:
                        shutil.copyfileobj(src, out)

        return {
            "ok": True,
            "dry_run": False,
            "manifest": info["manifest"],
            "user_count_restored": user_count,
            "safety_snapshot_db": str(db_safety_path),
            "safety_snapshot_chroma": str(chroma_safety_path) if chroma_safety_path else None,
            "message": (
                "Restore complete. RESTART THE SERVER for the swap to take "
                "effect everywhere — open SQLite + ChromaDB connections still "
                "point at the old data until processes recycle."
            ),
        }

    finally:
        # Best-effort cleanup of the staging dir. Skipped during dev errors
        # so the staged DB can be inspected if something goes wrong.
        try:
            shutil.rmtree(str(staging), ignore_errors=True)
        except Exception:
            pass
