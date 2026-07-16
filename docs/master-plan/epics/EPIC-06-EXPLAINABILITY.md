# EPIC-06 — Explainability: Architecture Discovery

**Status:** ARCHITECTURE DISCOVERY COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-06  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Architecture Discovery (Playbook §8.1)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-06; Product Goal P-06  
**Precondition:** EPIC-V13-05 CLOSED; EPIC-V13-01 CLOSED; Initialization COMPLETE (refined); regression baseline 6708 / 0.  
**Authority:** Findings only. No architecture decisions. No Domain Contracts. No Data Model. No ADR. No implementation plan. No presentation-mechanism selection.

---

## 1. Executive Summary

### 1.1 Business Objective (Master Plan)

Make every coaching assertion traceable to its evidence source, surfaced in the report UI. Candidates must be able to trace coaching advice to a specific observation / evidence origin in their session. The platform is explainable by design, not by documentation.

### 1.2 Architectural Objective (Initialization — neutral)

Extend EPIC-05 Unified Report host surfaces so explainability is a report-section concern: validate evidence references before render; keep projection LLM-free; preserve sole-writer / single-source rules.

The concrete presentation mechanism is intentionally left unresolved.

### 1.3 Scope (Master Plan §4 EPIC-V13-06)

- Every `NarrativeInsight` must render its evidence anchor in the report (I-15 candidate-visible)
- Every `CoachingAction` must render its `KnowledgeGap` origin
- Validate evidence references before report render; classify missing-anchor handling (not chosen here)
- UI affordance deferred to later planning / UX — not selected in Discovery

### 1.4 Non-Goals (Master Plan)

- AI-generated explanations of explanations
- Natural language “why” query interface (V2+)
- Audit trails for enterprise compliance (V2)

### 1.5 Dependencies

| Dependency | Status | Role |
|---|---|---|
| EPIC-V13-05 | CLOSED | Unified Report host; stable narrative/coaching DTO surfaces; explainability deferred |
| EPIC-V13-01 | CLOSED | `Report` sole scoring / report authority |
| ADR-023 / ADR-025 / ADR-033 / ADR-016 | Accepted | Known Inputs ADRs |

### 1.6 Discovery Verdict (findings only)

Explainability is **not surfaced** today. Domain narrative carry `source_feature_id` / `is_traceable` but presentation drops them. Master Plan coaching explainability wording assumes `CoachingAction` → `KnowledgeGap` linkage that **does not exist in the implemented schema**. Observation payloads are **not** embedded on `Report`. These are structural gaps for Domain Contracts — not solved here.

---

## 2. Current Architecture

*As implemented. No target proposals.*

### 2.1 Narrative explainability path

| Layer | Current state |
|---|---|
| Domain `NarrativeInsight` | `insight_type`, `prose`, `source_feature_id: FeatureIdentity` (required), `confidence`, `is_traceable` (must be `True`), `schema_version` |
| Evidence target | **ProfileFeature identity** (ADR-023 C-02). No Observation ID field. No `evidence_anchor` field in codebase. |
| On `Report` | Full `Narrative` including insights embedded |
| `NarrativeInsightDTO` | Maps **only** `insight_type`, `prose`, `confidence` |
| `narrative_section.py` | Renders type label, confidence, prose only |
| Pre-render validation of anchors | **None** beyond domain construction (`is_traceable` must be True) |

### 2.2 Coaching explainability path

| Layer | Current state |
|---|---|
| Domain `CoachingAction` | `action_id`, `objective_id`, `category`, `description`, `effort_estimate_hours`, `is_immediate`, `tags` |
| ADR-025 declared fields | `source_gap_id`, `source_feature_id`, `is_traceable`, etc. — **not present on implemented model** |
| Domain `LearningObjective` | `objective_id`, `feature_type`, `description`, `priority`, `confidence`, `supporting_observation_types` (enum types, not Observation IDs), `detected_at_question_index`, `candidate_identity_id` |
| On `Report` | `coaching_snapshot` holds objectives, actions, recommendations |
| `CoachingObjectiveDTO` | Maps objective fields only (no origin / evidence fields) |
| Coaching UI | Renders **objectives only** (`coaching_section.py`) |
| `CoachingAction` in report UI | **Not projected. Not rendered.** |

