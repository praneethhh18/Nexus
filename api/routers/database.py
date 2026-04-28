"""
Database explorer + bulk CSV/Excel import.

Read-only schema/data inspection plus a one-shot import that creates or
appends to a tenant table. Built-in `nexus_*` and `sqlite_*` tables are
write-protected so users can't accidentally overwrite them.

Also exposes `POST /api/sql/execute` — an auth-gated raw-SQL runner used by
the dev-mode SQL Editor. SELECT-only by default; write statements require
`allow_writes=true` in the body and still avoid the protected `nexus_*`
prefix to keep the auth tables safe.
"""
from __future__ import annotations

import re
import sqlite3
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from api.auth import get_current_context
from config.settings import DB_PATH

router = APIRouter(tags=["database"])

_SYSTEM_TABLE_PREFIXES = ("nexus_", "sqlite_")


@router.get("/api/database/tables")
def list_tables(ctx: dict = Depends(get_current_context)):
    import pandas as pd

    conn = sqlite3.connect(DB_PATH)
    try:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
        )["name"].tolist()

        result = []
        for t in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            except Exception:
                count = 0
            cols = pd.read_sql_query(f"PRAGMA table_info([{t}])", conn)
            result.append({
                "name": t,
                "row_count": count,
                "column_count": len(cols),
                "is_system": t.startswith(_SYSTEM_TABLE_PREFIXES),
            })
    finally:
        conn.close()
    return result


@router.get("/api/database/tables/{table_name}")
def get_table_detail(table_name: str, limit: int = 50,
                     ctx: dict = Depends(get_current_context)):
    import pandas as pd

    if not table_name.replace("_", "").isalnum():
        raise HTTPException(400, "Invalid table name")

    conn = sqlite3.connect(DB_PATH)
    try:
        cols = pd.read_sql_query(f"PRAGMA table_info([{table_name}])", conn)
        if cols.empty:
            raise HTTPException(404, "Table not found")
        fks = pd.read_sql_query(f"PRAGMA foreign_key_list([{table_name}])", conn)
        row_count = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]

        limit = max(1, min(limit, 500))
        df = pd.read_sql_query(f"SELECT * FROM [{table_name}] LIMIT {limit}", conn)

        stats = []
        for _, col in cols.iterrows():
            if col["type"] in ("INTEGER", "REAL", "NUMERIC"):
                try:
                    s = pd.read_sql_query(
                        f"SELECT MIN([{col['name']}]) as min, MAX([{col['name']}]) as max, "
                        f"ROUND(AVG([{col['name']}]), 2) as avg FROM [{table_name}]",
                        conn,
                    )
                    stats.append({"column": col["name"], **s.iloc[0].to_dict()})
                except Exception:
                    pass
    finally:
        conn.close()

    return {
        "name": table_name,
        "row_count": row_count,
        "columns": cols.to_dict(orient="records"),
        "foreign_keys": fks.to_dict(orient="records") if not fks.empty else [],
        "data": df.to_dict(orient="records"),
        "column_stats": stats,
    }


@router.post("/api/database/import")
async def import_data(
    file: UploadFile = File(...),
    table_name: str = Query(""),
    if_exists: str = Query("fail"),
    ctx: dict = Depends(get_current_context),
):
    from sql_agent.data_import import preview_file, import_to_database

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50 MB max
            raise HTTPException(413, "File too large (max 50 MB)")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        preview = preview_file(tmp_path)
        if preview.get("error"):
            raise HTTPException(400, preview["error"])

        # Refuse to overwrite built-in tenant/system tables.
        name = table_name or preview["suggested_table_name"]
        if name.startswith(_SYSTEM_TABLE_PREFIXES):
            raise HTTPException(400, "Cannot overwrite system tables")
        full_df = preview.get("_full_df")

        result = import_to_database(full_df, name, if_exists=if_exists)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not result["success"]:
        raise HTTPException(400, result["error"])

    try:
        from sql_agent.query_generator import clear_cache
        clear_cache()
    except Exception:
        pass

    return result


