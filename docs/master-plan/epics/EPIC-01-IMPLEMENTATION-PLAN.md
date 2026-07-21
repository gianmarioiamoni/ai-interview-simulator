# EPIC-01 — Implementation Plan

**Status:** ACCEPTED — Implementation COMPLETE (Phases 1–7C); EPIC CLOSED  
**Date:** 2026-07-05  
**Close-out sync:** 2026-07-22 — living status aligned at Release Documentation Synchronization  
**Revision:** 2026-07-05 — Phases 7+8 (previously atomic) replaced with bridge-based sequence 7A→7B→7C to satisfy engineering rule: "Zero Known Failing Tests per phase/commit."  
**Precondition:** Architecture Freeze passed (`EPIC-01-ARCHITECTURE-FREEZE.md`). No new architectural decisions permitted.  
**Authority:** This document translates the frozen architecture into an executable implementation roadmap. All decisions reference ADR-033, EPIC-01-DOMAIN-CONTRACTS.md, and EPIC-01-DATA-MODEL.md.  
**Living Overview:** `EPIC-01-OVERVIEW.md`

---

## Engineering Rule (adopted post-freeze)

> **Zero Known Failing Tests:** Every phase, every commit, every save-token must leave the complete regression suite green. No phase may intentionally introduce known failing tests or broken runtime behaviour. Bridge phases must be used where needed.

---

## Implementation Owner

**EPIC-V13-01** owns Phases 1–7C (domain layer, pipeline, state migration).  
**EPIC-V13-05** owns Phases 8–10 (presentation layer, DTO rebuild, new sections).

> Phase numbering: original Phases 9–11 are renumbered 8–10 following the split of the former atomic Phase 7+8 into 7A, 7B, 7C.

Each phase is independently completable and testable. No phase should be merged with an incomplete test suite.

---

## Phase 1 — New Domain Value Types

### Objective

Define the three new leaf value types required by all subsequent phases. No existing code is modified. This phase has zero regression risk.

### Production Files — Create

| File | Content |
|------|---------|
| `domain/contracts/report/scoring_dimension.py` | `ScoringDimension(BaseModel, frozen=True)` — fields: `dimension_type: PerformanceDimensionType`, `score: float`, `signal: float`, `weighted_contribution: float`, `justification: str`, `level: str` |
| `domain/contracts/report/scoring_narrative_item.py` | `ScoringNarrativeItem(BaseModel, frozen=True)` — fields: `category: str`, `description: str`, `why_it_matters: str`, `context_detail: str | None` |
| `domain/contracts/interview/generation_metadata.py` | `GenerationMetadata(BaseModel, frozen=True)` — fields: `total_tokens_used: int`, `total_cost_usd: float | None`, `cost_per_question_usd: float | None`, `schema_version: str = "1.0"` |

### Domain Contracts Involved

ADR-033 Decision 1 (`ScoringDimension`), Decision 3 (`ScoringNarrativeItem`), DATA-MODEL §1 (`GenerationMetadata`).

### Builders Involved

None — value types only; no builders in this phase.

### Prerequisites

None.

### Implementation Order

1. `ScoringDimension` (leaf; no dependencies on new artifacts)
2. `ScoringNarrativeItem` (leaf)
3. `GenerationMetadata` (leaf)

### Expected Behavioural Changes

None — new files only; no existing code modified.

### Regression Risks

None.

### Required Tests

- `tests/domain/contracts/report/test_scoring_dimension.py` — construct, validate constraints, freeze immutability
- `tests/domain/contracts/report/test_scoring_narrative_item.py` — construct, `context_detail` optional
- `tests/domain/contracts/interview/test_generation_metadata.py` — construct, optional cost fields

### Completion Checklist

- [ ] All three files created
- [ ] All `frozen=True`, `extra="forbid"`
- [ ] Unit tests pass for all three
- [ ] No existing test broken

### Commit boundary

`feat(domain): add ScoringDimension, ScoringNarrativeItem, GenerationMetadata value types`

---

## Phase 2 — `ScoringSnapshot` Contract

### Objective

Define `ScoringSnapshot` and `ScoringSnapshotBuilder`. This is the canonical scoring artifact that replaces the scoring fields of `InterviewEvaluation`.

### Production Files — Create

| File | Content |
|------|---------|
| `domain/contracts/report/scoring_snapshot.py` | `ScoringSnapshot(BaseModel, frozen=True)` — full field set per DATA-MODEL §2 and DOMAIN-CONTRACTS §1 |
| `domain/contracts/report/scoring_snapshot_builder.py` | `ScoringSnapshotBuilder` — accepts individual fields; `build()` derives `dimension_scores`, `dimension_signals`, `weighted_breakdown` dicts from `scoring_dimensions` tuple (R-12); validates V-SS-01 through V-SS-04 |

### Domain Contracts Involved

DATA-MODEL §2 (supersedes DOMAIN-CONTRACTS §1 on dimensions). DOMAIN-CONTRACTS §1 validation invariants V-SS-01–V-SS-04.

### Prerequisites

Phase 1 complete (`ScoringDimension` and `Confidence` available).

### Implementation Order

1. `scoring_snapshot.py` — define all fields; `scoring_dimensions: tuple[ScoringDimension, ...]`; three dict fields with `@model_validator(mode="after")` to verify R-12 consistency
2. `scoring_snapshot_builder.py` — builder that accepts `scoring_dimensions` and scoring fields; `build()` derives dicts from `scoring_dimensions` before constructing

### Expected Behavioural Changes

