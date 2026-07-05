# EPIC-01 — Data Model Specification

**Status:** FROZEN  
**Date:** 2026-07-05  
**Precondition:** ADR-033 accepted. EPIC-01-DOMAIN-CONTRACTS.md frozen. No production code modified.  
**Authority:** This document resolves all open modelling decisions from EPIC-01-DOMAIN-CONTRACTS.md and freezes the complete data model for implementation.

---

## 1. Report Metadata Model

### Problem

Three fields on `FinalReportDTO` currently read from live `InterviewState` rather than from `Report`:

- `context_profile: InterviewContextProfile` — sourced from `state.context_profile`
- `total_tokens_used: int` — sourced from `state.interview_metrics.total_tokens` or fallback per-question sum
- `role: RoleType` and `seniority_level: str` — sourced from `state.role.type` and `state.seniority_level`

After `FinalReportDTO.from_report(report)` becomes the sole factory, these fields must be derivable from `Report` alone.

Additionally, `InterviewMetrics` and `InterviewCostMetrics` are observability artifacts (not scoring artifacts) that currently live only on `InterviewState`. Their persistence path is unspecified.

### Decision

#### 1a — `InterviewContextProfile` in `Report`

`InterviewContextProfile` is embedded in `Report` as a new field:

```
report.context_profile: InterviewContextProfile
```

**Rationale:** `InterviewContextProfile` determines the framing of the entire interview (role, company context, business domain). It belongs with the report, not only with the runtime state. Without it, `FinalReportDTO.from_report` cannot populate `context_profile`. Embedding it in `Report` is the only path that is both replay-compatible and free of live `InterviewState` reads.

`InterviewContextProfile` is `frozen=True` with three fields: `job_description: str | None`, `company_description: str | None`, `business_context: BusinessContext`. It carries no mutable state and is safe to embed.

**Producer chain:** `session_close_node` reads `state.context_profile` → passes to `SessionHistoryBuilder.with_context_profile(...)` → embedded in `SessionHistory.context_profile: InterviewContextProfile` → `ReportBuilder.with_session_history(history)` reads `history.context_profile` → embedded in `Report.context_profile`.

#### 1b — Token Usage in `Report`

Token usage is embedded in `Report` as a new field:

```
report.generation_metadata: GenerationMetadata
```

`GenerationMetadata` is a new value type:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `total_tokens_used` | `int` | `ge=0` | Sum from `InterviewMetrics.total_tokens` |
| `total_cost_usd` | `float \| None` | `ge=0.0` if present | From `InterviewCostMetrics.total_cost_usd` |
| `cost_per_question_usd` | `float \| None` | `ge=0.0` if present | From `InterviewCostMetrics.cost_per_question_usd` |
| `schema_version` | `str` | Default `"1.0"` | |

`GenerationMetadata` is `frozen=True, extra="forbid"`. It is a snapshot of observable LLM execution metrics at close time. It is not used for scoring or routing — only for display and audit.

**Rationale:** `TokenCalculator` currently reads `state.interview_metrics`. After migration, `FinalReportDTO.from_report` cannot access `InterviewState`. Token count must be persisted. `GenerationMetadata` is the minimal artifact that carries it. `InterviewMetrics` and `InterviewCostMetrics` themselves are not embedded in `Report` — they are dataclass-based observability artifacts with operational detail (per-operation breakdowns, latencies) that exceed the report's display requirements. `GenerationMetadata` carries only the summary fields needed by the report.

**Producer chain:** `EvaluationAggregateNode` computes `interview_metrics` and `interview_cost_metrics` → `session_close_node` reads both and constructs `GenerationMetadata` → passes to `SessionHistoryBuilder.with_generation_metadata(...)` → `ReportBuilder.with_session_history(history)` reads it → embedded in `Report.generation_metadata`.

`InterviewMetrics` and `InterviewCostMetrics` remain on `InterviewState` as observability artifacts. They are not migrated to `Report` beyond the summary embedded in `GenerationMetadata`.

#### 1c — `role` and `seniority_level` in `Report`

