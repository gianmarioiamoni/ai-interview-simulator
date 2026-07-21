# EPIC-09 — Implementation Plan

**Status:** ACCEPTED  
**Date:** 2026-07-20  
**Epic ID:** EPIC-V13-09  
**Playbook Category:** Category A — Standard Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-09; Product Goal P-09  
**Governing Freeze:** `EPIC-09-ARCHITECTURE-FREEZE.md` (APPROVED)  
**ADR required:** NO  
**Domain Contracts / Data Model:** N/A  
**Playbook:** V13 Development Playbook Version 1.0 (§2 Implementation Dependency Validation; §8.6 DoD)

**Disambiguation:** Not PRD EPIC-09 (Interview Replay / session persistence).

---

## 1. Preflight

| Item | Value |
|---|---|
| Working tree at plan authoring | Clean at `d5c1d93` (+ planning docs only for this commit) |
| HEAD (plan base) | `d5c1d93` — docs(epic-08): close Deployment & Operations epic with observations |
| Architecture Freeze | APPROVED |
| Formal ADR | SKIP |
| Domain Contracts / Data Model | N/A (Category A) |
| Regression baseline (planning) | EPIC-08 close-out **7417** passed / 0 failed — **reconfirm at Pre-P1** |
| Pre-P1 gate | Record EPIC-09 implementation baseline in Overview before C1 |

---

## 2. Planning assumptions

| ID | Assumption | Freeze anchor |
|---|---|---|
| PA-01 | No InterviewState / Domain Contracts / Data Model / LangGraph topology / persistence / cache changes | CAT-01–CAT-08; AR-06–08, AR-20–21 |
| PA-02 | Measurement at infra/harness invoke boundary | MEAS-01–MEAS-07; AR-01–AR-02 |
| PA-03 | Reuse EPIC-08 Freeze structured-log schema only | OBS-01–OBS-06; AR-10 |
| PA-04 | SLO-D is N/A V1.3; baseline report must state N/A | AR-05; PRD-03; O-01 |
| PA-05 | Stub-LLM primary for load certification | LOAD-05–LOAD-06; AR-16 |
| PA-06 | P0 only inside existing compute surfaces | AR-14; ARC-01–ARC-03 |
| PA-07 | Exact session shape / degradation threshold are plan wiring (AR-22) | §3 below |
| PA-08 | Category A preserved; no ADR unless Category B stop | AR-20; PRD-05 |

---

## 3. AR-22 wiring (non-architectural)

| Concern | Plan choice |
|---|---|
| Synthetic session shape | **5 written questions** per session (written-heavy; fixed) |
| Load session count | **50** consecutive sessions (LOAD-01) |
| Early / late windows | Sessions **1–10** vs **41–50** |
| Degradation threshold | Late-window SLO-Q P99 and late-window SLO-R **max** must still meet absolute targets (**8s** / **3s**), **and** late/early ratio ≤ **1.25** for those metrics |
| SLO-Q measurement | Wall-clock around written evaluation `graph.invoke` (harness) |
| SLO-R measurement | Contiguous or summed wall-clock `session_close` entry → `report` exit |
| SLO-P measurement | `replay_node` / replay graph invoke on materialized `SessionHistory` (extend EPIC-04 fixture approach; ≥20q fixture retained for SLO-P) |
| Harness location | Tests under `tests/performance/` (+ optional script under `scripts/performance/` for baseline report generation) |
| Optional cycle emit | Infra-only existing Freeze fields (`execution_id`, cycle `event`, `duration_ms`, `session_id`) — no new schema fields |
| Baseline report path | `docs/ops/PERFORMANCE-BASELINE-REPORT.md` |
| Stub LLM | Deterministic fake/stub adapter already used in tests; no live network on primary gate |

---

## 4. Governing constraints (non-negotiable)

- Trace every change to Freeze AR / MEAS / PROF / LOAD / OBS / RPL / PRD / ARC / CAT rules.
- No new architecture beyond Freeze.
- Zero Known Failing Tests at every commit and phase end.
- ARC-01: no compute in projection; no topology/orchestration changes; P-06.
- If P0 appears to require cache/store/state/schema → **stop** (PRD-05).
- Mechanism details in §3 are wiring only — not architectural forks.

