# EPIC-05 — Unified Report: Architecture Discovery

**Status:** ARCHITECTURE DISCOVERY COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-05  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Architecture Discovery (Playbook §8.1)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-05; Product Goal P-05  
**Precondition:** EPIC-V13-01/02/03/04 CLOSED; ADR-033 Accepted; Initialization Report completed.  
**Authority:** Findings only. No architecture decisions. No Domain Contracts. No Data Model. No ADR. No implementation plan.

---

## 1. Executive Summary

### 1.1 Business Objective

Produce a single, cohesive session report that renders all session artifacts from `Report` as the sole data source, eliminating dual reads and legacy routing. The Unified Report is the primary deliverable of every completed session.

### 1.2 Architectural Objective

Consolidate all report presentation onto `FinalReportDTO.from_report(Report)`. Wire progress trend from `LongitudinalProfile` / `LearningProgress`, surface a replay entry point, and ensure no report section reads `SessionHistory` when the data is available on `Report`. Projection remains LLM-free; sole-writer rules remain intact.

### 1.3 Scope (Master Plan)

- Audit and consolidate all report rendering paths
- Ensure `FinalReportDTO` is the sole consumer API for report data
- Add replay entry point in the report (link to `ReplaySession`)
- Add progress trend panel sourced from `LongitudinalProfile`
- Add explainability anchors (§ EPIC-V13-06) to coaching sections — dependency classification in §7
- Validate that no report section reads from `SessionHistory` directly when data is available in `Report`

### 1.4 Non-Goals

- PDF export / email delivery / sharing (V2)
- Scoring logic changes
- Explainability UI affordance design (owned by EPIC-V13-06 per Master Plan non-goals of EPIC-05 planning docs and EPIC-01 Architecture Freeze NOTE)
- Accessibility hardening (EPIC-V13-07)
- Performance SLO verification (EPIC-V13-09)

### 1.5 Dependencies

| Dependency | Status | Description |
|---|---|---|
| EPIC-V13-01 | CLOSED | `Report` v2.0 sole scoring artifact; presentation migration foundation |
| EPIC-V13-02 | CLOSED | `LongitudinalProfile` + `LearningProgress` for progress trend |
| EPIC-V13-03 | CLOSED | `ReplaySession` / replay runtime for replay entry |
| EPIC-V13-04 | CLOSED | Replay UI live (validates replay entry target) |
| EPIC-V13-06 | NOT STARTED | Explainability anchors — see §7 Dependency Analysis |
| ADR-033 | Accepted | Unified Report Architecture (Decisions 1–6) |
| ADR-034 | Accepted | Longitudinal / `LearningProgress` ownership |
| ADR-037 | Accepted | Replay Engine Architecture |

### 1.6 Implementation Risks (discovery assessment)

| Risk | Severity | Current Assessment |
|---|---|---|
| Residual dual-read / incomplete sole-source consolidation | HIGH | Partially mitigated — see §2; AA-01/AA-02 |
| EPIC-05 ↔ EPIC-06 circular Master Plan dependency | HIGH (process) | Documented in §7; not resolved here |
| Progress trend panel missing entirely | MEDIUM | Confirmed missing — AA-04 |
| Study recommendations empty on DTO path | MEDIUM | Confirmed — F-W-03 |
| Explainability fields dropped at DTO boundary | MEDIUM | Confirmed — AA-06/AA-07 |
| New ADR temptation for presentation gaps already covered by ADR-033 | LOW | AA-03 |

---

## 2. Current Architecture

### 2.1 Report Pipeline

**Graph order:** `session_close` → `report` → `longitudinal_update` → `END`  
**File:** `app/graph/interview_graph.py`

| Artifact | Sole writer | Assembly |
|---|---|---|
| `InterviewState.session_history` | `session_close_node` / `SessionHistoryBuilder` | Closed session artifact |
| `InterviewState.report` | `report_node` | `ReportBuilder().with_session_history(state.session_history).build()` |
| `Report` object | `ReportBuilder.build()` only | Projection assembly; no FeatureEngine / KnowledgePipeline / LLM |

**`report_node` (`app/graph/nodes/report_node.py`):**
- Guard: if `state.session_history is None` → clear flags, no report
- Non-fatal on failure
- Declared zero LLM / feature / knowledge pipeline invocation

**`ReportBuilder.with_session_history` reads from `SessionHistory`:**
- `knowledge_snapshot` → `profile_snapshot`, `narrative`, `coaching_snapshot`
- `scoring_snapshot`, `scoring_narrative`
- `question_results` → `question_assessments`
- `interview_metadata`, `context_profile`, `generation_metadata`, `knowledge_epoch`

**`Report` fields (domain, `schema_version` default `"2.0"`):**  
`report_id`, `session_id`, `candidate_identity_id`, `interview_index`, `profile_snapshot`, `narrative`, `coaching_snapshot`, `question_assessments`, `scoring`, `scoring_narrative`, `context_profile`, `generation_metadata`, `role`, `seniority`, `interview_type`, `question_count`, `knowledge_epoch`, `created_at`, `metadata`

### 2.2 FinalReportDTO

**File:** `app/ui/dto/final_report_dto.py`

| Fact | Evidence |
|---|---|
| Sole factory | `FinalReportDTO.from_report(report: Report)` |
| Dual factory eliminated | `from_components` absent; asserted in `tests/ui/mappers/test_final_report_dto.py` |
| No InterviewState / SessionHistory reads in factory | Documented in `from_report` docstring; code path confirmed |