`Report` already carries `report.role: str` and `report.seniority: str`. These are sufficient.

`FinalReportDTO.from_report(report)` maps:
- `role` ← `RoleType(report.role)` (enum construction from string value)
- `seniority_level` ← `report.seniority`

No new field is needed.

### Complete `Report` Metadata Surface (post-EPIC-V13-01)

`Report` carries the following metadata fields (all previously defined plus new):

| Field | Type | Status |
|-------|------|--------|
| `report_id` | `str` | Existing |
| `session_id` | `str` | Existing |
| `candidate_identity_id` | `str` | Existing |
| `interview_index` | `int` | Existing |
| `role` | `str` | Existing |
| `seniority` | `str` | Existing |
| `interview_type` | `str` | Existing |
| `question_count` | `int` | Existing |
| `knowledge_epoch` | `str` | Existing |
| `schema_version` | `str` | Existing (bumped to `"2.0"`) |
| `created_at` | `datetime` | Existing |
| `metadata` | `dict[str, str]` | Existing |
| `context_profile` | `InterviewContextProfile` | **NEW** |
| `generation_metadata` | `GenerationMetadata` | **NEW** |

`Report` does not embed `InterviewMetrics` or `InterviewCostMetrics` directly. `GenerationMetadata` is the canonical report-level summary.

### `SessionHistory` Metadata Extension

`SessionHistory` gains:
- `context_profile: InterviewContextProfile` — new required field; populated by `session_close_node`
- `generation_metadata: GenerationMetadata` — new `Optional` field; populated by `session_close_node` if `interview_metrics` is available

`SessionHistory.schema_version` is already bumped to `"2.0"` by the `question_results` and `scoring_snapshot` additions; no further version bump is needed.

---

## 2. `ScoringSnapshot` Dimension Score Structure

### Problem

`ScoringSnapshot` must carry dimension scores. The question is whether they are stored as `dict[str, float]` or as typed `PerformanceDimension` objects (which carry `name`, `score`, `justification`).

`DimensionScoreMapper.map(...)` currently receives three inputs from `InterviewEvaluation`:
1. `dimension_scores: Dict` — `{dim_type_value: float}`
2. `weighted_breakdown: Dict` — `{dim_type_value: float}`
3. `performance_dimensions: list[PerformanceDimension]` — typed objects with `justification`

The `justification` field on `DimensionScoreDTO` is sourced from `PerformanceDimension.justification` (LLM-generated per-dimension commentary). This is the only field in the dimension display that requires a typed object.

### Decision: Typed `ScoringDimension` objects (Option B, extended)

`ScoringSnapshot` carries dimension scores as a typed tuple:

```
scoring_dimensions: tuple[ScoringDimension, ...]
```

`ScoringDimension` is a new value type:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `dimension_type` | `PerformanceDimensionType` | Required | Enum value |
| `score` | `float` | `ge=0.0, le=100.0` | Calibrated dimension score |
| `signal` | `float` | `ge=0.0, le=1.0` | Raw signal weight |
| `weighted_contribution` | `float` | `ge=0.0, le=1.0` | Weighted contribution to overall score |
| `justification` | `str` | `min_length=1` | LLM-generated per-dimension commentary |
| `level` | `str` | `min_length=1` | `"strong"`, `"moderate"`, or `"weak"` per threshold |

`ScoringDimension` is `frozen=True, extra="forbid"`.

`ScoringSnapshot` retains convenience dict-like fields alongside:

```
dimension_scores: dict[str, float]       # keyed by PerformanceDimensionType.value; derived from scoring_dimensions
dimension_signals: dict[str, float]      # keyed by PerformanceDimensionType.value; derived from scoring_dimensions
weighted_breakdown: dict[str, float]     # keyed by PerformanceDimensionType.value; derived from scoring_dimensions
```

These three dict fields are **derived** from `scoring_dimensions` at construction time and are included in `ScoringSnapshot` for backward compatibility with `ReportViewModelBuilder` and `render_signals`. They carry no additional information; they are projections of `scoring_dimensions`.

