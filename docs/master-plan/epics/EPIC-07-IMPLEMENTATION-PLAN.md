# EPIC-07 — Production UX: Implementation Plan

**Status:** IMPLEMENTATION PLAN ACCEPTED  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-07  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Implementation Plan (Playbook §8.6)  
**Precondition:** `EPIC-07-ARCHITECTURE-FREEZE.md` APPROVED; §8.4 ADR SKIP; HEAD `95c1744`; working tree clean  
**Authority:** Phases, commit boundaries, dependency validation, regression strategy, acceptance gates. No architecture changes. No Domain Contracts / Data Model edits. No new ADRs. No production code in this document step.

---

## Save Token (precondition)

| Check | Result |
|---|---|
| Working tree | Clean |
| HEAD | `95c1744` — docs(epic-07): approve Production UX architecture freeze |
| Stash | None |
| Architecture Freeze | APPROVED |
| ADR Gate | SKIP |

---

## 0. Governing Constraints (non-negotiable)

| Constraint | Rule |
|---|---|
| Zero Known Failing Tests | Every commit leaves full regression suite green |
| Frozen architecture | Follow AR-*/EC-*/DM-* only; no opportunistic refactors |
| No new InterviewState fields | AR-03 |
| No new persistent artifacts / nodes | AR-01 |
| FeedbackBundle sole writer unchanged | AR-11; presentation projection only |
| Language mode ≠ UI locale | AR-04 / ADR-019 |
| Progress report-hosted only | AR-05 |
| Sole live host | AR-06 |
| Plan Correction Rule | Sequencing-only fixes → Mini Architecture Freeze; else Freeze Integrity Check |
| Conversation Boundary Optimization | Prefer continue within a macro phase; new chat at macro-phase / checkpoint boundaries if needed |

---

## 1. Regression Baseline

| Item | Value |
|---|---|
| Last recorded baseline | 6708 passing / 0 failures (EPIC-06 initialization; not re-run in EPIC-07 planning) |
| **P0 gate (before P1 code)** | Run full regression suite; record count as **EPIC-07 implementation baseline** in Overview |
| Per-commit gate | Full suite green (or documented equivalent full target used by CI) before commit lands |
| Per-phase gate | Full suite green + phase acceptance checklist |
| Final gate | Full suite green + architectural tests from P7 |

---

## 2. Macro Phase Structure

| Macro Phase | Phases | Architecture Checkpoint |
|---|---|---|
| **A — Foundation & async/session** | P1, P2, P3 | Checkpoint A after P3 |
| **B — Feedback, report, replay polish** | P4, P5 | Checkpoint B after P5 |
| **C — Accessibility, deletion, hardening** | P6, P7 | Checkpoint C after P7 → CAR |

No Macro Phase may start until the preceding Architecture Checkpoint authorizes it.

---

## 3. Implementation Phases (scope)

### P1 — Presentation primitives & catalogs

**Scope:** Implement ephemeral types/enums/catalogs per Data Model §3–§5: `AsyncBoundary`, `SurfacePhase`, `ExecutionErrorKind`, `CandidateFacingError`, message/empty/execution copy catalogs, catalog lookup helpers. Unit tests for DM-V-CF/EX catalog equality and closed enums.  
**Out of scope:** Wiring into handlers/UI; a11y; deletion.  
**Freeze Integrity:** None expected (code only).

### P2 — Async boundary candidate-facing errors

**Scope:** Emit `CandidateFacingError` on all six `AsyncBoundary` values; surface `phase=ERROR` with catalog `message_text`; eliminate silent graph-failure recovery without candidate message (AR-08). Align replay enter with catalog/`ReplayErrorBoundary` consistency (AR-09).  
**Out of scope:** Language mode UI; history loader completeness beyond error path; feedback traceback removal (P4); a11y.  
**Depends on:** P1.

### P3 — Session configuration (language mode) & session history list

**Scope:** `SessionConfigPresentation` / ADR-019 language mode controls (not locale); validators DM-V-SC-*; `SessionHistoryListPresentation` READY/EMPTY/ERROR (forbid silent `None` stub).  
**Out of scope:** Feedback/report/replay polish beyond history→replay `session_id` handoff; deletion.  
**Depends on:** P1, P2 (history ERROR uses EC-CF-01).

### P4 — Execution error presentation & feedback/question surface states

