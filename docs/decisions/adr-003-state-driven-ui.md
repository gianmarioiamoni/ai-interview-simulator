# /docs/decisions/adr-003-state-driven-ui.md

# ADR-003 — State-Driven UI

# Status

Accepted

---

# Decision

The UI must derive entirely from InterviewState.

The UI must never own orchestration logic.

---

# Consequences

The graph becomes:
- orchestration owner
- runtime authority

The UI becomes:
- rendering layer
- intent trigger layer

---

# Benefits

- deterministic rendering
- cleaner orchestration
- easier debugging
- safer runtime transitions

---

# Important Invariants

- loaders derive from state
- buttons derive from allowed_actions
- UI states derive from state machine
- graph owns transitions