**Rationale:**

1. `DimensionScoreMapper` currently needs `performance_dimensions` (typed) to get `justification`. If `ScoringSnapshot` carried only dicts, the mapper would have no `justification` source after `InterviewEvaluation` is deleted. Typed `ScoringDimension` objects preserve `justification` without requiring a separate `PerformanceDimension` list.

2. `render_dimensions` reads `dimension_insights` from `ReportViewModelBuilder`, which calls `ReportInsightBuilder.build_dimension_insights(dims)`. `dims` is `List[DimensionScoreDTO]`, already constructed. The VM builder also reads `report.dimension_signals` (dict) for `signal_insights`. Retaining the dict fields on `ScoringSnapshot` means `ReportViewModelBuilder` requires no changes to its signal insight path.

3. Pure dicts (Option A) would require `DimensionScoreMapper` to be redesigned to source `justification` from elsewhere. There is no other source after `InterviewEvaluation` deletion.

4. Typed objects alone (without the dict convenience fields) would require rewriting `ReportViewModelBuilder.signal_insights` and `render_signals`, which read from `report.dimension_signals` (a `FinalReportDTO` dict field).

**`DimensionScoreMapper` update:** After migration, `DimensionScoreMapper.map(...)` receives `ScoringSnapshot.scoring_dimensions` (typed tuple) instead of three separate dict/list inputs. It reads `dim.score`, `dim.weighted_contribution`, `dim.justification`, `dim.level` directly from `ScoringDimension`. The three-parameter signature is replaced with a single `scoring_dimensions: tuple[ScoringDimension, ...]` parameter.

### `ScoringSnapshot` Updated Field Set

Supersedes the field set in EPIC-01-DOMAIN-CONTRACTS.md §1:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `overall_score` | `float` | `ge=0.0, le=100.0` | |
| `raw_score` | `float \| None` | `ge=0.0, le=100.0` | |
| `adjusted_score` | `float \| None` | `ge=0.0, le=100.0` | |
| `scoring_dimensions` | `tuple[ScoringDimension, ...]` | `len >= 1` | Canonical dimension data |
| `dimension_scores` | `dict[str, float]` | Derived | Convenience projection |
| `dimension_signals` | `dict[str, float]` | Derived | Convenience projection |
| `weighted_breakdown` | `dict[str, float]` | Derived | Convenience projection |
| `level` | `InterviewLevel` | Required | |
| `hire_decision` | `HireDecision` | Required | |
| `hiring_probability` | `float` | `ge=0.0, le=100.0` | |
| `percentile_rank` | `float` | `ge=0.0, le=100.0` | |
| `percentile_explanation` | `str` | `min_length=1` | |
| `decision_explanation` | `dict[str, list[str]]` | Required | |
| `gating_triggered` | `bool` | Required | |
| `gating_reason` | `str \| None` | Required if `gating_triggered=True` | |
| `confidence` | `Confidence` | Required | |
| `schema_version` | `str` | Default `"1.0"` | |

**Validation:** `len(scoring_dimensions) >= 1`. Dict fields (`dimension_scores`, `dimension_signals`, `weighted_breakdown`) are validated to have keys equal to `{d.dimension_type.value for d in scoring_dimensions}`.

---

## 3. Question Result Persistence Model

### Canonical Persisted Representation

`QuestionResultRecord` is the canonical persistence form of per-question assessment data. Its field set (from EPIC-01-DOMAIN-CONTRACTS.md §3) is confirmed. This section resolves the serialization and immutability contracts.

### Immutable Fields (produced at close time; never derived)

