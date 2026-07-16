# EPIC-05 — Unified Report: Domain Contracts

**Status:** DOMAIN CONTRACTS COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-05  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Domain Contracts (Playbook §8.2)  
**Precondition:** EPIC-05-UNIFIED-REPORT.md (Architecture Discovery) COMPLETE; Master Plan EPIC-05/06 dependency correction applied (2026-07-16)  
**Governing ADRs:** ADR-033, ADR-034, ADR-037, ADR-003, ADR-025  
**Authority:** Field-level contracts, ownership, lifecycle, Traceability Matrix. No Data Model field tables. No ADR. No Architecture Freeze. No implementation.

---

## 1. Contract Overview

### 1.1 Purpose

Specify every presentation contract for the Unified Report so that implementation is mechanical: sole ownership, sole source of truth, no dual reads, no dual writers.

### 1.2 Responsibilities (EPIC-05)

| Responsibility | In scope |
|---|---|
| Sole presentation API via `FinalReportDTO.from_report(Report)` | YES |
| Report section rendering from `FinalReportDTO` | YES |
| Study recommendations on sole DTO path | YES |
| Replay entry from report using `Report.session_id` | YES |
| Progress trend panel from `LearningProgress` (derived from `LongitudinalProfile`) | YES |
| Export (PDF/JSON) via sole DTO path | YES |
| Dual-read elimination (`SessionHistory` forbidden when field on `Report`) | YES |
| Stable narrative/coaching DTO surfaces for later EPIC-06 consumption | YES (expose only) |
| Explainability anchors / evidence UX | **NO — EPIC-V13-06** |
| Scoring / ReportBuilder / domain persistence changes | **NO** (frozen upstream) |

### 1.3 Ownership Summary

| Artifact | Sole producer / writer | Sole presentation consumer API | Lifecycle |
|---|---|---|---|
| `Report` | `report_node` via `ReportBuilder` | `FinalReportDTO.from_report` | Built once at session close; immutable |
| `FinalReportDTO` | `FinalReportDTO.from_report` (sole factory) | Report VM / renderer / export | Ephemeral presentation projection |
| `LearningProgress` | `LearningProgressBuilder` (via `ProgressTracker`) | Progress trend panel only | Derived on demand; never persisted |
| `LongitudinalProfile` | `longitudinal_update_node` | Indirect — input to `LearningProgressBuilder` only | Persisted after report_node |
| `ReplaySession` | `replay_node` | EPIC-04 Replay UI (not report HTML) | On-demand reconstruction |
| Report→Replay `session_id` | Read from `Report.session_id` only | `ReplayEntryPoint` | Trigger only; no domain write |

### 1.4 Read / Write Boundaries

| Layer | May read | May write |
|---|---|---|
| `FinalReportDTO.from_report` | `Report` only | Nothing (returns new DTO) |
| Report section renderers | `FinalReportDTO` / view-model only | Nothing |
| Progress trend panel | `LearningProgress` only | Nothing |
| Report→Replay entry | `Report.session_id` only | Nothing on domain; triggers Replay UI |
| Export path | `InterviewState.report` → `from_report` | Export bytes only |
| **Forbidden** | `SessionHistory` in report presentation / replay-from-report session_id resolution when `Report` is present | Any domain artifact from UI |

### 1.5 EPIC-06 Scope Boundary (resolves F-B-01 / AA-06)

Per Master Plan amendment 2026-07-16 and Architecture Clarification:

- Explainability implementation is **out of EPIC-05 contract scope**.
- EPIC-05 **shall** keep narrative/coaching presentation DTOs stable for EPIC-06 to extend later.
- EPIC-05 **shall not** require `source_feature_id`, `is_traceable`, or evidence-anchor fields on presentation DTOs.
- EPIC-05 **may** Architecture Freeze without explainability.

---

## 2. Presentation Contract Inventory

### PC-01 — Report (domain)

| Attribute | Value |
|---|---|
| **Owner** | Domain / `report_node` |
| **Producer** | `ReportBuilder.build()` via `report_node` |
| **Consumer (EPIC-05)** | `FinalReportDTO.from_report` only |
| **Lifecycle** | Created once per completed session; `frozen=True` |
| **Mutability** | Immutable |
| **Source of truth** | Closed session projection assembled from `SessionHistory` at report_node (assembly only — presentation must not re-read `SessionHistory`) |