---

## 5. Work breakdown structure

| WBS | Work package | Freeze |
|---|---|---|
| W1 | SLO-Q measurement harness + tests | AR-01, AR-02, SLO-Q |
| W2 | Optional infra cycle emit (existing schema) | AR-02, AR-10, OBS-* |
| W3 | SLO-R measurement harness + tests | AR-03, SLO-R |
| W4 | SLO-P measurement harness + tests | AR-04, RPL-*, SLO-P |
| W5 | Reasoner + KnowledgePipeline profiling harness | AR-11, AR-12, PROF-01/02/05 |
| W6 | Longitudinal update profiling harness | AR-12, PROF-03 |
| W7 | 50-session stub-LLM load + degradation gate | AR-15, AR-16, LOAD-* |
| W8 | P0 remediation (conditional) or P0-absent certification | AR-14, AR-17, PRD-01 |
| W9 | Category A / ARC-01 arch constraint tests | CAT-*, ARC-*, O-02 |
| W10 | Performance baseline report artifact | AR-19, PRD-02/03, O-01 |
| W11 | Full regression + epic readiness checklist | PRD-01; close gates |

---

## 6. Implementation phases

### Macro phase map

| Macro | Phases | Checkpoint |
|---|---|---|
| **A — Measurement** | P1, P2, P3 | Checkpoint A after P3 |
| **B — Profiling & load** | P4, P5 | Checkpoint B after P5 |
| **C — Remediation & release artifact** | P6, P7 | Checkpoint C after P7 → CAR |

---

### P1 — Question-cycle measurement (SLO-Q)

**Objective:** Certify written evaluation cycle wall-clock at invoke boundary; P99 target wired in tests.  
**In scope:** Harness for written `graph.invoke` timing; stub LLM; optional Freeze-schema cycle emit (infra-only); unit/integration tests.  
**Out of scope:** Load (P5); report/replay SLOs; P0 remediations; live LLM.  
**Depends on:** Pre-P1 baseline.  
**Freeze:** AR-01, AR-02, AR-09, AR-10, MEAS-01–04, MEAS-07, OBS-*.

---

### P2 — Report generation measurement (SLO-R)

**Objective:** Measure `session_close` → `report` span; assert &lt; 3s under harness conditions.  
**In scope:** Harness spanning close+report only; excludes longitudinal/UI/DTO; tests.  
**Out of scope:** Longitudinal timing (P4); load; DTO mapping.  
**Depends on:** P1 (shared harness utilities OK).  
**Freeze:** AR-03, MEAS-05, SLO-R.

---

### P3 — Replay load measurement (SLO-P)

**Objective:** Measure `replay_node` reconstruction from materialized SessionHistory; &lt; 1s.  
**In scope:** Extend/reuse materialized fixture loader pattern; wall-clock gate; no durable DB.  
**Out of scope:** SessionHistory store; caches.  
**Depends on:** P1 utilities optional.  
**Freeze:** AR-04, RPL-01–05, SLO-P; rejects AR-06/07.

---

### P4 — Profiling (reasoner, KP, longitudinal)

**Objective:** Produce profiling evidence for PROF-01–05 / AR-11–12.  
**In scope:** Harness/timers for reasoner stages + KP per-question; longitudinal_update (+ repo I/O); capture under stubbed sessions; evidence suitable for baseline report.  
**Out of scope:** Topology changes; Freeze-mandatory sub-stage schema fields.  
**Depends on:** Checkpoint A (measurement stable).  
**Freeze:** AR-11, AR-12, PROF-01–05.

---

### P5 — 50-session load & degradation

**Objective:** Primary stub-LLM load certification (LOAD-01–06).  
**In scope:** 50×5-written-question sessions; collect SLO-Q/SLO-R; early vs late degradation ≤1.25 and absolute SLO hold; zero hard failures; optional live-LLM appendix hook (non-gating).  
**Out of scope:** Live-LLM as sole P0 gate; horizontal scale.  
**Depends on:** P1–P4.  
**Freeze:** AR-15, AR-16, LOAD-*, PRD-01; O-03.

