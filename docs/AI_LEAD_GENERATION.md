# Stage 0 — Lead generation

The companion doc to [`AI_REVENUE_PIPELINE.md`](./AI_REVENUE_PIPELINE.md).
That document starts at "lead arrives." This one answers the prior
question: **where do leads come from?**

For a small business running NexusAgent, leads enter through five
distinct channels, each with its own motion. The product needs to
support all of them and route the result into the same pipeline so
the AI in stages 1–8 can pick up cleanly.

---

## The five channels

```
                                ┌─────────────────────┐
                                │   nexus_contacts    │
                                │   (single source    │
                                │    of truth)        │
                                └──────────▲──────────┘
                                           │
              ┌────────────┬───────────────┼───────────────┬────────────┐
              │            │               │               │            │
   ┌──────────▼──┐  ┌──────▼──────┐  ┌─────▼─────┐  ┌─────▼──────┐  ┌──▼──────────┐
   │  1. Public  │  │  2. Email   │  │ 3. WhatsApp│  │ 4. CSV /   │  │ 5. Outbound │
   │  form       │  │  forwarder  │  │  / chat    │  │  manual    │  │  (AI-found) │
   │  (website)  │  │  inbox      │  │            │  │  add       │  │             │
   └─────────────┘  └─────────────┘  └────────────┘  └────────────┘  └─────────────┘
```

Every lead lands as a row in `nexus_contacts` with a `source` column
recording where it came from, so attribution survives downstream.

---

### 1. Public lead-capture form (inbound, passive)

The simplest channel. Someone visits your website, fills a form,
becomes a contact. Today this requires a developer to wire up — we'll
make it a one-line embed.

**The motion:**

1. Workspace owner opens Settings → "Public lead form" → copies a key.
2. Pastes a 5-line `<script>` snippet (or a fetch call) onto their
   marketing site or landing page.
3. Form submissions hit `POST /api/public/leads` with that key.
4. The endpoint creates a `nexus_contacts` row scoped to the workspace
   that owns the key, tagged `source: "public_form"`.
5. Workspace owner gets a notification (in-app + Discord/email if
   configured) and the lead appears in `/inbox` for triage.

**Privacy posture:** the public endpoint accepts only the fields you
declare (name, email, message). It never reflects internal IDs or
errors. Rate-limited per IP. The intake key can be revoked + regenerated
without downtime.

**What's needed:**
- `nexus_intake_keys` table (one or more per workspace, revocable)
- `POST /api/public/leads` (unauth, key-validated, rate-limited)
- A Settings panel that shows the key + an embed snippet
- A sample `landing/widget/form.html` users can copy/paste

**Status today:** not built. Shipping in this batch alongside the doc.

---

### 2. Email forwarder (inbound, semi-active)

Many leads arrive as forwarded emails — "FYI a prospect reached out."
Or you give your team a shared address (`leads@yourcompany.com`) and
forward into NexusAgent.

**The motion:**

1. Workspace gets a magic email address: `leads-{workspace_id}@inbox.nexusagent.app`.
2. User forwards (or auto-forwards via a Gmail rule) inbound emails to it.
3. **Iris** (the existing email triage agent) parses the message:
   - Extracts the original sender if it's a forwarded email
   - Creates a `nexus_contacts` row with `source: "email"`
   - Logs the original email as the first interaction
   - Optionally creates a `lead`-stage deal

**Privacy posture:** the parser runs locally — same `sensitive=True`
flag Iris already uses for inbox triage. The cloud LLM never sees the
raw email body.

**What's needed:**
- A magic-inbox address per workspace (existing IMAP infrastructure
  + a routing rule)
- A small extension to Iris's classifier to route "from a stranger"
  messages into lead capture instead of regular triage
- A Settings panel showing the magic address

**Status today:** Iris exists for IMAP triage of *the user's own*
inbox. The "leads inbox" pattern needs a small extension — assign
a unique address per workspace and route everything from a stranger
into lead-capture flow.

---

### 3. WhatsApp / chat (inbound, active)

For Indian SMB and many international markets, WhatsApp is the dominant
inbound channel. The product already has a WhatsApp bridge router.

**The motion:**

1. Customer messages the workspace's WhatsApp Business number.
2. The bridge already creates a record. Extend it to: if the sender
   isn't an existing contact, create one with `source: "whatsapp"`.
3. Treat the first message as a lead-stage interaction.
4. Iris (or a dedicated agent) classifies: serious enquiry, vendor pitch,
   support question, spam. Routes accordingly.

**Privacy posture:** WhatsApp messages stay local — Bridge stores
locally, classifier runs `sensitive=True`.

**What's needed:**
- The bridge already exists. Just needs the "stranger → contact + lead"
  path on first message.

**Status today:** WhatsApp bridge exists; the lead-conversion step
is a small extension.

---

### 4. CSV import / manual add (inbound, manual)

Already shipped. CSV import via the entity-import wizard, manual
add through the CRM page. Both already create `nexus_contacts` rows.