**Mapped from `Report`:**
- Scoring fields ← `report.scoring`
- Prose / coaching dicts ← `report.scoring_narrative`
- Question assessments ← `report.question_assessments` via `QuestionAssessmentMapper`
- Dimension scores ← `DimensionScoreMapper`
- Role / seniority / context_profile / token metadata
- Phase 10: `narrative_insights`, `coaching_objectives`

**Not on FinalReportDTO:**
- Progress / `LearningProgress` / trend fields
- Replay link / `session_id` for UI replay entry
- Study recommendations
- Explainability fields (`source_feature_id`, `is_traceable`, observation origins)

**Nested DTO field drops:**

| Domain | Mapped to DTO | Dropped at DTO |
|---|---|---|
| `NarrativeInsight` | `insight_type`, `prose`, `confidence` | `source_feature_id`, `is_traceable` |
| `LearningObjective` | `objective_id`, `description`, `priority`, `confidence`, `feature_type` | `supporting_observation_types`, `detected_at_question_index` |

### 2.3 Report Rendering Flow

```
InterviewState.report
  → FinalReportDTO.from_report
  → build_report_markdown (ReportViewFacade)
  → ReportViewModelBuilder.build
  → ReportRenderer.render
  → section renderers → HTML string
  → UIResponse.report_output
```

| Layer | Path |
|---|---|
| Builder entry | `app/ui/builders/ui_response_builder.py` `_build_report` |
| Export mapper | `app/ui/mappers/interview_state_mapper.py` `to_final_report_dto` |
| Facade | `app/ui/views/report_view.py` |
| View model | `app/ui/views/report/report_view_model_builder.py` |
| Renderer | `app/ui/views/report/report_renderer.py` |
| Gradio chrome | `app/ui/layout/sections/report_section.py` |
| Export | `app/ui/state_handlers/export_handlers.py` + `services/report_export_service.py` |
| Insight helpers | `services/report_insight_builder.py` |

**Sections currently composed by `ReportRenderer`:**  
overall, executive, went_well, held_you_back, knowledge_gaps, next_strategy, performance, dimensions, questions, market, decision, signals, narrative, coaching_objectives, study_recommendations

**Missing section file:** progress trend panel — does not exist.

### 2.4 LongitudinalProfile / LearningProgress Integration

| Piece | Status in report path |
|---|---|
| `LongitudinalProfile` domain + persistence | Exists (EPIC-02); updated by `longitudinal_update_node` **after** `report_node` |
| `LearningProgress` + `LearningProgressBuilder` | Exist under `domain/contracts/progress/` |
| `services/progress/progress_tracker.py` | Exists; derives `LearningProgress` from repository |
| Report DTO / VM / renderer imports | **None** — zero wiring |
| Progress trend section | **Missing** |

### 2.5 Replay Integration

| Piece | Status |
|---|---|
| Gradio "Replay Session" button | Present in `report_section.py` (outside HTML body) |
| `ReplayEntryPoint` + `ReplayLayoutCoordinator` | Present; bound via `ui_event_orchestrator._bind_replay` |
| Replay link inside HTML report body | **Missing** |
| `session_id` on `FinalReportDTO` | **Missing** |
| Session id resolution | `resolve_session_id_from_report` prefers `state.session_history.session_id`, else `state.interview_id` |

**Note:** `Report.session_id` exists on the domain artifact but is not used by the report→replay resolver.

### 2.6 Narrative / Coaching Integration

| Surface | Status |
|---|---|
| Narrative insights panel | Present (`narrative_section.py`) — type / prose / confidence only |
| Coaching objectives panel | Present (`coaching_section.py`) — priority / feature_type / confidence / description |
| Study recommendations panel | Present in renderer; **DTO path yields empty list** (not on `FinalReportDTO`; VM fallback requires domain `coaching_snapshot`) |
| Coaching actions | Domain exists; **not rendered** |
| `Narrative` five mandatory sections (overview/strengths/weaknesses/growth/recommendations) | **Not rendered** as HTML sections (insights list only) |
| Explainability anchors | **Not surfaced** |

### 2.7 Remaining Legacy Presentation Paths

| Concern | Finding |
|---|---|
| `InterviewEvaluation` in `app/ui` report/export paths | **Absent** |
| `FinalReportDTO.from_components` | **Deleted** on DTO class |
| Stale script caller | `scripts/audit_report_quality.py` still references `from_components` |
| `QuestionMapper` (live-state question path) | File exists; **not** used by `FinalReportDTO` |
| SessionHistory reads in DTO / report views / export service | **None** |
| SessionHistory read at report→replay boundary | **Present** (`resolve_session_id_from_report`) |
| `InterviewState.interview_evaluation` field | **Absent** |

---

## 3. Target Architecture

*Descriptive of Master Plan intent only. No decisions frozen here.*

### 3.1 Sole Source

- One report. One data source: `Report`.
- `FinalReportDTO` is the sole consumer API for report presentation and export.
- Every report section is traceable to `Report` fields (or to explicitly approved adjacent projections for cross-session progress / replay entry as Master Plan requires).

### 3.2 Required Target Surfaces (Master Plan §4 EPIC-V13-05)

| Surface | Target source |
|---|---|
| Scoring / hire / dimensions / questions / scoring narrative | `Report.scoring`, `Report.scoring_narrative`, `Report.question_assessments` |
| Narrative insights | `Report.narrative` |
| Coaching / study | `Report.coaching_snapshot` |
| Progress trend panel | `LongitudinalProfile` → `LearningProgress` (post EPIC-02) |
| Replay entry point | Link / control resolving to `ReplaySession` (post EPIC-03/04) |
| Explainability anchors | Coaching / narrative evidence surfaces (§ EPIC-06) — classification in §7 |
| Dual-read elimination | No `SessionHistory` reads in report sections when field available on `Report` |