| Field | Source | Derivable? |
|-------|--------|------------|
| `question_id` | `Question.id` | No |
| `question_index` | Loop index in `session_close_node` | No |
| `question_type` | `Question.type.value` | No |
| `area_label` | `InterviewAreaMapper.to_label(question.area)` at close | No — enum label mapping |
| `question_prompt` | `Question.prompt` | No |
| `score` | `QuestionResult.evaluation.score` | No |
| `max_score` | `QuestionResult.evaluation.max_score` | No |
| `feedback` | `QuestionResult.evaluation.feedback` | No |
| `strengths` | `QuestionResult.evaluation.strengths` | No |
| `weaknesses` | `QuestionResult.evaluation.weaknesses` | No |
| `follow_up_question` | `QuestionResult.evaluation.follow_up_question` | No |
| `passed_tests` | `QuestionResult.execution.passed_tests` (if exists) | No |
| `total_tests` | `QuestionResult.execution.total_tests` (if exists) | No |
| `execution_status` | `QuestionResult.execution.status.value` (if exists) | No |
| `attempts` | Count of `state.answers` with matching `question_id` | No |
| `ai_hint_explanation` | `QuestionResult.ai_hint.explanation` (if exists) | No |
| `ai_hint_suggestion` | `QuestionResult.ai_hint.suggestion` (if exists) | No |

All fields are captured at `session_close_node` from live `InterviewState`. None are re-derived from other persisted artifacts.

### Derived Fields (computed at Report assembly; not stored on `QuestionResultRecord`)

| Derived value | How derived | Used in |
|---------------|-------------|---------|
| `passed: bool` | `passed_tests >= 1 if passed_tests else score >= threshold` | `QuestionAssessmentDTO` if needed |
| `area_display` | Already stored as `area_label` (pre-labeled at close) | `QuestionAssessmentDTO.area` |

No computation occurs in `ReportBuilder` when assembling `QuestionAssessmentRecord` from `QuestionResultRecord`. The assembly is a copy operation; all values are direct reads.

### Serialization Rules

- `QuestionResultRecord` is `frozen=True, extra="forbid"`.
- `tuple[str, ...]` for `strengths`, `weaknesses` — not `list`. Serializes as JSON array.
- `execution_status: str | None` — raw status string (enum value); enum is not embedded in the record.
- `area_label: str` — pre-mapped label string; enum is not embedded.
- All `Optional` numeric fields (`passed_tests`, `total_tests`, `score`) serialize as `null` when `None`.
- `schema_version: str` default `"1.0"`.

### Replay Requirements

For replay, `QuestionResultRecord` must be sufficient to render the per-question replay view without any LLM call and without access to live `InterviewState`. Replay completeness verification (§5 below) confirms that all required fields are present.

Specifically, `question_prompt` is stored **full** (not truncated). `QuestionMapper` currently truncates `question_prompt` to 120 chars; the record stores the full text. `FinalReportDTO` and `QuestionAssessmentDTO` may truncate for display, but the stored record is always the full text.

---

## 4. Dimension Mapping Strategy

This section specifies the canonical data source for every scoring-related report section.

### Overall Score Panel

| Report element | Source field | Path |
|----------------|-------------|------|
| `overall_score` | `report.scoring.overall_score` | Direct |
| `hire_decision` (display) | `HireDecisionMapper.to_label(report.scoring.hire_decision)` | Enum → string |
| `hiring_probability` | `report.scoring.hiring_probability` | Direct |
| `role` | `RoleType(report.role)` | String → enum |
| `seniority_level` | `report.seniority` | Direct |

### Percentile / Market Panel

| Report element | Source field | Path |
|----------------|-------------|------|
| `percentile_rank` | `report.scoring.percentile_rank` | Direct |
| `percentile_explanation` | `report.scoring.percentile_explanation` | Direct |
| `percentile_segment` | `build_percentile_segment(report.scoring.percentile_rank)` | Derived in VM builder |
| `percentile_narrative` | `build_percentile_narrative(report.scoring.percentile_rank, report.role)` | Derived in VM builder |

### Hire Decision Panel

| Report element | Source field | Path |
|----------------|-------------|------|
| `decision_explanation` | `report.scoring.decision_explanation` | Direct |
| `gating_triggered` | `report.scoring.gating_triggered` | Direct |
| `gating_reason` | `report.scoring.gating_reason` | Direct |

### Executive Summary Panel

