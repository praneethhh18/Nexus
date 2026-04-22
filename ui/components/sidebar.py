"""
Sidebar component — system status, model info, document upload, monitor.
"""
from __future__ import annotations

import streamlit as st


def render_sidebar() -> dict:
    """Render the left sidebar and return any UI actions triggered."""
    actions = {}

    with st.sidebar:
        st.markdown("## NexusAgent")
        st.caption("Multi-Agent AI Assistant")
        st.divider()

        # ── System Status ─────────────────────────────────────────────────
        st.markdown('<p class="sidebar-header">System Status</p>', unsafe_allow_html=True)
        try:
            from config.llm_config import health_check
            from config.settings import OLLAMA_MODEL, EMBED_MODEL
            healthy, msg = health_check()
            if healthy:
                st.markdown(
                    '<span class="status-badge status-online">'
                    '<span class="status-dot online"></span> Ollama Online'
                    '</span>',
                    unsafe_allow_html=True,
                )
                st.caption(f"LLM: `{OLLAMA_MODEL}`")
                st.caption(f"Embed: `{EMBED_MODEL}`")
            else:
                st.markdown(
                    '<span class="status-badge status-offline">'
                    '<span class="status-dot offline"></span> Ollama Offline'
                    '</span>',
                    unsafe_allow_html=True,
                )
                st.error("Run `ollama serve` to start")
        except Exception as e:
            st.error(f"Cannot check Ollama: {e}")

        st.divider()

        # ── Knowledge Base ────────────────────────────────────────────────
        st.markdown('<p class="sidebar-header">Knowledge Base</p>', unsafe_allow_html=True)
        try:
            from rag.vector_store import get_collection_stats
            stats = get_collection_stats()
            st.metric("Documents", stats["document_count"])
        except Exception as e:
            st.caption(f"ChromaDB: {e}")

        # ── Database ──────────────────────────────────────────────────────
        st.markdown('<p class="sidebar-header">Database</p>', unsafe_allow_html=True)
        try:
            from sql_agent.schema_reader import get_table_list
            tables = get_table_list()
            st.metric("Tables", len(tables))
            if tables:
                st.caption(", ".join(tables[:6]))
        except Exception as e:
            st.caption(f"DB: {e}")

        st.divider()

        # ── Document Upload ───────────────────────────────────────────────
        st.markdown('<p class="sidebar-header">Upload Documents</p>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drag & drop files here",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            help="Files are ingested into the RAG knowledge base",
            label_visibility="collapsed",
        )
        if uploaded:
            actions["uploaded_files"] = uploaded

        st.divider()

        # ── Proactive Monitor ─────────────────────────────────────────────
        st.markdown('<p class="sidebar-header">Proactive Monitor</p>', unsafe_allow_html=True)
        try:
            from orchestrator.proactive_monitor import get_last_check_status
            status = get_last_check_status()
            if "checked_at" in status:
                anomaly_count = len(status.get("anomalies_found", []))
                if anomaly_count > 0:
                    st.markdown(
                        f'<span class="status-badge status-offline">'
                        f'{anomaly_count} anomalies</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<span class="status-badge status-online">All clear</span>',
                        unsafe_allow_html=True,
                    )
                st.caption(f"Last check: {status['checked_at'][:16]}")
            else:
                st.caption("No checks run yet")
        except Exception:
            st.caption("Monitor not initialized")

        if st.button("Run Anomaly Check", use_container_width=True):
            actions["run_monitor"] = True

        st.divider()
        st.caption("NexusAgent v2.0 | 100% Local | Zero API Cost")

    return actions
