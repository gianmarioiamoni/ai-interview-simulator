# EPIC-06 — Explainability

**Status:** Final Review COMPLETE — **PASS WITH OBSERVATIONS** (0 P0/P1); Epic Close AUTHORIZED — 2026-07-22  
**Date:** 2026-07-16 (initialized); CAR/FR recovery 2026-07-22  
**Epic ID:** EPIC-V13-06  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-06; Product Goal P-06  
**Roadmap Phase:** Phase 3 — User Experience  
**Precondition:** EPIC-V13-05 CLOSED; EPIC-V13-01 CLOSED; regression baseline 6708 passing / 0 failures; working tree clean at initialization.  
**Regression baseline (initialization):** 6708 passing tests, 0 failures  
**Architecture Discovery:** `EPIC-06-EXPLAINABILITY.md` — COMPLETE  
**Domain Contracts:** `EPIC-06-DOMAIN-CONTRACTS.md` — COMPLETE  
**Data Model:** `EPIC-06-DATA-MODEL.md` — COMPLETE  
**Architecture Review:** COMPLETE (embedded Freeze §17) — **ADR STEP SKIPPED**  
**Architecture Freeze:** `EPIC-06-ARCHITECTURE-FREEZE.md` — **APPROVED**  
**Implementation Plan:** `EPIC-06-IMPLEMENTATION-PLAN.md` — **ACCEPTED**  
**Implementation:** COMPLETE (C1–C8, C10; C9/OF-04 deferred)  
**Construction Architecture Review (CAR):** **COMPLETE** — **PASS WITH OBSERVATIONS** (0 P0/P1) — 2026-07-22  
**Final Review (FR):** **COMPLETE** — **PASS WITH OBSERVATIONS** (0 P0/P1) — 2026-07-22  
**Epic Close:** AUTHORIZED (not performed)  
**Playbook:** V13 Development Playbook Version 1.0

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

Make every coaching assertion candidate-visible and traceable to its evidence source in the Unified Report UI: every `NarrativeInsight` surfaces its evidence identity; every `CoachingAction` surfaces its LearningObjective origin. Platform explainability is by design in the report experience, not by documentation alone.

*(Master Plan / historical phrases “Observation anchor” / “KnowledgeGap origin” = documentation drift D-01/D-02 — Contracts/Data Model authoritative: ProfileFeature identity + LearningObjective chain.)*

---

## 3. Architectural Objective

Extend the EPIC-05 Unified Report host surfaces so explainability is a report-section concern (not a standalone pipeline): validate evidence references before render; keep projection LLM-free; preserve sole-writer / single-source rules (`Report` / `FinalReportDTO` plane).

OF-01 presentation mechanism: **RESOLVED** in Implementation Plan — inline evidence inside existing report sections.

---

## 4. Dependencies

### Previous completed EPICs

| EPIC | Status | Dependency |
|---|---|---|
| EPIC-V13-05 | CLOSED | Unified Report host surfaces / DTO stability |
| EPIC-V13-01 | CLOSED | Clean scoring / `Report` authority |

Inherited context (not direct Master Plan dependencies for this epic): EPIC-V13-02/03/04 CLOSED via EPIC-05.

---

## 5. Expected Deliverables

- Living `EPIC-06-OVERVIEW.md` (this document — workflow status)
- Category B planning set (Discovery → Contracts → Data Model → ADR skip → Freeze → Implementation Plan)
- Report UI surfacing of `NarrativeInsight` → ProfileFeature evidence (`source_feature_id` + `is_traceable`)
- Report UI surfacing of `CoachingAction` → LearningObjective origin fields
- Pre-render / projection completeness validation (EC-V-01 fail-fast)
- Inline OF-01 presentation on C-20 + coaching actions + export parity
- Behavioral + architectural tests
- CAR (with Architecture Traceability) ← **COMPLETE**; FR ← **COMPLETE**; Epic Close AUTHORIZED

**Non-goals (Master Plan):** AI-generated explanations of explanations; NL “why” query UI (V2+); enterprise audit trails (V2).

---

## 6. Architecture Workflow

