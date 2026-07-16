# EPIC-06 — Explainability

**Status:** INITIALIZED — Architecture Discovery not started  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-06  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-06; Product Goal P-06  
**Roadmap Phase:** Phase 3 — User Experience  
**Precondition:** EPIC-V13-05 CLOSED; EPIC-V13-01 CLOSED; regression baseline 6708 passing / 0 failures; working tree clean at initialization.  
**Regression baseline (initialization):** 6708 passing tests, 0 failures

---

## 1. EPIC Identification

| Field | Value |
|---|---|
| **Identifier** | EPIC-V13-06 |
| **Title** | Explainability |
| **Master Plan reference** | `V13-PRODUCT-MASTER-PLAN.md` §4 EPIC-V13-06; Product Goal **P-06** |
| **Category** | **Category B** — Major Architectural Epic |
| **Phase** | Phase 3 — User Experience |

---

## 2. Business Objective

Make every coaching assertion candidate-visible and traceable to its evidence source in the Unified Report UI: every `NarrativeInsight` surfaces its `Observation` anchor; every `CoachingAction` surfaces its `KnowledgeGap` origin. Platform explainability is by design in the report experience, not by documentation alone.

---

## 3. Architectural Objective

Extend the EPIC-05 Unified Report host surfaces so explainability is a report-section concern (not a standalone pipeline): validate evidence references before render; keep projection LLM-free; preserve sole-writer / single-source rules (`Report` / `FinalReportDTO` plane).

The concrete presentation mechanism is intentionally left unresolved and will be determined during Architecture Discovery.

---

## 4. Dependencies

### Previous completed EPICs

| EPIC | Status | Dependency |
|---|---|---|
| EPIC-V13-05 | CLOSED | Unified Report host surfaces / DTO stability |
| EPIC-V13-01 | CLOSED | Clean scoring / `Report` authority |

Inherited context (not direct Master Plan dependencies for this epic): EPIC-V13-02/03/04 CLOSED via EPIC-05.

### Prerequisites

- EPIC-05 Architecture Freeze scope boundary: explainability owned exclusively by EPIC-06; narrative/coaching EPIC-05 DTO fields stable for additive extension
- ADR-033 Unified Report architecture (explainability out of EPIC-05)
- Domain evidence fields already governed by ADR-023 (`NarrativeInsight`) and ADR-025 (`CoachingAction`)

### Architectural assumptions inherited

- Projection never computes (ARC-01 P-01); explainability is presentation of existing evidence, not new runtime computation
- Single Ownership / no dual-read of `SessionHistory` for Report-owned sections (EPIC-05 / ADR-033)
- EPIC-05 deferred columns (`source_feature_id`, `is_traceable`, KnowledgeGap origin surfacing) are EPIC-06 scope
- Domain invariant I-15 must become candidate-visible, not only internally enforced

---

## 5. Expected Deliverables

- Living `EPIC-06-OVERVIEW.md` (this document — workflow status)
- Category B planning set (Discovery → Contracts → Data Model → conditional ADR → Freeze → Implementation Plan)
- Report UI surfacing of `NarrativeInsight` → Observation anchors
- Report UI surfacing of `CoachingAction` → KnowledgeGap origins
- Pre-render validation of evidence references; missing-anchor handling policy as classified by Architecture Discovery
- Presentation mechanism as determined by Architecture Discovery (not selected at initialization)
- Behavioral + architectural tests for explainability coverage / missing-anchor policy
- CAR (with Architecture Traceability), Regression, Documentation Certification, FR, Epic Close

**Non-goals (Master Plan):** AI-generated explanations of explanations; NL “why” query UI (V2+); enterprise audit trails (V2).

---

## 6. Implementation Risk Assessment

| Risk | Likelihood | Notes |
|---|---|---|
| Sparse / missing evidence anchors across real sessions | Medium | Master Plan product risk; coverage must be validated before ship |
| Scope creep into runtime recomputation or SessionHistory dual-read | Medium | Must remain projection on Report-plane / EPIC-05 surfaces |
| Premature ADR or presentation mechanism locked without Discovery | Medium | Playbook: ADR only if unresolved decision remains after Contracts + Data Model |
| Confusion with EPIC-05 boundary (re-open F-B-01) | Low | Master Plan amendment 2026-07-16 closed circular dep; EPIC-06 → EPIC-05 only |
| Missing-anchor handling policy misclassified | Medium | Domain invariant violation vs presentation degradation — open until Discovery |

