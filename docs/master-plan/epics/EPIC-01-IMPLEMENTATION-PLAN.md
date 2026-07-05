# EPIC-01 — Implementation Plan

**Status:** READY FOR IMPLEMENTATION  
**Date:** 2026-07-05  
**Precondition:** Architecture Freeze passed (`EPIC-01-ARCHITECTURE-FREEZE.md`). No new architectural decisions permitted.  
**Authority:** This document translates the frozen architecture into an executable implementation roadmap. All decisions reference ADR-033, EPIC-01-DOMAIN-CONTRACTS.md, and EPIC-01-DATA-MODEL.md.

---

## Implementation Owner

**EPIC-V13-01** owns Phases 1–7 (domain layer, pipeline, state migration).  
**EPIC-V13-05** owns Phases 8–11 (presentation layer, DTO rebuild, new sections).

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

## Phase 7 — `EvaluationAggregateNode` + `InterviewState` Migration

### Objective

Update `EvaluationAggregateNode` to write `scoring_snapshot` and `scoring_narrative` to `InterviewState` instead of `interview_evaluation`. Remove `InterviewState.interview_evaluation`. Delete `InterviewEvaluation` contract.

### Production Files — Modify

| File | Change |
|------|--------|
| `domain/contracts/interview_state/base.py` | Remove `interview_evaluation: Optional[InterviewEvaluation]`; add `scoring_snapshot: ScoringSnapshot \| None = None`; add `scoring_narrative: ScoringNarrative \| None = None` |
| `app/graph/nodes/evaluation_aggregate_node.py` | Update idempotency guard to `state.scoring_snapshot is not None`; unpack `(scoring_snapshot, scoring_narrative)` from service; write both to state |
| `domain/contracts/interview/interview_evaluation.py` | **Delete** |
| `domain/contracts/interview_state/factory.py` | Update `create_initial` / `create_empty` — remove `interview_evaluation=None` init |

### Production Files — Delete

| File |
|------|
| `domain/contracts/interview/interview_evaluation.py` |

### Domain Contracts Involved

`ScoringSnapshot`, `ScoringNarrative`, `InterviewState`. Rule R-08.

### Prerequisites

Phase 6 complete.

### Implementation Order

1. Update `InterviewStateBase` — remove `interview_evaluation`; add `scoring_snapshot`, `scoring_narrative`
2. Update `EvaluationAggregateNode.__call__` — new idempotency guard; unpack tuple; write new fields
3. Delete `interview_evaluation.py`
4. Update `InterviewState` factory and any `model_copy(update={"interview_evaluation": ...})` call sites (none in production after node update)
5. Update all test fixtures that set `interview_evaluation=` on `InterviewState`

### Expected Behavioural Changes

- `state.interview_evaluation` no longer exists — any access raises `AttributeError`
- `state.scoring_snapshot` and `state.scoring_narrative` carry the data
- `EvaluationAggregateNode` idempotency guard now checks `scoring_snapshot`

### Regression Risks

**High** — 14 test files reference `interview_evaluation` (see inventory). All must be updated.

The following production files still read `state.interview_evaluation` and will break — they are addressed in Phase 8:
- `app/ui/builders/ui_response_builder.py`
- `app/ui/mappers/interview_state_mapper.py`
- `app/ui/state_handlers/export_handlers.py` (indirectly)
- `app/graph/nodes/session_close_node.py`

**Phase 7 and Phase 8 must be committed together** to avoid a broken intermediate state. They are a single atomic migration unit.

### Required Architectural Tests

- `tests/domain/contracts/interview_state/test_interview_state_field_invariants.py` — assert `scoring_snapshot` field exists; assert `interview_evaluation` does not exist
- `tests/graph/nodes/test_evaluation_aggregate_node.py` — assert writes `scoring_snapshot` and `scoring_narrative`; assert idempotency on `scoring_snapshot is not None`

### Completion Checklist

- [ ] `interview_evaluation` field removed from `InterviewState`
- [ ] `scoring_snapshot` and `scoring_narrative` fields added with `None` default
- [ ] `EvaluationAggregateNode` writes both
- [ ] `interview_evaluation.py` deleted — zero references in production code
- [ ] All affected test fixtures updated
- [ ] Phase 8 committed atomically with this phase

---

## Phase 8 — `session_close_node` + `SessionHistory` Migration (atomic with Phase 7)

### Objective

Update `session_close_node` to pass `scoring_snapshot`, `scoring_narrative`, `question_results`, `context_profile`, and `generation_metadata` to `SessionHistoryBuilder`. Update `SessionHistory` contract.