```
EPIC Initialization  ← COMPLETE
        ↓
Architecture Discovery  ← COMPLETE
        ↓
Domain Contracts  ← COMPLETE
        ↓
Data Model  ← COMPLETE
        ↓
Architecture Review  ← COMPLETE (ADR STEP SKIPPED)
        ↓
Architecture Freeze  ← APPROVED
        ↓
Implementation Plan  ← ACCEPTED (OF-01 RESOLVED)
        ↓
Implementation (M0–M4 / C1–C8, C10)  ← COMPLETE
  (ACP-M0…M4 recovered at CAR Traceability — living markers absent pre-recovery)
        ↓
CAR (incl. Architecture Traceability)  ← COMPLETE — PASS WITH OBSERVATIONS (0 P0/P1)
        ↓
Regression / Documentation Certification  ← COMPLETE (FR reconfirm)
        ↓
Final Review (FR)  ← COMPLETE — PASS WITH OBSERVATIONS (0 P0/P1)
        ↓
Epic Close  ← AUTHORIZED (not performed)
```

---

## 7. Implementation commit map (C1–C10)

| Commit | Scope | Hash (short) | Status |
|---|---|---|---|
| C1 | NarrativeInsightDTO evidence + `from_report` mapping | `da74b05` | **DONE** |
| C2 | CoachingActionDTO + `coaching_actions` origin join | `caedbbb` | **DONE** |
| C3 | Projection completeness gate (PC-E05) | `4b4389a` | **DONE** |
| C4 | Architectural tests (dual-read / LLM-free / silent-omit) | `b8fec33` | **DONE** |
| C5 | Integration Report → DTO explainability | `587cfe1` | **DONE** |
| C6 | Narrative section inline evidence (OF-01) | `696291d` | **DONE** |
| C7 | Coaching actions inline origin (OF-01) | `1589bf3` | **DONE** |
| C8 | Export parity | `6d6d893` | **DONE** |
| C9 | Optional OF-04 objective enrichment | — | **DEFERRED** (plan-allowed) |
| C10 | Acceptance fixtures + regression seal | `3607242` | **DONE** |

Production touch set confined to Report DTO / report UI / export path + tests. **No** `ReportBuilder` / domain schema / SessionHistory dual-read.

---

## 8. Construction Architecture Review (CAR)

**Date:** 2026-07-22  
**HEAD reviewed:** `97f78ce6f7baca6ac0c2561a77b37ae319fc1a48`  
**Scope:** Architecture-conformance certification only (Playbook §10). Governance recovery — living CAR markers were missing despite implementation complete. No production code. No Final Review. No Epic Close.  
**Category:** B — Architecture Traceability Review **mandatory**.  
**Verdict:** **PASS WITH OBSERVATIONS** (0 P0 / 0 P1)

### Architecture Freeze compliance

| Frozen rule | Result |
|---|---|
| Report-plane only; no standalone explainability pipeline | **PASS** |
| Narrative evidence = ProfileFeature identity (EC-N-01 / ADR-023) | **PASS** |
| Coaching origin = parent LearningObjective via `objective_id` (EC-C-01) | **PASS** |
| ADR-025 KnowledgeGap / unrealized FKs not binding | **PASS** |
| Sole factory `FinalReportDTO.from_report` | **PASS** — AT-01 |
| Additive DTO fields; no new Report writers | **PASS** |
| Fail-fast EC-V-01; empty collections valid; silent omit forbidden | **PASS** — AT-04…AT-07 intent |
| Projection LLM-free; no SessionHistory/Observation-store dual-read | **PASS** — AT-02 / AT-03 |
| OF-01 inline presentation (Impl Plan) | **PASS** — C6–C8 |
| No new ADR; ADR-023 + ADR-033 binding | **PASS** |

### Implementation Plan compliance

| Item | Result |
|---|---|
| M1 DTO migrations C1–C3 | **PASS** |
| M2 architectural + integration C4–C5 | **PASS** |
| M3 UI + export C6–C8 | **PASS** |
| M4 acceptance C10 | **PASS** |
| C9 / OF-04 | **DEFERRED** — non-blocking (plan §18) |
| Forbidden surfaces untouched | **PASS** — no ReportBuilder / domain producer changes |

