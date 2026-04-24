# ADR 0002 — Agents as named personas, not abstract services

**Status:** accepted · **Date:** 2026-04-21

## Context

The classic "AI assistant" UI is a single chat box with a single generic
persona. That works for demos but falls apart once the product does several
kinds of background work — morning briefings, invoice reminders, meeting
prep, email triage, stale-deal monitoring. Users lose track of which
"assistant" did what, and nothing surfaces the fact that the product has
an autonomous team working on their behalf.

## Decision

We ship six named, persona-led agents with specific roles:

| Key                    | Name   | Role             |
|------------------------|--------|------------------|
| `morning_briefing`     | Atlas  | Chief of staff   |
| `email_triage`         | Iris   | Inbox triage     |
| `invoice_reminder`     | Kira   | Invoice chaser   |
| `stale_deal_watcher`   | Arjun  | Pipeline watcher |
| `meeting_prep`         | Sage   | Meeting prep     |
| `memory_consolidate`   | Echo   | Memory keeper    |

Every surface the agents touch — notifications, briefings, activity feed,
suggestions — is stamped with who did the work. Users can rename any agent
per-business; the behaviour is unchanged, the agent just wears the new
name. The identity is a presentation layer on top of the function.

## Consequences

- **Attribution is free.** An overdue-invoice reminder feels like Kira
  noticed it, not like "some automation fired". The suggestions panel
  voices each nudge in the right persona's voice.
- **Renaming is a 2-minute personalisation.** Small businesses use this
  to match their actual team's vocabulary.
- **Custom agents fit in.** The Session-4 custom agent builder lets users
  add their own named agents. Each sits alongside the built-in six in
  the Agents page.
- **One more layer of indirection** in every API response: we carry
  `agent_key` plus the resolved persona name/role/emoji. Worth it for
  the product clarity.

## Alternatives considered

- **Single "Nexus" assistant.** Rejected as losing the autonomy narrative.
- **Function-named ("Email Triager" / "Invoice Bot").** Rejected — those
  are labels, not identities, and users don't bond with them.
- **User-created names from day one.** Rejected for the first-run
  experience — we want users to meet the team on install day, then rename
  later if they want.
