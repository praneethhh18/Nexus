# Demo video & sandbox playbook

Tier-0 deliverables for "people can see the product before paying."
This file has two halves:

1. **Video** — a 90-second screen-recording script (shot list + voiceover).
2. **Sandbox** — how to deploy a public hosted instance from this codebase
   in under an hour using the new `NEXUS_DEMO` flag.

---

## Part 1 — 90-second demo video

Goal: a viewer who has never seen the product understands what it does and
why the privacy story is different — in 90 seconds. No music, no chrome,
no narrator face. Screen + voiceover. Aspect 16:9, 1080p, MP4.

### Equipment

- **Recorder:** OBS (free) or ScreenStudio (Mac, paid, smoother cursor).
- **Mic:** anything decent. Phone earbuds are fine if the room is quiet.
- **Cursor:** enable "highlight cursor" in your recorder. Default cursor
  movement reads as panic.
- **Window:** 1380×860 (default Electron size). Hides the OS taskbar
  cleanly for both Windows and Mac.

### Pre-flight (run these once before recording)

1. `NEXUS_DEMO=1 uvicorn api.server:app --port 8000`
2. `cd frontend && npm run dev`
3. Log in as `demo@nexusagent.app` / `Try-Nexus-2026!`.
4. Click **Load sample data** if the dashboard is empty.
5. Make sure Atlas has run today's briefing (Agents → Atlas → Run Now).
6. Make sure there's at least 1 overdue invoice and 2 pending approvals
   in the inbox.

### Shot list (90 s = 9 shots × ~10 s)

| # | Duration | What's on screen | What you say |
|---|---|---|---|
| 1 | 0:00–0:08 | Empty dashboard with the "Welcome, Praneeth" ribbon and 6 agent tiles. | "NexusAgent is a private AI business OS. Six named agents do the work, and your data never leaves your machine." |
| 2 | 0:08–0:18 | Click "View today's briefing" — Atlas's morning brief opens with 3 KPIs and a 4-line narrative. | "Atlas writes a one-page morning brief every day. Tasks, pipeline, overdue items — one place." |
| 3 | 0:18–0:30 | Open Inbox. Hover over a Kira nudge "2 invoices overdue — draft reminders?" Click "Approve all". | "Kira chases your invoices. She drafts the reminder, you approve it, then it sends. Nothing goes out without you." |
| 4 | 0:30–0:42 | Open Chat. Type "Show me revenue by month for Q1." Cursor pause. Send. The bot streams a SQL chart + 2-line interpretation. | "Ask anything in plain English. The SQL runs locally. The chart is local. Only the final aggregate prose comes from the cloud." |
| 5 | 0:42–0:52 | Below the chat reply, hover over the privacy badge. The popover shows "Cloud · 3 values redacted · phone, email, customer name." | "Every reply tells you exactly what was redacted before anything left the machine." |
| 6 | 0:52–1:04 | Click Workflows in the sidebar. Open the "Daily sales report" template. Hover the nodes once: Schedule → SQL → Summarize → PDF → Email draft. | "When you find something repetitive, drop it into a workflow. Twenty-plus node types, ten templates to start from." |
| 7 | 1:04–1:14 | Settings → Security. Show the Cloud Privacy panel: provider, model, redaction count, SHA-256 fingerprint, audit log preview. | "Every cloud call is logged. Provider, model, fingerprint. Proof, not promises." |
| 8 | 1:14–1:24 | Open Plan & Billing. The Free / Pro / Business / Self-hosted cards. Pause on Pro. | "Free for one person, ₹3,999 a month for a five-person team, or buy the self-hosted licence outright." |
| 9 | 1:24–1:30 | Cut to the landing page. CTA "Start free" highlighted. | "Start free. Five-minute install. Your data stays yours. Link below." |

### Voiceover tips

- **Read once before recording** to avoid the "ums."
- **Speak slightly slower** than feels natural. People half-watch demo
  videos; clarity beats density.
- **Don't apologise** ("a little app I'm working on"). It's a product.

### Edit pass (target: 30 minutes)

1. Trim hesitations.
2. Add a 0.3s zoom-in on each privacy badge moment (shots 5 and 7).
3. Title card at start (3 s, just "NexusAgent" in the brand wordmark).
4. End card at 1:30 (URL + email).
5. **Captions** — auto-generate via your editor or `whisper`, then proof.
   Half of LinkedIn watches with sound off.