| Report element | Source field | Path |
|----------------|-------------|------|
| `executive_summary` | `report.scoring_narrative.executive_summary` | Direct |

### Dimension Performance Panel (`render_performance`, `render_dimensions`)

| Report element | Source field | Path |
|----------------|-------------|------|
| `names` | `[d.dimension_type.value for d in report.scoring.scoring_dimensions]` | Via `DimensionScoreDTO.name` |
| `scores` | `[d.score for d in report.scoring.scoring_dimensions]` | Via `DimensionScoreDTO.score` |
| `strongest` | `DimensionRanking.compute(dims).strongest` | Derived in VM builder |
| `weakest` | `DimensionRanking.compute(dims).weakest` | Derived in VM builder |
| `dims` | `DimensionScoreMapper.map(report.scoring.scoring_dimensions)` | Typed → DTOs |
| `dimension_insights` | `ReportInsightBuilder.build_dimension_insights(dims)` | Derived from DTOs |
| `justification` per dim | `ScoringDimension.justification` → `DimensionScoreDTO.justification` | Via `DimensionScoreMapper` |
| `contribution` per dim | `ScoringDimension.weighted_contribution` → `DimensionScoreDTO.contribution` | Via `DimensionScoreMapper` |

### Signal Insights Panel (`render_signals`)

| Report element | Source field | Path |
|----------------|-------------|------|
| `signal_insights` | `build_signal_insights(report.scoring.dimension_signals)` | Derived from `ScoringSnapshot.dimension_signals` dict |

`ScoringSnapshot.dimension_signals` is a derived dict (from `scoring_dimensions`) and is sufficient for this path without changes to `ReportViewModelBuilder`.

### Coaching Panels

| Panel | Source field | Path |
|-------|-------------|------|
| `went_well` | `report.scoring_narrative.went_well` | Tuple → list |
| `held_you_back` | `[item.to_dict() for item in report.scoring_narrative.held_you_back]` | `ScoringNarrativeItem` → dict |
| `knowledge_gaps` | `[item.to_dict() for item in report.scoring_narrative.knowledge_gaps]` | Same |
| `next_strategy` | `[item.to_dict() for item in report.scoring_narrative.next_strategy]` | Same |
| `improvement_suggestions` | `list(report.scoring_narrative.improvement_suggestions)` | Tuple → list |
| Coaching objectives (new) | `report.coaching_snapshot` | EPIC-V13-05 Phase 3 |
| Study recommendations (new) | `report.coaching_snapshot` | EPIC-V13-05 Phase 3 |

### Narrative Insights Panel (new, EPIC-V13-05 Phase 3)

| Report element | Source field | Path |
|----------------|-------------|------|
| `narrative_insights` | `report.narrative.insights` | Tuple of `NarrativeInsight` |
| Per-insight evidence anchor | `insight.source_feature_id` | EPIC-V13-06 |

### Strengths / Weaknesses Panels

| Panel | Source field | Path |
|-------|-------------|------|
| `went_well` (positive) | `report.scoring_narrative.went_well` | List of strings |
| Per-question `strengths` | `report.question_assessments[i].strengths` | Tuple of strings |
| Per-question `weaknesses` | `report.question_assessments[i].weaknesses` | Tuple of strings |

### Question Assessment Panel

| Report element | Source field | Path |
|----------------|-------------|------|
| `question_assessments` | `report.question_assessments` | Tuple of `QuestionAssessmentRecord` → `List[QuestionAssessmentDTO]` |

Mapping: `QuestionAssessmentMapper.to_dto(record: QuestionAssessmentRecord) -> QuestionAssessmentDTO` — direct field copy; no computation.

### Token / Generation Panel

| Report element | Source field | Path |
|----------------|-------------|------|
| `total_tokens_used` | `report.generation_metadata.total_tokens_used` | Direct |
| `total_cost_usd` | `report.generation_metadata.total_cost_usd` | Direct (may be `None`) |

---

## 5. Replay Compatibility

### Completeness Verification

