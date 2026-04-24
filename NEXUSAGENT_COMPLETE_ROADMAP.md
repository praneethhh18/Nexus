# NexusAgent — Complete Product Roadmap
# Everything needed to go from current state → fully shippable product
# Solo developer · India-first · All platforms · Build first, deploy later

---

## CURRENT STATE SUMMARY
Already built: Core AI engine, 6 agents, LangGraph orchestrator, RAG, SQL agent,
4-layer privacy, JWT auth, multi-tenancy, 23 React pages, 66 tests, voice mode,
workflow builder, CRM, invoices, tasks, documents, analytics, audit trail.
~29,000 lines of code.

---

## WHAT IS STILL MISSING — COMPLETE LIST

---

# BLOCK 1 — CORE PRODUCT COMPLETENESS
# These are gaps in the existing product that will frustrate real users

## 1.1 Onboarding Flow (most important thing missing)
- Welcome screen after first signup with progress steps
- Step 1: Business profile setup (name, industry, size, timezone, currency)
- Step 2: Choose your stack — which agents to enable first
- Step 3: Connect your first data source (upload CSV or connect email)
- Step 4: Upload first document to RAG
- Step 5: Run first agent manually and see output
- Step 6: "Your workspace is ready" celebration screen
- Skip option on every step
- Progress saved — if user closes halfway, resumes where they left off
- Onboarding checklist widget on dashboard until all steps complete
- First-time empty states on every page (not blank — explain what goes here)

## 1.2 Empty States for All 23 Pages
Every page currently shows nothing when there's no data.
Replace with illustrated empty states that explain what the page does and have a CTA:
- Dashboard: "No briefing yet — run Atlas to generate your first morning briefing"
- CRM: "No contacts yet — add your first lead or import a CSV"
- Tasks: "No tasks — create one or ask the AI to generate tasks from a document"
- Invoices: "No invoices — create your first invoice in 30 seconds"
- Documents: "No documents — upload a PDF and start asking questions"
- Inbox: "You're all caught up — nothing needs your attention right now"
- Analytics: "No data yet — import a CSV or connect a data source"
- (same pattern for all remaining pages)

## 1.3 Notification System
- In-app notification bell with unread count badge
- Notification types: agent completed run, approval waiting, anomaly detected,
  invoice overdue, meeting in 30 min, document processed, workflow completed
- Mark as read / mark all read / delete
- Notification preferences page — toggle which events trigger notifications
- Browser push notifications (Web Push API) — works even when tab is not active
- Email digest — daily summary email of what the agents did (opt-in)
- Mobile push notifications (when mobile app is built)

## 1.4 Search — Global Command Palette
- Cmd+K / Ctrl+K opens a search overlay from anywhere in the app
- Searches across: contacts, tasks, invoices, documents, conversations, agents
- Shows results grouped by type with icons
- Recent searches stored locally
- Slash commands available from palette too (/task, /deal, /invoice)
- Keyboard navigation through results (arrow keys + Enter)

## 1.5 Keyboard Shortcuts
- Cmd+K — command palette
- Cmd+/ — focus chat input
- Cmd+N — new item (context-aware: on CRM = new contact, on Tasks = new task)
- Cmd+B — toggle sidebar
- Cmd+S — save current form
- Cmd+Enter — submit/send
- ? — show keyboard shortcut reference modal
- Esc — close any modal/drawer

## 1.6 Data Import / Export (complete)
- CSV import for: contacts, tasks, invoices, products
- Excel (.xlsx) import for same
- Column mapping UI — drag CSV columns to match system fields
- Import preview — show first 5 rows before confirming
- Import history — see past imports, re-run, or undo
- Full data export — every table as CSV in a ZIP file
- GDPR-style "export all my data" button in settings
- Scheduled exports — auto-export weekly to a folder

## 1.7 Bulk Actions
- Select multiple items on any list page
- Bulk delete, bulk tag, bulk assign, bulk status change
- Bulk email — select 10 contacts, draft one email, send to all (with approval)
- Undo bulk actions within 5 seconds (toast with undo button)

## 1.8 Activity Feed
- Per-record activity timeline on every CRM contact, deal, invoice
- Shows: who did what, when, what the AI agent suggested, what was approved
- Filterable by action type
- Global activity feed page showing everything across the workspace

