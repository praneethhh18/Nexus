"""
Schema Reader — reads SQLite schema + sample rows for LLM context.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from loguru import logger

from config.settings import DB_PATH


def get_schema_string() -> str:
    """
    Read all table schemas + 3 sample rows from each table.
    Returns a formatted string an LLM can understand.
    """
    if not Path(DB_PATH).exists():
        logger.warning("[SchemaReader] DB not found — running db_setup first.")
        from sql_agent.db_setup import setup_database
        setup_database()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row["name"] for row in c.fetchall()]

    parts = ["DATABASE SCHEMA\n" + "="*60]

    for table in tables:
        # Column info
        c.execute(f"PRAGMA table_info({table})")
        cols = c.fetchall()
        col_defs = ", ".join(
            f"{col['name']} ({col['type']})" + (" PK" if col['pk'] else "")
            for col in cols
        )

        # Foreign keys
        c.execute(f"PRAGMA foreign_key_list({table})")
        fks = c.fetchall()
        fk_str = ""
        if fks:
            fk_parts = [f"{fk['from']} → {fk['table']}.{fk['to']}" for fk in fks]
            fk_str = f"\n  Foreign keys: {', '.join(fk_parts)}"

        # Sample rows
        try:
            c.execute(f"SELECT * FROM {table} LIMIT 3")
            rows = c.fetchall()
            col_names = [col["name"] for col in c.execute(f"PRAGMA table_info({table})").fetchall()]
            sample_lines = []
            for row in rows:
                row_dict = dict(zip(col_names, row))
                sample_lines.append("  " + str(row_dict))
            sample_str = "\n".join(sample_lines) if sample_lines else "  (empty table)"
        except Exception:
            sample_str = "  (could not read sample rows)"

        parts.append(
            f"\nTABLE: {table}\n"
            f"  Columns: {col_defs}"
            f"{fk_str}\n"
            f"  Sample rows:\n{sample_str}"
        )

    conn.close()
    schema = "\n".join(parts)
    logger.debug(f"[SchemaReader] Schema built for {len(tables)} tables.")
    return schema


def get_table_list() -> list[str]:
    """Return just the list of table names."""
    if not Path(DB_PATH).exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in c.fetchall()]
    conn.close()
    return tables
