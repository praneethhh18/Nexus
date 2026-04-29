# NexusAgent Module Reference

What each module does, what it depends on, and how to fix it if it breaks.

---

## Tier 1 — High Impact Features (Latest)

### rag/multi_document_rag.py
**What it does:** Multi-document RAG with cross-source reasoning. Supports:
- Named source tracking — knows which answer came from which file
- Cross-document comparison — "Compare Q2 report vs Q3 report on margins"
- Contradiction detection — "Find contradictions between sales policy and HR policy"
- Multi-source synthesis — reasons across multiple documents simultaneously
**Depends on:** `rag/vector_store.py`, `rag/embedder.py`, `config/llm_config.py`
**If it fails:** Falls back to standard single-doc retrieval.

### memory/user_memory.py
**What it does:** Persistent long-term memory per user with:
- User profiles that grow smarter over time
- Preference tracking ("You always ask about South region first")
- Decision memory ("Last week you approved the budget cut scenario")
- Pattern recognition across sessions
- Personalized responses based on user history
- Automatic learning from every interaction
**Depends on:** `config/settings.py`, `config/llm_config.py`
**If it fails:** App continues without personalized memory. View/clear in Memory tab.

### orchestrator/multi_agent.py
**What it does:** Multi-agent collaboration system with specialist agents:
- **PlannerAgent** — breaks complex tasks into steps, delegates to specialists
- **DataAgent** — SQL + data analysis, chart generation
- **DocAgent** — RAG + document reasoning, cross-doc comparison
- **SynthesisAgent** — combines results from all agents into final answer
Automatically activates when query needs both data and document analysis.
**Depends on:** `sql_agent/executor.py`, `rag/multi_document_rag.py`, `config/llm_config.py`
**If it fails:** Falls back to single-agent pipeline.

---

## config/settings.py
**What it does:** Loads all `.env` values as typed Python constants. Every other module imports settings from here.
**Depends on:** `.env` file, `python-dotenv`
**If it fails:** Check `.env` exists and has `OLLAMA_BASE_URL` set. Run `python -c "from config.settings import validate_config; print(validate_config())"`

## config/llm_config.py
**What it does:** Creates and caches the Ollama LLM and embedding model instances. `health_check()` pings Ollama.
**Depends on:** `config/settings.py`, `langchain-community`, Ollama running locally
**If it fails:** Run `ollama serve` in a terminal. Verify with `ollama list`.

---

## rag/ingestion.py
**What it does:** Parses PDF/DOCX/TXT files into LangChain Document chunks with metadata (source, page, chunk_index).
**Depends on:** `pymupdf`, `python-docx`, `langchain`
**If it fails:** Check the file isn't corrupt. Try `python -c "import fitz; print(fitz.__version__)"`

## rag/embedder.py
**What it does:** Generates vector embeddings using Ollama's nomic-embed-text model. Caches the model in memory.
**Depends on:** Ollama running with `nomic-embed-text` model pulled
**If it fails:** Run `ollama pull nomic-embed-text`

## rag/vector_store.py
**What it does:** Stores and searches document embeddings in ChromaDB (persistent at `chroma_db/`).
**Depends on:** `chromadb`, `rag/embedder.py`
**If it fails:** Delete the `chroma_db/` folder and restart the app to rebuild.

## rag/retriever.py
**What it does:** Full RAG pipeline — embed query → search ChromaDB → LLM rerank → return top 3 with citations.
**Depends on:** `rag/embedder.py`, `rag/vector_store.py`, `config/llm_config.py`
**If it fails:** Check ChromaDB has documents (`get_collection_stats()`). Run `python rag/test_rag.py`

---

## sql_agent/db_setup.py
**What it does:** Creates the SQLite database with 8 tables and ~2,000 rows of MNC sample data. Includes planted anomalies.
**Depends on:** `faker`, `sqlite3` (stdlib)
**If it fails:** Delete `data/nexusagent.db` and run `python sql_agent/db_setup.py`

## sql_agent/schema_reader.py
**What it does:** Reads all table schemas + 3 sample rows from each table, formats as LLM-readable string.
**Depends on:** `config/settings.py`, `sqlite3`
**If it fails:** Check `DB_PATH` in `.env` points to existing database.

## sql_agent/query_generator.py
**What it does:** Converts natural language to SQL using local LLM. Validates SQL before returning.
**Depends on:** `config/llm_config.py`, `sql_agent/schema_reader.py`
**If it fails:** Check Ollama is running. The LLM output may need the model to be better at SQL.

## sql_agent/executor.py
**What it does:** Executes SQL, self-corrects on error (up to MAX_SQL_RETRIES), explains results in plain English.
**Depends on:** `sql_agent/query_generator.py`, `config/llm_config.py`, `memory/audit_logger.py`
**If it fails:** Run `python sql_agent/test_sql.py` to diagnose.

---

## action_tools/email_tool.py
**What it does:** Drafts professional emails with LLM, requires explicit approval, sends via Gmail SMTP.
**Depends on:** `config/llm_config.py`, `config/settings.py` (GMAIL credentials)
**If it fails:** If email disabled, drafts save to `outputs/email_drafts/`. Check Gmail App Password is correct.

