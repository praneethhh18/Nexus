"""
Database explorer + bulk CSV/Excel import.

Read-only schema/data inspection plus a one-shot import that creates or
appends to a tenant table. Built-in `nexus_*` and `sqlite_*` tables are
write-protected so users can't accidentally overwrite them.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

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