## 1.9 Tags and Filters (everywhere)
- Add custom tags to any record (contacts, tasks, invoices, documents)
- Filter any list by tag, date range, status, assigned user, agent
- Save filter presets ("Overdue invoices in South region")
- URL reflects current filters so you can share a filtered view

## 1.10 Recurring Items
- Recurring tasks (daily, weekly, monthly, custom)
- Recurring invoices (subscription clients)
- Recurring reminders
- Skip once / pause / stop options

---

# BLOCK 2 — AI & AGENT UPGRADES

## 2.1 Custom Agent Builder (no-code)
- Visual form to create a new agent:
  - Name, emoji, description
  - Trigger: schedule (cron picker) or event-based (new contact, invoice overdue etc.)
  - Goal: what should this agent do in plain English
  - Tools available: which of the 51 tools can it use
  - Output: where does it post results (inbox, dashboard widget, email)
- Preview mode — run once and show what it would do before activating
- Agent templates library — pre-built agents users can clone:
  - "Social media monitor" — checks mentions
  - "Competitor price watcher" — monitors competitor websites
  - "Weekly team digest" — summarizes team activity
  - "Lead scorer" — rates new contacts by potential value
  - "Contract expiry watcher" — flags contracts expiring in 30 days

## 2.2 Agent Interval Override UI
- On each agent card: click schedule to change it
- Visual cron picker (not raw cron syntax)
- "Run every: 15 min / 1 hour / 6 hours / daily / weekly / custom"
- Time of day picker for daily agents
- Timezone-aware scheduling

## 2.3 Multi-Step Workflow Chaining (upgrade existing builder)
- Current workflow builder has templates but limited chaining
- Add: trigger → condition → action → action → action chains
- Conditions: if/else branching ("if invoice > ₹50,000 then escalate, else auto-approve")
- Loops: "for each overdue invoice, draft a reminder"
- Wait steps: "wait 3 days, then check if replied, if not send follow-up"
- Error handling steps: "if email fails, notify on Discord instead"
- Workflow run history with per-step status

## 2.4 Agent Collaboration
- Agents can trigger other agents
- Atlas morning briefing → triggers Sage to prep meetings for the day
- Iris email triage → triggers Arjun if email is about a deal
- Define these chains visually in the workflow builder

## 2.5 AI Suggestions Throughout UI
- On CRM contact page: "Sage suggests: follow up with this contact — last touch was 3 weeks ago"
- On invoice page: "Kira suggests: this client typically pays late — send reminder 5 days early"
- On task page: "Recommend breaking this into 3 subtasks based on similar past tasks"
- On analytics: "Revenue dipped last Tuesday — correlates with the public holiday"
- These are passive nudges — not intrusive, dismissable

## 2.6 RAG Improvements
- Document collections — group documents by topic/project
- Re-ingestion when document is updated
- Document expiry — mark documents as outdated after X days
- Cross-collection search — search across multiple collections at once
- Citation display improvement — show the exact highlighted passage, not just page number
- Confidence threshold setting — user sets minimum confidence for answers

## 2.7 SQL Agent Improvements
- NL→SQL evaluation harness — golden query test suite run on every change
- Query history with saved queries
- Query explanation in plain English shown by default
- Chart auto-generated for every query result (currently optional)
- DuckDB for analytics queries on large CSVs (columnar, fast)
- Query templates — "revenue by month", "top customers", "overdue invoices"

## 2.8 Voice Mode Upgrades
- Wake word detection — say "Hey Nexus" to activate without clicking
- Streaming TTS — speaks response while still generating (not wait-then-speak)
- Conversation mode — back-and-forth without clicking record each time
- Voice command shortcuts — "Hey Nexus, run Atlas" / "Hey Nexus, show my inbox"
- Hindi voice support — Whisper already supports Hindi, add Hindi TTS
- Voice memo — record a note, agent transcribes and creates a task automatically

## 2.9 Research Agent Upgrade
- Multi-source research — searches web + your documents + your database together
- Research reports — structured output with sources, summary, key points
- Scheduled research — "every Monday, research our top 3 competitors and brief me"
- Save research results to knowledge base automatically

---

# BLOCK 3 — INTEGRATIONS

## 3.1 Communication Integrations
- WhatsApp Business API — receive and reply to WhatsApp messages from inbox
- Telegram bot — NexusAgent as a Telegram bot for mobile access
- Gmail full integration — not just SMTP send, full read/label/archive
- Outlook / Microsoft 365 — same as Gmail
- Slack — two-way: receive messages, post agent outputs, approve from Slack
- Google Meet / Zoom — pull meeting transcripts, Sage uses them for prep