---

### P6 — P0 remediation gate

**Objective:** Resolve any in-scope SLO violation under P5 load, or certify none.  
**In scope:** Optimisations **only** in existing compute surfaces (reasoner/KP/close pipelines) or harness/measurement; re-run P5 gates after each remediation commit; stop if Category B pressure.  
**Out of scope:** Caches, persistence, state fields, projection compute, topology.  
**Depends on:** P5 results.  
**Freeze:** AR-14, AR-17, ARC-01–03, PRD-05; rejects AR-07/08/13/21.

**Note:** If P5 is green, P6 is a **certification commit** (document P0-absent) — no speculative remediations.

---

### P7 — Baseline report & hardening

**Objective:** Publish baseline report; enforce Category A / ARC-01 arch tests; full regression.  
**In scope:** `docs/ops/PERFORMANCE-BASELINE-REPORT.md` (methodology, measurements, profiles, load, P0, SLO-D N/A, ARC-01 note); arch tests for CAT/ARC prohibitions; production-readiness checklist; full suite.  
**Out of scope:** EPIC-10; claiming SLO-D met.  
**Depends on:** P1–P6.  
**Freeze:** AR-19, PRD-02/03, CAT-*, O-01/O-02.

---

## 7. Commit plan

Each commit: one logical concern; independently testable; suite green after apply.

| ID | Phase | Objective | Affected components | Expected tests | Acceptance criteria | Architectural constraints | Dependencies |
|---|---|---|---|---|---|---|---|
| **C1** | P1 | SLO-Q harness: written invoke wall-clock + stub LLM | `tests/performance/` (+ shared helpers) | Unit/integration: cycle measured; stub path; P99 helper over sample | SLO-Q measurable per AR-01/02 | MEAS-*; no InterviewState fields | Pre-P1 |
| **C2** | P1 | Optional infra cycle emit via existing Freeze fields | Infra observability helpers only | Unit: emit uses existing schema; no control-flow swallow | OBS-01/03/05; optional emit only | AR-10; rejects new schema/domain models | C1 |
| **C3** | P2 | SLO-R harness: session_close→report span | `tests/performance/` | Integration: span &lt; 3s under stub; excludes longitudinal/DTO | SLO-R measurable per AR-03 | MEAS-05; ARC-01 | C1 |
| **C4** | P3 | SLO-P harness: replay reconstruction on materialized history | `tests/performance/` and/or extend `tests/ui/replay/test_replay_performance.py` | Integration: &lt; 1s; no DB store; no cache | SLO-P per AR-04/RPL-* | Rejects AR-06/07 | C1 |
| **C5** | P4 | Profile reasoner + KP stages under stubbed written cycle | tests/scripts performance profiling | Evidence artifacts / assertions for stage timings | PROF-01/02/05 | AR-11/12; no topology | Checkpoint A |
| **C6** | P4 | Profile longitudinal_update (+ repo I/O) | tests/scripts | Evidence for cross-session cost | PROF-03 | AR-12; no LongitudinalProfile cache | C5 |
| **C7** | P5 | 50-session stub-LLM load runner + absolute SLO asserts | `tests/performance/` load module | Integration/slow: 50 sessions; SLO-Q P99 &lt; 8s; SLO-R &lt; 3s; zero hard failures | LOAD-01/02/04/05 | AR-15/16; stub primary | C3, C4, C6 |
| **C8** | P5 | Early vs late degradation gate (≤1.25 + absolute hold) | Load tests | Assert windows 1–10 vs 41–50 | LOAD-03; §3 threshold | O-03 (live not primary) | C7 |
| **C9** | P6 | P0 remediation **or** P0-absent certification | Existing compute modules **only if needed**; else docs/cert note in plan/Overview | Re-run C7–C8; suite green | PRD-01; no Freeze violation | AR-14/17; PRD-05 stop rule | C8 |
| **C10** | P7 | Arch tests: no store/cache/state/topology/projection-compute drift from EPIC-09 | Arch test modules | Arch green for CAT/ARC prohibitions touched by epic | O-02 enforceable | CAT-*; ARC-* | C9 |
| **C11** | P7 | Performance baseline report + readiness checklist | `docs/ops/PERFORMANCE-BASELINE-REPORT.md`; Overview status | Doc checklist: AR-19 sections + SLO-D N/A | PRD-02/03; O-01 | AR-05/19 | C8–C10 |
| **C12** | P7 | Full regression certification + authorize CAR | Overview/plan status markers | Full suite green ≥ Pre-P1 baseline | Ready for CAR | Zero Known Failing Tests | C11 |