### PC-02 — FinalReportDTO

| Attribute | Value |
|---|---|
| **Owner** | Application presentation layer (EPIC-05) |
| **Producer** | `FinalReportDTO.from_report(report: Report)` — **sole factory** |
| **Consumer** | `ReportViewModelBuilder`, section renderers, export service |
| **Lifecycle** | Built per report render / export request; discarded after use |
| **Mutability** | Immutable after construction |
| **Source of truth** | `Report` exclusively |

**Required presentation fields (EPIC-05):**

| DTO field group | Source on `Report` |
|---|---|
| Scoring fields | `report.scoring` |
| Scoring narrative prose | `report.scoring_narrative` |
| Question assessments | `report.question_assessments` |
| Narrative insights (non-explainability) | `report.narrative.insights` → `NarrativeInsightDTO` |
| Coaching objectives (non-explainability) | `report.coaching_snapshot.collection.objectives` → `CoachingObjectiveDTO` |
| Study recommendations | `report.coaching_snapshot.collection.recommendations` → `StudyRecommendationDTO` |
| Session identity for replay | `report.session_id` → `session_id: str` |
| Role / seniority / context / tokens | `report.role`, `seniority`, `context_profile`, `generation_metadata` |

**Forbidden on FinalReportDTO producer path:** `InterviewState`, `SessionHistory`, `InterviewEvaluation`, second factory.

### PC-03 — NarrativeInsightDTO

| Attribute | Value |
|---|---|
| **Owner** | EPIC-05 presentation |
| **Producer** | `FinalReportDTO.from_report` |
| **Consumer** | Narrative section |
| **Lifecycle** | Embedded in `FinalReportDTO` |
| **Mutability** | Immutable |
| **Source of truth** | `Report.narrative.insights` |
| **EPIC-05 fields** | `insight_type`, `prose`, `confidence` |
| **Deferred to EPIC-06** | `source_feature_id`, `is_traceable`, evidence anchors |

### PC-04 — CoachingObjectiveDTO

| Attribute | Value |
|---|---|
| **Owner** | EPIC-05 presentation |
| **Producer** | `FinalReportDTO.from_report` |
| **Consumer** | Coaching objectives section |
| **Lifecycle** | Embedded in `FinalReportDTO` |
| **Mutability** | Immutable |
| **Source of truth** | `Report.coaching_snapshot.collection.objectives` |
| **EPIC-05 fields** | `objective_id`, `description`, `priority`, `confidence`, `feature_type` |
| **Deferred to EPIC-06** | Observation origins / KnowledgeGap surfacing |

### PC-05 — StudyRecommendationDTO (required)

| Attribute | Value |
|---|---|
| **Owner** | EPIC-05 presentation |
| **Producer** | `FinalReportDTO.from_report` |
| **Consumer** | Study recommendations section |
| **Lifecycle** | Embedded in `FinalReportDTO` |
| **Mutability** | Immutable |
| **Source of truth** | `Report.coaching_snapshot.collection.recommendations` |
| **Fields** | `recommendation_id`, `objective_id`, `resource_type`, `topic`, `rationale`, `estimated_duration_hours` |

**Invariant PC-05-01:** Study recommendations **must** be mapped onto `FinalReportDTO`. View-model fallback that requires a domain `Report` / `coaching_snapshot` object is **forbidden** on the production HTML path.

### PC-06 — LearningProgress (progress presentation source)

| Attribute | Value |
|---|---|
| **Owner** | Domain progress (`LearningProgressBuilder` sole constructor) |
| **Producer** | `ProgressTracker` → `LearningProgressBuilder` from persisted `LongitudinalProfile` |
| **Consumer** | Progress trend panel only |
| **Lifecycle** | Derived on demand when report UI needs progress; never persisted |
| **Mutability** | Immutable |
| **Source of truth** | `LongitudinalProfile` (ADR-034 Decision 5) |
| **Not owned by** | `Report`, `FinalReportDTO`, `SessionHistory` |

### PC-07 — Replay entry trigger

| Attribute | Value |
|---|---|
| **Owner** | EPIC-05 report chrome (trigger); EPIC-04 (Replay UI) |
| **Producer** | User action on report view |
| **Consumer** | `ReplayEntryPoint` / `ReplayLayoutCoordinator` |
| **Lifecycle** | Ephemeral trigger |
| **Mutability** | N/A |
| **Source of truth for `session_id`** | **`Report.session_id` only** when `InterviewState.report is not None` |
| **Forbidden** | `SessionHistory.session_id`, `interview_id` fallback when `Report` is present |

