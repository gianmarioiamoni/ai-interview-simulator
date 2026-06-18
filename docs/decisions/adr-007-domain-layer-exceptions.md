# ADR-007 — Domain Layer Boundary Exceptions

**Status:** Proposed
**Date:** 2026-06-18
**Owner:** Domain

---

## Context

<!-- TODO: Strict hexagonal/clean architecture requires domain to be framework-free.
Observed violations: domain/contracts imports services/ and app/ -->

## Decision

<!-- TODO: Document which imports are intentional exceptions and which are accidental coupling -->

## Rationale

<!-- TODO: Pragmatic decision vs full refactor cost -->

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Full domain isolation (no service imports) | |
| Flatten domain into services | |

## Consequences

### Positive
-

### Negative / Risks
- Domain tests require mocking service layer
- Clean Architecture invariant broken in 3+ files

## Implementation Evidence

- `domain/contracts/interview_state/base.py` — imports `services/`, `app/`
- `domain/contracts/question/question_bank_item.py` — imports `services.question_ingestion`
- `domain/contracts/question/question_runtime_lineage.py` — imports `services.interview_selection`

## Review Trigger

Domain refactor or violation count increases beyond 5 files.
