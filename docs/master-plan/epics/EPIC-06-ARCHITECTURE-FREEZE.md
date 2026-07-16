# EPIC-06 — Explainability: Architecture Freeze

**Status:** ARCHITECTURE FREEZE APPROVED  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-06  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Architecture Freeze (Playbook §8.5)  
**Precondition:** `EPIC-06-OVERVIEW.md`, `EPIC-06-DOMAIN-CONTRACTS.md`, `EPIC-06-DATA-MODEL.md` COMPLETE; Architecture Review COMPLETE (ADR STEP SKIPPED); no production code modified  
**Authority:** Formal gate between planning and implementation. EPIC-06 implementation may not begin until this document declares APPROVED. Implementation Plan acceptance remains a subsequent Exit Criterion.

---

## Save Token (precondition)

| Check | Result |
|---|---|
| Working tree | Clean |
| HEAD | `11422b96338d66481511318fd0aab207ff807eed` (`11422b9` — docs(epic-06): define explainability data model) |
| Stash | Not created |

---

## 1. Architecture Freeze Certification

### ARCHITECTURE FREEZE: APPROVED

The Explainability architecture for EPIC-V13-06 is frozen.

| Gate | Verdict |
|---|---|
| Architecture Discovery | PASS |
| Domain Contracts | PASS |
| Data Model | PASS |
| Architecture Review / ADR (conditional) | PASS — **ADR STEP SKIPPED** |
| Architecture Assumptions (architectural scope) | PASS — see §6 |
| BLOCKER findings | PASS — zero open |
| Architectural contradiction review | PASS |
| Category B Exit Criteria (planning subset) | PASS |

**BLOCKER count: 0**

Implementation planning may proceed. Production implementation begins only after Implementation Plan acceptance.

---

## 2. Authority Hierarchy Consistency

| Rank | Authority | EPIC-06 role |
|---|---|---|
| 1 | ADR-033 | Report sole source; `FinalReportDTO.from_report`; dual-read ban; explainability on Report plane |
| 2 | ADR-023 | Narrative evidence identity (`source_feature_id`, `is_traceable`); explainability principle |
| 3 | ADR-025 | Historical reference only — **not** EPIC-06 binding schema |
| 4 | Domain Contracts | Ownership, EC-N-01 / EC-C-01 / EC-V-01, Traceability Matrix |
| 5 | Data Model | Field tables, serialization, reconstruction, failure model |
| 6 | Overview | Living status surface (not field authority) |

| Check | Verdict | Class |
|---|---|---|
| Contracts subordinate to ADR-023 / ADR-033 | Consistent | PASS |
| Data Model subordinate to Contracts (no ownership rewrite) | Consistent | PASS |
| ADR-025 not used as binding schema | Consistent with Contracts §8 / Data Model §12 | PASS |
| Overview §2 Master Plan phrases (“Observation anchor”, “KnowledgeGap origin”) vs Contracts binding | Historical wording retained on Overview; Contracts/Data Model authoritative | WARNING — Documentation drift (non-blocking) |

**Authority hierarchy review: PASS** (no blockers).

---

## 3. Cross-Document Consistency

| Topic | Overview | Domain Contracts | Data Model | ADRs | Verdict |
|---|---|---|---|---|---|
| Narrative evidence target | Business wording: Observation | ProfileFeature identity (EC-N-01) | Same + DTO fields | ADR-023 C-02 | PASS under Contracts authority; Overview wording = drift WARNING |
| Coaching origin | Business wording: KnowledgeGap | Parent `LearningObjective` (EC-C-01) | Same + `CoachingActionDTO` | ADR-025 text unrealized | PASS under Contracts; ADR-025 = OF-03 |
| Fail-fast | Inherited AA-06 | EC-V-01 | §10–§11 | ADR-033 / ARC-01 | PASS |
| Sole factory | PC-E06 host | PC-E06 | DM-FR-01 | ADR-033 I-A | PASS |
| No new Report writer | Stated | §4.1 | DM-P-01 / DM-E06-01 | ADR-033 | PASS |
| Reconstruction completeness | AA-05 partial | Feasibility AA-04 | §8 VERIFIED | — | PASS |
| Presentation mechanism | Unresolved at init | Out of Contracts | OF-01 open | N/A | PASS — non-architectural (§12) |