### PC-08 — UIResponse.report_output

| Attribute | Value |
|---|---|
| **Owner** | `UIResponseBuilder` |
| **Producer** | `_build_report` via `build_report_markdown(FinalReportDTO)` |
| **Consumer** | Gradio report HTML component |
| **Lifecycle** | Per UI response |
| **Mutability** | String payload |
| **Source of truth** | Rendered from `FinalReportDTO` only |

---

## 3. Field Ownership

Every field rendered by Unified Report has exactly one ownership class.

### 3.1 Report-owned (session report body)

All of the following are **Report-owned**. Presentation reads them only via `FinalReportDTO` mapped from `Report`.

| Rendered surface | Authoritative `Report` path |
|---|---|
| Overall score / hire / readiness | `scoring.*` |
| Executive summary | `scoring_narrative.executive_summary` |
| Went well / held you back / knowledge gaps / next strategy | `scoring_narrative.*` |
| Improvement suggestions / roadmap inputs | `scoring_narrative.improvement_suggestions` + scoring dimensions |
| Performance / dimensions / signals / market / decision | `scoring.*` |
| Question assessments | `question_assessments` |
| Narrative insights (EPIC-05 fields) | `narrative.insights` |
| Coaching objectives (EPIC-05 fields) | `coaching_snapshot.collection.objectives` |
| Study recommendations | `coaching_snapshot.collection.recommendations` |
| Role / seniority / context | `role`, `seniority`, `context_profile` |
| Token usage | `generation_metadata.total_tokens_used` |
| Replay `session_id` | `session_id` |

### 3.2 LongitudinalProfile-owned (progress trend only)

| Rendered surface | Authoritative path |
|---|---|
| Progress trend panel | `LongitudinalProfile` → `LearningProgress` (`behavioral_trend`, `session_entries`, `session_count`, `has_sufficient_data`) |
| Insufficient-data state | Presentation of progress sufficiency (see §7) |

**Invariant FO-LP-01:** Progress fields are **never** embedded into `Report` for EPIC-05.  
**Invariant FO-LP-02:** Progress panel **must not** read `SessionHistory[]` (ADR-034 Decision 5).

### 3.3 Replay-owned (post-trigger only)

| Surface | Authoritative path |
|---|---|
| Replay UI panels | `ReplaySession` (EPIC-04 contracts) |
| Report→Replay handoff | `session_id` string only — identity handoff, not ReplaySession payload in report HTML |

**Invariant FO-RP-01:** Report HTML does not embed `ReplaySession`.  
**Invariant FO-RP-02:** After handoff, EPIC-04 ownership applies unchanged.

### 3.4 Explicitly not owned by EPIC-05 presentation

| Field / concern | Owner |
|---|---|
| Explainability anchors | EPIC-V13-06 |
| `Narrative` five mandatory prose sections as separate HTML panels | Not required by Master Plan EPIC-05; not EPIC-05 deliverables |
| `CoachingAction` tree rendering | Not required by Master Plan EPIC-05 Expected Outcome; deferred unless Data Model elevates |
| `SessionHistory` fields | Closed-session assembly only; forbidden in presentation |

---

## 4. Component Contracts

Component IDs align with Architecture Discovery §5 where applicable.

### 4.1 C-01 — UIResponseBuilder._build_report

| Attribute | Value |
|---|---|
| **Inputs** | `InterviewState.report: Report` (required) |
| **Outputs** | `UIResponse.report_output: str` |
| **Dependencies** | PC-02 `FinalReportDTO`, C-04 facade |
| **Responsibilities** | Call `from_report`; build HTML; never read `session_history` / evaluation |
| **Invariants** | I-C01-01: `report is None` → no report HTML / fail-fast per existing UI rules. I-C01-02: sole factory only. |

### 4.2 C-02 — FinalReportDTO

| Attribute | Value |
|---|---|
| **Inputs** | `Report` |
| **Outputs** | Complete presentation DTO including PC-03, PC-04, PC-05, `session_id` |
| **Dependencies** | Scoring/question mappers |
| **Responsibilities** | Sole mapping from `Report` → presentation fields |
| **Invariants** | I-C02-01: no second factory. I-C02-02: study recommendations non-empty mapping path (empty list only when domain recommendations empty). I-C02-03: `session_id == report.session_id`. |

