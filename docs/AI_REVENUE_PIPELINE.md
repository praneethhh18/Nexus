# AI lead-to-revenue pipeline

A proposal for how NexusAgent threads AI through the full sales lifecycle —
from a stranger arriving with a form fill, all the way to invoice paid +
renewal. Designed for the existing architecture (agent personas, approval
queue, privacy gate, workflow engine) so we can ship it incrementally
without rewriting anything we already have.

**Guiding principle**: AI is the co-pilot, not the autopilot. The human
approves anything outbound. The AI does the grunt work — research,
drafting, scoring, summarising, watching for staleness — so a single
operator can run the pipeline of a small sales team.

---

## The 8 stages

```
   ┌──────────┐   ┌────────────┐   ┌──────────┐   ┌──────────┐
   │ 1. Lead  │ → │ 2. Qualify │ → │ 3. Prop. │ → │ 4. Negot.│ → ...
   └──────────┘   └────────────┘   └──────────┘   └──────────┘
                                                          │
                                          ┌───────────────┴────────┐
                                          │                        │
                                     ┌────▼─────┐            ┌─────▼────┐
                                     │ 5. Won   │            │ 5. Lost  │
                                     └────┬─────┘            └─────┬────┘
                                          │                        │
                                          ▼                        ▼
                                     ┌──────────┐            ┌──────────┐
                                     │ 6. Invo. │            │ 8. Memory│
                                     └────┬─────┘            └──────────┘
                                          │
                                          ▼
                                     ┌──────────┐            ┌──────────┐
                                     │ 7. Paid  │ ───────────►│ 8. Renew │
                                     └──────────┘            └──────────┘
```

For each stage, three columns: **what runs**, **who decides**, **the data
artefact created or updated**.

### 1. Lead capture & enrichment

| What runs | Who decides | Artefact |
|---|---|---|
| New lead arrives (form, email forwarded to a triage inbox, manual entry, integration). **Iris** triages email replies; a new agent **Forge** (proposed) handles the enrichment pass: scrape company website, identify role + industry + size, find the LinkedIn URL, fetch a 1-line "about us" summary. Score the lead against the ICP profile (configurable in Settings). | Auto-creates the contact + company. The enrichment notes show as a discoverable "AI-suggested" badge on the contact detail page; the user accepts or edits. | `nexus_contacts.ai_enrichment` JSON column with `{score, summary, signals: ['B2B SaaS', '50-200', 'YC-backed'], confidence}` |

**Status today**: not built. The enrichment uses the existing `rag_search`
+ web search tools that the agent registry already has, so the wiring is
small.

### 2. Qualification

| What runs | Who decides | Artefact |
|---|---|---|
| **Forge** drafts 2–3 outreach variants (warm / professional / direct) using the contact's signals and a couple of past wins for reference (drawn from `business_memory`). When the prospect replies (Iris triages it), an extractor pass pulls structured BANT signals — budget, authority, need, timing — from the reply text. Updates the deal record. | User approves which variant to send. After the reply, AI suggests "looks like budget = X, timing = Y, ready to advance to Proposal?" and the user clicks one button. | New `nexus_deal_signals` table: `(deal_id, signal_kind, value, confidence, source_message_id, extracted_at)`. |

**Status today**: outreach drafting works (template generation exists);
BANT extraction is the missing piece. Same LLM-with-prompt pattern as
the existing `email_triage._classify`.

### 3. Proposal

| What runs | Who decides | Artefact |
|---|---|---|
| **Sage** (current meeting-prep agent) widens to "engagement prep". When the deal moves to `proposal`, Sage pre-fills the existing proposal template with: contact name + company, scope inferred from conversation history (RAG over `nexus_interactions`), suggested pricing tier based on company size + signals, deliverables, milestones. Drafts the cover email. | User reviews + tweaks the proposal in the existing document editor. Approves the cover email send. | An entry in `nexus_documents` linked to the deal via a new `deal_id` FK. |

**Status today**: document templates work; the AI pre-fill is missing.
The deliverables/milestones inference is a single LLM prompt with the
contact's interaction history as input — same pattern as the morning
briefing.

### 4. Negotiation