## 3.2 Calendar Integrations
- Google Calendar — read events for Sage meeting prep, create tasks as calendar events
- Outlook Calendar — same
- Calendly — when a meeting is booked, auto-create contact + deal in CRM

## 3.3 Business Tool Integrations
- Zoho CRM — sync contacts and deals bidirectionally
- Tally / Busy — Indian accounting software, sync invoices
- Razorpay — see payment status on invoices automatically
- Shopify — import orders as sales data for analytics
- WooCommerce — same
- Google Sheets — two-way sync for any data table
- Notion — sync tasks and documents

## 3.4 Integration Architecture
- Integrations marketplace page — browse, connect, configure each integration
- OAuth flow for each integration (not manual API key entry where possible)
- Webhook receiver — accept incoming webhooks from any service
- Zapier / Make (Integromat) connector — so users can connect 5000+ apps
- Per-integration permission control — which agents can access which integrations
- Integration health status — show if connection is working or broken

---

# BLOCK 4 — MOBILE APP (React Native)

## 4.1 Core Mobile Pages
- Login / signup
- Dashboard with KPIs and today's briefing (read-only)
- Inbox — approvals, nudges, alerts (most important mobile page)
- Chat with AI (text + voice)
- Contacts list + detail page
- Tasks list + quick add
- Invoices list + status

## 4.2 Mobile-Specific Features
- Biometric login (Face ID / fingerprint)
- Push notifications for approvals and alerts
- Offline mode for inbox and contacts (read-only when no connection)
- Quick actions from notification: Approve / Reject without opening app
- Home screen widget: today's task count + one-tap to inbox
- Voice memo → auto task creation (speak a task, it appears in your list)
- Business card scanner → auto-create contact (camera + OCR)

## 4.3 Mobile Voice Mode
- Same voice orb from web, optimized for mobile
- Works over Bluetooth headphones
- Background audio — can listen to briefing while commuting

---

# BLOCK 5 — DESKTOP APP (Electron)

## 5.1 Desktop-Specific Features
- System tray icon — NexusAgent runs in background, shows notification count
- Desktop notifications — native OS notifications for approvals and alerts
- Global hotkey — Cmd+Shift+N opens NexusAgent from anywhere on desktop
- Local file system access — drag files directly from Finder/Explorer into documents
- Auto-start on login option
- Offline-first — full functionality without internet (local LLM + local DB)
- Automatic updates — check for new version on launch, one-click update

## 5.2 Ollama Integration (Desktop Only)
- Bundled Ollama installer — first launch detects if Ollama is installed, offers to install
- Model manager — download, delete, switch models from within the app
- Local model status in system tray — green when Ollama running, red when not
- Auto-start Ollama when desktop app launches

---

# BLOCK 6 — BILLING & MONETIZATION
# Build this last — after everything else works

## 6.1 Pricing Tiers
- Free: 1 user, 2 agents, 100 documents, local LLM only
- Pro (₹3,999/mo or $49/mo): 5 users, all agents, 1000 docs, cloud LLM toggle
- Business (₹12,999/mo or $159/mo): 20 users, custom agents, unlimited docs, SSO
- Self-hosted license (₹24,999 one-time or $299): everything, your own server

## 6.2 Payment Integration
- Razorpay for Indian customers (UPI, cards, net banking, EMI)
- Stripe for international customers
- LemonSqueezy as backup (easier tax handling globally)
- Auto-detect user location and show appropriate payment method

## 6.3 Subscription Management
- Upgrade / downgrade plan
- Cancel with offboarding survey
- Pause subscription (keeps data, disables agents)
- Invoice generation for every payment
- Failed payment handling and retry logic
- Grace period (3 days) before account restrictions

## 6.4 Usage Limits & Metering
- Track per-tenant: user count, document count, agent runs, API calls
- Usage dashboard in settings — see current usage vs limits
- Warning at 80% of limit
- Hard block at 100% with upgrade prompt
- Overage option for Business tier (pay per extra unit)

## 6.5 Admin Billing Dashboard (for you)
- MRR, ARR, churn rate, new signups
- Per-customer revenue and plan
- Failed payments list
- Refund processing

---

# BLOCK 7 — SECURITY & COMPLIANCE