Export H.264, 1080p, ~10 Mbps. Aim for a final file under 25 MB so it
embeds cleanly on the landing page.

### Where it goes

- Above the fold on `landing/`, autoplay muted with a play button overlay.
- Pinned post on LinkedIn.
- Email signature.
- Top of the GitHub README (replace the ASCII art).

---

## Part 2 — Public hosted sandbox

The product is local-first, so a "sandbox" is technically a contradiction.
Solve it with: **one VM running the whole stack with seed data, public
read+write, reset every 6 hours.**

### What the sandbox shows

- All 25 pages, populated with realistic-looking sample data.
- Agents that actually run on schedule (Atlas every morning, Kira every
  4 hours, etc.) — visitors see live agent runs, not stale screenshots.
- The privacy badge and audit log work exactly the same as a private
  install — because the redaction layer doesn't care that the data is
  fake.

### What the sandbox does NOT show

- **No real cloud LLM calls.** Set `ALLOW_CLOUD_LLM=false` so visitor
  prompts can't burn through your API budget. Replies will use local
  Ollama, which is fine for a 60-second poke.
- **No outbound email / Discord** — `EMAIL_ENABLED=false`,
  `DISCORD_WEBHOOK_URL=""`. The "approve" button on a draft puts the draft
  in `outputs/email_drafts/` instead of sending.

### Setup (60 minutes the first time)

1. **Spin up a VM.** A 4-vCPU / 16 GB / 50 GB Linode or Hetzner is enough
   (~$30/mo). Enough RAM to run llama3.1:8b without thrashing.
2. **Install Ollama** + pull the two required models.
3. **Clone the repo**, `cd NexusAgent`, copy `.env.example` to `.env`.
4. **Edit `.env`:**
   ```bash
   NEXUS_DEMO=1
   DEMO_USERNAME=demo@nexusagent.app
   DEMO_PASSWORD=Try-Nexus-2026!
   ALLOW_CLOUD_LLM=false
   REDACT_PII=true
   AUDIT_CLOUD_CALLS=true
   EMAIL_ENABLED=false
   DISCORD_WEBHOOK_URL=
   SCHEDULER_TZ=Asia/Kolkata
   ```
5. **`docker compose up -d`** — the existing `Dockerfile` and
   `docker-compose.yml` cover it.
6. **First-boot seed** — log in as the demo user, click "Load sample data."
   When `NEXUS_DEMO=1` the onboarding wizard auto-skips so the visitor
   lands on a populated dashboard.
7. **Cron the reset** — at 00:00, 06:00, 12:00, 18:00 IST run:
   ```bash
   docker compose exec api rm -f /app/data/nexusagent.db
   docker compose restart api
   ```
   Sample data re-seeds on next login. Six-hour windows mean a visitor
   never sees someone else's "we tried to break it" mess.
8. **Reverse-proxy with TLS** — `deploy/nginx.conf` + Let's Encrypt.
   Point `demo.nexusagent.app` at the VM.
9. **Login screen banner** — the frontend already reads
   `health.demo === true`; add a yellow ribbon at the top of `Login.jsx`
   that says "Sandbox · use demo@nexusagent.app / Try-Nexus-2026!" so
   visitors can sign in without thinking.

### Read-only-ish guard rails

The point of the sandbox is for someone to *try* the product. Don't make
it read-only — visitors can click "approve a draft" and "create a task,"
and that's the magic moment. Reset every 6 hours covers cleanup.

The two things that **must** stay real-only:
- `EMAIL_ENABLED=false` — protects you from spam loops.
- `DISCORD_WEBHOOK_URL=""` — same.

### Monitoring

- `outputs/cloud_audit.jsonl` should stay empty (because cloud is off).
  If it grows, your kill switch broke. Alert on size > 0.
- VM disk — sample data + ChromaDB grow ~50 MB/day. Reset at 6h keeps
  this bounded.
- `/api/health` — wire to UptimeRobot (free tier) so you know within
  5 minutes if the demo dies.

---

## Done checklist

- [ ] Video shot, edited, captioned, exported.
- [ ] Video embedded on landing page above the fold.
- [ ] Sandbox VM provisioned, `NEXUS_DEMO=1`, sample data loaded.
- [ ] Login screen shows the demo banner when `NEXUS_DEMO=1`.
- [ ] Cron reset job tested.
- [ ] Audit log monitored for accidental cloud calls.
- [ ] `demo.nexusagent.app` linked from landing CTA "Try without
      installing."
