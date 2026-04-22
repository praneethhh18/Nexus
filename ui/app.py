"""
NexusAgent — Main Streamlit Application
Voice-first multi-agent AI system. Run: streamlit run ui/app.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
from loguru import logger

# ── Page Config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="NexusAgent",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load CSS ──────────────────────────────────────────────────────────────────
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Bootstrap (first run only) ────────────────────────────────────────────────
@st.cache_resource(show_spinner="Starting NexusAgent...")
def _bootstrap():
    from config.settings import ensure_directories, validate_config
    ensure_directories()
    cfg = validate_config()

    from pathlib import Path as P
    from config.settings import DB_PATH
    if not P(DB_PATH).exists():
        from sql_agent.db_setup import setup_database
        setup_database()

    from utils.sample_docs_generator import ensure_documents_loaded
    ensure_documents_loaded()

    try:
        from orchestrator.proactive_monitor import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.warning(f"Monitor start failed: {e}")

    try:
        from workflows.scheduler import sync_all_workflows
        sync_all_workflows()
    except Exception as e:
        logger.warning(f"Workflow scheduler start failed: {e}")

    return cfg


cfg = _bootstrap()

# ── Session State ─────────────────────────────────────────────────────────────
_defaults = {
    "messages": [],
    "alert_history": [],
    "last_state": {},
    "voice_text": None,
    "processing": False,
    "query_count": 0,
    "conversation_id": None,
    "voice_enabled": True,
    "auto_speak": True,
    "max_chat_display": 50,
    "auto_chart": True,
}
for key, val in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Tier 1: Session tracking
if "user_session_id" not in st.session_state:
    from memory.user_memory import start_session
    st.session_state.user_session_id = start_session("default")


# ── Sidebar ───────────────────────────────────────────────────────────────────
from ui.components.sidebar import render_sidebar
sidebar_actions = render_sidebar()

# Handle file uploads (documents for RAG)
if sidebar_actions.get("uploaded_files"):
    with st.spinner("Ingesting uploaded documents..."):
        from rag.ingestion import ingest_file
        from rag.embedder import embed_documents
        from rag.vector_store import add_documents
        from config.settings import DOCUMENTS_DIR

        for uploaded_file in sidebar_actions["uploaded_files"]:
            dest = Path(DOCUMENTS_DIR) / uploaded_file.name
            dest.write_bytes(uploaded_file.read())
            docs = ingest_file(str(dest))
            if docs:
                texts = [d.page_content for d in docs]
                metas = [d.metadata for d in docs]
                embeddings = embed_documents(texts)
                added = add_documents(texts, embeddings, metas)
                st.sidebar.success(f"{uploaded_file.name}: {added} chunks loaded")

# Handle manual monitor trigger
if sidebar_actions.get("run_monitor"):
    with st.spinner("Running anomaly check..."):
        from orchestrator.proactive_monitor import manual_trigger
        result = manual_trigger()
        anomalies = result.get("anomalies_found", [])
        if anomalies:
            for a in anomalies:
                st.session_state.alert_history.append({
                    "title": f"Anomaly: {a['region']} Region",
                    "message": f"Revenue dropped {a['drop_pct']:.1f}% below average",
                    "severity": "critical" if a["drop_pct"] > 30 else "warning",
                    "timestamp": result.get("checked_at", ""),
                })
            st.sidebar.error(f"{len(anomalies)} anomalies found!")
        else:
            st.sidebar.success("No anomalies detected.")

# Handle conversation loading from sidebar
if sidebar_actions.get("load_conversation"):
    conv_id = sidebar_actions["load_conversation"]
    from memory.conversation_store import load_messages
    st.session_state.messages = load_messages(conv_id)
    st.session_state.conversation_id = conv_id
    st.session_state.last_state = {}


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="nexus-header">'
    '<h1>NexusAgent</h1>'
    '<p class="nexus-subtitle">'
    'Multi-Agent AI Assistant &middot; Runs 100% Locally &middot; Zero API Cost'
    '</p></div>',
    unsafe_allow_html=True,
)

# ── Page Navigation ───────────────────────────────────────────────────────────
page = st.radio(
    "",
    ["Chat", "Database", "What-If", "Reports", "History", "Workflows", "Settings"],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
#   PAGE: CHAT
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Chat":
    main_col, right_col = st.columns([7, 3])

    with main_col:
        # ── Welcome screen when no messages ───────────────────────────────
        if not st.session_state.messages:
            st.markdown(
                '<div class="welcome-container">'
                '<h3>Welcome to NexusAgent</h3>'
                '<p>Ask about your business data, documents, or operations. '
                'Use voice or type below.</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            quick_actions = [
                ("Show me revenue by region", "Data Query"),
                ("What does our company policy say about remote work?", "Document Search"),
                ("Generate a sales performance report", "PDF Report"),
                ("What if revenue drops 20%?", "What-If Scenario"),
            ]
            cols = st.columns(len(quick_actions))
            for i, (query, label) in enumerate(quick_actions):
                with cols[i]:
                    if st.button(
                        f"{label}",
                        key=f"qa_{i}",
                        use_container_width=True,
                        help=query,
                    ):
                        st.session_state.voice_text = query
                        st.rerun()

            st.markdown("---")
        else:
            # ── Render chat history ───────────────────────────────────────
            from ui.components.chat import render_chat_history
            render_chat_history(
                st.session_state.messages,
                max_display=st.session_state.max_chat_display,
            )

        # ── Input Area ────────────────────────────────────────────────────
        input_col, voice_col = st.columns([10, 1])

        with input_col:
            user_text = st.chat_input(
                "Ask about data, documents, or operations..."
            )

        with voice_col:
            voice_clicked = st.button("Mic", help="Record voice input (5 seconds)")

        # Handle voice
        if voice_clicked:
            with st.spinner("Listening..."):
                try:
                    from voice.listener import listen
                    voice_text = listen(duration=5)
                    if voice_text:
                        st.session_state.voice_text = voice_text
                        st.info(f"Heard: *{voice_text}*")
                    else:
                        st.warning("Could not capture voice. Please type instead.")
                except Exception as e:
                    logger.warning(f"Voice input failed: {e}")
                    st.warning("Voice input unavailable. Please type your question.")

        # Use voice text if set
        if st.session_state.voice_text:
            user_text = st.session_state.voice_text
            st.session_state.voice_text = None

        # ── Process Query ─────────────────────────────────────────────────
        if user_text:
            timestamp = datetime.now().strftime("%H:%M")

            # Auto-create conversation if needed
            if st.session_state.conversation_id is None:
                from memory.conversation_store import create_conversation, auto_title
                conv_id = create_conversation()
                st.session_state.conversation_id = conv_id
                auto_title(conv_id, user_text)

            st.session_state.messages.append({
                "role": "user",
                "content": user_text,
                "tools_used": [],
                "citations": [],
                "timestamp": timestamp,
            })

            query_start = time.time()
            with st.spinner("Thinking..."):
                try:
                    from orchestrator.graph import run
                    result_state = run(user_text)
                except Exception as e:
                    logger.error(f"Graph run error: {e}")
                    result_state = {
                        "final_answer": (
                            f"I encountered an error processing your request. "
                            f"Please make sure Ollama is running (`ollama serve`).\n\n"
                            f"Error details: {e}"
                        ),
                        "tools_used": [],
                        "citations": [],
                    }
            query_duration = int((time.time() - query_start) * 1000)

            answer = result_state.get("final_answer", "I couldn't generate a response.")
            tools = result_state.get("tools_used", [])
            citations = result_state.get("citations", [])

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "tools_used": tools,
                "citations": citations,
                "sources_used": result_state.get("sources_used", []),
                "multi_agent": result_state.get("multi_agent", False),
                "agents_used": result_state.get("agents_used", []),
                "timestamp": datetime.now().strftime("%H:%M"),
            })

            st.session_state.last_state = result_state
            st.session_state.query_count += 1

            # ── Save to conversation store ────────────────────────────────
            try:
                from memory.conversation_store import save_full_conversation
                save_full_conversation(
                    st.session_state.conversation_id,
                    st.session_state.messages,
                )
            except Exception as e:
                logger.warning(f"Failed to save conversation: {e}")

            # ── Log to query history ──────────────────────────────────────
            try:
                from memory.query_history import log_query
                log_query(
                    query=user_text,
                    intent=result_state.get("intent", {}).get("primary_intent", "unknown"),
                    tools_used=tools,
                    answer_preview=answer[:500],
                    success="error" not in answer.lower()[:50],
                    duration_ms=query_duration,
                )
            except Exception as e:
                logger.warning(f"Failed to log query: {e}")

            # Tier 1: Log session query
            try:
                from memory.user_memory import log_session_query
                log_session_query(
                    session_id=st.session_state.user_session_id,
                    topic=result_state.get("intent", {}).get("primary_intent", "unknown"),
                    tools=tools,
                )
            except Exception:
                pass

            # Speak the answer if enabled
            if st.session_state.voice_enabled and st.session_state.auto_speak:
                try:
                    from voice.speaker import speak
                    speak(answer)
                except Exception:
                    pass

            st.rerun()

        # ── Action buttons ────────────────────────────────────────────────
        if st.session_state.messages:
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button("New Chat", use_container_width=True):
                    # Save current conversation first
                    if st.session_state.conversation_id:
                        try:
                            from memory.conversation_store import save_full_conversation
                            save_full_conversation(
                                st.session_state.conversation_id,
                                st.session_state.messages,
                            )
                        except Exception:
                            pass
                    st.session_state.messages = []
                    st.session_state.conversation_id = None
                    from memory.short_term import get_default_memory
                    get_default_memory().clear()
                    st.session_state.last_state = {}
                    st.session_state.query_count = 0
                    st.rerun()
            with btn_col2:
                # Export as Markdown
                from utils.export_conversation import to_markdown
                md_content = to_markdown(st.session_state.messages)
                st.download_button(
                    "Export Markdown",
                    md_content,
                    file_name=f"nexus_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with btn_col3:
                # Export as PDF
                if st.button("Export PDF", use_container_width=True):
                    with st.spinner("Building PDF..."):
                        from utils.export_conversation import to_pdf
                        pdf_path = to_pdf(st.session_state.messages)
                    if pdf_path and Path(pdf_path).exists():
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                "Download PDF",
                                f.read(),
                                file_name=Path(pdf_path).name,
                                mime="application/pdf",
                                key="dl_conv_pdf",
                            )
                    else:
                        st.warning("PDF export failed.")

    # ── Right Panel ───────────────────────────────────────────────────────
    with right_col:
        tab_charts, tab_reports, tab_alerts, tab_audit, tab_kb, tab_memory = st.tabs(
            ["Charts", "Reports", "Alerts", "Audit", "Knowledge", "Memory"]
        )

        with tab_charts:
            from ui.components.charts import render_charts_panel
            ls = st.session_state.last_state
            fig = None
            chart_path = None
            sql_res = ls.get("sql_results", {})
            if (
                st.session_state.auto_chart
                and sql_res.get("success")
                and sql_res.get("dataframe") is not None
            ):
                df = sql_res["dataframe"]
                if not df.empty:
                    try:
                        from report_generator.chart_selector import select_chart_type
                        from report_generator.chart_builder import build_chart
                        query = ls.get("query", "")
                        ct, _ = select_chart_type(df, query)
                        fig, chart_path = build_chart(df, ct, query[:50], save=False)
                    except Exception:
                        pass
            render_charts_panel({**ls, "plotly_fig": fig, "chart_path": chart_path})

        with tab_reports:
            from action_tools.file_dispatcher import get_recent_outputs
            reports = get_recent_outputs(n=10, subfolder="reports")
            if reports:
                for r in reports:
                    st.markdown(
                        f'<div class="report-card">'
                        f'<b>{r["name"]}</b> &middot; {r["size_kb"]} KB<br>'
                        f'<span style="font-size:11px;color:#94a3b8;">{r["modified"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    with open(r["path"], "rb") as f:
                        st.download_button(
                            "Download",
                            f.read(),
                            file_name=r["name"],
                            mime="application/pdf",
                            key=r["path"],
                        )
            else:
                st.info("Ask me to generate a report to see PDF reports here.")

        with tab_alerts:
            from ui.components.alerts import render_alerts_panel
            render_alerts_panel(st.session_state.alert_history)

        with tab_audit:
            from ui.components.audit import render_audit_panel
            render_audit_panel()

        with tab_kb:
            st.markdown("#### Knowledge Base")
            from rag.multi_document_rag import get_sources_list
            sources = get_sources_list()
            if sources:
                st.caption(f"{len(sources)} document(s) loaded")
                for s in sources:
                    st.markdown(
                        f'<div class="kb-entry">'
                        f'<b>{s["name"]}</b> &middot; '
                        f'{s["chunk_count"]} chunks &middot; '
                        f'{s["page_count"]} pages &middot; '
                        f'{s["file_type"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No documents loaded. Upload files via the sidebar.")

        with tab_memory:
            st.markdown("#### Agent Memory")
            from memory.user_memory import get_user_summary
            summary = get_user_summary("default")
            profile = summary.get("profile", {})
            interactions = profile.get("total_interactions", 0)
            st.caption(f"Total interactions: {interactions}")

            if summary.get("favorite_topics"):
                topics = summary["favorite_topics"]
                if isinstance(topics, list) and topics:
                    st.markdown("**Frequent Topics**")
                    for t in topics[:5]:
                        st.caption(f"- {t}")

            if summary.get("preferred_regions"):
                regions = summary["preferred_regions"]
                if isinstance(regions, list) and regions:
                    st.markdown("**Preferred Regions**")
                    for r in regions[:3]:
                        st.caption(f"- {r}")

            if summary.get("top_patterns"):
                st.markdown("**Detected Patterns**")
                for p in summary["top_patterns"][:5]:
                    st.caption(
                        f"- {p['pattern_type']}: '{p['pattern_key']}' "
                        f"({p['frequency']}x)"
                    )

            if interactions > 0:
                st.divider()
                if st.button("Clear Memory", type="secondary"):
                    confirm = st.checkbox("Confirm: clear all agent memory?", key="confirm_clear_mem")
                    if confirm:
                        from memory.user_memory import _get_conn
                        conn = _get_conn()
                        conn.execute("DELETE FROM nexus_user_memory WHERE user_id='default'")
                        conn.execute("DELETE FROM nexus_user_patterns WHERE user_id='default'")
                        conn.execute(
                            "UPDATE nexus_user_profiles SET total_interactions=0, "
                            "favorite_topics='[]', preferred_regions='[]' WHERE user_id='default'"
                        )
                        conn.commit()
                        conn.close()
                        st.success("Memory cleared.")
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#   PAGE: DATABASE EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Database":
    from ui.pages.database_explorer import render
    render()


# ═══════════════════════════════════════════════════════════════════════════════
#   PAGE: WHAT-IF SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "What-If":
    st.markdown("### What-If Scenario Simulator")
    st.caption("Model business scenarios and get AI-powered impact analysis with critique.")

    examples = [
        "What if our revenue drops 20%?",
        "What if we increase prices by 10% and lose 15% of customers?",
        "What if the South region improves by 30%?",
        "What if our top product's sales dropped 25%?",
    ]
    selected = st.selectbox("Try an example scenario:", ["Custom..."] + examples)
    if selected == "Custom...":
        scenario_text = st.text_input("Enter your what-if scenario:")
    else:
        scenario_text = selected

    if st.button("Run Simulation", type="primary") and scenario_text:
        with st.spinner("Running simulation..."):
            from utils.whatif_simulator import run_full_simulation
            result = run_full_simulation(scenario_text)

        if result.get("error"):
            st.error(f"Simulation failed: {result['error']}")
        else:
            st.success(f"**Scenario:** {result.get('scenario_description')}")

            m1, m2, m3 = st.columns(3)
            m1.metric("Before Revenue",
                       f"${result.get('before_total_revenue', 0):,.0f}")
            m2.metric("After Revenue",
                       f"${result.get('after_total_revenue', 0):,.0f}",
                       delta=f"{result.get('net_impact_pct', 0):+.1f}%")
            m3.metric("Net Impact", result.get("net_impact", "N/A"))

            if result.get("chart_path"):
                st.image(result["chart_path"], use_column_width=True)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                with st.expander("Assumptions", expanded=True):
                    st.write(result.get("assumptions", "N/A"))
            with col_d2:
                with st.expander("CFO Critique", expanded=True):
                    st.write(result.get("critique", "N/A"))

            with st.expander("Before vs After Data"):
                col_b, col_a = st.columns(2)
                col_b.subheader("Before")
                col_b.dataframe(result.get("before_df"), use_container_width=True)
                col_a.subheader("After")
                col_a.dataframe(result.get("after_df"), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#   PAGE: REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Reports":
    st.markdown("### Generate Business Reports")
    st.caption("Create professional PDF reports from your data.")

    report_query = st.text_input(
        "What do you want a report about?",
        placeholder="e.g. Regional sales performance for Q3 2025",
    )

    if st.button("Generate Report", type="primary") and report_query:
        progress_bar = st.progress(0, text="Querying data...")
        try:
            progress_bar.progress(20, text="Generating SQL...")
            from orchestrator.graph import run
            result = run(f"Generate a report: {report_query}")
            progress_bar.progress(70, text="Building PDF...")
            pdf_path = result.get("report_path", "")
            progress_bar.progress(100, text="Done!")
            time.sleep(0.5)
            progress_bar.empty()

            if pdf_path and Path(pdf_path).exists():
                st.success(f"Report generated: {Path(pdf_path).name}")
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Download PDF Report",
                        f.read(),
                        file_name=Path(pdf_path).name,
                        mime="application/pdf",
                        type="primary",
                    )
            else:
                st.warning("Report generated. Check the Reports tab on the Chat page.")
        except Exception as e:
            progress_bar.empty()
            st.error(f"Report generation failed: {e}")

    st.divider()
    st.markdown("### Recent Reports")
    from action_tools.file_dispatcher import get_recent_outputs
    reports = get_recent_outputs(n=10, subfolder="reports")
    if reports:
        for r in reports:
            with st.expander(f"{r['name']} - {r['modified']}"):
                st.caption(f"Size: {r['size_kb']} KB")
                with open(r["path"], "rb") as f:
                    st.download_button(
                        "Download",
                        f.read(),
                        file_name=r["name"],
                        mime="application/pdf",
                        key=f"dl_{r['path']}",
                    )
    else:
        st.info("No reports generated yet.")


# ═══════════════════════════════════════════════════════════════════════════════
#   PAGE: QUERY HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "History":
    from ui.pages.query_history_page import render
    render()


# ═══════════════════════════════════════════════════════════════════════════════
#   PAGE: WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Workflows":
    from ui.pages.workflow_builder import render
    render()


# ═══════════════════════════════════════════════════════════════════════════════
#   PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Settings":
    from ui.pages.settings_page import render
    render()


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="nexus-footer">'
    'NexusAgent v2.0 &middot; 100% Local &middot; Zero API Cost &middot; '
    'Powered by Ollama + LangGraph'
    '</div>',
    unsafe_allow_html=True,
)