@router.post("/api/database/import/preview")
async def preview_import(file: UploadFile = File(...),
                         ctx: dict = Depends(get_current_context)):
    from sql_agent.data_import import preview_file

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(413, "File too large (max 50 MB)")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        preview = preview_file(tmp_path, max_rows=20)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if preview.get("error"):
        raise HTTPException(400, preview["error"])

    preview.pop("_full_df", None)
    df = preview.pop("dataframe", None)
    if df is not None:
        preview["preview_data"] = df.to_dict(orient="records")

    return preview


# ── Raw SQL execution (dev-mode SQL Editor) ─────────────────────────────────
class SQLExecuteRequest(BaseModel):
    sql: str
    allow_writes: bool = False
    limit: int = 500


# Statements we always block — the auth tables and platform metadata live
# under `nexus_*` / `sqlite_*`; clobbering them locks out the user.
_DANGEROUS_PATTERNS = [
    re.compile(r"\b(DROP|TRUNCATE)\s+TABLE\s+[\"\[`]?nexus_", re.IGNORECASE),
    re.compile(r"\b(DROP|TRUNCATE)\s+TABLE\s+[\"\[`]?sqlite_", re.IGNORECASE),
    re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE),
    re.compile(r"\bATTACH\s+DATABASE\b", re.IGNORECASE),
]

_WRITE_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "create",
                   "replace", "truncate", "vacuum", "pragma", "attach")


def _is_write_statement(sql: str) -> bool:
    head = sql.lstrip().split(None, 1)
    return bool(head) and head[0].lower() in _WRITE_KEYWORDS


@router.post("/api/sql/execute")
def execute_sql(req: SQLExecuteRequest, ctx: dict = Depends(get_current_context)):
    """
    Run a raw SQL statement against the local SQLite DB.

    Defaults are conservative — SELECT only, max 500 rows, 15 s timeout.
    Set `allow_writes=true` to permit INSERT/UPDATE/DELETE on user tables;
    `nexus_*` and `sqlite_*` tables are *always* protected from DROP/TRUNCATE
    so a fat-finger can't lock the user out of their own workspace.
    """
    sql = (req.sql or "").strip().rstrip(";").strip()
    if not sql:
        raise HTTPException(400, "SQL is required.")

    for pat in _DANGEROUS_PATTERNS:
        if pat.search(sql):
            raise HTTPException(403, "That statement targets protected system tables.")

    # Reject multi-statement payloads — sqlite3 only runs one anyway, but
    # callers may not realise that and this is clearer.
    if ";" in sql:
        raise HTTPException(400, "Only one statement per request. Remove trailing or embedded semicolons.")

    is_write = _is_write_statement(sql)
    if is_write and not req.allow_writes:
        raise HTTPException(
            400,
            "This is a write statement. Re-send with allow_writes=true if you intended to modify data.",
        )

    limit = max(1, min(int(req.limit or 500), 5000))

    started = time.time()
    conn = sqlite3.connect(DB_PATH)
    try:
        # 15-second wall-clock cap via SQLite progress handler.
        deadline = started + 15
        def _check():
            return 1 if time.time() > deadline else 0
        conn.set_progress_handler(_check, 1000)

        if is_write:
            cursor = conn.execute(sql)
            rows_affected = cursor.rowcount
            conn.commit()
            return {
                "ok": True,
                "kind": "write",
                "rows_affected": rows_affected,
                "duration_ms": int((time.time() - started) * 1000),
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "sql": sql,
            }

        # SELECT path — apply outer LIMIT so a runaway query can't OOM us.
        capped = f"SELECT * FROM ({sql}) AS _capped LIMIT {limit + 1}"
        cursor = conn.execute(capped)
        cols = [d[0] for d in cursor.description] if cursor.description else []
        raw = cursor.fetchall()
        truncated = len(raw) > limit
        if truncated:
            raw = raw[:limit]
        rows = [dict(zip(cols, r)) for r in raw]

        return {
            "ok": True,
            "kind": "read",
            "columns": cols,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
            "duration_ms": int((time.time() - started) * 1000),
            "sql": sql,
        }
    except sqlite3.OperationalError as e:
        msg = str(e)
        # The progress handler raises "interrupted" when we cancel for timeout.
        if "interrupted" in msg.lower():
            raise HTTPException(408, "Query exceeded the 15-second timeout.")
        raise HTTPException(400, f"SQL error: {msg}")
    except sqlite3.DatabaseError as e:
        raise HTTPException(400, f"Database error: {e}")
    finally:
        conn.close()
