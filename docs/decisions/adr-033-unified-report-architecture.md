# ADR-033 — Unified Report Architecture

**Status:** Accepted  
**Date:** 2026-07-05  
**Owner:** Arch  
**Epic:** EPIC-V13-05 — Unified Report  
**Precondition:** EPIC-01-UNIFIED-REPORT.md planning complete; EPIC-01 Architecture Review complete.

---

## Context

V1.2 left the reporting pipeline in a structurally inconsistent state. Two incompatible sources coexist:

1. **`InterviewEvaluation`** — produced by `EvaluationAggregateNode` via an LLM-backed `InterviewEvaluationService`. Carries all scoring data (`overall_score`, `dimension_scores`, `hire_decision`, `hiring_probability`, `percentile_rank`, `gating_*`), all LLM coaching narrative (`went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions`, `executive_summary`), and per-question assessments (`per_question_assessment`). This is the **only** data source rendered by the UI today via `FinalReportDTO`.

2. **`Report`** (domain) — produced by `report_node` from closed `SessionHistory.knowledge_snapshot`. Carries `profile_snapshot`, `Narrative` (typed `NarrativeInsight` list), and `CoachingSnapshot` (typed `LearningObjective` / `CoachingAction` tree). Declared the authoritative artifact by V1.2 architecture. Not rendered anywhere in the UI.

The architecture review identified five blocking structural gaps that prevent `Report` from becoming the sole report source without additional decisions:

- **Scoring ownership:** scoring fields live only on `InterviewEvaluation`; `Report` has no scoring data.
- **Question assessment gap:** `QuestionAssessmentDTO` depends on live `InterviewState` fields (`questions`, `results_by_question`, `answers`); `area` and `ai_hint` are not persisted in `SessionHistory` or `Report` after session close.
- **Executive summary gap:** `InterviewEvaluation.executive_summary` is an LLM-generated hiring-readiness narrative; `Narrative.executive_summary` inside `Report.narrative` is a separate deterministic placeholder. They are semantically incompatible and cannot replace each other.
- **Coaching narrative gap:** `InterviewEvaluation` coaching dicts (`went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions`) are LLM-generated hiring-context prose. `CoachingSnapshot` is a deterministic rule-based structure from feature signals. They are different pipelines with non-overlapping semantics.
- **`SessionHistory.evaluation_result` residue:** `SessionHistory` embeds an `Optional[InterviewEvaluation]`; after `InterviewEvaluation` is deleted, this field becomes a dead typed reference unless explicitly replaced.

This ADR freezes the architectural decisions required to unblock EPIC-V13-01 (Scoring Pipeline Migration) and EPIC-V13-05 (Unified Report) implementation.

---

## Decision 1 — Unified Scoring Ownership

**Decision:** All scoring fields (`overall_score`, `raw_score`, `adjusted_score`, `dimension_scores`, `dimension_signals`, `hire_decision`, `hiring_probability`, `percentile_rank`, `percentile_explanation`, `level`, `gating_triggered`, `gating_reason`, `weighted_breakdown`, `confidence`) are migrated from `InterviewEvaluation` into a new immutable domain artifact: **`ScoringSnapshot`**.

`ScoringSnapshot` is embedded in `Report` as a required field `report.scoring: ScoringSnapshot`.

`ReportBuilder` accepts `ScoringSnapshot` via `with_scoring(snapshot: ScoringSnapshot)` and embeds it in the built `Report`.

`ScoringSnapshot` is produced by `InterviewEvaluationService` (or its successor after decomposition) and passed to `session_close_node`, which writes it to `SessionHistoryBuilder` and then to `ReportBuilder`.

`ScoringSnapshot` is `frozen=True` with a single builder (`ScoringSnapshotBuilder`). It has no computation methods — it is a pure Projection Artifact (OP-02).

### Rationale

`Report` becomes the sole report artifact. Scoring data must live in `Report` for `FinalReportDTO.from_report(report)` to be field-complete. Introducing `ScoringSnapshot` as a named artifact rather than flattening fields onto `Report` preserves SRP, allows independent versioning, and makes the scoring subsystem's boundary explicit.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Flatten all scoring fields directly onto `Report` | Breaks `Report`'s single responsibility; mixes knowledge-pipeline data with scoring-pipeline data; naming collisions with existing fields |
| Keep scoring on `InterviewEvaluation` and read both artifacts | Preserves the dual-source problem; violates the constitutional requirement of a single report artifact |
| Source scoring from `SessionHistory.evaluation_result` | `evaluation_result` is `Optional[InterviewEvaluation]` — a V1.1 artifact; the goal is to retire it, not reference it more broadly |

