# NexusAgent — Complete Build Instructions for Claude Code

> This is a self-contained build document. Claude Code should read this entire file, ask the user for any required information listed in the **"What I Need From You"** section, then build the complete system autonomously without further prompting.

---

## What I Need From You (Claude Code must ask these before starting)

Before writing any code, ask the user for the following. Number each question and wait for all answers before proceeding:

1. **Your OS** — Windows, Mac, or Linux? (affects some install commands)
2. **Ollama models** — Have you installed Ollama from ollama.ai? If yes, which models do you have pulled? If no, I will give you the exact commands.
3. **Email** — Do you want the email action tool enabled? If yes, provide your Gmail address and a Gmail App Password (not your regular password — I will explain how to get one).
4. **Discord notifications** — Do you want Discord alerts enabled? If yes, provide a Discord webhook URL. If no, I will use a local desktop notification fallback.
5. **Project location** — Which folder should I create the project in? Provide the full path or just say "current folder".
6. **Demo dataset** — Should I use a sample e-commerce dataset (customers, orders, sales) or a finance dataset (transactions, accounts, budgets)? This is for demonstrating the SQL agent.
7. **Sample documents** — Do you have any PDFs you want to load into the RAG system? If yes, tell me their location. If no, I will generate sample company documents automatically.

Once you have all answers, confirm with the user: "I have everything I need. Starting the build now." Then proceed through all phases in order without stopping.

---

## Project Overview

**Name:** NexusAgent  
**Tagline:** A voice-first multi-agent AI system that reads your documents, queries your data, takes actions, and monitors your business — all running locally for free.  
**Framework:** LangGraph orchestrator with modular tools  
**LLM:** Ollama (local, open source, free)  
**Cost:** ₹0 — everything runs on your machine  

### What It Does (5 Core Scenarios)

1. **Document Q&A** — Ask anything about uploaded PDFs/docs → RAG engine finds the answer with exact citations
2. **Data queries** — Ask business questions → SQL agent queries the database and returns data + charts
3. **Automated actions** — Ask it to send emails or notifications → it drafts, shows you, waits for approval, then sends
4. **Business reports** — Ask for a summary or analysis → generates a professional PDF report automatically
5. **Proactive monitoring** — Runs in background, detects anomalies in data, alerts you without being asked

### Unique Features That Make This Stand Out

- Self-reflection loop (agent checks its own answer before responding)
- Human-in-the-loop (asks permission before any real-world action)
- Proactive anomaly detection (acts without being prompted)
- What-if scenario simulator with critique
- Full audit trail of every action
- Voice input (Whisper local) + Voice output (pyttsx3 local)
- Tone detection from voice input
- Multi-tool routing (uses RAG + SQL simultaneously when needed)
- Long-term memory across sessions
- 100% open source, zero API costs

---

## Complete Tech Stack (Open Source Only)

| Component | Tool | Why |
|---|---|---|
| LLM | Ollama + Llama3.1 / Mistral / Qwen2.5 | Local, free, powerful |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Local, no API needed |
| Vector DB | ChromaDB | Local, open source |
| Orchestrator | LangGraph | Production-grade, free |
| PDF parsing | PyMuPDF (fitz) + Unstructured | Best open source parsers |
| Database | SQLite + DuckDB | Local, zero config |
| Voice input | faster-whisper | Local Whisper, no API |
| Voice output | pyttsx3 + Coqui TTS | Fully offline TTS |
| UI | Streamlit | Free, fast |
| Charts | Plotly + Matplotlib | Free, beautiful |
| PDF reports | ReportLab + WeasyPrint | Free PDF generation |
| Scheduling | APScheduler | Free background jobs |
| Email | Python smtplib | Built into Python |
| Notifications | Discord webhook / desktop notify | Free |
| Data generation | Faker | Free fake data |
| Containerization | Docker + docker-compose | Free |

---

## Folder Structure to Create