### 2.3 Observation / KnowledgeGap substrate

| Artifact | Current state |
|---|---|
| `Observation` | Exists as domain contract with `ObservationId` and metadata |
| On `Report` | Observation **payloads not embedded**. `CandidateProfileSnapshot` / `FeatureProvenance` carry `source_observation_ids` (IDs only) |
| `KnowledgeGap` class | **No `class KnowledgeGap` in domain codebase** |
| Domain Freeze / ADR-025 | Describe KnowledgeGap as coaching origin |
| Report “knowledge gaps” | `ScoringNarrative.knowledge_gaps: ScoringNarrativeItem` prose items (`category`, `description`, `why_it_matters`, `context_detail`) — not KnowledgeGap entities |
| UI `knowledge_gap_section.py` | Renders scoring-narrative knowledge-gap prose from DTO — not coaching-action origins |

### 2.4 Unified Report presentation plane (EPIC-05)

| Concern | Current state |
|---|---|
| Sole factory | `FinalReportDTO.from_report(Report)` |
| Dual-read ban | Report-owned sections read via DTO; no SessionHistory in section renderers (EPIC-05 closed) |
| Explainability fields | Explicitly deferred to EPIC-06 in EPIC-05 Domain Contracts / Data Model |
| Extensibility claim (EPIC-05 Data Model §7) | Additive DTO fields + section enrichment supported without changing ADR-033 planes |

### 2.5 Domain invariant I-15 (docs)

From `V1.2-DOMAIN-FREEZE.md`:

> **I-15 — NarrativeInsights must be anchored.** Every NarrativeInsight must reference at least one Observation **or** ProfileFeature as its evidence anchor.

Code today enforces ProfileFeature + `is_traceable=True` at construction. I-15 is **not** named in Python. Candidate-facing surfacing does **not** exist.

Related docs invariant **I-10**: CoachingActions must map to KnowledgeGaps — **not reflected** in implemented `CoachingAction` schema.

### 2.6 Report validation

`ReportValidator` enforces structural report invariants (R-01…R-10 class). No insight/action evidence-anchor completeness checks before render.

---

## 3. Target Capability

*Master Plan product capability only. Not an implementation design.*

EPIC-V13-06 is expected to deliver:

1. Candidate-visible evidence for every `NarrativeInsight` in the Unified Report.
2. Candidate-visible KnowledgeGap (or authoritative origin) for every `CoachingAction` in the Unified Report.
3. Validation that evidence references are present/consistent before the report is rendered to the candidate.
4. A defined handling policy when evidence is missing (policy classification required; policy not chosen in Discovery).
5. Explainability as part of the report experience hosted on EPIC-05 surfaces — not a standalone product surface.
6. Preservation of constitutional constraints: projection LLM-free; Report sole source for Report-owned sections; no dual-read regression.

Non-goals remain as Master Plan §4 Non-Goals.

---

## 4. Affected Subsystems

