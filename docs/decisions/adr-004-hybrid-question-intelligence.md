# ADR-004 — Hybrid Question Intelligence as Primary Architecture

**Status:** Accepted
**Date:** 2026-06-18
**Owner:** Arch

---

## Context

The platform generates interview questions across three domains: written, coding, and SQL. Each domain imposes distinct constraints:

- **Written questions** — corpus wording has intrinsic value; diversity must be preserved.
- **Coding questions** — problem statements are reusable but must be framed within a business context; execution remains language-independent.
- **SQL questions** — generic HR-schema corpus is aligned with generic contexts, but FINTECH / ECOMMERCE / SAAS / HEALTHCARE schemas use different entities, making corpus seed text incompatible.

Cross-cutting requirements:

- High question quality and controlled difficulty across sessions.
- Low duplication over time.
- Deterministic execution for coding and SQL.
- Support for business-specific contexts via `BusinessContext`.
- Future extensibility without replacing the core architecture.

**Pure approaches were insufficient:**

| Approach | Failure Mode |
|---|---|
| Pure retrieval | Limited diversity; constrained question space; no business framing |
| Pure generation | Higher hallucination risk; weaker difficulty calibration; weak duplicate control |
| Retrieval + Enrichment everywhere | SQL business-context corpus entities conflict with target schemas |
| Metadata-only generation everywhere | Loses valuable corpus wording for written and coding questions |

---

## Decision

Adopt a **Hybrid Question Intelligence** architecture that combines retrieval, enrichment, metadata-driven generation, and runtime validation. Pipeline strategy is determined per question type and per business context.

**High-level flow:**

```
Question Request
      ↓
Retrieval (Chroma)
      ↓
Pipeline Strategy Selection
      ↓
Enrichment  OR  Metadata-Only Generation
      ↓
Validation
      ↓
Question
```

**Pipeline ownership:**

| Pipeline | Owner class |
|---|---|
| Written | `WrittenQuestionPipeline` |
| Coding | `CodingQuestionPipeline` |
| SQL | `SQLQuestionPipeline` |

---

## Strategy by Question Type

### Written Questions — Retrieval + Enrichment

- Corpus wording preserved as primary signal.
- Enrichment layer introduces diversity without rewriting intent.
- No execution constraints.

### Coding Questions — Retrieval + Enrichment

- Corpus problem statements reused as structural anchors.
- `BusinessContext` modifies framing only; execution remains domain-independent.

### SQL Questions

#### GENERIC context — Retrieval + Enrichment

- Corpus schema aligned with generic HR model.
- Enrichment improves diversity while preserving structural validity.

#### FINTECH / ECOMMERCE / SAAS / HEALTHCARE — Metadata-Only Generation

```
Retrieval
      ↓
Extract metadata (domains, difficulty, scenario anchor)
      ↓
Generation (seed text discarded)
      ↓
Validation
```

Seed question text is **intentionally discarded**. Only metadata is forwarded to generation. Rationale: corpus entities (employees, salaries) conflict with business-domain entities (transactions, orders, patients), producing wording/SQL mismatches that cannot be corrected post-generation.

---

## Rationale

- Retrieval remains the primary source of structural diversity and difficulty calibration.
- Enrichment preserves corpus value while introducing controlled variation.
- Metadata-only generation is narrowly scoped to contexts where corpus wording is actively harmful.
- Validation is mandatory at all exit points regardless of strategy path.
- `BusinessContext` influences strategy selection without coupling pipeline internals to context logic.

---

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Pure retrieval (Chroma only) | Limited diversity; no business framing; constrained long-term question space |
| Pure LLM generation | Higher hallucination risk; weaker difficulty calibration; weaker duplicate control |
| Retrieval + Enrichment everywhere | SQL business-context corpus entities conflict with domain schemas; wording/schema mismatch risk |
| Metadata-only generation everywhere | Loses valuable corpus wording for written and coding questions unnecessarily |

---

## Consequences

### Positive

- Better diversity than retrieval-only.
- Lower hallucination risk than generation-only.
- Schema-safe SQL generation for business contexts.
- Corpus metadata remains reusable across all contexts.
- Business-context specialization without full pipeline redesign.
- Architecture supports additional contexts without structural change.

### Negative / Risks

- Multiple generation strategies increase implementation surface.
- Additional metadata extraction layer required.
- Pipeline complexity higher than single-strategy approaches.
- Metadata quality becomes a dependency for SQL business-context generation.

---

## Architectural Invariants

- Retrieval remains the primary source of diversity.
- Validation remains mandatory at all exit points.
- SQL business contexts never consume corpus seed text.
- Corpus metadata remains reusable across contexts.
- Pipeline strategy is owned by the pipeline, not the caller.
- `BusinessContext` influences strategy selection.
- `Question` objects are the runtime contract across all paths.

---

## Future Evolution

**Supported without architectural change:**

- Additional `BusinessContext` variants.
- Additional SQL schemas.
- Additional metadata dimensions (e.g., cognitive level, seniority band).
- Improved retrieval signals (re-ranking, hybrid dense/sparse).

**Not required:**

- Replacement of hybrid architecture.
- Elimination of retrieval layer.
- Elimination of validation layer.

---

## Implementation Evidence

- `services/question_intelligence/pipelines/base_llm_question_pipeline.py`
- `services/question_intelligence/pipelines/sql_question_pipeline.py`
- `services/question_intelligence/pipelines/coding_question_pipeline.py`
- `services/question_intelligence/pipelines/written_question_pipeline.py`
- `services/question_intelligence/area_question_builder.py`
- `infrastructure/vector_store/chroma_question_store.py`

---

## Related Documents

- `docs/architecture/question-intelligence.md`
- `docs/architecture/business-context.md`
- `docs/architecture/sql-engine.md`
- `docs/decisions/adr-006-business-context-profiles.md`

---

## Review Trigger

When retrieval coverage exceeds 90% of question-area needs, or when a new question domain is introduced that cannot be mapped to an existing pipeline strategy.