**Cross-document consistency review: PASS** (WARNING only on Overview/Master Plan legacy phrases).

---

## 4. Ownership Model

| Concern | Sole owner | Sole writer | Sole presentation API | Freeze |
|---|---|---|---|---|
| Narrative evidence identity | Domain narrative (ADR-023) | NarrativeGenerator → Report | `from_report` | PASS |
| Narrative explainability DTO fields | EPIC-06 presentation | `from_report` | C-20 / C-26 | PASS |
| Coaching action + origin | Domain coaching / LearningObjective | CoachingEngine → Report | `from_report` → action surface | PASS |
| Coaching explainability DTO | EPIC-06 presentation | `from_report` | Coaching hosts / C-26 | PASS |
| Scoring-narrative knowledge_gaps | EPIC-01/05 | Scoring narrative assembly | C-11 (out of origin contract) | PASS |
| Validation gate | EPIC-06 projection | `from_report` / pre-render | Render + export | PASS |

No shared ownership. **Ownership review: PASS.**

---

## 5. Sole-Writer Invariants

| Invariant | Source | Freeze |
|---|---|---|
| NarrativeGenerator sole writer of Narrative / insight evidence | ADR-023 | PASS |
| CoachingEngine sole writer of CoachingSnapshot tree | ADR-025 runtime / implemented path | PASS |
| `report_node` / ReportBuilder sole Report assembly writers | ADR-033 | PASS — EPIC-06 does not add writers |
| `FinalReportDTO.from_report` sole presentation factory | ADR-033 I-A / PC-E06 | PASS |
| No SessionHistory / Observation-store dual-read on explainability path | ADR-033 / AA-04 | PASS |

**Sole-writer review: PASS.**

---

## 6. Report-Only Presentation Model

| Rule | Evidence | Verdict |
|---|---|---|
| Explainability is Report-section concern | Contracts R-05; Overview architectural objective | PASS |
| No standalone explainability pipeline | Contracts §5 / forbidden scope | PASS |
| Projection LLM-free | ARC-01; Contracts §4.3; Data Model SR-07 | PASS |
| DTO-only UI consumption on production path | PC-E02–PC-E06 | PASS |

**Report-only presentation review: PASS.**

---

## 7. Explainability Reconstruction Completeness

| Required persisted field | On implemented domain / Report | Verdict |
|---|---|---|
| `NarrativeInsight.source_feature_id` | Yes | PASS |
| `NarrativeInsight.is_traceable` | Yes | PASS |
| `FeatureIdentity` components | Yes | PASS |
| `CoachingAction.objective_id` | Yes | PASS |
| Parent `LearningObjective` origin fields | Yes | PASS |

Presentation DTO gaps are **Data Model extensions** (implementation), not domain persistence gaps.

**Reconstruction review: PASS.**  
AA-05 architectural half: **VERIFIED**. Remaining OF-01 is non-architectural (§12).

---

## 8. Fail-Fast Semantics

| Layer | Rule | Verdict |
|---|---|---|
| Domain | Invalid insight evidence / `is_traceable=False` | PASS (ADR-023 + EC-V-01) |
| Snapshot | Unresolved `objective_id` | PASS (EC-C-01 / Data Model X-03) |
| Projection | Missing required explainability DTO fields | PASS (EC-V-01 / §11) |
| Empty sets | Valid | PASS |
| Silent omission | Forbidden | PASS |

**Fail-fast review: PASS.**

---

## 9. DTO Mapping Completeness

| Mapping | Frozen in Data Model | Verdict |
|---|---|---|
| `NarrativeInsightDTO` + `source_feature_id` / `is_traceable` | §2.3 | PASS |
| `FeatureIdentity` serialization shape | §2.2 | PASS |
| `CoachingActionDTO` + origin fields | §3.3 | PASS |
| `FinalReportDTO.coaching_actions` | §5.1 | PASS |
| Optional `CoachingObjectiveDTO.supporting_observation_types` | §3.4 (OF-04) | PASS — optional |
| Sole factory mapping algorithm | §5.2 | PASS |

OF-02: **Resolved** at Data Model. **DTO mapping review: PASS.**

---

## 10. Presentation Architecture Boundaries

