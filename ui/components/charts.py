"""
Charts panel component with improved empty state and layout.
"""
from __future__ import annotations

import streamlit as st


def render_charts_panel(state: dict) -> None:
    """Render the charts tab content."""
    fig = state.get("plotly_fig")
    chart_path = state.get("chart_path")
    whatif = state.get("whatif_result", {})

    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
        # Show data summary if SQL results available
        sql_res = state.get("sql_results", {})
        if sql_res.get("success") and sql_res.get("dataframe") is not None:
            df = sql_res["dataframe"]
            if not df.empty:
                with st.expander(f"View Data ({len(df)} rows)", expanded=False):
                    st.dataframe(df, use_container_width=True, height=200)
    elif chart_path:
        st.image(chart_path, use_column_width=True)
    elif whatif and not whatif.get("error"):
        wp = whatif.get("chart_path")
        if wp:
            st.image(wp, use_column_width=True)
        st.metric("Net Revenue Impact", whatif.get("net_impact", "N/A"))
        st.caption(f"Scenario: {whatif.get('scenario_description', '')}")
        if whatif.get("critique"):
            with st.expander("CFO Critique"):
                st.write(whatif["critique"])
    else:
        st.markdown(
            '<div class="info-card">'
            '<h4>No charts yet</h4>'
            '<p>Charts appear here automatically after data queries. '
            'Try asking about revenue, sales, or performance metrics.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