### Production Files — Modify

| File | Change |
|------|--------|
| `domain/contracts/session_history/session_history.py` | Add `question_results: tuple[QuestionResultRecord, ...]`; replace `evaluation_result` with `scoring_snapshot: ScoringSnapshot \| None`; add `scoring_narrative: ScoringNarrative \| None`; add `context_profile: InterviewContextProfile` (required); add `generation_metadata: GenerationMetadata \| None`; bump `schema_version` default to `"2.0"` |
| `domain/contracts/session_history/session_history_builder.py` | Delete `with_evaluation_result`; add `with_question_results`, `with_scoring_snapshot`, `with_scoring_narrative`, `with_context_profile`, `with_generation_metadata`; add `context_profile` to mandatory validation; add V-SH-01 (scoring pair) |
| `app/graph/nodes/session_close_node.py` | Read `state.scoring_snapshot`, `state.scoring_narrative`, `state.context_profile`, `state.interview_metrics`, `state.interview_cost_metrics`; build `QuestionResultRecord` per answered question from `state.results_by_question` + `state.questions` + `state.answers`; build `GenerationMetadata` from metrics; pass all to `SessionCloseContext` or `SessionHistoryBuilder` directly |
| `services/session_close/session_close_pipeline.py` | Pass `question_results`, `scoring_snapshot`, `scoring_narrative`, `context_profile`, `generation_metadata` to builder; remove `evaluation_result` path |
| `services/session_close/session_close_context.py` | Replace `evaluation_result: Optional[InterviewEvaluation]` with new fields; add `question_results`, `scoring_snapshot`, `scoring_narrative`, `context_profile`, `generation_metadata` |
| `app/ui/builders/ui_response_builder.py` | Remove `state.interview_evaluation` read from `_build_report`; gate only on `state.report is not None` |
| `app/ui/mappers/interview_state_mapper.py` | Remove `interview_evaluation` guard; call `FinalReportDTO.from_report(state.report)` (stub — full implementation in Phase 10) |

### Production Files — Delete

None in this phase (contracts only evolved).

### Domain Contracts Involved

`SessionHistory v2.0`, `QuestionResultRecord`, `ScoringSnapshot`, `ScoringNarrative`, `GenerationMetadata`, `InterviewContextProfile`. Rules R-13, R-14, R-15. V-SH-01.

### Builders Involved

`SessionHistoryBuilder`

### Prerequisites

Phases 1–7.

### Implementation Order

1. Update `SessionHistory` contract and `SessionHistoryBuilder`
2. Update `SessionCloseContext`
3. Update `session_close_node` — add `QuestionResultRecord` construction loop; `GenerationMetadata` construction
4. Update `session_close_pipeline.py` — remove `evaluation_result` path; add new fields
5. Update `ui_response_builder._build_report` — remove `final_eval` read; gate on `state.report` only
6. Update `interview_state_mapper.to_final_report_dto` — stub `from_report` call (Phase 10 completes it)
7. Update all test fixtures that construct `SessionHistory` or `SessionHistoryBuilder`

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

- `UIResponseBuilder._build_report` no longer requires `state.interview_evaluation` — gates on `state.report` only
- `SessionHistory` v2.0 has `context_profile`, `question_results`, `scoring_snapshot` in place of `evaluation_result`
- `session_close_node` writes the full closure payload

### Regression Risks

**High** — 15 test files reference `SessionHistory` or `SessionHistoryBuilder`. All fixtures must be updated.

### Required Architectural Tests

- `tests/domain/contracts/session_history/test_session_history_contracts.py` — assert `context_profile` required; assert `evaluation_result` does not exist; assert V-SH-01 enforced; assert `schema_version` default is `"2.0"`
- `tests/app/graph/nodes/test_session_close_node.py` — assert `question_results` populated; assert `scoring_snapshot` embedded; assert `context_profile` embedded

### Completion Checklist

- [ ] `SessionHistory.evaluation_result` does not exist
- [ ] `SessionHistory.scoring_snapshot`, `scoring_narrative`, `question_results`, `context_profile`, `generation_metadata` exist
- [ ] `SessionHistory.schema_version` defaults to `"2.0"`
- [ ] V-SH-01 enforced in builder
- [ ] R-13 enforced: `context_profile` required
- [ ] `ui_response_builder` no longer reads `interview_evaluation`
- [ ] All test fixtures updated
- [ ] Full test suite passes

### Commit boundary

