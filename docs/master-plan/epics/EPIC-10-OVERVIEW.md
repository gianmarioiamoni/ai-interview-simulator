# EPIC-10 — Final Architecture Cleanup

**Status:** IMPLEMENTATION IN PROGRESS — Macro B complete; Checkpoint B ready  
**Date:** 2026-07-21  
**Epic ID:** EPIC-V13-10  
**Playbook Category:** Category B — Major Architectural Epic (**confirmed** — Freeze)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-10; Product Goal P-10  
**Roadmap Phase:** Phase 5 — Release Gate  
**Precondition:** EPIC-V13-01 CLOSED; EPIC-V13-09 CLOSED; Phase 4 complete; working tree clean at initialization.  
**Regression baseline (initialization):** 7485 passed / 0 failed (EPIC-09 close-out)  
**EPIC-10 implementation baseline (pre-P1):** 7485 passed / 0 failed (reconfirmed 2026-07-21; ≥ planning baseline)  
**P1 regression (post C1–C2):** 7490 passed / 0 failed (+5 AT-04/AT-05)  
**P3 regression (post C6–C7):** 7494 passed / 0 failed  
 
**Architecture Discovery:** `EPIC-10-ARCHITECTURE-DISCOVERY.md` — **COMPLETE**  
**Architecture Review:** `EPIC-10-ARCHITECTURE-REVIEW.md` — **APPROVED WITH OBSERVATIONS**  
**Formal ADR:** **SKIP** (AR-11 — ADR required: NO)  
**Domain Contracts:** `EPIC-10-DOMAIN-CONTRACTS.md` — **APPROVED**  
**Data Model:** **N/A — CERTIFIED** (Contracts §8)  
**Architecture Freeze:** `EPIC-10-ARCHITECTURE-FREEZE.md` — **APPROVED**  
**Implementation Plan:** `EPIC-10-IMPLEMENTATION-PLAN.md` — **ACCEPTED**  
**Implementation:** Macro B COMPLETE (P2–P3); next Macro C / P4  
**Playbook:** V13 Development Playbook Version 1.0

**Disambiguation:** Not PRD EPIC-10 (Progress Tracking). This is V13 Final Architecture Cleanup / release-gate audit.

---

## 1. EPIC Identification

| Field | Value |
|---|---|
| **Identifier** | EPIC-V13-10 |
| **Title** | Final Architecture Cleanup |
| **Master Plan reference** | `V13-PRODUCT-MASTER-PLAN.md` §4 EPIC-V13-10; Product Goal **P-10** |
| **Category** | **Category B** — Major Architectural Epic |
| **Phase** | Phase 5 — Release Gate |
| **Category rationale** | Review AR-13: state-contract Ownership Matrix + possible InterviewState field deletion. Domain Contracts REQUIRED; Data Model N/A by default (AR-07). |

---

## 2. Business Objective

Leave the codebase in a state suitable for long-term production maintenance: complete the V1.2 technical debt register deferred into V1.3, enforce all V1.3 PAT requirements, and close the release-gate architecture checklist with zero known architectural violations.

---

## 3. Architectural Objective

Close the Phase 5 architecture audit problem space defined by the Master Plan:

- Formal registration / enforcement of emerging V1.2 retrospective patterns plus Reconstruction Completeness (alongside the six original PATs).
- Disposition of every `deprecated` annotation (delete or promote with a deletion milestone).
- Complete `InterviewState` ownership audit (declared sole writer and declared readers per field).
- Enforce PAT-06 corollary: services must not implement routing logic via service-to-service calls.
- Retire dead test infrastructure from V1.2 migration scaffolding.
- Satisfy deploy-artifact dead-code purity deferred from EPIC-08 (`TD-EP08-001` / AR-16).

Concrete cleanup mechanisms, registry locations, ownership declaration formats, and deletion sequences are intentionally left unresolved and will be determined during Architecture Discovery.

---

## 4. Dependencies

### Master Plan dependencies (blocking)

| EPIC | Status | Dependency |
|---|---|---|
| EPIC-V13-01 | CLOSED | Scoring pipeline migration complete before architecture audit can close scoring residue findings |

### Phase 5 / release-gate sequencing (context)

