"""
Database connection abstraction — supports both SQLite (default) and Postgres.

Every module in NexusAgent calls `sqlite3.connect(DB_PATH)` directly today.
That's fine. When/if you want to move to Postgres, switch to this module's
`get_conn()` instead — it returns a connection object with the same shape
(`.execute()`, `.commit()`, `.close()`, `.row_factory`), and translates the
`?` placeholder style to the Postgres `%s` style under the hood.

Configure via env:
    DATABASE_URL=postgresql://user:pass@host:5432/dbname   # use Postgres
    DATABASE_URL=sqlite:///data/nexusagent.db             # explicit SQLite (default)

If DATABASE_URL is unset, falls back to config.settings.DB_PATH (SQLite).

NOTE: This module exists as a migration PATH. The rest of the codebase still
uses sqlite3 directly for speed and simplicity. When you're ready to move to
Postgres, replace `sqlite3.connect(DB_PATH)` with `from config.db import get_conn`
module-by-module, then run `tools/migrate_to_postgres.py`.
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any


# DB_PATH and DATABASE_URL are resolved on EACH call rather than at import
# time. Reason: tests use monkeypatch.setenv("DB_PATH", ...) + importlib.reload
# on `config.settings`. If we cached values here at import, those reloads
# wouldn't propagate and tests would silently hit the wrong database.

def _database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def _db_path() -> str:
    # Read fresh from config.settings so settings reloads in tests are seen.
    from config import settings as _settings
    return _settings.DB_PATH


def backend() -> str:
    """Return 'postgres' if DATABASE_URL points at Postgres, else 'sqlite'."""
    if _database_url().startswith(("postgresql://", "postgres://")):
        return "postgres"
    return "sqlite"


def is_postgres() -> bool:
    return backend() == "postgres"


# ── SQLite path (default) ────────────────────────────────────────────────────
def _sqlite_conn() -> sqlite3.Connection:
    db_path = _db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    # Apply WAL + production pragmas per-connection for safety
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 10000")
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception:
        pass
    return conn


# ── Postgres path (opt-in via DATABASE_URL) ──────────────────────────────────
class _PgRow:
    """
    Drop-in replacement for `sqlite3.Row`. Behaves like a tuple AND lets
    callers index by column name: `row['email']` or `row[2]`. NexusAgent's
    SQLite code reads results both ways, so the Postgres path needs the same
    duality to be a true drop-in.
    """
    __slots__ = ("_values", "_columns")

    def __init__(self, values, columns):
        self._values = tuple(values)
        self._columns = tuple(columns)

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                idx = self._columns.index(key)
            except ValueError:
                raise IndexError(f"No such column: {key!r}")
            return self._values[idx]
        return self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return f"_PgRow({dict(zip(self._columns, self._values))!r})"

    def keys(self):
        return list(self._columns)


class _PgCursor:
    """Wraps a psycopg cursor to accept ?-style placeholders and emit
    sqlite3.Row-style rows when the parent connection has row_factory set."""
    __slots__ = ("_c", "_row_factory")

    def __init__(self, c, row_factory=None):
        self._c = c
        self._row_factory = row_factory

    def execute(self, sql: str, params: Any = ()):
        sql = _translate_sql(sql)
        self._c.execute(sql, params)
        return self

    def _wrap(self, row):
        if row is None:
            return None
        if self._row_factory is None:
            return row
        # row_factory is set — emit dict-indexable rows. Column names from
        # the cursor description survive across both psycopg and sqlite.
        cols = [d[0] for d in (self._c.description or [])]
        return _PgRow(row, cols)

    def fetchone(self):
        return self._wrap(self._c.fetchone())

    def fetchall(self):
        if self._row_factory is None:
            return list(self._c.fetchall())
        cols = [d[0] for d in (self._c.description or [])]
        return [_PgRow(r, cols) for r in self._c.fetchall()]

    def __iter__(self):
        for r in self._c:
            yield self._wrap(r)

    @property
    def description(self):
        return self._c.description

    def close(self):
        """psycopg cursors expose close(); pandas.read_sql_query and other
        DB-API-2 consumers call this when they're done iterating. The wrapper
        was missing it — proactive_monitor.check_anomalies was erroring once
        an hour with '_PgCursor object has no attribute close'."""
        try:
            self._c.close()
        except Exception:
            pass

    @property
    def rowcount(self):
        return self._c.rowcount

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        self.close()

    @property
    def rowcount(self):
        return self._c.rowcount

    @property
    def lastrowid(self):
        # psycopg doesn't expose lastrowid for non-sequential inserts.
        # For NexusAgent the only place lastrowid is used is autoincrement
        # tables that should use RETURNING id on Postgres. Callers that
        # rely on lastrowid must be updated when migrating.
        return None


class _PgConn:
    """Wraps psycopg connection to mimic the sqlite3.Connection API.

    Pool-aware: if `_pool` is set, close() returns the underlying connection
    to the pool instead of actually closing it. Without pooling every request
    paid the Postgres TCP+SSL+auth handshake cost (~100-200ms per query) —
    callers commonly run 4-5 queries per request, so this matters a lot.
    """
    __slots__ = ("_c", "_pool", "row_factory")

    def __init__(self, c, pool=None):
        self._c = c
        self._pool = pool
        # Set to truthy (e.g. sqlite3.Row) to get dict-indexable rows.
        # We don't compare against the literal sqlite3.Row class so callers
        # don't need to import sqlite3 in a Postgres-only deployment.
        self.row_factory = None

    def execute(self, sql: str, params: Any = ()):
        cur = self._c.cursor()
        translated = _translate_sql(sql)
        try:
            cur.execute(translated, params)
        except Exception as e:
            # CREATE INDEX IF NOT EXISTS deadlocks against itself across
            # processes — 20+ call sites in this codebase race-create
            # indexes from per-request _get_conn() helpers, and an
            # uvicorn reload kicks all of them off at once. When this
            # happens, just swallow it: the index will exist by the
            # time we need it (a competing process is finishing the
            # same statement right now).
            stripped = translated.strip().upper()
            is_index_create = (
                stripped.startswith("CREATE INDEX")
                or stripped.startswith("CREATE UNIQUE INDEX")
            )
            cls = type(e).__name__
            if is_index_create and cls in ("DeadlockDetected", "LockNotAvailable", "QueryCanceled"):
                # Best-effort rollback so the transaction doesn't poison
                # subsequent statements.
                try: self._c.rollback()
                except Exception: pass
                return _PgCursor(cur, row_factory=self.row_factory)
            raise
        return _PgCursor(cur, row_factory=self.row_factory)

    def cursor(self):
        return _PgCursor(self._c.cursor(), row_factory=self.row_factory)

    def commit(self):
        self._c.commit()

    def rollback(self):
        self._c.rollback()

    def close(self):
        if self._pool is not None:
            # Discard any pending transaction state before returning to pool —
            # otherwise the next checkout would inherit our half-finished tx.
            try:
                self._c.rollback()
            except Exception:
                pass
            try:
                self._pool.putconn(self._c)
            except Exception:
                # Pool rejected (broken connection) — fall back to a real close
                # so we don't leak the fd.
                try: self._c.close()
                except Exception: pass
            self._pool = None  # idempotent close
        else:
            self._c.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        if a[0] is None:
            self.commit()
        else:
            self.rollback()
        self.close()


_PARAM_RE = re.compile(r"\?")
_OR_IGNORE_RE = re.compile(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", re.IGNORECASE)


def _translate_sql(sql: str) -> str:
    """
    Convert SQLite-flavored SQL to something Postgres can execute.

    Handles the common cases across NexusAgent's codebase:
      ?  → %s                (parameter style)
      INTEGER PRIMARY KEY AUTOINCREMENT → BIGSERIAL PRIMARY KEY
      datetime('now')  → NOW()
      LOWER(col) LIKE ? → LOWER(col) LIKE %s   (handled by ? → %s)
      INSERT OR IGNORE INTO → INSERT INTO ... ON CONFLICT DO NOTHING
      INSERT OR REPLACE INTO → NOT handled — callers must rewrite explicitly
      PRAGMA ...        → silently ignored (→ SELECT 1)
    """
    out = sql

    # Silently drop SQLite PRAGMAs — harmless on Postgres
    if out.strip().upper().startswith("PRAGMA"):
        return "SELECT 1"  # Postgres-safe no-op

    # ── COLLATE NOCASE — SQLite-only, translate to Postgres equivalents ──
    # Inside UNIQUE(...) constraints, Postgres can't accept function calls
    # inline, so just strip the modifier (case-insensitive uniqueness is
    # lost; the app layer already validates).
    out = re.sub(
        r"(UNIQUE\s*\([^)]*?)\s+COLLATE\s+NOCASE",
        r"\1",
        out,
        flags=re.IGNORECASE,
    )
    # `col = ? COLLATE NOCASE` → `LOWER(col) = LOWER(?)`  (WHERE clauses)
    out = re.sub(
        r"(\b\w+(?:\.\w+)?)\s*=\s*\?\s+COLLATE\s+NOCASE\b",
        r"LOWER(\1) = LOWER(?)",
        out,
        flags=re.IGNORECASE,
    )
    # Remaining `col COLLATE NOCASE` → `LOWER(col)`  (ORDER BY clauses, etc.)
    out = re.sub(
        r"(\b\w+(?:\.\w+)?)\s+COLLATE\s+NOCASE\b",
        r"LOWER(\1)",
        out,
        flags=re.IGNORECASE,
    )

    # AUTOINCREMENT isn't valid on Postgres
    out = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "BIGSERIAL PRIMARY KEY", out, flags=re.IGNORECASE)

    # datetime('now') → NOW()
    out = re.sub(r"datetime\(\s*'now'\s*\)", "NOW()", out, flags=re.IGNORECASE)

    # INSERT OR IGNORE → INSERT ... ON CONFLICT DO NOTHING
    if _OR_IGNORE_RE.search(out):
        out = _OR_IGNORE_RE.sub("INSERT INTO", out)
        out = out.rstrip() + " ON CONFLICT DO NOTHING"

    # Placeholder style
    out = _PARAM_RE.sub("%s", out)

    return out


# ── Connection pool (Postgres only) ──────────────────────────────────────
# Lazily initialised on first request. Reuses connections across requests
# instead of paying the ~150ms TCP+SSL+auth handshake on every query.
#
# Sizing: min_size keeps a small warm pool ready for the next request;
# max_size caps concurrent DB connections so a traffic spike doesn't blow
# past the Postgres server's connection limit (managed Postgres tiers
# usually allow 25-100). Tunable via POSTGRES_POOL_MIN/MAX env vars.
#
# Set POSTGRES_POOL_DISABLED=1 to fall back to per-call psycopg.connect()
# behaviour (useful for debugging or constrained envs).
_PG_POOL = None
_PG_POOL_LOCK = None  # threading.Lock — imported lazily to avoid top-level cost


def _pool_enabled() -> bool:
    """Pool is OPT-IN via POSTGRES_POOL_ENABLED=1.
    Defaulted off because under uvicorn --reload the worker process spawns
    children that fight for the same pool — symptoms include the backend
    hanging on first request after a hot-reload. In a stable prod deploy
    (gunicorn, single uvicorn worker, no --reload) it's safe to enable.
    """
    raw = (os.getenv("POSTGRES_POOL_ENABLED") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _get_pg_pool():
    """Lazy-init the Postgres connection pool. Returns None if pooling
    is disabled (POSTGRES_POOL_DISABLED=1) or psycopg_pool isn't installed
    — callers fall back to per-call psycopg.connect()."""
    global _PG_POOL, _PG_POOL_LOCK
    if not _pool_enabled():
        return None
    if _PG_POOL is not None:
        return _PG_POOL
    # Double-checked locking — avoid creating two pools under a race.
    if _PG_POOL_LOCK is None:
        import threading
        _PG_POOL_LOCK = threading.Lock()
    with _PG_POOL_LOCK:
        if _PG_POOL is not None:
            return _PG_POOL
        try:
            from psycopg_pool import ConnectionPool
        except ImportError:
            # Pool package not installed — gracefully fall back to one-shot
            # connects so the app still boots. Log so the operator knows.
            try:
                from loguru import logger
                logger.warning(
                    "[db] psycopg_pool not installed — falling back to "
                    "per-request connects (slower). Install with: "
                    "pip install 'psycopg_pool>=3.2'"
                )
            except Exception:
                pass
            return None
        min_size = int(os.getenv("POSTGRES_POOL_MIN", "2"))
        max_size = int(os.getenv("POSTGRES_POOL_MAX", "10"))
        _PG_POOL = ConnectionPool(
            conninfo=_database_url(),
            min_size=min_size,
            max_size=max_size,
            kwargs={"autocommit": False},
            # Lazy open: don't block startup waiting for min_size conns to
            # come up. Initial connect cost is paid by the first request,
            # not by `import config.db`. Stops a flaky DB from breaking
            # backend boot, and avoids racing with an already-running
            # uvicorn worker that holds the same conn-limit budget.
            open=False,
            max_lifetime=60 * 30,    # 30 min — recycle long-lived conns
            max_idle=60 * 5,         # 5 min idle → close
            timeout=10.0,            # getconn() blocks up to 10s
            name="nexusagent",
        )
        _PG_POOL.open(wait=False)    # fill min_size in background
        return _PG_POOL


def close_pg_pool() -> None:
    """Shutdown hook — called from FastAPI's lifespan on app stop so we
    don't leak connections on hot reload / graceful shutdown."""
    global _PG_POOL
    if _PG_POOL is not None:
        try:
            _PG_POOL.close()
        except Exception:
            pass
        _PG_POOL = None


