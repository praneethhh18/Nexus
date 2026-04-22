"""
Database Explorer — visual schema browser with sample data, table stats, and data import.
"""
from __future__ import annotations

import sqlite3
import streamlit as st
import pandas as pd
from pathlib import Path


def render():
    """Render the Database Explorer page."""
    st.markdown("### Database Explorer")
    st.caption("Browse tables, view schemas, preview data, and import new datasets.")

    from config.settings import DB_PATH

    if not Path(DB_PATH).exists():
        st.warning("Database not found. It will be created on first chat query.")
        return

    conn = sqlite3.connect(DB_PATH)

    # Get all tables
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
    )["name"].tolist()

    # Filter out internal NexusAgent tables for cleaner display
    internal_prefixes = ("nexus_", "sqlite_")
    data_tables = [t for t in tables if not any(t.startswith(p) for p in internal_prefixes)]
    system_tables = [t for t in tables if any(t.startswith(p) for p in internal_prefixes)]

    # ── Overview Metrics ──────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Data Tables", len(data_tables))
    m2.metric("System Tables", len(system_tables))

    total_rows = 0
    for t in data_tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            total_rows += count
        except Exception:
            pass
    m3.metric("Total Data Rows", f"{total_rows:,}")
    db_size = Path(DB_PATH).stat().st_size / 1024
    m4.metric("Database Size", f"{db_size:.0f} KB")

    st.divider()

    # ── Table Selector ────────────────────────────────────────────────────
    tab_data, tab_import, tab_system = st.tabs(["Data Tables", "Import Data", "System Tables"])

    with tab_data:
        if not data_tables:
            st.info("No data tables found. Import data or run the database setup.")
        else:
            selected_table = st.selectbox(
                "Select a table to explore",
                data_tables,
                key="data_table_select",
            )
            _render_table_detail(conn, selected_table)

    with tab_import:
        _render_import_section()

    with tab_system:
        if system_tables:
            selected_sys = st.selectbox(
                "Select a system table",
                system_tables,
                key="sys_table_select",
            )
            _render_table_detail(conn, selected_sys)
        else:
            st.info("No system tables yet.")

    conn.close()


def _render_table_detail(conn: sqlite3.Connection, table_name: str):
    """Render detailed view for a single table."""
    # ── Schema Info ───────────────────────────────────────────────────
    st.markdown(f"#### Table: `{table_name}`")

    cols_df = pd.read_sql_query(f"PRAGMA table_info([{table_name}])", conn)
    row_count = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]

    col_info, col_stats = st.columns([2, 1])

    with col_info:
        st.markdown("**Schema**")
        schema_display = cols_df[["name", "type", "notnull", "pk"]].copy()
        schema_display.columns = ["Column", "Type", "Not Null", "Primary Key"]
        schema_display["Not Null"] = schema_display["Not Null"].map({1: "Yes", 0: "No"})
        schema_display["Primary Key"] = schema_display["Primary Key"].map(
            lambda x: "Yes" if x > 0 else ""
        )
        st.dataframe(schema_display, use_container_width=True, hide_index=True)

    with col_stats:
        st.markdown("**Statistics**")
        st.metric("Rows", f"{row_count:,}")
        st.metric("Columns", len(cols_df))

        # Foreign keys
        fks = pd.read_sql_query(f"PRAGMA foreign_key_list([{table_name}])", conn)
        if not fks.empty:
            st.markdown("**Foreign Keys**")
            for _, fk in fks.iterrows():
                st.caption(f"`{fk['from']}` -> `{fk['table']}.{fk['to']}`")

    st.divider()

    # ── Data Preview ──────────────────────────────────────────────────
    st.markdown("**Data Preview**")
    preview_rows = st.slider(
        "Rows to show", 5, 100, 25, key=f"preview_{table_name}"
    )
    try:
        df = pd.read_sql_query(f"SELECT * FROM [{table_name}] LIMIT {preview_rows}", conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Could not read table: {e}")

    # ── Column Statistics ─────────────────────────────────────────────
    if row_count > 0:
        with st.expander("Column Statistics", expanded=False):
            numeric_cols = []
            for _, col in cols_df.iterrows():
                if col["type"] in ("INTEGER", "REAL", "NUMERIC"):
                    numeric_cols.append(col["name"])

            if numeric_cols:
                stats_parts = []
                for nc in numeric_cols[:8]:
                    try:
                        stat = pd.read_sql_query(
                            f"SELECT MIN([{nc}]) as min, MAX([{nc}]) as max, "
                            f"AVG([{nc}]) as avg, COUNT([{nc}]) as count "
                            f"FROM [{table_name}]",
                            conn,
                        )
                        stat.insert(0, "column", nc)
                        stats_parts.append(stat)
                    except Exception:
                        pass
                if stats_parts:
                    stats_df = pd.concat(stats_parts, ignore_index=True)
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No numeric columns to show statistics for.")


def _render_import_section():
    """Render the data import section."""
    st.markdown("#### Import CSV or Excel Data")
    st.caption("Upload a file to create a new database table you can query with natural language.")

    uploaded = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        key="data_import_upload",
    )

    if uploaded:
        import tempfile
        from sql_agent.data_import import preview_file, import_to_database, get_existing_tables

        # Save to temp file
        suffix = Path(uploaded.name).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        preview = preview_file(tmp_path)

        if preview.get("error"):
            st.error(preview["error"])
            return

        st.success(
            f"**{uploaded.name}** - {preview['file_type']} file with "
            f"{preview['total_rows']:,} rows and {preview['total_columns']} columns"
        )

        # Show preview
        st.markdown("**Preview (first 10 rows)**")
        st.dataframe(preview["dataframe"], use_container_width=True, hide_index=True)

        # Column info
        with st.expander("Column Details", expanded=False):
            for col_info in preview["columns"]:
                samples = ", ".join(col_info["sample_values"][:3])
                nulls = col_info["null_count"]
                null_str = f" ({nulls} nulls)" if nulls > 0 else ""
                st.caption(
                    f"`{col_info['name']}` ({col_info['dtype']}){null_str} - "
                    f"e.g. {samples}"
                )

        st.divider()

        # Import options
        st.markdown("**Import Settings**")
        table_name = st.text_input(
            "Table name",
            value=preview["suggested_table_name"],
            key="import_table_name",
        )

        existing = get_existing_tables()
        if table_name in existing:
            st.warning(f"Table `{table_name}` already exists.")
            action = st.radio(
                "What should we do?",
                ["Append rows to existing table", "Replace entire table", "Cancel"],
                key="import_conflict",
            )
            if_exists_map = {
                "Append rows to existing table": "append",
                "Replace entire table": "replace",
                "Cancel": None,
            }
            if_exists = if_exists_map[action]
        else:
            if_exists = "fail"

        if st.button("Import to Database", type="primary", key="import_btn"):
            if if_exists is None:
                st.info("Import cancelled.")
                return

            full_df = preview.get("_full_df")
            if full_df is None:
                st.error("Data not available. Please re-upload.")
                return

            with st.spinner(f"Importing {len(full_df):,} rows..."):
                result = import_to_database(full_df, table_name, if_exists=if_exists)

            if result["success"]:
                st.success(
                    f"Imported {result['rows_imported']:,} rows into `{result['table_name']}`. "
                    f"You can now query this table with natural language!"
                )
                # Clear the schema cache so new table is visible
                try:
                    from sql_agent.query_generator import clear_cache
                    clear_cache()
                except Exception:
                    pass
            else:
                st.error(f"Import failed: {result['error']}")

        # Clean up temp file
        try:
            Path(tmp_path).unlink()
        except Exception:
            pass