### Category B Architecture Traceability Review

| Traceability item | Evidence | Status |
|---|---|---|
| `FeatureIdentityDTO` + insight evidence fields | `final_report_dto.py`; C1 | **PASS** |
| `CoachingActionDTO` + `coaching_actions` + origin join | C2; EC-C-01 | **PASS** |
| Projection completeness gate PC-E05 | C3 | **PASS** |
| AT-01 sole factory (HTML + export) | `test_export_explainability_architecture.py` | **PASS** |
| AT-02 dual-read ban | `test_explainability_architecture.py` | **PASS** |
| AT-03 LLM-free projection | same | **PASS** |
| AT-04 / AT-05 fail-fast | unit + arch tests | **PASS** |
| AT-06 silent-omit forbidden | arch tests | **PASS** |
| AT-07 empty collections | unit + IT | **PASS** |
| AT-08 knowledge_gaps ≠ coaching origin | Implemented via `objective_by_id` only; C-11 unchanged | **PASS** (no dedicated named AT-08 module — O-CAR-02) |
| IT-01…IT-06 | integration + acceptance suites | **PASS** |
| OF-01 inline UI | `narrative_section.py`; `coaching_section.py` | **PASS** |
| Export parity X-08 | C8 | **PASS** |
| Ownership / sole-writer | No new writers | **PASS** |
| Data sources = Report plane only | Contracts §2 | **PASS** |

### Explainability invariants (R-01…R-07)

| ID | Result |
|---|---|
| R-01 Insight evidence in UI + export | **PASS** |
| R-02 Action origin in UI + export | **PASS** |
| R-03 / R-04 Fail-fast / no silent omit | **PASS** |
| R-05 No standalone pipeline | **PASS** |
| R-06 No dual-read / LLM | **PASS** |
| R-07 Acceptance fixtures | **PASS** |

### Regression (CAR reconfirm)

| Metric | Value |
|---|---|
| Explainability CAR suite | **111 passed / 0 failed** |
| Full-suite context | EPIC-06 code retained through later epic closes; EPIC-10 close-out **7378 / 0** at HEAD lineage |
| Implementation gaps blocking CAR | **None** |

### Findings

| Severity | Count | Notes |
|---|---|---|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 / P3 | 5 observations | Non-blocking; see §10 |

### Authorization

**Final Review authorized** (CAR 2026-07-22). Superseded by §9 Final Review.

---

## 9. Final Review (FR)

**Date:** 2026-07-22  
**HEAD reviewed:** `e7f0b4677ed81a2de6805700fa3dcb1d5c54ff32`  
**Scope:** Epic-closure gate only (Playbook §10). Governance recovery. No implementation or architecture changes. No Epic Close.  
**Category:** B  
**Verdict:** **PASS WITH OBSERVATIONS** (0 P0 / 0 P1) — binary outcome **Closed**

### Preflight

| Item | Result |
|---|---|
| Working tree | **CLEAN** |
| HEAD | `e7f0b4677ed81a2de6805700fa3dcb1d5c54ff32` |
| CAR | **PASS WITH OBSERVATIONS** (0 P0/P1) — Final Review authorized |
| Implementation C1–C8, C10 | **COMPLETE** |
| C9 / OF-04 | **DEFERRED** (plan-allowed) |

### FR checklist

| Criterion | Result |
|---|---|
| Master Plan / Overview objectives (P-06 explainability) | **PASS** — candidate-visible insight evidence + action origins on Report plane |
| Frozen planning fully implemented | **PASS** — Freeze §22 / Contracts / Data Model / Plan C1–C8,C10; OF-04 optional deferred |
| CAR outcome incorporated | **PASS** — Traceability held; observations carried forward |
| Explainability acceptance R-01…R-07 | **PASS** |
| No temporary bridges / compatibility layers | **PASS** — none introduced |
| Runtime matches frozen architecture | **PASS** — CAR + FR suite reconfirm |
| No new InterviewState writers / dual-read | **PASS** |
| Implementation debt classified | **PASS** — O-CAR-* / OF-03 / OF-04 non-blocking |
| Evidence present | **PASS** — CAR Traceability; FR suite 111/0 |
| ADR | **SKIP** (Freeze §17) |
| Zero open P0/P1 | **PASS** |

