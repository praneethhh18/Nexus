"""
Document collections — group documents by topic/project so RAG can answer
narrow questions ("what does our HR handbook say about leave?") without
getting distracted by unrelated material.

Also surfaces document expiry: if a document has `expires_at` in the past,
it's considered stale and the UI can show a warning + the retriever can
optionally exclude it.

Collections themselves are lightweight — just a name, color, description.
A document can belong to at most one collection (nullable FK). RAG cross-
collection search is achieved by passing a list of collection IDs at query
time rather than modeling many-to-many here.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from config.settings import DB_PATH

TABLE = "nexus_document_collections"

# Curated palette to keep collection chips visually coherent.
_PALETTE = [
    "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b",
    "#ef4444", "#ec4899", "#06b6d4", "#a855f7",
]


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id          TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            name        TEXT NOT NULL,
            color       TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at  TEXT NOT NULL,
            UNIQUE (business_id, name COLLATE NOCASE)
        )
    """)
    conn.commit()
    return conn


def _docs_conn() -> sqlite3.Connection:
    """Shared accessor so callers don't need to touch the documents module
    just to read document rows. Ensures the nexus_documents columns exist."""
    from api import documents as _docs
    conn = _docs._get_conn()
    return conn


def _pick_color(business_id: str) -> str:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT color, COUNT(*) AS n FROM {TABLE} "
            f"WHERE business_id = ? GROUP BY color",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    used = {r["color"]: int(r["n"]) for r in rows}
    return min(_PALETTE, key=lambda c: used.get(c, 0))


def _validate_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Collection name cannot be empty")
    if len(name) > 60:
        raise ValueError("Collection name is too long (max 60 chars)")
    return name


