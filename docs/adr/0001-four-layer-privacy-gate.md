# ADR 0001 — Four-layer privacy gate for cloud LLM calls

**Status:** accepted · **Date:** 2026-04-23

## Context

NexusAgent is pitched as a local-first AI business OS. The most natural data
paths through the product touch real customer records: the SQL agent explains
DataFrames, Iris classifies inbound email bodies, the briefing agent reads
deal movement. When we added optional cloud LLM support (Claude + Bedrock Nova)
for polished narrative writing, we created a very real risk of exfiltrating
business data even when users intended to stay local-only.

The question was: how do we let users opt into cloud quality without leaking
business data by accident?

## Decision

Every outbound cloud call passes through four independent gates, any one of
which can force the call to stay local:

1. **Kill switch** (`ALLOW_CLOUD_LLM=false`) — operator-level veto. No cloud
   calls regardless of what callers request.
2. **Sensitivity routing** (`sensitive=True` argument) — callers that know
   they're handling DB rows / PII / customer records flag themselves. That
   flag forces local even if cloud is configured.
3. **PII redaction** (`config.privacy.redact`) — emails, phones, Aadhaar/PAN/
   SSN, cards, secrets, IPs, user paths replaced with opaque tokens before
   any cloud call. A reversible mapping is kept locally so the response is
   un-redacted before the user sees it.
4. **Audit log** (`config.privacy.audit_cloud_call`) — every cloud call
   writes an append-only record to `outputs/cloud_audit.jsonl` with a
   SHA-256 fingerprint of the prompt + character count. **The raw prompt is
   never stored** — the log itself can't leak what it's protecting.

All four gates live in `config/privacy.py`. The LLM provider module calls
them in order so a caller can't accidentally skip a step.

## Consequences

- Users can run with `ALLOW_CLOUD_LLM=true` and feel safe because the
  routing + redaction gates are still active.
- Adding a new cloud-capable feature means adding one call to
  `privacy.note_call(...)` — the rest is handled.
- The audit log gives us something to point at during a security review
  without ever having to promise "we don't store your data" — we can
  demonstrate that we *can't* store it at the source.
- Bedrock's `invoke` originally skipped this pipeline; the Session-7
  hardening pass fixed that. Every new provider adapter must go through
  `prepare_for_cloud()` → `audit_cloud_call()` → `restore()`.

## Alternatives considered

- **Always-local, no cloud ever.** Rejected: the hosted tier needs cloud
  polish for reports + briefings; a pure-local stance limits the product's
  reach to a technical audience.
- **Single env flag + "trust us" privacy policy.** Rejected as
  insufficient — the whole product category has trained users to distrust
  vendor claims.
- **Homomorphic encryption / TEE.** Out of scope for the first version;
  the redaction approach covers the same threat model at 0.1% of the
  engineering cost.