| EPIC | Status | Notes |
|---|---|---|
| EPIC-V13-02 … EPIC-V13-07 | CLOSED | Feature / UX surface complete — full audit runs after Phase 3/4 product work |
| EPIC-V13-08 | CLOSED WITH OBSERVATIONS | Carry-forward `TD-EP08-001` — deploy-artifact dead-code purity deferred to EPIC-10 |
| EPIC-V13-09 | CLOSED | Phase 4 complete; performance baseline published; next roadmap activity is EPIC-10 |

### Prerequisites (Definition of Ready)

- [x] Master Plan epic definition unambiguous (scope, outcome, non-goals)
- [x] EPIC-V13-01 CLOSED
- [x] EPIC-V13-09 CLOSED (Phase 4 complete)
- [x] Working tree clean at initialization
- [x] Category confirmation — Category B confirmed (Discovery §9); Contracts/Data Model conditional (ARD-07)
- [x] Full inventory of `deprecated`, dead code, and `InterviewState` ownership gaps — Architecture Discovery

---

## 5. Expected Deliverables

- Living `EPIC-10-OVERVIEW.md` (this document — workflow status)
- Category B planning set as required after Discovery (Discovery → Contracts/Data Model if needed → conditional ADR → Freeze → Implementation Plan)
- Formalized registration of the four emerging retrospective patterns + Reconstruction Completeness PAT (Master Plan: six original + five new PATs named and enforced where possible)
- Disposition of every `deprecated` annotation (delete or promote with deletion milestone)
- `InterviewState` ownership matrix: every field has declared sole writer and declared readers
- PAT-06 corollary enforcement (architectural tests where feasible)
- Retirement of dead V1.2 migration test scaffolding
- Deploy-artifact dead-code purity close-out (`TD-EP08-001`)
- Zero known architectural / constitutional violations at epic close
- CAR (with Architecture Traceability), Regression, Documentation Certification, FR, Epic Close

**Non-goals (Master Plan):** New feature implementation; test coverage expansion beyond architectural enforcement; performance optimisation (addressed by respective epics).

---

## 6. Implementation Risk Assessment

| ID | Risk | Likelihood | Notes (Discovery required — no design) |
|---|---|---|---|
| R-01 | InterviewState ownership audit forces state-contract or write-order changes | Medium | Category B trigger; may require Contracts / Data Model |
| R-02 | PAT formalization conflicts with existing OP-* / PAT registry naming | Medium | Six PATs vs OP-* vs “five new PATs” inventory must be reconciled in Discovery |
| R-03 | Deprecated deletion breaks latent consumers or deploy artifact | High | Master Plan: deletion completes migration; inventory before delete |
| R-04 | Scope expands into feature work or performance work | Medium | Non-goals bind; Product Before Features |
| R-05 | PAT-06 corollary surface is broader than expected (routing via services) | Medium | Discovery must bound enforcement targets |
| R-06 | Phase 1 governance partial work vs Phase 5 full-audit boundary unclear | Medium | Master Plan distinguishes governance phase from Phase 5 full audit |
| R-07 | Reconstruction Completeness enforcement overlaps prior epic audits | Medium | Reuse prior matrices; avoid duplicate ownership |
| R-08 | Premature ADR / mechanism selection at Initialization | Low | Architecture-neutral Initialization; ADR only if needed after Contracts + Data Model |

---

## 7. Estimated Size

**Large (L)** — cross-cutting audit (patterns, deprecations, state ownership, dead code, deploy artifact) with release-gate closure criteria; size confirmed after Architecture Discovery inventory.

---

## 8. Candidate ADR Evaluation

| Existing artifact | Relevance | Reuse? |
|---|---|---|
| ARC-01 — Architecture Constitution | Constitutional constraints for cleanup / ownership | **Reuse** |
| `V1.2-PATTERN-FREEZE.md` (PAT-01…PAT-06) | Original six PATs | **Reuse** |
| Architecture Guide OP-01…OP-06 | Emerging / operative patterns already documented | **Reuse** (inspect; do not re-decide at init) |
| Prior epic ADRs / Freezes (01–09) | Scoring residue, replay, report, ops deferred items | **Reuse** as needed |
| Technical Debt Register (`TD-EP08-001`, others) | Deferred cleanup inventory | **Reuse** |