## 7.1 Authentication Upgrades
- Google OAuth (Sign in with Google) — most users expect this
- Microsoft OAuth — for enterprise customers
- Magic link login — passwordless email login option
- Session management improvements — auto-logout after inactivity
- Login attempt rate limiting and lockout

## 7.2 Security Features
- IP allowlist — Business tier can restrict access to office IPs
- Audit log improvements — exportable, searchable, filterable by user/action
- Data retention policies — auto-delete data older than X days (configurable)
- Encryption at rest — SQLite database encrypted with SQLCipher
- HTTPS enforced everywhere (when deployed)
- CSP headers, CORS properly configured
- Dependency vulnerability scanning in CI

## 7.3 Compliance
- Privacy policy page (in-app)
- Terms of service page (in-app)
- Cookie consent banner
- GDPR: right to erasure (delete account + all data)
- GDPR: data portability (export all data)
- India DPDP Act compliance (Digital Personal Data Protection Act 2023)

---

# BLOCK 8 — PERFORMANCE & RELIABILITY

## 8.1 Backend Performance
- Database query optimization — add indexes on frequently filtered columns
- LLM response caching — cache identical prompts for 1 hour (already partial)
- Background job queue — Celery or ARQ for heavy tasks (report generation, ingestion)
- Rate limiting on all API endpoints
- Request timeout handling — if LLM takes >30s, return partial result
- Health check endpoint — /health returns DB status, Ollama status, queue status

## 8.2 Frontend Performance
- Code splitting — each page loads only its own JS bundle
- Lazy loading for charts, heavy components
- Skeleton loading states on every page (not spinners)
- Optimistic UI updates — task marked complete immediately, rolled back if server fails
- Service worker for PWA — works offline, installable on phone from browser
- Image optimization pipeline

## 8.3 Error Handling (complete overhaul)
- Global error boundary in React — catches any crash, shows friendly message
- Every API error has a user-readable message (no raw error codes)
- Retry logic on network failures (3 attempts with backoff)
- Toast notifications for success/failure of every action
- Error reporting to Sentry (or self-hosted Glitchtip)
- Automatic error recovery where possible

## 8.4 Testing (expand existing 66 tests)
- Frontend unit tests (Vitest + React Testing Library)
- E2E tests (Playwright) covering the 10 most critical user flows
- Load testing — simulate 100 concurrent users
- LLM output testing — assert that agent outputs match expected format
- Regression test suite — run before every deployment

---

# BLOCK 9 — DEVELOPER EXPERIENCE & DEPLOYMENT

## 9.1 CI/CD Pipeline
- GitHub Actions workflow:
  - On every PR: run all tests, lint, type-check
  - On merge to main: build Docker image, push to registry
  - On tag/release: deploy to production
- Automated versioning (semantic-release)
- Changelog auto-generation from commit messages

## 9.2 Deployment Options
- Docker Compose (already done — complete this)
- One-click deploy to Railway / Render (for managed hosting option)
- Kubernetes Helm chart (for enterprise self-hosted)
- DigitalOcean 1-Click App
- AWS CDK / Terraform scripts for cloud deployment
- Coolify / Dokku support for self-hosted VPS

## 9.3 Self-Hosted Setup Wizard
- Web-based installer (like Notion Calendar setup)
- Detects OS, checks prerequisites
- Installs Ollama automatically if missing
- Pulls recommended model based on available RAM
- Configures .env interactively
- Runs health check and shows green/red for each service
- Generates a startup script

## 9.4 Update System
- Version check on app startup — compare current vs latest GitHub release
- In-app update notification with changelog preview
- One-click update for Docker deployments
- Database migration system (Alembic) — schema changes apply automatically on update

---

# BLOCK 10 — LANDING PAGE & MARKETING SITE

## 10.1 Public Website (separate from the app)
- Hero section: headline, subheadline, animated demo video/GIF
- Problem section: "Your business data is scattered across 7 tools"
- Solution section: show the 6 agents with what they each do
- Privacy section: "Everything runs on your machine" — this is the main differentiator
- Features grid: all key features with icons
- Pricing section: 3 tiers + self-hosted option
- FAQ section
- Testimonials section (add after beta)
- CTA: "Start free" button → signup page

## 10.2 Documentation Site
- Getting started guide (5 minutes to first value)
- Agent reference — what each agent does, how to configure
- Integration guides — step-by-step for each integration
- API reference — for developers building on top
- Self-hosting guide — complete deployment instructions
- Troubleshooting guide — common issues and fixes
- Video tutorials (Loom recordings)