For replay, `ReplaySession` must reconstruct all data visible in the Unified Report (scores, narrative, coaching, per-question data) without LLM calls. `ReplaySession` sources data from `SessionHistory`. The following table verifies that every report section can be reconstructed from `SessionHistory` alone.

| Report section | `SessionHistory` source | Complete? |
|----------------|------------------------|-----------|
| Overall score | `session_history.scoring_snapshot.overall_score` | ✅ |
| Hire decision | `session_history.scoring_snapshot.hire_decision` | ✅ |
| Hiring probability | `session_history.scoring_snapshot.hiring_probability` | ✅ |
| Percentile rank | `session_history.scoring_snapshot.percentile_rank` | ✅ |
| Decision explanation | `session_history.scoring_snapshot.decision_explanation` | ✅ |
| Gating | `session_history.scoring_snapshot.gating_triggered/reason` | ✅ |
| Dimension scores | `session_history.scoring_snapshot.scoring_dimensions` | ✅ |
| Dimension justifications | `session_history.scoring_snapshot.scoring_dimensions[i].justification` | ✅ |
| Executive summary | `session_history.scoring_narrative.executive_summary` | ✅ |
| Went well | `session_history.scoring_narrative.went_well` | ✅ |
| Held you back | `session_history.scoring_narrative.held_you_back` | ✅ |
| Knowledge gaps | `session_history.scoring_narrative.knowledge_gaps` | ✅ |
| Next strategy | `session_history.scoring_narrative.next_strategy` | ✅ |
| Improvement suggestions | `session_history.scoring_narrative.improvement_suggestions` | ✅ |
| Per-question scores | `session_history.question_results[i].score` | ✅ |
| Per-question feedback | `session_history.question_results[i].feedback` | ✅ |
| Per-question area | `session_history.question_results[i].area_label` | ✅ |
| Per-question prompt | `session_history.question_results[i].question_prompt` | ✅ |
| Per-question strengths/weaknesses | `session_history.question_results[i].strengths/weaknesses` | ✅ |
| Per-question execution | `session_history.question_results[i].passed_tests/total_tests/execution_status` | ✅ |
| Per-question AI hint | `session_history.question_results[i].ai_hint_explanation/suggestion` | ✅ |
| Narrative insights | `session_history.knowledge_snapshot.narrative.insights` | ✅ |
| Coaching objectives | `session_history.knowledge_snapshot.coaching_snapshot` | ✅ |
| Candidate profile | `session_history.knowledge_snapshot.profile_snapshot` | ✅ |
| Session metadata | `session_history.interview_metadata` | ✅ |
| Context profile | `session_history.context_profile` | ✅ (new field) |
| Generation metadata | `session_history.generation_metadata` | ✅ (new field) |

**Verdict: Replay completeness confirmed.** Every report section is reconstructible from `SessionHistory` without LLM calls.

### Replay Constraints

- Replay never invokes `InterviewEvaluationService`, `NarrativeGenerator`, `CoachingEngine`, or any LLM-backed service (domain invariant I-11).
- `ReplaySession` reads `SessionHistory.question_results`, `SessionHistory.scoring_snapshot`, `SessionHistory.scoring_narrative`, and `SessionHistory.knowledge_snapshot` directly.
- `ReplaySession` does not construct `Report` — it reads `SessionHistory`. `Report` is the production pipeline artifact; `SessionHistory` is the replay source.
- All `Optional` fields in `SessionHistory` (`scoring_snapshot`, `scoring_narrative`, `generation_metadata`) have graceful `None` handling in the replay view — missing sections render as "not available".

---

## 6. Future Extensibility

### Multi-Session Reports

A multi-session report (not in V1.3 scope) would require aggregating data across multiple `SessionHistory` instances. The current model supports this:

- `SessionHistory` carries `interview_index: int` — identifies position in a candidate's history.
- `SessionHistory.scoring_snapshot` carries `overall_score`, `dimension_scores` — directly comparable across sessions.
- `LongitudinalProfile` (EPIC-V13-02) accumulates `CandidateProfileSnapshot` instances from `SessionHistory.knowledge_snapshot.profile_snapshot`.
- A future `MultiSessionReport` artifact would read `List[SessionHistory]` and aggregate without requiring schema changes to any individual artifact.