### 3.3 Constitutional Constraints (operative, not new decisions)

- P-01: Projection never computes; report render path remains LLM-free
- P-02: Single ownership; no parallel presentation factories
- ADR-033 Decision 6 pipeline remains the declared target architecture for Unified Report composition

---

## 4. Affected Subsystems

| Subsystem | Impact type |
|---|---|
| Domain — `Report` / `ReportBuilder` | Consumption completeness; no expected writer change |
| Domain — `LongitudinalProfile` / `LearningProgress` | New report consumer path |
| Domain — `Narrative` / `CoachingSnapshot` | Field projection completeness to DTO/UI |
| Application — `FinalReportDTO` + mappers | Field extensions / sole-API enforcement |
| Application — Report VM / renderer / sections | New panels; gap closure |
| Application — Gradio report chrome | Replay entry / progress placement |
| Application — Export handlers / `ReportExportService` | Remain on `from_report`; parity with HTML |
| Application — Replay entry from report | Session-id source alignment with sole-source rule |
| Graph — `report_node` / `longitudinal_update_node` | Ordering constraint for progress data availability (discovery finding only) |
| Scripts / tooling | Stale `from_components` caller |
| Tests | Presentation / dual-read / panel coverage |

---

## 5. Component Inventory

### C-01 — UIResponseBuilder._build_report

| Field | Value |
|---|---|
| **Name** | `UIResponseBuilder._build_report` |
| **Responsibility** | Build report HTML into `UIResponse.report_output` from `state.report` |
| **Owner** | EPIC-05 (existing; consolidation owner) |
| **Inputs** | `InterviewState.report` |
| **Outputs** | `UIResponse.report_output` (HTML string) |
| **Dependencies** | `FinalReportDTO`, `build_report_markdown` |
| **Read/Write** | Read-only on domain; writes UI response field |
| **Report fields consumed** | Entire `Report` via `from_report` |

---

### C-02 — FinalReportDTO

| Field | Value |
|---|---|
| **Name** | `FinalReportDTO` |
| **Responsibility** | Sole presentation DTO factory and field set for report/export |
| **Owner** | EPIC-05 |
| **Inputs** | `Report` |
| **Outputs** | Immutable presentation DTO |
| **Dependencies** | `Report`, scoring/question mappers, hire decision mapper |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring`, `scoring_narrative`, `question_assessments`, `narrative.insights`, `coaching_snapshot.collection.objectives`, role/seniority/context/generation metadata |

---

### C-03 — InterviewStateMapper.to_final_report_dto

| Field | Value |
|---|---|
| **Name** | `InterviewStateMapper.to_final_report_dto` |
| **Responsibility** | Export path: state → `FinalReportDTO` |
| **Owner** | EPIC-05 |
| **Inputs** | `InterviewState.report` |
| **Outputs** | `FinalReportDTO` |
| **Dependencies** | `FinalReportDTO.from_report` |
| **Read/Write** | Read-only |
| **Report fields consumed** | Same as C-02 |

---

### C-04 — ReportViewFacade / build_report_markdown

| Field | Value |
|---|---|
| **Name** | `ReportViewFacade` |
| **Responsibility** | Entry to VM + renderer pipeline |
| **Owner** | EPIC-05 |
| **Inputs** | `FinalReportDTO` (runtime path) |
| **Outputs** | HTML markdown/string |
| **Dependencies** | `ReportViewModelBuilder`, `ReportRenderer` |
| **Read/Write** | Read-only |
| **Report fields consumed** | Via DTO / VM |

---

### C-05 — ReportViewModelBuilder

| Field | Value |
|---|---|
| **Name** | `ReportViewModelBuilder` |
| **Responsibility** | Build view-model dict for all section renderers |
| **Owner** | EPIC-05 |
| **Inputs** | `FinalReportDTO` or domain `Report` (getattr dual-shape support) |
| **Outputs** | View-model dict |
| **Dependencies** | `ReportInsightBuilder`, `DimensionRanking` |
| **Read/Write** | Read-only |
| **Report fields consumed** | Dimension scores/signals, percentile, improvement suggestions, narrative insights, coaching objectives, study recommendations (fallback to `coaching_snapshot`) |

---

### C-06 — ReportRenderer

| Field | Value |
|---|---|
| **Name** | `ReportRenderer` |
| **Responsibility** | Compose all HTML sections in fixed order |
| **Owner** | EPIC-05 |
| **Inputs** | View-model dict |
| **Outputs** | Full report HTML |
| **Dependencies** | All section renderers (C-07–C-22) |
| **Read/Write** | Read-only |
| **Report fields consumed** | Indirect via VM |

---

### C-07 — OverallSection

| Field | Value |
|---|---|
| **Name** | `overall_section` |
| **Responsibility** | Score / hire / readiness header |
| **Owner** | EPIC-05 |
| **Inputs** | VM (`overall_score`, hire decision fields) |
| **Outputs** | HTML |
| **Dependencies** | Badges components |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring.overall_score`, `scoring.hire_decision`, related scoring fields |

---

### C-08 — ExecutiveSection

