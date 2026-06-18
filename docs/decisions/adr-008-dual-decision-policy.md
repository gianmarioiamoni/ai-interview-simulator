# ADR-008 — Two DecisionPolicy Concepts

**Status:** Proposed
**Date:** 2026-06-18
**Owner:** Domain

---

## Context

<!-- TODO: Two distinct policies share the name "DecisionPolicy":
1. domain/policies/decision_policy.py — retry/next question logic
2. services/decision_engine/decision_policy.py — hire/no-hire scoring gates -->

## Decision

<!-- TODO: Document intentional separation; define naming contract going forward -->

## Rationale

<!-- TODO -->

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Merge into single policy | |
| Rename one | |

## Consequences

### Positive
-

### Negative / Risks
- Cognitive confusion for contributors
- Risk of wrong policy being referenced

## Implementation Evidence

- `domain/policies/decision_policy.py`
- `services/decision_engine/decision_policy.py`

## Review Trigger

Naming conflict causes a bug or test failure.