```
nexusagent/
├── config/
│   ├── llm_config.py          # Ollama LLM + embedding setup
│   ├── settings.py            # All config constants
│   └── setup_guide.md         # How to install Ollama + pull models
├── rag/
│   ├── ingestion.py           # PDF/TXT/DOCX parsing + chunking
│   ├── embedder.py            # Local sentence-transformers embeddings
│   ├── vector_store.py        # ChromaDB operations
│   ├── retriever.py           # Query + rerank + citations
│   └── test_rag.py            # Test script
├── sql_agent/
│   ├── db_setup.py            # Create + populate sample database
│   ├── schema_reader.py       # Auto-read DB schema
│   ├── query_generator.py     # NL to SQL with local LLM
│   ├── executor.py            # Execute + self-correct on error
│   └── test_sql.py            # Test script
├── action_tools/
│   ├── email_tool.py          # Draft + approve + send via smtplib
│   ├── discord_tool.py        # Discord webhook notifications
│   └── file_dispatcher.py     # Save + serve generated files
├── report_generator/
│   ├── chart_selector.py      # LLM picks chart type
│   ├── chart_builder.py       # Plotly chart generation
│   ├── pdf_builder.py         # ReportLab PDF assembly
│   └── test_report.py         # Test script
├── voice/
│   ├── listener.py            # Mic recording + faster-whisper STT
│   ├── speaker.py             # pyttsx3 + Coqui TTS output
│   └── tone_analyzer.py       # Detect urgent/confused/casual tone
├── memory/
│   ├── short_term.py          # Last 10 turns in RAM
│   ├── long_term.py           # SQLite persistent memory
│   └── audit_logger.py        # Full audit trail logger
├── orchestrator/
│   ├── intent_detector.py     # Classify query intent + route tools
│   ├── graph.py               # LangGraph state graph (main brain)
│   ├── nodes.py               # All graph node functions
│   ├── self_reflection.py     # Answer quality checker
│   └── proactive_monitor.py   # APScheduler anomaly detection
├── utils/
│   ├── whatif_simulator.py    # Scenario simulation + critique
│   ├── data_helpers.py        # Pandas utilities
│   └── sample_docs_generator.py # Auto-generate sample PDFs
├── ui/
│   ├── app.py                 # Main Streamlit application
│   ├── components/
│   │   ├── chat.py            # Chat interface component
│   │   ├── sidebar.py         # System status sidebar
│   │   ├── charts.py          # Chart display component
│   │   ├── audit.py           # Audit trail viewer
│   │   └── alerts.py          # Proactive alerts panel
│   └── styles.css             # Custom styling
├── outputs/                   # Generated PDFs, charts, logs
├── data/
│   ├── documents/             # Uploaded PDFs go here
│   └── nexusagent.db          # SQLite database
├── tests/
│   └── test_e2e.py            # End-to-end test for all 5 scenarios
├── .env.example               # Template for environment variables
├── .env                       # Actual env vars (gitignored)
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── PROGRESS.md                # What each module does
└── README.md                  # Full setup + usage guide
```

---

## Phase 1 — Environment Setup

### 1.1 Create requirements.txt

```
# Core LLM + Orchestration
langchain==0.3.0
langchain-community==0.3.0
langchain-core==0.3.0
langgraph==0.2.0
ollama==0.3.0

# RAG + Embeddings
chromadb==0.5.0
sentence-transformers==3.0.0
pymupdf==1.24.0
unstructured==0.15.0
unstructured[pdf]==0.15.0

# Database
sqlalchemy==2.0.0
duckdb==1.1.0
pandas==2.2.0
faker==30.0.0

# Voice
faster-whisper==1.0.0
sounddevice==0.5.0
soundfile==0.12.0
pyttsx3==2.90
numpy==1.26.0

# Reports + Charts
reportlab==4.2.0
weasyprint==62.0
plotly==5.24.0
matplotlib==3.9.0
kaleido==0.2.1

# UI
streamlit==1.39.0
streamlit-extras==0.4.0

# Actions + Notifications
discord-webhook==1.3.0
requests==2.32.0

# Scheduling + Utils
apscheduler==3.10.0
python-dotenv==1.0.0
python-docx==1.1.0
pypdf==5.0.0
tqdm==4.66.0
loguru==0.7.0
```

