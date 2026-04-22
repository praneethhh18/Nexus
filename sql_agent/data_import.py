"""Data Import — import CSV/Excel files as new database tables."""
from __future__ import annotations
import re, sqlite3
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from loguru import logger
from config.settings import DB_PATH

def _sanitize_table_name(name):
    name = Path(name).stem
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"^[0-9]+", "", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name or "imported_data"

def _sanitize_column_name(name):
    name = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    name = re.sub(r"^[0-9]+", "", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name or "column"

def preview_file(file_path, max_rows=10):
    path = Path(file_path); ext = path.suffix.lower()
    try:
        if ext == ".csv": df = pd.read_csv(file_path); file_type = "CSV"
        elif ext in (".xlsx", ".xls"): df = pd.read_excel(file_path); file_type = "Excel"
        else: return {"error": f"Unsupported file type: {ext}"}
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}
    clean_cols = {}
    for col in df.columns:
        clean = _sanitize_column_name(str(col))
        if clean in clean_cols.values():
            i = 2
            while f"{clean}_{i}" in clean_cols.values(): i += 1
            clean = f"{clean}_{i}"
        clean_cols[col] = clean
    df.rename(columns=clean_cols, inplace=True)
    columns = [{"name": c, "dtype": "INTEGER" if pd.api.types.is_integer_dtype(df[c]) else "REAL" if pd.api.types.is_float_dtype(df[c]) else "TEXT",
                "sample_values": [str(v) for v in df[c].dropna().head(3).tolist()], "null_count": int(df[c].isna().sum())} for c in df.columns]
    return {"dataframe": df.head(max_rows), "total_rows": len(df), "total_columns": len(df.columns),
            "columns": columns, "suggested_table_name": _sanitize_table_name(path.name), "file_type": file_type, "_full_df": df}

def get_existing_tables():
    conn = sqlite3.connect(DB_PATH)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
    conn.close(); return tables

def import_to_database(df, table_name, if_exists="fail"):
    table_name = _sanitize_table_name(table_name)
    protected = {"customers","products","orders","order_items","sales_metrics","employees","budgets","transactions",
                 "nexus_audit_log","nexus_conversations","nexus_conversation_messages","nexus_query_history",
                 "nexus_user_memory","nexus_user_profiles","nexus_user_patterns","nexus_user_sessions"}
    if table_name in protected and if_exists == "replace":
        return {"success": False, "error": f"Cannot replace protected table '{table_name}'.", "table_name": table_name, "rows_imported": 0, "columns": []}
    try:
        conn = sqlite3.connect(DB_PATH); df.to_sql(table_name, conn, if_exists=if_exists, index=False); conn.close()
        return {"success": True, "table_name": table_name, "rows_imported": len(df), "columns": list(df.columns), "error": None}
    except ValueError as e:
        return {"success": False, "error": str(e), "table_name": table_name, "rows_imported": 0, "columns": []}
    except Exception as e:
        return {"success": False, "error": str(e), "table_name": table_name, "rows_imported": 0, "columns": []}