**Scope:** `ExecutionErrorPresentation` (`shows_traceback=False`, catalog messages); question/feedback `SurfaceState` EMPTY/READY/ERROR with frozen empty keys; no placeholder chrome (I-SS-03). **Must not** reassign `FeedbackBundle` writer.  
**Out of scope:** Report deterministic loader rule (P5); a11y; deletion.  
**Depends on:** P1 (P2 not strictly required for EX projection, but P2 recommended prior for shared error rendering helpers — ordered after P2/P3 for shared surface error rendering).

### P5 — Report, progress, replay production-quality surfaces

**Scope:** Report `SurfaceState` I-SS-02 (no LOADING when DTO ready); report/progress/replay empty catalogs; replay empty-label cleanup; progress insufficient-data copy; export already covered by P2 boundary.  
**Out of scope:** A11y audits (P6); module deletion (P7).  
**Depends on:** P1, P2, P4.

### P6 — Accessibility baseline

**Scope:** EC-AX-01 AX-01…AX-05 verification artefacts (keyboard primary flows; report/replay WCAG 2.1 AA target evidence tests/audits as automatable; perceivable error/empty text). No architecture change if Gradio limits appear — record evidence gaps as verification findings, not ADR.  
**Depends on:** P3 (primary setup controls), P5 (report/replay surfaces stable).

### P7 — Unwired host deletion & architectural hardening

**Scope:** Prove live bind path does not import EC-UH-01 modules → delete DELETE_TARGET modules → architectural tests: AsyncBoundary coverage, FeedbackBundle writer invariant, DELETE_TARGET absent, language_mode≠locale sole satisfaction.  
**Depends on:** P1–P6 (no live dependency on deleted modules; verify before delete).  
**Bridge rule:** If any unexpected import appears, fix live path to sole host **before** deletion commit (still green); do not delete while imports remain.

---

## 4. Commit Boundary Table

| Commit | Phase | One logical concern | Depends on | Test gate (executable at boundary) | Green suite |
|---|---|---|---|---|---|
| C1 | P1 | Enums + immutable `CandidateFacingError` + catalog modules | — | Unit: enum closed; catalog key→text; I-CF message equality | Yes |
| C2 | P1 | `SurfaceState` value + DM-V-SS validation helpers | C1 | Unit: ERROR↔error; EMPTY↔empty_copy_key; loader forbidden cases | Yes |
| C3 | P2 | Emit errors for `SESSION_START`, `ANSWER_SUBMIT`, `NEXT_OR_REPORT` | C1–C2 | Unit/integration: each boundary failure yields catalog message; no silent recovery | Yes |
| C4 | P2 | Emit errors for `REPORT_EXPORT`, `REPLAY_ENTER`, `SESSION_HISTORY_LOAD` | C1–C3 | Same as C3 for remaining boundaries; AsyncBoundary 6/6 covered | Yes |
| C5 | P3 | Language mode setup presentation + validation (ADR-019) | C1–C2 | Unit: DM-V-SC-01/02/03; locale-alone insufficient | Yes |
| C6 | P3 | Session history list presentation READY/EMPTY/ERROR | C1–C4 | Unit/integration: silent None forbidden; EMPTY/ERROR catalogs | Yes |
| C7 | P4 | `ExecutionErrorPresentation` projector; traceback ban | C1 | Unit: `shows_traceback=False`; kinds→catalog; no path/exception class | Yes |
| C8 | P4 | Question/feedback surface EMPTY/READY/ERROR wiring | C2, C7 | Unit/UI: empty keys; no placeholder patterns | Yes |
| C9 | P5 | Report deterministic no-loader + report empty copy | C2, C4 | Test: DTO ready ∧ not processing ⇒ phase≠LOADING | Yes |
| C10 | P5 | Progress + replay empty/error polish (catalogs) | C2, C4 | Unit/UI: progress insufficient; replay empty/error catalogs | Yes |
| C11 | P6 | Keyboard primary-flow tests (AX-01) | C5, C8–C10 | Automated keyboard-path tests for primary controls | Yes |
| C12 | P6 | Report/replay a11y verification hooks (AX-02…AX-05) | C9–C10 | A11y tests/audits as automatable; text-not-icon-only | Yes |
| C13 | P7 | Architectural test: DELETE_TARGET not imported by live bind | C5–C12 | Arch test green **before** deletion | Yes |
| C14 | P7 | Delete DELETE_TARGET modules | C13 | Full suite green; imports gone | Yes |
| C15 | P7 | Hardening arch tests (boundaries, FeedbackBundle writer, language mode) | C4, C7, C5, C14 | Arch tests green; full suite green | Yes |