**Policy application:** Reuse existing ADRs / constitution / pattern documents. **Do not author a new ADR at initialization.** Propose a new ADR only if Architecture Discovery → Domain Contracts → Data Model leave a genuine unresolved architectural decision.

**Initialization recommendation:** Conditional ADR step expected to be **skipped unless Discovery proves otherwise**.

---

## 9. Required Planning Documents

| # | Document | Role |
|---|---|---|
| 1 | `docs/master-plan/epics/EPIC-10-OVERVIEW.md` | Living Category B status surface (this document) |
| 2 | `docs/master-plan/epics/EPIC-10-ARCHITECTURE-DISCOVERY.md` | Architecture Discovery (next) |
| 3 | Domain Contracts (conditional) | Only if Discovery proves contract work |
| 4 | Data Model (conditional) | Only if Contracts required |
| 5 | Architecture Review / ADR (conditional) | Only if unresolved decision remains |
| 6 | `docs/master-plan/epics/EPIC-10-ARCHITECTURE-FREEZE.md` | Gate authorizing Implementation Plan |
| 7 | `docs/master-plan/epics/EPIC-10-IMPLEMENTATION-PLAN.md` | Phases + commit boundaries + Dependency Validation |

---

## 10. Architecture Workflow

```
EPIC Initialization  ← COMPLETE
        ↓
Architecture Discovery  ← COMPLETE
        ↓
Architecture Review  ← APPROVED WITH OBSERVATIONS
  (ADR SKIP — AR-11)
        ↓
Architecture Freeze  ← APPROVED (decision Freeze)
        ↓
Domain Contracts  ← APPROVED
        ↓
Data Model  ← N/A — CERTIFIED
        ↓
Implementation Plan  ← ACCEPTED
        ↓
Pre-P1 baseline  ← COMPLETE (7485)
        ↓
Implementation (C1–C14; Macros A–E)
  Macro A / P1  ← COMPLETE (C1–C2; Checkpoint A ready)
  Macro B / P2  ← COMPLETE (C3–C5; ownership matrix + asked_question_ids)
  Macro B / P3  ← COMPLETE (C6–C7; progress + current_reasoning_decision deleted)
  (Checkpoint A → B → C → D → E → CAR …)
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

### Governance / process (existing)

- `docs/master-plan/ARC-01-ARCHITECTURE-CONSTITUTION.md`
- `docs/master-plan/V13-DEVELOPMENT-PLAYBOOK.md` Version 1.0
- `docs/master-plan/V13-PRODUCT-MASTER-PLAN.md` §2 P-10; §4 EPIC-V13-10; §5 Go-Live Architecture items; §8 Phase 5; §10 DoD item 9
- `docs/master-plan/V1.2-PATTERN-FREEZE.md` (PAT-01…PAT-06)
- `docs/master-plan/ARCHITECTURE-GUIDE.md` §8 OP-01…OP-06
- `docs/master-plan/V1.2-ARCHITECTURE-RETROSPECTIVE.md` (emerging pattern source)
- `docs/technical-debt-register.md` (incl. `TD-EP08-001`)
- Prior epic close / freeze carry-forwards referencing EPIC-10 (EPIC-08 AR-16 / OI-04; EPIC-09 NG-06)

### Runtime / state (existing)

- `InterviewState` and current field surface
- LangGraph node / sole-writer declarations already present in codebase and prior epic freezes
- Service call graph surfaces relevant to PAT-06 corollary

### Deprecation / dead code / tests (existing)

- Existing `deprecated` annotations and related artifacts
- V1.2 migration scaffolding / dead test infrastructure still present
- Deploy / build artifact composition paths (dead-code purity target from EPIC-08)

### Pattern / reconstruction artifacts (existing)

- Existing Reconstruction Completeness matrices / audits from prior epics (e.g. EPIC-03)
- Registered PAT / OP documentation surfaces listed above

### Regression baseline (existing)

- EPIC-09 close-out: 7485 passed / 0 failed

---

## 12. Architecture Assumptions Register

Initial register for Discovery to verify. Status values follow Playbook: `UNVERIFIED` → `VERIFIED` / `INVALIDATED`.

| ID | Description | Status | Verification Document | Notes |
|---|---|---|---|---|
| AA-01 | Full Phase 5 audit can close without introducing new product features. | VERIFIED | `EPIC-10-ARCHITECTURE-DISCOVERY.md` §10 | |
| AA-02 | Domain Contracts / Data Model required only if ownership or stored-shape changes proven necessary. | VERIFIED (conditional) | Discovery §9–§10 | Final necessity → Review ARD-07 |
| AA-03 | Existing ARC-01 + PAT-01…06 + OP-* are sufficient starting inputs for registry reconciliation. | VERIFIED | Discovery §3 / §10 | Unification action → Review |
| AA-04 | EPIC-V13-01 closure removed scoring-residue blockers that prevent audit start. | VERIFIED | Discovery §10 | Residue services remain cleanup scope |
| AA-05 | `TD-EP08-001` deploy-artifact dead-code purity is in EPIC-10 scope. | VERIFIED | Discovery §5.4 / §10 | |
| AA-06 | Phase 1 governance does not by itself satisfy Phase 5 full-audit close. | VERIFIED | Discovery §3 / §10 | |
| AA-07 | Reconstruction Completeness enforcement can build on prior epic evidence without reopening closed feature epics. | VERIFIED | Discovery §10 | P-08 vs PAT naming → Review |
| AA-08 | Master Plan “five new PATs” = OP-01…04 + P-08 (not five new Pattern Freeze IDs). | VERIFIED | Discovery §3.2 | |
| AA-09 | No open confirmed live PAT-06 corollary violation documented today. | VERIFIED | Discovery §6.3 | Suspects remain |
| AA-10 | Complete OP-04 ownership matrix does not exist for all 45 fields. | VERIFIED | Discovery §4 | |

---

## 13. Risks Requiring Architecture Discovery

| ID | Discovery question |
|---|---|
| D-01 | What is the authoritative inventory of original six PATs vs five new PATs vs OP-* guide entries? |
| D-02 | Which `InterviewState` fields lack declared sole writer / readers, and does fixing that change contracts? |
| D-03 | What is the complete `deprecated` and dead-code inventory (code + tests + deploy artifact)? |
| D-04 | Where is PAT-06 corollary currently violated, if at all? |
| D-05 | What remains from Phase 1 governance vs what must still close in Phase 5? |
| D-06 | Are Domain Contracts / Data Model mandatory for this epic, or N/A after inventory? |
| D-07 | Which architectural tests already enforce PATs / ownership, and which gaps remain? |

---

## 14. Initialization Outcome

| Item | Result |
|---|---|
| Epic initialized | **YES** |
| Living Overview created | **YES** — this document |
| Architecture Discovery | **COMPLETE** — `EPIC-10-ARCHITECTURE-DISCOVERY.md` |
| Architecture Review | **APPROVED WITH OBSERVATIONS** — `EPIC-10-ARCHITECTURE-REVIEW.md` |
| Architecture Freeze | **APPROVED** — `EPIC-10-ARCHITECTURE-FREEZE.md` |
| Formal ADR | **SKIP** (AR-11) |
| Domain Contracts | **APPROVED** — `EPIC-10-DOMAIN-CONTRACTS.md` |
| Data Model | **N/A — CERTIFIED** |
| Implementation Plan | **ACCEPTED** — `EPIC-10-IMPLEMENTATION-PLAN.md` |
| Pre-P1 baseline | **COMPLETE** — 7485 passed / 0 failed |
| Macro A / P1 (C1–C2) | **COMPLETE** — INDEX OP registry; OP-02 hygiene; AT-04/AT-05 green |
| Checkpoint A | **PASSED** — Macro B authorized |
| Macro B / P2 (C3–C5) | **COMPLETE** — Ownership matrix JSON; AT-01; asked_question_ids aligned |
| Macro B / P3 (C6–C7) | **COMPLETE** — `progress` + `current_reasoning_decision` deleted; matrix 43/43 |
| Checkpoint B | **READY** — AT-01 green; deleted fields absent; asked_question_ids aligned |
| Implementation | **IN PROGRESS** — next: Macro C / P4 (C8) |

**Next planned activity:** Macro C / **P4** — Delete stubs & scaffolding (C8–C10) per Implementation Plan.
