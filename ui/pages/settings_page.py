"""
Settings Page — in-app configuration for NexusAgent.
"""
from __future__ import annotations

import streamlit as st
from pathlib import Path


def render():
    """Render the Settings page."""
    st.markdown("### Settings")
    st.caption("Configure NexusAgent behavior, models, and preferences.")

    tab_general, tab_models, tab_system = st.tabs(["General", "Models", "System Info"])

    # ── General Settings ──────────────────────────────────────────────────
    with tab_general:
        st.markdown("#### General Preferences")

        # Voice toggle
        if "voice_enabled" not in st.session_state:
            st.session_state.voice_enabled = True
        voice = st.toggle(
            "Enable Voice Output (TTS)",
            value=st.session_state.voice_enabled,
            help="When enabled, NexusAgent speaks responses aloud using pyttsx3",
        )
        st.session_state.voice_enabled = voice

        # Auto-speak toggle
        if "auto_speak" not in st.session_state:
            st.session_state.auto_speak = True
        auto = st.toggle(
            "Auto-speak responses",
            value=st.session_state.auto_speak,
            help="Automatically speak every response. If off, you can still use the voice button.",
            disabled=not voice,
        )
        st.session_state.auto_speak = auto

        st.divider()

        # Chat settings
        st.markdown("#### Chat Behavior")

        if "max_chat_display" not in st.session_state:
            st.session_state.max_chat_display = 50
        max_display = st.slider(
            "Messages to display in chat",
            min_value=10,
            max_value=200,
            value=st.session_state.max_chat_display,
            step=10,
            help="Older messages are still saved, just not displayed",
        )
        st.session_state.max_chat_display = max_display

        if "auto_chart" not in st.session_state:
            st.session_state.auto_chart = True
        auto_chart = st.toggle(
            "Auto-generate charts for data queries",
            value=st.session_state.auto_chart,
            help="Automatically create a chart when SQL queries return data",
        )
        st.session_state.auto_chart = auto_chart

        st.divider()

        # Reflection settings
        st.markdown("#### Quality Control")
        from config.settings import MAX_REFLECTION_RETRIES, MAX_SQL_RETRIES

        st.caption(f"Self-reflection retries: {MAX_REFLECTION_RETRIES}")
        st.caption(f"SQL retry attempts: {MAX_SQL_RETRIES}")
        st.caption("Edit `.env` to change these values.")

    # ── Model Settings ────────────────────────────────────────────────────
    with tab_models:
        st.markdown("#### LLM Configuration")

        from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_FALLBACK_MODEL, EMBED_MODEL

        # Show current config
        st.markdown("**Current Models**")
        st.code(
            f"Ollama URL:     {OLLAMA_BASE_URL}\n"
            f"Primary LLM:    {OLLAMA_MODEL}\n"
            f"Fallback LLM:   {OLLAMA_FALLBACK_MODEL}\n"
            f"Embedding:      {EMBED_MODEL}",
            language="yaml",
        )

        # Check available models
        st.divider()
        st.markdown("**Available Ollama Models**")
        try:
            import requests
            resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                if models:
                    for m in models:
                        name = m.get("name", "?")
                        size_gb = m.get("size", 0) / (1024 ** 3)
                        modified = m.get("modified_at", "")[:10]
                        is_active = name == OLLAMA_MODEL or OLLAMA_MODEL in name

                        status = " (active)" if is_active else ""
                        st.caption(f"`{name}` - {size_gb:.1f} GB{status}")
                else:
                    st.warning("No models found. Pull a model with: `ollama pull <model>`")
            else:
                st.error(f"Ollama returned HTTP {resp.status_code}")
        except Exception as e:
            st.error(f"Cannot connect to Ollama: {e}")

        st.divider()
        st.markdown("**Temperature**")
        if "llm_temperature" not in st.session_state:
            st.session_state.llm_temperature = 0.1
        temp = st.slider(
            "LLM Temperature",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.llm_temperature,
            step=0.05,
            help="Lower = more deterministic. Higher = more creative. Default: 0.1",
        )
        st.session_state.llm_temperature = temp

        if temp != 0.1:
            st.info(
                f"Temperature set to {temp}. This applies to new LLM calls. "
                "Restart the app to fully apply."
            )

        st.divider()
        st.caption(
            "To change models permanently, edit the `.env` file in the project root "
            "and restart the app."
        )

    # ── System Info ───────────────────────────────────────────────────────
    with tab_system:
        st.markdown("#### System Information")

        from config.settings import VERSION, DB_PATH, CHROMA_PATH, OUTPUTS_DIR

        st.code(
            f"Version:        NexusAgent v{VERSION}\n"
            f"Database:       {DB_PATH}\n"
            f"ChromaDB:       {CHROMA_PATH}\n"
            f"Outputs:        {OUTPUTS_DIR}",
            language="yaml",
        )

        st.divider()

        # Python & package info
        import sys
        st.markdown("**Runtime**")
        st.caption(f"Python: {sys.version.split()[0]}")
        st.caption(f"Platform: {sys.platform}")

        # Key packages
        st.markdown("**Key Packages**")
        packages = [
            "langchain", "langgraph", "langchain_ollama",
            "chromadb", "streamlit", "pandas",
            "reportlab", "plotly",
        ]
        for pkg in packages:
            try:
                mod = __import__(pkg)
                ver = getattr(mod, "__version__", "installed")
                st.caption(f"`{pkg}` {ver}")
            except ImportError:
                st.caption(f"`{pkg}` not installed")

        st.divider()

        # Database stats
        st.markdown("**Database Statistics**")
        try:
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            st.caption(f"Tables: {len(tables)}")

            total_rows = 0
            for (t,) in tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
                    total_rows += count
                except Exception:
                    pass
            st.caption(f"Total rows: {total_rows:,}")
            conn.close()
        except Exception as e:
            st.caption(f"DB stats unavailable: {e}")

        # ChromaDB stats
        st.markdown("**Knowledge Base**")
        try:
            from rag.vector_store import get_collection_stats
            stats = get_collection_stats()
            st.caption(f"Documents: {stats['document_count']}")
        except Exception as e:
            st.caption(f"ChromaDB stats unavailable: {e}")

        st.divider()

        # Danger zone
        st.markdown("#### Maintenance")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Reset LLM Connection", use_container_width=True):
                from config.llm_config import reset_instances
                reset_instances()
                st.success("LLM connection reset. Next query will reconnect.")

        with col_b:
            if st.button("Clear SQL Cache", use_container_width=True):
                try:
                    from sql_agent.query_generator import clear_cache
                    clear_cache()
                    st.success("SQL query cache cleared.")
                except Exception as e:
                    st.error(f"Failed: {e}")