### Regression (FR reconfirm)

| Metric | Value |
|---|---|
| Explainability FR suite | **111 passed / 0 failed** |
| Full-suite lineage | EPIC-06 retained; later epic closes green (EPIC-10 **7378 / 0**) |

### Findings

| Severity | Count | Notes |
|---|---|---|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 / P3 | 5 observations | Non-blocking; §10 |

### Authorization

**Epic Close authorized** (FR 2026-07-22). Do not perform Epic Close in this activity.

---

## 10. Remaining observations (non-blocking)

1. **O-CAR-01 / OF-03** — ADR-025 unrealized KnowledgeGap / FK documentation drift remains open docs debt (Freeze INFORMATION; out of critical path).
2. **O-CAR-02** — AT-08 intent enforced by implementation (origin join from LearningObjective; scoring `knowledge_gaps` not used as action origin) but no dedicated named `AT-08` architectural test module.
3. **O-CAR-03 / D-01–D-02** — Master Plan / historical Overview business phrases (“Observation anchor”, “KnowledgeGap origin”) intentionally accepted at Freeze; Contracts/Data Model remain authoritative.
4. **O-CAR-04** — Formal living ACP-M0…M4 checkpoint transcripts were absent pre-recovery; Traceability Review at CAR recovered conformance. Process observation only.
5. **OF-04** — Optional objective-level enrichment deferred (C9 skipped); action-level origin complete (R-02 satisfied).

---

## 11. Architecture Assumptions Register

Authoritative Contracts statuses: `EPIC-06-DOMAIN-CONTRACTS.md` §6; Freeze §18.

| ID | Status | Anchor |
|---|---|---|
| AA-01 | **VERIFIED** | EPIC-05 host + PC-E06 |
| AA-02 | **INVALIDATED** | Superseded: ProfileFeature identity (EC-N-01) |
| AA-03 | **INVALIDATED** | Superseded: LearningObjective origin chain (EC-C-01) |
| AA-04 | **VERIFIED** | Constraint + Report-plane feasibility |
| AA-05 | **VERIFIED** | Reconstruction + OF-01 executed as presentation design |
| AA-06 | **VERIFIED** | EC-V-01 fail-fast class |
| AA-07 | **VERIFIED** | ADR skip confirmed at Freeze |
| AA-08 | **INVALIDATED** | Named payloads not required; Report fields suffice |
| AA-09 | **VERIFIED** | Discovery inventory |
| AA-10 | **VERIFIED** | EPIC-06 ownership of go-live explainability |

---

## 12. Status

| Workflow step | Status |
|---|---|
| Initialization | **COMPLETE** |
| Architecture Discovery | **COMPLETE** |
| Domain Contracts | **COMPLETE** |
| Data Model | **COMPLETE** |
| Architecture Review / ADR | **COMPLETE** — ADR **SKIPPED** |
| Architecture Freeze | **APPROVED** |
| Implementation Plan | **ACCEPTED** |
| Implementation (C1–C8, C10) | **COMPLETE** |
| Construction Architecture Review (CAR) | **COMPLETE** — **PASS WITH OBSERVATIONS**; 0 P0/P1 |
| Regression Certification | **COMPLETE** — FR reconfirm **111 passed / 0 failed** |
| Documentation Certification | **COMPLETE** — Overview / Plan / Master Plan FR markers aligned |
| Final Review (FR) | **COMPLETE** — **PASS WITH OBSERVATIONS** (0 P0/P1) |
| Epic Close | **AUTHORIZED** — not performed |

---

## 13. Next Activities

1. **Epic Close** for EPIC-V13-06 — authorized by this Final Review.
2. Do **not** treat epic as CLOSED until Epic Close is performed.
3. Non-blocking carry-forward: OF-03 ADR-025 docs alignment; optional named AT-08 module; optional OF-04.

---

*This Overview is the living status document for EPIC-V13-06. Frozen Discovery / Domain Contracts / Data Model / Architecture Freeze bodies remain historical records after freeze.*