**Commit count:** 15. **No mixed concerns per commit.**

---

## 5. Dependency Graph

```
C1 → C2 → C3 → C4 → C6
                ↓
C1 → C5
C1 → C7 → C8 → C9 → C10 → C11 → C12 → C13 → C14 → C15
         ↘______↗
C4 ─────────────→ C9, C10
C5 ─────────────────────────→ C11
```

**Cycles:** None.  
**Hidden deps check:** History ERROR (C6) needs C4; report/replay polish (C9–C10) need C2+C4; a11y (C11–C12) need stable surfaces (C8–C10) and setup (C5); deletion (C14) needs C13 proof. Feedback projector (C7) does not depend on P2/P3 handlers.

---

## 6. Implementation Order (authoritative)

1. P1: C1 → C2  
2. P2: C3 → C4  
3. P3: C5 → C6  
4. **Checkpoint A** (authorize Macro B)  
5. P4: C7 → C8  
6. P5: C9 → C10  
7. **Checkpoint B** (authorize Macro C)  
8. P6: C11 → C12  
9. P7: C13 → C14 → C15  
10. **Checkpoint C** → CAR (Architecture Traceability) → Regression → Docs → FR → Close  

---

## 7. Implementation Dependency Validation (§2)

| Commit | Independently implementable? | Test gate without future commits? | Circular deps? | Full suite green? |
|---|---|---|---|---|
| C1 | Yes | Yes — catalog/enum unit tests | No | Required |
| C2 | Yes (needs C1 only) | Yes — SurfaceState unit tests | No | Required |
| C3 | Yes (C1–C2) | Yes — three-boundary tests | No | Required |
| C4 | Yes (C1–C3) | Yes — remaining boundary tests | No | Required |
| C5 | Yes (C1–C2) | Yes — SC validation tests | No | Required |
| C6 | Yes (C1–C4) | Yes — history presentation tests | No | Required |
| C7 | Yes (C1) | Yes — EX presentation unit tests | No | Required |
| C8 | Yes (C2, C7) | Yes — surface wiring tests | No | Required |
| C9 | Yes (C2, C4) | Yes — report loader/empty tests | No | Required |
| C10 | Yes (C2, C4) | Yes — progress/replay empty tests | No | Required |
| C11 | Yes (prior surfaces) | Yes — keyboard tests | No | Required |
| C12 | Yes (C9–C10) | Yes — a11y verification tests | No | Required |
| C13 | Yes | Yes — import arch test (no delete yet) | No | Required |
| C14 | Yes (C13 green) | Yes — suite after delete | No | Required |
| C15 | Yes | Yes — hardening arch tests | No | Required |

**Validation result:** PASS — no redesign required.

---

## 8. Parallelization Opportunities

| Opportunity | Allowed? | Constraint |
|---|---|---|
| C5 (language mode) after C2, parallel with C3–C4 | **Limited** | Prefer sequential for single-branch green suite; optional only on isolated worktrees with merge discipline |
| C7 after C1, parallel with C3–C6 | **Limited** | Same — default **sequential C1…C15** |
| C9 ∥ C10 after C4+C2+C8 | **Limited** | Prefer C9 then C10 |
| P6 vs early P7 | **No** | C13 requires P6 surfaces stable |

**Default policy:** Strict sequential commits. Parallelization is optional optimization only; not required for acceptance.

---

## 9. Stopping Rules

Stop implementation and do **not** proceed to the next commit when:

| Trigger | Action |
|---|---|
| Need new `InterviewState` field / persistent artifact / ADR | Full Freeze Integrity Check + possible ADR (AR-03/AR-01) |
| Frozen Contracts/Data Model field change | Freeze Integrity Check before any doc edit |
| Ownership conflict (e.g. FeedbackBundle writer drift) | Stop; RT-02; no silent fix that reassigns writer |
| Commit cannot leave suite green | Redesign commit / bridge; never land red |
| Sequencing-only issue | Mini Architecture Freeze + plan revision note |
| Architectural decision not in Freeze | Stop — reopen planning (not Plan Correction) |

---

## 10. Freeze Integrity Check Checkpoints