# ── Collection CRUD ─────────────────────────────────────────────────────────
def list_collections(business_id: str) -> List[Dict]:
    """Every collection in this business with doc counts + stale counts."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT id, name, color, description, created_at FROM {TABLE} "
            f"WHERE business_id = ? ORDER BY name COLLATE NOCASE",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()

    out = []
    d = _docs_conn()
    d.row_factory = sqlite3.Row
    try:
        now = datetime.utcnow().isoformat()
        for r in rows:
            counts = d.execute(
                "SELECT COUNT(*) AS total, "
                "SUM(CASE WHEN expires_at IS NOT NULL AND expires_at < ? THEN 1 ELSE 0 END) AS stale "
                "FROM nexus_documents WHERE business_id = ? AND collection_id = ?",
                (now, business_id, r["id"]),
            ).fetchone()
            out.append({
                "id":          r["id"],
                "name":        r["name"],
                "color":       r["color"],
                "description": r["description"] or "",
                "created_at":  r["created_at"],
                "document_count": int(counts["total"] or 0),
                "stale_count":    int(counts["stale"] or 0),
            })
    finally:
        d.close()
    return out


def create_collection(business_id: str, name: str, description: str = "",
                      color: Optional[str] = None) -> Dict:
    name = _validate_name(name)
    if not color:
        color = _pick_color(business_id)
    cid = f"col-{uuid.uuid4().hex[:10]}"
    now = datetime.utcnow().isoformat()
    conn = _conn()
    try:
        try:
            conn.execute(
                f"INSERT INTO {TABLE} (id, business_id, name, color, description, created_at) "
                f"VALUES (?, ?, ?, ?, ?, ?)",
                (cid, business_id, name, color, (description or "").strip()[:500], now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            row = conn.execute(
                f"SELECT id, name, color, description, created_at FROM {TABLE} "
                f"WHERE business_id = ? AND name = ? COLLATE NOCASE",
                (business_id, name),
            ).fetchone()
            if row:
                return {"id": row[0], "name": row[1], "color": row[2],
                        "description": row[3] or "", "created_at": row[4],
                        "document_count": 0, "stale_count": 0}
            raise
    finally:
        conn.close()
    return {"id": cid, "name": name, "color": color, "description": description,
            "created_at": now, "document_count": 0, "stale_count": 0}


def delete_collection(business_id: str, collection_id: str) -> None:
    """Drop the collection — documents unassign (set collection_id = NULL)."""
    conn = _conn()
    try:
        conn.execute(
            f"DELETE FROM {TABLE} WHERE id = ? AND business_id = ?",
            (collection_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()
    d = _docs_conn()
    try:
        d.execute(
            "UPDATE nexus_documents SET collection_id = NULL "
            "WHERE business_id = ? AND collection_id = ?",
            (business_id, collection_id),
        )
        d.commit()
    finally:
        d.close()


# ── Assignment + expiry ─────────────────────────────────────────────────────
def _assert_collection(conn: sqlite3.Connection, business_id: str,
                       collection_id: Optional[str]) -> None:
    if collection_id is None:
        return
    row = conn.execute(
        f"SELECT 1 FROM {TABLE} WHERE id = ? AND business_id = ?",
        (collection_id, business_id),
    ).fetchone()
    if not row:
        raise ValueError("Collection not found for this business")


def assign_document(business_id: str, document_id: str,
                    collection_id: Optional[str]) -> None:
    """Move a document into a collection (or None to unassign)."""
    conn = _conn()
    try:
        _assert_collection(conn, business_id, collection_id)
    finally:
        conn.close()
    d = _docs_conn()
    try:
        d.execute(
            "UPDATE nexus_documents SET collection_id = ? "
            "WHERE id = ? AND business_id = ?",
            (collection_id, document_id, business_id),
        )
        d.commit()
    finally:
        d.close()


def set_expiry(business_id: str, document_id: str,
               expires_at: Optional[str]) -> None:
    """Set or clear the expiry date (ISO format). Clear by passing None."""
    if expires_at:
        try:
            datetime.fromisoformat(expires_at)
        except Exception:
            raise ValueError("expires_at must be an ISO datetime")
    d = _docs_conn()
    try:
        d.execute(
            "UPDATE nexus_documents SET expires_at = ? "
            "WHERE id = ? AND business_id = ?",
            (expires_at, document_id, business_id),
        )
        d.commit()
    finally:
        d.close()


def list_documents_in_collection(business_id: str, collection_id: str,
                                 include_stale: bool = True) -> List[Dict]:
    d = _docs_conn()
    d.row_factory = sqlite3.Row
    try:
        sql = ("SELECT id, title, format, created_at, expires_at FROM nexus_documents "
               "WHERE business_id = ? AND collection_id = ?")
        params = [business_id, collection_id]
        if not include_stale:
            sql += " AND (expires_at IS NULL OR expires_at >= ?)"
            params.append(datetime.utcnow().isoformat())
        sql += " ORDER BY created_at DESC"
        rows = d.execute(sql, params).fetchall()
    finally:
        d.close()
    return [dict(r) for r in rows]


def stale_documents(business_id: str) -> List[Dict]:
    """All documents whose expires_at is in the past."""
    d = _docs_conn()
    d.row_factory = sqlite3.Row
    try:
        rows = d.execute(
            "SELECT id, title, collection_id, expires_at FROM nexus_documents "
            "WHERE business_id = ? AND expires_at IS NOT NULL AND expires_at < ? "
            "ORDER BY expires_at ASC",
            (business_id, datetime.utcnow().isoformat()),
        ).fetchall()
    finally:
        d.close()
    return [dict(r) for r in rows]


# ── Re-ingest ───────────────────────────────────────────────────────────────
def mark_for_reingest(business_id: str, document_id: str) -> Dict:
    """
    Flag a document for re-ingestion. The actual work (re-reading the file,
    re-chunking, re-embedding) is delegated to `rag.ingestion` by the caller
    — this function just clears any stale flag and bumps the updated_at field.

    Returns the updated document row.
    """
    d = _docs_conn()
    d.row_factory = sqlite3.Row
    try:
        row = d.execute(
            "SELECT id, file_path FROM nexus_documents "
            "WHERE id = ? AND business_id = ?",
            (document_id, business_id),
        ).fetchone()
        if not row:
            raise KeyError("Document not found")
        # Clear expiry and touch timestamps to signal a fresh copy.
        d.execute(
            "UPDATE nexus_documents SET expires_at = NULL "
            "WHERE id = ? AND business_id = ?",
            (document_id, business_id),
        )
        d.commit()
    finally:
        d.close()
    return {"ok": True, "document_id": document_id,
            "note": "Marked fresh; caller must re-run ingestion for the file."}
