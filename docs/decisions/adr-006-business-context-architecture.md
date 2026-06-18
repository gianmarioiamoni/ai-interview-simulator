# ADR-006 — BusinessContext as Canonical Domain Classification

**Status:** Accepted
**Date:** 2026-06-18
**Owner:** Domain

---

## Context

Prior to this decision:

- `company_description` existed only as raw prompt context injected into LLM calls.
- SQL generation relied on a single generic HR schema regardless of industry.
- Coding question generation had no domain-specific behavior.
- No canonical domain classification existed anywhere in the system.

This produced four compounding problems:

- Domain personalization was inconsistent across question generators.
- SQL schemas could not vary by industry; all companies received the same table layout.
- Coding scenarios were generic and not aligned to the candidate's business context.
- Future vertical expansion (FINTECH, HEALTHCARE, etc.) had no stable abstraction to extend.

---

## Decision

Introduce `BusinessContext` as a first-class domain contract resolved once per interview.

`BusinessContext` is:

- classified from `company_description` exactly once at session start.
- stored immutably in `InterviewContextProfile`.
- consumed by generators exclusively through registries.
- the single source of truth for all domain-specific branching.

Supported values:

```
GENERIC | FINTECH | ECOMMERCE | SAAS | HEALTHCARE
```

Resolution and consumption flow:

```
Company Description
        ↓
BusinessContext  (classified once)
        ↓
InterviewContextProfile  (stored immutably)
        ↓
Registry lookup
        ↓
Context-specific assets
```

Two registries consume `BusinessContext`:

| Registry | Purpose |
|---|---|
| `SchemaRegistry` | Returns the SQL schema for the matching context |
| `CodingDomainProfileRegistry` | Returns coding scenarios, vocabulary, and constraints |

Unknown or unclassifiable descriptions fall back to `GENERIC`.

---

## Rationale

A single classification point eliminates divergence between generators. Storing the result in `InterviewContextProfile` makes it available to all downstream components without re-derivation. Registry-based lookup enforces the open/closed principle: adding a new context requires only extending the enum and adding registry entries, not modifying generator logic.

Prompt-only approaches were rejected because they produce non-deterministic routing and cannot be tested in isolation.

---

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Use `company_description` directly in prompts only | Non-deterministic routing; no testable classification contract; difficult vertical expansion |
| Derive context inside each generator independently | Multiple classification points; inconsistency risk; violates single source of truth |
| Configurable taxonomy / weighted ontology system | Unnecessary complexity for a small, stable context set; enum model is sufficient |

---

## Consequences

### Positive

- Deterministic domain classification with a single classification call.
- SQL schema specialization per industry context.
- Coding scenario specialization per industry context.
- Centralized extension model: new contexts added in one enum and two registries.
- Generators contain no domain-derivation logic; behavior is fully registry-driven.
- `company_description` is preserved as immutable raw input.

### Negative / Risks

- Classifier quality determines correctness of all downstream specialization.
- New contexts require registry assets in both `SchemaRegistry` and `CodingDomainProfileRegistry`.
- Enum-based approach scales only to a moderate number of contexts; a large taxonomy would require a different model.

---

## Architectural Invariants

- `BusinessContext` is resolved exactly once per session.
- `BusinessContext` is stored in `InterviewContextProfile` and must not be re-derived downstream.
- `SchemaRegistry` and `CodingDomainProfileRegistry` are the sole sources of truth for context-specific assets.
- Unresolved or unknown classifications fall back to `GENERIC`; no exception is raised.
- Generators must not derive `BusinessContext` internally.
- `company_description` is preserved as raw input and is not mutated by classification.
- SQL and Coding generators consume `BusinessContext` through registries only, never through prompt heuristics.

---

## Future Evolution

Supported without architectural change:

- Additional `BusinessContext` enum values.
- Additional SQL schemas in `SchemaRegistry`.
- Additional `CodingDomainProfile` entries.

Not required currently:

- Taxonomy registry or configuration-driven context model.
- Weighted ontology classification.
- Multi-context classification per session.

---

## Implementation Evidence

- `domain/contracts/business_context.py`
- `domain/contracts/interview/interview_context_profile.py`
- `services/sql_engine/schema_registry.py`
- `services/question_intelligence/coding_domain_profile_registry.py`

---

## Review Trigger

Addition of a new `BusinessContext` value, or growth beyond eight distinct contexts requiring a taxonomy model.

---

## Related Documents

- `docs/architecture/business-context.md`
- `docs/architecture/question-intelligence.md`
- `docs/decisions/adr-006-business-context-profiles.md`