def _pg_conn() -> _PgConn:
    try:
        import psycopg
    except ImportError:
        raise RuntimeError(
            "DATABASE_URL points at Postgres but 'psycopg' is not installed. "
            "Run: pip install 'psycopg[binary]>=3.1'"
        )
    pool = _get_pg_pool()
    if pool is not None:
        raw = pool.getconn()
        return _PgConn(raw, pool=pool)
    raw = psycopg.connect(_database_url(), autocommit=False)
    return _PgConn(raw)


# ── Public entry point ───────────────────────────────────────────────────────
def get_conn():
    """Return a connection. Same API shape for SQLite and Postgres callers."""
    if is_postgres():
        return _pg_conn()
    return _sqlite_conn()


def table_exists(conn, table: str) -> bool:
    """
    True if `table` exists in the active database. Backend-aware. Replaces
    the SQLite-only `SELECT 1 FROM sqlite_master WHERE type='table' AND name=?`
    pattern, which fails on Postgres (no sqlite_master table).
    """
    if is_postgres():
        cur = conn.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = ?",
            (table,),
        )
    else:
        cur = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        )
    return cur.fetchone() is not None


def list_tables(conn) -> list[str]:
    """Return all table names (public schema on Postgres). Backend-aware."""
    if is_postgres():
        cur = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
    else:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    return [r[0] for r in cur.fetchall()]


