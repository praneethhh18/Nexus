"""
Data Import — import CSV/Excel files as new database tables.
Includes column type detection, preview, and safe table creation.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
from loguru import logger

from config.settings import DB_PATH


def _sanitize_table_name(name: str) -> str:
    """Convert a filename into a safe SQLite table name."""
    # Remove extension
    name = Path(name).stem
    # Replace non-alphanumeric with underscore
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Remove leading digits
    name = re.sub(r"^[0-9]+", "", name)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")
    # Lowercase
    name = name.lower()
    # Ensure not empty
    if not name:
        name = "imported_data"
    return name


def _sanitize_column_name(name: str) -> str:
    """Convert a column header into a safe SQLite column name."""
    name = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    name = re.sub(r"^[0-9]+", "", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    if not name:
        name = "column"
    return name


def _detect_column_types(df: pd.DataFrame) -> Dict[str, str]:
    """Detect SQLite column types from DataFrame dtypes."""
    type_map = {}
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            type_map[col] = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            type_map[col] = "REAL"
        elif pd.api.types.is_bool_dtype(dtype):
            type_map[col] = "INTEGER"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            type_map[col] = "TEXT"
        else:
            type_map[col] = "TEXT"
    return type_map


def preview_file(file_path: str, max_rows: int = 10) -> Dict[str, Any]:
    """
    Read a CSV/Excel file and return a preview with metadata.

    Returns:
        {
            dataframe: pd.DataFrame (first max_rows),
            total_rows: int,
            columns: list[{name, dtype, sample_values}],
            suggested_table_name: str,
            file_type: str,
        }
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
            file_type = "CSV"
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
            file_type = "Excel"
        else:
            return {"error": f"Unsupported file type: {ext}. Use CSV or Excel."}
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    # Sanitize column names
    clean_cols = {}
    for col in df.columns:
        clean = _sanitize_column_name(str(col))
        # Handle duplicates
        if clean in clean_cols.values():
            i = 2
            while f"{clean}_{i}" in clean_cols.values():
                i += 1
            clean = f"{clean}_{i}"
        clean_cols[col] = clean
    df.rename(columns=clean_cols, inplace=True)

    col_types = _detect_column_types(df)
    columns = []
    for col in df.columns:
        sample = df[col].dropna().head(3).tolist()
        columns.append({
            "name": col,
            "dtype": col_types.get(col, "TEXT"),
            "sample_values": [str(v) for v in sample],
            "null_count": int(df[col].isna().sum()),
        })

    return {
        "dataframe": df.head(max_rows),
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": columns,
        "suggested_table_name": _sanitize_table_name(path.name),
        "file_type": file_type,
        "_full_df": df,  # internal, used by import_to_database
    }


def get_existing_tables() -> List[str]:
    """Get list of existing table names in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def import_to_database(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "fail",
) -> Dict[str, Any]:
    """
    Import a DataFrame into SQLite as a new table.

    Args:
        df: The data to import
        table_name: Target table name
        if_exists: 'fail', 'replace', or 'append'

    Returns:
        {success, table_name, rows_imported, columns, error}
    """
    table_name = _sanitize_table_name(table_name)

    # Safety check: don't overwrite core tables
    protected = {
        "customers", "products", "orders", "order_items",
        "sales_metrics", "employees", "budgets", "transactions",
        "nexus_audit_log", "nexus_conversations", "nexus_conversation_messages",
        "nexus_query_history", "nexus_user_memory", "nexus_user_profiles",
        "nexus_user_patterns", "nexus_user_sessions",
    }
    if table_name in protected and if_exists == "replace":
        return {
            "success": False,
            "error": f"Cannot replace protected table '{table_name}'. Choose a different name.",
            "table_name": table_name,
            "rows_imported": 0,
            "columns": [],
        }

    try:
        conn = sqlite3.connect(DB_PATH)
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        conn.close()

        logger.success(
            f"[DataImport] Imported {len(df)} rows into table '{table_name}' "
            f"({len(df.columns)} columns)"
        )

        return {
            "success": True,
            "table_name": table_name,
            "rows_imported": len(df),
            "columns": list(df.columns),
            "error": None,
        }

    except ValueError as e:
        if "already exists" in str(e):
            return {
                "success": False,
                "error": f"Table '{table_name}' already exists. Choose 'replace' or 'append', or use a different name.",
                "table_name": table_name,
                "rows_imported": 0,
                "columns": [],
            }
        return {
            "success": False,
            "error": str(e),
            "table_name": table_name,
            "rows_imported": 0,
            "columns": [],
        }
    except Exception as e:
        logger.error(f"[DataImport] Import failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "table_name": table_name,
            "rows_imported": 0,
            "columns": [],
        }