No schema redesign is required. The `interview_index` field on `Report` and `SessionHistory` is the anchor for cross-session sequencing.

### Longitudinal Profile

`LearningProgress` (already defined in `domain/contracts/progress/learning_progress.py`) consumes `List[SessionHistory]` via `LearningProgressBuilder.with_session_histories()`. The current `SessionHistory` v2.0 schema is fully forward-compatible with this builder:

- `session_history.knowledge_snapshot.profile_snapshot` → `CandidateProfileSnapshot` → `DimensionalScore` list
- `session_history.interview_metadata` → `SessionProgressEntry` metadata
- `session_history.scoring_snapshot.dimension_scores` → scoring trend data

`LearningProgressBuilder` does not need to change when `SessionHistory` bumps to `"2.0"` because it does not read `evaluation_result` (which is the only removed field).

`LongitudinalProfile` (EPIC-V13-02) accumulates `CandidateProfileSnapshot` instances. `SessionHistory.knowledge_snapshot.profile_snapshot` is the source. No schema change to `CandidateProfileSnapshot` or `KnowledgeSnapshot` is required.

### Historical Comparisons

Historical score comparison requires `scoring_snapshot.overall_score` and `scoring_snapshot.scoring_dimensions` across sessions. Both are stored in `SessionHistory.scoring_snapshot`. The `ScoringDimension.dimension_type: PerformanceDimensionType` enum provides a stable key for cross-session dimension alignment.

If the dimension taxonomy changes in a future version, `ScoringDimension.schema_version` (inherited from `ScoringSnapshot.schema_version`) provides the versioning signal. No additional versioning mechanism is required in V1.3.

### Schema Evolution Summary

| Artifact | V1.3 schema_version | Breaking changes | Additive changes safe? |
|----------|---------------------|------------------|------------------------|
| `Report` | `"2.0"` | New required fields | Yes — `extra="forbid"` prevents silent additions |
| `SessionHistory` | `"2.0"` | Removed `evaluation_result`; new required `context_profile` | Yes |
| `ScoringSnapshot` | `"1.0"` | New artifact | Yes |
| `ScoringNarrative` | `"1.0"` | New artifact | Yes |
| `QuestionResultRecord` | `"1.0"` | New artifact | Yes |
| `GenerationMetadata` | `"1.0"` | New artifact | Yes |
| `Narrative` | `"1.0"` | Field rename only (`executive_summary` → `overview_section`) | Rename is breaking; handled by `schema_version` |
| `CandidateProfileSnapshot` | `"1.0"` | None | Yes |

---

## 7. Final Artifact Field Tables (Complete)

### `SessionHistory` v2.0 — Complete Field Set

| Field | Type | Default | Status |
|-------|------|---------|--------|
| `session_id` | `str` | Required | Existing |
| `candidate_identity_id` | `str` | Required | Existing |
| `interview_index` | `int` | Required | Existing |
| `knowledge_snapshot` | `KnowledgeSnapshot` | Required | Existing |
| `transcript` | `tuple[TranscriptEntry, ...]` | `tuple()` | Existing |
| `question_timeline` | `tuple[QuestionTimelineEntry, ...]` | `tuple()` | Existing |
| `question_results` | `tuple[QuestionResultRecord, ...]` | `tuple()` | **NEW** |
| `scoring_snapshot` | `ScoringSnapshot \| None` | `None` | **NEW** (replaces `evaluation_result`) |
| `scoring_narrative` | `ScoringNarrative \| None` | `None` | **NEW** |
| `context_profile` | `InterviewContextProfile` | Required | **NEW** |
| `generation_metadata` | `GenerationMetadata \| None` | `None` | **NEW** |
| `interview_metadata` | `InterviewMetadata` | Required | Existing |
| `language_profile` | `LanguageProfile` | Required | Existing |
| `replay_metadata` | `ReplayMetadata` | `ReplayMetadata()` | Existing |
| `schema_version` | `str` | `"2.0"` | Changed |
| `created_at` | `datetime` | Required | Existing |
| `metadata` | `dict[str, str]` | `{}` | Existing |

