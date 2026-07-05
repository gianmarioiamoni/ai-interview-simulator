# EPIC-01 — Domain Contract Design

**Status:** AUTHORITATIVE DESIGN SPECIFICATION  
**Date:** 2026-07-05  
**Precondition:** ADR-033 accepted. No production code modified.  
**Authority:** This document specifies the complete domain model for all new artifacts introduced by EPIC-V13-01. Implementation must be mechanically derivable from this document.

---

## 1. `ScoringSnapshot`

### Purpose

`ScoringSnapshot` is a Projection Artifact (PAT-04). It captures the aggregate scoring result of a completed interview session: the final numeric scores, hire decision, confidence, and gating outcome. It is immutable and has no computational methods. It is the canonical, sole-authoritative source of scoring data for the presentation layer after `InterviewEvaluation` is deleted.

### Ownership

- **Produced by:** `InterviewEvaluationService` (or its internal refactor). The service produces `ScoringSnapshot` and `ScoringNarrative` as separate outputs instead of assembling `InterviewEvaluation`.
- **Written to `InterviewState` by:** `EvaluationAggregateNode` — sole writer of `InterviewState.scoring_snapshot`.
- **Written to `SessionHistory` by:** `session_close_node` via `SessionHistoryBuilder.with_scoring_snapshot(...)`.
- **Written to `Report` by:** `report_node` via `ReportBuilder.with_scoring(snapshot)`.
- **No other writers exist.**

### Lifecycle

```
InterviewEvaluationService.evaluate(...)
  → produces ScoringSnapshot + ScoringNarrative
  → EvaluationAggregateNode writes both to InterviewState

session_close_node
  → reads state.scoring_snapshot
  → passes to SessionHistoryBuilder → embedded in SessionHistory.scoring_snapshot

report_node
  → reads state.session_history.scoring_snapshot (via ReportBuilder)
  → embedded in Report.scoring
```

`ScoringSnapshot` is write-once per session. It is not modified after `EvaluationAggregateNode` produces it.

### Fields

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `overall_score` | `float` | `ge=0.0, le=100.0` | Final calibrated score |
| `raw_score` | `float \| None` | `ge=0.0, le=100.0` if present | Pre-calibration score |
| `adjusted_score` | `float \| None` | `ge=0.0, le=100.0` if present | Post-adjustment score |
| `dimension_scores` | `dict[str, float]` | Each value `ge=0.0, le=100.0` | Keyed by `PerformanceDimensionType.value` |
| `dimension_signals` | `dict[str, float]` | Each value `ge=0.0, le=1.0` | Raw signal weights |
| `weighted_breakdown` | `dict[str, float]` | Each value `ge=0.0, le=1.0` | Weighted contribution per dimension |
| `level` | `InterviewLevel` | Required | Enum: assessed seniority level |
| `hire_decision` | `HireDecision` | Required | Enum: `STRONG_HIRE`, `HIRE`, `NO_HIRE`, `STRONG_NO_HIRE` |
| `hiring_probability` | `float` | `ge=0.0, le=100.0` | Calibrated hire probability |
| `percentile_rank` | `float` | `ge=0.0, le=100.0` | Relative position |
| `percentile_explanation` | `str` | `min_length=1` | Prose explanation |
| `decision_explanation` | `dict[str, list[str]]` | Required | Keys: decision facets; values: explanation points |
| `gating_triggered` | `bool` | Required | Whether a scoring gate was tripped |
| `gating_reason` | `str \| None` | Required when `gating_triggered=True` | Reason string |
| `confidence` | `Confidence` | Required | Scoring confidence envelope |
| `schema_version` | `str` | Default `"1.0"`, `min_length=1` | |

### Validation Invariants

- `V-SS-01`: If `gating_triggered=True`, `gating_reason` must not be `None`.
- `V-SS-02`: `len(dimension_scores) > 0` — at least one dimension must be scored.
- `V-SS-03`: `schema_version` must be non-empty.
- `V-SS-04`: `weighted_breakdown` keys must be a subset of `dimension_scores` keys.

