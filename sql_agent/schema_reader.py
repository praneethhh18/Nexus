"""
Schema Reader — reads schema + sample rows for LLM context.

Backend-aware: uses sqlite_master / PRAGMA on SQLite; uses information_schema
on Postgres. Returns the same string shape regardless of backend so callers
don't care which database is live.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from pathlib import Path
from loguru import logger

from config.db import get_conn, is_postgres
from config.settings import DB_PATH


def _list_tables(c) -> list[str]:
    if is_postgres():
        c.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
        return [r[0] for r in c.fetchall()]
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [r[0] for r in c.fetchall()]


def _columns_of(c, table: str) -> list[tuple[str, str, bool]]:
    """Returns [(name, type, is_pk), ...]."""
    if is_postgres():
        c.execute(
            "SELECT column_name, data_type, "
            "  EXISTS (SELECT 1 FROM information_schema.table_constraints tc "
            "          JOIN information_schema.key_column_usage kcu "
            "          ON tc.constraint_name = kcu.constraint_name "
            "          WHERE tc.table_name = ? AND kcu.column_name = c.column_name "
            "          AND tc.constraint_type = 'PRIMARY KEY') AS is_pk "
            "FROM information_schema.columns c "
            "WHERE table_name = ? ORDER BY ordinal_position",
            (table, table),
        )
        return [(r[0], r[1], bool(r[2])) for r in c.fetchall()]
    c.execute(f"PRAGMA table_info({table})")
    return [(r[1], r[2], bool(r[5])) for r in c.fetchall()]  # name, type, pk


def _foreign_keys_of(c, table: str) -> list[tuple[str, str, str]]:
    """Returns [(from_col, to_table, to_col), ...]."""
    if is_postgres():
        c.execute(
            "SELECT kcu.column_name, ccu.table_name, ccu.column_name "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "JOIN information_schema.constraint_column_usage ccu "
            "  ON ccu.constraint_name = tc.constraint_name "
            "WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = ?",
            (table,),
        )
        return [(r[0], r[1], r[2]) for r in c.fetchall()]
    c.execute(f"PRAGMA foreign_key_list({table})")
    return [(r[3], r[2], r[4]) for r in c.fetchall()]  # from, table, to


def get_schema_string() -> str:
    """Read all table schemas + 3 sample rows for LLM context."""
    if not is_postgres() and not Path(DB_PATH).exists():
        logger.warning("[SchemaReader] DB not found — running db_setup first.")
        from sql_agent.db_setup import setup_database
        setup_database()

    conn = get_conn()
    c = conn.cursor()

    tables = _list_tables(c)
    parts = ["DATABASE SCHEMA\n" + "=" * 60]

    for table in tables:
        cols = _columns_of(c, table)
        col_defs = ", ".join(
            f"{name} ({dtype})" + (" PK" if is_pk else "")
            for name, dtype, is_pk in cols
        )

        fks = _foreign_keys_of(c, table)
        fk_str = ""
        if fks:
            fk_parts = [f"{from_col} → {to_table}.{to_col}" for from_col, to_table, to_col in fks]
            fk_str = f"\n  Foreign keys: {', '.join(fk_parts)}"

        try:
            c.execute(f"SELECT * FROM {table} LIMIT 3")
            rows = c.fetchall()
            col_names = [name for name, _, _ in cols]
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
    if not is_postgres() and not Path(DB_PATH).exists():
        return []
    conn = get_conn()
    c = conn.cursor()
    tables = _list_tables(c)
    conn.close()
    return tables
