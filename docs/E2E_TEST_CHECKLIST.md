# NexusAgent — End-to-End Test Checklist

> **Goal:** verify every customer-facing flow works on localhost before
> deploying to AWS. Tick each box as you confirm. Anything that fails →
> note the bug under the section and we fix before deploy.
>
> **Estimated time:** 30 min critical-path smoke, 2-3 hours full test.
>
> **Setup before starting:**
> ```bash
> # Terminal 1 — backend
> cd c:\Users\Praneeth p\OneDrive\Desktop\NexusAgent
> python -m uvicorn api.server:app --port 8000 --reload
>
> # Terminal 2 — frontend
> cd frontend && npm run dev    # http://localhost:5173
>
> # Terminal 3 — landing (optional, only for landing page tests)
> cd landing && npm run dev     # http://localhost:4000
> ```
>
> Tick boxes by changing `- [ ]` to `- [x]` in this file.

---

## 🟢 CRITICAL PATH (Phase 1) — must pass before deploy

### 1. Backend boots cleanly

- [ ] `python -m uvicorn api.server:app --port 8000 --reload` starts with no errors
- [ ] Logs show `[Boot] Sentry initialised (env=development)`
- [ ] Logs show `[Tools] Registered 71 agent tools`
- [ ] Logs show `INFO: Application startup complete`
- [ ] `curl http://localhost:8000/api/health` returns 200 OK

### 2. Frontend boots cleanly

- [ ] `npm run dev` in `frontend/` starts on port 5173
- [ ] No red errors in browser console at `http://localhost:5173`
- [ ] Landing page (or login redirect) loads in <2 sec

### 3. Signup → Trial auto-grant

- [ ] Open `http://localhost:5173/setup` → see signup form
- [ ] Enter test email, name, password → submit
- [ ] Lands on dashboard after signup
- [ ] **Trial banner appears at top:** "Pro trial ends in 14 days"
- [ ] Banner is purple (calm color, not red)
- [ ] Welcome email arrives at the email you signed up with (check Gmail inbox + spam)
- [ ] Email subject: "Welcome to NexusAgent — your 14-day Pro trial is live"
- [ ] Backend logs show: `[subscriptions] trial started biz=biz-XXX plan=pro`

### 4. Trial banner UX

- [ ] Click **X** on trial banner → banner disappears
- [ ] Refresh page → banner stays hidden for 24h (snoozed)
- [ ] Manually clear `sessionStorage` in DevTools → banner reappears
- [ ] Click **Upgrade** button in banner → goes to `/pricing`

### 5. Pricing page — all 5 tiers visible

- [ ] Navigate to `http://localhost:5173/pricing`
- [ ] See 5 cards: Free / Starter / Pro / Privacy / Enterprise
- [ ] Pro card shows "MOST POPULAR" ribbon
- [ ] Prices match: ₹0 / ₹1,499 / ₹5,999 / ₹14,999 / Custom
- [ ] Each card has correct features listed
- [ ] No layout issues (no right-side gap, no overflow)

### 6. Razorpay payment flow — Pro tier

- [ ] Click **Subscribe** on Pro tier card
- [ ] Razorpay modal opens (purple/black UI with "NexusAgent" branding)
- [ ] Modal shows correct amount: **₹5,999**
- [ ] Pay with UPI: enter `success@razorpay` → modal flow → success
- [ ] Modal closes
- [ ] Green banner appears: "Payment verified. Welcome to Pro!"
- [ ] After 1.2 sec, redirects to `/?welcome=pro`
- [ ] **Welcome modal opens** with confetti header "Welcome to Pro"
- [ ] Modal shows "What's now unlocked" with feature list
- [ ] "Invite up to 4 teammates" button visible
- [ ] "Activate your AI agents" CTA visible
- [ ] Click X → modal closes, URL strips `?welcome=pro`

### 7. Post-payment side effects

- [ ] Welcome email arrives at signup email (subject: "Welcome to NexusAgent Pro — payment received")
- [ ] **GST invoice PDF attached** to email (filename `NexusAgent-Invoice-202605-XXXXX.pdf`)
- [ ] Open PDF → shows "TAX INVOICE" or "BILL OF SUPPLY" header, amount ₹5,999, payment ID
- [ ] Founder notification email arrives at `FOUNDER_NOTIFY_EMAIL` (subject: "💰 NexusAgent: ... paid ₹5,999")
- [ ] Backend logs show `[billing-email] welcome sent` + `[billing-email] founder pinged`
- [ ] Backend logs show `[subscriptions] biz=... -> pro period_end=...`

### 8. Subscription state persisted

