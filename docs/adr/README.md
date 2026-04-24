# Architecture Decision Records

One file per major decision that would puzzle a future contributor. Short
enough to read in 2 minutes. Format:

```
# ADR NNNN — <title>

**Status:** proposed | accepted | superseded by ADR-X · **Date:** YYYY-MM-DD

## Context
What force pushed us to decide something.

## Decision
What we picked.

## Consequences
What now flows from that choice — good and bad.

## Alternatives considered
What we looked at and why we didn't pick them.
```

Keep existing ADRs immutable. If a decision is reversed, write a new ADR
that supersedes the old one and leaves both in place for history.

## Index

| # | Title                                   | Status   |
|---|-----------------------------------------|----------|
| 0001 | [Four-layer privacy gate](0001-four-layer-privacy-gate.md)   | accepted |
| 0002 | [Agents as named personas](0002-agents-as-named-personas.md) | accepted |