| In scope | Out of scope |
|---|---|
| Additive DTO fields; projection validation; candidate-visible evidence on Report hosts | Domain schema redesign; KnowledgeGap introduction; Observation embedding |
| C-20 / coaching hosts / C-26 consuming DTO | SessionHistory dual-read; LLM explainability; NL “why” UI |
| Export parity via same factory | New Report writers |

Concrete layout/interaction mechanism: **out of architectural freeze** — see §12 OF-01.

**Presentation boundary review: PASS.**

---

## 11. Documentation Drift Classification

| ID | Drift | Class | Freeze disposition |
|---|---|---|---|
| D-01 | Master Plan / Overview “Observation anchor” vs ADR-023 ProfileFeature | Documentation drift | **INTENTIONALLY ACCEPTED** for EPIC-06 binding (EC-N-01) |
| D-02 | “KnowledgeGap origin” vs LearningObjective chain | Documentation drift | **INTENTIONALLY ACCEPTED** (EC-C-01) |
| D-03 / OF-03 | ADR-025 unrealized FKs / KnowledgeGap entity vs implemented coaching | Documentation drift | **Confirmed documentation-alignment-only** |
| Overview §2 retained Master Plan phrases | Same as D-01/D-02 | WARNING | Non-blocking; Contracts/Data Model authoritative |

### OF-03 explicit verification

| Question | Verdict |
|---|---|
| ADR-025 differences = historical documentation drift only? | **YES** |
| Any implemented contract diverges from EPIC-06 binding? | **NO** |
| Architecture issue / Domain Contracts extension required? | **NO** |
| ADR amendment required before Freeze? | **NO** |

**Documentation drift review: PASS.**

---

## 12. Serialization Consistency

| Rule set | Evidence | Verdict |
|---|---|---|
| Enum → `.value` strings | Data Model SR-01 | PASS |
| FeatureIdentity nested required keys | SR-02 / §2.2 | PASS |
| ObservationType → `List[str]` | SR-03 | PASS |
| No defaulting required explainability fields | SR-06 | PASS |
| Report schema_version unchanged | DM-V-01 | PASS |

Minor host-type choice (`FeatureIdentityDTO` vs inline dict with same keys): **implementation-local** — not architectural divergence.

**Serialization review: PASS.**

---

## 13. Remaining Architectural Decisions

| Decision | Status |
|---|---|
| Narrative evidence target | Frozen — ProfileFeature identity |
| Coaching origin model | Frozen — parent LearningObjective |
| Missing-evidence class | Frozen — fail-fast |
| Persistence writers | Frozen — none new |
| Sole presentation factory | Frozen — `from_report` |
| ADR required? | **No** |

**Unresolved architectural decisions: none.**

---

## 14. OF-01 — Presentation Mechanism Classification

| Question | Verdict |
|---|---|
| Is OF-01 an architectural decision (ownership, sole-writer, source plane, fail-fast class)? | **NO** |
| Is OF-01 an implementation decision (module/file placement, helper extraction)? | Partially — only after UX choice |
| Is OF-01 a presentation-layer design choice (layout, interaction, visual surfacing)? | **YES** |

**Disposition:** OF-01 is a **presentation-layer design choice**. It does not alter ownership, persistence, DTO required fields, validation class, or ADR-033/023 boundaries.

**ADR required for OF-01?** **NO.**

**Freeze impact:** Non-blocking. Mechanism selection belongs in Implementation Plan / UI phase within frozen DTO contracts. AA-05 architectural reconstruction remains VERIFIED; mechanism portion is explicitly non-architectural and does not reopen Architecture Review.

---

## 15. Hidden Implementation Decisions

| Item | Class | Freeze disposition |
|---|---|---|
| `FeatureIdentityDTO` type vs inline dict | Implementation-local | Allowed if keys/requiredness match Data Model |
| Validation hook timing (`from_report` vs immediate pre-render) | Implementation-local within PC-E05 | Both allowed; fail-fast required |
| Whether to project optional objective `supporting_observation_types` (OF-04) | Presentation/implementation choice | Optional; must not replace action-level origin |
| Exact Gradio/HTML chrome for evidence display (OF-01) | Presentation-layer design | Deferred to Implementation Plan |
| Exception type / error messaging for projection failures | Implementation-local | Must fail-fast; no silent omit |

No hidden architectural decisions found.

---

