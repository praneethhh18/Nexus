"""
Lightweight migration runner — supports SQLite (default) and Postgres.

How it works:

  1. Migration files live in `db/migrations/` and are named
     `NNNN_description.sql`. The four-digit prefix is the version number;
     it must be monotonically increasing.

  2. A `nexus_migrations` table records which versions have been applied.
     One row per applied migration: `(version, name, applied_at, sha256)`.

  3. On startup (or via `python -m db.migrate`) the runner:
       - ensures `nexus_migrations` exists
       - lists `db/migrations/*.sql` in numeric order
       - applies any not yet recorded, each in its own transaction
       - records the version + SHA-256 of the applied SQL
     If a migration's recorded SHA doesn't match the on-disk file, we WARN
     loudly (someone edited a shipped migration — usually a mistake) but
     don't fail.

  4. Running it twice is a no-op. Tests assert this.

Backend notes:

  - On Postgres (`DATABASE_URL=postgresql://...`) the runner uses
    `config.db.get_conn()` and executes statements one-by-one after
    splitting on `;`. `_translate_sql()` converts AUTOINCREMENT→BIGSERIAL,
    datetime('now')→NOW(), and so on automatically.
  - On SQLite (default) it opens a native `sqlite3.Connection` and uses
    `executescript` for multi-statement files. SQLite-specific env:
    `db_path` arg overrides `DB_PATH` for tests.

Adding a migration:

    1. Touch `db/migrations/0002_add_foo_column.sql`.
    2. Write the SQL. Use multiple statements separated by `;`.
    3. Restart the server (or run `python -m db.migrate`).

Conventions:

  - Migrations should be idempotent (`IF NOT EXISTS`, `IF EXISTS`).
  - Don't edit a migration after it's shipped. Ship a follow-up instead.
  - The 0001 baseline is intentionally a no-op marker — existing workspaces
    already have the schema; new ones get it via `setup_database()` +
    per-module `CREATE IF NOT EXISTS` pattern.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from loguru import logger

from config.settings import DB_PATH

LEDGER_TABLE = "nexus_migrations"
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_FILENAME_RE = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$", re.IGNORECASE)


# ── Ledger ──────────────────────────────────────────────────────────────────
def _ensure_ledger(conn) -> None:
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
            version    INTEGER PRIMARY KEY,
            name       TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            sha256     TEXT NOT NULL
        )
    """)
    conn.commit()


def _applied_versions(conn) -> dict[int, dict]:
    rows = conn.execute(
        f"SELECT version, name, applied_at, sha256 FROM {LEDGER_TABLE}"
    ).fetchall()
    return {
        int(r[0]): {"version": int(r[0]), "name": r[1], "applied_at": r[2], "sha256": r[3]}
        for r in rows
    }


# ── Migration discovery ─────────────────────────────────────────────────────
def _discover() -> List[Tuple[int, str, Path]]:
    """Return sorted (version, name, path) for every well-named migration file."""
    if not _MIGRATIONS_DIR.exists():
        return []
    out: List[Tuple[int, str, Path]] = []
    for p in sorted(_MIGRATIONS_DIR.iterdir()):
        if not p.is_file() or not p.name.endswith(".sql"):
            continue
        m = _FILENAME_RE.match(p.name)
        if not m:
            logger.warning(f"[Migrate] ignoring oddly-named file: {p.name}")
            continue
        version = int(m.group(1))
        name = m.group(2)
        out.append((version, name, p))
    out.sort(key=lambda t: t[0])

    seen = set()
    for v, n, p in out:
        if v in seen:
            raise RuntimeError(
                f"[Migrate] duplicate migration version {v}: see {p.name}. "
                "Each NNNN_ prefix must be unique."
            )
        seen.add(v)
    return out


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_statements(sql: str) -> list[str]:
    """Split a SQL script into individual statements by semicolons."""
    parts = re.split(r";", sql)
    return [p.strip() for p in parts if p.strip()]