None — new files only.

### Regression Risks

None.

### Required Tests

- `tests/domain/contracts/report/test_scoring_snapshot.py` — construct valid snapshot; validate V-SS-01 (gating), V-SS-02 (non-empty dimensions), V-SS-04 (dict key parity); freeze; builder round-trip

### Completion Checklist

- [ ] `ScoringSnapshot` and `ScoringSnapshotBuilder` created
- [ ] Dict fields derived from `scoring_dimensions` in validator
- [ ] All four validation invariants enforced
- [ ] Unit tests pass
- [ ] No existing test broken

### Commit boundary

`feat(domain): add ScoringSnapshot and ScoringSnapshotBuilder`

---

## Phase 3 — `ScoringNarrative` Contract

### Objective

Define `ScoringNarrative`. This carries all LLM-generated report prose previously on `InterviewEvaluation`.

### Production Files — Create

| File | Content |
|------|---------|
| `domain/contracts/report/scoring_narrative.py` | `ScoringNarrative(BaseModel, frozen=True)` — fields: `executive_summary: str`, `went_well: tuple[str, ...]`, `held_you_back: tuple[ScoringNarrativeItem, ...]`, `knowledge_gaps: tuple[ScoringNarrativeItem, ...]`, `next_strategy: tuple[ScoringNarrativeItem, ...]`, `improvement_suggestions: tuple[str, ...]`, `schema_version: str = "1.0"` |

### Domain Contracts Involved

DOMAIN-CONTRACTS §2. Validation invariants V-SN-01–V-SN-03.

### Prerequisites

Phase 1 complete (`ScoringNarrativeItem` available).

### Implementation Order