### Relationships

- `ScoringSnapshot` replaces the scoring fields previously on `InterviewEvaluation`.
- `ScoringSnapshot` is embedded in `InterviewState.scoring_snapshot` (new field), `SessionHistory.scoring_snapshot` (replaces `evaluation_result`), and `Report.scoring`.
- `ScoringSnapshot` does not reference `InterviewEvaluation`, `SessionHistory`, or `Report`.
- `ScoringSnapshotBuilder` is the sole construction path. No `from_*` classmethods.

### Serialization Expectations

- `frozen=True, extra="forbid"`.
- All enum fields serialized as `.value` strings (Pydantic default).
- `dict[str, float]` fields: keys are stable strings; no ordering guarantee.

### Future Evolution

- When dimension taxonomy changes, `schema_version` increments. `ScoringSnapshot` is not responsible for migrating old snapshots.
- `weighted_breakdown` may be deprecated in favor of a dedicated `WeightedBreakdown` artifact in V2; the field is retained in `"1.0"` for backward compatibility.

---

## 2. `ScoringNarrative`

### Purpose

`ScoringNarrative` captures the LLM-generated hiring-context narrative for a completed session. It is a Projection Artifact (PAT-04). It encapsulates the candidate-facing prose sections that explain the hire decision and provide actionable coaching advice. It is immutable, produced once per session, and sourced exclusively by the presentation layer.

### Ownership

- **Produced by:** `EvaluationNarrativeAssembler` (refactored to produce `ScoringNarrative` instead of embedding narrative fields in `InterviewEvaluation`).
- **Written to `InterviewState` by:** `EvaluationAggregateNode` — sole writer of `InterviewState.scoring_narrative`.
- **Written to `SessionHistory` by:** `session_close_node` via `SessionHistoryBuilder.with_scoring_narrative(...)`.
- **Written to `Report` by:** `report_node` via `ReportBuilder.with_scoring_narrative(narrative)`.
- **No other writers exist.**

### Lifecycle

Same as `ScoringSnapshot` — produced together by `InterviewEvaluationService`, written through the same pipeline.

### Fields

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `executive_summary` | `str` | `min_length=1` | LLM hiring-readiness summary |
| `went_well` | `tuple[str, ...]` | May be empty | Positive reinforcement items |
| `held_you_back` | `tuple[ScoringNarrativeItem, ...]` | May be empty | Behavioural barriers |
| `knowledge_gaps` | `tuple[ScoringNarrativeItem, ...]` | May be empty | Identified knowledge deficits |
| `next_strategy` | `tuple[ScoringNarrativeItem, ...]` | May be empty | Prioritised interview strategy items |
| `improvement_suggestions` | `tuple[str, ...]` | May be empty | High-level improvement directives |
| `schema_version` | `str` | Default `"1.0"`, `min_length=1` | |

### `ScoringNarrativeItem` (nested value type)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `category` | `str` | `min_length=1` | Classification label |
| `description` | `str` | `min_length=1` | Primary content |
| `why_it_matters` | `str` | `min_length=1` | Relevance explanation |
| `context_detail` | `str \| None` | Optional | Section-specific detail (e.g. `impact`, `interview_impact`, `expected_improvement`) |

`context_detail` consolidates the previously ad-hoc per-section dict keys (`impact` for `held_you_back`, `interview_impact` for `knowledge_gaps`, `expected_improvement` for `next_strategy`) into a single optional field. The UI section renderers must be updated to read `context_detail` instead of section-specific dict keys.

`ScoringNarrativeItem` is `frozen=True, extra="forbid"`.

### Validation Invariants

- `V-SN-01`: `executive_summary` must not be empty.
- `V-SN-02`: Each `ScoringNarrativeItem` in all four tuple fields must have non-empty `category`, `description`, `why_it_matters`.
- `V-SN-03`: `schema_version` must be non-empty.