| What runs | Who decides | Artefact |
|---|---|---|
| **Arjun** (current pipeline watcher) gets richer. For each deal in `proposal` or `negotiation`: summarise interaction history into "what's agreed / what's outstanding / what could derail this". Drafts responses to objection emails using a learned-from-past-wins memory layer. Surfaces deal risks: long silence (>14 days), competitor mentions, scope creep ("they keep asking for more"). Lets the user run a "what if we discount 10%?" simulation against the deal value. | Risks surface as nudges in `/inbox` ("Arjun noticed Acme has gone quiet for 11 days"). Discount simulations are inline in the deal detail page, no commitment. | Existing `nexus_nudges` + a new `nexus_deal_risks` table with a `kind` enum: `silence`, `scope_creep`, `competitor`, `mismatch`. |

**Status today**: stale-deal watcher exists. Risk classification is new
but small. Deal-level what-if uses the simulator I just rewrote.

### 5a. Closed — Won

| What runs | Who decides | Artefact |
|---|---|---|
| Stage flips to `won`. The deal detail page already prompts "Draft invoice" — that creates an invoice pre-filled from the deal value + customer. **Atlas** drafts a confirmation email to the contact and a short Slack/Discord post for the team. Suggests onboarding tasks (kickoff call, project workspace setup, intro to delivery team). | User approves both messages. Tasks are auto-created; the user edits or deletes. | `nexus_invoices` row with `deal_id` FK linking back to the won deal. `nexus_tasks` rows tagged `project:<deal_id>`. |

**Status today**: the "Draft invoice" button exists in the deal detail
page I just shipped. The confirmation email + onboarding-task generation
are new — but follow the same pattern as the briefing agent.

### 5b. Closed — Lost

| What runs | Who decides | Artefact |
|---|---|---|
| When the user marks a deal lost, **Echo** prompts for a structured loss reason (price / timing / competitor / fit / silence) — a quick form, not free-text. The reason + last interaction context goes into `business_memory` so future leads with similar profiles get a "we lost a deal like this last quarter because of X" warning. AI drafts a "stay in touch" follow-up task scheduled for +6 months. | User picks the loss reason from a dropdown; clicks Save. The future task is a draft task they can edit / delete. | New `nexus_deal_losses` table with `(deal_id, reason, notes, similar_profile_ids[])`. Echo's memory grows. |

**Status today**: not built. The loss-reason form is one component;
the memory-write is one call into the existing business_memory system.

### 6. Invoice → 7. Paid

This is mostly built already. **Kira** drafts overdue reminders. The new
work is layered escalation:

| Days overdue | What Kira does |
|---:|---|
| 1–7 | Polite "just checking in" reminder, drafted, queued for approval. |
| 8–30 | Firmer "this is N days overdue" with payment-link prominent. |
| 31–60 | Calendar-it reminder draft, includes a "is something blocking this?" line. |
| 61+ | Escalation note for the user (not the customer) — "this might need a phone call." |

**Status today**: Kira drafts one type of reminder. Adding the escalation
ladder is a small switch on `days_overdue` in the existing module.

### 8. Account expansion / renewal

| What runs | Who decides | Artefact |
|---|---|---|
| **Atlas** tracks engagement signals per won customer: invoice frequency, last-interaction recency, unanswered emails, whether they're using more or less than expected. 60 days before a contract anniversary, surfaces a renewal touch-point. For high-engagement customers, suggests a specific upsell ("they paid 3 invoices on time and grew headcount — pitch the Pro tier"). | User reviews the suggestion in `/inbox`, approves the outreach draft. | New `nexus_account_signals` aggregating across invoices + interactions + memory. |