## 10.3 In-App Help
- Contextual help tooltips on complex features
- Help button on every page → links to relevant docs
- Interactive product tour (Shepherd.js or custom)
- AI-powered help chat — "ask anything about NexusAgent"
- Keyboard shortcut reference modal (press ?)

---

# BLOCK 11 — ANALYTICS & GROWTH (for you, the founder)

## 11.1 Product Analytics (self-hosted, privacy-respecting)
- Plausible Analytics or Umami for website traffic
- PostHog (self-hosted) for in-app behavior: which pages visited, features used
- Funnel tracking: signup → onboarding → first agent run → paid
- Feature flags — roll out new features to % of users for testing
- A/B testing framework for onboarding and pricing

## 11.2 Business Metrics Dashboard (internal)
- Daily/weekly/monthly active users
- Agent run counts per agent
- Most used features
- Error rate and P95 response times
- Conversion rate (free → paid)
- Churn rate

---

# BUILD ORDER (follow exactly — each block depends on previous)

Phase 1 (Build first — core completeness):
→ 1.1 Onboarding flow
→ 1.2 Empty states for all pages
→ 1.3 Notification system
→ 1.4 Global search / command palette
→ 1.5 Keyboard shortcuts
→ 1.6 Data import/export complete
→ 1.7 Bulk actions
→ 1.8 Activity feed
→ 1.9 Tags and filters
→ 1.10 Recurring items

Phase 2 (AI upgrades):
→ 2.1 Custom agent builder
→ 2.2 Agent interval override UI
→ 2.3 Multi-step workflow chaining
→ 2.4 Agent collaboration
→ 2.5 AI suggestions throughout UI
→ 2.6 RAG improvements
→ 2.7 SQL agent improvements
→ 2.8 Voice mode upgrades
→ 2.9 Research agent upgrade

Phase 3 (Integrations):
→ 3.1 WhatsApp Business + Gmail full + Slack
→ 3.2 Google Calendar + Outlook
→ 3.3 Zoho CRM + Razorpay + Google Sheets
→ 3.4 Integration marketplace UI + Zapier connector

Phase 4 (Mobile app):
→ 4.1 React Native app — all core pages
→ 4.2 Mobile-specific features
→ 4.3 Mobile voice mode

Phase 5 (Desktop app):
→ 5.1 Electron wrapper with desktop features
→ 5.2 Ollama integration + model manager

Phase 6 (Security & compliance):
→ 7.1 Google OAuth + Microsoft OAuth
→ 7.2 Security hardening
→ 7.3 Privacy policy + ToS + GDPR

Phase 7 (Performance):
→ 8.1 Backend optimization
→ 8.2 Frontend performance
→ 8.3 Error handling overhaul
→ 8.4 Expand test suite

Phase 8 (Deployment):
→ 9.1 CI/CD pipeline
→ 9.2 Docker + one-click deploy options
→ 9.3 Self-hosted setup wizard
→ 9.4 Update system

Phase 9 (Landing page):
→ 10.1 Public website
→ 10.2 Documentation site
→ 10.3 In-app help system

Phase 10 (Billing — last):
→ 6.1-6.5 Complete billing system
→ Razorpay + Stripe integration
→ Usage metering

Phase 11 (Analytics):
→ 11.1 PostHog self-hosted
→ 11.2 Internal metrics dashboard

---

# WHAT TO GIVE CLAUDE CODE

For each phase, paste this as your prompt:

"Read NEXUSAGENT_COMPLETE_ROADMAP.md.
I have completed everything up to [last thing built].
Now build Phase [X] — [phase name].
The existing codebase is at [folder path].
Scan the existing code before writing anything new.
Build everything in Phase [X] completely, test each
feature, and confirm when done before moving on."

---

# HONEST ESTIMATE

Total features remaining: ~180 individual features
Estimated Claude Code sessions: 40-60 sessions
Estimated real calendar time (solo, evenings + weekends): 3-4 months
Result: A product genuinely competitive with Notion AI + Zapier + a CRM

---

# STOP BUILDING WHEN:
→ All 11 phases are complete
→ The self-hosted setup wizard works for a non-technical person
→ The mobile app is on Play Store (beta)
→ 10 real people have used it without your help
→ The landing page is live with a waitlist

That is your definition of "done."
