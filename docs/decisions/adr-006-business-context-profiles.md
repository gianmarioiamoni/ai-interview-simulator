# ADR-006 — Business-Context Profiles via Parallel Registries

**Status:** Proposed
**Date:** 2026-06-18
**Owner:** Services

---

## Context

<!-- TODO: Coding and SQL questions need domain-specific vocabulary, schemas, scenarios -->

## Decision

<!-- TODO: Two parallel registries keyed by BusinessContext: CodingDomainProfileRegistry + SchemaRegistry -->

## Rationale

<!-- TODO -->

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Single merged registry | |
| Config file per context | |

## Consequences

### Positive
-

### Negative / Risks
- Extension requires touching both registries separately

## Implementation Evidence

- `services/question_intelligence/coding_domain_profile_registry.py`
- `services/sql_engine/schema_registry.py`
- `domain/contracts/interview/interview_area.py`

## Related Documents

- `docs/architecture/business-context.md`
- `docs/architecture/sql-engine.md`
- `docs/architecture/coding-engine.md`
- `docs/decisions/adr-004-hybrid-question-intelligence.md`

## Review Trigger

Addition of new `BusinessContext` value.