### Relationships

- `ScoringNarrative` is produced alongside `ScoringSnapshot` by the same evaluation pipeline but is a separate artifact.
- `ScoringNarrative` does not reference `ScoringSnapshot`, `CoachingSnapshot`, or `Narrative`. They are independent.
- `ScoringNarrative` replaces the LLM-prose fields previously on `InterviewEvaluation` (`executive_summary`, `went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions`).

### LLM Ownership Boundaries

- `executive_summary` is produced by `ExecutiveSummaryGenerator` (LLM call). This call is owned by `InterviewEvaluationService`.
- `went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions` are produced by `EvaluationNarrativeAssembler` (LLM call). This call is owned by `InterviewEvaluationService`.
- `ScoringNarrative` carries only the output. It does not expose the LLM prompt, model version, or token count.
- `InterviewCostMetrics` tracks token usage separately; it is not embedded in `ScoringNarrative`.

---

## 3. `QuestionResultRecord`

### Purpose

`QuestionResultRecord` is a persistence artifact that captures all data required to reconstruct per-question report sections and replay views after session close. It is the closure-time snapshot of `QuestionResult` (a live runtime artifact) combined with question metadata not otherwise persisted.

### Ownership

- **Produced by:** `session_close_node` — reads `InterviewState.results_by_question` and `InterviewState.questions` and constructs one `QuestionResultRecord` per answered question.
- **Written to `SessionHistory` by:** `session_close_node` via `SessionHistoryBuilder.with_question_results(records)`.
- **Read by:** `ReportBuilder.with_session_history(history)` — assembles `QuestionAssessmentRecord` list from `history.question_results`.
- **Read by:** `replay_node` (EPIC-V13-03) — constructs `ReplaySession` question views.
- **No other writers exist.**

### Lifecycle

```
session_close_node
  → iterates state.questions
  → for each question: reads state.results_by_question[q.id]
  → constructs QuestionResultRecord per question
  → passes tuple to SessionHistoryBuilder.with_question_results(...)
  → embedded in SessionHistory.question_results

report_node → ReportBuilder
  → reads history.question_results
  → constructs QuestionAssessmentRecord per record
  → embedded in Report.question_assessments
```

### Fields

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `question_id` | `str` | `min_length=1` | Matches `Question.id` |
| `question_index` | `int` | `ge=0` | Position in interview |
| `question_type` | `str` | `min_length=1` | `QuestionType.value` |
| `area_label` | `str` | `min_length=1` | Output of `InterviewAreaMapper.to_label(question.area)` |
| `question_prompt` | `str` | `min_length=1` | Full question text (not truncated) |
| `score` | `float` | `ge=0.0, le=100.0` | Question-level score |
| `max_score` | `float` | `gt=0.0` | Maximum achievable score |
| `feedback` | `str` | `min_length=1` | Evaluator feedback |
| `strengths` | `tuple[str, ...]` | May be empty | |
| `weaknesses` | `tuple[str, ...]` | May be empty | |
| `follow_up_question` | `str \| None` | Optional | Follow-up if asked |
| `passed_tests` | `int \| None` | `ge=0` if present | Coding-only |
| `total_tests` | `int \| None` | `gt=0` if present | Coding-only |
| `execution_status` | `str \| None` | Optional | Coding-only |
| `attempts` | `int` | `ge=1` | Count of submitted answers |
| `ai_hint_explanation` | `str \| None` | Optional | Hint explanation if requested |
| `ai_hint_suggestion` | `str \| None` | Optional | Hint suggestion if requested |
| `schema_version` | `str` | Default `"1.0"`, `min_length=1` | |

### Validation Invariants

- `V-QRR-01`: If `question_type` corresponds to a coding question, `passed_tests` and `total_tests` must both be present or both be `None`.
- `V-QRR-02`: If `total_tests` is present, `passed_tests <= total_tests`.
- `V-QRR-03`: If `ai_hint_suggestion` is present, `ai_hint_explanation` must also be present.