| Field | Value |
|---|---|
| **Name** | `executive_section` |
| **Responsibility** | Executive summary prose |
| **Owner** | EPIC-05 |
| **Inputs** | VM executive summary |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring_narrative.executive_summary` |

---

### C-09 — WentWellSection

| Field | Value |
|---|---|
| **Name** | `went_well_section` |
| **Responsibility** | Went-well bullets |
| **Owner** | EPIC-05 |
| **Inputs** | VM went_well |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring_narrative.went_well` |

---

### C-10 — HeldYouBackSection

| Field | Value |
|---|---|
| **Name** | `held_you_back_section` |
| **Responsibility** | Held-you-back items (`context_detail`) |
| **Owner** | EPIC-05 |
| **Inputs** | VM held_you_back |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring_narrative.held_you_back` |

---

### C-11 — KnowledgeGapSection

| Field | Value |
|---|---|
| **Name** | `knowledge_gap_section` |
| **Responsibility** | Knowledge gap items (`context_detail`) |
| **Owner** | EPIC-05 |
| **Inputs** | VM knowledge_gaps |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring_narrative.knowledge_gaps` |

---

### C-12 — NextStrategySection

| Field | Value |
|---|---|
| **Name** | `next_strategy_section` |
| **Responsibility** | Next strategy items (`context_detail`) |
| **Owner** | EPIC-05 |
| **Inputs** | VM next_strategy |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring_narrative.next_strategy` |

---

### C-13 — PerformanceSection

| Field | Value |
|---|---|
| **Name** | `performance_section` |
| **Responsibility** | Radar chart + strongest/weakest |
| **Owner** | EPIC-05 |
| **Inputs** | VM dims / strongest / weakest |
| **Outputs** | HTML |
| **Dependencies** | Radar chart component |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring` dimension scores |

---

### C-14 — DimensionSection

| Field | Value |
|---|---|
| **Name** | `dimension_section` |
| **Responsibility** | Dimension table / insights |
| **Owner** | EPIC-05 |
| **Inputs** | VM dimension insights |
| **Outputs** | HTML |
| **Dependencies** | Tables component |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring` dimensions / weighted breakdown |

---

### C-15 — QuestionSection

| Field | Value |
|---|---|
| **Name** | `question_section` |
| **Responsibility** | Per-question assessments |
| **Owner** | EPIC-05 |
| **Inputs** | VM question assessments |
| **Outputs** | HTML |
| **Dependencies** | Bars components |
| **Read/Write** | Read-only |
| **Report fields consumed** | `question_assessments` |

---

### C-16 — MarketSection

| Field | Value |
|---|---|
| **Name** | `market_section` |
| **Responsibility** | Percentile / market narrative |
| **Owner** | EPIC-05 |
| **Inputs** | VM percentile fields |
| **Outputs** | HTML |
| **Dependencies** | Distribution chart |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring.percentile_rank`, related scoring fields |

---

### C-17 — DecisionSection

| Field | Value |
|---|---|
| **Name** | `decision_section` |
| **Responsibility** | Drivers / blockers / decision explanation |
| **Owner** | EPIC-05 |
| **Inputs** | VM decision fields |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring.decision_explanation`, gating fields |

---

### C-18 — SignalSection

| Field | Value |
|---|---|
| **Name** | `signal_section` |
| **Responsibility** | Behavioral signal insights |
| **Owner** | EPIC-05 |
| **Inputs** | VM signal insights |
| **Outputs** | HTML |
| **Dependencies** | `ReportInsightBuilder` |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring.dimension_signals` |

---

### C-19 — RoadmapSection

| Field | Value |
|---|---|
| **Name** | `roadmap_section` |
| **Responsibility** | Improvement roadmap |
| **Owner** | EPIC-05 |
| **Inputs** | VM roadmap / improvement suggestions |
| **Outputs** | HTML |
| **Dependencies** | `ReportInsightBuilder` |
| **Read/Write** | Read-only |
| **Report fields consumed** | `scoring_narrative.improvement_suggestions`, dimension-derived roadmap |

---

### C-20 — NarrativeSection

| Field | Value |
|---|---|
| **Name** | `narrative_section` |
| **Responsibility** | Narrative insights panel |
| **Owner** | EPIC-05 |
| **Inputs** | VM `narrative_insights` |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | `narrative.insights` (partial — explainability fields not consumed) |

---

### C-21 — CoachingObjectivesSection

| Field | Value |
|---|---|
| **Name** | `coaching_section` |
| **Responsibility** | Coaching objectives panel |
| **Owner** | EPIC-05 |
| **Inputs** | VM `coaching_objectives` |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | `coaching_snapshot.collection.objectives` (partial) |

---

### C-22 — StudyRecommendationsSection

| Field | Value |
|---|---|
| **Name** | `study_recommendations_section` |
| **Responsibility** | Study recommendations panel |
| **Owner** | EPIC-05 |
| **Inputs** | VM `study_recommendations` |
| **Outputs** | HTML |
| **Dependencies** | None |
| **Read/Write** | Read-only |
| **Report fields consumed** | Intended: `coaching_snapshot.collection.recommendations` — **not on FinalReportDTO path today** |

---

### C-23 — ProgressTrendPanel (target — not implemented)

| Field | Value |
|---|---|
| **Name** | `ProgressTrendPanel` (candidate) |
| **Responsibility** | Render progress trend from `LearningProgress`; insufficient-data state for &lt; 3 sessions |
| **Owner** | EPIC-05 |
| **Inputs** | `LearningProgress` (derived from `LongitudinalProfile`) |
| **Outputs** | HTML / Gradio fragment |
| **Dependencies** | `ProgressTracker` / `LearningProgressBuilder`, Longitudinal repository |
| **Read/Write** | Read-only |
| **Report fields consumed** | None directly — Master Plan sources panel from `LongitudinalProfile` |

