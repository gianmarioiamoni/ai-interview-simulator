# ADR-010 — Humanizer Follow-Up System

**Status:** Proposed
**Date:** 2026-06-18
**Owner:** Services

---

## Context

<!-- TODO: Bare question delivery feels robotic; follow-up probing increases realism -->

## Decision

<!-- TODO: enable_humanizer flag (default True); max 2 follow-ups per question;
HumanizerPolicyEngine governs eligibility -->

## Rationale

<!-- TODO -->

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Always generate follow-ups | |
| User-configured follow-up count | |

## Consequences

### Positive
-

### Negative / Risks
- LangGraph follow-up wiring deferred to V1.1 per operational status

## Implementation Evidence

- `domain/contracts/interview_state/base.py` — `enable_humanizer: bool = True`
- `services/humanizer/humanizer_policy_engine.py`

## Review Trigger

V1.1 follow-up wiring completion.