---

## 8. Implementation order (authoritative)

1. Pre-P1: full regression → record EPIC-09 implementation baseline in Overview  
2. P1: C1 → C2  
3. P2: C3  
4. P3: C4  
5. **Checkpoint A** (authorize Macro B)  
6. P4: C5 → C6  
7. P5: C7 → C8  
8. **Checkpoint B** (authorize Macro C)  
9. P6: C9  
10. P7: C10 → C11 → C12  
11. **Checkpoint C** → CAR → Regression → Documentation → FR → Epic Close  

---

## 9. Checkpoints

| Checkpoint | After | Authorize | Pass criteria |
|---|---|---|---|
| **A** | P3 / C4 | Macro B (P4–P5) | SLO-Q/R/P harnesses green; suite green; no Freeze reopen |
| **B** | P5 / C8 | Macro C (P6–P7) | 50-session stub load + degradation green **or** explicit P0 list for C9; suite green |
| **C** | P7 / C12 | CAR | Baseline report present with SLO-D N/A; arch tests green; full regression green; P0 resolved or certified absent |

---

## 10. Dependency validation (Playbook §2)

| Check | Result |
|---|---|
| Every commit depends only on prior commits | **PASS** |
| Every commit has executable test/doc gate | **PASS** |
| No circular dependencies | **PASS** — linear C1…C12 with checkpoints |
| Suite can stay green after each commit | **PASS** — additive harnesses; remediation only if needed |
| C9 conditional remediation | **PASS** — may be cert-only; if code, re-runs C7–C8 |
| Hidden dep: load needs measurement | **Satisfied** — C7 after C3/C4 |
| Hidden dep: report needs load+profile evidence | **Satisfied** — C11 after C8–C10 |

**Validation verdict:** Implementation Dependency Validation **PASSED**.

---

## 11. Dependency graph

```
Pre-P1 baseline
    → C1 → C2
    → C1 → C3
    → C1 → C4
Checkpoint A
    → C5 → C6 → C7 → C8
Checkpoint B
    → C9 → C10 → C11 → C12
Checkpoint C → CAR → … → Epic Close
```

**Optional parallel (same green-suite rules):** C3 ∥ C4 after C1; C2 ∥ C3 after C1. Authoritative order remains §8 if parallel unused.

---

## 12. Acceptance criteria

### Per-commit

See Commit plan table.

### Per-phase

| Phase | Acceptance |
|---|---|
| P1 | SLO-Q measurable at invoke boundary; optional emit schema-safe; suite green |
| P2 | SLO-R span close→report &lt; 3s under harness; suite green |
| P3 | SLO-P replay reconstruct &lt; 1s on materialized history; no store/cache; suite green |
| P4 | Reasoner/KP + longitudinal profiling evidence captured; suite green |
| P5 | 50-session stub load; absolute SLOs + degradation ≤1.25; suite green |
| P6 | P0 resolved within Freeze **or** P0-absent certified; C7–C8 still green |
| P7 | Baseline report complete (incl. SLO-D N/A); arch tests green; full regression green |

### Epic (post-CAR/FR)

- Freeze AO-01–AO-08 satisfied for in-scope SLOs  
- Master Plan P-09 expected outcome (with SLO-D N/A disposition)  
- Category A constraints held  
- Full regression green  

---

## 13. Regression strategy

