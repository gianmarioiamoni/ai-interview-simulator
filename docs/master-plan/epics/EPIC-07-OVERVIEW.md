# EPIC-07 — Production UX

**Status:** CLOSED  
**Date:** 2026-07-17  
**Epic ID:** EPIC-V13-07  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-07; Product Goal P-07  
**Roadmap Phase:** Phase 4 — Production Readiness  
**Precondition:** EPIC-V13-04 CLOSED; EPIC-V13-05 CLOSED; Master Plan Dependencies for EPIC-V13-07 satisfied; working tree clean at initialization.  
**Regression baseline (initialization):** 6708 / 0 (EPIC-06 init).  
**EPIC-07 implementation baseline (pre-P1):** 6787 passing / 0 failures.  
**Regression (close-out):** 7003 passing / 0 failures.  
**Planning:** COMPLETE  
**Implementation:** COMPLETE (P1–P7; C1–C15)  
**Construction Architecture Review (CAR):** COMPLETE — PASS WITH MINOR OBSERVATIONS (Architecture Traceability; 0 P0/P1)  
**Final Review (FR):** APPROVED — 2026-07-17  
**Epic Close:** CLOSED — 2026-07-17  
**Architecture Discovery:** `EPIC-07-PRODUCTION-UX.md` — COMPLETE  
**Architecture Review:** `EPIC-07-ARCHITECTURE-REVIEW.md` — COMPLETE  
**Domain Contracts:** `EPIC-07-DOMAIN-CONTRACTS.md` — COMPLETE  
**Data Model:** `EPIC-07-DATA-MODEL.md` — COMPLETE  
**Architecture Freeze:** `EPIC-07-ARCHITECTURE-FREEZE.md` — **APPROVED**  
**Implementation Plan:** `EPIC-07-IMPLEMENTATION-PLAN.md` — **ACCEPTED**; EPIC CLOSED  
**Formal §8.4 ADR:** **SKIP** (Freeze §2)  
**Playbook:** V13 Development Playbook Version 1.0

---

## 1. EPIC Identification

| Field | Value |
|---|---|
| **Identifier** | EPIC-V13-07 |
| **Title** | Production UX |
| **Master Plan reference** | `V13-PRODUCT-MASTER-PLAN.md` §4 EPIC-V13-07; Product Goal **P-07** |
| **Category** | **Category B** — Major Architectural Epic |
| **Phase** | Phase 4 — Production Readiness |
| **Category rationale** | UI-bearing epic that may substantially change report and replay presentation surfaces (error boundaries, accessibility, loading/error affordances). Prefer Category B over Category A to avoid Playbook misclassification violation. Discovery confirms whether new contracts are required. |

---

## 2. Business Objective

Bring every candidate-facing flow to production quality: no placeholder states, no error surfaces that expose internal state, no unhandled loading regressions. A candidate who has never used the platform can complete a session, receive a report, and navigate replay without encountering unfinished or internal-feeling states.

---

## 3. Architectural Objective

Harden existing candidate-facing presentation surfaces across session configuration, question presentation, code-execution feedback, report delivery, replay navigation, and progress view — while preserving frozen runtime/projection boundaries, sole-writer rules, and LLM-free UI constraints already established by prior epics.

Concrete presentation mechanisms, ownership solutions, and component-level designs are intentionally left unresolved and will be determined during Architecture Discovery.

---

## 4. Dependencies

### Master Plan dependencies (blocking)

| EPIC | Status | Dependency |
|---|---|---|
| EPIC-V13-04 | CLOSED | Replay UI feature-complete — polish target |
| EPIC-V13-05 | CLOSED | Unified Report feature-complete — polish / accessibility target |

### Inherited context (not Master Plan dependencies for this epic)

| EPIC | Status | Notes |
|---|---|---|
| EPIC-V13-01 | CLOSED | `Report` authority |
| EPIC-V13-02 | CLOSED | Progress / longitudinal surfaces |
| EPIC-V13-03 | CLOSED | Replay engine / `ReplaySession` |
| EPIC-V13-06 | NOT CLOSED in living Overview | Explainability implementation commits present; CAR / FR / Epic Close markers absent from `EPIC-06-OVERVIEW.md`. Not listed as EPIC-07 Master Plan dependency. See Open Issues. |

### Prerequisites (Definition of Ready — Master Plan dependency subset)

- [x] EPIC-V13-04 CLOSED
- [x] EPIC-V13-05 CLOSED
- [x] Master Plan epic definition unambiguous (scope, outcome, non-goals)
- [x] Phase-3-complete sequencing vs explicit Dependencies — inconsistency classified (DOC-I-01); explicit EPIC-07 Dependencies govern
- [x] No open P0/P1 from prior epics affecting polish targets — verified during Architecture Discovery / Freeze (AA-13)
- [x] Sole writer for any `InterviewState` field this epic may touch — none introduced (AR-03); verified at Freeze / CAR