**Status today**: not built. Needs the longest lead time to ship — but
also has the highest revenue impact (every existing customer is the
cheapest deal you'll ever close).

---

## Cross-cutting infrastructure

These three pieces are the difference between "AI features sprinkled on
top" and "AI threaded through the whole product":

### A. Pattern memory ("what worked / what didn't")

Every stage transition writes to a normalised memory layer. Won deals
embed their key features (industry, size, signals at qualification, key
objections that were overcome) into a vector store. New leads get
similarity-searched against this corpus → "deals like this one closed
74% of the time when we sent a follow-up within 48 hours."

Implementation: extend the existing `business_memory` module with a
`pattern_kind = 'win' | 'loss' | 'objection_handled'` tag. RAG over it on
every stage transition. Adds maybe ~2 days of work; pays itself back
within a quarter of usage.

### B. Confidence-gated automation

Every AI suggestion ships with a confidence number (already a pattern in
the orchestrator's intent detector). For each agent action, the user
configures a per-agent threshold:

```
Confidence ≥ 0.95 → auto-execute (rare; almost always overkill)
Confidence ≥ 0.80 → auto-draft, queue for approval
Confidence ≥ 0.60 → suggest, don't draft
Confidence < 0.60 → don't surface
```

Settings page already has the agent enable/disable toggle. Adding
per-agent thresholds is one form. Lets the user dial up trust gradually
as they see results — exactly the right pacing for a product where the
default posture is "AI is a co-pilot, not autopilot."

### C. Conversation-stitch view

The single best UX on most modern AI sales tools is "show me everything
about this customer in one timeline." We already have:

- `nexus_interactions` — calls, emails, meetings, notes
- `nexus_deal_stage_events` — every stage transition
- `nexus_invoices` — billing history
- `nexus_agent_runs` — AI actions taken on the account
- Email triage history

Stitch them by `contact_id` (and recursively up to `company_id`) into a
single chronological feed on the contact / company detail pages. The
detail pages I just shipped have empty space on the right rail that's
perfect for this. ~1 day of frontend work; the backend joins are
straightforward.

---

## Privacy posture (non-negotiable)

Every AI step in this pipeline obeys the existing four-layer gate:

1. **Enrichment** — the web-scrape tool already runs locally. The fit-scoring
   prompt is short + aggregate; can go cloud (redacted) or stay local.
2. **BANT extraction** — runs `sensitive=True` (sees email body content).
   Forced local Ollama every time.
3. **Proposal pre-fill** — uses the aggregate-then-cloud pattern that
   already powers reports. The deal value + tier go to cloud; the contact
   list and conversation history stay local.
4. **Pattern memory** — embeddings always local via `nomic-embed-text`.
   The "deals like this" reasoning prompt sees only summarised features,
   not raw rows.

No new privacy-engineering work needed — the existing
`config/privacy.py` gate covers all of these paths.

---

## Shipping order (proposed)

If we built one thing per week, the order that produces value fastest:

1. **Conversation-stitch view** on contact / company / deal detail pages.
   Highest immediate value: the user finally has *one screen* per customer.
   Pure frontend + a few backend joins. (1 week)

2. **Loss-reason capture + memory write**. Tiny scope, lays the foundation
   for the pattern-memory layer. (3 days)

3. **BANT extraction** on email replies. Iris already classifies; this is
   one more LLM pass with a structured-output prompt. (3 days)

4. **Per-agent confidence thresholds** in Settings. Unlocks safe autonomy
   for the user who's ready to trust Kira but not Iris yet. (2 days)

5. **Win-deal automation**: confirmation email + onboarding-task draft. (3 days)

6. **Lead enrichment + ICP scoring**. The biggest single feature; needs
   ICP profile config + web-scrape tool wiring. (1 week)

7. **Renewal/expansion signals**. The longest payoff; needs 60+ days of
   data before it's useful. Defer until after a few customers have been
   on the product for that long. (1 week)

Total: ~6 weeks of focused work to thread AI through the full pipeline.
Each week ships something a user can feel. None of it requires
re-architecting what's already there.

---

## What this proposal does NOT do

- It does not add a new "AI Sales" page. The AI lives inside the existing
  surfaces (Inbox, CRM, Deal detail, Invoices). A separate page would
  imply AI is a feature; it isn't — it's a way of working.
- It does not require a new agent persona for every stage. Existing
  personas (Atlas, Iris, Kira, Arjun, Sage, Echo) already map cleanly to
  these stages. Only **Forge** is genuinely new (lead enrichment).
- It does not promise "fully autonomous sales." The product's brand is
  "co-pilot, not autopilot" — every outbound action stays approval-gated
  by default.

The result is a sales experience where the operator is always one click
away from doing the right thing — because the AI already drafted it,
scored it, and put it in front of them with the right context attached.