| When | Check |
|---|---|
| Before editing any frozen EPIC-07 planning doc | Freeze Integrity Check |
| After Checkpoint A / B / C | Confirm no frozen-doc drift; authorize next macro phase |
| Before CAR | Confirm implementation traceable to Freeze/Contracts/Data Model/Plan |
| Plan Correction (sequencing only) | Mini Architecture Freeze |

---

## 11. Regression Strategy

| Gate | Action |
|---|---|
| Pre-P1 | Full suite → record EPIC-07 baseline |
| Each commit C1–C15 | Full suite green |
| Each phase end | Full suite + phase checklist |
| Each Architecture Checkpoint | Full suite + authorize next macro phase |
| Post-P7 / pre-CAR | Full suite + all P7 arch tests |
| Epic Regression Certification | Full suite vs baseline; 0 failures |

---

## 12. Acceptance Gates

### Per-phase acceptance

| Phase | Gate |
|---|---|
| P1 | Catalogs/types exist; unit tests green; no UI wiring required |
| P2 | All 6 AsyncBoundary failures emit CandidateFacingError; no silent nav/start/submit recovery |
| P3 | Language mode usable per ADR-019; history READY/EMPTY/ERROR |
| P4 | No traceback in feedback presentation; question/feedback empty catalogs |
| P5 | Report no unjustified loader; progress/replay finished empty/error copy |
| P6 | AX-01…AX-05 verification artefacts present and green (or documented automation limits without architecture change) |
| P7 | DELETE_TARGET removed; hardening arch tests green |

### Epic acceptance (after CAR/FR — not this document)

Master Plan R-01…R-15 satisfied per Contracts Traceability; Freeze scope complete.

---

## 13. Implementation Risks

| ID | Risk | Likelihood | Mitigation in plan |
|---|---|---|---|
| IR-01 | Feedback polish touches runtime FeedbackBundle writer | Medium | C7/C15 arch tests; RT-02; presentation-only |
| IR-02 | Language mode control missing in live layout | Medium | C5 explicit; fail tests if locale-only |
| IR-03 | History port incomplete beyond stub | Medium | C6 EMPTY/ERROR contracts; no new persistence |
| IR-04 | Gradio a11y limits | Medium | C11–C12 verification obligation; no ADR (AA-04 response) |
| IR-05 | Unexpected import of DELETE_TARGET | Low | C13 before C14 bridge |
| IR-06 | Scope creep into new features | Medium | Phase isolation; Product Before Features |
| IR-07 | Suite runtime cost per commit | Medium | Acceptable; Zero Known Failing Tests non-negotiable |

---

## 14. Architecture Checkpoint Mandates

| Checkpoint | After | Must verify | Authorizes |
|---|---|---|---|
| **A** | P3 / C6 | P1–P3 scope complete; suite green; no Freeze drift | Macro B (P4–P5) |
| **B** | P5 / C10 | Report/replay/feedback polish complete; suite green | Macro C (P6–P7) |
| **C** | P7 / C15 | Deletion + hardening complete; suite green | CAR |

Intermediate informal reviews do not replace these checkpoints.

---

## 15. First Implementation Phase (P1)

**P1 begins after this plan is accepted and pre-P1 baseline is recorded.**

| Field | Value |
|---|---|
| Phase | **P1 — Presentation primitives & catalogs** |
| First commit | **C1** — Enums + `CandidateFacingError` + catalogs |
| Second commit | **C2** — `SurfaceState` + DM-V-SS helpers |
| Forbidden in P1 | Handler wiring, UI chrome, a11y, deletion, FeedbackBundle changes |

---

## 16. §8.6 Definition of Done Checklist

| Criterion | Status |
|---|---|
| Commit boundary table complete | YES §4 |
| Implementation Dependency Validation applied | YES §7 PASS |
| Every commit independently implementable + test gate | YES |
| No circular dependencies | YES §5 |
| Regression baseline declared | YES §1 |
| Phase breakdown matches Freeze scope | YES §3 |
| No architecture / Contracts / Data Model / ADR changes in this plan | YES |

---

## 17. Recommendation

**EPIC-07 is implementation-ready for production code starting at P1/C1** after: (1) this plan remains ACCEPTED; (2) pre-P1 full regression baseline is recorded.

**Do not start P2 until P1 (C1–C2) is complete and green.**

---

*Living status: `EPIC-07-OVERVIEW.md`. Frozen architecture documents remain unchanged by implementation.*