---

## 5. Expected Deliverables

- Living `EPIC-07-OVERVIEW.md` (this document — workflow status)
- Category B planning set (Discovery → Contracts → Data Model → conditional ADR → Freeze → Implementation Plan) — **COMPLETE**
- Production-quality polish across Master Plan in-scope flows — **COMPLETE** (C1–C15):
  - Session configuration (role, seniority, language mode)
  - Question presentation (written, coding, SQL)
  - Code execution feedback (candidate-friendly test / syntax / runtime errors)
  - Report delivery flow (no loading regressions on deterministic data)
  - Replay navigation
  - Progress view
- Error boundary completeness at every async boundary (candidate-facing fallback) — **COMPLETE**
- Accessibility baseline: keyboard navigation for primary flows; WCAG 2.1 AA target for report and replay — **COMPLETE** (verification artefacts per AR-14)
- Behavioral + architectural tests as required by frozen Implementation Plan — **COMPLETE**
- CAR (with Architecture Traceability) — **COMPLETE**
- Regression — **COMPLETE** (7003 / 0)
- Documentation Certification (living Overview alignment) — **COMPLETE**
- Final Review (FR) — **APPROVED**
- Epic Close — **CLOSED**

**Non-goals (Master Plan):** Onboarding tours, tooltips, or help overlays; internationalisation (V2); dark mode (V2).

---

## 6. Implementation Risk Assessment

| Risk | Likelihood | Notes |
|---|---|---|
| Scope creep into new product features beyond polish | Medium | Product Before Features; defer to Deferred Features / V2 |
| Accidental dual-read or runtime computation from UI | Medium | Preserve ARC-01 / Runtime First; UI remains projection |
| Accessibility target expands beyond report/replay + primary-flow keyboard | Medium | Bound to Master Plan Go-Live checklist |
| EPIC-06 close-out incomplete while Phase 4 starts | Medium | Explicit EPIC-07 deps are 04/05 only; Phase sequencing inconsistency classified |
| Premature ADR or presentation mechanism locked at Initialization | Medium | Playbook: architecture-neutral Initialization; ADR only if needed after Contracts + Data Model |

---

## 7. Estimated Size

**Large (L)** — cross-cutting UI polish across multiple host surfaces; no new domain pipeline expected at Initialization, but Component Inventory and accessibility/error-boundary coverage are broad.

---

## 8. Candidate ADR Evaluation

| Existing ADR | Relevance | Reuse? |
|---|---|---|
| ADR-003 — State-Driven UI | Session / navigation UI state patterns | **Reuse** |
| ADR-033 — Unified Report | Report presentation sole-source boundary | **Reuse** |
| ADR-037 — Replay Engine / `ReplaySession` | Replay UI consumption boundary | **Reuse** |
| ADR-019 / ADR-035 — Language / session config | Session configuration flow | **Reuse** (as needed) |
| ADR-023 / ADR-025 — Narrative / Coaching | Report explainability fields already projected (EPIC-06 path) | **Reuse** (inspect; do not re-own) |
| ARC-01 — Architecture Constitution | Runtime vs projection; LLM-free UI | **Reuse** |

**Policy application:** Reuse existing ADRs. **Do not author a new ADR at initialization.** Propose a new ADR only if Architecture Discovery → Domain Contracts → Data Model leave a genuine unresolved architectural decision.

**Initialization recommendation:** Conditional ADR step expected to be **skipped unless Discovery proves otherwise**.

---

## 9. Required Planning Documents

| # | Document | Role |
|---|---|---|
| 1 | `docs/master-plan/epics/EPIC-07-OVERVIEW.md` | Living Category B status surface (this document) |
| 2 | `docs/master-plan/epics/EPIC-07-PRODUCTION-UX.md` | Architecture Discovery — COMPLETE |
| 3 | `docs/master-plan/epics/EPIC-07-ARCHITECTURE-REVIEW.md` | Discovery Architecture Review — COMPLETE; ADR count = 0 |
| 4 | `docs/master-plan/epics/EPIC-07-DOMAIN-CONTRACTS.md` | Domain Contracts — COMPLETE |
| 5 | `docs/master-plan/epics/EPIC-07-DATA-MODEL.md` | Data Model — COMPLETE |
| 6 | Formal §8.4 Architecture Review / ADR (conditional) | **SKIP** — Freeze §2 |
| 7 | `docs/master-plan/epics/EPIC-07-ARCHITECTURE-FREEZE.md` | Architecture Freeze — **APPROVED** |
| 8 | `docs/master-plan/epics/EPIC-07-IMPLEMENTATION-PLAN.md` | Implementation Plan — **ACCEPTED**; EPIC CLOSED |