### 1.2 Create .env.example

```
# Ollama Settings (required)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
OLLAMA_FALLBACK_MODEL=mistral
EMBED_MODEL=all-MiniLM-L6-v2

# Email Settings (optional - leave blank to disable)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password

# Discord Settings (optional - leave blank to use desktop notifications)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_here

# Database
DB_PATH=data/nexusagent.db

# App Settings
LOG_LEVEL=INFO
ANOMALY_THRESHOLD=0.15
MONITOR_INTERVAL_MINUTES=60
MAX_SQL_RETRIES=3
MAX_REFLECTION_RETRIES=2
TOP_K_RETRIEVAL=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### 1.3 Create .gitignore

```
.env
__pycache__/
*.pyc
*.pyo
.DS_Store
outputs/*.pdf
outputs/*.png
data/nexusagent.db
chroma_db/
*.egg-info/
dist/
build/
.pytest_cache/
venv/
.venv/
```

---

## Phase 2 — Config Module

### config/llm_config.py

Build a module that:
- Connects to Ollama at the URL from .env
- Creates a LangChain OllamaLLM instance with the configured model
- Creates a local SentenceTransformer embedding function using the model from .env
- Has a `health_check()` function that pings Ollama and returns True/False with a status message
- Has a `get_llm()` function that returns the LLM instance, falling back to the fallback model if primary is unavailable
- Has a `get_embedder()` function that returns the embedding model
- Logs all model loading events using loguru

### config/settings.py

Build a settings module that:
- Loads all values from .env using python-dotenv
- Exposes them as typed constants (not raw strings)
- Has sensible defaults for every optional setting
- Has a `validate_config()` function that checks required settings are present and warns about missing optional ones

### config/setup_guide.md

Write a clear, beginner-friendly guide explaining:
- How to download and install Ollama from ollama.ai
- Exact terminal commands to pull each model:
  ```
  ollama pull llama3.1
  ollama pull mistral
  ollama pull qwen2.5
  ollama pull nomic-embed-text
  ```
- How to verify Ollama is running: `ollama list`
- How to get a Gmail App Password (step by step with screenshots description)
- How to create a Discord webhook (step by step)
- How to run the app after setup

---

## Phase 3 — RAG Engine

### rag/ingestion.py

Build a document ingestion module that:
- Accepts file paths for PDF, TXT, DOCX formats
- For PDFs: uses PyMuPDF to extract text page by page, preserving page numbers
- For DOCX: uses python-docx
- For TXT: plain read with encoding detection
- Splits text into chunks of CHUNK_SIZE tokens with CHUNK_OVERLAP overlap using LangChain RecursiveCharacterTextSplitter
- Attaches metadata to each chunk: source filename, page number, chunk index, file type
- Returns a list of LangChain Document objects
- Handles corrupt/unreadable files gracefully with error logging

### rag/embedder.py

Build an embedding module that:
- Uses SentenceTransformer with all-MiniLM-L6-v2 model loaded locally
- Has an `embed_documents(docs)` function for batch embedding
- Has an `embed_query(query)` function for single query embedding
- Caches the model in memory after first load
- Returns numpy arrays

### rag/vector_store.py

Build a ChromaDB vector store module that:
- Creates/loads a persistent ChromaDB collection at `chroma_db/` folder
- Has `add_documents(docs, embeddings)` function
- Has `search(query_embedding, top_k)` function returning results with distances
- Has `delete_collection()` function for resetting
- Has `get_collection_stats()` function returning document count and collection name
- Handles duplicate documents by checking filename before adding

### rag/retriever.py

Build the retrieval module that:
- Takes a natural language query
- Embeds it using the embedder
- Searches ChromaDB for top K results
- Calculates a confidence score (0-1) from the distance metric
- Uses the local LLM to rerank the top 5 results and pick the most relevant 3
- Returns results as a list of dicts: `{text, source, page, confidence, rank}`
- If confidence of top result is below 0.4, adds a warning: "Low confidence — answer may not be accurate"

### rag/test_rag.py

Create a test script that:
- Generates a sample company policy text file if no real document exists
- Ingests it into ChromaDB
- Runs 3 test queries and prints results with citations
- Prints a summary of what was found

---

## Phase 4 — SQL Agent

### sql_agent/db_setup.py

Create a database setup script that:
- Creates a SQLite database at the path from .env
- Creates these tables with realistic columns:
  - `customers` (id, name, email, region, segment, created_date, lifetime_value)
  - `products` (id, name, category, price, cost, stock_quantity)
  - `orders` (id, customer_id, order_date, status, total_amount, region)
  - `order_items` (id, order_id, product_id, quantity, unit_price)
  - `sales_metrics` (id, date, region, revenue, units_sold, returns, metric_type)
- Populates each table with 200-500 rows of realistic data using Faker
- Includes seasonal patterns in sales data (higher in Dec, lower in Jan)
- Includes a few anomalies (sudden drops) for the proactive monitor to detect
- Prints a summary of what was created

### sql_agent/schema_reader.py

Build a schema reader that:
- Connects to the SQLite database
- Reads all table names, column names, data types, and foreign key relationships
- Formats the schema as a clear string that an LLM can understand
- Includes sample rows (first 3 rows) from each table to help the LLM understand data format
- Returns the formatted schema string

### sql_agent/query_generator.py

Build the NL-to-SQL generator that:
- Takes a natural language question + schema string
- Constructs a prompt asking the local LLM to write a SQL query
- Extracts only the SQL from the LLM response (strips markdown, explanations etc.)
- Validates the SQL is syntactically plausible before returning
- Detects query intent type: aggregation, trend, comparison, lookup, or mixed
- Returns: `{sql, intent_type, confidence}`

### sql_agent/executor.py

Build the SQL executor that:
- Takes a SQL query and executes it against the database
- If execution fails: sends the error message back to LLM with original question asking it to fix the query
- Retries up to MAX_SQL_RETRIES times
- On success: returns result as pandas DataFrame
- Asks the local LLM to write a plain English explanation of the result
- Returns: `{dataframe, explanation, query_used, retries_needed, intent_type}`
- Logs every attempt to audit trail

---

## Phase 5 — Action Tools

### action_tools/email_tool.py

Build an email tool that:
- Takes: recipient email, subject hint, context (what the email is about)
- Uses local LLM to draft a professional email based on context
- Displays the full draft clearly: To, Subject, Body
- Asks for explicit confirmation: "Send this email? (yes/no)"
- If yes: sends via smtplib using Gmail SMTP with TLS
- If no: asks if user wants to edit and regenerates with feedback
- If Gmail credentials not in .env: saves draft to `outputs/email_drafts/` as .txt file and notifies user
- Logs the action to audit trail with approval status

### action_tools/discord_tool.py

Build a Discord notification tool that:
- Takes: message text, severity level (info/warning/critical), optional title
- Formats a rich Discord embed message with color coding (blue=info, yellow=warning, red=critical)
- Sends via Discord webhook URL from .env
- If webhook URL not configured: falls back to desktop notification using plyer library and also prints to console clearly
- Has a `send_alert(title, message, severity)` function
- Has a `send_report_ready(report_path)` function for notifying when PDF is ready
- Logs to audit trail

### action_tools/file_dispatcher.py

Build a file dispatcher that:
- Saves any generated file (PDF, chart, CSV) to `outputs/` with timestamp
- Returns the absolute file path
- Has a `get_recent_outputs(n=5)` function listing recent files
- Has a `cleanup_old_outputs(days=7)` function removing files older than N days

---

## Phase 6 — Report Generator

### report_generator/chart_selector.py

Build a chart type selector that:
- Takes a pandas DataFrame and a description of what the data represents
- Uses the local LLM to decide: bar chart (comparisons), line chart (time trends), pie chart (proportions), scatter (correlations), table only (complex multi-column)
- Returns the chart type as a string with reasoning

### report_generator/chart_builder.py

Build a Plotly chart builder that:
- Takes a DataFrame, chart type string, and title
- Builds the appropriate Plotly figure with clean professional styling
- Uses a consistent color palette
- Saves the chart as a PNG using kaleido
- Also returns the Plotly figure object for embedding in Streamlit
- Handles edge cases: empty data, single row, too many categories (groups small ones into "Other")

### report_generator/pdf_builder.py

Build a PDF report builder using ReportLab that:
- Takes: title, executive_summary (text), dataframe, chart_image_path, key_insights (list of strings)
- Generates a professional PDF with:
  - Cover page: NexusAgent logo text, report title, generated timestamp
  - Executive summary section with the LLM-written summary
  - Data table with alternating row colors, headers, formatted numbers
  - Chart image embedded full-width
  - Key insights section as a bulleted list
  - Footer on every page with page number and timestamp
- Saves to `outputs/reports/` with timestamp filename
- Returns the file path

---

## Phase 7 — Voice Module

### voice/listener.py

Build a voice input module that:
- Records audio from the default microphone using sounddevice
- Default recording duration: 5 seconds (configurable)
- Shows a visual countdown while recording
- Saves to a temporary WAV file
- Transcribes using faster-whisper with the "base" model running locally
- Returns the transcribed text
- Handles errors gracefully: no microphone, too quiet, unclear audio
- Falls back to text input if voice fails with a clear message to user

### voice/speaker.py

Build a voice output module that:
- Primary: uses pyttsx3 for fully offline TTS
- Configures a clear voice, moderate speed (150 wpm)
- Has a `speak(text)` function
- Has a `speak_alert(text)` function that speaks with higher urgency tone
- Truncates very long responses to first 3 sentences for speaking, reads the rest as text
- Has a `is_available()` check

### voice/tone_analyzer.py

Build a tone analyzer that:
- Takes transcribed text
- Uses local LLM to classify the tone: urgent, confused, frustrated, casual, formal, curious
- Returns: `{tone, confidence, suggested_response_style}`
- The response style guides how the orchestrator should phrase its answer (brief for urgent, detailed for confused etc.)

---

## Phase 8 — Memory System

### memory/short_term.py

Build a short-term memory class that:
- Maintains a deque of last 10 conversation turns
- Each turn stores: role (user/assistant), content, timestamp, tools_used
- Has `add_turn(role, content, tools_used=[])` method
- Has `get_context_string()` method that formats history as a string for LLM prompts
- Has `clear()` method
- Has `get_summary()` method that asks local LLM to summarize the conversation so far

### memory/long_term.py

Build a long-term memory system that:
- Uses SQLite to persist facts across sessions
- Has `store_fact(key, value, category)` method — categories: preference, insight, entity, decision
- Has `recall(query)` method that searches stored facts using simple keyword matching
- Has `get_recent_facts(n=10)` method
- Has `forget(key)` method
- Automatically extracts and stores key facts from conversations using LLM after every 5 turns
- Injects relevant recalled facts into LLM prompts automatically

### memory/audit_logger.py

Build a comprehensive audit trail logger that:
- Uses both a JSON file (`outputs/audit_log.json`) and a SQLite table
- Logs every event with: event_id, timestamp, event_type, tool_name, input_summary, output_summary, duration_ms, human_approved (bool), success (bool), error_message
- Has `log_tool_call(tool, input, output, duration, approved, success, error=None)` method
- Has `get_recent_logs(n=20)` method returning list of dicts
- Has `get_stats()` method returning: total calls, success rate, most used tool, avg duration
- Has `export_csv(path)` method for exporting logs

---

## Phase 9 — LangGraph Orchestrator

### orchestrator/intent_detector.py

Build an intent detector that:
- Takes: user query text, tone metadata from voice analyzer
- Uses local LLM to classify intent into one or more categories:
  - `document_query` — answer from uploaded documents
  - `data_query` — answer from database
  - `hybrid_query` — needs both documents and database
  - `action_request` — send email, notification
  - `report_request` — generate a PDF report
  - `whatif_query` — scenario simulation
  - `chitchat` — general conversation
- Returns: `{primary_intent, secondary_intents, tools_needed, urgency_level}`
- For ambiguous queries, uses the conversation history to resolve

### orchestrator/nodes.py

Build all LangGraph node functions. Each node:
- Takes the full graph state as input
- Does its work using the appropriate module
- Updates and returns the state
- Handles failures without crashing the whole graph

Nodes to build:
- `intent_node` — runs intent detector, sets tools_needed in state
- `rag_node` — runs RAG retrieval, stores results + citations in state
- `sql_node` — runs SQL agent, stores dataframe + explanation in state
- `action_node` — runs action tool with approval flow, stores result in state
- `report_node` — runs report generator, stores PDF path in state
- `whatif_node` — runs what-if simulator, stores simulation result in state
- `chitchat_node` — simple LLM response with memory context
- `reflection_node` — reviews combined answer, flags if incomplete
- `synthesizer_node` — combines all state results into final answer with citations

### orchestrator/graph.py

Build the main LangGraph state graph:

Define the state schema with these fields:
```python
{
  "query": str,
  "tone": dict,
  "intent": dict,
  "rag_results": list,
  "sql_results": dict,
  "action_result": dict,
  "report_path": str,
  "whatif_result": dict,
  "reflection_passed": bool,
  "reflection_attempts": int,
  "final_answer": str,
  "citations": list,
  "tools_used": list,
  "error": str,
  "conversation_history": list
}
```

Build the graph with these edges:
- START → intent_node
- intent_node → (parallel) rag_node, sql_node, action_node, report_node, whatif_node, chitchat_node based on intent
- all tool nodes → synthesizer_node
- synthesizer_node → reflection_node
- reflection_node → synthesizer_node (if not passed and attempts < MAX_REFLECTION_RETRIES)
- reflection_node → END (if passed)

Add conditional edges that activate only the needed tools based on `tools_needed` in state.

### orchestrator/self_reflection.py

Build the self-reflection module that:
- Takes the synthesized answer + original query
- Asks local LLM: "Given the question '{query}', is this answer complete, accurate, and helpful? Reply with PASS or FAIL and a brief reason."
- If FAIL: extracts what is missing and adds it to state for the synthesizer to retry with
- If PASS: sets `reflection_passed = True`
- Maximum MAX_REFLECTION_RETRIES attempts before forcing PASS to avoid infinite loops
- Logs reflection decisions to audit trail

### orchestrator/proactive_monitor.py

Build the proactive monitoring system:
- Uses APScheduler to run a check every MONITOR_INTERVAL_MINUTES
- `check_anomalies()` function:
  - Queries the database for all metrics in `sales_metrics` table
  - Calculates 7-day rolling average for each metric and region
  - Detects if latest value is more than ANOMALY_THRESHOLD (15%) below average
  - For each anomaly found: generates a PDF report, sends Discord/desktop alert, speaks a voice alert
  - Logs to audit trail
- `manual_trigger()` function for testing via UI
- `get_last_check_status()` function for UI status display
- Handles scheduler start/stop gracefully

---

## Phase 10 — What-If Simulator

### utils/whatif_simulator.py

Build the what-if simulator:
- `parse_scenario(query)` — uses local LLM to extract: metric affected, change percentage, secondary effect (e.g. churn rate)
- `run_simulation(scenario)` — pulls current data from DB using pandas, applies the mathematical scenario
- `generate_comparison(before, after)` — creates a Plotly before/after comparison chart
- `critique_simulation(result)` — second LLM call that reviews assumptions and flags potential issues
- Returns: `{scenario_description, before_metrics, after_metrics, net_impact, chart_path, assumptions, critique, confidence}`
- Example queries it should handle:
  - "What if revenue drops 20%?"
  - "What if we increase prices by 10% and lose 15% of customers?"
  - "What if the South region improves by 30%?"

---

## Phase 11 — Sample Documents Generator

### utils/sample_docs_generator.py

Build a sample document generator that runs if no user documents are provided:
- Generates 4 realistic text files and saves to `data/documents/`:
  1. `company_policy.txt` — HR and refund policies, 3 pages of content
  2. `q3_report.txt` — Quarterly business review with metrics and analysis
  3. `product_catalog.txt` — Product descriptions, pricing, categories
  4. `sales_playbook.txt` — Sales process, client handling, escalation procedures
- Each document should be 500-1000 words of realistic business content
- Automatically ingests all 4 into the RAG system after generation
- Prints confirmation of what was created and loaded

---

## Phase 12 — Streamlit UI

### ui/app.py

Build the main Streamlit application:

**Page config:**
- Title: "NexusAgent"
- Layout: wide
- Initial sidebar state: expanded
- Dark theme preferred

**Main layout — 3 columns:**
- Left sidebar (20%): system status, model info, document upload
- Main area (55%): chat interface
- Right panel (25%): charts, reports, alerts

**Chat interface features:**
- Message history displayed with role badges (You / NexusAgent)
- Each assistant message shows tool badges: which tools were used
- Voice record button below text input (toggles recording)
- Clear conversation button
- Loading spinner with status messages while processing ("Searching documents...", "Running query...", etc.)

**Sidebar features:**
- Ollama model status indicator (green/red dot)
- Currently loaded model name
- ChromaDB document count
- Database table count
- Document upload widget (drag and drop)
- Manual anomaly check trigger button

**Right panel tabs:**
- Charts tab: displays latest Plotly chart
- Reports tab: lists generated PDFs with download buttons
- Alerts tab: shows proactive monitor alerts with severity colors
- Audit tab: shows last 20 audit log entries as a table

**What-if tab (separate page):**
- Dedicated input for scenario questions
- Before/after comparison display
- Critique display

**All processing must go through the LangGraph orchestrator — no direct module calls from UI**

### ui/styles.css

Write custom CSS for Streamlit that:
- Gives a clean, professional dark-compatible look
- Styles the tool badges (small colored pills)
- Styles the alert severity indicators
- Makes the chat bubbles visually distinct for user vs assistant

---

## Phase 13 — End-to-End Tests

### tests/test_e2e.py

Build end-to-end tests that verify the complete system works:

```python
# Test 1: Document query
# Ask: "What is the refund policy for enterprise clients?"
# Expected: Answer with source citation from company_policy.txt

# Test 2: Data query  
# Ask: "Which region had the highest sales last month?"
# Expected: Answer with data from database + chart generated

# Test 3: Hybrid query
# Ask: "Our South region sales dropped. What does our sales playbook say to do in this situation?"
# Expected: SQL data about South region + RAG result from sales_playbook.txt

# Test 4: Action request
# Ask: "Draft a follow-up email to a client about their order status"
# Expected: Email drafted, shown for approval, NOT sent (test mode)

# Test 5: What-if scenario
# Ask: "What if our top product's sales dropped 25%?"
# Expected: Simulation result with before/after chart

# Test 6: Proactive monitor
# Manually trigger the anomaly check
# Expected: Check runs, finds planted anomaly in sample data, generates alert
```

Each test should print PASS/FAIL with details.

---

## Phase 14 — Docker Setup

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsndfile1 \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p outputs/reports outputs/email_drafts data/documents chroma_db

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  nexusagent:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./outputs:/app/outputs
      - ./chroma_db:/app/chroma_db
      - ./.env:/app/.env
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
```

---

## Phase 15 — Documentation

### README.md

Write a complete README with these sections:
1. Project banner (ASCII art title + tagline)
2. What is NexusAgent (2 paragraph description)
3. Key features (bullet list with emojis)
4. Architecture diagram (ASCII art showing the flow)
5. Tech stack table
6. Prerequisites (Ollama, Python 3.11+, Git)
7. Installation steps (numbered, copy-paste friendly commands)
8. Configuration (.env setup walkthrough)
9. Running the app (single command)
10. Usage guide (how to use each feature with examples)
11. The 5 demo scenarios with example questions
12. Running tests
13. Docker deployment
14. Project structure explanation
15. Contributing section
16. License (MIT)

### PROGRESS.md

Write a module-by-module explanation of what each file does, which other modules it depends on, and what to do if it fails.

---

## Build Order (Follow Exactly)

Claude Code must build in this order and test each phase before moving to the next:

```
Phase 1  → Environment setup (requirements.txt, .env, .gitignore)
Phase 2  → Config module (llm_config.py, settings.py) → TEST: health_check() returns True
Phase 3  → RAG engine → TEST: ingest sample doc, run 3 queries, get citations
Phase 4  → SQL agent → TEST: create DB, run 5 NL queries, verify self-correction works
Phase 5  → Action tools → TEST: draft email (don't send), trigger Discord/desktop notify
Phase 6  → Report generator → TEST: generate PDF from sample data, verify chart + table
Phase 7  → Voice module → TEST: TTS speaks a test sentence, STT records + transcribes
Phase 8  → Memory system → TEST: store/recall facts, verify audit log writes correctly
Phase 9  → Orchestrator → TEST: send 3 queries, verify correct tools are activated
Phase 10 → What-if simulator → TEST: run 2 scenarios, verify math + critique
Phase 11 → Sample docs → TEST: generate docs, verify RAG ingestion works
Phase 12 → Streamlit UI → TEST: app starts, all tabs load, chat sends a message
Phase 13 → E2E tests → RUN all 6 test scenarios, fix any failures
Phase 14 → Docker → TEST: docker-compose up starts the app
Phase 15 → Documentation → Verify README is complete and accurate
```

---

## Error Handling Standards

Apply these rules everywhere in the codebase:

- Never show raw Python tracebacks to the user — always catch and show friendly messages
- Every external call (Ollama, DB, file I/O) must be in try/except
- Use loguru for all logging — debug level for development, info for production
- If Ollama is down: show "AI model is offline. Please run: ollama serve" and gracefully disable AI features
- If DB is missing: auto-run db_setup.py to recreate it
- If ChromaDB is empty: auto-run sample_docs_generator.py
- All file operations must check if directories exist and create them if not

---

## Final Checklist Before Marking Complete

Claude Code must verify all of these before declaring the build done:

- [ ] `streamlit run ui/app.py` starts without errors
- [ ] All 6 e2e tests pass
- [ ] No hardcoded API keys anywhere in code (all from .env)
- [ ] All secrets in .env.example with placeholder values
- [ ] README.md has complete setup instructions
- [ ] Dockerfile builds successfully
- [ ] docker-compose up works
- [ ] Audit log writes correctly after each action
- [ ] Human-in-the-loop triggers before email send
- [ ] Proactive monitor starts with the app
- [ ] Voice input falls back gracefully if no microphone
- [ ] All outputs save to outputs/ folder
- [ ] .gitignore excludes sensitive files

---

## Success Definition

The build is complete when a non-technical user can:
1. Follow the README setup steps and get the app running
2. Upload a PDF and ask questions about it
3. Ask a business question and get a data-backed answer with a chart
4. Request an email draft and approve/reject it
5. Ask a what-if question and get a simulation with a chart
6. See proactive alerts appear in the alerts panel
7. Download a generated PDF report
8. View the full audit trail of all actions taken

---

*Built with 100% open source tools. Zero API costs. Runs entirely on your machine.*
*NexusAgent — Built to impress, designed to scale.*