### Consequences

**Positive:**
- `Report` becomes self-contained; `FinalReportDTO.from_report(report)` is field-complete.
- `ScoringSnapshot` is independently testable and versionable.
- `InterviewEvaluation` can be deleted once all consumers migrate to `report.scoring`.

**Negative / Risks:**
- New domain artifact requires contract definition, builder, and validator — increases EPIC-V13-01 scope.
- `ReportBuilder` gains a new mandatory parameter; all `ReportBuilder` call sites must be updated.

### Migration Impact

- EPIC-V13-01: define `ScoringSnapshot`, `ScoringSnapshotBuilder`, `ScoringSnapshotValidator`. Extend `ReportBuilder.with_scoring(...)`. Extend `report_node` to receive and embed `ScoringSnapshot`. Update `session_close_node` to pass `ScoringSnapshot` to both `SessionHistoryBuilder` and `ReportBuilder`.
- EPIC-V13-05: `FinalReportDTO.from_report` maps scoring fields from `report.scoring`.

---

## Decision 2 — Question Assessment Ownership

**Decision:** Per-question assessment data is persisted in **`SessionHistory`** via a new embedded tuple: `question_results: tuple[QuestionResultRecord, ...]`.

`QuestionResultRecord` carries: `question_id`, `question_type`, `area_label`, `question_prompt`, `score`, `max_score`, `feedback`, `strengths`, `weaknesses`, `follow_up_question`, `passed_tests`, `total_tests`, `execution_status`, `attempts`, `ai_hint_explanation`, `ai_hint_suggestion`.

`session_close_node` populates `question_results` from `InterviewState.results_by_question` and `InterviewState.questions` before calling `SessionHistoryBuilder`.

`ReportBuilder.with_session_history(history)` reads `history.question_results` and assembles `report.question_assessments: tuple[QuestionAssessmentRecord, ...]`.

`FinalReportDTO.from_report(report)` maps `report.question_assessments` to `List[QuestionAssessmentDTO]`.

`per_question_assessment` on `InterviewEvaluation` is **not** the source for this path. It may be deleted with `InterviewEvaluation`.

### Rationale

Live `InterviewState` is not available during replay (`replay_node` has no access to original `results_by_question`). The Unified Report and Replay UI must both serve question-level data from the same closed artifact. `SessionHistory` is the correct closure point. `Report` is assembled from `SessionHistory` — embedding question results in `SessionHistory` makes the chain self-consistent and replay-compatible. Embedding directly in `Report` without a `SessionHistory` path would require `report_node` to read from `InterviewState` directly, which violates the Sole-Writer PAT for `report_node`.

The `area_label` field resolves the current gap where `area` (derived from `Question.area` via `InterviewAreaMapper`) is not persisted anywhere after session close.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Keep `QuestionMapper` reading live `InterviewState` | Incompatible with replay; ties `FinalReportDTO` to live session lifetime; violates single-source goal |
| Embed `question_assessments` directly in `Report` without `SessionHistory` extension | Requires `report_node` to read `InterviewState.results_by_question` directly — violates Sole-Writer PAT; breaks replay compatibility |
| Derive from `SessionHistory.transcript` + `evaluation_result.per_question_assessment` | `area_label` and `ai_hint` are not present in transcript; `per_question_assessment` does not carry them; reconstruction would be partial |

### Consequences

**Positive:**
- Question data is persisted at the correct closure point.
- `Report` assembles question assessments from `SessionHistory` — consistent with the existing `ReportBuilder` pattern.
- Replay UI can render per-question data from `ReplaySession` (which reads `SessionHistory`).

**Negative / Risks:**
- `SessionHistory` contract breaks; `session_close_node` must populate `question_results`.
- `SessionHistory.schema_version` must be incremented to `"2.0"`.
- `ReportBuilder.with_session_history` gains new assembly logic.

### Migration Impact

- EPIC-V13-01: define `QuestionResultRecord`. Extend `SessionHistoryBuilder.with_question_results(...)`. Update `session_close_node` to populate it. Extend `ReportBuilder` to assemble `question_assessments` from `history.question_results`. Define `QuestionAssessmentRecord` on `Report`.
- EPIC-V13-05: `FinalReportDTO.from_report` maps `report.question_assessments` → `List[QuestionAssessmentDTO]`. `QuestionMapper` call in `FinalReportDTO.from_components` is deleted.