### 4.3 C-03 — InterviewStateMapper.to_final_report_dto

| Attribute | Value |
|---|---|
| **Inputs** | `InterviewState.report` |
| **Outputs** | `FinalReportDTO` |
| **Dependencies** | C-02 |
| **Responsibilities** | Export entry mapping; identical sole-source rules as C-01 |

### 4.4 C-04 / C-05 / C-06 — Facade / ViewModel / Renderer

| Attribute | Value |
|---|---|
| **Inputs** | `FinalReportDTO` (+ separately injected `LearningProgress` for progress section only) |
| **Outputs** | HTML string / view-model dict |
| **Dependencies** | Section components; `ReportInsightBuilder` (presentation-only string helpers) |
| **Responsibilities** | Compose sections; no domain writes; no `SessionHistory` |
| **Invariants** | I-C05-01: Production path accepts `FinalReportDTO` only for Report-owned sections. I-C05-02: Domain-`Report` getattr fallbacks are non-production / test-only unless identical field projection. |

### 4.5 Report sections (Report-owned) — C-07…C-22

| Component | Inputs (from VM/DTO) | Outputs | Dependencies | Responsibility |
|---|---|---|---|---|
| Overall | scoring header fields | HTML | badges | Score / hire header |
| Executive | executive_summary | HTML | — | Executive prose |
| Went well | went_well | HTML | — | Strengths bullets |
| Held you back | held_you_back (`context_detail`) | HTML | — | Constraint items |
| Knowledge gaps | knowledge_gaps (`context_detail`) | HTML | — | Gap items |
| Next strategy | next_strategy (`context_detail`) | HTML | — | Strategy items |
| Performance | dims / strongest / weakest | HTML | radar chart | Performance overview |
| Dimensions | dimension insights | HTML | tables | Dimension detail |
| Questions | question_assessments | HTML | bars | Per-question assessments |
| Market | percentile fields | HTML | distribution chart | Market position |
| Decision | decision_explanation / gating | HTML | — | Decision detail |
| Signals | signal insights | HTML | insight builder | Behavioral signals |
| Roadmap | improvement / roadmap | HTML | insight builder | Improvement roadmap |
| Narrative | narrative_insights | HTML | — | Insights list (EPIC-05 fields) |
| Coaching objectives | coaching_objectives | HTML | — | Objectives list |
| Study recommendations | study_recommendations | HTML | — | Study list from PC-05 |

All: **read-only**; **Report-owned** via DTO.

### 4.6 C-23 — ProgressTrendPanel

| Attribute | Value |
|---|---|
| **Inputs** | `LearningProgress` (PC-06) |
| **Outputs** | HTML (trend or insufficient-data) |
| **Dependencies** | `ProgressTracker` / repository read of `LongitudinalProfile` **outside** `from_report` |
| **Responsibilities** | Render progress; never extrapolate; never read `Report` for trend series |
| **Invariants** | See §7 |

### 4.7 C-24 — ReportSection (Gradio chrome)

| Attribute | Value |
|---|---|
| **Inputs** | `report_output` HTML; `InterviewState.report` for replay `session_id` |
| **Outputs** | Gradio updates |
| **Dependencies** | Export handlers; C-25 |
| **Responsibilities** | Host HTML, export buttons, **Replay Session** control |
| **Replay placement contract** | Master Plan “replay entry point in the report” is **satisfied by Gradio chrome control on the report view**. In-HTML replay link is **not required**. |

### 4.8 C-25 — ReplayEntryFromReport

| Attribute | Value |
|---|---|
| **Inputs** | `session_id: str` from `Report.session_id` |
| **Outputs** | Handoff to EPIC-04 `ReplayEntryPoint.enter(session_id)` |
| **Dependencies** | EPIC-04 Replay UI |
| **Responsibilities** | Resolve identity; invoke replay; no `SessionHistory` read when report present |
| **Invariants** | I-C25-01: If `state.report is not None`, `session_id = state.report.session_id` exclusively. I-C25-02: If `state.report is None`, replay-from-report is rejected (fail-fast). |

### 4.9 C-26 — ExportHandlers / ReportExportService