---

### C-24 — ReportSection (Gradio chrome)

| Field | Value |
|---|---|
| **Name** | `report_section` (layout) |
| **Responsibility** | Gradio report container: HTML output, PDF/JSON export, Replay Session button, New Interview |
| **Owner** | EPIC-05 (chrome); EPIC-04 (replay target) |
| **Inputs** | `UIResponse.report_output`; interview state for replay entry |
| **Outputs** | Gradio UI updates |
| **Dependencies** | Export handlers, `ReplayLayoutCoordinator` |
| **Read/Write** | Read-only on domain |
| **Report fields consumed** | Indirect (`report_output`); replay path currently bypasses `Report.session_id` |

---

### C-25 — ReplayEntryFromReport

| Field | Value |
|---|---|
| **Name** | `ReplayEntryPoint` + `resolve_session_id_from_report` |
| **Responsibility** | Enter replay from completed report view |
| **Owner** | EPIC-05 (entry alignment); EPIC-04 (replay UI) |
| **Inputs** | `session_id` (today from `session_history` / `interview_id`) |
| **Outputs** | Replay layout snapshot |
| **Dependencies** | `ReplaySession`, session loader |
| **Read/Write** | Read-only |
| **Report fields consumed** | **None today** — should consume `Report.session_id` under sole-source rule |

---

### C-26 — ExportHandlers / ReportExportService

| Field | Value |
|---|---|
| **Name** | Export handlers + `ReportExportService` |
| **Responsibility** | PDF/JSON export from `FinalReportDTO` |
| **Owner** | EPIC-05 |
| **Inputs** | `InterviewState.report` via mapper |
| **Outputs** | PDF bytes / JSON |
| **Dependencies** | `FinalReportDTO`, `build_report_markdown` |
| **Read/Write** | Read-only |
| **Report fields consumed** | Same as C-02 |

---

### C-27 — ReportInsightBuilder

| Field | Value |
|---|---|
| **Name** | `ReportInsightBuilder` |
| **Responsibility** | Derive presentation insight strings (percentile narrative, dimension insights, signals, roadmap) |
| **Owner** | EPIC-05 |
| **Inputs** | DTO dimension/percentile/signal fields |
| **Outputs** | Insight strings for VM |
| **Dependencies** | None on domain engines |
| **Read/Write** | Read-only |
| **Report fields consumed** | Via DTO scoring fields |

---

## 6. Architecture Assumptions Register

Assumptions initialized from EPIC-V13-05 Initialization Report. Status updated where Architecture Discovery provides evidence.

---

### AA-01 — Remaining Scope Is Additive Presentation

| Field | Value |
|---|---|
| **ID** | AA-01 |
| **Description** | Remaining EPIC-05 scope is additive presentation (progress trend, replay entry alignment, dual-read audit, section completeness); core `from_report` sole-factory path already exists |
| **Status** | **VERIFIED** |
| **Rationale** | Inventory confirms `from_report` sole factory, scoring/narrative/question/narrative/coaching objective panels present. Gaps are progress trend (missing), study recommendations on DTO path (empty), explainability (missing), replay session_id sole-source alignment (partial). |
| **Verification Document** | EPIC-05-UNIFIED-REPORT.md §2 |
| **Notes** | Does not assert Master Plan full-scope completion — only that remaining work is presentation consolidation/extension |

---

### AA-02 — No Report Section Reads SessionHistory When Field Available on Report

| Field | Value |
|---|---|
| **ID** | AA-02 |
| **Description** | No production report section reads `SessionHistory` when the field is available on `Report` |
| **Status** | **CONDITIONALLY VERIFIED** |
| **Rationale** | DTO / report views / export service have zero `SessionHistory` reads. Report→replay resolver still prefers `state.session_history.session_id` even though `Report.session_id` exists. Section renderers themselves comply; boundary path does not. |
| **Verification Document** | EPIC-05-UNIFIED-REPORT.md §2.5, §2.7 |
| **Notes** | Full VERIFIED requires Domain Contracts to specify replay entry session_id source |

---

### AA-03 — ADR-033 Sufficient; No New ADR Required

| Field | Value |
|---|---|
| **ID** | AA-03 |
| **Description** | ADR-033 Decisions 1–6 remain sufficient; no new ADR required for Unified Report |
| **Status** | **CONDITIONALLY VERIFIED** |
| **Rationale** | Discovery found no new structural ownership conflict requiring an ADR at this stage. Remaining gaps are presentation projection completeness and EPIC-06 dependency classification. Final confirmation belongs to Architecture Review / ADR (conditional) after Domain Contracts + Data Model. |
| **Verification Document** | Architecture Review / ADR step (conditional); Architecture Freeze |
| **Notes** | Do not author ADR proactively |

---

### AA-04 — LongitudinalProfile + LearningProgressBuilder Suffice for Progress Trend

| Field | Value |
|---|---|
| **ID** | AA-04 |
| **Description** | `LongitudinalProfile` + `LearningProgressBuilder` suffice for progress trend without new persistent artifacts |
| **Status** | **CONDITIONALLY VERIFIED** |
| **Rationale** | EPIC-02 closed with frozen `LearningProgress` derived from `LongitudinalProfile` (ADR-034 Decision 5). Domain + `ProgressTracker` exist. Report path has zero wiring — sufficiency of *fields for UI* still needs Domain Contracts mapping, but no new persistent artifact is indicated by Discovery. |
| **Verification Document** | Domain Contracts / Data Model |
| **Notes** | Graph ordering: longitudinal update runs after report_node — progress panel may require post-session read of persisted profile, not `InterviewState` at report build time |

