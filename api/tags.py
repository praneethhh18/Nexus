"""
Universal tags — attach user-defined labels to any record in the system.

Design:
    nexus_tags              — (id, business_id, name, color, created_at)
    nexus_tag_assignments   — (tag_id, entity_type, entity_id)

entity_type is a free-form string matching the caller's domain
(`contact`, `task`, `invoice`, `deal`, `document`, ...) so new record types
can be tagged without touching this module.

Tag names are unique per business (case-insensitive). Each tag picks a color
from a curated palette if the caller doesn't specify one — keeps the UI
visually coherent without making users choose hex codes.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import DB_PATH

TAGS_TABLE = "nexus_tags"
ASSIGN_TABLE = "nexus_tag_assignments"

# Curated palette — eight high-contrast colors on the existing dark theme.
_PALETTE = [
    "#8b5cf6",  # violet
    "#3b82f6",  # blue
    "#10b981",  # emerald
    "#f59e0b",  # amber
    "#ef4444",  # red
    "#ec4899",  # pink
    "#06b6d4",  # cyan
    "#a855f7",  # purple
]

# Known entity types — validated so typos don't create phantom tag buckets.
VALID_ENTITY_TYPES = {"contact", "company", "deal", "task", "invoice", "document"}


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TAGS_TABLE} (
            id            TEXT PRIMARY KEY,
            business_id   TEXT NOT NULL,
            name          TEXT NOT NULL,
            color         TEXT NOT NULL,
            created_at    TEXT NOT NULL,
            UNIQUE (business_id, name COLLATE NOCASE)
        )
    """)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {ASSIGN_TABLE} (
            tag_id        TEXT NOT NULL,
            entity_type   TEXT NOT NULL,
            entity_id     TEXT NOT NULL,
            created_at    TEXT NOT NULL,
            PRIMARY KEY (tag_id, entity_type, entity_id)
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{ASSIGN_TABLE}_entity "
        f"ON {ASSIGN_TABLE}(entity_type, entity_id)"
    )
    conn.commit()
    return conn


def _pick_color(business_id: str) -> str:
    """Pick the least-used color from the palette so tags stay distinct."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT color, COUNT(*) AS n FROM {TAGS_TABLE} "
            f"WHERE business_id = ? GROUP BY color",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    used = {r["color"]: int(r["n"]) for r in rows}
    best = min(_PALETTE, key=lambda c: used.get(c, 0))
    return best


def _validate_entity_type(et: str) -> str:
    et = (et or "").strip().lower()
    if et not in VALID_ENTITY_TYPES:
        raise ValueError(f"Unknown entity_type '{et}' — must be one of {sorted(VALID_ENTITY_TYPES)}")
    return et


def _validate_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Tag name cannot be empty")
    if len(name) > 40:
        raise ValueError("Tag name is too long (max 40 chars)")
    return name


# ── Tag CRUD ────────────────────────────────────────────────────────────────
def list_tags(business_id: str) -> List[Dict]:
    """All tags for a business with a count of how many records use each one."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT t.id, t.name, t.color, t.created_at,
                   (SELECT COUNT(*) FROM {ASSIGN_TABLE} a WHERE a.tag_id = t.id) AS usage_count
              FROM {TAGS_TABLE} t
             WHERE t.business_id = ?
             ORDER BY t.name COLLATE NOCASE
            """,
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def create_tag(business_id: str, name: str, color: Optional[str] = None) -> Dict:
    name = _validate_name(name)
    if not color:
        color = _pick_color(business_id)
    tag_id = uuid.uuid4().hex
    now = datetime.utcnow().isoformat()
    conn = _conn()
    try:
        try:
            conn.execute(
                f"INSERT INTO {TAGS_TABLE} (id, business_id, name, color, created_at) "
                f"VALUES (?, ?, ?, ?, ?)",
                (tag_id, business_id, name, color, now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Name already exists — return the existing tag instead of failing,
            # so callers using "create or reuse" semantics don't need to catch.
            row = conn.execute(
                f"SELECT id, name, color, created_at FROM {TAGS_TABLE} "
                f"WHERE business_id = ? AND name = ? COLLATE NOCASE",
                (business_id, name),
            ).fetchone()
            if row:
                return {
                    "id": row[0], "name": row[1], "color": row[2],
                    "created_at": row[3], "usage_count": 0,
                }
            raise
    finally:
        conn.close()
    return {
        "id": tag_id, "name": name, "color": color,
        "created_at": now, "usage_count": 0,
    }


def delete_tag(business_id: str, tag_id: str) -> None:
    """Delete a tag and all its assignments (cascade)."""
    conn = _conn()
    try:
        # Delete assignments only for tags that belong to this business.
        conn.execute(
            f"DELETE FROM {ASSIGN_TABLE} WHERE tag_id IN "
            f"(SELECT id FROM {TAGS_TABLE} WHERE id = ? AND business_id = ?)",
            (tag_id, business_id),
        )
        conn.execute(
            f"DELETE FROM {TAGS_TABLE} WHERE id = ? AND business_id = ?",
            (tag_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()


# ── Assignment API ──────────────────────────────────────────────────────────
def assign(business_id: str, tag_id: str, entity_type: str, entity_id: str) -> None:
    entity_type = _validate_entity_type(entity_type)
    conn = _conn()
    try:
        # Reject if tag isn't in this business (prevents cross-tenant leakage).
        row = conn.execute(
            f"SELECT 1 FROM {TAGS_TABLE} WHERE id = ? AND business_id = ?",
            (tag_id, business_id),
        ).fetchone()
        if not row:
            raise ValueError("Tag not found for this business")
        conn.execute(
            f"INSERT OR IGNORE INTO {ASSIGN_TABLE} "
            f"(tag_id, entity_type, entity_id, created_at) VALUES (?, ?, ?, ?)",
            (tag_id, entity_type, entity_id, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def unassign(business_id: str, tag_id: str, entity_type: str, entity_id: str) -> None:
    entity_type = _validate_entity_type(entity_type)
    conn = _conn()
    try:
        conn.execute(
            f"DELETE FROM {ASSIGN_TABLE} "
            f"WHERE tag_id = ? AND entity_type = ? AND entity_id = ? "
            f"AND tag_id IN (SELECT id FROM {TAGS_TABLE} WHERE business_id = ?)",
            (tag_id, entity_type, entity_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()


def set_tags(business_id: str, entity_type: str, entity_id: str, tag_ids: List[str]) -> List[Dict]:
    """Replace the entity's tag set with exactly `tag_ids`. Returns the new set."""
    entity_type = _validate_entity_type(entity_type)
    conn = _conn()
    try:
        # Scope tag_ids to this business, quietly dropping anything foreign.
        if tag_ids:
            placeholders = ",".join("?" for _ in tag_ids)
            rows = conn.execute(
                f"SELECT id FROM {TAGS_TABLE} "
                f"WHERE business_id = ? AND id IN ({placeholders})",
                [business_id, *tag_ids],
            ).fetchall()
            valid_ids = [r[0] for r in rows]
        else:
            valid_ids = []
        conn.execute(
            f"DELETE FROM {ASSIGN_TABLE} "
            f"WHERE entity_type = ? AND entity_id = ? "
            f"AND tag_id IN (SELECT id FROM {TAGS_TABLE} WHERE business_id = ?)",
            (entity_type, entity_id, business_id),
        )
        now = datetime.utcnow().isoformat()
        for tid in valid_ids:
            conn.execute(
                f"INSERT OR IGNORE INTO {ASSIGN_TABLE} "
                f"(tag_id, entity_type, entity_id, created_at) VALUES (?, ?, ?, ?)",
                (tid, entity_type, entity_id, now),
            )
        conn.commit()
    finally:
        conn.close()
    return tags_for(business_id, entity_type, entity_id)