---

## 10. Architecture Workflow

```
EPIC Initialization  ← COMPLETE
        ↓
Architecture Discovery  ← COMPLETE
  → EPIC-07-PRODUCTION-UX.md
        ↓
Discovery Architecture Review  ← COMPLETE
  → EPIC-07-ARCHITECTURE-REVIEW.md  (ADR count = 0)
        ↓
Domain Contracts  ← COMPLETE
  → EPIC-07-DOMAIN-CONTRACTS.md
        ↓
Data Model  ← COMPLETE
  → EPIC-07-DATA-MODEL.md
        ↓
Formal §8.4 Architecture Review / ADR  ← SKIP
        ↓
Architecture Freeze  ← APPROVED
  → EPIC-07-ARCHITECTURE-FREEZE.md
        ↓
Implementation Plan  ← ACCEPTED
  → EPIC-07-IMPLEMENTATION-PLAN.md
        ↓
Macro Phase A (P1–P3 / C1–C6)  ← COMPLETE
        ↓
Architecture Checkpoint A  ← AUTHORIZED Macro B
        ↓
Macro Phase B (P4–P5 / C7–C10)  ← COMPLETE
        ↓
Architecture Checkpoint B  ← AUTHORIZED Macro C
        ↓
Macro Phase C (P6–P7 / C11–C15)  ← COMPLETE
        ↓
Architecture Checkpoint C  ← AUTHORIZED CAR
        ↓
Implementation  ← COMPLETE (P1–P7; C1–C15)
        ↓
CAR (incl. Architecture Traceability)  ← COMPLETE — PASS WITH MINOR OBSERVATIONS
        ↓
Regression  ← COMPLETE (7003 / 0)
        ↓
Documentation Certification  ← COMPLETE (living Overview aligned)
        ↓
Final Review (FR)  ← APPROVED
        ↓
Epic Close  ← CLOSED
```

---

## 11. Implementation Progress

| Macro Phase | Phases | Commits | Status |
|---|---|---|---|
| A — Foundation & async/session | P1, P2, P3 | C1–C6 | **COMPLETE** |
| B — Feedback, report, replay polish | P4, P5 | C7–C10 | **COMPLETE** |
| C — Accessibility, deletion, hardening | P6, P7 | C11–C15 | **COMPLETE** |

| Commit | Phase | Concern | Status |
|---|---|---|---|
| C1 | P1 | Enums + `CandidateFacingError` + catalogs | COMPLETE |
| C2 | P1 | `SurfaceState` + DM-V-SS helpers | COMPLETE |
| C3 | P2 | Emit errors for start / submit / next-or-report | COMPLETE |
| C4 | P2 | Emit errors for export / replay-enter / history-load | COMPLETE |
| C5 | P3 | Language mode setup presentation + validation | COMPLETE |
| C6 | P3 | Session history list READY/EMPTY/ERROR | COMPLETE |
| C7 | P4 | `ExecutionErrorPresentation` projector; traceback ban | COMPLETE |
| C8 | P4 | Question/feedback SurfaceState wiring | COMPLETE |
| C9 | P5 | Report deterministic no-loader + empty catalog | COMPLETE |
| C10 | P5 | Progress + replay empty/error polish | COMPLETE |
| C11 | P6 | Keyboard primary-flow tests (AX-01) | COMPLETE |
| C12 | P6 | Report/replay a11y verification (AX-02…AX-05) | COMPLETE |
| C13 | P7 | Arch test: DELETE_TARGET not imported by live bind | COMPLETE |
| C14 | P7 | Delete DELETE_TARGET modules | COMPLETE |
| C15 | P7 | Hardening arch tests | COMPLETE |

---

## 12. Certification Record

| Gate | Outcome |
|---|---|
| Architecture Checkpoint A | AUTHORIZED Macro B |
| Architecture Checkpoint B | AUTHORIZED Macro C |
| Architecture Checkpoint C | AUTHORIZED CAR |
| Construction Architecture Review (CAR) | **COMPLETE** — PASS WITH MINOR OBSERVATIONS (Architecture Traceability; 0 P0/P1) |
| Regression Certification | **COMPLETE** — 7003 passed / 0 failed |
| Documentation Certification | **COMPLETE** — living Overview aligned with post-CAR state |
| Final Review (FR) | **APPROVED** — 2026-07-17 (APPROVED WITH MINOR OBSERVATIONS) |
| Epic Close | **CLOSED** — 2026-07-17 |