**Small improvements proposed:**
- CSV import sets `source: "csv_import"` so attribution is honest
  (currently it goes in untagged).
- Manual add prompts for source as a dropdown ("How did this lead
  arrive?"): Referral / Cold list / Conference / Past customer / Other.

**Status today:** CSV import works; just needs the source tag. Manual
add works; needs the source dropdown.

---

### 5. Outbound prospecting (AI-driven find)

The biggest unlock. Instead of the user manually building a target
list, they ask the AI:

> *"Find me 30 D2C brands in Bangalore with 20-100 employees that
> raised funding in the last 18 months."*

**The motion (proposed):**

1. User opens `/chat` and types the prospecting request.
2. A new agent — **Forge** (also referenced in the pipeline doc) —
   handles this:
   - Parses the constraints (industry, geo, headcount, signals)
   - Web-searches authoritative sources (Crunchbase-like, LinkedIn
     directories, government registries) — uses the existing web-search
     tool the agent registry already supports
   - For each candidate: visits their site, extracts a contact path
     (Contact Us page, founder LinkedIn), scores fit against ICP
3. Returns a draft list of 30 prospects, each with a confidence score
   and the source link that backs each claim.
4. User reviews + accepts (single click). Accepted prospects become
   `nexus_contacts` rows with `source: "ai_outbound"` and the discovered
   ICP signals attached.
5. From there, **Stage 1** of the revenue pipeline takes over: enrichment,
   outreach drafting, qualification.

**Privacy posture:** these are public web searches over public data.
No tenant data leaves the machine during prospecting. The accepted
list lives in the workspace's local `nexus_contacts`.

**What's needed:**
- Forge agent module (`agents/forge_prospecting.py` — proposed)
- Web-search + page-extract tools (already in the agent tool registry)
- An ICP profile in Settings the user fills in once: industry, geo,
  size, signals
- A chat interaction pattern that surfaces the candidate list
  inline — same pattern as `/whatif` or `/research`

**Status today:** not built. The components (web search, page extract,
ICP profile, chat slash command) all exist or are trivial. Forge
itself is ~2-3 days of work.

---

## Cross-cutting concerns

### Source attribution + dedup

Every lead carries `source` from one of:
`public_form | email | whatsapp | csv_import | manual | ai_outbound | referral`.

Dedup on first contact: if a lead with the same email exists, we don't
create a duplicate — we add the new touch as an interaction on the
existing contact and bump its `last_seen_at`. Same for phone.

The contact detail page (just shipped) already shows interactions
chronologically; this surfaces dedup naturally — you see *every*
touch from this person, regardless of channel.

### Lead scoring & routing

The pipeline doc covers Stage 1 enrichment/scoring once a lead exists.
Three things to add at the *intake* layer:

1. **ICP score on arrival.** Forge runs the same scoring at ingest:
   high → user notified immediately, medium → batched into the morning
   briefing, low → silently filed, surfaceable later if data improves.

2. **Spam filter.** A small classifier on the public form path:
   "I'm interested in your enterprise solution" submitted from a
   throwaway email is probably noise.

3. **Auto-routing.** Per-source rules: enterprise-shaped leads route
   to a human; SMB-shaped route to AI for the qualification draft.

### Marketing-automation-lite

A few small features that compound the inbound channels:

- **Newsletter list.** Subscribers via the public-form route, segmented
  by their declared intent. Atlas (existing chief-of-staff agent) can
  draft a monthly digest of recent product changes/wins. User approves
  before send.
- **Drip sequences.** For unqualified leads (status = `lead`, no
  reply in 7 days), Iris can draft a polite follow-up. Three touches
  max, then quietly tag as cold.
- **Re-engagement.** Echo (memory keeper) surfaces cold leads quarterly:
  "12 leads from Q1 went cold without a reply. Want to re-approach?"

---

## What ships in this batch

The single highest-leverage piece in this whole doc is **#1, the public
lead-capture endpoint**. It unlocks every other inbound flow conceptually
(if you can wire up the public form, you can wire up Zapier, custom
integrations, anything). It's also the smallest concrete piece of work.

Shipping today:

- `nexus_intake_keys` table — one or more revocable keys per workspace.
- `POST /api/public/leads` — unauth, key-validated, rate-limited.
- Settings panel showing the key + a copy-paste embed snippet.
- Pytest contract: key generates, leads land, dedup on email, invalid
  keys rejected, rate limit applies.

Next batches (in suggested shipping order):

1. **Manual-add source dropdown** + **CSV import source tagging** —
   one afternoon. Honest attribution from day one.
2. **Email forwarder magic-inbox** — extends Iris.
3. **WhatsApp bridge stranger → contact** — extends existing bridge.
4. **Forge prospecting agent** — the big-bang feature.
5. **ICP profile + scoring** — closes the loop.

Total path from "no lead-gen" to "complete lead-gen pipeline":
roughly 4–5 weeks of focused work. Each piece ships independent value.