### `Report` v2.0 — Complete Field Set

| Field | Type | Default | Status |
|-------|------|---------|--------|
| `report_id` | `str` | Required | Existing |
| `session_id` | `str` | Required | Existing |
| `candidate_identity_id` | `str` | Required | Existing |
| `interview_index` | `int` | Required | Existing |
| `profile_snapshot` | `CandidateProfileSnapshot` | Required | Existing |
| `narrative` | `Narrative` | Required | Existing |
| `coaching_snapshot` | `CoachingSnapshot` | Required | Existing |
| `question_assessments` | `tuple[QuestionAssessmentRecord, ...]` | `tuple()` | **NEW** |
| `scoring` | `ScoringSnapshot` | Required | **NEW** |
| `scoring_narrative` | `ScoringNarrative` | Required | **NEW** |
| `context_profile` | `InterviewContextProfile` | Required | **NEW** |
| `generation_metadata` | `GenerationMetadata \| None` | `None` | **NEW** |
| `role` | `str` | Required | Existing |
| `seniority` | `str` | Required | Existing |
| `interview_type` | `str` | Required | Existing |
| `question_count` | `int` | Required | Existing |
| `knowledge_epoch` | `str` | Required | Existing |
| `schema_version` | `str` | `"2.0"` | Changed |
| `created_at` | `datetime` | Required | Existing |
| `metadata` | `dict[str, str]` | `{}` | Existing |

### `InterviewState` v2.0 — Changed Fields Only

| Action | Field | Type |
|--------|-------|------|
| **REMOVE** | `interview_evaluation` | `Optional[InterviewEvaluation]` |
| **ADD** | `scoring_snapshot` | `ScoringSnapshot \| None` (default `None`) |
| **ADD** | `scoring_narrative` | `ScoringNarrative \| None` (default `None`) |
| RETAIN | `interview_metrics` | `InterviewMetrics \| None` |
| RETAIN | `interview_cost_metrics` | `InterviewCostMetrics \| None` |
| RETAIN | `context_profile` | `InterviewContextProfile` |

---

## 8. Constraint Additions

These constraints amend and extend those in EPIC-01-DOMAIN-CONTRACTS.md §11:

| Rule | Constraint |
|------|-----------|
| `R-11` | `ScoringSnapshot.scoring_dimensions` must not be empty. At least one dimension must be scored. |
| `R-12` | `ScoringSnapshot.dimension_scores`, `dimension_signals`, `weighted_breakdown` dict keys must equal `{d.dimension_type.value for d in scoring_dimensions}`. These three dicts are derived; they must be populated at construction time from `scoring_dimensions`. |
| `R-13` | `SessionHistory.context_profile` is a required field in v2.0. `SessionHistoryBuilder.build()` raises `ValueError` if `context_profile` is not set. |
| `R-14` | `GenerationMetadata` is `Optional` in both `SessionHistory` and `Report`. A missing `GenerationMetadata` renders the token count as `0` in `FinalReportDTO`. No error is raised. |
| `R-15` | `QuestionResultRecord.question_prompt` is the full question text. Truncation is a display concern; it must not be applied at persistence time. |
| `R-16` | `DimensionScoreMapper.map(...)` accepts `tuple[ScoringDimension, ...]` after migration. The three-parameter signature `(dimension_scores, weighted_breakdown, performance_dimensions)` does not exist after EPIC-V13-01. |
| `R-17` | `TokenCalculator.calculate(state)` is not called by `FinalReportDTO.from_report`. Token count is read from `report.generation_metadata.total_tokens_used`. |

---

*This document is the final frozen data model for EPIC-V13-01 and EPIC-V13-05. No modelling decision in either epic may deviate from this specification without a formal ADR amendment.*
