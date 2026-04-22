```
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗ █████╗  ██████╗ ███████╗███╗   ██╗████████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
```

**Voice-first multi-agent AI that reads your documents, queries your data, takes actions,
and monitors your business — all running locally for free.**

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-50%20passed-brightgreen)

---

## What is NexusAgent?

NexusAgent is a production-grade, voice-enabled AI business assistant that runs entirely
on your local machine. It combines a large language model (via Ollama), a vector database
(ChromaDB), a SQL agent, and a multi-agent orchestrator (LangGraph) into a single,
cohesive system accessible through a beautiful Streamlit interface.

Unlike cloud AI tools, NexusAgent keeps all your data local, runs at zero cost after
setup, and gives you full transparency into every action it takes through a complete audit
trail. It learns from your conversations, proactively monitors your business for anomalies,
and can take real actions like sending emails — always with your explicit approval first.

---

## Key Features

- **Document Q&A** — Upload PDFs and ask questions; get answers with exact citations
- **Natural Language SQL** — Ask business questions in plain English; get data + charts
- **Human-in-the-Loop Actions** — Drafts emails, shows you first, sends only with your approval
- **PDF Report Generation** — Generates professional reports with charts automatically
- **Proactive Anomaly Detection** — Monitors your data in background, alerts without being asked
- **What-If Simulator** — Models business scenarios with before/after comparison charts
- **Self-Reflection Loop** — Agent reviews its own answers before showing them to you
- **Voice Input/Output** — Speak your queries; hear responses (fully offline)
- **Tone Detection** — Adapts response style based on detected urgency/tone
- **Long-Term Memory** — Remembers facts and preferences across sessions
- **Full Audit Trail** — Every action logged with timestamps, inputs, outputs
- **Zero API Cost** — 100% local, 100% open source, $0 after setup

---

## Architecture

```
User Input (text/voice)
        │
        ▼
┌─────────────────────┐
│  Tone Analyzer      │ ← Local LLM classifies urgency/tone
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Intent Detector    │ ← LLM classifies: RAG/SQL/Action/Report/WhatIf
└──────────┬──────────┘
           │
    ┌──────┼──────┬──────────┬────────────┐
    ▼      ▼      ▼          ▼            ▼
 [RAG]  [SQL]  [Action]  [Report]   [WhatIf]
  │       │      │           │           │
  └───────┴──────┴───────────┴───────────┘
                    │
                    ▼
         ┌─────────────────┐
         │  Synthesizer    │ ← Combines all results
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Self-Reflection │ ← Checks answer quality
         └────────┬────────┘
                  │
                  ▼
            Final Answer
         (+ citations, charts, PDFs)
```

---

## Tech Stack

| Component | Tool | Why |
|---|---|---|
| LLM | Ollama + llama3.1:8b | Local, free, powerful |
| Embeddings | Ollama nomic-embed-text | Local, no API needed |
| Vector DB | ChromaDB | Local, persistent |
| Orchestrator | LangGraph | Production-grade agent graph |
| PDF parsing | PyMuPDF | Best open source parser |
| Database | SQLite | Local, zero config |
| Voice input | faster-whisper | Local Whisper STT |
| Voice output | pyttsx3 | Fully offline TTS |
| UI | Streamlit | Fast, free |
| Charts | Plotly | Beautiful, interactive |
| PDF reports | ReportLab | Professional PDF output |
| Scheduling | APScheduler | Background job runner |

---

## Prerequisites

- **Python 3.11+** — [python.org](https://python.org)
- **Ollama** — [ollama.ai](https://ollama.ai) (see setup guide below)
- **Git** — [git-scm.com](https://git-scm.com)
- 8GB+ RAM recommended (for 8B parameter model)

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-org/nexusagent.git
cd nexusagent

# 2. Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull Ollama models (Ollama must be installed first)
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull nomic-embed-text

# 5. Configure environment
cp .env.example .env
# Edit .env with your settings (Ollama URL is pre-configured)
```

---

## Configuration

Edit `.env` — minimum required:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M
EMBED_MODEL=nomic-embed-text:latest
```

Optional (for email sending):
```bash
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
```

See `config/setup_guide.md` for step-by-step Gmail App Password instructions.

---

## Running the App

```bash
streamlit run ui/app.py
```

Opens at **http://localhost:8501**

On first launch:
- SQLite database is auto-created with MNC sample data
- 4 sample business documents are auto-generated and loaded into RAG
- Proactive monitoring starts automatically in background

---

## Usage Guide

### Document Q&A
Upload PDFs or use auto-generated sample docs. Ask:
> "What is the refund policy for enterprise clients?"
> "Summarize the Q3 report"

### Data Queries
> "Which region had the highest revenue last month?"
> "Show me the top 5 products by sales"
> "What's the average order value by customer segment?"

### Email Drafts
> "Draft a follow-up email to a client about their order status"
NexusAgent drafts it, shows you, and only sends after you approve.

### Business Reports
> "Generate a regional sales report for Q3"
PDF report auto-generated with charts, table, and executive summary.

### What-If Scenarios
Use the What-If Simulator tab:
> "What if revenue drops 20%?"
> "What if we increase prices 10% and lose 15% of customers?"

### Voice Input
Click the 🎙️ button and speak your question. NexusAgent transcribes it locally using Whisper.

---

## The 5 Demo Scenarios

```
1. Document Q&A:
   "What is the refund policy for enterprise clients?"
   → Answer with citation from company_policy.txt

2. Data query:
   "Which region had the highest sales last month?"
   → SQL result + Plotly chart

3. Hybrid:
   "Our South region sales dropped. What does the sales playbook say?"
   → SQL data about South + RAG from sales_playbook.txt

4. Action:
   "Draft a follow-up email about order status"
   → Email shown for approval, saved to draft (not sent)

5. What-If:
   "What if our top product's sales dropped 25%?"
   → Before/after chart + CFO critique
```

---

## Running Tests

```bash
python tests/test_e2e.py
```

All 6 scenarios tested automatically. PASS/FAIL reported for each.

---

## Docker Deployment

```bash
# Make sure Ollama is running on your host machine
ollama serve

# Build and run NexusAgent in Docker
docker-compose up --build
```

Access at **http://localhost:8501**

---

## Project Structure

```
nexusagent/
├── config/         LLM connection, settings, setup guide
├── rag/            PDF ingestion, embeddings, ChromaDB, retrieval
├── sql_agent/      NL-to-SQL, schema reader, self-correcting executor
├── action_tools/   Email, Discord/desktop notifications, file dispatcher
├── report_generator/ Chart selection, Plotly builder, ReportLab PDF
├── voice/          Whisper STT, pyttsx3 TTS, tone analyzer
├── memory/         Short-term (RAM), long-term (SQLite), audit logger
├── orchestrator/   LangGraph graph, all node functions, self-reflection
├── utils/          What-if simulator, data helpers, sample doc generator
├── ui/             Streamlit app + component modules
├── tests/          End-to-end test suite
├── data/           SQLite database + uploaded documents
├── outputs/        Generated PDFs, charts, email drafts
└── chroma_db/      ChromaDB vector store
```

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please ensure all tests pass before submitting a PR.

---

## License

MIT License — free to use, modify, and distribute.

---

*NexusAgent — Built to impress, designed to scale. 100% open source. Zero API costs.*