| Subsystem | Responsibility | Ownership | Current role | Expected interaction with explainability |
|---|---|---|---|---|
| Domain — `Narrative` / `NarrativeInsight` | Evidence-grounded narrative findings | NarrativeGenerator / knowledge pipeline | Carries `source_feature_id`; embedded on `Report` | Source of narrative evidence identity for presentation |
| Domain — `CoachingSnapshot` / `LearningObjective` / `CoachingAction` | Coaching plan artifacts | CoachingEngine | Objectives rendered; actions stored but not rendered; no gap FK on actions | Master Plan names actions as explainability carriers |
| Domain — `Observation` / `FeatureProvenance` | Evidence substrate / feature lineage | Observation / FeatureEngine | Observations exist; IDs on profile features; payloads not on Report | Potential Observation resolution path (reachability open) |
| Domain — scoring “knowledge gaps” | Candidate-facing gap prose | Scoring / `ScoringNarrative` | Rendered as report section; not coaching FK | Possible confusion with Master Plan “KnowledgeGap origin” |
| Domain — `Report` / `ReportBuilder` / `report_node` | Sole report artifact production | `report_node` | Embeds narrative + coaching + profile snapshot | Host artifact for projection; writer ownership unchanged unless Contracts prove otherwise |
| Presentation — `FinalReportDTO` + mappers | Sole presentation API | EPIC-05 / UI DTO layer | Omits explainability fields by design | Additive host for EPIC-06 fields (EPIC-05 §7) |
| Presentation — Narrative / Coaching sections | Candidate-facing HTML | Report UI | No anchors / no action origins | Host sections for explainability surfacing |
| Presentation — Knowledge gap section | Scoring narrative gaps | Report UI | Prose gaps only | Distinct from coaching-action origin unless Contracts unify |
| Export / `ReportExportService` | Export parity with HTML | EPIC-05 | Uses `from_report` | Must remain sole-source if explainability enters DTO |
| Replay UI coaching panel | Replay coaching display | EPIC-04 | Objectives + recommendations | Out of EPIC-06 Master Plan scope unless Contracts expand; noted as adjacent |
| Tests / architectural enforcement | Regression + invariants | Test suite | No explainability surface tests | Will need coverage after Contracts freeze |

---

## 5. Component Inventory

*Existing components only. No invented explainability components.*

### C-01 — UIResponseBuilder._build_report

| Attribute | Value |
|---|---|
| Responsibility | Build report HTML from `InterviewState.report` via sole DTO factory |
| Owner | Application UI / EPIC-05 |
| Inputs | `InterviewState.report: Report` |
| Outputs | `UIResponse.report_output: str` |
| Dependencies | `FinalReportDTO`, report facade |
| Read/write | Read Report; write UI response string |
| Consumed artifacts | `Report` → `FinalReportDTO` |

### C-02 — FinalReportDTO

| Attribute | Value |
|---|---|
| Responsibility | Sole presentation projection from `Report` |
| Owner | `app/ui/dto/final_report_dto.py` / EPIC-05 |
| Inputs | `Report` |
| Outputs | Presentation DTO including `NarrativeInsightDTO`, `CoachingObjectiveDTO`, study recommendations, `session_id` |
| Dependencies | Report field mappers |
| Read/write | Read-only projection |
| Consumed artifacts | `Report.narrative.insights` (partial), `Report.coaching_snapshot` (objectives + recommendations; **not actions**) |

### C-03 — InterviewStateMapper.to_final_report_dto

| Attribute | Value |
|---|---|
| Responsibility | Export/entry mapping to `FinalReportDTO` |
| Owner | Application mappers / EPIC-05 |
| Inputs | `InterviewState.report` |
| Outputs | `FinalReportDTO` |
| Dependencies | C-02 |
| Read/write | Read-only |
| Consumed artifacts | Same as C-02 |

### C-04 / C-05 / C-06 — Report facade / ViewModel / Renderer

| Attribute | Value |
|---|---|
| Responsibility | Compose report HTML sections from DTO / VM |
| Owner | `app/ui/views/report/` |
| Inputs | `FinalReportDTO` (+ Plane B `LearningProgress` for progress only) |
| Outputs | HTML string / view-model |
| Dependencies | Section renderers C-07…C-22 (EPIC-05 inventory) |
| Read/write | Read-only |
| Consumed artifacts | DTO fields only for Report-owned sections |

### C-11 — KnowledgeGapSection

| Attribute | Value |
|---|---|
| Responsibility | Render scoring-narrative knowledge-gap prose |
| Owner | `knowledge_gap_section.py` / EPIC-05 |
| Inputs | DTO `knowledge_gaps` dicts |
| Outputs | HTML |
| Dependencies | Report renderer |
| Read/write | Read-only |
| Consumed artifacts | `ScoringNarrativeItem` projections — **not** coaching `CoachingAction` origins |

