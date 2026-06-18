# ADR-012 — Prompt Centralization

**Status:** Proposed
**Date:** 2026-06-18
**Owner:** Services

---

## Context

<!-- TODO: Prompts were inline strings scattered across service files (pre-R-series refactors) -->

## Decision

<!-- TODO: All prompts live in app/prompts/; loaded via PromptLoader; services reference by key -->

## Rationale

<!-- TODO: Testability, reuse, prompt engineering iteration without service changes -->

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Inline prompt strings | |
| External prompt registry service | |

## Consequences

### Positive
-

### Negative / Risks
- Prompt key mismatches are runtime errors

## Implementation Evidence

- `app/prompts/`
- PromptLoader (centralized loader)
- Completed per OPERATIONAL_PROJECT_STATUS.md R-series refactors

## Review Trigger

Prompt format versioning need arises.
