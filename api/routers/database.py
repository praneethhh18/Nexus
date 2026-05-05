"""
Database explorer + bulk CSV/Excel import.

Read-only schema/data inspection plus a one-shot import that creates or
appends to a tenant table. Built-in `nexus_*` tables are write-protected
so users can't accidentally overwrite them.

Also exposes `POST /api/sql/execute` — an auth-gated raw-SQL runner used by
the dev-mode SQL Editor. SELECT-only by default; write statements require
`allow_writes=true` in the body and still avoid the protected `nexus_*`
prefix to keep the auth tables safe.
"""
from __future__ import annotations

import re
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from api.auth import get_current_context
from config.db import get_conn, is_postgres, list_tables as _list_tables, list_columns as _list_columns

router = APIRouter(tags=["database"])

_SYSTEM_TABLE_PREFIXES = ("nexus_", "sqlite_")


def _qi(name: str) -> str:
    """Quote an identifier appropriately for the active backend."""
    if is_postgres():
        return '"' + name.replace('"', '""') + '"'
    return "[" + name + "]"


def _get_column_info(conn, table: str) -> list[dict]:
    """Return column metadata as a list of dicts with normalized keys."""
    if is_postgres():
        cur = conn.execute(
            "SELECT column_name, data_type, is_nullable, column_default, ordinal_position "
            "FROM information_schema.columns WHERE table_name = ? ORDER BY ordinal_position",
            (table,),
        )
        rows = cur.fetchall()
        pk_cur = conn.execute(
            "SELECT kcu.column_name FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = ?",
            (table,),
        )
        pk_cols = {r[0] for r in pk_cur.fetchall()}
        return [
            {
                "cid": i,
                "name": r[0],
                "type": r[1],
                "notnull": int(r[2] == "NO"),
                "dflt_value": r[3],
                "pk": int(r[0] in pk_cols),
            }
            for i, r in enumerate(rows)
        ]
    # SQLite: get_conn() returns a native sqlite3.Connection — PRAGMA works directly
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [
        {"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "dflt_value": r[4], "pk": r[5]}
        for r in rows
    ]


def _get_fk_info(conn, table: str) -> list[dict]:
    """Return FK metadata as a list of dicts. Empty list if not supported."""
    try:
        if is_postgres():
            cur = conn.execute(
                "SELECT kcu.column_name, ccu.table_name, ccu.column_name "
                "FROM information_schema.table_constraints tc "
                "JOIN information_schema.key_column_usage kcu "
                "  ON tc.constraint_name = kcu.constraint_name "
                "JOIN information_schema.constraint_column_usage ccu "
                "  ON ccu.constraint_name = tc.constraint_name "
                "WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = ?",
                (table,),
            )
            rows = cur.fetchall()
            return [{"from": r[0], "table": r[1], "to": r[2]} for r in rows]
        rows = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        return [{"id": r[0], "seq": r[1], "table": r[2], "from": r[3], "to": r[4]} for r in rows]
    except Exception:
        return []


@router.get("/api/database/tables")
def list_tables_endpoint(ctx: dict = Depends(get_current_context)):
    conn = get_conn()
    try:
        tables = _list_tables(conn)
        result = []
        for t in tables:
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {_qi(t)}").fetchone()
                count = int(row[0]) if row else 0
            except Exception:
                count = 0
            col_count = len(_list_columns(conn, t))
            result.append({
                "name": t,
                "row_count": count,
                "column_count": col_count,
                "is_system": t.startswith(_SYSTEM_TABLE_PREFIXES),
            })
    finally:
        conn.close()
    return result


@router.get("/api/database/tables/{table_name}")
def get_table_detail(table_name: str, limit: int = 50,
                     ctx: dict = Depends(get_current_context)):
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
        raise HTTPException(400, "Invalid table name")

    conn = get_conn()
    try:
        cols = _get_column_info(conn, table_name)
        if not cols:
            raise HTTPException(404, "Table not found")
        fks = _get_fk_info(conn, table_name)

        row = conn.execute(f"SELECT COUNT(*) FROM {_qi(table_name)}").fetchone()
        row_count = int(row[0]) if row else 0

        limit = max(1, min(limit, 500))
        cursor = conn.execute(f"SELECT * FROM {_qi(table_name)} LIMIT {limit}")
        col_names = [d[0] for d in (cursor.description or [])]
        raw_rows = cursor.fetchall()
        data = [dict(zip(col_names, r)) for r in raw_rows]

        stats = []
        numeric_types = ("integer", "real", "numeric", "float", "double", "bigint",
                         "smallint", "decimal", "bigserial", "serial")
        for col in cols:
            if any(t in (col["type"] or "").lower() for t in numeric_types):
                try:
                    cn = col["name"]
                    row = conn.execute(
                        f"SELECT MIN({_qi(cn)}), MAX({_qi(cn)}), AVG({_qi(cn)}) "
                        f"FROM {_qi(table_name)}"
                    ).fetchone()
                    if row:
                        stats.append({
                            "column": cn,
                            "min": row[0],
                            "max": row[1],
                            "avg": round(float(row[2] or 0), 2) if row[2] is not None else None,
                        })
                except Exception:
                    pass
    finally:
        conn.close()

    return {
        "name": table_name,
        "row_count": row_count,
        "columns": cols,
        "foreign_keys": fks,
        "data": data,
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
    Run a raw SQL statement against the database.

    Defaults are conservative — SELECT only, max 500 rows, 15 s timeout.
    Set `allow_writes=true` to permit INSERT/UPDATE/DELETE on user tables;
    `nexus_*` tables are always protected from DROP/TRUNCATE.
    """
    sql = (req.sql or "").strip().rstrip(";").strip()
    if not sql:
        raise HTTPException(400, "SQL is required.")

    for pat in _DANGEROUS_PATTERNS:
        if pat.search(sql):
            raise HTTPException(403, "That statement targets protected system tables.")

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
    conn = get_conn()
    try:
        # Timeout: SQLite supports a progress handler; Postgres uses statement_timeout.
        if not is_postgres():
            deadline = started + 15
            def _check():
                return 1 if time.time() > deadline else 0
            conn.set_progress_handler(_check, 1000)
        else:
            conn.execute("SET LOCAL statement_timeout = '15s'")

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

        capped = f"SELECT * FROM ({sql}) AS _capped LIMIT {limit + 1}"
        cursor = conn.execute(capped)
        cols = [d[0] for d in (cursor.description or [])]
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
    except Exception as e:
        msg = str(e)
        if any(k in msg.lower() for k in ("interrupted", "timeout", "statement timeout", "canceling")):
            raise HTTPException(408, "Query exceeded the 15-second timeout.")
        raise HTTPException(400, f"SQL error: {msg}")
    finally:
        conn.close()