def list_columns(conn, table: str) -> list[str]:
    """
    Return column names of a table, backend-aware. Replaces the SQLite-only
    pattern `[r[1] for r in conn.execute("PRAGMA table_info(t)").fetchall()]`
    which silently breaks on Postgres (the wrapper translates PRAGMA to
    SELECT 1, then `r[1]` IndexErrors).

    Use whenever code needs to introspect "does this column exist".
    """
    if is_postgres():
        cur = conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = ? ORDER BY ordinal_position",
            (table,),
        )
        return [r[0] for r in cur.fetchall()]
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def get_raw_conn():
    """
    Return the UNDERLYING DB-API connection (raw sqlite3.Connection or
    psycopg.Connection), bypassing the `?`/AUTOINCREMENT translation layer.

    Use only when the caller needs strict DB-API 2.0 conformance — e.g.:
      * `pandas.read_sql_query(sql, conn)` — pandas inspects the connection
        type and breaks with our wrapper.
      * `conn.set_progress_handler(...)` — SQLite-only API not on the wrapper.
      * Database-specific introspection (PRAGMAs, system catalogs).

    Caller is responsible for using backend-appropriate SQL on the result.
    """
    if is_postgres():
        try:
            import psycopg
        except ImportError:
            raise RuntimeError(
                "DATABASE_URL points at Postgres but 'psycopg' is not installed."
            )
        return psycopg.connect(_database_url(), autocommit=False)
    db_path = _db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def health_check() -> dict:
    """Quick ping to verify the database is reachable."""
    try:
        conn = get_conn()
        try:
            cur = conn.execute("SELECT 1")
            row = cur.fetchone()
            return {"backend": backend(), "online": bool(row)}
        finally:
            conn.close()
    except Exception as e:
        return {"backend": backend(), "online": False, "error": str(e)[:200]}