---

## Decision 3 — Executive Summary Ownership

**Decision:** The LLM-generated hiring-readiness executive summary is migrated into **`ScoringNarrative`** — a new immutable domain artifact embedded in `Report` as `report.scoring_narrative: ScoringNarrative`.

`ScoringNarrative` carries: `executive_summary: str`, `went_well: tuple[str, ...]`, `held_you_back: tuple[ScoringNarrativeItem, ...]`, `knowledge_gaps: tuple[ScoringNarrativeItem, ...]`, `next_strategy: tuple[ScoringNarrativeItem, ...]`, `improvement_suggestions: tuple[str, ...]`.

`ScoringNarrativeItem` carries: `category`, `description`, `why_it_matters`, and one additional context field specific to each section (e.g. `impact` for `held_you_back`, `interview_impact` for `knowledge_gaps`, `expected_improvement` for `next_strategy`). These match the existing dict shapes consumed by the UI section renderers, promoted to typed domain objects.

`ScoringNarrative` is produced by `EvaluationNarrativeAssembler` (or its successor) and passed through `session_close_node` → `SessionHistoryBuilder` → `ReportBuilder`.

`Narrative.executive_summary` (the deterministic `NarrativeSection` from the knowledge pipeline) is **renamed** to `Narrative.overview_section` to eliminate the naming collision. This rename is applied before any migration code touches either field.

### Rationale

The `executive_summary` from `InterviewEvaluation` is the primary candidate-facing narrative. It uses scoring + LLM context not available in the knowledge pipeline. It cannot be derived from `Narrative.insights` (which are feature-grounded atomic findings, not hiring summaries). Migrating it alongside all coaching dicts into a single `ScoringNarrative` artifact co-locates related LLM outputs, keeps them distinct from the deterministic `Narrative` (knowledge pipeline), and gives them a typed domain representation that survives `InterviewEvaluation` deletion.

Renaming `Narrative.executive_summary` → `Narrative.overview_section` eliminates the naming collision at source, preventing silent substitution by any implementer.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Accept `Narrative.executive_summary` (deterministic placeholder) as the production executive summary | Semantic downgrade; placeholder prose is not equivalent to LLM hiring-readiness summary; unacceptable for production report |
| Derive executive summary from `Report` fields at render time | Computation in projection; violates P-01 (The Runtime Computes; Projection Never Computes) from the Architecture Constitution |
| Embed `executive_summary` as a flat string field on `Report` | Loses semantic grouping with related coaching dicts; `went_well` and `executive_summary` are from the same LLM call; separating them creates partial artifact risk |

### Consequences

**Positive:**
- All LLM-generated report prose is co-located in `ScoringNarrative`.
- Naming collision eliminated; no silent substitution risk.
- `FinalReportDTO` maps all prose fields from `report.scoring_narrative`.

**Negative / Risks:**
- `EvaluationNarrativeAssembler` output must be captured into `ScoringNarrative` before `session_close_node` runs (or within it).
- `Narrative.overview_section` rename touches `Narrative` contract and all its readers.

### Migration Impact

- EPIC-V13-01: define `ScoringNarrative`, `ScoringNarrativeItem`. Extend `ReportBuilder.with_scoring_narrative(...)`. Rename `Narrative.executive_summary` → `Narrative.overview_section`. Update all readers of `Narrative.executive_summary`.
- EPIC-V13-05: `FinalReportDTO.from_report` maps `report.scoring_narrative` for all prose sections.

---

## Decision 4 — Coaching Narrative Ownership

**Decision:** The LLM coaching dicts (`went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions`) are **migrated into `ScoringNarrative`** (Decision 3) as typed fields. `CoachingSnapshot` is **not** extended to carry these fields.

`CoachingSnapshot` retains its current scope: deterministic, feature-signal-driven `LearningObjective` / `CoachingAction` / `StudyRecommendation` tree. It is surfaced in a new dedicated coaching section of the Unified Report.

The Unified Report thus contains **two distinct coaching surfaces**:

1. **Scoring narrative coaching** (from `report.scoring_narrative`): LLM-generated, hiring-context coaching. Sections: `went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions`. These map directly to the existing report section renderers (`render_went_well`, `render_held_you_back`, etc.) with no UI change.
2. **Knowledge-pipeline coaching** (from `report.coaching_snapshot`): Deterministic, feature-grounded `LearningObjective` / `CoachingAction` tree. New report section: `render_coaching_objectives`. New report section: `render_study_recommendations`.

