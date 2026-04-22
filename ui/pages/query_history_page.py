"""
Query History — searchable history of past queries with re-run support.
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime


def render():
    """Render the Query History page."""
    st.markdown("### Query History")
    st.caption("Search, filter, and re-run your past queries.")

    from memory.query_history import get_history, get_stats, toggle_star, clear_history

    # ── Stats ─────────────────────────────────────────────────────────────
    stats = get_stats()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Queries", stats["total_queries"])
    m2.metric("Avg Response Time", f"{stats['avg_duration_ms']}ms")
    m3.metric("Success Rate", f"{stats['success_rate_pct']}%")

    if stats["top_intents"]:
        with st.expander("Top Query Types", expanded=False):
            for item in stats["top_intents"]:
                st.caption(f"`{item['intent']}` - {item['count']} queries")

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────
    filter_col1, filter_col2, filter_col3 = st.columns([3, 2, 1])
    with filter_col1:
        search = st.text_input(
            "Search queries",
            placeholder="Type to search...",
            key="qh_search",
            label_visibility="collapsed",
        )
    with filter_col2:
        intent_options = ["All"] + [i["intent"] for i in stats.get("top_intents", [])]
        intent_filter = st.selectbox(
            "Filter by type",
            intent_options,
            key="qh_intent",
            label_visibility="collapsed",
        )
    with filter_col3:
        starred_only = st.checkbox("Starred only", key="qh_starred")

    # ── Query List ────────────────────────────────────────────────────────
    history = get_history(
        search=search if search else None,
        intent_filter=intent_filter if intent_filter != "All" else None,
        starred_only=starred_only,
        limit=50,
    )

    if not history:
        st.info(
            "No query history yet. Start chatting to build your history, "
            "or adjust your filters."
        )
        return

    st.caption(f"Showing {len(history)} queries")

    for item in history:
        query_id = item["id"]
        query_text = item["query"]
        answer = item.get("answer_preview", "")
        intent = item.get("intent", "unknown")
        tools = item.get("tools_used", [])
        success = item.get("success", True)
        duration = item.get("duration_ms", 0)
        ts = item.get("timestamp", "")
        starred = item.get("starred", False)

        # Format timestamp
        try:
            dt = datetime.fromisoformat(ts)
            time_str = dt.strftime("%b %d, %H:%M")
        except Exception:
            time_str = ts[:16] if ts else ""

        # Render query card
        tools_str = ", ".join(tools) if tools else ""
        status_icon = "OK" if success else "FAIL"
        star_label = "[*]" if starred else "[ ]"

        with st.expander(f"{star_label} {query_text[:80]}", expanded=False):
            # Metadata row
            meta_col1, meta_col2, meta_col3 = st.columns([2, 2, 1])
            meta_col1.caption(f"Type: `{intent}` | Tools: `{tools_str}`")
            meta_col2.caption(f"Time: {time_str} | Duration: {duration}ms")
            meta_col3.caption(f"Status: {status_icon}")

            # Answer preview
            if answer:
                st.markdown(f"**Answer:** {answer[:300]}{'...' if len(answer) > 300 else ''}")

            # Actions
            action_col1, action_col2, action_col3 = st.columns(3)
            with action_col1:
                if st.button("Re-run", key=f"rerun_{query_id}", use_container_width=True):
                    st.session_state.voice_text = query_text
                    st.switch_page_hack = "Chat"
                    st.rerun()

            with action_col2:
                star_text = "Unstar" if starred else "Star"
                if st.button(star_text, key=f"star_{query_id}", use_container_width=True):
                    toggle_star(query_id)
                    st.rerun()

            with action_col3:
                if st.button("Copy", key=f"copy_{query_id}", use_container_width=True):
                    st.code(query_text, language=None)

    # ── Clear History ─────────────────────────────────────────────────────
    st.divider()
    if stats["total_queries"] > 0:
        if st.button("Clear All History", type="secondary"):
            confirm = st.checkbox("Confirm: delete all query history?", key="confirm_clear_qh")
            if confirm:
                count = clear_history()
                st.success(f"Cleared {count} queries from history.")
                st.rerun()
