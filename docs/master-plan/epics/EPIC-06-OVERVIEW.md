# EPIC-06 — Explainability

**Status:** CAR COMPLETE — **PASS WITH OBSERVATIONS** (0 P0/P1); Final Review AUTHORIZED — 2026-07-22  
**Date:** 2026-07-16 (initialized); CAR recovery 2026-07-22  
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
**Final Review (FR):** PENDING (authorized by CAR)  
**Epic Close:** PENDING  
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
- CAR (with Architecture Traceability) ← **COMPLETE**; Regression / Docs / FR / Epic Close remain

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
Regression / Documentation Certification  ← PENDING (FR path)
        ↓
Final Review (FR)  ← AUTHORIZED
        ↓
Epic Close  ← PENDING
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
| P2 / P3 | 3 observations | Non-blocking; see §9 |

### Authorization

**Final Review authorized** (CAR 2026-07-22). Do not perform Final Review or Epic Close in this activity.

---

## 9. Open observations (non-blocking)

1. **O-CAR-01 / OF-03** — ADR-025 unrealized KnowledgeGap / FK documentation drift remains open docs debt (Freeze INFORMATION; out of critical path).
2. **O-CAR-02** — AT-08 intent enforced by implementation (origin join from LearningObjective; scoring `knowledge_gaps` not used as action origin) but no dedicated named `AT-08` architectural test module.
3. **O-CAR-03 / D-01–D-02** — Master Plan / historical Overview business phrases (“Observation anchor”, “KnowledgeGap origin”) intentionally accepted at Freeze; Contracts/Data Model remain authoritative.
4. **O-CAR-04** — Formal living ACP-M0…M4 checkpoint transcripts were absent pre-recovery; Traceability Review at CAR recovered conformance. Process observation only.
5. **OF-04** — Optional objective-level enrichment deferred (C9 skipped); action-level origin complete (R-02 satisfied).

---

## 10. Architecture Assumptions Register

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

## 11. Status

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
| Regression Certification | **PENDING** (FR path; CAR reconfirm 111/0) |
| Documentation Certification | **PENDING** (FR path; living Overview aligned at CAR) |
| Final Review (FR) | **AUTHORIZED** — not performed |
| Epic Close | **PENDING** |

---

## 12. Next Activities

1. **Final Review (FR)** for EPIC-V13-06 — authorized by this CAR.
2. Do **not** treat epic as CLOSED until FR + Epic Close complete.
3. Non-blocking: OF-03 ADR-025 docs alignment; optional named AT-08 module; optional OF-04.

---

*This Overview is the living status document for EPIC-V13-06. Frozen Discovery / Domain Contracts / Data Model / Architecture Freeze bodies remain historical records after freeze.*
