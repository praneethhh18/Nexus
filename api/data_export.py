"""
Workspace data export — bundles every record a business owns into a ZIP of
CSVs. Intentionally simple: reads each known tenant-scoped table directly
from SQLite and streams one CSV per table into an in-memory ZIP.

Scope:
    - Business-scoped tables only (filters by business_id).
    - No Chroma vectors, no model weights, no cloud audit — those are global
      or regenerable.
    - Tags and tag assignments ride along so the user keeps their labels.

Triggered by GET /api/export/all. Admin/owner only — verified in server.py
before calling this module.
"""
from __future__ import annotations

import csv
import io
import sqlite3
import zipfile
from datetime import datetime
from typing import List, Tuple

from loguru import logger

from config.settings import DB_PATH

# (table_name, filter_column) — None filter means "whole table" (tags table has
# business_id too; assignments table joins through tags).
EXPORTED_TABLES: List[Tuple[str, str]] = [
    ("nexus_businesses",          "id"),
    ("nexus_business_members",    "business_id"),
    ("nexus_contacts",            "business_id"),
    ("nexus_companies",           "business_id"),
    ("nexus_deals",               "business_id"),
    ("nexus_tasks",               "business_id"),
    ("nexus_invoices",            "business_id"),
    ("nexus_invoice_items",       "business_id"),
    ("nexus_documents",           "business_id"),
    ("nexus_conversations",       "business_id"),
    ("nexus_messages",            "business_id"),
    ("nexus_audit_log",           "business_id"),
    ("nexus_approvals",           "business_id"),
    ("nexus_notifications",      "business_id"),
    ("nexus_briefings",           "business_id"),
    ("nexus_agent_runs",          "business_id"),
    ("nexus_agent_personas",      "business_id"),
    ("nexus_business_memory",     "business_id"),
    ("nexus_query_history",       "business_id"),
    ("nexus_tags",                "business_id"),
]


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ? LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def _filter_column_exists(conn: sqlite3.Connection, table: str, col: str) -> bool:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return col in cols


def _write_table_csv(conn: sqlite3.Connection, table: str, filter_col: str,
                     business_id: str, zf: zipfile.ZipFile) -> int:
    if not _table_exists(conn, table):
        return 0
    if not _filter_column_exists(conn, table, filter_col):
        return 0

    rows = conn.execute(
        f"SELECT * FROM {table} WHERE {filter_col} = ?",
        (business_id,),
    ).fetchall()
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(cols)
    for r in rows:
        writer.writerow(["" if v is None else v for v in r])
    zf.writestr(f"{table}.csv", buf.getvalue())
    return len(rows)


def _write_tag_assignments(conn: sqlite3.Connection, business_id: str,
                           zf: zipfile.ZipFile) -> int:
    """Tag assignments don't carry business_id directly — join through tags."""
    if not _table_exists(conn, "nexus_tag_assignments"):
        return 0
    rows = conn.execute(
        """
        SELECT a.tag_id, a.entity_type, a.entity_id, a.created_at
          FROM nexus_tag_assignments a
          JOIN nexus_tags t ON t.id = a.tag_id
         WHERE t.business_id = ?
        """,
        (business_id,),
    ).fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["tag_id", "entity_type", "entity_id", "created_at"])
    for r in rows:
        writer.writerow(["" if v is None else v for v in r])
    zf.writestr("nexus_tag_assignments.csv", buf.getvalue())
    return len(rows)


def build_export_zip(business_id: str) -> bytes:
    """Build a ZIP archive of the business's data. Returns the bytes."""
    mem = io.BytesIO()
    totals: dict = {}
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as zf:
        # README so the user knows what they're looking at.
        readme = (
            "NexusAgent — Workspace Export\n"
            f"Generated: {datetime.utcnow().isoformat()}Z\n"
            f"Business ID: {business_id}\n\n"
            "Each CSV corresponds to one table, filtered to records owned by this "
            "business. Re-import is not yet automated — this archive is for your "
            "own backup or portability.\n"
        )
        zf.writestr("README.txt", readme)

        conn = sqlite3.connect(DB_PATH)
        try:
            for table, filter_col in EXPORTED_TABLES:
                try:
                    n = _write_table_csv(conn, table, filter_col, business_id, zf)
                    totals[table] = n
                except Exception as e:
                    logger.warning(f"[Export] {table} failed: {e}")
                    totals[table] = f"error: {e}"
            try:
                totals["nexus_tag_assignments"] = _write_tag_assignments(conn, business_id, zf)
            except Exception as e:
                logger.warning(f"[Export] tag_assignments failed: {e}")
        finally:
            conn.close()

        # Manifest summarising what was exported.
        lines = ["table,rows"]
        for t, n in totals.items():
            lines.append(f"{t},{n}")
        zf.writestr("manifest.csv", "\n".join(lines))
    return mem.getvalue()
