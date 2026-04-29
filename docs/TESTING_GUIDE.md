# Tester's guide

Hand this to anyone evaluating NexusAgent for the first time. Walks them
through a 30-minute smoke test that exercises every load-bearing feature.

---

## Setup (one time, ~10 min)

```bash
# 1. Install Ollama (https://ollama.com/download) and pull the models
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull nomic-embed-text

# 2. Backend
python -m venv venv && venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn api.server:app --port 8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Sign up with any email + password ≥ 8 chars.
The first user becomes the workspace owner.

> **Faster path on Windows:** double-click `start.bat` — it ties all three
> together and opens the browser.

---

## The 30-minute smoke test

### 1. First impressions (Dashboard)

- After sign-up you land on `/`. The Dashboard should show the **"Today's
  focus"** strip. With a fresh workspace it'll be the clean-desk state.
- Click **"Load sample data"** to seed contacts, deals, invoices.

✓ Pass: dashboard shows non-zero stats within 5 seconds.

### 2. CRM detail pages (the click-through test)

- Open `/crm`. You're on the **Leads tab** by default (first tab).
- Switch to **Contacts**. Click any contact row — should open
  `/crm/contacts/{id}` with the contact's full profile.
- On the Contact detail page, look for: profile editable inline,
  **Timeline** (interactions + deals + invoices stitched together),
  **Open deals**, **Invoices**, action rail on the right.

✓ Pass: every list row in CRM (contacts / companies / deals) and Invoices
opens its detail page.

### 3. AI lead scoring (the "spend time on the right people" demo)

- Go to **Settings**, scroll to **"Ideal Customer Profile"**. Paste:

  > We sell to B2B SaaS companies in India with 50–500 staff. Buyers are
  > usually Heads of Sales, RevOps leads, or founders. Look for active
  > hiring in revenue roles.

- Click **Save ICP**.
- Go to a Contact detail page → click **"Score this lead"** in the right
  rail. Wait ~3 seconds. The header gets a colored chip ("High fit · 85"
  or similar) and a new **"AI fit assessment"** panel surfaces the
  reasoning.

✓ Pass: score is between 0–100 with non-empty reasoning.

### 4. AI-drafted outreach (the "wow this writes for me" demo)

- On the same Contact detail page, click **"AI draft outreach"**.
- Modal opens with three tabs: **warm / professional / direct**. Each tab
  has a subject + body draft.
- Edit one variant. Click **"Open in mail"** — your default mail client
  opens with subject + body prefilled.

✓ Pass: three variants generated, all editable, mailto: opens.

### 5. Public lead-capture (the "leads land in CRM" demo)

- Go to **CRM → Leads tab → Public form keys** section.
- Click **Generate key**. Copy the raw key shown (it's only visible once).
- Click **Show embed snippet**. Copy the snippet.
- In a separate terminal, simulate a form submission:

```bash
curl -X POST http://localhost:8000/api/public/leads \
  -H "Content-Type: application/json" \
  -d '{"intake_key":"PASTE_KEY_HERE","name":"Test Lead","email":"test@example.com","company":"Test Co","message":"Demo submission"}'
