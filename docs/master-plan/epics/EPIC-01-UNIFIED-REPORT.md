# EPIC-V13-05 — Unified Report

**Status:** PLANNING  
**Version:** 1.0  
**Date:** 2026-07-05  
**Precondition:** V1.2 RC2 frozen. V1.3 master plan approved. No production code modified.  
**Authority:** Governed by `V13-PRODUCT-MASTER-PLAN.md` §EPIC-V13-05 and the Architecture Constitution.

---

## Vision

`Report` was introduced in V1.2 as the sole authoritative domain artifact for session knowledge: profile snapshot, narrative insights, and coaching snapshot. However, the presentation layer never migrated to consume it. `InterviewEvaluation` — a V1.1 scoring artifact — remains the primary data source for every rendered report section, every export, and every routing decision in the UI beyond the `UIStateMachine.REPORT` state gate.

This means two incompatible truths coexist in production:

1. `Report` is declared the authoritative artifact by architecture.
2. `InterviewEvaluation` is what is actually rendered, exported, and consumed by the UI.

EPIC-V13-05 ends this duality. Its purpose is to produce a **single, cohesive session report** that renders all session artifacts from `Report` as the sole data source, with no secondary read from `InterviewEvaluation`, `SessionHistory`, or any legacy path. The Unified Report is the primary deliverable of every completed session.

This epic depends on EPIC-V13-01 (scoring pipeline migration), which must promote `Report` to carry scoring data before EPIC-V13-05 can consolidate the presentation layer onto it. It also depends on EPIC-V13-02 (progress trend panel), EPIC-V13-03 (replay link), and EPIC-V13-06 (explainability anchors) for its full content scope.

---

## Current State

### Dual-Source Architecture

The report rendering pipeline is split across two incompatible sources:

| Source | Fields it provides today | Consumed by |
|--------|--------------------------|-------------|
| `InterviewEvaluation` | `overall_score`, `raw_score`, `adjusted_score`, `executive_summary`, `performance_dimensions`, `dimension_scores`, `dimension_signals`, `level`, `hire_decision`, `decision_explanation`, `hiring_probability`, `percentile_rank`, `percentile_explanation`, `gating_triggered`, `gating_reason`, `weighted_breakdown`, `per_question_assessment`, `improvement_suggestions`, `went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `confidence` | `FinalReportDTO.from_components`, all UI sections, PDF/JSON export |
| `Report` (domain) | `profile_snapshot` (features), `narrative` (NarrativeInsight list), `coaching_snapshot` (CoachingCollection), session metadata | **Not rendered anywhere.** Used only as a routing gate in `UIStateMachine` and `UIResponseBuilder`. |

### `InterviewEvaluation` — Sole Presentation Source

`InterviewEvaluation` is constructed by `EvaluationAggregateNode` via `InterviewEvaluationService`, written into `InterviewState.interview_evaluation`, and embedded in `SessionHistory.evaluation_result`. Every rendered section of the current report HTML reads from it via `FinalReportDTO`.

`InterviewEvaluation` carries scoring data (`overall_score`, `dimension_scores`, `hire_decision`, etc.) and coaching narrative data (`went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions`) as raw `List[Dict]` / `List[str]` structures populated by `EvaluationNarrativeAssembler`.

### `Report` — Construction Complete, Rendering Absent

`Report` is produced by `report_node` (sole writer), assembled by `ReportBuilder` from a closed `SessionHistory`. It contains:

- `profile_snapshot: CandidateProfileSnapshot` — feature-level profile of the candidate
- `narrative: Narrative` — typed `NarrativeInsight` list with `source_feature_id`, `confidence`, `is_traceable`
- `coaching_snapshot: CoachingSnapshot` — `CoachingCollection` with typed `LearningObjective` → `CoachingAction` tree

None of these are projected to the UI. `Report` appears in the graph, is written to `InterviewState.report`, and then used only as a boolean gate: `state.report is not None` triggers `UIState.REPORT`. All HTML rendering reads from `InterviewState.interview_evaluation`.

### `FinalReportDTO` — Structural Gap

`FinalReportDTO.from_components(state, final_evaluation)` accepts `InterviewState` and `InterviewEvaluation`. It maps all fields from `InterviewEvaluation`. It maps `question_assessments` from `InterviewState` via `QuestionMapper`. It reads `state.report` only as a guard: the mapper raises `ValueError` if `state.report is None`, but never reads any field from it.

The consequence: `FinalReportDTO` structurally depends on `InterviewEvaluation` for 100% of its scoring and narrative content.

### `UIStateMachine` — Report Gate Only

`UIStateMachine.resolve()` transitions to `UIState.REPORT` based on `state.report is not None`. This correctly uses `Report` as the gate. But `UIResponseBuilder._build_report()` reads `state.interview_evaluation` to actually build the rendered output. The two conditions must both be satisfied today — `report` gates the state, `interview_evaluation` provides the data.

### `UIResponseBuilder` / `UIResponse.report_output`

`UIResponseBuilder._build_report()` calls `FinalReportDTO.from_components(state, state.interview_evaluation)` and then `build_report_markdown(dto)`. The output is a string assigned to `UIResponse.report_output` (an HTML string field on `UIResponse`, **not** a field on `InterviewState`). Note: `InterviewState` does not have a `report_output` field; that dead field is referenced in planning documents but does not exist in code.

### Report Sections and Their Current Sources

All rendered sections come from `FinalReportDTO`, which in turn comes from `InterviewEvaluation`:

| Section | Renderer | Current source field |
|---------|----------|---------------------|
| Overall score / hire decision | `render_overall` | `overall_score`, `hire_decision`, `hiring_probability` |
| Executive summary | `render_executive` | `executive_summary` |
| Went well | `render_went_well` | `went_well: List[str]` |
| Held you back | `render_held_you_back` | `held_you_back: List[Dict]` |
| Knowledge gaps | `render_knowledge_gaps` | `knowledge_gaps: List[Dict]` |
| Next strategy | `render_next_strategy` | `next_strategy: List[Dict]` |
| Performance dimensions | `render_performance` | `dimension_scores` via VM |
| Dimension insights | `render_dimensions` | `dimension_signals`, `weighted_breakdown` |
| Question assessments | `render_questions` | `question_assessments` from QuestionMapper |
| Market position | `render_market` | `overall_score`, `percentile_rank` |
| Hire decision detail | `render_decision` | `decision_explanation`, `gating_*` |
| Signal insights | `render_signals` | `dimension_signals` |
| Improvement roadmap | `render_roadmap` | `improvement_suggestions` |
| Radar chart | `radar_chart` | Dimension names/scores |
| Distribution chart | `distribution_chart` | Percentile |

None of these sections consume `Report.narrative`, `Report.coaching_snapshot`, or `Report.profile_snapshot`.

### `LearningProgress` — Domain-Only, Not Wired

`LearningProgress` exists in `domain/contracts/progress/learning_progress.py` with a builder and validator. It is not wired to any service, graph node, or UI component. `ProgressTracker` is documented but not implemented. `LongitudinalProfile` is planned but does not exist in code.

### `NarrativeInsight` and `CoachingAction` — Not Surfaced

`NarrativeInsight` carries `source_feature_id: FeatureIdentity`, `is_traceable: bool`, and typed `NarrativeInsightType`. `CoachingAction` carries `action_id`, `objective_id`, `category`, `description`, and `tags`. Neither is rendered in any UI component. The explainability architecture exists in the domain layer but has no presentation path.

### Export Path

`export_pdf_handler` and `export_json_handler` both call `InterviewStateMapper.to_final_report_dto(state)`, which also gates on `state.report` but reads from `state.interview_evaluation`. Both export formats are downstream of the same dual-source structural problem.

---

## Target State

### Single Source of Truth

After EPIC-V13-05 completes:

- `Report` is the **sole data source** for all report rendering, export, and presentation routing.
- `FinalReportDTO` is rebuilt to read exclusively from `Report` (post-EPIC-V13-01, `Report` carries scoring data).
- `InterviewEvaluation` is not referenced by any presentation consumer.
- `UIResponseBuilder._build_report()` reads `state.report` directly.
- All rendered sections source their data from `Report` fields.

### Extended `Report` Structure (post-EPIC-V13-01)

After the scoring pipeline migration (EPIC-V13-01), `Report` must carry scoring fields currently held by `InterviewEvaluation`. The exact extension is defined in EPIC-V13-01. The Unified Report assumes this extension is complete. `Report` will carry:

- All current domain fields: `profile_snapshot`, `narrative`, `coaching_snapshot`, session metadata.
- All scoring fields migrated from `InterviewEvaluation`: `overall_score`, `dimension_scores`, `dimension_signals`, `hire_decision`, `hiring_probability`, `percentile_rank`, `executive_summary`, etc.
- All coaching narrative fields migrated from `InterviewEvaluation`: `went_well`, `held_you_back`, `knowledge_gaps`, `next_strategy`, `improvement_suggestions` — promoted to typed domain structures.

### Unified `FinalReportDTO`

`FinalReportDTO.from_report(report: Report)` replaces `FinalReportDTO.from_components(state, evaluation)`. It maps all fields from `Report` only. `InterviewState` is no longer a parameter. `QuestionMapper` accesses question data through `Report` (via `SessionHistory` linkage or embedded question results).

### Added Sections

The Unified Report includes sections not present in the current report:

| New section | Source |
|-------------|--------|
| Narrative insights panel | `Report.narrative.insights` — typed `NarrativeInsight` list with `NarrativeInsightType`, `prose`, `source_feature_id` |
| Coaching objectives panel | `Report.coaching_snapshot` — `LearningObjective` → `CoachingAction` tree |
| Explainability anchors (EPIC-V13-06) | `NarrativeInsight.source_feature_id` linked to session `Observation` |
| Progress trend panel (EPIC-V13-02) | `LongitudinalProfile` (cross-session; post-EPIC-V13-02) |
| Replay entry point (EPIC-V13-03) | `ReplaySession` link or session id (post-EPIC-V13-03) |

### `UIStateMachine` — Simplified Gate

After migration: `UIStateMachine` gates on `state.report is not None`. No reference to `interview_evaluation` required. The existing gate condition is already correct; it requires no change.

### Export Path — Unified

Both PDF and JSON exports consume `FinalReportDTO.from_report(state.report)`. `InterviewStateMapper.to_final_report_dto()` is replaced or updated to use the new factory.

### `LearningProgress` — Wired (post-EPIC-V13-02)

`LearningProgress` is computed from `LongitudinalProfile` and surfaced in the progress trend panel. `ProgressTracker` is implemented as the service that derives `LearningProgress` from accumulated `CandidateProfileSnapshot` instances. The trend panel renders only when `LongitudinalProfile.session_count >= 3`.

---

## Architectural Impact

### Affected Subsystems

#### Graph Layer

| Node | Impact |
|------|--------|
| `evaluation_aggregate_node` | Upstream dependency. After EPIC-V13-01, writes scoring into `Report` (via `ReportBuilder` extension), not only `interview_evaluation`. |
| `session_close_node` | Must ensure `SessionHistory.knowledge_snapshot` carries all data required by the extended `ReportBuilder`. |
| `report_node` | After EPIC-V13-01, `ReportBuilder` is extended to include scoring fields. `report_node` produces a complete `Report` with no missing presentation fields. |

#### Domain Contracts

| Artifact | Impact |
|----------|--------|
| `Report` | Extended by EPIC-V13-01 to carry scoring fields. Consumed by `FinalReportDTO` after migration. |
| `ReportBuilder` | Extended by EPIC-V13-01 to assemble scoring fields from `InterviewEvaluation` (during migration) or directly from scoring data. |
| `FinalReportDTO` | **Breaking change:** `from_components(state, evaluation)` replaced by `from_report(report: Report)`. All field mappings updated. |
| `InterviewEvaluation` | **Deleted** by EPIC-V13-01 once migration is complete. No reference survives in any presentation path. |
| `NarrativeInsight` | Promoted from domain-only to actively rendered. `is_traceable`, `source_feature_id` become UI-visible fields. |
| `CoachingAction` | Promoted from domain-only to actively rendered. `category`, `description`, `tags` become UI-visible fields. |
| `LearningProgress` | Wired to UI progress trend panel (post-EPIC-V13-02). |
| `CandidateProfileSnapshot` | Rendered in profile section of Unified Report. |

#### UI Layer

| Component | Impact |
|-----------|--------|
| `UIResponseBuilder._build_report` | Signature changes: reads `state.report` instead of `state.interview_evaluation`. |
| `FinalReportDTO.from_components` | Replaced by `from_report(report)`. All callers updated. |
| `InterviewStateMapper.to_final_report_dto` | Updated to call `FinalReportDTO.from_report(state.report)`. Guard on `state.report is not None` retained. |
| All report section renderers | Potential field name changes if `Report`-sourced fields use different naming conventions than `InterviewEvaluation`-sourced fields. |
| `ReportViewModelBuilder` | Updated to consume new `FinalReportDTO` shape. |
| `render_*` section functions | Updated for new/renamed fields: narrative section added, coaching section added. |
| `radar_chart`, `distribution_chart` | Field sources unchanged if dimension data naming is preserved. |
| Export handlers | Updated to call `FinalReportDTO.from_report(state.report)` via updated mapper. |
| `report_section` (layout) | No structural change; receives `UIResponse.report_output` HTML string as before. |

#### State Layer

| Field | Impact |
|-------|--------|
| `InterviewState.interview_evaluation` | **Deleted** once EPIC-V13-01 is complete. |
| `InterviewState.report` | Promoted from routing gate to primary data source for all report consumers. |
| `UIResponse.report_output` | Continues to hold rendered HTML string. No structural change. |

#### DTOs

| DTO | Impact |
|-----|--------|
| `FinalReportDTO` | Rebuilt. New factory. New field set aligned to `Report` structure. |
| `DimensionScoreDTO` | Source changes from `InterviewEvaluation.performance_dimensions` to `Report` dimension fields. |
| `QuestionAssessmentDTO` | Source changes; must be derivable from `Report` (requires question result data in `Report` or in linked `SessionHistory`). |

#### Services

| Service | Impact |
|---------|--------|
| `InterviewEvaluationService` | **Deleted** once `InterviewEvaluation` is retired (EPIC-V13-01). |
| `EvaluationNarrativeAssembler` | **Deleted** once coaching narrative is sourced from `Report.coaching_snapshot`. |
| `ReportInsightBuilder` | Rewritten to consume `Report.narrative` and `Report.coaching_snapshot` instead of `InterviewEvaluation` signal dicts. |
| `ReportExportService` | Updated to consume `FinalReportDTO` from `Report`. |
| `ProgressTracker` (new) | Implemented as service that derives `LearningProgress` from `LongitudinalProfile`. |

#### Tests

| Test area | Impact |
|-----------|--------|
| `FinalReportDTO` tests | All fixture construction migrated from `InterviewEvaluation`-based to `Report`-based. |
| Report section renderer tests | Updated fixtures. New sections (narrative, coaching) require new test cases. |
| `UIResponseBuilder` tests | Updated: `state.interview_evaluation` fixtures removed; `state.report` fixtures used. |
| Export handler tests | Updated: `to_final_report_dto` now accepts `Report`. |
| Integration tests for full report path | Updated to assert no `InterviewEvaluation` read. |

---

## Migration Strategy

### Phase 0 — Prerequisite Confirmation

Confirm all four upstream epics are complete before starting EPIC-V13-05 implementation:

- EPIC-V13-01: `Report` carries scoring fields. `InterviewEvaluation` is retired and deleted. `FinalReportDTO` gate is broken (requires rebuild).
- EPIC-V13-02: `LongitudinalProfile` is persisted per session. `LearningProgress` is computable.
- EPIC-V13-03: `ReplaySession` is produced by `replay_node`. Replay link is available.
- EPIC-V13-06: `NarrativeInsight.source_feature_id` is validated before report render. Evidence anchors are defined.

Do not begin EPIC-V13-05 implementation until EPIC-V13-01 is complete. The other three epics may be in progress, but their output fields must have stable contracts before wiring into `FinalReportDTO`.

### Phase 1 — `FinalReportDTO` Rebuild

Rebuild `FinalReportDTO.from_report(report: Report)` to map all fields from the extended `Report` (post-EPIC-V13-01). This is a breaking change. All existing callers of `from_components` must be updated in the same increment. No intermediate dual-factory period.

After Phase 1:
- `from_components` does not exist.
- `from_report` is the sole factory.
- All UI section renderers receive the same `FinalReportDTO` shape as before (field names preserved where possible to minimize section churn).

### Phase 2 — `UIResponseBuilder` and Mapper Migration

Update `UIResponseBuilder._build_report()` to call `FinalReportDTO.from_report(state.report)`. Update `InterviewStateMapper.to_final_report_dto()`. Update export handlers. Validate that all rendered output is identical to pre-migration output (regression baseline: same test session data produces identical rendered HTML).

After Phase 2:
- `state.interview_evaluation` is not referenced by any presentation consumer.
- `InterviewEvaluation` has zero remaining production consumers.

### Phase 3 — New Sections: Narrative and Coaching

Add narrative insights panel and coaching objectives panel to the report. Implement new `render_narrative` and `render_coaching` section functions. Update `ReportViewModelBuilder` to populate these sections from `Report.narrative` and `Report.coaching_snapshot`. Add corresponding `FinalReportDTO` fields (`narrative_insights`, `coaching_objectives`).

After Phase 3:
- `NarrativeInsight` and `CoachingAction` are rendered in the report UI for the first time.

### Phase 4 — Explainability Anchors (EPIC-V13-06 integration)

Wire `NarrativeInsight.source_feature_id` to evidence anchor display. Implement the UI affordance (inline anchor reference, expandable panel, or tooltip — design decision deferred to UX phase). Validate that every `NarrativeInsight` with `is_traceable=True` has a resolvable `source_feature_id`. Fail gracefully for untraceable insights: render insight prose but suppress anchor affordance.

### Phase 5 — Progress Trend Panel (EPIC-V13-02 integration)

Wire `LongitudinalProfile` (post-EPIC-V13-02) to the progress trend panel. Compute `LearningProgress` via `ProgressTracker`. Render trend panel when `LongitudinalProfile.session_count >= 3`. Render "insufficient data" state for fewer sessions.

### Phase 6 — Replay Entry Point (EPIC-V13-03 integration)

Add replay link/button to report header or metadata section. Link resolves to `ReplaySession` via session id. No re-submission controls.

### Phase 7 — Export Path Validation

Validate that PDF and JSON exports produce output identical in structure and content to pre-migration exports. Add export regression tests asserting no `InterviewEvaluation` field appears in export output.

### Phase 8 — Final Audit

Audit every report section renderer, every DTO field, and every export path. Assert zero references to `InterviewEvaluation` in any report-related file. Run full regression suite. Confirm all new sections render correctly across representative session fixtures.

---

## Risks

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `FinalReportDTO` field count mismatch after migration — `InterviewEvaluation` has more fields than the migrated `Report` exposes | High | High | Audit every field in `FinalReportDTO` against the EPIC-V13-01 `Report` extension before Phase 1 begins; block Phase 1 on field parity confirmation |
| `QuestionAssessmentDTO` loses its data source — question results are in `InterviewState.results_by_question`, not in `Report` | High | Medium | EPIC-V13-01 must define whether question results are embedded in `Report` or derived from linked `SessionHistory`; EPIC-V13-05 blocks on this decision |
| `render_*` section renderers rely on raw `List[Dict]` shapes from `InterviewEvaluation`; migrated `Report` uses typed domain objects — shape mismatch | Medium | Medium | Preserve `List[Dict]` shape in `FinalReportDTO` by projecting typed domain objects to dicts at the DTO layer; no renderer changes beyond field name alignment |
| Regression: rendered HTML differs subtly after migration due to field name or ordering changes | Medium | Medium | Establish HTML snapshot baseline before Phase 1; assert zero diff for same-session input after migration |
| `ReportInsightBuilder` signal insight logic depends on `InterviewEvaluation.dimension_signals` dict format; `Report`-based equivalent may differ | Medium | Low | Rewrite `ReportInsightBuilder` to consume `CandidateProfileSnapshot.features` directly; decouple from dimension signal dict format |
| Progress trend panel misleads candidates with sparse data (< 3 sessions) | Medium | Medium | Enforce explicit "insufficient data" guard in `ProgressTracker`; never extrapolate from single-session data |

### Migration Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| EPIC-V13-01 is not complete when EPIC-V13-05 implementation begins | High | Blocking | Do not begin Phase 1 until EPIC-V13-01 acceptance criteria are verified; `Report` must carry all scoring fields |
| Dual-path period introduced if `from_components` is kept alongside `from_report` | Low | High | Prohibit parallel factory existence; `from_components` is deleted in the same increment that `from_report` is activated |
| Export formats (PDF/JSON) produce structurally different output after migration, breaking downstream consumers | Low | Medium | Maintain `FinalReportDTO` field names wherever possible; structural changes require explicit versioning |
| Test suite covers `InterviewEvaluation`-based paths exclusively; `Report`-based paths are undertested before migration | High | Medium | Write `Report`-based `FinalReportDTO` tests in Phase 1 before deleting `InterviewEvaluation`-based tests |

### Compatibility Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `SessionHistory.evaluation_result: Optional[InterviewEvaluation]` persists in stored histories after `InterviewEvaluation` is deleted from production | Medium | Low | After EPIC-V13-01 deletes `InterviewEvaluation`, stored `SessionHistory` records carry a now-orphaned field; define migration policy for stored records in EPIC-V13-01 ADR |
| `LearningProgress.session_entries` shape is incompatible with `LongitudinalProfile` once EPIC-V13-02 introduces the latter | Low | Medium | Confirm `LearningProgressBuilder.with_session_histories()` is forward-compatible with `LongitudinalProfile` before Phase 5 |
| Explainability anchor rendering fails silently if `NarrativeInsight.source_feature_id` references a deleted or unmapped `FeatureIdentity` | Medium | Low | Fail gracefully: render prose, suppress anchor affordance, log warning; never fail the report render on missing anchor |

---

## Success Criteria

The epic is complete when all of the following are true simultaneously:

1. **Single source.** `FinalReportDTO` is constructed exclusively from `Report`. Zero references to `InterviewEvaluation` exist in any report rendering, export, or routing path.

2. **Full field parity.** Every field currently rendered by the report UI is available in `Report` (post-EPIC-V13-01). No section is blank or degraded after migration.

3. **New sections rendered.** Narrative insights panel and coaching objectives panel render correctly from `Report.narrative` and `Report.coaching_snapshot` for every test session fixture.

4. **Explainability anchors present.** Every `NarrativeInsight` with `is_traceable=True` surfaces its `source_feature_id` anchor in the report UI. No traceable insight is rendered without its anchor.

5. **Progress trend panel wired.** When `LongitudinalProfile.session_count >= 3`, the trend panel renders. When `session_count < 3`, the "insufficient data" state renders. No extrapolation from sparse data.

6. **Replay entry point present.** Report includes a replay link/button that resolves to the correct `ReplaySession` for the session.

7. **Export regression clean.** PDF and JSON exports produce structurally equivalent output to pre-migration exports. No structural field is removed without an explicit versioning decision.

8. **Rendering regression clean.** HTML snapshot baseline matches post-migration output for all representative session fixtures.

9. **No parallel factory.** `FinalReportDTO.from_components` does not exist in the codebase. `from_report` is the sole factory.

10. **Test coverage.** All new sections have unit tests. `FinalReportDTO.from_report` has full field-coverage tests. Export path tests assert zero `InterviewEvaluation` dependency.

11. **Architecture audit passes.** Zero references to `InterviewEvaluation` in any file under `app/ui/`, `app/graph/`, or `services/` report-related paths.

---

## Out of Scope

The following are explicitly excluded from EPIC-V13-05:

- **Scoring logic changes.** Dimension weights, calibration constants, and scoring algorithms are not modified. EPIC-V13-05 is a presentation migration, not a scoring redesign.
- **`InterviewEvaluation` deletion.** The deletion of `InterviewEvaluation` from the domain and the scoring pipeline migration are owned by EPIC-V13-01.
- **`ReportBuilder` extension.** Adding scoring fields to `Report` and `ReportBuilder` is owned by EPIC-V13-01.
- **`LongitudinalProfile` implementation.** The cross-session accumulation contract and its persistence are owned by EPIC-V13-02.
- **`replay_node` implementation.** The replay engine is owned by EPIC-V13-03.
- **Explainability evidence panel design.** The UI affordance design (tooltip, expandable panel, inline anchor) is deferred to the UX design phase within EPIC-V13-06.
- **PDF export infrastructure.** Export rendering format is preserved; new export distribution channels (email, sharing) are V2.
- **Accessibility hardening.** WCAG 2.1 AA compliance for the report is owned by EPIC-V13-07 (Production UX).
- **Performance optimisation of report rendering.** SLO verification for report generation time is owned by EPIC-V13-09.
- **`GoalTrack`.** Not a V1.3 commitment; excluded from all report sections.
- **Peer benchmarking panel.** `PeerBenchmark` is V2.
- **Dark mode.** V2 UX concern.
- **Internationalisation.** V2.

---

## Appendix A — Affected File Inventory

### Domain Contracts

| File | Change |
|------|--------|
| `domain/contracts/report/report.py` | Extended (EPIC-V13-01 owned) |
| `domain/contracts/report/report_builder.py` | Extended (EPIC-V13-01 owned) |
| `domain/contracts/report/report_summary.py` | Review: ensure `from_report` is compatible post-extension |
| `domain/contracts/report/report_statistics.py` | Review: ensure `from_report` is compatible post-extension |
| `domain/contracts/interview/interview_evaluation.py` | **Deleted** (EPIC-V13-01 owned) |
| `domain/contracts/progress/learning_progress.py` | Wired to UI (EPIC-V13-05 Phase 5) |
| `domain/contracts/narrative/narrative_insight.py` | Promoted to UI-rendered |
| `domain/contracts/coaching/coaching_action.py` | Promoted to UI-rendered |

### Application Layer — DTOs

| File | Change |
|------|--------|
| `app/ui/dto/final_report_dto.py` | **Rebuilt.** `from_report(report: Report)` replaces `from_components`. All field mappings updated. |

### Application Layer — UI

| File | Change |
|------|--------|
| `app/ui/builders/ui_response_builder.py` | `_build_report` reads `state.report` |
| `app/ui/mappers/interview_state_mapper.py` | `to_final_report_dto` calls `from_report` |
| `app/ui/state_handlers/export_handlers.py` | Updated to use `from_report` path |
| `app/ui/views/report.py` | No structural change (consumes `FinalReportDTO`) |
| `app/ui/views/report/report_view_model_builder.py` | Updated for new/renamed fields; narrative and coaching VM sections added |
| `app/ui/views/report/report_renderer.py` | Updated for new sections |
| `app/ui/views/report/sections/overall_section.py` | Field source updated |
| `app/ui/views/report/sections/executive_section.py` | Field source updated |
| `app/ui/views/report/sections/went_well_section.py` | Field source updated |
| `app/ui/views/report/sections/held_you_back_section.py` | Field source updated |
| `app/ui/views/report/sections/knowledge_gap_section.py` | Field source updated |
| `app/ui/views/report/sections/next_strategy_section.py` | Field source updated |
| `app/ui/views/report/sections/performance_section.py` | Field source updated |
| `app/ui/views/report/sections/dimension_section.py` | Field source updated |
| `app/ui/views/report/sections/question_section.py` | Field source review (question data path) |
| `app/ui/views/report/sections/market_section.py` | Field source updated |
| `app/ui/views/report/sections/decision_section.py` | Field source updated |
| `app/ui/views/report/sections/signal_section.py` | Field source updated |
| `app/ui/views/report/sections/roadmap_section.py` | Field source updated |
| (new) `sections/narrative_section.py` | **New** — renders `NarrativeInsight` list |
| (new) `sections/coaching_section.py` | **New** — renders `CoachingAction` tree |

### Services

| File | Change |
|------|--------|
| `services/report_insight_builder.py` | Rewritten to consume `Report.narrative` / `CandidateProfileSnapshot.features` |
| `services/report_export_service.py` | Updated to consume `FinalReportDTO` from `Report` |
| `services/interview_evaluation_service.py` | **Deleted** (EPIC-V13-01 owned) |
| (new) `services/progress_tracker.py` | **New** — derives `LearningProgress` from `LongitudinalProfile` |

### Graph Nodes

| File | Change |
|------|--------|
| `app/graph/nodes/evaluation_aggregate_node.py` | Updated (EPIC-V13-01 owned) |
| `app/graph/nodes/report_node.py` | Extended (EPIC-V13-01 owned) |

### State

| Field | Change |
|-------|--------|
| `InterviewState.interview_evaluation` | **Deleted** (EPIC-V13-01 owned) |
| `InterviewState.report` | Promoted to primary presentation source |

---

## Appendix B — Dependency Graph

```
EPIC-V13-01 (Scoring Pipeline Migration)
  └── Report carries all scoring fields
  └── InterviewEvaluation deleted
  └── FinalReportDTO.from_components broken → triggers EPIC-V13-05 Phase 1

EPIC-V13-02 (Cross-Session Profile Continuity)
  └── LongitudinalProfile persisted
  └── LearningProgress computable → triggers EPIC-V13-05 Phase 5

EPIC-V13-03 (Replay Engine)
  └── ReplaySession produced
  └── Replay link available → triggers EPIC-V13-05 Phase 6

EPIC-V13-06 (Explainability)
  └── NarrativeInsight.source_feature_id validated
  └── Evidence anchor contracts stable → triggers EPIC-V13-05 Phase 4

EPIC-V13-05 (Unified Report)
  └── Phases 1–3: FinalReportDTO rebuilt; all sections migrated; narrative/coaching added
  └── Phase 4: Explainability anchors (needs EPIC-V13-06)
  └── Phase 5: Progress trend panel (needs EPIC-V13-02)
  └── Phase 6: Replay entry point (needs EPIC-V13-03)
  └── Phases 7–8: Export validation; final audit
```

---

*This document is the authoritative planning specification for EPIC-V13-05. No production code may be modified based on this document. Implementation begins after Phase 0 prerequisite confirmation.*