1. `scoring_narrative.py` — define fields; validate V-SN-01 (`executive_summary` non-empty); validate V-SN-02 (each item's required fields non-empty)

### Expected Behavioural Changes

None — new file only.

### Regression Risks

None.

### Required Tests

- `tests/domain/contracts/report/test_scoring_narrative.py` — construct with all sections; validate V-SN-01/02/03; empty tuples permitted for optional sections; freeze

### Completion Checklist

- [ ] `ScoringNarrative` created
- [ ] All three validation invariants enforced
- [ ] Unit tests pass
- [ ] No existing test broken

### Commit boundary

`feat(domain): add ScoringNarrative contract`

---

## Phase 4 — `QuestionResultRecord` Contract

### Objective

Define `QuestionResultRecord` — the closure-time persistence record for per-question data.

### Production Files — Create

| File | Content |
|------|---------|
| `domain/contracts/session_history/question_result_record.py` | `QuestionResultRecord(BaseModel, frozen=True)` — full field set per DOMAIN-CONTRACTS §3 and DATA-MODEL §3 |

### Domain Contracts Involved

DOMAIN-CONTRACTS §3. DATA-MODEL §3 (immutable fields, serialization rules). Validation invariants V-QRR-01–V-QRR-03.

### Prerequisites

None (leaf type — no new type dependencies).

### Implementation Order

1. `question_result_record.py` — define all fields; validate V-QRR-01 (coding test pair), V-QRR-02 (passed_tests ≤ total_tests), V-QRR-03 (hint pair)

### Expected Behavioural Changes

None — new file only.

### Regression Risks

None.

### Required Tests

- `tests/domain/contracts/session_history/test_question_result_record.py` — construct for written and coding questions; validate coding invariants; validate hint pair; freeze

### Completion Checklist

- [ ] `QuestionResultRecord` created
- [ ] All three validation invariants enforced
- [ ] Full `question_prompt` stored (not truncated) — no max_length on `question_prompt`
- [ ] Unit tests pass
- [ ] No existing test broken

### Commit boundary

`feat(domain): add QuestionResultRecord contract`

---

## Phase 5 — `Narrative.executive_summary` Rename

### Objective

Rename `Narrative.executive_summary` → `Narrative.overview_section` to eliminate the naming collision with `ScoringNarrative.executive_summary` (Architecture Freeze Finding 4.2 + DOMAIN-CONTRACTS §8 + Rule R-07).

### Production Files — Modify

| File | Change |
|------|--------|
| `domain/contracts/narrative/narrative.py` | Rename field `executive_summary` → `overview_section`; update `_section_type_invariant` validator |
| `services/narrative_generator/narrative_generator.py` | Update construction to use `overview_section=` kwarg |
| Any other file constructing `Narrative(executive_summary=...)` | Update to `overview_section=` |

### Domain Contracts Involved

DOMAIN-CONTRACTS §8. Rule R-07.

### Prerequisites

None — rename only; does not depend on new artifacts.

### Implementation Order

1. Rename field in `narrative.py`; update validator
2. Update `narrative_generator.py`
3. Search and update all remaining `Narrative(executive_summary=` construction call sites
4. Update all test fixtures constructing `Narrative` with `executive_summary=`

### Expected Behavioural Changes

- `Narrative.executive_summary` attribute access raises `AttributeError` after rename
- `Narrative.overview_section` returns the same data

### Regression Risks

**High** — any test or code accessing `narrative.executive_summary` will break. All must be updated in the same commit.

### Required Architectural Tests

- `tests/domain/contracts/narrative/test_narrative_contracts.py` — assert `overview_section` exists; assert `executive_summary` attribute does not exist

### Required Tests (update existing)

- `tests/domain/contracts/narrative/test_narrative_contracts.py` — update fixture construction
- `tests/services/narrative_generator/test_narrative_generator_architecture.py` — update assertions

### Completion Checklist

- [ ] `Narrative.overview_section` field exists
- [ ] `Narrative.executive_summary` field does not exist
- [ ] All construction call sites updated
- [ ] All test fixtures updated
- [ ] All existing narrative tests pass

### Commit boundary

`refactor(domain): rename Narrative.executive_summary to overview_section`

---

## Phase 6 — `InterviewEvaluationService` Refactor

### Objective

Refactor `InterviewEvaluationService.evaluate(...)` to return `tuple[ScoringSnapshot, ScoringNarrative]` instead of `InterviewEvaluation`. This is the core scoring pipeline migration.

### Production Files — Modify

| File | Change |
|------|--------|
| `services/interview_evaluation_service.py` | Change return type from `InterviewEvaluation` to `tuple[ScoringSnapshot, ScoringNarrative]`; use `ScoringSnapshotBuilder` and `ScoringNarrative` construction internally |
| `services/interview_evaluation/assemblers/evaluation_narrative_assembler.py` | Refactor to return `ScoringNarrative` instead of dict; populate `ScoringNarrativeItem` objects for `held_you_back`, `knowledge_gaps`, `next_strategy` |

### Domain Contracts Involved

`ScoringSnapshot`, `ScoringNarrative`, `ScoringDimension`. ADR-033 Decision 1 + 3.

### Builders Involved

`ScoringSnapshotBuilder`

### Prerequisites

Phase 2 (`ScoringSnapshot`), Phase 3 (`ScoringNarrative`), Phase 1 (`ScoringDimension`, `ScoringNarrativeItem`).

### Implementation Order

1. Refactor `EvaluationNarrativeAssembler.assemble(...)` → returns `ScoringNarrative`
2. Refactor `InterviewEvaluationService.evaluate(...)` → uses `ScoringSnapshotBuilder`; assembles `ScoringDimension` per dimension; returns `(ScoringSnapshot, ScoringNarrative)`
3. Update `tests/services/test_interview_evaluation_service.py` — assert return type is tuple

### Expected Behavioural Changes

- `InterviewEvaluationService.evaluate(...)` now returns `(ScoringSnapshot, ScoringNarrative)` — any caller that expected `InterviewEvaluation` will break at this point (addressed in Phase 7)

### Regression Risks

**High** — `EvaluationAggregateNode` still expects `InterviewEvaluation`. Phase 7 must follow immediately.

### Required Tests

- `tests/services/test_interview_evaluation_service.py` — assert `(ScoringSnapshot, ScoringNarrative)` returned; assert field parity with previous `InterviewEvaluation` field values
- `tests/services/interview_evaluation/test_evaluation_narrative_assembler.py` (new) — assert `ScoringNarrative` returned; `ScoringNarrativeItem` constructed for each coaching section

### Completion Checklist

- [ ] `evaluate(...)` returns `(ScoringSnapshot, ScoringNarrative)`
- [ ] `ScoringDimension` constructed per dimension with `justification` from assembler
- [ ] Dict fields derived correctly in `ScoringSnapshotBuilder.build()`
- [ ] Unit tests pass for both service and assembler

### Commit boundary

`refactor(services): InterviewEvaluationService returns ScoringSnapshot + ScoringNarrative`

---

## Phase 7A — `InterviewState` Extension (Bridge) [TRANSITION]

> **Bridge phase.** Adds new fields to `InterviewState` **without removing** `interview_evaluation`. `EvaluationAggregateNode` updated to call `evaluate_scoring()` and write both old and new fields. Runtime and full suite stay green.

### Objective

Extend `InterviewState` with `scoring_snapshot` and `scoring_narrative`; update `EvaluationAggregateNode` to populate them via `evaluate_scoring()` while also writing `interview_evaluation` via `evaluate()` (bridge). All downstream readers of `interview_evaluation` continue working.

### Production Files — Modify

| File | Change |
|------|--------|
| `domain/contracts/interview_state/base.py` | Add `scoring_snapshot: ScoringSnapshot \| None = None`; add `scoring_narrative: ScoringNarrative \| None = None`; **keep** `interview_evaluation: Optional[InterviewEvaluation]` |
| `app/graph/nodes/evaluation_aggregate_node.py` | Call `evaluate_scoring()` to get `(scoring_snapshot, scoring_narrative)`; call `evaluate()` for `interview_evaluation`; update idempotency guard to check `state.scoring_snapshot is not None`; write all three fields to state |

### Domain Contracts Involved

`ScoringSnapshot`, `ScoringNarrative`, `InterviewState`. Rule R-08.

### Prerequisites

Phase 6 complete.

### Implementation Order

1. Add `scoring_snapshot` and `scoring_narrative` fields to `InterviewStateBase` (`None` default)
2. Update `EvaluationAggregateNode.__call__` — new idempotency guard; call both service methods; write all three state fields
3. Update test fixtures and architectural tests

### Expected Behavioural Changes

- `state.scoring_snapshot` and `state.scoring_narrative` populated after evaluation
- `state.interview_evaluation` still populated — no downstream breakage
- Idempotency guard uses `scoring_snapshot is not None`

### Regression Risks

**Low** — additive only; no field removal. Test fixtures that set `interview_evaluation` continue to work.

### Required Tests

- `tests/domain/contracts/interview_state/test_interview_state_field_invariants.py` — assert `scoring_snapshot` and `scoring_narrative` fields exist; assert `interview_evaluation` still exists
- `tests/graph/nodes/test_evaluation_aggregate_node.py` — assert writes all three fields; assert idempotency on `scoring_snapshot is not None`

### Completion Checklist

- [ ] `scoring_snapshot` and `scoring_narrative` added with `None` default
- [ ] `interview_evaluation` kept (bridge)
- [ ] `EvaluationAggregateNode` writes all three fields
- [ ] Idempotency guard checks `scoring_snapshot`
- [ ] Full suite green

### Commit boundary

`feat(state): add scoring_snapshot and scoring_narrative to InterviewState (bridge)`

---

## Phase 7B — `SessionHistory` Extension (Bridge) [TRANSITION]

> **Bridge phase.** Extends `SessionHistory` and `session_close_node` to carry new fields **alongside** the legacy `evaluation_result`. `session_close_node` reads `state.scoring_snapshot` (available from 7A) and writes both old and new fields. Runtime and full suite stay green.

### Objective

Evolve `SessionHistory` to v1.5 (additive): add `scoring_snapshot`, `scoring_narrative`, `question_results`, `context_profile`, `generation_metadata` while keeping `evaluation_result`. Update `session_close_node` to populate all. Update `SessionCloseContext` accordingly.

### Production Files — Modify

| File | Change |
|------|--------|
| `domain/contracts/session_history/session_history.py` | Add `question_results: tuple[QuestionResultRecord, ...] = ()`; add `scoring_snapshot: ScoringSnapshot \| None = None`; add `scoring_narrative: ScoringNarrative \| None = None`; add `context_profile: InterviewContextProfile \| None = None`; add `generation_metadata: GenerationMetadata \| None = None`; add soft V-SH-01 warning (not enforced yet); **keep** `evaluation_result` |
| `domain/contracts/session_history/session_history_builder.py` | Add `with_question_results`, `with_scoring_snapshot`, `with_scoring_narrative`, `with_context_profile`, `with_generation_metadata`; **keep** `with_evaluation_result` |
| `services/session_close/session_close_context.py` | Add `question_results`, `scoring_snapshot`, `scoring_narrative`, `context_profile`, `generation_metadata` fields alongside `evaluation_result` |
| `services/session_close/session_close_pipeline.py` | Pass all new fields to builder alongside `evaluation_result` |
| `app/graph/nodes/session_close_node.py` | Read `state.scoring_snapshot`, `state.scoring_narrative`, `state.context_profile`; build `QuestionResultRecord` per answered question; build `GenerationMetadata`; pass all to context alongside existing `evaluation_result` path |

### Domain Contracts Involved

`SessionHistory v1.5`, `QuestionResultRecord`, `ScoringSnapshot`, `ScoringNarrative`, `GenerationMetadata`, `InterviewContextProfile`. Rules R-13, R-14, R-15.

### Builders Involved

`SessionHistoryBuilder`

### Prerequisites

Phase 7A complete.

### `QuestionResultRecord` Construction (session_close_node)

For each `Question` in `state.questions` where `state.results_by_question.get(q.id)` is not None:

- `question_id` ← `q.id`
- `question_index` ← loop index
- `question_type` ← `q.type.value`
- `area_label` ← `InterviewAreaMapper.to_label(q.area)`
- `question_prompt` ← `q.prompt` (full, not truncated)
- `score`, `max_score`, `feedback`, `strengths`, `weaknesses`, `follow_up_question` ← `result.evaluation` fields (if evaluation exists)
- `passed_tests`, `total_tests`, `execution_status` ← `result.execution` fields (if execution exists)
- `attempts` ← count of `state.answers` with matching `question_id`
- `ai_hint_explanation`, `ai_hint_suggestion` ← `result.ai_hint` fields (if hint exists)

### Expected Behavioural Changes

- `SessionHistory` now carries both old and new artifacts (dual-write)
- `session_close_node` produces `QuestionResultRecord` and `GenerationMetadata`
- No reader of `evaluation_result` breaks

### Regression Risks

**Low-Medium** — additive only; `evaluation_result` and legacy builder methods kept.

### Required Tests

- `tests/domain/contracts/session_history/test_session_history_contracts.py` — assert new fields present; assert `evaluation_result` still present; assert new builder methods exist
- `tests/app/graph/nodes/test_session_close_node.py` — assert `question_results` populated; assert `scoring_snapshot` embedded; assert `context_profile` embedded

### Completion Checklist

- [ ] New fields added to `SessionHistory` (all optional, no breaking change)
- [ ] `evaluation_result` kept (bridge)
- [ ] Builder extended with new methods; `with_evaluation_result` kept
- [ ] `session_close_node` builds `QuestionResultRecord` and `GenerationMetadata`
- [ ] Full suite green

### Commit boundary

`feat(state): extend SessionHistory v1.5 — add scoring artifacts (bridge)`

---

## Phase 7C — Legacy Cleanup (Removal) [REMOVAL]

> **Removal phase.** Removes `interview_evaluation` from `InterviewState`, removes `evaluation_result` from `SessionHistory`, deletes `InterviewEvaluation` contract, makes `context_profile` required in `SessionHistory`, enforces V-SH-01. Also migrates UI readers away from `interview_evaluation`. Full suite stays green.

### Objective

Complete the migration by removing all bridge fields and the legacy `InterviewEvaluation` artifact. Enforce `SessionHistory` v2.0 invariants. Update all UI readers.

### Production Files — Modify

| File | Change |
|------|--------|
| `domain/contracts/interview_state/base.py` | Remove `interview_evaluation`; remove import of `InterviewEvaluation` |
| `domain/contracts/interview_state/factory.py` | Remove `interview_evaluation=None` init |
| `domain/contracts/session_history/session_history.py` | Remove `evaluation_result`; make `context_profile: InterviewContextProfile` required; enforce V-SH-01 (scoring pair); bump `schema_version` default to `"2.0"` |
| `domain/contracts/session_history/session_history_builder.py` | Remove `with_evaluation_result`; add `context_profile` to mandatory validation; enforce V-SH-01 |
| `services/session_close/session_close_context.py` | Remove `evaluation_result` field |
| `services/session_close/session_close_pipeline.py` | Remove `evaluation_result` path |
| `app/graph/nodes/evaluation_aggregate_node.py` | Remove `evaluate()` call (legacy bridge); keep only `evaluate_scoring()` |
| `app/ui/builders/ui_response_builder.py` | Remove `state.interview_evaluation` read from `_build_report`; gate only on `state.report is not None` |
| `app/ui/mappers/interview_state_mapper.py` | Remove `interview_evaluation` guard; call `FinalReportDTO.from_report(state.report)` (stub — full implementation in Phase 9) |
| `services/interview_evaluation_service.py` | Remove `evaluate()` bridge method; keep only `evaluate_scoring()` and `_compute()` |

### Production Files — Delete

| File |
|------|
| `domain/contracts/interview/interview_evaluation.py` |

### Domain Contracts Involved

`InterviewState`, `SessionHistory v2.0`, `InterviewEvaluation` (deleted). Rule R-08. V-SH-01. R-13.

### Prerequisites

Phase 7B complete.

### Implementation Order

1. Remove `interview_evaluation` from `InterviewStateBase`; update factory
2. Update `EvaluationAggregateNode` — remove legacy `evaluate()` call
3. Remove `evaluation_result` from `SessionHistory`; enforce invariants; bump schema version
4. Remove `with_evaluation_result` from builder; add mandatory `context_profile` validation
5. Update `SessionCloseContext` and `session_close_pipeline`
6. Update `ui_response_builder` and `interview_state_mapper`
7. Remove `evaluate()` bridge from `InterviewEvaluationService`
8. Delete `interview_evaluation.py`
9. Update all test fixtures

### Expected Behavioural Changes

- `state.interview_evaluation` does not exist
- `session_history.evaluation_result` does not exist
- `SessionHistory.schema_version` defaults to `"2.0"`
- `SessionHistory.context_profile` required
- V-SH-01 enforced
- UI readers gate on `state.report` only

### Regression Risks

**High** — removes legacy fields. All 14+ test files that reference `interview_evaluation` or `evaluation_result` must be updated before this phase commits.

### Required Tests

- `tests/domain/contracts/interview_state/test_interview_state_field_invariants.py` — assert `interview_evaluation` does not exist
- `tests/domain/contracts/session_history/test_session_history_contracts.py` — assert `evaluation_result` does not exist; assert V-SH-01 enforced; assert `schema_version` default `"2.0"`
- All previously updated fixtures must continue passing

### Completion Checklist

- [ ] `interview_evaluation` removed from `InterviewState`
- [ ] `interview_evaluation.py` deleted — zero production references
- [ ] `evaluation_result` removed from `SessionHistory`
- [ ] `context_profile` required in `SessionHistory`
- [ ] V-SH-01 enforced in builder
- [ ] `SessionHistory.schema_version` defaults to `"2.0"`
- [ ] `ui_response_builder` no longer reads `interview_evaluation`
- [ ] `evaluate()` bridge removed from `InterviewEvaluationService`
- [ ] Full suite green

### Commit boundary

`refactor(migration): retire InterviewEvaluation — InterviewState + SessionHistory v2.0 cleanup`

---

## Phase 8 — `ReportBuilder` + `Report` Migration

> _(was Phase 9)_

### Objective

Extend `ReportBuilder` and `Report` to carry `scoring`, `scoring_narrative`, `question_assessments`, `context_profile`, and `generation_metadata`. Update `report_node`. Delete `InterviewEvaluation` assembly path from `report_node` (already done; this phase verifies and extends).

### Production Files — Modify

| File | Change |
|------|--------|
| `domain/contracts/report/report.py` | Add `scoring: ScoringSnapshot` (required); add `scoring_narrative: ScoringNarrative` (required); add `question_assessments: tuple[QuestionAssessmentRecord, ...]`; add `context_profile: InterviewContextProfile` (required); add `generation_metadata: GenerationMetadata \| None`; bump `schema_version` default to `"2.0"`; add V-R-01 validator |
| `domain/contracts/report/report_builder.py` | Update `with_session_history` to read `history.scoring_snapshot`, `history.scoring_narrative`, `history.question_results` (→ `QuestionAssessmentRecord`), `history.context_profile`, `history.generation_metadata`; add `with_scoring`, `with_scoring_narrative`, `with_question_assessments`, `with_context_profile`, `with_generation_metadata` setters; update `build()` validation to require `scoring`, `scoring_narrative`, `context_profile`; add V-R-01 (len check) |
| `domain/contracts/report/report_builder.py` | Handle `session_history.scoring_snapshot is None` → `report_node` skips (no change to `report_node`; `ReportBuilder.build()` raises `ValueError` if `scoring` not set; `report_node` catches and logs) |

### Production Files — Create

| File | Content |
|------|---------|
| `domain/contracts/report/question_assessment_record.py` | `QuestionAssessmentRecord(BaseModel, frozen=True)` — identical field set to `QuestionResultRecord`; `schema_version: str = "1.0"`; same validation invariants V-QAR-01 applied at Report build time |

### Domain Contracts Involved

`Report v2.0`, `ReportBuilder`, `QuestionAssessmentRecord`, `ScoringSnapshot`, `ScoringNarrative`. DOMAIN-CONTRACTS §4, §7. DATA-MODEL §7. Validation invariants V-R-01–V-R-03.

### Builders Involved

`ReportBuilder`

### Prerequisites

Phase 7C complete.

### Implementation Order

1. Create `question_assessment_record.py`
2. Update `report.py` — add new fields; add `@model_validator` for V-R-01
3. Update `report_builder.py` — update `with_session_history`; add new setters; update `build()` validation
4. Update `report_node` (if needed) — no functional change; exception handling already present for failed `build()`
5. Update `tests/domain/contracts/report/test_report_contracts.py` — add `scoring`, `scoring_narrative`, `context_profile` to all `Report` fixture constructions; assert V-R-01

### Expected Behavioural Changes

- `Report` is now fully self-contained for report rendering
- `report_node` skips silently when `session_history.scoring_snapshot is None` (existing behaviour via exception handling)
- `ReportBuilder.build()` raises `ValueError` for missing `scoring`, `scoring_narrative`, `context_profile`

### Regression Risks

**Medium** — 7 test files reference `ReportBuilder` or `report_node`. Fixtures must add new required fields.

### Required Architectural Tests

- `tests/domain/contracts/report/test_report_contracts.py` — assert `scoring`, `scoring_narrative`, `question_assessments`, `context_profile` on `Report`; assert V-R-01 enforced; assert `schema_version` default `"2.0"`
- `tests/app/graph/nodes/test_report_node.py` — assert `Report` built with `scoring`; assert skips when `scoring_snapshot is None` in `session_history`

### Completion Checklist

- [ ] `Report.scoring`, `scoring_narrative`, `question_assessments`, `context_profile`, `generation_metadata` exist
- [ ] `Report.schema_version` defaults to `"2.0"`
- [ ] V-R-01 enforced
- [ ] `ReportBuilder.with_session_history` reads all new fields
- [ ] All existing report tests pass with updated fixtures

### Commit boundary

`feat(domain): Report v2.0 — add ScoringSnapshot, ScoringNarrative, QuestionAssessmentRecord`

---

## Phase 9 — `FinalReportDTO` Rebuild (EPIC-V13-05)

> _(was Phase 10)_

### Objective

Replace `FinalReportDTO.from_components(state, evaluation)` with `FinalReportDTO.from_report(report: Report)`. Delete `from_components`. Update all callers.

### Production Files — Modify

| File | Change |
|------|--------|
| `app/ui/dto/final_report_dto.py` | Delete `from_components`; implement `from_report(cls, report: Report) -> FinalReportDTO`; full field mapping per DATA-MODEL §4 |
| `app/ui/dto/builders/dimension_score_mapper.py` | Update signature to accept `tuple[ScoringDimension, ...]`; remove three-parameter signature (R-16) |
| `app/ui/mappers/interview_state_mapper.py` | Complete `to_final_report_dto` — call `FinalReportDTO.from_report(state.report)` |
| `app/ui/builders/ui_response_builder.py` | Complete `_build_report` — call `FinalReportDTO.from_report(state.report)` |
| `app/ui/state_handlers/export_handlers.py` | Update to use `FinalReportDTO.from_report(state.report)` via mapper |
| `app/ui/dto/builders/token_calculator.py` | Remove `calculate(state)` call from report path (R-17); retain for observability use if needed elsewhere |

### Production Files — Create

| File | Content |
|------|---------|
| `app/ui/dto/builders/question_assessment_mapper.py` | `QuestionAssessmentMapper.to_dto(record: QuestionAssessmentRecord) -> QuestionAssessmentDTO` — direct field copy |

### Domain Contracts Involved

`FinalReportDTO`, `ScoringSnapshot`, `ScoringNarrative`, `QuestionAssessmentRecord`. DATA-MODEL §4. Rules R-05, R-16, R-17.

### Prerequisites

Phase 8 complete.

### `from_report` Field Mapping Summary

| `FinalReportDTO` field | Source |
|------------------------|--------|
| `overall_score` | `report.scoring.overall_score` |
| `raw_score` | `report.scoring.raw_score or 0.0` |
| `adjusted_score` | `report.scoring.adjusted_score or report.scoring.overall_score` |
| `hiring_probability` | `report.scoring.hiring_probability` |
| `hire_decision` | `HireDecisionMapper.to_label(report.scoring.hire_decision)` |
| `decision_explanation` | `report.scoring.decision_explanation` |
| `dimension_signals` | `report.scoring.dimension_signals` |
| `percentile_rank` | `report.scoring.percentile_rank` |
| `percentile_explanation` | `report.scoring.percentile_explanation` |
| `executive_summary` | `report.scoring_narrative.executive_summary` |
| `gating_triggered` | `report.scoring.gating_triggered` |
| `gating_reason` | `report.scoring.gating_reason` |
| `weighted_breakdown` | `report.scoring.weighted_breakdown` |
| `dimension_scores` | `DimensionScoreMapper.map(report.scoring.scoring_dimensions)` |
| `question_assessments` | `[QuestionAssessmentMapper.to_dto(r) for r in report.question_assessments]` |
| `improvement_suggestions` | `list(report.scoring_narrative.improvement_suggestions)` |
| `went_well` | `list(report.scoring_narrative.went_well)` |
| `held_you_back` | `[item.to_dict() for item in report.scoring_narrative.held_you_back]` |
| `knowledge_gaps` | `[item.to_dict() for item in report.scoring_narrative.knowledge_gaps]` |
| `next_strategy` | `[item.to_dict() for item in report.scoring_narrative.next_strategy]` |
| `total_tokens_used` | `report.generation_metadata.total_tokens_used if report.generation_metadata else 0` |
| `confidence` | `report.scoring.confidence` |
| `role` | `RoleType(report.role)` |
| `seniority_level` | `report.seniority` |
| `context_profile` | `report.context_profile` |

### Renderer Dict Key Update (Finding 1.5 from Architecture Freeze)

`render_held_you_back`, `render_knowledge_gaps`, `render_next_strategy` currently read section-specific dict keys. After migration, `ScoringNarrativeItem.to_dict()` returns `{"category": ..., "description": ..., "why_it_matters": ..., "context_detail": ...}`. These three renderer functions must be updated to read `context_detail` instead of `impact`, `interview_impact`, `expected_improvement`.

| Renderer | Old key | New key |
|----------|---------|---------|
| `render_held_you_back` | `impact` | `context_detail` |
| `render_knowledge_gaps` | `interview_impact` | `context_detail` |
| `render_next_strategy` | `expected_improvement` | `context_detail` |

### Expected Behavioural Changes

- Report renders identically from `Report` data (regression baseline must confirm)
- `FinalReportDTO.from_components` does not exist
- PDF and JSON exports now source from `Report`

### Regression Risks

**High** — 3 test files reference `FinalReportDTO` or `from_components`; must be updated. Renderer key change breaks `render_held_you_back`, `render_knowledge_gaps`, `render_next_strategy` if not updated simultaneously.

### Required Architectural Tests

- `tests/ui/mappers/test_final_report_dto.py` (new) — assert `from_report` maps all fields; assert `from_components` does not exist; assert field-level values match expected from `Report` fixture
- `tests/ui/builders/test_ui_response_builder_completion.py` — update fixture; assert report HTML generated from `state.report` only
- `tests/ui/mappers/test_interview_state_mapper.py` — update; assert `interview_evaluation` not accessed

### Completion Checklist

- [ ] `FinalReportDTO.from_components` does not exist
- [ ] `FinalReportDTO.from_report(report)` exists
- [ ] `DimensionScoreMapper.map(...)` accepts `tuple[ScoringDimension, ...]` only
- [ ] Three renderers updated to read `context_detail`
- [ ] `QuestionAssessmentMapper` created
- [ ] All three export paths use `from_report`
- [ ] All affected tests pass
- [ ] Zero references to `interview_evaluation` in `app/ui/` directory

### Commit boundary

`feat(presentation): FinalReportDTO.from_report — retire from_components (EPIC-V13-05 Phase 1-2)`

---

## Phase 10 — New Report Sections (EPIC-V13-05 Phase 3)

> _(was Phase 11)_

### Objective

Add narrative insights panel and coaching objectives panel to the Unified Report.

### Production Files — Create

| File | Content |
|------|---------|
| `app/ui/views/report/sections/narrative_section.py` | `render_narrative(vm)` — renders `NarrativeInsight` list |
| `app/ui/views/report/sections/coaching_section.py` | `render_coaching_objectives(vm)` — renders `CoachingSnapshot` objectives |
| `app/ui/views/report/sections/study_recommendations_section.py` | `render_study_recommendations(vm)` — renders `StudyRecommendation` list |

### Production Files — Modify

| File | Change |
|------|--------|
| `app/ui/views/report/report_view_model_builder.py` | Add `narrative_insights` and `coaching_objectives` VM keys from `report.narrative.insights` and `report.coaching_snapshot` |
| `app/ui/views/report/report_renderer.py` | Call new renderers in section order |
| `app/ui/dto/final_report_dto.py` | Add `narrative_insights: List[NarrativeInsightDTO]` and `coaching_objectives: List[CoachingObjectiveDTO]` fields (Optional, default empty); add `NarrativeInsightDTO` and `CoachingObjectiveDTO` DTO types |

### Prerequisites

Phase 9 complete.

### Expected Behavioural Changes

- Two new sections appear in report HTML
- Existing sections unchanged

### Regression Risks

Low — additive only.

### Required Tests

- `tests/ui/views/report/test_narrative_section.py` — construct with `NarrativeInsight` list; verify prose rendered
- `tests/ui/views/report/test_coaching_section.py` — construct with `CoachingSnapshot`; verify objective rendered

### Completion Checklist

- [ ] `render_narrative`, `render_coaching_objectives`, `render_study_recommendations` implemented
- [ ] VM builder populates `narrative_insights` and `coaching_objectives`
- [ ] `FinalReportDTO` carries new optional fields
- [ ] All new section tests pass
- [ ] No regression in existing sections

### Commit boundary

`feat(ui): add narrative insights and coaching objectives sections to Unified Report`

---

## Estimated Implementation Sequence

```
Phase 1  ──┐
Phase 4  ──┤─── no dependencies; can run in parallel
Phase 5  ──┘

Phase 2  ─── depends on Phase 1 (ScoringDimension)
Phase 3  ─── depends on Phase 1 (ScoringNarrativeItem)

Phase 6  ─── depends on Phase 2 + Phase 3

Phase 7A ─── depends on Phase 6 + Phase 4 + Phase 5    [bridge: additive InterviewState]
Phase 7B ─── depends on Phase 7A                        [bridge: additive SessionHistory]
Phase 7C ─── depends on Phase 7B                        [removal: retire InterviewEvaluation]

Phase 8  ─── depends on Phase 7C

Phase 9  ─── depends on Phase 8

Phase 10 ─── depends on Phase 9
```

**Critical path:** 1 → 2 → 6 → 7A → 7B → 7C → 8 → 9 → 10  
(Phase 3 runs in parallel with Phase 2; Phases 4 and 5 run in parallel with Phases 1–3)

---

## Parallelizable Work

| Parallel track A | Parallel track B |
|-----------------|-----------------|
| Phase 1 → Phase 2 → Phase 6 | Phase 4 (QuestionResultRecord) |
| | Phase 5 (Narrative rename) |
| | Phase 3 (ScoringNarrative) — after Phase 1 |

Phases 3, 4, and 5 can all be developed against their prerequisites independently of the scoring pipeline track.

---

## Critical Path

1. `ScoringDimension` (Phase 1) must exist before `ScoringSnapshot` (Phase 2)
2. `ScoringSnapshotBuilder` (Phase 2) must exist before `InterviewEvaluationService` refactor (Phase 6)
3. Service refactor (Phase 6) must exist before `InterviewState` extension (Phase 7A)
4. Phase 7A must exist before Phase 7B (new state fields needed by `session_close_node`)
5. Phase 7B must exist before Phase 7C (new `SessionHistory` fields must be populated before legacy fields removed)
6. `Report v2.0` (Phase 8) must exist before `FinalReportDTO.from_report` (Phase 9)

---

## Recommended Commit Boundaries

| Commit | Phase | Type | Description |
|--------|-------|------|-------------|
| C1 | 1 | Feature | New value types (leaf) |
| C2 | 4 | Feature | `QuestionResultRecord` |
| C3 | 5 | Refactor | `Narrative` field rename |
| C4 | 2 | Feature | `ScoringSnapshot` |
| C5 | 3 | Feature | `ScoringNarrative` |
| C6 | 6 | Refactor | `InterviewEvaluationService` bridge refactor |
| C7 | 7A | Bridge | `InterviewState` extension — add scoring fields |
| C8 | 7B | Bridge | `SessionHistory` v1.5 — add new fields, build `QuestionResultRecord` |
| C9 | 7C | Removal | Retire `InterviewEvaluation`, enforce `SessionHistory` v2.0 |
| C10 | 8 | Feature | Report v2.0 |
| C11 | 9 | Feature | FinalReportDTO rebuild (EPIC-V13-05) |
| C12 | 10 | Feature | New report sections (EPIC-V13-05) |

---

## Test Files Requiring Updates

| Phase | Test files to update |
|-------|---------------------|
| 5 | `tests/domain/contracts/narrative/test_narrative_contracts.py`, `tests/services/narrative_generator/test_narrative_generator_architecture.py` |
| 7A | `tests/graph/nodes/test_evaluation_aggregate_node.py`, `tests/domain/contracts/interview_state/test_interview_state_field_invariants.py`, `tests/integration/use_cases/test_evaluate_answer_execution.py` |
| 7B | `tests/domain/contracts/session_history/test_session_history_contracts.py`, `tests/app/graph/nodes/test_session_close_node.py`, `tests/services/session_close/test_session_close_pipeline.py`, `tests/app/graph/nodes/test_narrative_integration.py`, `tests/app/graph/nodes/test_rs01_feature_propagation.py` |
| 7C | `tests/domain/contracts/interview_state/test_interview_state_field_invariants.py` (update: assert removed), `tests/domain/contracts/session_history/test_session_history_contracts.py` (update: assert removal + v2.0), `tests/domain/contracts/test_interview_state.py`, `tests/services/test_interview_evaluation_service.py`, `tests/services/test_signal_enrichment_step.py`, `tests/ui/mappers/test_final_report_dto_seniority.py`, `tests/ui/mappers/test_final_report_dto_context_profile.py`, `tests/ui/builders/test_ui_response_builder_completion.py`, `tests/hardening/test_r541_coaching_credibility.py`, `tests/infrastructure/llm/test_interview_metrics_integration.py`, `tests/app/graph/nodes/test_coaching_integration.py` |
| 8 | `tests/domain/contracts/report/test_report_contracts.py`, `tests/app/graph/nodes/test_report_node.py` |
| 9 | `tests/ui/mappers/test_interview_state_mapper.py`, `tests/ui/mappers/test_final_report_dto_seniority.py`, `tests/ui/mappers/test_final_report_dto_context_profile.py`, `tests/ui/builders/test_ui_response_builder_completion.py`, `tests/services/test_report_export_service.py` |

---

## Stopping Rule

If any phase reveals an unresolved architectural question, stop. Do not proceed. Apply the Stopping Rule from `V13-DEVELOPMENT-PLAYBOOK.md §8`: return to ADR, freeze the decision, update planning documents, resume.

---

*This document is the executable implementation roadmap for EPIC-V13-01 and EPIC-V13-05. No architectural decisions may be made during implementation. All decisions are frozen in ADR-033, EPIC-01-DOMAIN-CONTRACTS.md, and EPIC-01-DATA-MODEL.md.*

*Revision 2026-07-05: Replaced atomic Phases 7+8 with bridge sequence 7A (InterviewState extension) → 7B (SessionHistory extension) → 7C (legacy removal), renumbered downstream phases 9→8, 10→9, 11→10. Engineering rule "Zero Known Failing Tests" applied. Architecture unchanged.*