These two coaching surfaces are conceptually complementary: the scoring narrative explains what happened in the interview; the coaching snapshot prescribes what to study next.

### Rationale

`CoachingSnapshot` and the `InterviewEvaluation` coaching dicts are produced by different pipelines (deterministic rules vs LLM), from different inputs (feature signals vs question evaluations + scoring), with different semantic goals (study prescription vs hiring-context narrative). Merging them into a single artifact would require `CoachingEngine` to become LLM-dependent, or `EvaluationNarrativeAssembler` to become knowledge-pipeline-dependent — both violating the existing architectural separation. Keeping them separate under `Report` as distinct fields (`report.scoring_narrative` and `report.coaching_snapshot`) preserves pipeline independence and makes the report composition explicit.

`went_well` has no equivalent in `CoachingSnapshot` (the `CoachingEngine` models only gaps and objectives, not positive reinforcement). Placing `went_well` in `ScoringNarrative` is the only path that preserves it without redesigning `CoachingEngine`.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Extend `CoachingSnapshot` to absorb LLM coaching dicts | Makes `CoachingEngine` LLM-dependent or creates mixed-pipeline artifact; violates SRP and pipeline independence; `went_well` has no natural coaching model |
| Delete LLM coaching dicts and rely solely on `CoachingSnapshot` | Loss of `went_well`, `held_you_back`, `knowledge_gaps` in the form currently rendered; semantic downgrade for the candidate-facing report; unacceptable for V1.3 |
| Produce a merged coaching view at render time from both sources | Computation in projection; violates P-01 |

### Consequences

**Positive:**
- Pipeline separation preserved: deterministic coaching and LLM narrative coaching remain independent.
- No redesign of `CoachingEngine` or `EvaluationNarrativeAssembler`.
- `went_well` preserved in production report.
- New knowledge-pipeline coaching sections added to Unified Report without disrupting existing sections.

**Negative / Risks:**
- Report has two coaching sources — implementers and candidates must understand the distinction.
- Section ordering in the Unified Report must clearly communicate the two surfaces (e.g. "Interview Feedback" for scoring narrative vs "Study Plan" for coaching snapshot).

### Migration Impact

- EPIC-V13-01: `went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions` migrate to `ScoringNarrative` (Decision 3). No `CoachingSnapshot` changes.
- EPIC-V13-05: New `render_coaching_objectives` and `render_study_recommendations` sections added. Existing scoring narrative sections (`render_went_well`, `render_held_you_back`, etc.) re-sourced from `report.scoring_narrative`.

---

## Decision 5 — `SessionHistory.evaluation_result` Disposition

**Decision:** `SessionHistory.evaluation_result: Optional[InterviewEvaluation]` is **replaced** by `SessionHistory.scoring_snapshot: Optional[ScoringSnapshot]` in the same migration increment that defines `ScoringSnapshot` (Decision 1).

`session_close_node` writes `ScoringSnapshot` (the same instance passed to `ReportBuilder`) into `SessionHistoryBuilder.with_scoring_snapshot(...)`.

`SessionHistorySummary.has_evaluation` is renamed to `has_scoring_snapshot`.

`SessionHistoryStatistics` equivalent field is updated accordingly.

`SessionHistory.schema_version` is incremented to `"2.0"` to reflect the combined changes from this ADR (new `question_results` field, `scoring_snapshot` replacing `evaluation_result`).

`evaluation_result` and the `InterviewEvaluation` type are **not** referenced from `SessionHistory` after this migration.

### Rationale

Retaining `evaluation_result` as a dead typed field creates a permanent reference to the deleted `InterviewEvaluation` contract. Replacing it with `ScoringSnapshot` preserves archival scoring value (overall score, dimension scores, hire decision — useful for any future cross-session analysis or replay scoring display) without retaining the full `InterviewEvaluation` structure. Deleting the field entirely would lose all archival scoring context. The `Optional` constraint is preserved — sessions where `EvaluationAggregateNode` was bypassed (or failed non-fatally) produce a `None` scoring snapshot.

Since no production `SessionHistory` persistence layer exists at the time of this ADR, there is no live data migration cost.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Retain `evaluation_result: Optional[InterviewEvaluation]` until `InterviewEvaluation` is deleted, then null it | Permanent dead field after deletion; any future code referencing `evaluation_result` would need to handle a permanent `None`; semantically confusing |
| Delete `evaluation_result` with no replacement | Loses archival scoring context; `has_scoring_snapshot` boolean has no data backing it; no recovery path if cross-session scoring analysis is required |
| Retain full `InterviewEvaluation` embedded in `SessionHistory` indefinitely | Prevents `InterviewEvaluation` deletion; perpetuates dual-source architecture in the persistence layer |

