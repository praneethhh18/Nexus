"""
Audit trail viewer component.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd


def render_audit_panel() -> None:
    """Render the audit log tab."""
    try:
        from memory.audit_logger import get_recent_logs, get_stats, export_csv
        import tempfile, os

        stats = get_stats()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Calls", stats["total_calls"])
        col2.metric("Success Rate", f"{stats['success_rate_pct']}%")
        col3.metric("Most Used", stats["most_used_tool"])
        col4.metric("Avg Duration", f"{stats['avg_duration_ms']}ms")

        st.divider()

        logs = get_recent_logs(n=20)
        if logs:
            df = pd.DataFrame(logs)
            display_cols = ["timestamp", "tool_name", "input_summary",
                            "output_summary", "success", "duration_ms"]
            display_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, height=300)

            if st.button("Export Audit CSV"):
                tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
                export_csv(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button(
                        "Download CSV",
                        f.read(),
                        file_name="nexusagent_audit.csv",
                        mime="text/csv",
                    )
                os.unlink(tmp.name)
        else:
            st.info("No audit entries yet. Start chatting to see logs here.")

    except Exception as e:
        st.error(f"Audit log unavailable: {e}")