---

### AA-05 — Replay Entry Via Existing ReplayEntryPoint Without New ADR

| Field | Value |
|---|---|
| **ID** | AA-05 |
| **Description** | Replay entry resolves via existing `ReplayEntryPoint` / `ReplaySession` without new ADR |
| **Status** | **VERIFIED** (architecturally) |
| **Rationale** | Gradio button + `ReplayEntryPoint` + EPIC-04 Replay UI already operational. Gap is sole-source session_id alignment and optional in-HTML entry affordance — not a new replay architecture. |
| **Verification Document** | EPIC-05-UNIFIED-REPORT.md §2.5; ADR-037 |
| **Notes** | Presentation placement (HTML vs Gradio chrome) is a Domain Contracts concern, not an ADR trigger by itself |

---

### AA-06 — Explainability Deferred to EPIC-06; Not Blocking Core EPIC-05 Freeze

| Field | Value |
|---|---|
| **ID** | AA-06 |
| **Description** | Explainability UI is deferred to EPIC-06 and does not block EPIC-05 Architecture Freeze for core Unified Report scope |
| **Status** | **UNVERIFIED** |
| **Rationale** | Conflicting authoritative signals: Master Plan lists EPIC-06 as EPIC-05 dependency; EPIC-06 lists EPIC-05 as dependency; EPIC-01 Architecture Freeze NOTE says explainability UI affordance is deferred to EPIC-06 and not blocking V13-05. Discovery records the conflict (§7) but cannot declare freeze-blocking status without a process resolution outside Discovery. |
| **Verification Document** | Domain Contracts (scope boundary) + Architecture Freeze recording |
| **Notes** | Finding F-B-01 |

---

### AA-07 — NarrativeInsightDTO / CoachingObjectiveDTO Cover Non-Explainability Sections

| Field | Value |
|---|---|
| **ID** | AA-07 |
| **Description** | Existing `NarrativeInsightDTO` / `CoachingObjectiveDTO` field sets cover non-explainability narrative/coaching sections |
| **Status** | **CONDITIONALLY VERIFIED** |
| **Rationale** | Current panels render with existing DTO fields. Study recommendations are not on DTO (gap). Explainability fields intentionally absent. Non-explainability narrative/coaching *panels that exist* are covered; completeness vs Master Plan “all coaching sections” still needs Domain Contracts. |
| **Verification Document** | Domain Contracts |
| **Notes** | Linked to F-W-03 |

---

### AA-08 — Existing Gradio / Report Stack Sufficient

| Field | Value |
|---|---|
| **ID** | AA-08 |
| **Description** | Report UI remains within existing Gradio/report stack; no new frontend dependency |
| **Status** | **VERIFIED** |
| **Rationale** | All report and replay chrome are Gradio + HTML section renderers. Progress trend and replay entry can be expressed in the same stack (EPIC-04 precedent). No evidence of a required new UI library. |
| **Verification Document** | EPIC-05-UNIFIED-REPORT.md §5 Component Inventory |
| **Notes** | None |

---

### AA-09 — FinalReportDTO.from_report Never Reads InterviewState or SessionHistory

| Field | Value |
|---|---|
| **ID** | AA-09 |
| **Description** | `FinalReportDTO.from_report` never reads `InterviewState` or `SessionHistory` |
| **Status** | **VERIFIED** |
| **Rationale** | Factory signature accepts only `Report`; implementation reads only `Report` fields and mappers. Architectural test already asserts `from_components` absence. |
| **Verification Document** | `app/ui/dto/final_report_dto.py`; `tests/ui/mappers/test_final_report_dto.py` |
| **Notes** | Broader sole-source rule for report *chrome* still tracked by AA-02 |

---

### AA-10 — Insufficient-Data Progress State Is Presentation of LearningProgress Flags

| Field | Value |
|---|---|
| **ID** | AA-10 |
| **Description** | Insufficient-data progress state (&lt; 3 sessions) is presentation of `LearningProgress` flags; no trend extrapolation |
| **Status** | **CONDITIONALLY VERIFIED** |
| **Rationale** | EPIC-02 contracts define `LearningProgress.has_sufficient_data` / empty progress when profile absent. UI panel not implemented; presentation rule is architecturally available but not verified in a report consumer. |
| **Verification Document** | Domain Contracts / Data Model |
| **Notes** | Master Plan product risk mitigation |

---

### Assumption Status Summary

| ID | Previous | Discovery status |
|---|---|---|
| AA-01 | UNVERIFIED | **VERIFIED** |
| AA-02 | UNVERIFIED | **CONDITIONALLY VERIFIED** |
| AA-03 | UNVERIFIED | **CONDITIONALLY VERIFIED** |
| AA-04 | UNVERIFIED | **CONDITIONALLY VERIFIED** |
| AA-05 | UNVERIFIED | **VERIFIED** (architecturally) |
| AA-06 | UNVERIFIED | **UNVERIFIED** |
| AA-07 | UNVERIFIED | **CONDITIONALLY VERIFIED** |
| AA-08 | UNVERIFIED | **VERIFIED** |
| AA-09 | UNVERIFIED | **VERIFIED** |
| AA-10 | UNVERIFIED | **CONDITIONALLY VERIFIED** |