## 16. Document Duplication

| Duplication | Class | Disposition |
|---|---|---|
| Evidence resolutions restated across Contracts + Data Model | INFORMATION | Acceptable layering (ownership vs fields) |
| AA register mirrored Overview / Contracts / Data Model | INFORMATION | Overview is living; Data Model authoritative for AA-05 split |
| Master Plan / Overview business phrases vs Contracts binding | WARNING | Drift classified; no Freeze blocker |

**Duplication review: PASS** (no contradictory duplicate authorities beyond classified drift).

---

## 17. Architecture Review Result

### 17.1 Decision

**ADR STEP SKIPPED**

No genuine unresolved architectural decision remains after Domain Contracts and Data Model. OF-01 is non-architectural. OF-03 is documentation drift only.

### 17.2 Governing ADRs

| ADR | Role in EPIC-06 |
|---|---|
| **ADR-023** | Binding — narrative evidence / explainability |
| **ADR-033** | Binding — Unified Report plane / sole factory |
| **ADR-025** | Historical reference — not binding schema |
| **ADR-016** | Substrate only — not presentation source |

### 17.3 Review validation

| Check | Result |
|---|---|
| Unresolved ownership | None |
| Unresolved lifecycle | None |
| Unresolved field model | None (DTO tables frozen) |
| Unresolved dependency | None |
| Unresolved architectural decision | None |

**Architecture Review: PASS.**

---

## 18. Architecture Assumptions Review

| ID | Status | Freeze disposition |
|---|---|---|
| AA-01 | **VERIFIED** | Additive EPIC-05 host |
| AA-02 | **INVALIDATED** | Superseded by EC-N-01 |
| AA-03 | **INVALIDATED** | Superseded by EC-C-01 |
| AA-04 | **VERIFIED** | Report-plane feasibility |
| AA-05 | **VERIFIED** (architectural scope) | Reconstruction complete; OF-01 carved out as non-architectural presentation design |
| AA-06 | **VERIFIED** | Fail-fast |
| AA-07 | **VERIFIED** | ADR skip confirmed |
| AA-08 | **INVALIDATED** | Named payloads not required |
| AA-09 | **VERIFIED** | Inventory / hosts |
| AA-10 | **VERIFIED** | EPIC-06 ownership |

**UNVERIFIED (architectural): none**  
**Assumptions review: PASS.**

---

## 19. Finding Summary

| ID | Finding | Class | Freeze disposition |
|---|---|---|---|
| OF-01 | Presentation mechanism unresolved | INFORMATION | **Presentation-layer design choice** — deferred to Implementation Plan; **no ADR** |
| OF-02 | DTO field tables | WARNING (historical) | **RESOLVED** — Data Model |
| OF-03 | ADR-025 documentation drift | INFORMATION | **Confirmed documentation-alignment-only**; no implemented-contract divergence vs EPIC-06 binding |
| OF-04 | Optional objective origin enrichment | INFORMATION | **Resolved as optional** |
| D-01/D-02 | Overview/Master Plan legacy phrases | WARNING | **INTENTIONALLY ACCEPTED** — Contracts/Data Model authoritative |

### Classification totals

| Class | Open at Freeze | Blocks Freeze? |
|---|---|---|
| BLOCKER | 0 | — |
| WARNING | Overview/Master Plan wording drift (D-01/D-02) | **No** |
| INFORMATION | OF-01, OF-03 (accepted), OF-04 (optional) | **No** |

**Findings review: PASS.**

---

## 20. Exit Criteria

| # | Criterion | Verdict |
|---|---|---|
| 1 | Architecture Discovery complete | **SATISFIED** |
| 2 | Component Inventory complete | **SATISFIED** (Discovery / Overview §11) |
| 3 | Traceability Matrix complete | **SATISFIED** (Contracts §5; Data Model §7) |
| 4 | Domain Contracts frozen | **SATISFIED** |
| 5 | Data Model frozen | **SATISFIED** |
| 6 | Architecture Assumptions VERIFIED (architectural scope) | **SATISFIED** — §18 |
| 7 | No BLOCKER findings open | **SATISFIED** |
| 8 | ADR decisions complete (where required) | **SATISFIED** — ADR STEP SKIPPED |
| 9 | Architecture Freeze declared | **SATISFIED** — this document |
| 10 | Implementation Plan accepted | **PENDING** |

