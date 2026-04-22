"""
File Dispatcher — saves generated files to outputs/ with timestamps.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from loguru import logger

from config.settings import OUTPUTS_DIR, REPORTS_DIR


def save_file(source_path: str, subfolder: str = "") -> str:
    """
    Copy or move a file to outputs/ (with optional subfolder).
    Returns the absolute destination path.
    """
    src = Path(source_path)
    dest_dir = Path(OUTPUTS_DIR) / subfolder if subfolder else Path(OUTPUTS_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_name = f"{src.stem}_{timestamp}{src.suffix}"
    dest = dest_dir / dest_name

    shutil.copy2(str(src), str(dest))
    logger.info(f"[Dispatcher] Saved: {dest}")
    return str(dest.resolve())


def save_bytes(data: bytes, filename: str, subfolder: str = "") -> str:
    """Save raw bytes to a file in outputs/."""
    dest_dir = Path(OUTPUTS_DIR) / subfolder if subfolder else Path(OUTPUTS_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    dest.write_bytes(data)
    logger.info(f"[Dispatcher] Saved bytes: {dest}")
    return str(dest.resolve())


def get_recent_outputs(n: int = 5, subfolder: str = "") -> List[dict]:
    """List the n most recently modified files in outputs/."""
    base = Path(OUTPUTS_DIR) / subfolder if subfolder else Path(OUTPUTS_DIR)
    if not base.exists():
        return []
    files = sorted(
        [f for f in base.rglob("*") if f.is_file()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return [
        {
            "path": str(f),
            "name": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        }
        for f in files[:n]
    ]


def cleanup_old_outputs(days: int = 7) -> int:
    """Remove files older than `days` days from outputs/. Returns count deleted."""
    cutoff = datetime.now() - timedelta(days=days)
    deleted = 0
    base = Path(OUTPUTS_DIR)
    if not base.exists():
        return 0
    for f in base.rglob("*"):
        if f.is_file():
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                try:
                    f.unlink()
                    deleted += 1
                except Exception as e:
                    logger.warning(f"[Dispatcher] Could not delete {f}: {e}")
    logger.info(f"[Dispatcher] Cleaned up {deleted} files older than {days} days.")
    return deleted