- [ ] Navigate to `/pricing` again
- [ ] Free tier now shows "You are on this plan" — WAIT, should show on Pro now
- [ ] Pro tier card shows green "CURRENT" badge
- [ ] Trial banner is GONE (because status flipped from trial to active)
- [ ] Hit `GET /api/billing/subscription` (use browser dev tools or curl) → returns `{"plan_key":"pro","status":"active","current_period_end":"2026-XX-XX"}`

### 9. Magic Workflows (Pro feature)

- [ ] Navigate to `/workflows` → click "Gallery" tab
- [ ] Click any of the 4 example chips → textarea fills
- [ ] Hit Cmd/Ctrl+Enter (or click Generate)
- [ ] Within 3-8 sec, redirects to workflow builder canvas
- [ ] Generated workflow has at least 2 nodes (trigger + action)
- [ ] Nodes have descriptive names (not random IDs)
- [ ] Click Save → workflow appears in saved list
- [ ] Toggle Enable → workflow goes active

### 10. Plan gating works

- [ ] In DB, manually set this business to plan='free': `UPDATE nexus_subscriptions SET plan='free', status='active' WHERE business_id=...`
- [ ] Refresh `/pricing` → Free tier shows CURRENT
- [ ] Try to generate Magic Workflow → should fail with "Magic Workflows is a Pro feature"
- [ ] Try to trigger outbound voice call → should return 402 with upgrade message
- [ ] Try to generate Privacy Bridge token → should return 402

---

## 🟡 IMPORTANT (Phase 2) — should pass before customer onboarding

### 11. Login / logout

- [ ] Logout from dashboard
- [ ] Lands at `/login` with login form
- [ ] Enter credentials → logs in successfully
- [ ] Session persists across browser refresh
- [ ] Logout button works again

### 12. Multi-business switching

- [ ] In dashboard, top-left "Business switcher" dropdown
- [ ] Click → see list of businesses
- [ ] Create new business → switches to it automatically
- [ ] Trial auto-grants on new business too (new banner appears)

### 13. CRM — Contacts

- [ ] Navigate to `/crm`
- [ ] Click "Add Contact" → form opens
- [ ] Fill name, email, phone, company → save
- [ ] Contact appears in list
- [ ] Click contact → detail page opens
- [ ] Add note → saves and appears in timeline
- [ ] Add task → appears in tasks tab
- [ ] Edit contact → changes persist
- [ ] Delete contact → confirms + removes from list

### 14. CRM — Deals

- [ ] Click "Add Deal" → form opens
- [ ] Link to existing contact, enter amount, stage → save
- [ ] Deal appears in pipeline view
- [ ] Drag deal between stages (if Kanban) → stage updates
- [ ] Deal detail page shows amount, contact, history

### 15. CRM — Tasks

- [ ] Navigate to `/tasks`
- [ ] Add task → appears in list
- [ ] Mark complete → strikethrough + moves to completed
- [ ] Filter by status (open / completed) → list updates

### 16. CRM — Invoices

- [ ] Navigate to `/invoices`
- [ ] Click "Create Invoice" → form opens
- [ ] Fill customer details, line items → save as draft
- [ ] Generate PDF (if button exists) → PDF downloads
- [ ] Send invoice via email (if integration set up) → email sent

### 17. Chat / AI Agent