Phases 7 + 8 committed atomically: `feat(migration): InterviewState + SessionHistory v2.0 — retire InterviewEvaluation`

---

## Phase 9 — `ReportBuilder` + `Report` Migration

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

Phase 8 complete.

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

## Phase 10 — `FinalReportDTO` Rebuild (EPIC-V13-05)

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

Phase 9 complete.

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

## Phase 11 — New Report Sections (EPIC-V13-05 Phase 3)

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

Phase 10 complete.

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

Phases 7 + 8  ─── atomic; depends on Phase 6 + Phase 4 + Phase 5

Phase 9  ─── depends on Phases 7+8

Phase 10 ─── depends on Phase 9

Phase 11 ─── depends on Phase 10
```

**Critical path:** 1 → 2 → 6 → 7+8 → 9 → 10 → 11  
(Phase 3 runs in parallel with Phase 2; Phase 4 and 5 run in parallel with Phases 1–3)

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
3. Service refactor (Phase 6) must exist before `EvaluationAggregateNode` migration (Phase 7)
4. **Phases 7 and 8 are atomic** — they must be committed together
5. `Report v2.0` (Phase 9) must exist before `FinalReportDTO.from_report` (Phase 10)

---

## Recommended Commit Boundaries

| Commit | Phases | Description |
|--------|--------|-------------|
| C1 | 1 | New value types (leaf) |
| C2 | 4 | `QuestionResultRecord` |
| C3 | 5 | `Narrative` field rename |
| C4 | 2 | `ScoringSnapshot` |
| C5 | 3 | `ScoringNarrative` |
| C6 | 6 | `InterviewEvaluationService` refactor |
| C7 | 7 + 8 | **Atomic** — InterviewState + SessionHistory migration, InterviewEvaluation deletion |
| C8 | 9 | Report v2.0 |
| C9 | 10 | FinalReportDTO rebuild (EPIC-V13-05) |
| C10 | 11 | New report sections (EPIC-V13-05) |

---

## Test Files Requiring Updates

| Phase | Test files to update |
|-------|---------------------|
| 5 | `tests/domain/contracts/narrative/test_narrative_contracts.py`, `tests/services/narrative_generator/test_narrative_generator_architecture.py` |
| 7 | `tests/graph/nodes/test_evaluation_aggregate_node.py`, `tests/domain/contracts/interview_state/test_interview_state_field_invariants.py`, `tests/domain/contracts/test_interview_state.py`, `tests/integration/use_cases/test_evaluate_answer_execution.py`, `tests/services/test_interview_evaluation_service.py`, `tests/services/test_signal_enrichment_step.py`, `tests/ui/mappers/test_final_report_dto_seniority.py`, `tests/ui/mappers/test_final_report_dto_context_profile.py`, `tests/ui/builders/test_ui_response_builder_completion.py`, `tests/hardening/test_r541_coaching_credibility.py`, `tests/infrastructure/llm/test_interview_metrics_integration.py` |
| 8 | `tests/domain/contracts/session_history/test_session_history_contracts.py`, `tests/app/graph/nodes/test_session_close_node.py`, `tests/services/session_close/test_session_close_pipeline.py`, `tests/app/graph/nodes/test_coaching_integration.py`, `tests/app/graph/nodes/test_narrative_integration.py`, `tests/app/graph/nodes/test_rs01_feature_propagation.py`, `tests/domain/contracts/interview_state/test_candidate_identity.py`, `tests/services/knowledge_pipeline/test_knowledge_pipeline_architecture.py`, `tests/infrastructure/execution/test_domain_isolation.py` |
| 9 | `tests/domain/contracts/report/test_report_contracts.py`, `tests/app/graph/nodes/test_report_node.py` |
| 10 | `tests/ui/mappers/test_interview_state_mapper.py`, `tests/ui/mappers/test_final_report_dto_seniority.py`, `tests/ui/mappers/test_final_report_dto_context_profile.py`, `tests/ui/builders/test_ui_response_builder_completion.py`, `tests/services/test_report_export_service.py` |

---

## Stopping Rule

If any phase reveals an unresolved architectural question, stop. Do not proceed. Apply the Stopping Rule from `V13-DEVELOPMENT-PLAYBOOK.md §8`: return to ADR, freeze the decision, update planning documents, resume.

---

*This document is the executable implementation roadmap for EPIC-V13-01 and EPIC-V13-05. No architectural decisions may be made during implementation. All decisions are frozen in ADR-033, EPIC-01-DOMAIN-CONTRACTS.md, and EPIC-01-DATA-MODEL.md.*