### Relationship with `QuestionResult`

`QuestionResult` is a live runtime artifact (in `InterviewState.results_by_question`). It carries `evaluation: Optional[QuestionEvaluation]`, `execution: Optional[ExecutionResult]`, `ai_hint: Optional[AiHint]`. `QuestionResultRecord` is the closure-time projection of `QuestionResult` — it flattens the nested structure into a flat, serializable record and adds question metadata (`area_label`, `question_prompt`, `attempts`) that is not in `QuestionResult`.

`QuestionResult` is not persisted. `QuestionResultRecord` is its sole persistence form.

### Relationship with `SessionHistory`

`QuestionResultRecord` is a member of `SessionHistory.question_results: tuple[QuestionResultRecord, ...]`. It is embedded at close time. It is `frozen=True, extra="forbid"`.

---

## 4. `QuestionAssessmentRecord`

### Purpose

`QuestionAssessmentRecord` is a `Report`-layer artifact. It is the report-facing projection of `QuestionResultRecord`. It carries exactly the fields needed to populate `QuestionAssessmentDTO` from `Report` alone. It is what `ReportBuilder` assembles from `SessionHistory.question_results`.

### Ownership

- **Produced by:** `ReportBuilder` — reads `SessionHistory.question_results` and constructs one `QuestionAssessmentRecord` per record.
- **Written to `Report` by:** `report_node` via `ReportBuilder.build()`.
- **Read by:** `FinalReportDTO.from_report(report)` — maps to `List[QuestionAssessmentDTO]`.
- **Read by:** Replay UI (via `ReplaySession`, which sources from `SessionHistory.question_results` directly).
- **No other writers exist.**

### Lifecycle

```
ReportBuilder.with_session_history(history)
  → reads history.question_results
  → for each QuestionResultRecord: constructs QuestionAssessmentRecord
  → stores as tuple internally

ReportBuilder.build()
  → embeds as Report.question_assessments: tuple[QuestionAssessmentRecord, ...]
```

### Fields

`QuestionAssessmentRecord` carries the same fields as `QuestionResultRecord`. It is not a separate domain concept — it is the `Report`-embedded form. Its field set is identical to `QuestionResultRecord` to avoid any loss during assembly.

The `ReportBuilder` copies fields directly from `QuestionResultRecord` without transformation. The only permitted transformation is type normalization (e.g. `list` to `tuple`) for immutability.

`QuestionAssessmentRecord` is `frozen=True, extra="forbid"`, `schema_version: str = "1.0"`.

### Validation Invariants

Same as `QuestionResultRecord` (V-QRR-01 through V-QRR-03).

Additionally:
- `V-QAR-01`: `len(report.question_assessments) == report.question_count` — the count of assessment records must match the declared question count on `Report`.

### Relationship with `Report`

`QuestionAssessmentRecord` is a member of `Report.question_assessments: tuple[QuestionAssessmentRecord, ...]`. It is a required field on `Report` after the migration (may be an empty tuple for edge cases where no questions were answered, but `V-QAR-01` must be satisfied).

---

## 5. `InterviewState` Evolution

### New Fields

| Field | Type | Default | Sole Writer | Readers |
|-------|------|---------|-------------|---------|
| `scoring_snapshot` | `ScoringSnapshot \| None` | `None` | `EvaluationAggregateNode` | `session_close_node` |
| `scoring_narrative` | `ScoringNarrative \| None` | `None` | `EvaluationAggregateNode` | `session_close_node` |

### Removed Fields

| Field | Removed when | Migration |
|-------|-------------|-----------|
| `interview_evaluation` | EPIC-V13-01 completion | Replaced by `scoring_snapshot` + `scoring_narrative` |

`interview_metrics` and `interview_cost_metrics` are **retained**. They are not part of `ScoringSnapshot` — they are observability artifacts, not report data.