| Attribute | Value |
|---|---|
| **Inputs** | `FinalReportDTO` via C-03 |
| **Outputs** | PDF / JSON |
| **Dependencies** | C-02, C-04 |
| **Responsibilities** | Same sole-source rules; no dual factory |

### 4.10 C-27 — ReportInsightBuilder

| Attribute | Value |
|---|---|
| **Inputs** | DTO scoring/dimension/percentile fields |
| **Outputs** | Presentation insight strings |
| **Dependencies** | None on engines / LLM |
| **Responsibilities** | Display helpers only; not a second source of truth |

---

## 5. Traceability Matrix

Every Master Plan EPIC-V13-05 requirement maps **exactly once**.

| # | Master Plan Requirement | Domain / Presentation Contract | Responsible Component | Verification Artifact |
|---|---|---|---|---|
| R-01 | Consolidate all report rendering paths onto sole source | PC-01, PC-02; §1.4 dual-read ban | C-01, C-04, C-05, C-06, C-07…C-22 | Architectural test: zero `SessionHistory` / `InterviewEvaluation` imports on report presentation path |
| R-02 | `FinalReportDTO` is sole consumer API for report data | PC-02 sole factory | C-02, C-03, C-26 | Unit test: `from_components` absent; all export/HTML use `from_report` |
| R-03 | Replay entry point in the report → `ReplaySession` | PC-07; FO-RP-*; C-25 invariants | C-24, C-25 | Integration test: replay-from-report uses `Report.session_id` only; lands in EPIC-04 Replay UI |
| R-04 | Progress trend panel sourced from `LongitudinalProfile` | PC-06; FO-LP-*; §7 | C-23 | Integration test: panel renders from `LearningProgress`; no `Report` trend fields |
| R-05 | No report section reads `SessionHistory` when data available on `Report` | §1.4; FO-*; I-C25-01 | C-02, C-25, all Report-owned sections | Architectural test: forbidden reads; replay resolver compliance |
| R-06 | Expose stable report surfaces for later EPIC-V13-06 (explainability not implemented) | PC-03, PC-04; §1.5 scope boundary | C-02, C-20, C-21 | Contract test: EPIC-05 DTO fields stable; no explainability fields required |
| R-07 | One data source / one report; sections traceable to `Report` fields (Expected Outcome) | §3.1 Report-owned map | C-02 + Report-owned sections | Field-coverage tests: each Report-owned section sourced from mapped DTO fields |
| R-08 | Study recommendations rendered from coaching snapshot (coaching surface completeness) | PC-05 | C-02, study recommendations section | Unit test: recommendations mapped on `from_report`; panel non-empty when domain has recommendations |
| R-09 | Insufficient-data progress state (Master Plan product risk: no extrapolation &lt; 3 sessions) | §7 Progress Trend Contract | C-23 | Unit test: insufficient-data UI when presentation sufficiency false; no fabricated trend |

**Unmet / excluded:** Explainability anchors — **not a Master Plan EPIC-05 requirement** after 2026-07-16 correction (owned by EPIC-06). No matrix row.

**Status:** 9/9 EPIC-05 requirements mapped exactly once. No unmet in-scope requirement. No dual mapping.

---

## 6. Replay Integration Contract

### 6.1 Interface

```
Report view (EPIC-05)
  → read session_id := Report.session_id
  → ReplayEntryPoint.enter(session_id)   # EPIC-04
  → ReplaySession (EPIC-03/04 ownership)
```

### 6.2 Ownership

| Concern | Owner |
|---|---|
| `session_id` value | `Report.session_id` (Report-owned) |
| Trigger control placement | EPIC-05 Gradio report chrome (C-24) |
| Replay reconstruction | EPIC-03 `replay_node` |
| Replay UI | EPIC-04 |
| `ReplaySession` fields | ADR-037 / EPIC-04 Domain Contracts |

### 6.3 Invariants

- RI-01: No `SessionHistory` read for report→replay when `Report` present.
- RI-02: No `ReplaySession` embedded in `FinalReportDTO` or report HTML.
- RI-03: No new ADR required for replay integration (AA-05).
- RI-04: In-HTML replay hyperlink not required; chrome button is the contract.

### 6.4 Out of scope

Replay navigation, panels, LLM-free enforcement inside replay — EPIC-04.

---

## 7. Progress Trend Contract

### 7.1 Ownership

