"""
NexusAgent database backup — SQLite online backup API.

This uses SQLite's `backup()` method which takes a **consistent snapshot**
while the database is being written to. It's much safer than just copying
the .db file, which can corrupt if a write is mid-flight.

Rotation: keeps the last N daily backups, the last M weekly backups.

Usage:
    python tools/backup_db.py                 # run once (for cron/Task Scheduler)
    python tools/backup_db.py --list          # show existing backups
    python tools/backup_db.py --restore FILE  # restore from a backup (prompts)
    python tools/backup_db.py --upload s3://bucket/prefix  # optional: push to S3

Schedule it:
  Linux cron:       0 3 * * *  cd /path/to/NexusAgent && venv/bin/python tools/backup_db.py
  Windows Task Sched: daily at 03:00 → run python.exe tools\backup_db.py
"""
from __future__ import annotations

import argparse
import gzip
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Allow running as a script from project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import DB_PATH

BACKUP_DIR = ROOT / "backups"
KEEP_DAILY = 14      # last 14 daily backups
KEEP_WEEKLY = 8      # plus weekly snapshots going back 8 weeks


def _ensure_dir() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def run_backup(gzip_output: bool = True) -> Path:
    """Take a live SQLite backup + optional gzip. Returns the backup file path."""
    _ensure_dir()
    src = Path(DB_PATH)
    if not src.exists():
        print(f"[backup] Source DB not found: {src}")
        sys.exit(2)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_name = f"nexusagent_{stamp}.db"
    raw_path = BACKUP_DIR / raw_name

    print(f"[backup] Snapshotting {src} → {raw_path}")
    t0 = time.time()

    # Use SQLite's online backup API — safe while other processes are writing
    src_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    dest_conn = sqlite3.connect(str(raw_path))
    try:
        src_conn.backup(dest_conn, pages=200, progress=None)
    finally:
        dest_conn.close()
        src_conn.close()

    size_mb = raw_path.stat().st_size / (1024 * 1024)
    dur = time.time() - t0
    print(f"[backup] Snapshot done — {size_mb:.2f} MB in {dur:.1f}s")

    out_path = raw_path
    if gzip_output:
        gz_path = raw_path.with_suffix(".db.gz")
        with open(raw_path, "rb") as fin, gzip.open(gz_path, "wb", compresslevel=6) as fout:
            shutil.copyfileobj(fin, fout)
        raw_path.unlink()
        out_path = gz_path
        gz_mb = gz_path.stat().st_size / (1024 * 1024)
        print(f"[backup] Compressed → {gz_path.name} ({gz_mb:.2f} MB)")

    _rotate()
    print(f"[backup] Done: {out_path}")
    return out_path


def _rotate() -> None:
    """Keep KEEP_DAILY most recent daily backups, plus weekly ones older than that."""
    _ensure_dir()
    backups = sorted(BACKUP_DIR.glob("nexusagent_*.db*"), key=lambda p: p.stat().st_mtime, reverse=True)

    if len(backups) <= KEEP_DAILY:
        return

    # Keep daily for the most recent KEEP_DAILY files
    keep = set(b.name for b in backups[:KEEP_DAILY])

    # Among older ones, keep one per calendar week for KEEP_WEEKLY weeks
    now = datetime.now()
    weekly_by_week: dict[str, Path] = {}
    for b in backups[KEEP_DAILY:]:
        mtime = datetime.fromtimestamp(b.stat().st_mtime)
        if now - mtime > timedelta(weeks=KEEP_WEEKLY):
            continue
        # Year-week key; keep the newest for each week
        wk = f"{mtime.year}-W{mtime.strftime('%W')}"
        if wk not in weekly_by_week:
            weekly_by_week[wk] = b
            keep.add(b.name)

    for b in backups:
        if b.name not in keep:
            try:
                b.unlink()
                print(f"[backup] Pruned {b.name}")
            except Exception as e:
                print(f"[backup] Prune failed for {b.name}: {e}")


def list_backups() -> None:
    _ensure_dir()
    backups = sorted(BACKUP_DIR.glob("nexusagent_*.db*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not backups:
        print("[backup] No backups yet.")
        return
    print(f"{'Date':<20} {'Size':>10}  File")
    print("-" * 60)
    for b in backups:
        mt = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_mb = b.stat().st_size / (1024 * 1024)
        print(f"{mt:<20} {size_mb:>9.2f}M  {b.name}")


def restore_backup(path: str) -> None:
    """
    Restore the app database from a backup. Moves the existing DB aside first.
    The server MUST be stopped before running this.
    """
    src = Path(path)
    if not src.exists():
        src = BACKUP_DIR / path
    if not src.exists():
        print(f"[restore] File not found: {path}")
        sys.exit(2)

    print(f"[restore] About to restore from: {src}")
    print(f"[restore] Current DB will be moved to: {DB_PATH}.bak")
    print(f"[restore] ⚠  Stop the NexusAgent server before continuing.")
    confirm = input("[restore] Type 'yes' to proceed: ").strip().lower()
    if confirm != "yes":
        print("[restore] Aborted.")
        return

    # Move current DB aside
    cur = Path(DB_PATH)
    if cur.exists():
        bak = cur.with_suffix(cur.suffix + ".bak")
        cur.rename(bak)
        print(f"[restore] Existing DB moved to {bak}")

    # Decompress if needed
    if src.suffix == ".gz":
        target = cur
        with gzip.open(src, "rb") as fin, open(target, "wb") as fout:
            shutil.copyfileobj(fin, fout)
        print(f"[restore] Decompressed to {target}")
    else:
        shutil.copy2(src, cur)
        print(f"[restore] Copied to {cur}")

    print("[restore] ✅ Done. Start the server — it should pick up the restored DB.")


def _maybe_upload(path: Path, destination: str) -> None:
    """Optional S3/GCS upload. Requires boto3 or gcloud CLI."""
    if destination.startswith("s3://"):
        try:
            import boto3
            bucket_prefix = destination[5:]
            bucket, _, prefix = bucket_prefix.partition("/")
            key = f"{prefix.rstrip('/')}/{path.name}" if prefix else path.name
            s3 = boto3.client("s3")
            s3.upload_file(str(path), bucket, key)
            print(f"[backup] Uploaded → s3://{bucket}/{key}")
        except Exception as e:
            print(f"[backup] S3 upload failed: {e}")
    else:
        print(f"[backup] Unknown destination scheme: {destination}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--list", action="store_true", help="List existing backups")
    p.add_argument("--restore", metavar="FILE", help="Restore from a backup file")
    p.add_argument("--no-gzip", action="store_true", help="Skip compression")
    p.add_argument("--upload", metavar="DEST", help="Upload to s3://bucket/prefix after backup")
    args = p.parse_args()

    if args.list:
        list_backups()
        return
    if args.restore:
        restore_backup(args.restore)
        return

    out = run_backup(gzip_output=not args.no_gzip)
    if args.upload:
        _maybe_upload(out, args.upload)


if __name__ == "__main__":
    main()
