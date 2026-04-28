# Changelog

All notable changes to NexusAgent. Dates are YYYY-MM-DD. Versions follow
[Semantic Versioning](https://semver.org/).

The format is loosely based on [Keep a Changelog](https://keepachangelog.com).

---

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in settings.py (`settings.py`)

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in index-IVqHpmXj.js (`index-IVqHpmXj.js`)

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in Workflows-CO3Czt_R.js (`Workflows-CO3Czt_R.js`)

## [Unreleased] - 2026-04-28

### Added
- [feature] Changes in sw.js (`sw.js`)

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in Dashboard.jsx (`Dashboard.jsx`)

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in preload.js (`preload.js`)

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in main.js (`main.js`)

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in setup.js (`setup.js`)

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in ollama.js (`ollama.js`)

## [Unreleased] - 2026-04-28

### Fixed
- [bugfix] Changes in Pricing.jsx (`Pricing.jsx`)

## [Unreleased]

### Added
- Pricing page (`/pricing`) with Free / Pro / Team tiers, feature comparison,
  and FAQ.
- First-run installer wizard in the Electron desktop app: detects Ollama,
  guides install if missing, pulls the default model with progress, then
  unlocks the main UI.
- Demo-mode build flag (`NEXUS_DEMO=1`) that loads pre-canned data and skips
  auth so a public sandbox can be shipped from the same codebase.

### Changed
- Replaced the auto-generated `CHANGELOG.md` and `PROJECT_DOCUMENTATION.md`
  with hand-curated, human-readable versions.
- Design-token pass across the React frontend (colors, spacing, motion);
  high-traffic pages (Dashboard, Chat, Inbox, Agents, Settings) refreshed.

---

## [2.1.0] — 2026-04-26

Trust, polish, and the router refactor.

### Added
- **Sensitive-conversation lock** — per-chat toggle that forces every LLM
  call in that chat to local Ollama, regardless of the caller's
  `sensitive=` flag.
- **Per-call audit receipts** — every assistant message now ships with the
  provider, model, redaction count, redaction kinds, and SHA-256 of the
  payload that left the machine.
- **Daily briefing ribbon** on the chat welcome screen + auto-generation on
  first dashboard load.
- **Evening digest** ("what got done today") agent — runs at 18:00, surfaces
  a wrap ribbon on the welcome screen after 16:00.

### Changed
- **API server split into 35+ dedicated routers** under `api/routers/`.
  `api/server.py` is now a thin assembly. Easier to find, easier to test,
  no more 5k-line god module.
- Privacy badge on chat now shows a kind-by-kind redaction breakdown.
- Streaming responses surface live privacy stats as they arrive.

### Fixed
- Scheduler timezone — every cron trigger is now pinned to the scheduler's
  `SCHEDULER_TZ` env var. Previously some triggers used the local server tz
  silently.

---

## [2.0.0] — 2026-04-24

Productisation pass. The "v2" label reflects a rewrite from a Streamlit
prototype into a React + FastAPI app, plus the privacy layer that is now the
product's main differentiator.

### Added
- **The agent team** — six named personas with editable display names:
  Atlas (chief of staff), Kira (invoices), Arjun (pipeline), Iris (inbox),
  Sage (meetings), Echo (memory).
- **Morning briefing agent** — Atlas writes a one-page summary of overdue
  tasks, pipeline, and meetings every day at 08:00. Aggregates only.
- **Proactive nudges** — agents raise a hand when they spot something
  actionable; one click to accept, one click to dismiss.
- **Run Now** button per agent + per-card last-run timestamp + history drawer.
- **Voice chat mode** — fullscreen hands-free conversation with VAD-based
  listening (no fixed 5s cap), Whisper STT, browser TTS.
- **Slash commands** — `/remind`, `/task`, `/deal`, `/contact`, `/invoice`,
  `/brief`, `/triage`. Typeahead menu opens on `/`.
- **Smart Inbox** (`/inbox`) — pending approvals + nudges + overdue tasks +
  today's meetings, on one page. Replaces the old Approvals page.
- **Agent run log** (`agents/run_log.py` + `nexus_agent_runs` table) with a
  pause/resume toggle and a history drawer per agent.
- **Privacy layer** (`config/privacy.py`) — kill switch, sensitivity routing,
  PII redaction (email/phone/Aadhaar/PAN/SSN/card/secret/IP/path), audit log
  at `outputs/cloud_audit.jsonl` with SHA-256 fingerprints only.
- **Aggregate-then-cloud reports** — row-level data never leaves the machine;
  only redacted aggregates go to the cloud LLM for narrative writing.
- **Privacy badge** under every assistant message.
- **Onboarding wizard**, empty states across every page, notification prefs,
  keyboard shortcuts modal.
- **Tags + bulk actions** on CRM and Invoices, **recurring tasks**,
  **recurring invoices**, **CSV import wizard**, **workspace export**.
- **Custom agent builder** with templates + per-agent interval picker.
- **Workflow builder upgrades** — `for_each` node, `error_handler` node,
  `trigger_agent` node, AI-suggested workflows.
- **RAG collections** with expiry, **saved queries** + templates,
  **structured research reports**.
- **Integrations framework** + marketplace page + webhook receiver +
  Hindi voice + memo-to-task.
- **Electron desktop wrapper** — tray, global hotkey, Ollama probe, native
  notifications.
- **Self-hosted setup wizard**, CI workflows, release workflows.
- **Rate limiter**, **deep health endpoint**, **DB indexes**, **error
  boundary**, **toast host**, **skeleton loaders**, **PWA manifest**.
- **Playwright e2e suite** covering 10 critical user flows + CI job.
- **Usage metrics** + admin dashboard + public landing page.
- **2FA + session management** — TOTP enrollment, recovery codes,
  per-device session revocation.

### Changed
- Frontend rewritten from Streamlit to **React + Vite + Tailwind +
  React Flow**. All pages now lazy-loaded; main bundle dropped from
  ~850 KB to ~150 KB.
- `langchain_ollama` replaces deprecated `langchain_community` Ollama imports.
- ESLint rules relaxed: stylistic and new-hook rules downgraded to warnings.

### Fixed
- VoiceMode hoist bug.
- `utcnow()` deprecation warnings across the codebase.

---

## [1.0.0] — 2026-04-22

Initial public version. Streamlit-only.

### Added
- Streamlit chat UI with welcome screen + quick actions.
- Conversation persistence (SQLite), CSV/Excel import, database explorer,
  query history, settings page, conversation export (Markdown + PDF).
- LangGraph orchestrator with intent detector, RAG node, SQL node, action
  node, report node, what-if node, multi-agent node, synthesizer.
- ChromaDB-backed RAG with `nomic-embed-text` embeddings.
- NL-to-SQL via local Ollama (`llama3.1:8b-instruct-q4_K_M`).
- Plotly charts + ReportLab PDF reports.
- Discord webhook + email actions with human approval.
- 72 passing pytest tests.

---

## Versioning policy

- **MAJOR** — breaking API changes, schema migrations users must run, or a
  rewrite of a primary surface (frontend stack, agent model).
- **MINOR** — new agent, new page, new integration, new privacy control.
- **PATCH** — bug fixes, copy edits, dependency bumps.

Pre-1.0 versions made no compatibility promises. From 2.0 onwards, schema
changes ship with a migration runner and a documented rollback path.
