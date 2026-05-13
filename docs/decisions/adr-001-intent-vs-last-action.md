# /docs/decisions/adr-001-intent-vs-last-action.md

# ADR-001 — Intent vs Last Action

# Status

Accepted

---

# Decision

Use:

state.intent

as orchestration driver instead of:

state.last_action

---

# Context

last_action mixed:
- runtime semantics
- UI state
- historical state

This caused:
- stale transitions
- loader desynchronization
- ambiguous routing

---

# Consequences

Benefits:
- cleaner graph routing
- semantic orchestration
- clearer runtime flow
- deterministic transitions

---

# Tradeoffs

Introduced:
- explicit intent reset logic
- stronger state discipline

Accepted intentionally.