def tags_for(business_id: str, entity_type: str, entity_id: str) -> List[Dict]:
    entity_type = _validate_entity_type(entity_type)
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT t.id, t.name, t.color
              FROM {TAGS_TABLE} t
              JOIN {ASSIGN_TABLE} a ON a.tag_id = t.id
             WHERE t.business_id = ?
               AND a.entity_type = ?
               AND a.entity_id = ?
             ORDER BY t.name COLLATE NOCASE
            """,
            (business_id, entity_type, entity_id),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def entities_with_tag(business_id: str, tag_id: str, entity_type: str) -> List[str]:
    """Return entity IDs of `entity_type` tagged with `tag_id`."""
    entity_type = _validate_entity_type(entity_type)
    conn = _conn()
    try:
        rows = conn.execute(
            f"""
            SELECT a.entity_id FROM {ASSIGN_TABLE} a
              JOIN {TAGS_TABLE} t ON t.id = a.tag_id
             WHERE t.business_id = ?
               AND a.entity_type = ?
               AND a.tag_id = ?
            """,
            (business_id, entity_type, tag_id),
        ).fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def bulk_tags_for(business_id: str, entity_type: str, entity_ids: List[str]) -> Dict[str, List[Dict]]:
    """Fetch tags for many entities at once — used by list pages."""
    entity_type = _validate_entity_type(entity_type)
    if not entity_ids:
        return {}
    placeholders = ",".join("?" for _ in entity_ids)
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"""
            SELECT a.entity_id, t.id AS tag_id, t.name, t.color
              FROM {ASSIGN_TABLE} a
              JOIN {TAGS_TABLE} t ON t.id = a.tag_id
             WHERE t.business_id = ?
               AND a.entity_type = ?
               AND a.entity_id IN ({placeholders})
             ORDER BY t.name COLLATE NOCASE
            """,
            [business_id, entity_type, *entity_ids],
        ).fetchall()
    finally:
        conn.close()
    out: Dict[str, List[Dict]] = {eid: [] for eid in entity_ids}
    for r in rows:
        out.setdefault(r["entity_id"], []).append({
            "id": r["tag_id"], "name": r["name"], "color": r["color"],
        })
    return out