```

- Refresh the **Leads tab**. The new lead appears in "Recent inbound"
  with `public_form` source pill and an auto-score badge.

✓ Pass: lead lands and scores within 5 seconds of the curl.

### 6. Capture from email (the "no SMTP needed" demo)

- On the Leads tab, click **"Capture from email"**.
- Paste any email content. Click **Extract**.
- Review the parsed sender + summary. Click **Save as lead**.
- You land on the new contact's detail page, auto-scored.

✓ Pass: parsing works end-to-end; new contact tagged `email_paste`.

### 7. BANT extraction (the "pipeline progression" demo)

- On a contact who has an open deal, click **"Qualify their reply"** in
  the right rail.
- Paste a sample reply, e.g. *"Hi, we have budget approved for Q2,
  I'm the head of sales here, current tool is too expensive, want to
  start in 30 days."*
- Click **Extract BANT**. The result shows four quadrants
  (Budget / Authority / Need / Timing) each tagged yes/no/unknown with
  evidence quotes.
- If the model suggests a stage advance, click **"Advance"** — the
  open deal moves stages.

✓ Pass: signals extracted, evidence quoted, stage suggestion appears.

### 8. Reports (the "narrate my data" demo)

- Go to **Reports**. Click any of the **sample query** buttons.
- Watch the four-stage progress UI: Understanding → Querying → Writing
  → Building PDF.
- A PDF file appears in the list. Click **Download**.

✓ Pass: PDF generates within 30 seconds, downloads cleanly.

### 9. Privacy posture (the moat demo)

- Go to **Audit** in the sidebar.
- Top band shows: actions logged · cloud calls · redactions ·
  kill-switch state.
- Switch to the **Cloud calls** tab. If you've been using cloud LLMs,
  you'll see entries with provider, model, redaction count + kinds,
  and an opt-in fingerprint reveal.
- Open `.env`, set `ALLOW_CLOUD_LLM=false`, restart the server. Refresh
  Audit — kill-switch indicator turns green: **"Cloud OFF · local only"**.

✓ Pass: every cloud call is logged with redaction details; kill switch
flips clean.

### 10. Backup + restore-readiness

- Go to **Settings → Disaster-recovery backup**.
- Click **Download backup**. A zip downloads (~MB, depending on data).
- Unzip locally. You should see: `manifest.json` (version + sizes),
  `nexusagent.db` (a valid SQLite file), `chroma_db/` (vector store),
  `README.txt` (manual restore steps).

✓ Pass: zip extracts cleanly, manifest valid, DB opens with `sqlite3`.

---

## Things to break on purpose

A tester earns their keep by trying these:

1. **Cross-tenant leak attempt.** Sign up a second user, create their
   workspace. Use their JWT but try to GET `/api/crm/contacts/{id}` for
   user 1's contact. Must 404. Same for delete + update.

2. **Public form abuse.** Hit `/api/public/leads` 11 times in one
   minute from the same IP — the 11th must 429.

3. **Bad ICP scoring.** Save an ICP with garbage text. Rescore a
   contact. The model output may be junk — but the API must NOT invent
   a number; it should return `score=null` with a "try Rescore" reason.

4. **Workflow loop.** Open a workflow template, save it, run it. Check
   `Audit` for the action log entries. If any agent action silently
   fails, the run log will show `error` status — that's the bug.

5. **Offline PWA.** Install the app via Chrome's PWA prompt. Take WiFi
   off. Reload — should still load `/index.html` from cache instead of
   showing the dino.

---

## What to file

If you find anything that:
- Returns a 500 instead of a 404/400 → file as **bug**.
- Surfaces a stack trace to the user → file as **bug**.
- Sends raw customer data to the cloud (check `outputs/cloud_audit.jsonl`
  — every line should have a SHA, never raw text) → file as **security**.
- Looks visually broken on phone width (~375px) → file as **UX**.
- Has a feature that lies (says one thing, does another) → file as
  **trust**.

Privacy bugs are the highest priority. Trust bugs are second. UX is
third. Cosmetic stuff is everything after.

---

## Known limitations

These are documented gaps, not bugs:

1. **Restore is manual** — backup feature works; the guided restore
   endpoint is on the roadmap. Manual steps are in the zip's README.
2. **Multi-currency in What-If** — picks the most common currency on
   the workspace, ignores others. Mixed-currency workspaces get a
   single-currency simulation.
3. **Email forwarder magic-inbox** isn't wired up to a real SMTP
   receiver — the workaround is the "Capture from email" paste flow.
4. **Forge AI prospecting** ("find me 30 D2C brands…") is on the
   roadmap, not shipped.
5. **Code-signing** for the desktop installer isn't done — the
   checklist is in `desktop/SIGNING_CHECKLIST.md`.

---

## Final word

This is a serious build. 323 backend tests pass. Privacy is enforced
by construction, not by promise. Multi-tenant isolation is verified
across 28 contract tests. The agent system actually does work — the
operator's job is to approve, not to do.

Treat anything that contradicts those claims as a P0.