### Write Order (graph execution sequence, unchanged)

```
evaluation_aggregate_node
  → writes: scoring_snapshot, scoring_narrative, interview_metrics, interview_cost_metrics
  → (formerly wrote: interview_evaluation)

session_close_node
  → reads: scoring_snapshot, scoring_narrative, candidate_profile_v2, observation_store,
           questions, answers, results_by_question, role, seniority_level, interview_type,
           language, company, current_question_index, candidate_identity_id, interview_id
  → writes: session_history

report_node
  → reads: session_history, interview_id
  → writes: report
```

### Idempotency Guards

- `EvaluationAggregateNode` no-ops if `state.scoring_snapshot is not None` (replaces the current `state.interview_evaluation is not None` guard).
- `session_close_node` no-ops if `state.session_history is not None` (unchanged).
- `report_node` no-ops if `state.report is not None` (unchanged).

### Invariant

`InterviewState` must not carry `interview_evaluation` after EPIC-V13-01. Any reference to `state.interview_evaluation` in any node, service, or UI component is a bug.

---

## 6. `SessionHistory` Evolution

### New Fields

| Field | Type | Default | Source |
|-------|------|---------|--------|
| `question_results` | `tuple[QuestionResultRecord, ...]` | `default_factory=tuple` | `session_close_node` via `SessionHistoryBuilder.with_question_results(...)` |
| `scoring_snapshot` | `ScoringSnapshot \| None` | `None` | `session_close_node` via `SessionHistoryBuilder.with_scoring_snapshot(...)` |
| `scoring_narrative` | `ScoringNarrative \| None` | `None` | `session_close_node` via `SessionHistoryBuilder.with_scoring_narrative(...)` |

### Removed Fields

| Field | Replaced by | Migration |
|-------|-------------|-----------|
| `evaluation_result: Optional[InterviewEvaluation]` | `scoring_snapshot: ScoringSnapshot \| None` | Removed in the same increment as `InterviewEvaluation` deletion |

### `SessionHistoryBuilder` New Methods

| Method | Parameter | Notes |
|--------|-----------|-------|
| `with_question_results` | `question_results: list[QuestionResultRecord]` | Required for EPIC-V13-01 sessions |
| `with_scoring_snapshot` | `scoring_snapshot: ScoringSnapshot` | Optional (session may not have evaluation) |
| `with_scoring_narrative` | `scoring_narrative: ScoringNarrative` | Optional (session may not have evaluation) |

`with_evaluation_result` is **deleted** from `SessionHistoryBuilder`.

### Schema Version Transition

| Version | Changes | Trigger |
|---------|---------|---------|
| `"1.0"` | Current production schema | V1.2 |
| `"2.0"` | Add `question_results`, replace `evaluation_result` with `scoring_snapshot`, add `scoring_narrative` | EPIC-V13-01 |

`SessionHistory.schema_version` default changes from `"1.0"` to `"2.0"`.

Since no production persistence layer exists, there is no live data migration. All new `SessionHistory` instances are constructed at schema `"2.0"`. The `"1.0"` schema is not forward-compatible.

### Validation Evolution

`SessionHistoryBuilder.build()` gains one new validation:
- `V-SH-01`: If `scoring_snapshot is not None` and `scoring_narrative is None`, raise `ValueError` — scoring snapshot and narrative are produced together and must both be present or both absent.

Existing validations (`session_id` match, `knowledge_snapshot` identity match) are unchanged.

---

## 7. `Report` Evolution

### Target Structure (post-EPIC-V13-01)