UNVERIFIED remaining: **AA-06** only (EPIC-06 dependency classification). CONDITIONALLY VERIFIED items must reach VERIFIED before Architecture Freeze (Playbook §8 Assumptions Register rules).

---

## 7. Traceability Preparation

Formal Traceability Matrix belongs to Domain Contracts. This section maps Master Plan requirements to **candidate** components / sources only.

| Master Plan Requirement | Candidate source | Candidate component(s) | Gap vs current |
|---|---|---|---|
| Sole data source `Report` | `Report` via `FinalReportDTO.from_report` | C-01, C-02, C-03, C-26 | Largely present; boundary dual-read on replay session_id |
| Consolidate report rendering paths | Existing section pipeline | C-04–C-22 | Audit/complete; study recommendations broken on DTO path |
| `FinalReportDTO` sole consumer API | `FinalReportDTO` | C-02 | Present; extend fields for gaps |
| Replay entry point in report | `Report.session_id` → `ReplayEntryPoint` | C-24, C-25 | Partial (Gradio button; SessionHistory-preferred id) |
| Progress trend panel | `LongitudinalProfile` → `LearningProgress` | C-23 | Missing |
| Explainability anchors on coaching/narrative | Domain evidence fields / EPIC-06 contracts | C-20, C-21 (+ future) | Missing; EPIC-06 dependency (§7) |
| No `SessionHistory` dual read when on `Report` | `Report` fields only | C-02, C-25 | Section path OK; replay resolver not |
| Narrative insights panel | `Report.narrative.insights` | C-20 | Present (partial fields) |
| Coaching objectives panel | `Report.coaching_snapshot` | C-21 | Present (partial fields) |
| Study recommendations | `coaching_snapshot.collection.recommendations` | C-22 | Renderer present; DTO path empty |
| Export from sole source | `from_report` | C-03, C-26 | Present |
| Insufficient-data progress state | `LearningProgress.has_sufficient_data` | C-23 | Missing UI |

---

## 8. Dependency Analysis — EPIC-05 ↔ EPIC-06

### 8.1 Authoritative statements

| Source | Statement |
|---|---|
| Master Plan EPIC-05 Dependencies | EPIC-01, EPIC-02, EPIC-03, **EPIC-06** |
| Master Plan EPIC-06 Dependencies | **EPIC-05**, EPIC-01 |
| Master Plan Roadmap Phase 3 | EPIC-06 can begin UI design in parallel with Phase 2; EPIC-05 depends on EPIC-01/02/03/06 for full report integration |
| EPIC-01 Architecture Freeze NOTE | Explainability anchor UI affordance deferred to EPIC-06; **not blocking V13-01/V13-05** |
| EPIC-05 Non-Goals (planning) | Explainability evidence panel design deferred to EPIC-06 UX phase |

### 8.2 Classification (findings only — no resolution)

| Dependency type | Assessment |
|---|---|
| **Architectural dependency** | **Weak / deferred.** Core Unified Report pipeline (ADR-033) does not require EPIC-06 contracts to exist. Evidence fields (`source_feature_id`, etc.) already exist on domain narrative/coaching objects. |
| **Implementation dependency** | **Partial / optional integration phase.** Wiring anchors into report sections requires EPIC-06 affordance decisions *if* EPIC-05 claims Master Plan “add explainability anchors” as in-scope. |
| **Product dependency** | **Present for full Master Plan wording** of EPIC-05 Expected Outcome (“every report section…”) including explainability surfaces listed under EPIC-06 purpose. |
| **Documentation inconsistency** | **Yes.** Mutual Master Plan dependency (05↔06) contradicts EPIC-01 Freeze NOTE and creates an unsatisfiable strict DoR if both epics require the other to be CLOSED first. |

### 8.3 Discovery conclusion

This is a **documentation / sequencing inconsistency** with a **product-scope coupling**, not a missing domain architecture for Unified Report itself. Resolution is out of scope for Architecture Discovery (no architecture change here). Domain Contracts must record an explicit EPIC-05 scope boundary relative to EPIC-06 before Architecture Freeze.

---

## 9. Open Findings

### BLOCKER

#### F-B-01 — EPIC-05 ↔ EPIC-06 Circular Dependency / Scope Boundary Unresolved

- **Type:** BLOCKER (process / DoR)
- **Description:** Master Plan creates a circular CLOSED-epic dependency between EPIC-05 and EPIC-06, while EPIC-01 Architecture Freeze states explainability UI is deferred and not blocking V13-05. Architecture Discovery cannot declare full-scope Definition of Ready.
- **Impact:** Blocks Architecture Freeze for *full* Master Plan wording until scope boundary is recorded (in Domain Contracts / Freeze), even if core Unified Report work can proceed.
- **Resolution path:** Domain Contracts must classify explainability as (a) out-of-scope handoff to EPIC-06, or (b) in-scope integration requiring EPIC-06 contracts first. No architecture change in Discovery.

---

### WARNING

#### F-W-01 — Report→Replay SessionId Prefers SessionHistory

- **Type:** WARNING
- **Description:** `resolve_session_id_from_report` reads `state.session_history.session_id` first despite `Report.session_id` existing.
- **Impact:** Violates Master Plan dual-read elimination intent at the report chrome boundary.
- **Resolution path:** Domain Contracts specify sole session_id source for report→replay entry.

#### F-W-02 — Progress Trend Panel Entirely Absent

- **Type:** WARNING
- **Description:** No DTO fields, section renderer, or ProgressTracker wiring in the report path.
- **Impact:** Master Plan progress trend requirement unmet.
- **Resolution path:** Domain Contracts + Component Inventory C-23 specification.