| Concern | Owner |
|---|---|
| Persisted cross-session data | `LongitudinalProfile` (`longitudinal_update_node`) |
| Derived presentation model | `LearningProgress` / `LearningProgressBuilder` |
| Orchestration helper | `ProgressTracker` (application service; no persistence) |
| UI panel | C-23 ProgressTrendPanel (EPIC-05) |

### 7.2 Lifecycle (given graph order)

```
session_close → report_node → longitudinal_update → END
```

- Progress panel **must not** assume longitudinal data is available on `InterviewState` at `report_node` time.
- Progress panel loads `LearningProgress` by reading the **persisted** `LongitudinalProfile` for `candidate_identity_id` (from `Report.candidate_identity_id` or equivalent identity already on report) **at report UI render / bind time**, after longitudinal update has completed for the session — or on subsequent report view when profile is available.
- Exact timing/bind mechanics are Data Model / Implementation Plan concerns; ownership and forbidden inputs are frozen here.

### 7.3 Presentation rules

| Condition | UI |
|---|---|
| Presentation sufficiency **false** | Explicit insufficient-data state; **no trend extrapolation** |
| Presentation sufficiency **true** | Render trend from `LearningProgress.behavioral_trend` / session entries |

**Presentation sufficiency (Master Plan):** trend UI requires `LearningProgress.session_count >= 3`.

**Open modelling note (for Data Model — not resolved here):** domain invariant LP-LP-03 sets `has_sufficient_data == (session_count >= 2)`. Data Model must reconcile presentation threshold (`>= 3`) with domain flag (`>= 2`) — e.g. panel uses `session_count >= 3` explicitly, or domain flag is amended under a separate governance path. Domain Contracts **do not** change LP-LP-03.

### 7.4 Invariants

- PT-01: Progress is LongitudinalProfile-owned derivation; never Report-owned.
- PT-02: No `SessionHistory[]` input to progress derivation (ADR-034).
- PT-03: No LLM calls on progress path.
- PT-04: Empty / insufficient states are explicit; never silent zeros presented as trends.

---

## 8. Study Recommendation Contract

### 8.1 Ownership

| Concern | Owner |
|---|---|
| Domain artifact | `StudyRecommendation` on `Report.coaching_snapshot.collection.recommendations` (Report-owned; ADR-025 / ADR-033 Decision 4) |
| Presentation DTO | `StudyRecommendationDTO` on `FinalReportDTO` (PC-05) |
| Renderer | Study recommendations section |

### 8.2 Resolution of F-W-03

| Rule | Statement |
|---|---|
| SR-01 | `FinalReportDTO.from_report` **must** map `report.coaching_snapshot.collection.recommendations` → `study_recommendations`. |
| SR-02 | Production HTML path **must not** rely on domain `Report` getattr fallback for recommendations. |
| SR-03 | Empty list is valid only when domain collection is empty. |
| SR-04 | No second source (no `SessionHistory`, no live coaching engine call). |

### 8.3 DTO fields

| Field | Source |
|---|---|
| `recommendation_id` | `StudyRecommendation.recommendation_id` |
| `objective_id` | `StudyRecommendation.objective_id` |
| `resource_type` | `StudyRecommendation.resource_type` |
| `topic` | `StudyRecommendation.topic` |
| `rationale` | `StudyRecommendation.rationale` |
| `estimated_duration_hours` | `StudyRecommendation.estimated_duration_hours` |

---

## 9. Dual-Read / Dual-Ownership Prohibitions

| Prohibition | Status |
|---|---|
| Two factories for `FinalReportDTO` | Forbidden |
| Report section reading `SessionHistory` for Report-owned fields | Forbidden |
| Report→replay using `SessionHistory.session_id` when `Report` present | Forbidden |
| Progress trend reading `Report` for longitudinal series | Forbidden |
| Progress trend reading `SessionHistory[]` | Forbidden |
| Explainability implemented under EPIC-05 ownership | Forbidden (EPIC-06) |
| Two owners for any rendered field | Forbidden — §3 is authoritative |

---

## 10. Architecture Assumptions Register