### Consequences

**Positive:**
- `SessionHistory` severs its `InterviewEvaluation` dependency in the same increment.
- Archival scoring context preserved in a neutral, typed artifact.
- `SessionHistory` schema version explicitly bumped — signals the breaking change.

**Negative / Risks:**
- Breaking contract change to `SessionHistory`; any test or code that constructs `SessionHistory` with `evaluation_result` must be updated.
- `ScoringSnapshot` must be defined before `SessionHistory` is updated (sequential dependency within EPIC-V13-01).

### Migration Impact

- EPIC-V13-01: Replace `evaluation_result` field with `scoring_snapshot: Optional[ScoringSnapshot]`. Update `SessionHistoryBuilder`. Update `session_close_node`. Update `SessionHistorySummary`, `SessionHistoryStatistics`. Increment `schema_version` to `"2.0"`.
- No live data migration required (no production persistence layer).

---

## Decision 6 — Unified Report Target Architecture

**Decision:** The Unified Report is produced by a single pipeline:

```
InterviewState (runtime)
  ↓ session_close_node
SessionHistory v2.0
  ├── knowledge_snapshot (profile_snapshot + narrative + coaching_snapshot)
  ├── interview_metadata
  ├── transcript
  ├── question_timeline
  ├── question_results: tuple[QuestionResultRecord, ...]      ← NEW (Decision 2)
  ├── scoring_snapshot: Optional[ScoringSnapshot]             ← NEW (Decision 5)
  └── scoring_narrative: Optional[ScoringNarrative]           ← NEW (Decision 3/4)

  ↓ report_node → ReportBuilder.with_session_history(history)
Report v2.0
  ├── profile_snapshot: CandidateProfileSnapshot
  ├── narrative: Narrative                                     (overview_section renamed)
  ├── coaching_snapshot: CoachingSnapshot
  ├── question_assessments: tuple[QuestionAssessmentRecord, ...] ← NEW (Decision 2)
  ├── scoring: ScoringSnapshot                                 ← NEW (Decision 1)
  └── scoring_narrative: ScoringNarrative                      ← NEW (Decision 3/4)

  ↓ FinalReportDTO.from_report(report)
FinalReportDTO (rebuilt, sole factory from_report)
  ├── scoring fields         ← from report.scoring
  ├── executive_summary      ← from report.scoring_narrative.executive_summary
  ├── coaching dicts         ← from report.scoring_narrative (went_well, held_you_back, ...)
  ├── question_assessments   ← from report.question_assessments
  ├── narrative_insights     ← NEW: from report.narrative.insights
  └── coaching_objectives    ← NEW: from report.coaching_snapshot

  ↓ ReportViewModelBuilder → render_* → UIResponse.report_output
```

**Invariants enforced by this architecture:**

- I-A: `FinalReportDTO.from_report(report: Report)` is the **sole** `FinalReportDTO` factory. `from_components` does not exist.
- I-B: `InterviewEvaluation` has **zero** references in any file under `app/ui/`, `app/graph/`, or `services/` report-related paths after EPIC-V13-01 is complete.
- I-C: `report_node` is the **sole writer** of `InterviewState.report`.
- I-D: `session_close_node` is the **sole writer** of `InterviewState.session_history`.
- I-E: `ReportBuilder` reads `SessionHistory` only — no live `InterviewState` access.
- I-F: All LLM computation for report data occurs **before** `session_close_node` completes. `report_node` performs no computation.
- I-G: `Narrative.overview_section` (renamed from `executive_summary`) is never rendered as a hiring-readiness summary; `ScoringNarrative.executive_summary` is the production hiring summary.

**Graph node ordering (post-migration, no change to sequence):**
```
completion → evaluation_aggregate → session_close → report → END
```
`evaluation_aggregate` produces `ScoringSnapshot` and `ScoringNarrative` (via updated `InterviewEvaluationService`). `session_close` receives them and embeds them in `SessionHistory`. `report_node` assembles `Report` from closed `SessionHistory`.

### Rationale

This architecture satisfies all six constitutional principles: (P-01) no computation in projection; (P-02) single ownership; (P-03) immutable contracts; (P-04) LangGraph as sole orchestrator; (P-05) builders assemble, engines compute. It eliminates the dual-source problem by making `Report` self-contained. It preserves all current UI sections and adds new ones without breaking existing behavior.