#### F-W-03 — Study Recommendations Empty on FinalReportDTO Path

- **Type:** WARNING
- **Description:** `study_recommendations` not on `FinalReportDTO`; VM fallback requires domain `coaching_snapshot`, which the runtime HTML path does not pass.
- **Impact:** Study recommendations panel silently empty in production report rendering.
- **Resolution path:** Domain Contracts field mapping for study recommendations onto sole DTO API.

#### F-W-04 — Explainability Fields Dropped at DTO Boundary

- **Type:** WARNING
- **Description:** `source_feature_id` / `is_traceable` / observation origins not projected to DTOs or UI.
- **Impact:** Blocks EPIC-06 integration and Master Plan explainability visibility if claimed in EPIC-05 scope.
- **Resolution path:** Tied to F-B-01 scope boundary; Domain Contracts.

#### F-W-05 — Graph Ordering: Longitudinal Update After Report

- **Type:** WARNING
- **Description:** `report_node` precedes `longitudinal_update_node`. Progress panel cannot assume longitudinal data is on `InterviewState` at report HTML build time.
- **Impact:** Progress panel data-loading design must use persisted `LongitudinalProfile` read (or equivalent), not report_node outputs.
- **Resolution path:** Domain Contracts / Data Model lifecycle for progress panel inputs.

#### F-W-06 — Stale Tooling References `from_components`

- **Type:** WARNING
- **Description:** `scripts/audit_report_quality.py` still calls deleted `FinalReportDTO.from_components`.
- **Impact:** Tooling breakage / false dual-path signal; not a runtime UI path.
- **Resolution path:** Implementation cleanup once Freeze authorizes; not an ADR.

---

### INFORMATION

#### F-I-01 — Core Sole-Factory Path Already Landed

- Scoring / scoring_narrative / questions / narrative insights / coaching objectives render via `from_report`.
- `InterviewEvaluation` absent from `app/ui` report paths.

#### F-I-02 — Replay Chrome Entry Exists Outside HTML Body

- Gradio "Replay Session" button is live and routes through EPIC-04 Replay UI.
- Master Plan “replay entry point in the report” may be satisfied by chrome and/or HTML — Domain Contracts must state which.

#### F-I-03 — Coaching Actions and Narrative Five-Sections Not Rendered

- Domain artifacts exist; HTML surfaces insights list + objectives only.
- Confirm whether Master Plan requires actions / five narrative sections in EPIC-05 or treats them as non-goals.

#### F-I-04 — Prior Planning Doc Stale

- `EPIC-01-UNIFIED-REPORT.md` describes pre-EPIC-01 dual-source state. This Discovery document supersedes it for current-state inventory. No edit performed here beyond recognition.

#### F-I-05 — No New Persistent Artifact Indicated

- Discovery did not identify a need for a new frozen persistent domain artifact beyond consuming existing Report / Longitudinal / Replay contracts.

---

## 10. Confirmed Decisions (Governing — Not New)

Listed for inventory completeness. **No new decisions are made by this document.**

| Decision | Governing artifact |
|---|---|
| Unified Report target pipeline | ADR-033 Decision 6 |
| Scoring / narrative / question ownership on Report | ADR-033 Decisions 1–5 |
| `LearningProgress` from `LongitudinalProfile` | ADR-034 Decision 5 |
| `ReplaySession` as replay projection | ADR-037 |
| `report_node` sole writer of `state.report` | ADR-033 / ARC-01 |

---

## 11. Missing Decisions (Open — Not Resolved Here)

| Open item | Why open | Next document |
|---|---|---|
| EPIC-05 vs EPIC-06 scope boundary for explainability | Circular Master Plan dependency | Domain Contracts + Freeze record |
| Progress panel input lifecycle given graph order | Longitudinal after report | Domain Contracts / Data Model |
| Sole session_id source for report→replay | Dual-read at chrome boundary | Domain Contracts |
| Whether study recommendations / coaching actions / narrative five-sections are EPIC-05 required surfaces | Master Plan vs current partial UI | Domain Contracts Traceability Matrix |
| Whether replay entry must appear inside HTML body | Gradio chrome already exists | Domain Contracts / Component Inventory refinement |

---

## 12. Architecture Discovery Definition of Done (§8.1)

| Criterion | Status |
|---|---|
| Current vs target state analysis complete | YES — §2, §3 |
| All affected subsystems identified | YES — §4 |
| Confirmed decisions listed with governing ADR | YES — §10 |
| Missing decisions listed as open items | YES — §11 |
| Risks identified and classified | YES — §1.6, §9 |
| Component Inventory complete (UI-bearing) | YES — §5 |
| Architecture Assumptions Register populated | YES — §6 |
| No code produced or modified | YES |

---

## 13. Next Step

**Domain Contracts** — `docs/master-plan/epics/EPIC-05-DOMAIN-CONTRACTS.md`

Must include:
- Formal Traceability Matrix (Master Plan → domain/DTO fields → components → verification)
- EPIC-05 / EPIC-06 scope boundary recording (addresses F-B-01)
- Progress panel input contract (addresses F-W-02, F-W-05)
- Sole-source session_id / study recommendations field specs (addresses F-W-01, F-W-03)
- No ADR authoring unless a genuine unresolved architectural decision remains after Domain Contracts + Data Model

---

*This document is Architecture Discovery for EPIC-V13-05. It produces findings only. It does not freeze architecture, author ADRs, define Domain Contracts, define a Data Model, or authorize implementation.*