### C-20 — NarrativeSection

| Attribute | Value |
|---|---|
| Responsibility | Render narrative insights list |
| Owner | `narrative_section.py` / EPIC-05 |
| Inputs | `narrative_insights` VM/DTO entries |
| Outputs | HTML (type, confidence, prose) |
| Dependencies | C-06 |
| Read/write | Read-only |
| Consumed artifacts | `NarrativeInsightDTO` fields only — **no** `source_feature_id` / `is_traceable` |

### C-21 — CoachingObjectivesSection

| Attribute | Value |
|---|---|
| Responsibility | Render coaching objectives |
| Owner | `coaching_section.py` / EPIC-05 |
| Inputs | `coaching_objectives` |
| Outputs | HTML (priority, feature_type, confidence, description) |
| Dependencies | C-06 |
| Read/write | Read-only |
| Consumed artifacts | `CoachingObjectiveDTO` — **no** KnowledgeGap / Observation origin fields; **no actions** |

### C-22 — StudyRecommendationsSection

| Attribute | Value |
|---|---|
| Responsibility | Render study recommendations |
| Owner | EPIC-05 |
| Inputs | `study_recommendations` |
| Outputs | HTML |
| Dependencies | C-06 / PC-05 |
| Read/write | Read-only |
| Consumed artifacts | `StudyRecommendationDTO` |

### C-24 — ReportSection (Gradio chrome)

| Attribute | Value |
|---|---|
| Responsibility | Host report HTML, export, replay control |
| Owner | Gradio report chrome / EPIC-05 |
| Inputs | `report_output`; `Report.session_id` for replay |
| Outputs | Gradio updates |
| Dependencies | C-25 replay entry |
| Read/write | Read-only presentation chrome |
| Consumed artifacts | Report HTML; session identity |

### C-26 — ExportHandlers / ReportExportService

| Attribute | Value |
|---|---|
| Responsibility | Export report via sole DTO factory |
| Owner | EPIC-05 |
| Inputs | `FinalReportDTO` |
| Outputs | Export artifacts |
| Dependencies | C-02 / C-03 |
| Read/write | Read-only |
| Consumed artifacts | Same Report-plane fields as HTML |

### C-27 — ReportInsightBuilder

| Attribute | Value |
|---|---|
| Responsibility | Presentation string helpers for scoring/signal/roadmap sections |
| Owner | EPIC-05 |
| Inputs | DTO scoring fields |
| Outputs | Display strings |
| Dependencies | None on engines / LLM |
| Read/write | Read-only helpers |
| Consumed artifacts | Scoring / dimension DTO fields — **not** explainability anchors |

### Inventory gap note (not a component invention)

No existing component currently surfaces NarrativeInsight evidence identity, Observation anchors, CoachingAction rows, or CoachingAction→KnowledgeGap origins. Discovery records this absence; it does not invent replacement components.

---

## 6. Known Inputs Review

### 6.1 Existing ADRs

| Artifact | Current purpose | Relevance to EPIC-06 | Architectural observations |
|---|---|---|---|
| ADR-016 Observation schema | Defines Observation as evidence substrate | High — Master Plan names Observation anchors | Observations exist; not embedded as payloads on `Report` |
| ADR-023 Narrative intelligence | Freezes `NarrativeInsight` + `source_feature_id` (ProfileFeature) | High — implemented and enforced at domain construction | Anchors to **ProfileFeature**, not Observation ID; aligns with I-15 “or ProfileFeature” |
| ADR-025 Coaching intelligence | Declares CoachingAction `source_gap_id` / `source_feature_id` and explainability principles | High — Master Plan / I-10 rely on this model | **Implementation diverges:** `CoachingAction` lacks gap/feature FK fields |
| ADR-033 Unified Report | Report sole source; presentation via `FinalReportDTO` | High — host architecture | Explainability deferred; additive presentation extension claimed by EPIC-05 |
| ADR-034 / ADR-037 | Progress / replay boundaries for EPIC-05 | Low–medium — plane boundaries | Planes B/C unaffected by explainability unless Contracts expand scope |