Items 1–9 satisfied. Item 10 is the sole remaining gate before production code changes.

---

## 21. Architecture Contradiction Review

| Check | Result |
|---|---|
| Ownership conflicts | **None** |
| Dual-read paths allowed | **None** |
| Dual ownership | **None** |
| Fail-fast vs degradation conflict | **None** — EC-V-01 wins over Master Plan “graceful” for required fields |
| ADR-025 text vs implemented binding | **Classified drift** — not a contradiction under hierarchy |
| Overview business phrases vs Contracts | **Classified drift** — Contracts win |
| Hidden architectural decisions | **None** |

**Contradiction review: PASS.**

---

## 22. Frozen Architecture Summary

1. Explainability is Report-plane only; LLM-free projection; no standalone pipeline.
2. Narrative evidence = `NarrativeInsight.source_feature_id` + `is_traceable` (ADR-023); not Observation payloads.
3. Coaching action origin = parent `LearningObjective` via `objective_id` on same `coaching_snapshot` (EC-C-01).
4. ADR-025 KnowledgeGap / unrealized FKs are documentation drift; not EPIC-06 binding targets.
5. Sole presentation API = `FinalReportDTO.from_report`; additive DTO fields only; no new Report writers.
6. Required DTO additives: insight evidence fields; `coaching_actions` / `CoachingActionDTO` with origin fields.
7. Missing required evidence → fail-fast (EC-V-01); empty collections valid; silent omit forbidden.
8. Reconstruction uses only fields already on `Report`; Report `schema_version` bump not required.
9. No new ADR; governing binding set = ADR-023 + ADR-033.
10. OF-01 (UI mechanism) is presentation-layer design — Implementation Plan scope; not an ADR.
11. Zero Known Failing Tests on every implementation commit (Playbook §2).
12. Modifications to frozen planning docs require Freeze Integrity Check (Playbook §9).

---

## 23. Implementation Readiness

| Prerequisite | Status |
|---|---|
| EPIC-V13-05 CLOSED | SATISFIED |
| ADR-023, ADR-033 Accepted | SATISFIED |
| Domain Contracts + Data Model COMPLETE | SATISFIED |
| Architecture Freeze APPROVED | SATISFIED — this document |
| Implementation Plan accepted | PENDING |

### Remaining implementation risks (non-blocking)

| Risk | Likelihood | Note |
|---|---|---|
| Sparse real-session evidence coverage | Medium | Product risk; validate fixtures/coverage in implementation |
| Export/HTML parity miss on new fields | Medium | Enforce same factory (X-08) |
| Accidental dual-read / soft-hide of missing anchors | Medium | Architecture Checkpoint must reject |
| OF-01 UX underspecification delaying UI | Low–Medium | Plan must pick mechanism within frozen DTO contracts |
| Confusion with scoring-narrative knowledge_gaps | Low | EC-C-02; keep C-11 distinct |

### Architecture Checkpoint Mandate

Implementation Plan must define macro phases with mandatory Architecture Checkpoints after each completed macro phase.

---

## 24. Definition of Done — Architecture Freeze (§8.5)

| Criterion | Status |
|---|---|
| Architecture Exit Criteria (planning) satisfied | YES — §20 items 1–9 |
| Explicit record of ADR required / skipped | YES — §17 ADR STEP SKIPPED |
| Architecture Assumptions VERIFIED (architectural scope) | YES — §18 |
| Traceability Matrix referenced | YES |
| Component Inventory referenced | YES |
| No open issues that block freeze | YES |
| OF-01 / OF-03 classified | YES — §11, §14 |
| No modifications to prior planning docs / ADRs in this step | YES |

---

## 25. Next Step

Produce **Implementation Plan**: `docs/master-plan/epics/EPIC-06-IMPLEMENTATION-PLAN.md`

Include OF-01 presentation-mechanism selection as an implementation/UX planning item bounded by frozen DTO contracts. Do not reopen ownership, persistence, or ADR-025 redesign.

---

## 26. Architecture Freeze Decision

**APPROVED**

EPIC-V13-06 is architecturally complete and implementation-ready pending Implementation Plan acceptance.

---

*Architecture Freeze complete. No production code modified. No ADRs modified. No prior planning documents modified.*
