# ADR-013 — Partial Adapter Registry

**Status:** Proposed
**Date:** 2026-06-18
**Owner:** Services

---

## Context

<!-- TODO: 10+ dataset adapters exist; AdapterRegistry only registers 3.
Remaining adapters are used directly without registry. -->

## Decision

<!-- TODO: Document intentional registry scope; define which adapters must be registered -->

## Rationale

<!-- TODO: Registry created for extensibility; partial registration is pragmatic for V1 -->

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Register all adapters | |
| Remove registry, use direct imports | |

## Consequences

### Positive
-

### Negative / Risks
- Inconsistent adapter discovery pattern
- New contributors may bypass registry

## Implementation Evidence

- `services/question_ingestion/adapters/adapter_registry.py` — 3 registered
- `services/question_ingestion/adapters/` — 10+ adapter files

## Review Trigger

All adapters migrated to registry (target: V1.1).
