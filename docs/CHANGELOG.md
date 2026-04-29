# Changelog

All notable changes to NexusAgent. Dates are YYYY-MM-DD. Versions follow
[Semantic Versioning](https://semver.org/).

The format is loosely based on [Keep a Changelog](https://keepachangelog.com).

> **Note for maintainers:** disable the **DocTo** VS Code extension for this
> workspace, otherwise it auto-prepends bot-generated entries to this file
> on every save.

---

## [Unreleased]

### Added — AI lead-to-revenue pipeline (incremental)
- **Detail pages** for contacts, companies, deals, invoices. Click any row
  in the CRM or Invoices list and you land on its full profile page —
  edit-in-place, related entities cross-linked, action rail (send email,
  log call, create task, draft invoice).
- **Public lead-capture endpoint** (`POST /api/public/leads`) — workspace
  intake keys + a 5-line embed snippet for any website. Auto-deduplicates
  on email and rate-limits per IP.
- **CRM Leads tab** — first tab on the CRM. Stats band, source breakdown
  bar chart, recent inbound list, intake-key management, future-channel
  roadmap tiles.
- **AI-drafted outreach** on every contact — three personalised email
  variants (warm / professional / direct) per click, editable inline,
  copy or open in mail client.
- **AI lead scoring** — Settings → Ideal Customer Profile. Inbound leads
  auto-score against the ICP; CRM Leads tab + Contact detail show
  colored score badges with the model's reasoning.
- **Capture-from-email** — paste a forwarded email into the CRM Leads tab,
  AI extracts sender + summary, creates a scored contact.
- **BANT extraction** — paste a prospect's reply, AI pulls Budget /
  Authority / Need / Timing signals + suggests a stage advance with a
  one-click "advance deal" action.
- **Conversation-stitch timeline** on contact detail — interactions,
  deals, invoices unified in one chronological feed.
- **Today's focus** strip on Dashboard — pending approvals + today's
  tasks + overdue invoices, surfaces only the tiles with non-zero counts.
  Clean-desk state when there's nothing pending.

### Added — operational
- **Disaster-recovery backup** (`POST /api/admin/backup`) — VACUUM-INTO
  SQLite snapshot + ChromaDB folder + manifest, streamed as a zip.
  Settings panel shows estimated size before the download.
- **Schema migration runner** (`db/migrate.py`) — versioned SQL files in
  `db/migrations/`, idempotent on every boot, ledger with SHA tracking.
- **Multi-tenant isolation contract** — 28 contract tests across every
  single-resource path; surfaced + fixed three real production bugs
  (custom_agents / saved_queries / rag_collections returning 500 on
  missing rows instead of 404).
- **Persona ↔ scheduler ↔ UI** wiring contract — five tests fail loudly
  if a persona is declared but not scheduled, scheduled but not listed,
  or any of the three sources drifts apart.

### Added — UX
- **Pricing page** (`/pricing`) with Free / Pro / Business / Self-hosted
  tiers, current-plan badge, FAQ.
- **First-run installer wizard** in the Electron desktop app — detects
  Ollama, guides install if missing, pulls models with progress.
- **Mobile responsiveness** — Inbox row buttons wrap on phones, stat
  grids stack 2-up, tap-target floor for icon buttons.
- **History page** fleshed out — 5 KPI band, search + intent + date
  filters, starred-only toggle, inline confirm-delete.
- **Reports** progress UI — four visible stages, hard 120s timeout,
  one-click sample queries.
- **Tasks UI redesign** — round done-toggle on the left (status), square
  bulk-select hidden until hover or bulk mode (selection). Linear-style.
- **Workflows how-to guide** — dismissible panel explaining triggers /
  conditions / actions with a worked example.
- **CRM list rows are click-through** — open contact / company / deal /
  invoice with one click; action buttons stop event propagation.
- **AuditLog page** — privacy-first showpiece. Tabs (actions / cloud
  calls), redaction-kind breakdown, opt-in fingerprint reveal, honest
  empty states (kill-switch-off shows the *good* empty).

### Changed
- **Tenant-scoped What-If** — reads from `nexus_invoices` for the workspace
  when present (was always demo data); falls back to bundled samples
  with an honest disclosure when there are no real invoices yet.
- **Service worker** is real — precaches the shell, network-first for
  navigation with offline fallback to `/index.html`, cache-first for
  Vite content-hashed assets. Installed PWAs survive offline reload.
- **Sidebar** collapses cleanly when content overflows (developer mode
  no longer pushes items off-screen). Sticky group label.
- **Analytics** moved into Dashboard as a tab; sidebar entry removed.
- **Silent agent failures surfaced** — every `except: pass` in `agents/`
  replaced with logged warnings (operational) or debug (intentional
  fallback). Failures now show up in `nexus_agent_runs`.

### Privacy invariants (still non-negotiable)
- Every prompt that touches customer data passes `sensitive=True` →
  forced local Ollama. New paths (lead scoring, outreach drafting,
  email-paste extraction, BANT) all comply. Tests assert this.
- Public lead-capture endpoint stores key SHA only, never the raw key.
- Cross-tenant access continues to 404 across every router. Verified
  by `test_multitenant_isolation` (28 cases) and per-feature tests.

### Tests
- Backend suite: **323 passed, 1 skipped** (was 72 at v2.0 start).
- New suites this cycle: `test_multitenant_isolation`, `test_migrate`,
  `test_persona_schedule_contract`, `test_backup_export`,
  `test_public_lead_intake`, `test_lead_scoring`, `test_email_paste`,
  `test_crm_drafts`, `test_bant`, `test_whatif_tenant_scope`.
- Frontend lint: 0 errors. Vite build clean.
- Playwright e2e: 27 critical flows.

---

## [2.1.0] — 2026-04-26

Trust, polish, and the router refactor.

### Added
- **Sensitive-conversation lock** — per-chat toggle that forces every LLM
  call in that chat to local Ollama, regardless of the caller's
  `sensitive=` flag.
- **Per-call audit receipts** — every assistant message ships with the
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
  Sage (meetings), Echo (memory). A seventh, Nyx (evening digest), was
  added later in this version line.
- **Morning briefing agent** — Atlas writes a one-page summary of overdue
  tasks, pipeline, and meetings every day at 08:00. Aggregates only.
- **Proactive nudges** — agents raise a hand when they spot something
  actionable; one click to accept, one click to dismiss.
- **Run Now** button per agent + per-card last-run timestamp + history drawer.
- **Voice chat mode** — fullscreen hands-free conversation with VAD-based
  listening (no fixed 5s cap), Whisper STT, browser TTS.
- **Slash commands** — `/remind`, `/task`, `/deal`, `/contact`, `/invoice`,
  `/brief`, `/triage`, `/whatif`. Typeahead menu opens on `/`.
- **Smart Inbox** (`/inbox`) — pending approvals + nudges + overdue tasks +
  today's meetings, on one page.
- **Privacy layer** (`config/privacy.py`) — kill switch, sensitivity routing,
  PII redaction (email/phone/Aadhaar/PAN/SSN/card/secret/IP/path), audit log
  at `outputs/cloud_audit.jsonl` with SHA-256 fingerprints only.
- **Aggregate-then-cloud reports** — row-level data never leaves the machine;
  only redacted aggregates go to the cloud LLM for narrative writing.
- **Onboarding wizard**, empty states across every page, notification prefs,
  keyboard shortcuts modal.
- **Tags + bulk actions** on CRM and Invoices, recurring tasks, recurring
  invoices, CSV import wizard, workspace export.
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
- **Rate limiter**, deep health endpoint, DB indexes, error boundary,
  toast host, skeleton loaders, PWA manifest.
- **Playwright e2e suite** covering 10 critical user flows + CI job.
- **Usage metrics** + admin dashboard + public landing page.
- **2FA + session management** — TOTP enrollment, recovery codes,
  per-device session revocation.

### Changed
- Frontend rewritten from Streamlit to **React + Vite + Tailwind +
  React Flow**. All pages now lazy-loaded; main bundle dropped from
  ~850 KB to ~150 KB.
- `langchain_ollama` replaces deprecated `langchain_community` Ollama imports.

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