### FR observations (non-blocking; registered)

1. NI-02 — Gradio full browser a11y evidence depth remains structural/automated (acceptable / backlog; `TD-EP07-001`).
2. PROC-I-01 — EPIC-06 living Overview close-out still open (external process; does not reopen EPIC-07).

---

## 13. Known Inputs

Existing artifacts Architecture Discovery is expected to inspect. **No architectural decisions. No analysis. No assumptions.** Historical Initialization inventory — retained unchanged.

### Existing ADRs

- ADR-003 — State-Driven UI
- ADR-019 — LanguageConfig design
- ADR-023 — Narrative intelligence architecture
- ADR-025 — Coaching intelligence architecture
- ADR-033 — Unified Report architecture
- ADR-035 — LanguageProfile runtime lifecycle
- ADR-037 — Replay Engine / `ReplaySession` architecture
- ARC-01 — Architecture Constitution

### Existing domain artifacts

- `Report` / `FinalReportDTO` presentation plane
- `ReplaySession` / replay projection artifacts
- `LongitudinalProfile` / progress-related presentation inputs
- `LanguageProfile` / session configuration artifacts
- Session question / answer / execution-result presentation inputs already consumed by UI hosts

### Existing presentation artifacts

- Session configuration UI host surfaces
- Question presentation UI host surfaces (written, coding, SQL)
- Code execution feedback UI host surfaces
- Unified Report UI host surfaces (EPIC-05; explainability fields as projected by EPIC-06 path)
- Replay UI host surfaces (EPIC-04)
- Progress view UI host surfaces
- Existing error / loading / empty-state presentation surfaces (as currently implemented)

### Existing report / replay planning artifacts

- `EPIC-04-OVERVIEW.md` and frozen EPIC-04 planning set (CLOSED)
- `EPIC-05-OVERVIEW.md` and frozen EPIC-05 planning set (CLOSED)
- EPIC-01 / EPIC-05 notes deferring accessibility hardening to EPIC-V13-07
- `EPIC-06-OVERVIEW.md` and frozen EPIC-06 planning set (inspect for report explainability presentation boundaries; epic close status see Open Issues)

### Existing UI host components (inventory names for Discovery; not redesigned here)

- Report hosts previously inventoried under EPIC-05 / EPIC-06 (report sections, facade, renderer, export)
- Replay hosts previously inventoried under EPIC-04
- Session setup / question / execution / progress Gradio (or successor) view hosts under `app/ui/`
- Async boundary / error-boundary host surfaces as they exist today

---

## 14. Architecture Assumptions Register

Authoritative register: `EPIC-07-PRODUCTION-UX.md` §6 (updated by Architecture Review). Remaining UNVERIFIED must close before Architecture Freeze.

| ID | Status | Anchor |
|---|---|---|
| AA-01, AA-02, AA-03, AA-05, AA-06, AA-07, AA-09, AA-10, AA-11, AA-12, AA-13 | **VERIFIED** | Review + Contracts + Data Model |
| AA-08 | **INVALIDATED** | AR-04 / language mode = ADR-019 session mode |
| AA-04 | **INVALIDATED** | Data Model §11 — a11y = impl verification under frozen AX rows |

---

## 15. Master Plan Inconsistencies (classified — no planning changes proposed)

| ID | Class | Statement | Disposition at Initialization |
|---|---|---|---|
| DOC-I-01 | Documentation sequencing inconsistency | Master Plan §8 Phase 4 opens “after Phase 3 complete” (Phase 3 includes EPIC-V13-06), while EPIC-V13-07 Dependencies list only EPIC-V13-04 and EPIC-V13-05 | Classified. Explicit Dependencies govern Definition of Ready for EPIC-07 start. No Master Plan edit in this step. |
| PROC-I-01 | Process / living-status inconsistency | User context asserts prior epics complete; `EPIC-06-OVERVIEW.md` is not CLOSED (Architecture Review / Freeze / Implementation Plan artifacts exist; implementation commits present; CAR / FR / Epic Close markers absent) | Classified. Does not block EPIC-07 Initialization under explicit Master Plan Dependencies. Recommend EPIC-06 close-out before or in parallel with EPIC-07 Discovery. |

---

## 16. Recommendation

**EPIC-V13-07 is CLOSED.**  
**Next planned activity:** Continue Phase 4 — initialize or advance **EPIC-V13-08 (Deployment & Operations)**; optionally complete EPIC-06 living close-out (PROC-I-01) in parallel if still open.

---

*This Overview is the living status document for EPIC-V13-07. Frozen Discovery / Domain Contracts / Data Model / Architecture Freeze bodies remain historical records. Epic CLOSED.*