---

## 7. Estimated Size

**Medium (M)** — focused presentation/DTO extension + UI + validation on frozen Unified Report host; smaller than EPIC-05 consolidation, larger than a pure Category A polish epic.

---

## 8. Candidate ADR Evaluation

| Existing ADR | Relevance | Reuse? |
|---|---|---|
| ADR-023 Narrative Intelligence | `NarrativeInsight` + `source_feature_id` / traceability | **Reuse** |
| ADR-025 Coaching Intelligence | `CoachingAction` + `source_gap_id` / explainability principles | **Reuse** |
| ADR-033 Unified Report | Report sole source; explainability deferred from EPIC-05 | **Reuse** |
| ADR-016 Observation schema | Observation as evidence substrate | **Reuse** (as needed) |

**Policy application:** Reuse existing ADRs. **Do not author a new ADR at initialization.** Propose a new ADR only if Architecture Discovery → Domain Contracts → Data Model leave a genuine unresolved architectural decision.

**Initialization recommendation:** Conditional ADR step expected to be **skipped unless Discovery proves otherwise**.

---

## 9. Required Planning Documents

| # | Document | Role |
|---|---|---|
| 1 | `docs/master-plan/epics/EPIC-06-OVERVIEW.md` | Living Category B status surface |
| 2 | Architecture Discovery document | Current vs target; Component Inventory; Assumptions Register |
| 3 | `docs/master-plan/epics/EPIC-06-DOMAIN-CONTRACTS.md` | Field-level contracts + Traceability Matrix |
| 4 | `docs/master-plan/epics/EPIC-06-DATA-MODEL.md` | Frozen field tables; presentation completeness; assumptions VERIFIED |
| 5 | Architecture Review / ADR (conditional) | Only if unresolved decision remains |
| 6 | `docs/master-plan/epics/EPIC-06-ARCHITECTURE-FREEZE.md` | Gate authorizing implementation |
| 7 | `docs/master-plan/epics/EPIC-06-IMPLEMENTATION-PLAN.md` | Phases + commit boundaries + Dependency Validation |

---

## 10. Architecture Workflow

```
EPIC Initialization  ← COMPLETE (refined 2026-07-16)
        ↓
Architecture Discovery  ← NEXT
        ↓
Domain Contracts
        ↓
Data Model
        ↓
Architecture Review
(ADR only if required)
        ↓
Architecture Freeze
        ↓
Implementation Plan
        ↓
Implementation
  (Macro Phase → Architecture Checkpoint → …)
        ↓
CAR (incl. Architecture Traceability)
        ↓
Regression
        ↓
Documentation Certification
        ↓
Final Review (FR)
        ↓
Epic Close
```

---

## 11. Known Inputs

Existing artifacts Architecture Discovery is expected to inspect. **No architectural decisions. No analysis. No assumptions.**

### Existing ADRs

- ADR-016 — Observation schema architecture
- ADR-023 — Narrative intelligence architecture
- ADR-025 — Coaching intelligence architecture
- ADR-033 — Unified Report architecture
- ADR-034 / ADR-037 — Accepted governing ADRs referenced by EPIC-05 (inspect as needed for Report / replay boundaries)

### Existing domain artifacts

- `Report`
- `Narrative` / `NarrativeSection` / `NarrativeInsight` (incl. domain `source_feature_id`, `is_traceable`)
- `CoachingPlan` / `LearningObjective` / `CoachingAction` (incl. domain `source_gap_id`, `source_feature_id`)
- `CoachingSnapshot` (as carried on `Report`)
- `Observation`
- `KnowledgeGap`
- `ProfileFeature` / feature identity types used by narrative and coaching traceability

### Existing presentation artifacts

- `FinalReportDTO` (sole factory `from_report`)
- `NarrativeInsightDTO` (EPIC-05 field set; explainability fields deferred)
- Coaching presentation DTOs (`CoachingObjectiveDTO` and related EPIC-05 coaching DTO surfaces)
- `StudyRecommendationDTO`