| ID | Description | Status | Verification Document | Notes |
|---|---|---|---|---|
| AA-01 | Remaining EPIC-05 scope is additive presentation; sole-factory path exists | **VERIFIED** | Discovery §2; this document §1–2 | Unchanged |
| AA-02 | No report section / replay-from-report reads `SessionHistory` when field on `Report` | **VERIFIED** | This document §1.4, §6, I-C25-01 | Contract specifies sole `Report.session_id`; closes F-W-01 |
| AA-03 | ADR-033 sufficient; no new ADR required | **CONDITIONALLY VERIFIED** | This document §1, §9; final confirm at Architecture Review / Freeze | No unresolved ownership decision found; Review step still records skip/accept |
| AA-04 | `LongitudinalProfile` + `LearningProgressBuilder` suffice for progress trend | **VERIFIED** | This document §3.2, §7; ADR-034 | No new persistent artifact |
| AA-05 | Replay entry via existing `ReplayEntryPoint` without new ADR | **VERIFIED** | This document §6 | Chrome placement contracted |
| AA-06 | Explainability deferred to EPIC-06; not blocking EPIC-05 freeze | **VERIFIED** | Master Plan amendment 2026-07-16; Clarification BLOCKER REMOVED; this document §1.5 | F-B-01 closed |
| AA-07 | NarrativeInsightDTO / CoachingObjectiveDTO cover non-explainability sections; study recommendations via PC-05 | **VERIFIED** | This document PC-03, PC-04, PC-05, §8 | F-W-03 resolved at contract level |
| AA-08 | Existing Gradio/report stack sufficient | **VERIFIED** | Discovery §5; this document C-24 | Unchanged |
| AA-09 | `from_report` never reads `InterviewState` / `SessionHistory` | **VERIFIED** | PC-02; Discovery | Unchanged |
| AA-10 | Insufficient-data progress state is presentation of sufficiency; no extrapolation | **CONDITIONALLY VERIFIED** | This document §7.3 | Presentation rule `session_count >= 3` frozen here; reconcile with LP-LP-03 (`>= 2`) in Data Model |

**UNVERIFIED remaining:** none.  
**CONDITIONALLY VERIFIED remaining:** AA-03 (Review/Freeze confirmation), AA-10 (threshold reconciliation in Data Model).

---

## 11. Open Findings

### BLOCKER

None. F-B-01 removed by Master Plan correction + §1.5.

### WARNING

| ID | Finding | Status after Domain Contracts |
|---|---|---|
| F-W-01 | Replay session_id dual-read | **RESOLVED** at contract level (I-C25-01) |
| F-W-02 | Progress panel absent | **SPECIFIED** (C-23 / §7) — implementation pending |
| F-W-03 | Study recommendations empty on DTO path | **RESOLVED** at contract level (PC-05 / §8) |
| F-W-04 | Explainability fields dropped | **ACCEPTED** — out of EPIC-05 scope (§1.5) |
| F-W-05 | Longitudinal after report_node | **SPECIFIED** (§7.2) — bind timing detail → Data Model |
| F-W-06 | Stale `from_components` script | **OPEN** (tooling; implementation cleanup) |

### INFORMATION

| ID | Note |
|---|---|
| F-I-03 | Coaching actions / narrative five-sections not EPIC-05 Master Plan requirements — excluded §3.4 |
| OI-DM-01 | Data Model must reconcile progress sufficiency threshold (presentation `>= 3` vs domain `has_sufficient_data` / LP-LP-03 `>= 2`) |

---

## 12. Definition of Done — Domain Contracts (§8.2)

| Criterion | Status |
|---|---|
| Every new/changed presentation artifact has field specification | YES |
| Sole writer / readers / lifecycle declared | YES |
| Traceability Matrix complete; each Master Plan requirement once | YES (R-01…R-09) |
| No untraced dead required field | YES |
| No unmet in-scope requirement | YES |
| No alternatives evaluation (ADR territory) | YES |
| No Data Model / ADR / Freeze / implementation | YES |

---

## 13. Next Step

**Data Model Specification** — `docs/master-plan/epics/EPIC-05-DATA-MODEL.md`

Must:
- Freeze complete presentation field tables for `FinalReportDTO` extensions (`study_recommendations`, `session_id`)
- Resolve OI-DM-01 (progress sufficiency threshold)
- Verify presentation completeness for all Traceability rows
- Advance AA-10 (and confirm AA-03 path) toward VERIFIED
- Remain decision-free regarding new ADRs unless a genuine conflict appears

---

*This document is the Domain Contracts specification for EPIC-V13-05. It does not authorize implementation. Architecture Freeze remains a subsequent gate.*