### 6.2 Existing domain artifacts

| Artifact | Current purpose | Relevance | Architectural observations |
|---|---|---|---|
| `Report` | Authoritative session report | Host | Embeds narrative + coaching + profile snapshot; no Observation payloads |
| `NarrativeInsight` | Atomic narrative finding | Core | Has `source_feature_id` / `is_traceable`; no Observation field |
| `LearningObjective` | Coaching objective | High | Has `feature_type` + `supporting_observation_types`; no gap IDs |
| `CoachingAction` | Concrete coaching step | Core (Master Plan) | On snapshot; **no** `source_gap_id`; **not rendered** |
| `CoachingSnapshot` | Coaching aggregate on Report | High | Contains actions unused by UI |
| `Observation` | Evidence unit | Core (Master Plan wording) | Reachable only via IDs on feature provenance / snapshot — not as Report-embedded payloads |
| `KnowledgeGap` (docs) | Coaching origin concept | Core (Master Plan wording) | **No implemented domain class**; scoring uses `ScoringNarrativeItem` |
| `ProfileFeature` / `FeatureIdentity` | Feature identity + provenance | High | Provenance holds `source_observation_ids` |

### 6.3 Existing presentation artifacts

| Artifact | Current purpose | Relevance | Architectural observations |
|---|---|---|---|
| `FinalReportDTO` | Sole presentation API | Host | Stable for additive fields per EPIC-05 |
| `NarrativeInsightDTO` | Insight presentation | Core | Explainability fields intentionally absent |
| `CoachingObjectiveDTO` | Objective presentation | Core | No origin fields; actions absent |
| `StudyRecommendationDTO` | Study list | Adjacent | Linked to objectives, not gap origins |

### 6.4 Existing report artifacts

| Artifact | Current purpose | Relevance | Architectural observations |
|---|---|---|---|
| `report_node` / `ReportBuilder` | Produce `Report` | Boundary | Sole writers of Report; Discovery finds no evidence EPIC-06 must change writers — Contracts must confirm |
| `from_report` mapping | DTO projection | Core | Drop point for explainability fields today |
| Report HTML path | Candidate render | Core | No evidence UI |
| EPIC-05 frozen docs | Host contracts / extensibility | Process | Explicit EPIC-06 deferral + additive extensibility recorded |

### 6.5 Existing UI host components

Reviewed in §5. Primary explainability-adjacent hosts: C-20, C-21, C-11, C-02, C-04–C-06, C-26. None currently implement explainability.

---

## 7. Architecture Assumptions Register