| Field | Type | Status | Notes |
|-------|------|--------|-------|
| `report_id` | `str` | Unchanged | |
| `session_id` | `str` | Unchanged | |
| `candidate_identity_id` | `str` | Unchanged | |
| `interview_index` | `int` | Unchanged | |
| `profile_snapshot` | `CandidateProfileSnapshot` | Unchanged | |
| `narrative` | `Narrative` | Unchanged (field name) | But `Narrative.executive_summary` field renamed to `Narrative.overview_section` (see §8 below) |
| `coaching_snapshot` | `CoachingSnapshot` | Unchanged | |
| `question_assessments` | `tuple[QuestionAssessmentRecord, ...]` | **NEW** | Per-question report data |
| `scoring` | `ScoringSnapshot` | **NEW** | All scoring fields |
| `scoring_narrative` | `ScoringNarrative` | **NEW** | All LLM coaching/narrative prose |
| `role` | `str` | Unchanged | |
| `seniority` | `str` | Unchanged | |
| `interview_type` | `str` | Unchanged | |
| `question_count` | `int` | Unchanged | |
| `knowledge_epoch` | `str` | Unchanged | |
| `schema_version` | `str` | Changed to `"2.0"` default | |
| `created_at` | `datetime` | Unchanged | |
| `metadata` | `dict[str, str]` | Unchanged | |

### `model_config`

`frozen=True, extra="forbid", arbitrary_types_allowed=True` — unchanged.

### New Validation Invariants

- `V-R-01`: `len(question_assessments) == question_count`.
- `V-R-02`: `scoring.dimension_scores` keys must be non-empty.
- `V-R-03`: `candidate_identity_id == profile_snapshot.candidate_identity_id` (unchanged from current).

### `ReportBuilder` New Methods

| Method | Parameter | Notes |
|--------|-----------|-------|
| `with_scoring` | `scoring: ScoringSnapshot` | Required for build to succeed |
| `with_scoring_narrative` | `scoring_narrative: ScoringNarrative` | Required for build to succeed |
| `with_question_assessments` | `question_assessments: tuple[QuestionAssessmentRecord, ...]` | Required for build to succeed |

`ReportBuilder.build()` validation additions:
- Raises `ValueError` if `scoring` is not set.
- Raises `ValueError` if `scoring_narrative` is not set.
- Raises `ValueError` if `len(question_assessments) != question_count` (V-R-01).

`ReportBuilder.with_session_history(history)` updated to read:
- `history.question_results` → constructs `QuestionAssessmentRecord` tuple → stored as `_question_assessments`
- `history.scoring_snapshot` → stored as `_scoring`
- `history.scoring_narrative` → stored as `_scoring_narrative`

### `Report.schema_version`

Default changes from `"1.0"` to `"2.0"` to reflect the new fields.

---

## 8. `Narrative` Evolution (`executive_summary` rename)

### Rename

`Narrative.executive_summary: NarrativeSection` → `Narrative.overview_section: NarrativeSection`

The `NarrativeSectionType.EXECUTIVE_SUMMARY` enum value is renamed to `NarrativeSectionType.OVERVIEW` (or the existing enum value is kept with a new alias — the implementation choice is left to EPIC-V13-01, but the field name on `Narrative` must change).

The `_section_type_invariant` validator on `Narrative` is updated to check that the `overview_section` slot has `section_type == NarrativeSectionType.OVERVIEW` (or equivalent).

### Rationale

The rename eliminates the naming collision between `Narrative.executive_summary` (deterministic feature-based placeholder) and `ScoringNarrative.executive_summary` (LLM hiring-readiness summary). After the rename, `report.scoring_narrative.executive_summary` is unambiguously the hiring summary and `report.narrative.overview_section` is the feature-based overview.

### All readers of `Narrative.executive_summary` that must be updated

- `domain/contracts/narrative/narrative.py` — field definition and validator
- `services/narrative_generator/narrative_generator.py` — construction
- Any test that constructs or asserts on `Narrative.executive_summary`

---

## 9. Artifact Ownership Table