# ── Apply ───────────────────────────────────────────────────────────────────
def _apply_one_sqlite(conn: sqlite3.Connection, version: int, name: str, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        logger.info(f"[Migrate] {path.name} is empty — recording as no-op")
    else:
        try:
            conn.executescript(sql)
        except Exception:
            logger.error(f"[Migrate] {path.name} failed; ledger NOT updated — fix the SQL and retry")
            raise

    conn.execute(
        f"INSERT INTO {LEDGER_TABLE} (version, name, applied_at, sha256) "
        f"VALUES (?, ?, ?, ?)",
        (version, name, datetime.now(timezone.utc).isoformat(), _sha256(sql)),
    )
    conn.commit()
    logger.info(f"[Migrate] applied {version:04d}_{name}")


def _apply_one_pg(conn, version: int, name: str, path: Path) -> None:
    """Apply a migration on Postgres — split by semicolons, run one by one."""
    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        logger.info(f"[Migrate] {path.name} is empty — recording as no-op")
    else:
        stmts = _split_statements(sql)
        try:
            for stmt in stmts:
                conn.execute(stmt)  # _translate_sql applied inside _PgConn.execute
        except Exception:
            conn.rollback()
            logger.error(f"[Migrate] {path.name} failed; ledger NOT updated — fix the SQL and retry")
            raise

    conn.execute(
        f"INSERT INTO {LEDGER_TABLE} (version, name, applied_at, sha256) "
        f"VALUES (?, ?, ?, ?)",
        (version, name, datetime.now(timezone.utc).isoformat(), _sha256(sql)),
    )
    conn.commit()
    logger.info(f"[Migrate] applied {version:04d}_{name}")


def _apply_one(conn, version: int, name: str, path: Path, *, is_pg: bool) -> None:
    if is_pg:
        _apply_one_pg(conn, version, name, path)
    else:
        _apply_one_sqlite(conn, version, name, path)


def apply_pending(db_path: str | None = None) -> List[dict]:
    """
    Apply every unapplied migration in order. Returns the list of newly
    applied migrations. Idempotent — safe to call on every boot.
    """
    from config.db import get_conn, is_postgres

    pg = is_postgres()
    if pg:
        conn = get_conn()
    else:
        target = db_path or DB_PATH
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(target)

    try:
        _ensure_ledger(conn)
        applied = _applied_versions(conn)
        discovered = _discover()
        if not discovered:
            return []

        new_runs: List[dict] = []
        for version, name, path in discovered:
            if version in applied:
                stored_sha = applied[version]["sha256"]
                file_sha = _sha256(path.read_text(encoding="utf-8"))
                if stored_sha != file_sha:
                    logger.warning(
                        f"[Migrate] {path.name} content has changed since it was "
                        f"applied (stored sha={stored_sha[:10]}…, file={file_sha[:10]}…). "
                        "Don't edit shipped migrations — add a follow-up instead."
                    )
                continue
            _apply_one(conn, version, name, path, is_pg=pg)
            new_runs.append({
                "version": version, "name": name,
                "path": path.name,
            })
        return new_runs
    finally:
        conn.close()


def status(db_path: str | None = None) -> dict:
    """Inspection helper — returns applied + pending migrations."""
    from config.db import get_conn, is_postgres

    pg = is_postgres()
    if pg:
        conn = get_conn()
    else:
        target = db_path or DB_PATH
        if not Path(target).exists():
            return {"applied": [], "pending": [t[0] for t in _discover()]}
        conn = sqlite3.connect(target)

    try:
        _ensure_ledger(conn)
        applied = _applied_versions(conn)
        discovered = _discover()
        return {
            "applied": sorted(applied.values(), key=lambda r: r["version"]),
            "pending": [
                {"version": v, "name": n, "path": p.name}
                for (v, n, p) in discovered if v not in applied
            ],
        }
    finally:
        conn.close()


# ── CLI: python -m db.migrate ───────────────────────────────────────────────
def _main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Apply pending NexusAgent migrations.")
    parser.add_argument("--status", action="store_true",
                        help="Show applied + pending migrations and exit.")
    parser.add_argument("--db", default=None, help="Override DB path (SQLite only; ignored on Postgres).")
    args = parser.parse_args()

    if args.status:
        s = status(args.db)
        print(f"Applied: {len(s['applied'])}")
        for r in s["applied"]:
            print(f"  ✓ {r['version']:04d}  {r['name']:<40s}  {r['applied_at']}")
        print(f"Pending: {len(s['pending'])}")
        for r in s["pending"]:
            print(f"  · {r['version']:04d}  {r['name']:<40s}  {r['path']}")
        return 0

    runs = apply_pending(args.db)
    if not runs:
        print("Nothing to apply.")
        return 0
    print(f"Applied {len(runs)} migration(s):")
    for r in runs:
        print(f"  ✓ {r['version']:04d}_{r['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