## action_tools/discord_tool.py
**What it does:** Sends rich Discord embed alerts via webhook. Falls back to desktop notifications (plyer).
**Depends on:** `config/settings.py`, `requests`, `plyer`
**If it fails:** If DISCORD_WEBHOOK_URL is empty, falls back to desktop notification. Check webhook URL is valid.

## action_tools/file_dispatcher.py
**What it does:** Saves generated files to `outputs/` with timestamps. Lists recent files.
**Depends on:** stdlib only
**If it fails:** Check `outputs/` directory exists and is writable.

---

## report_generator/chart_selector.py
**What it does:** Uses local LLM to pick the best chart type (bar/line/pie/scatter/table) for a DataFrame.
**Depends on:** `config/llm_config.py`, `pandas`
**If it fails:** Falls back to heuristic selection based on data shape.

## report_generator/chart_builder.py
**What it does:** Builds Plotly charts and saves as PNG using kaleido.
**Depends on:** `plotly`, `kaleido`
**If it fails:** If kaleido fails, charts still work in Streamlit (just no PNG file). Run `pip install kaleido`

## report_generator/pdf_builder.py
**What it does:** Generates professional PDF reports with cover page, chart, data table, insights.
**Depends on:** `reportlab`
**If it fails:** Run `pip install reportlab`. Check `outputs/reports/` directory exists.

---

## voice/listener.py
**What it does:** Records from microphone, transcribes with faster-whisper (local). Falls back to text input.
**Depends on:** `sounddevice`, `soundfile`, `faster-whisper`
**If it fails:** Gracefully falls back to text input. Check microphone is plugged in and permissions granted.

## voice/speaker.py
**What it does:** Text-to-speech via pyttsx3 (fully offline). Falls back to printing text.
**Depends on:** `pyttsx3`
**If it fails:** Falls back to printing the response. `pyttsx3` may need system voice engine.

## voice/tone_analyzer.py
**What it does:** Classifies query tone (urgent/confused/casual etc.) to adapt response style.
**Depends on:** `config/llm_config.py`
**If it fails:** Falls back to "casual" tone. Non-critical component.

---

## memory/short_term.py
**What it does:** In-RAM deque of last 10 conversation turns. Used for conversation context in prompts.
**Depends on:** `config/llm_config.py` (for summarization)
**If it fails:** Loses conversation context but doesn't break other features.

## memory/long_term.py
**What it does:** Persists extracted facts in SQLite across sessions. Auto-extracts after every 5 turns.
**Depends on:** `config/settings.py`, `config/llm_config.py`
**If it fails:** App continues without cross-session memory. Check DB_PATH is writable.

## memory/audit_logger.py
**What it does:** Logs every tool call to `outputs/audit_log.json` AND SQLite. Never fails silently.
**Depends on:** `config/settings.py`, stdlib
**If it fails:** Audit logs simply won't be written. Non-critical for core functionality.

---

## orchestrator/intent_detector.py
**What it does:** Classifies query intent and selects which tools to activate.
**Depends on:** `config/llm_config.py`
**If it fails:** Defaults to `chitchat` intent (LLM responds directly).

## orchestrator/nodes.py
**What it does:** All LangGraph node functions. Each node calls the appropriate module and updates state.
**Depends on:** Every module above
**If it fails:** Individual node errors are caught and don't crash the whole graph.

## orchestrator/graph.py
**What it does:** Main LangGraph state machine. Routes queries through nodes based on intent. Falls back to sequential pipeline if LangGraph not available.
**Depends on:** `langgraph`, `orchestrator/nodes.py`, `orchestrator/intent_detector.py`
**If it fails:** Falls back to `_run_fallback_pipeline()` which runs nodes sequentially.

## orchestrator/self_reflection.py
**What it does:** Reviews synthesized answers for completeness. Forces PASS after MAX_REFLECTION_RETRIES.
**Depends on:** `config/llm_config.py`
**If it fails:** Forces PASS on error (doesn't block responses).

## orchestrator/proactive_monitor.py
**What it does:** APScheduler background job that detects revenue anomalies every MONITOR_INTERVAL_MINUTES.
**Depends on:** `apscheduler`, `sql_agent`, `report_generator`, `action_tools/discord_tool.py`
**If it fails:** Run `manual_trigger()` from the UI sidebar. Check `data/nexusagent.db` exists.

---

## utils/whatif_simulator.py
**What it does:** Parses what-if questions, applies math to DB data, generates comparison charts, critiques assumptions.
**Depends on:** `config/llm_config.py`, `sql_agent`, `report_generator/chart_builder.py`
**If it fails:** Returns error in result dict. Check database exists and has `sales_metrics` table.

## utils/sample_docs_generator.py
**What it does:** Generates 4 realistic business text documents and auto-ingests them into ChromaDB.
**Depends on:** `rag/` modules, `config/settings.py`
**If it fails:** Check ChromaDB path is writable. Run `python utils/sample_docs_generator.py`

---

## ui/app.py
**What it does:** Main Streamlit application. Routes all interactions through the LangGraph orchestrator.
**Depends on:** Everything above
**If it fails:** Check `streamlit run ui/app.py` from the project root. Check all dependencies installed.