| Artifact | Producer | Sole Writer (InterviewState) | Written to SessionHistory | Written to Report | Lifecycle |
|----------|----------|------------------------------|--------------------------|-------------------|-----------|
| `ScoringSnapshot` | `InterviewEvaluationService` | `EvaluationAggregateNode` (`scoring_snapshot`) | `session_close_node` (`scoring_snapshot`) | `report_node` → `ReportBuilder.with_scoring(...)` → `Report.scoring` | Produced once per session at `evaluation_aggregate`; immutable thereafter |
| `ScoringNarrative` | `EvaluationNarrativeAssembler` (via `InterviewEvaluationService`) | `EvaluationAggregateNode` (`scoring_narrative`) | `session_close_node` (`scoring_narrative`) | `report_node` → `ReportBuilder.with_scoring_narrative(...)` → `Report.scoring_narrative` | Same lifecycle as `ScoringSnapshot` |
| `QuestionResultRecord` | `session_close_node` | Not a standalone state field | `session_close_node` (`question_results`) | `report_node` → `ReportBuilder` → `Report.question_assessments` (as `QuestionAssessmentRecord`) | Produced once per question at session close |
| `QuestionAssessmentRecord` | `ReportBuilder` (from `QuestionResultRecord`) | N/A (lives in `Report`) | N/A | `Report.question_assessments` | Assembled by `ReportBuilder`; immutable in `Report` |
| `Report` | `ReportBuilder` | `report_node` (`report`) | N/A | Self | Produced once per session; immutable; sole report artifact post-migration |
| `SessionHistory` | `SessionHistoryBuilder` | `session_close_node` (`session_history`) | Self | N/A | Produced once per session; immutable after close |
| `Narrative` | `NarrativeGenerator` | Via `session_close_node` → `KnowledgeSnapshot` → `SessionHistory` → `ReportBuilder` | Embedded in `knowledge_snapshot` | `Report.narrative` | Produced at session close; immutable |
| `CoachingSnapshot` | `CoachingEngine` / `CoachingBuilder` | Via `session_close_node` → `KnowledgeSnapshot` → `SessionHistory` → `ReportBuilder` | Embedded in `knowledge_snapshot` | `Report.coaching_snapshot` | Same as `Narrative` |
| `CandidateProfileSnapshot` | `session_close_node` (from `candidate_profile_v2.features`) | Via `session_close_node` → `KnowledgeSnapshot` | Embedded in `knowledge_snapshot` | `Report.profile_snapshot` | Produced at session close; immutable |

---

## 10. `FinalReportDTO` Evolution

After EPIC-V13-01, `FinalReportDTO.from_components(state, evaluation)` is deleted.

`FinalReportDTO.from_report(report: Report) -> FinalReportDTO` is the sole factory.

### Field Mapping (`from_report`)

| `FinalReportDTO` field | Source | Notes |
|-----------------------|--------|-------|
| `overall_score` | `report.scoring.overall_score` | |
| `raw_score` | `report.scoring.raw_score` | |
| `adjusted_score` | `report.scoring.adjusted_score` | |
| `hiring_probability` | `report.scoring.hiring_probability` | |
| `hire_decision` | `HireDecisionMapper.to_label(report.scoring.hire_decision)` | Enum → display string |
| `decision_explanation` | `report.scoring.decision_explanation` | |
| `dimension_signals` | `report.scoring.dimension_signals` | |
| `percentile_rank` | `report.scoring.percentile_rank` | |
| `percentile_explanation` | `report.scoring.percentile_explanation` | |
| `executive_summary` | `report.scoring_narrative.executive_summary` | |
| `gating_triggered` | `report.scoring.gating_triggered` | |
| `gating_reason` | `report.scoring.gating_reason` | |
| `weighted_breakdown` | `report.scoring.weighted_breakdown` | |
| `dimension_scores` | `DimensionScoreMapper.from_scoring(report.scoring)` | Maps `dimension_scores` dict → `List[DimensionScoreDTO]` |
| `question_assessments` | `[QuestionAssessmentMapper.to_dto(r) for r in report.question_assessments]` | `QuestionAssessmentRecord` → `QuestionAssessmentDTO` |
| `improvement_suggestions` | `list(report.scoring_narrative.improvement_suggestions)` | |
| `went_well` | `list(report.scoring_narrative.went_well)` | |
| `held_you_back` | `[item.to_dict() for item in report.scoring_narrative.held_you_back]` | `ScoringNarrativeItem` → dict for renderers |
| `knowledge_gaps` | `[item.to_dict() for item in report.scoring_narrative.knowledge_gaps]` | Same |
| `next_strategy` | `[item.to_dict() for item in report.scoring_narrative.next_strategy]` | Same |
| `total_tokens_used` | `TokenCalculator.from_report(report)` | Reads `interview_metrics` or `report.metadata` |
| `confidence` | `report.scoring.confidence` | |
| `role` | `RoleType(report.role)` | |
| `seniority_level` | `report.seniority` | |
| `context_profile` | Derived from `report.metadata` or session context | TBD by EPIC-V13-05 implementer |