### Existing report artifacts

- `report_node` / `ReportBuilder` / `Report` production path
- `FinalReportDTO.from_report` mapping path
- Report HTML / markdown composition path (`build_report_markdown` / report facade / renderer)
- EPIC-05 frozen planning documents: `EPIC-05-DOMAIN-CONTRACTS.md`, `EPIC-05-DATA-MODEL.md`, `EPIC-05-ARCHITECTURE-FREEZE.md`, `EPIC-05-UNIFIED-REPORT.md`, `EPIC-05-OVERVIEW.md`

### Existing UI host components

- C-01 — `UIResponseBuilder._build_report`
- C-02 — `FinalReportDTO`
- C-03 — `InterviewStateMapper.to_final_report_dto`
- C-04 / C-05 / C-06 — Report facade / view-model / renderer
- C-11 — KnowledgeGapSection
- C-20 — NarrativeSection
- C-21 — CoachingObjectivesSection
- C-22 — StudyRecommendationsSection
- C-24 — ReportSection (Gradio chrome)
- C-26 — ExportHandlers / ReportExportService
- C-27 — ReportInsightBuilder
- File-level hosts under `app/ui/views/report/` (sections, renderer, view-model builder) and `app/ui/dto/final_report_dto.py`

---

## 12. Architecture Assumptions Register

| ID | Description | Initial status | Verification document | Notes |
|---|---|---|---|---|
| AA-01 | EPIC-05 narrative/coaching DTO surfaces are stable hosts for additive explainability fields | UNVERIFIED | Architecture Discovery; Domain Contracts | From EPIC-05 Freeze / Data Model §7 |
| AA-02 | Domain `NarrativeInsight` already carries traceable evidence identity (`source_feature_id` / ADR-023) sufficient for Observation anchoring | UNVERIFIED | Architecture Discovery; Domain Contracts | No new runtime producer assumed |
| AA-03 | Domain `CoachingAction` already carries `source_gap_id` (ADR-025) sufficient for KnowledgeGap origin surfacing | UNVERIFIED | Architecture Discovery; Domain Contracts | |
| AA-04 | Explainability is projection/presentation only — no LLM, no `reasoner_node` recomputation, no SessionHistory dual-read for Report-owned sections | UNVERIFIED | Architecture Discovery; Architecture Freeze | ARC-01 P-01; ADR-033 |
| AA-05 | Presentation-mechanism choice does not introduce a new sole-writer domain artifact or persistent schema | UNVERIFIED | Architecture Discovery; Component Inventory | Mechanism unresolved at initialization |
| AA-06 | The handling policy for missing evidence anchors shall be architecturally classified during Architecture Discovery (domain invariant violation vs presentation degradation) | UNVERIFIED | Architecture Discovery; Domain Contracts; Data Model | Policy not chosen at initialization |
| AA-07 | No new ADR is required if ADR-023 / ADR-025 / ADR-033 fully cover ownership and boundaries after Contracts + Data Model | UNVERIFIED | Architecture Review (conditional); Architecture Freeze | Playbook §8.4 |
| AA-08 | Observation / KnowledgeGap payloads needed for UI are already reachable via Report-plane / EPIC-05 host data without new persistence writers | UNVERIFIED | Architecture Discovery; Data Model | Extensibility claim from EPIC-05 |
| AA-09 | Epic is UI-bearing → Component Inventory is mandatory in Architecture Discovery | UNVERIFIED | Architecture Discovery | Playbook Component Inventory rule |
| AA-10 | Go-live explainability checklist items (every NarrativeInsight / CoachingAction surfaced) are acceptance criteria for this epic, not EPIC-05 | UNVERIFIED | Domain Contracts Traceability Matrix; Architecture Freeze | Master Plan §5 Product |

**UNVERIFIED:** AA-01…AA-10. **VERIFIED:** none. **INVALIDATED:** none.

---

## 13. Recommendation

**Next engineering task:** Produce Architecture Discovery for EPIC-V13-06 (Category B step 2). No Domain Contracts, no ADR, no implementation.

---

*This Overview is the living status document for EPIC-V13-06. Frozen Discovery / Domain Contracts / Data Model / Architecture Freeze bodies (when authored) remain historical records after freeze.*