| ID | Description | Status | Justification |
|---|---|---|---|
| AA-01 | EPIC-05 narrative/coaching DTO surfaces are stable hosts for additive explainability fields | **VERIFIED** | EPIC-05 Data Model §7 and Architecture Freeze record additive DTO/section extension without ADR-033 plane change; matches current `FinalReportDTO` sole-factory architecture |
| AA-02 | Domain `NarrativeInsight` already carries traceable evidence identity (`source_feature_id`) **sufficient for Observation anchoring** | **INVALIDATED** | Domain carries **ProfileFeature** identity (ADR-023), not Observation identity. No Observation field on `NarrativeInsight`. Master Plan wording (“Observation anchor”) does not match implemented narrative anchor type. I-15 permits Observation **or** ProfileFeature — terminology conflict remains an open question |
| AA-03 | Domain `CoachingAction` already carries `source_gap_id` (ADR-025) | **INVALIDATED** | Implemented `CoachingAction` has no `source_gap_id` / `source_feature_id`. ADR-025 taxonomy is not realized in code |
| AA-04 | Explainability is projection/presentation only — no LLM, no `reasoner_node` recomputation, no SessionHistory dual-read for Report-owned sections | **VERIFIED** (constraint) | ARC-01 P-01, ADR-033, Master Plan / EPIC-05 freeze require projection-only report path. **Feasibility without domain schema work remains open** (see AA-08 / OQ-01 / OQ-02) — constraint verified; feasibility not claimed |
| AA-05 | Presentation-mechanism choice does not introduce a new sole-writer domain artifact or persistent schema | **UNVERIFIED** | Presentation mechanism unresolved; cannot verify without selecting a mechanism |
| AA-06 | Missing evidence-anchor handling shall be architecturally classified (domain invariant violation vs presentation degradation) | **UNVERIFIED** | Discovery frames the question (OQ-03) but does **not** choose the policy (reserved for Domain Contracts / later gates) |
| AA-07 | No new ADR required if ADR-023 / ADR-025 / ADR-033 fully cover ownership after Contracts + Data Model | **UNVERIFIED** | Premature before Contracts. Discovery notes ADR-025↔code drift may become an ADR candidate if Contracts cannot reconcile within existing decisions |
| AA-08 | Observation / KnowledgeGap payloads needed for UI are already reachable via Report-plane / EPIC-05 host data without new persistence writers | **INVALIDATED** | Observation payloads not on `Report`; no KnowledgeGap domain type; coaching actions lack gap FK. Report-plane alone does not currently expose the Master Plan’s named origin payloads |
| AA-09 | Epic is UI-bearing → Component Inventory mandatory | **VERIFIED** | This document §5 |
| AA-10 | Go-live explainability checklist items are EPIC-06 acceptance criteria, not EPIC-05 | **VERIFIED** | Master Plan amendment 2026-07-16; EPIC-05 Non-Goals / Freeze scope boundary |

**Summary:** VERIFIED: AA-01, AA-04 (constraint), AA-09, AA-10. INVALIDATED: AA-02, AA-03, AA-08. UNVERIFIED: AA-05, AA-06, AA-07.

---

## 8. Open Questions

| ID | Question | Class |
|---|---|---|
| OQ-01 | Master Plan requires NarrativeInsight → **Observation** anchor; implemented domain anchors to **ProfileFeature** (`source_feature_id`); Observations are not embedded on `Report`. What is the authoritative evidence target for EPIC-06 candidate surfacing? | **BLOCKER** |
| OQ-02 | Master Plan requires CoachingAction → **KnowledgeGap** origin; no `KnowledgeGap` domain type exists; implemented `CoachingAction` has no gap FK; ADR-025 declares fields absent from code. What is the authoritative coaching origin model for EPIC-06? | **BLOCKER** |
| OQ-03 | Missing evidence-anchor handling: domain invariant violation (fail-fast) vs presentation degradation — which architectural class applies at report render? | **BLOCKER** |
| OQ-04 | `CoachingAction` exists on `Report.coaching_snapshot` but is never projected/rendered. Is EPIC-06 required to surface **action-level** origins, objective-level origins, or both? | **WARNING** |
| OQ-05 | Are scoring-narrative `knowledge_gaps` (`ScoringNarrativeItem`) related to, distinct from, or a substitute for Master Plan “KnowledgeGap origin”? | **WARNING** |
| OQ-06 | If Observation payloads are required candidate-facing, can they be resolved from `Report.profile_snapshot` feature provenance IDs alone, or is additional Report-plane data required? (Reachability only — no design.) | **WARNING** |
| OQ-07 | Concrete presentation mechanism remains unresolved (Initialization neutrality). | **INFORMATION** |
| OQ-08 | I-15 allows Observation **or** ProfileFeature; Master Plan EPIC-06 text is Observation-specific — documentation consistency to resolve in Contracts. | **INFORMATION** |
| OQ-09 | ADR-025 / Domain Freeze I-10 vs implemented coaching schema — accepted ADR vs code drift must be reconciled in later planning (Contracts and possibly ADR evaluation). | **WARNING** |

---

## 9. Architecture Risks