**New fields on `FinalReportDTO` (added by EPIC-V13-05, not EPIC-V13-01):**

| Field | Type | Source |
|-------|------|--------|
| `narrative_insights` | `List[NarrativeInsightDTO]` | `report.narrative.insights` |
| `coaching_objectives` | `List[CoachingObjectiveDTO]` | `report.coaching_snapshot` |

These fields are added in EPIC-V13-05 Phase 3, not Phase 1. `FinalReportDTO` is not required to carry them during Phase 1–2.

### `ScoringNarrativeItem.to_dict()` contract

Each `ScoringNarrativeItem` exposes a `to_dict() -> dict` method (or the mapper handles it) that produces:

```
{
  "category": item.category,
  "description": item.description,        # maps to "behaviour", "concept", "priority" etc.
  "why_it_matters": item.why_it_matters,
  "context_detail": item.context_detail   # maps to "impact", "interview_impact", "expected_improvement"
}
```

The UI section renderers (`render_held_you_back`, `render_knowledge_gaps`, `render_next_strategy`) must be updated to read `context_detail` instead of their current section-specific keys. This is a breaking change to the renderer contracts, owned by EPIC-V13-05.

---

## 11. Consistency Rules for Implementation

The following rules are binding on all EPIC-V13-01 and EPIC-V13-05 implementers:

| Rule | Constraint |
|------|-----------|
| `R-01` | `ScoringSnapshot` and `ScoringNarrative` are always produced together by `InterviewEvaluationService`. They are passed to `EvaluationAggregateNode` as a pair. |
| `R-02` | `EvaluationAggregateNode` writes both in the same state update. There is no intermediate state where `scoring_snapshot` is set but `scoring_narrative` is `None` (or vice versa). |
| `R-03` | `session_close_node` passes both to `SessionHistoryBuilder` if `state.scoring_snapshot is not None`. |
| `R-04` | `ReportBuilder.build()` raises `ValueError` if `scoring` or `scoring_narrative` is missing. |
| `R-05` | `FinalReportDTO.from_components` does not exist after EPIC-V13-01 merge. The factory method name is `from_report`. |
| `R-06` | `QuestionMapper` is not called by `FinalReportDTO` after EPIC-V13-05 Phase 1. |
| `R-07` | `Narrative.executive_summary` field name does not exist after EPIC-V13-01 merge. All references use `Narrative.overview_section`. |
| `R-08` | `InterviewState.interview_evaluation` field does not exist after EPIC-V13-01 merge. |
| `R-09` | `SessionHistory.evaluation_result` field does not exist after EPIC-V13-01 merge. |
| `R-10` | `Report.schema_version` defaults to `"2.0"` after EPIC-V13-01. Any test constructing `Report` with `schema_version="1.0"` is a legacy test that must be updated. |

---

*This document is the authoritative domain contract specification for EPIC-V13-01 pre-implementation. No code may deviate from these specifications without a new ADR or an amendment to this document.*
