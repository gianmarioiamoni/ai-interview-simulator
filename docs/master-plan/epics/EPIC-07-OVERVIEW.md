# EPIC-07 — Production UX

**Status:** INITIALIZATION COMPLETE — Architecture Discovery next  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-07  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-07; Product Goal P-07  
**Roadmap Phase:** Phase 4 — Production Readiness  
**Precondition:** EPIC-V13-04 CLOSED; EPIC-V13-05 CLOSED; Master Plan Dependencies for EPIC-V13-07 satisfied; working tree clean at initialization.  
**Regression baseline (initialization):** Last recorded epic baseline 6708 passing / 0 failures (EPIC-06 initialization); reconfirm at Architecture Discovery — suite not re-run in this planning step.  
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
- [ ] Phase-3-complete sequencing vs explicit Dependencies — inconsistency classified (see Open Issues); does not alter explicit EPIC-07 Dependencies
- [ ] No open P0/P1 from prior epics affecting polish targets — verify during Architecture Discovery
- [ ] Sole writer for any `InterviewState` field this epic may touch — identify during Architecture Discovery (Initialization assumes none until proven otherwise)

---

## 5. Expected Deliverables

- Living `EPIC-07-OVERVIEW.md` (this document — workflow status)
- Category B planning set (Discovery → Contracts → Data Model → conditional ADR → Freeze → Implementation Plan)
- Production-quality polish across Master Plan in-scope flows:
  - Session configuration (role, seniority, language mode)
  - Question presentation (written, coding, SQL)
  - Code execution feedback (candidate-friendly test / syntax / runtime errors)
  - Report delivery flow (no loading regressions on deterministic data)
  - Replay navigation
  - Progress view
- Error boundary completeness at every async boundary (candidate-facing fallback)
- Accessibility baseline: keyboard navigation for primary flows; WCAG 2.1 AA target for report and replay
- Behavioral + architectural tests as required by frozen Implementation Plan
- CAR (with Architecture Traceability), Regression, Documentation Certification, FR, Epic Close

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
| 2 | `docs/master-plan/epics/EPIC-07-PRODUCTION-UX.md` | Architecture Discovery (next) |
| 3 | `docs/master-plan/epics/EPIC-07-DOMAIN-CONTRACTS.md` | Domain Contracts (if Discovery proves contract work) |
| 4 | `docs/master-plan/epics/EPIC-07-DATA-MODEL.md` | Data Model (after Contracts) |
| 5 | Architecture Review / ADR (conditional) | Only if unresolved decision remains |
| 6 | `docs/master-plan/epics/EPIC-07-ARCHITECTURE-FREEZE.md` | Gate authorizing Implementation Plan |
| 7 | `docs/master-plan/epics/EPIC-07-IMPLEMENTATION-PLAN.md` | Phases + commit boundaries + Dependency Validation |

---

## 10. Architecture Workflow

```
EPIC Initialization  ← COMPLETE (this document)
        ↓
Architecture Discovery  ← NEXT
  → EPIC-07-PRODUCTION-UX.md
        ↓
Domain Contracts
        ↓
Data Model
        ↓
Architecture Review / ADR (conditional)
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

## 12. Architecture Assumptions Register

Initialized at Initialization as UNVERIFIED. Architecture Discovery populates verification evidence. All must be VERIFIED (or INVALIDATED with response) before Architecture Freeze.

| ID | Description | Status | Verification Document | Notes |
|---|---|---|---|---|
| AA-01 | EPIC-07 can be delivered without new persistent domain artifacts or new LangGraph nodes | UNVERIFIED | Architecture Discovery | Master Plan describes polish; Discovery confirms |
| AA-02 | Existing frozen ADRs (esp. ADR-003, ADR-033, ADR-037, ARC-01) govern presentation boundaries without modification | UNVERIFIED | Architecture Discovery / Architecture Review | New ADR only if genuine gap remains |
| AA-03 | No new `InterviewState` fields are required for Production UX | UNVERIFIED | Architecture Discovery | Sole-writer identification if any field is touched |
| AA-04 | Report and replay accessibility (WCAG 2.1 AA) and primary-flow keyboard navigation are achievable on existing host surfaces | UNVERIFIED | Architecture Discovery Component Inventory | Bound to Master Plan Go-Live Product checklist |
| AA-05 | Deterministic report/replay data paths already eliminate justified loading spinners; remaining loading/error regressions are presentation-only | UNVERIFIED | Architecture Discovery | No runtime recomputation from UI |
| AA-06 | EPIC-04 and EPIC-05 CLOSED surfaces are the complete polish targets required by Master Plan Dependencies | UNVERIFIED | Architecture Discovery | EPIC-06 not a Master Plan dependency for EPIC-07 |
| AA-07 | Conditional ADR step can be skipped | UNVERIFIED | Architecture Review | Reconfirm after Contracts + Data Model |

---

## 13. Master Plan Inconsistencies (classified — no planning changes proposed)

| ID | Class | Statement | Disposition at Initialization |
|---|---|---|---|
| DOC-I-01 | Documentation sequencing inconsistency | Master Plan §8 Phase 4 opens “after Phase 3 complete” (Phase 3 includes EPIC-V13-06), while EPIC-V13-07 Dependencies list only EPIC-V13-04 and EPIC-V13-05 | Classified. Explicit Dependencies govern Definition of Ready for EPIC-07 start. No Master Plan edit in this step. |
| PROC-I-01 | Process / living-status inconsistency | User context asserts prior epics complete; `EPIC-06-OVERVIEW.md` is not CLOSED (Architecture Review / Freeze / Implementation Plan artifacts exist; implementation commits present; CAR / FR / Epic Close markers absent) | Classified. Does not block EPIC-07 Initialization under explicit Master Plan Dependencies. Recommend EPIC-06 close-out before or in parallel with EPIC-07 Discovery. |

---

## 14. Recommendation

**Next engineering task:** Architecture Discovery for EPIC-V13-07 (`EPIC-07-PRODUCTION-UX.md`), including Component Inventory for all UI-bearing polish surfaces and population of the Architecture Assumptions Register. No Domain Contracts, ADR, Freeze, Implementation Plan, or production code in the next step until Discovery completes.

---

*This Overview is the living status document for EPIC-V13-07. Frozen Discovery / Domain Contracts / Data Model / Architecture Freeze bodies (when authored) remain historical records after freeze.*