- [ ] Navigate to `/chat`
- [ ] Type "Hello, who are you?" → AI responds
- [ ] Try "List my top 5 contacts" → returns CRM data
- [ ] Try "Send an email to john@example.com saying hi" → drafts an email (goes to approval queue, doesn't auto-send)

### 18. Magic Search

- [ ] In CRM or anywhere with global search, type "deals over 10000"
- [ ] Returns matching deals
- [ ] Type "contacts in Mumbai" → returns matching contacts
- [ ] Empty queries return empty (no crash)

### 19. Workflows — Templates

- [ ] On `/workflows` gallery tab, scroll past Magic Workflows section
- [ ] See pre-built template cards
- [ ] Click "Use this" on one → creates enabled workflow
- [ ] Click "Customize" → opens canvas builder

### 20. Workflow Builder — Manual

- [ ] Click "New Workflow" (empty)
- [ ] Drag a trigger node onto canvas
- [ ] Drag an action node
- [ ] Connect them with an edge
- [ ] Configure each node's settings
- [ ] Save → returns to list
- [ ] Run manually → see execution log

### 21. Agents page

- [ ] Navigate to `/agents`
- [ ] See list of 8 default agents (Email Triage, Briefing, Research, etc.)
- [ ] Click an agent → detail page with config
- [ ] Toggle on/off → state persists

### 22. Briefing

- [ ] Navigate to dashboard
- [ ] Click "Daily Briefing" or "Generate Briefing" button (if visible)
- [ ] AI generates morning briefing with today's tasks/deals
- [ ] Renders as markdown without raw `**bold**` text

### 23. Documents / RAG

- [ ] Navigate to `/documents`
- [ ] Upload a PDF (any PDF, e.g. an invoice or doc)
- [ ] PDF parses successfully (no "PyMuPDF" error)
- [ ] Document appears in list with extracted text preview
- [ ] In chat: "What's in my latest uploaded document?" → AI references it

### 24. Settings page

- [ ] Navigate to `/settings`
- [ ] Edit business name → saves
- [ ] Notification preferences toggle → saves
- [ ] See current plan badge "Pro"
- [ ] System info section shows backend version

### 25. Security page

- [ ] Navigate to `/security`
- [ ] See 2FA section, sessions list
- [ ] Try enabling 2FA → QR code appears (don't need to actually scan)
- [ ] Cancel out

### 26. Privacy Mode page

- [ ] Navigate to `/settings/privacy-mode`
- [ ] Should be plan-gated — currently Pro shouldn't access Privacy Bridge
- [ ] Wait — test as Pro: should see "Upgrade to Privacy" or token generation
- [ ] Manually change DB to plan='privacy' → reload → should now allow token issue
- [ ] Click "Generate Token" → token displayed (pb_xxx)
- [ ] Click "Copy" → copies to clipboard
- [ ] State pill shows "Not set up"

### 27. Notifications

- [ ] Click the bell icon top-right
- [ ] See notification dropdown
- [ ] If notifications exist, mark one read → indicator updates
- [ ] Clear all → list empties

### 28. Sidebar UX (we just fixed these)

- [ ] Click chevron in sidebar → sidebar collapses to 60px
- [ ] In collapsed state, chevron is still visible (we fixed this)
- [ ] Click chevron again → expands
- [ ] Each nav item has tooltip on hover when collapsed

### 29. Theme switching

- [ ] Find theme toggle (sun/moon icon)
- [ ] Toggle to light mode → all pages re-skin
- [ ] Toggle back to dark mode → re-skins
- [ ] Refresh → theme persists

---

## 🟠 ADVANCED (Phase 3) — nice to verify but not blocking

### 30. WhatsApp Bridge (if you want to test)

- [ ] Start `whatsapp_bridge` Node.js process
- [ ] Scan QR with WhatsApp Business app
- [ ] Send "Hello" from your phone to the linked number
- [ ] Message appears in NexusAgent activity feed
- [ ] AI generates a draft reply (goes to approval queue)
- [ ] Approve → reply sent back via WhatsApp

### 31. Voice (Vox) — if running nexuscaller-lab

- [ ] In CRM, on a contact, click "Call now" button
- [ ] Redirects to vox precall page (localhost:8765/precall)
- [ ] Pick a stack combo, click Place call
- [ ] Vox dials your number → answers with AI
- [ ] After hang up, transcript appears in NexusAgent activity feed

### 32. Email triage (if Gmail IMAP configured)

- [ ] Send a test email to the linked Gmail
- [ ] Wait ~15 min for scheduler to pick it up
- [ ] In dashboard, see new "Email triage" activity
- [ ] AI categorizes (Urgent / FYI / Spam etc.)

### 33. Calendar integration

- [ ] In `/settings`, link Google Calendar (OAuth flow)
- [ ] Calendar events appear on dashboard
- [ ] Click event → details
- [ ] Briefing references upcoming meetings

### 34. Background scheduler

- [ ] Check uvicorn logs for `[AgentScheduler] 9 jobs registered`
- [ ] Wait ~5 min, check for `[AgentScheduler] privacy-bridge health checks` log
- [ ] Set a workflow with `schedule_trigger` for every 5 min
- [ ] Verify it runs at the scheduled time

### 35. Audit log

- [ ] Perform a few actions (create contact, edit deal, etc.)
- [ ] Navigate to `/audit`
- [ ] See entries for each action with timestamp + user

### 36. Setup wizard (first-run)

- [ ] In a fresh browser session, visit `/setup`
- [ ] Setup wizard appears
- [ ] Walk through steps (Ollama probe, demo data, etc.)
- [ ] Complete setup → redirected to login or dashboard

### 37. Razorpay webhook (advanced)

- [ ] Make a test payment
- [ ] Backend logs show `[billing] webhook event=payment.captured` (if webhook configured)
- [ ] If RAZORPAY_WEBHOOK_SECRET set, signature validation passes

### 38. Trial → paid conversion

- [ ] Create new business (auto-grants 14-day trial)
- [ ] Immediately pay for Pro → `current_period_end` should be ~44 days out (14 trial + 30 paid)
- [ ] Verify in DB or via `/api/billing/subscription` endpoint

### 39. Trial expiry

- [ ] In DB, set `trial_ends_at` to yesterday for a trial business
- [ ] Run `python -c "from api.subscriptions import reap_expired; print(reap_expired())"`
- [ ] Business plan flips to 'free', status='active'
- [ ] Trial expired email arrives at signup email

### 40. Plan downgrade flow

- [ ] On a paid business, find "Disable bridge" or "Cancel subscription" button
- [ ] Click → confirmation
- [ ] Status flips to 'cancelled', plan stays Pro until period_end
- [ ] After period_end, plan auto-flips to free

---

## 🔧 ADMIN / OPS — verify these work before customer #1

### 41. Database migrations applied

- [ ] Connect to Postgres → `SELECT * FROM nexus_migrations;`
- [ ] See migrations 1-6 applied
- [ ] No errors in boot logs about migrations

### 42. Sentry events

- [ ] Trigger an exception (visit `/api/this-doesnt-exist` or similar)
- [ ] Check Sentry dashboard within 1 min → event appears
- [ ] Event has stack trace, breadcrumbs, business_id context

### 43. Backup script

- [ ] Run `bash scripts/backup_db.sh` (Postgres dump or SQLite copy)
- [ ] Verify backup file created in `backups/` or `/tmp/`
- [ ] If `BACKUP_S3_BUCKET` set, uploaded to S3

### 44. Cost guardrails

- [ ] Try to hit cloud LLM 100K times rapidly → should rate-limit
- [ ] Check `nexus_cloud_usage` table for per-business token cap enforcement

### 45. CI workflow

- [ ] Push a commit to a test branch
- [ ] GitHub Actions runs CI workflow
- [ ] All 9 jobs pass (Backend, Frontend, Landing, WhatsApp bridge, Privacy Bridge installer, Secrets scan, E2E Playwright, CI summary)
- [ ] Mermaid graph renders in workflow summary

### 46. Production smoke test (NexusAgent)

- [ ] Run `python -m scripts.smoke_privacy_bridge`
- [ ] All 20 tests pass

---

## 📝 BUGS FOUND DURING TESTING

(Note bugs here as you find them — section by section.)

### Phase 1 critical issues:
- (none yet — fill in as you test)

### Phase 2 important issues:
- (none yet)

### Phase 3 advanced issues:
- (none yet)

---

## 🚀 AFTER ALL CRITICAL CHECKS PASS — Deployment Plan

Once Phases 1-2 are 100% checked:

1. **Deploy landing page** to Vercel/Cloudflare Pages (15 min)
   - Build `landing/dist/`
   - Connect GitHub repo
   - Point `nexusagent.in` A record to deploy target

2. **Add robots.txt** at `landing/public/robots.txt`:
   ```
   User-agent: *
   Allow: /
   ```

3. **Provision AWS infrastructure** with $100 credit:
   - 1× EC2 t3.medium (Ubuntu 24) — ~$30/mo
   - 1× Elastic IP attached — free
   - EBS 30GB gp3 — ~$3/mo
   - Route 53 hosted zone for `nexusagent.in` — $0.50/mo
   - **Total: ~$33/mo → $100 credit = ~3 months free**

4. **Setup billing alerts** at $5/$25/$50/$90 before provisioning

5. **Deploy NexusAgent backend** to EC2:
   - systemd service for FastAPI
   - systemd service for WhatsApp bridge
   - Caddy reverse proxy for HTTPS
   - Postgres self-hosted on same EC2 (skip RDS for now)

6. **Point `app.nexusagent.in`** A record at Elastic IP

7. **Update production .env**:
   - `SENTRY_ENV=production`
   - `RAZORPAY_KEY_ID=rzp_test_...` (still test until KYC)
   - `APP_BASE_URL=https://app.nexusagent.in`
   - All other secrets

8. **Verify production** works:
   - Visit `https://nexusagent.in` → landing page
   - Visit `https://app.nexusagent.in` → app loads
   - Sign up flow works
   - Payment flow works

9. **Reapply to AWS Activate** with the deployed site → much higher approval odds

10. **Apply to Microsoft for Startups / Twilio / Anthropic** with `hi@nexusagent.in` from deployed app

---

**Last updated:** May 11, 2026
**Tester:** Praneeth P K
**Environment:** localhost (pre-deployment)
