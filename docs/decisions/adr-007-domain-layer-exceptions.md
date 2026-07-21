# ADR-007 — Domain Layer Boundary Exceptions

**Status:** Superseded (Resolved)
**Date:** 2026-06-18
**Resolved:** 2026-07-22 (V1.3 Maintainability Remediation)
**Owner:** Domain

---

## Context

Strict hexagonal/clean architecture requires the domain layer to be free of
`services/`, `app/`, and `infrastructure/` imports. Historical exceptions existed
in InterviewState and related question contracts (TD-DL-001).

## Decision

No domain → outer-layer import exceptions are permitted.

Canonical contract types used by InterviewState / question bank models live under
`domain/contracts/`. Former outer-layer modules may re-export for compatibility
only.

## Rationale

Layer separation and coupling maintainability scores were blocked by confirmed
domain → outer imports. Moving pure contracts into domain restores Dependency
Inversion without changing runtime behavior.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Keep intentional exceptions (ADR-007 Proposed) | Blocks Maintainability Certification (layer separation / coupling) |
| Flatten domain into services | Violates ARC-01 ownership and Ownership Matrix |

## Consequences

### Positive
- Domain isolatable and testable without outer-layer imports
- Enforced by `tests/infrastructure/architecture/test_domain_layer_isolation.py`

### Negative / Risks
- Thin compatibility re-exports remain at prior service/app paths (temporary)

## Implementation Evidence

- `domain/contracts/question/interview_retrieval_memory.py`
- `domain/contracts/question/ingestion_metadata.py`
- `domain/contracts/interview/interview_stage.py`
- `domain/contracts/interview/loader_step.py`
- `domain/contracts/interview/follow_up_limits.py`
- `domain/contracts/interview/business_context_constants.py`
- TD-DL-001 **CLOSED**

## Review Trigger

Any new domain import of `services/`, `app/`, or `infrastructure/` fails AT gate.