| ID | Risk |
|---|---|
| R-01 | Master Plan product language assumes domain linkages that are not implemented (Observation on insights; KnowledgeGap on actions) |
| R-02 | Surfacing explainability without resolving OQ-01/OQ-02 may produce cosmetic UI over incomplete evidence |
| R-03 | Confusing scoring-narrative knowledge-gap prose with coaching KnowledgeGap origins |
| R-04 | Dual-read temptation: fetching Observation store / SessionHistory from UI to “complete” anchors |
| R-05 | Silent omission of missing anchors (Master Plan product risk) vs Fail-Fast constitutional tension |
| R-06 | ADR-025 documentation treated as implemented truth — planning on non-existent fields |
| R-07 | Scope creep into CoachingEngine / NarrativeGenerator recomputation under explainability pressure |
| R-08 | Export/HTML parity breakage if explainability enters HTML path only |

*No mitigations in Discovery.*

---

## 10. Candidate ADR Evaluation

| ADR | Evaluation |
|---|---|
| ADR-023 | **Existing ADR sufficient** for NarrativeInsight → ProfileFeature identity semantics as implemented |
| ADR-016 | **Existing ADR sufficient** as Observation substrate definition |
| ADR-033 | **Existing ADR sufficient** for Unified Report sole-source / presentation plane; explainability remains additive presentation concern unless Contracts prove otherwise |
| ADR-025 | **Possible future ADR candidate** — accepted taxonomy (`source_gap_id`, etc.) diverges from implemented `CoachingAction` / missing KnowledgeGap type. May alternatively be reconciled in Domain Contracts without a new ADR if Contracts explicitly bind EPIC-06 to the **implemented** schema and record ADR-025 drift as out-of-band debt. **No ADR authored here.** |
| New explainability ADR | **Not warranted at Discovery.** Re-evaluate after Domain Contracts + Data Model only if ownership, projection boundary, or persistence writer decisions remain unresolved |

**Discovery recommendation on ADR step:** defer; conditional; reuse first.

---

## 11. Confirmed Decisions (already frozen elsewhere — not new)

| Decision | Governing artifact |
|---|---|
| Explainability owned by EPIC-06, not EPIC-05 | Master Plan amendment 2026-07-16; EPIC-05 Freeze |
| `FinalReportDTO.from_report` sole presentation factory | ADR-033; EPIC-05 |
| NarrativeInsight domain requires `source_feature_id` + `is_traceable=True` | ADR-023; code |
| Projection never computes; report path LLM-free | ARC-01 P-01 |
| Presentation mechanism unresolved at Initialization / Discovery | EPIC-06 Overview |

---

## 12. Missing Decisions (for later stages)

- Authoritative evidence target for narrative (Observation vs ProfileFeature vs both)
- Authoritative coaching origin model (KnowledgeGap entity vs scoring item vs objective linkage vs schema extension)
- Whether actions must enter presentation plane
- Missing-anchor handling policy class
- Presentation mechanism
- Whether any domain schema / builder change is in EPIC-06 scope (if required for reachability) vs presentation-only mapping of existing fields
- ADR-025 drift remediation path

---

## 13. Recommendation

**Next engineering task (exactly one):**  
**Produce Domain Contracts for EPIC-V13-06**, resolving BLOCKER open questions OQ-01, OQ-02, and OQ-03 against existing ADRs and implemented artifacts — without selecting a presentation mechanism and without authoring an ADR unless Contracts prove a genuine unresolved decision remains.

---

## 14. Playbook §8.1 Definition of Done Checklist

| Criterion | Status |
|---|---|
| Current state vs target capability analysis complete | YES (§2–§3) |
| Affected subsystems identified | YES (§4) |
| Confirmed decisions listed with governing ADR/docs | YES (§11) |
| Missing decisions listed as open items | YES (§8, §12) |
| Risks identified and classified | YES (§9) |
| Component Inventory complete (UI-bearing; existing only) | YES (§5) |
| Architecture Assumptions Register populated with statuses | YES (§7) |
| No code produced or modified | YES |

---

*Architecture Discovery complete. Findings only. No Domain Contracts. No Data Model. No ADR. No implementation.*