### Consequences

**Positive:**
- `Report` is self-contained and replay-compatible.
- `FinalReportDTO` has a single, testable factory.
- All report content is traceable to `Report` fields.
- Replay UI can source all data from `ReplaySession` (which reads `SessionHistory`).

**Negative / Risks:**
- EPIC-V13-01 scope is larger than originally described in the master plan: it must define `ScoringSnapshot`, `ScoringNarrative`, `ScoringNarrativeItem`, `QuestionResultRecord`, `QuestionAssessmentRecord`, update `SessionHistory`, update `ReportBuilder`, and update `session_close_node`. These changes must ship atomically — no intermediate dual-factory period.
- `SessionHistory.schema_version` bumps to `"2.0"` — all `SessionHistory` construction paths must be updated.
- `Narrative.overview_section` rename touches all `Narrative` readers.

### Migration Impact

This decision is the authoritative target for EPIC-V13-01 and EPIC-V13-05 implementation. All implementation decisions must be traceable to one of Decisions 1–5 above or require a new ADR.

---

## Implementation Evidence

Artifacts to be created or modified (owned by EPIC-V13-01 unless noted):

| Artifact | Action | Owner |
|---|---|---|
| `domain/contracts/report/scoring_snapshot.py` | **Create** `ScoringSnapshot`, `ScoringSnapshotBuilder` | EPIC-V13-01 |
| `domain/contracts/report/scoring_narrative.py` | **Create** `ScoringNarrative`, `ScoringNarrativeItem` | EPIC-V13-01 |
| `domain/contracts/session_history/question_result_record.py` | **Create** `QuestionResultRecord` | EPIC-V13-01 |
| `domain/contracts/report/question_assessment_record.py` | **Create** `QuestionAssessmentRecord` | EPIC-V13-01 |
| `domain/contracts/report/report.py` | Extend: add `scoring`, `scoring_narrative`, `question_assessments` | EPIC-V13-01 |
| `domain/contracts/report/report_builder.py` | Extend: `with_scoring`, `with_scoring_narrative`, `with_question_assessments` | EPIC-V13-01 |
| `domain/contracts/session_history/session_history.py` | Replace `evaluation_result` → `scoring_snapshot`; add `question_results`; bump `schema_version` to `"2.0"` | EPIC-V13-01 |
| `domain/contracts/session_history/session_history_builder.py` | Update setters | EPIC-V13-01 |
| `domain/contracts/narrative/narrative.py` | Rename `executive_summary` → `overview_section` | EPIC-V13-01 |
| `app/graph/nodes/session_close_node.py` | Populate `question_results`, `scoring_snapshot`, `scoring_narrative` in `SessionHistoryBuilder` | EPIC-V13-01 |
| `app/graph/nodes/evaluation_aggregate_node.py` | Produce `ScoringSnapshot` + `ScoringNarrative`; write to `InterviewState` (new fields) | EPIC-V13-01 |
| `app/ui/dto/final_report_dto.py` | Rebuild: replace `from_components` with `from_report(report: Report)` | EPIC-V13-05 |
| `app/ui/mappers/interview_state_mapper.py` | Update: call `from_report(state.report)` | EPIC-V13-05 |
| `app/ui/builders/ui_response_builder.py` | Update: read `state.report` only | EPIC-V13-05 |
| `app/ui/views/report/report_view_model_builder.py` | Add narrative_insights, coaching_objectives sections | EPIC-V13-05 |
| `domain/contracts/interview/interview_evaluation.py` | **Delete** | EPIC-V13-01 |
| `services/interview_evaluation_service.py` | Refactor to produce `ScoringSnapshot` + `ScoringNarrative`; delete `InterviewEvaluation` assembly | EPIC-V13-01 |
| `domain/contracts/interview_state/base.py` | Remove `interview_evaluation`; add `scoring_snapshot`, `scoring_narrative` fields | EPIC-V13-01 |

## Review Trigger

This ADR must be revisited if:

- The V1.3 coaching pipeline is redesigned to merge LLM and deterministic coaching outputs.
- A production persistence layer for `SessionHistory` is introduced (schema migration required).
- `ScoringNarrative` content is changed to be derived rather than LLM-generated.
- EPIC-V13-02 (`LongitudinalProfile`) requires scoring data from `SessionHistory.scoring_snapshot` — confirm `ScoringSnapshot` field set is sufficient.