| Gate | Action |
|---|---|
| Pre-P1 | Full suite → record EPIC-09 implementation baseline |
| End of each commit | Targeted tests + no known failures |
| End of each phase | Full suite green |
| Checkpoint A/B/C | Full suite green + checkpoint acceptance |
| After any C9 code remediation | Re-run C7–C8 + full suite |
| Post-P7 / pre-CAR | Full suite + C10 arch tests |
| Epic close | Full suite green; count ≥ Pre-P1 baseline |

Mark load tests with appropriate pytest markers if slow; CI must still execute them on the certification path defined in C7–C8 (or dedicated job) — detail at implementation, not architecture.

---

## 14. Documentation plan

| When | Document | Update |
|---|---|---|
| This commit | `EPIC-09-IMPLEMENTATION-PLAN.md` | Accepted plan |
| This commit | `EPIC-09-OVERVIEW.md` | Living status: planning complete; Impl Plan accepted |
| This commit | `EPIC-09-ARCHITECTURE-FREEZE.md` | Exit criteria: Impl Plan items checked |
| This commit | `V13-PRODUCT-MASTER-PLAN.md` | EPIC-09 status: Implementation Plan accepted |
| During P6–P7 | Overview | Phase/commit markers; P0 list or P0-absent |
| C11 | `docs/ops/PERFORMANCE-BASELINE-REPORT.md` | Create release artifact |
| CAR / FR / Close | Overview + plan status headers | Gate markers only; do not rewrite frozen Discovery/Review/Freeze bodies |

**Frozen docs (bodies not rewritten for status):** Discovery, Review, Freeze (except Freeze §15 exit checkboxes + status line as needed).

---

## 15. Risk validation

| ID | Plan mitigation |
|---|---|
| R-01/R-02 | C1–C2 harness + optional emit; no state fields |
| R-03/R-04 | C4 materialized only; C11 SLO-D N/A; no store |
| R-05/R-06 | C3 span definition; C5–C6 dual profiling |
| R-07 | C9 stop rule + C10 arch tests |
| R-08/R-13 | C7–C8 stub primary; degradation threshold §3 |
| R-09/R-10/R-14 | C5–C6 + C11 authoritative sources |
| R-11 | C9 close-pipeline only if needed |
| R-12 | AR-18 / proceed |

**Verdict:** No unmitigated P0 plan gap within Freeze.

---

## 16. Final approval

| Item | Status |
|---|---|
| Traces to Freeze AR-01–AR-22 | **Yes** |
| Category A preserved | **Yes** |
| No Domain Contracts / Data Model / ADR | **Yes** |
| Implementation Dependency Validation | **PASSED** |
| Regression baseline protocol | **Declared** (reconfirm Pre-P1) |
| AR-22 wiring only | **Yes** (§3) |
| Rejected decisions reopened | **No** |
| Implementation Plan | **ACCEPTED** |

**Implementation authorized** against `EPIC-09-ARCHITECTURE-FREEZE.md` beginning at Pre-P1 / C1.

---

## 17. Implementation progress

| Gate | Status |
|---|---|
| Pre-P1 baseline | **DONE** — 7417 passed / 0 failed (recorded in Overview) |
| C1 | **DONE** — SLO-Q harness under `tests/performance/` |
| C2 | **DONE** — optional infra cycle emit (`question_cycle_logging`) |
| C3 | **DONE** — SLO-R close→report harness under `tests/performance/` |
| C4 | **DONE** — SLO-P replay reconstruction harness under `tests/performance/` |
| Checkpoint A | **PASSED** — Macro A measurement green; Macro B authorized |
| C5 | **DONE** — reasoner + KP profiling harness (`profiling_reasoner_kp`) |
| C6 | **DONE** — longitudinal_update (+ repo I/O) profiling harness |
| C7 | **DONE** — 50-session stub-LLM load + absolute SLO gates |
| C8 | **DONE** — early vs late degradation gate (≤1.25 + absolute hold) |
| Checkpoint B | **PASSED** — Macro C (P6–P7) authorized |
| C9 | **DONE** — **P0-ABSENT** certified (no compute remediation; C7–C8 re-verified green) |
| Next | **C10** |

---

## 18. Next activity

**C10** — Category A / ARC-01 arch constraint tests (P7).
