# EPIC-10 — Implementation Plan

**Status:** ACCEPTED — Implementation COMPLETE (C1–C14); Checkpoint E PASSED; CAR COMPLETE — PASS WITH OBSERVATIONS; Final Review AUTHORIZED  

**Date:** 2026-07-21  
**Epic ID:** EPIC-V13-10  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-10; Product Goal P-10  
**Governing Freeze:** `EPIC-10-ARCHITECTURE-FREEZE.md` (APPROVED)  
**Governing Contracts:** `EPIC-10-DOMAIN-CONTRACTS.md` (APPROVED)  
**ADR required:** NO (AR-11)  
**Data Model:** N/A — CERTIFIED (Contracts §8)  
**Playbook:** V13 Development Playbook Version 1.0 (§2 Implementation Dependency Validation; §8.6 DoD)

**Disambiguation:** Not PRD EPIC-10 (Progress Tracking).

---

## 1. Preflight

| Item | Value |
|---|---|
| HEAD (plan base) | `d39c70cc` — docs(epic-10): approve InterviewState Ownership Matrix contracts |
| Architecture Freeze | APPROVED |
| Domain Contracts | APPROVED |
| Data Model | N/A — CERTIFIED |
| Formal ADR | SKIP |
| Regression baseline (planning) | EPIC-09 close-out **7485** passed / 0 failed — **reconfirm at Pre-P1** |
| Pre-P1 gate | Record EPIC-10 implementation baseline in Overview before C1 |
| Scope | Cleanup / governance / arch tests only — **no** features, **no** performance work |

---

## 2. Planning assumptions

| ID | Assumption | Anchor |
|---|---|---|
| PA-01 | No InterviewState redesign; Ownership Matrix documents authorized sets only | AR-03; OWN-04; Contracts I-OM-06 |
| PA-02 | `dimension_signals` KEEP; `progress` + `current_reasoning_decision` DELETE | Contracts §5 |
| PA-03 | No CandidateProfile dual-model / rename | AR-08; CLN-08 |
| PA-04 | Dual PAT/OP namespaces; no OP→PAT renumber | AR-01; REG-01…03 |
| PA-05 | P-08 stays principle; INDEX cross-link only | AR-02; REG-04 |
| PA-06 | Data Model remains N/A unless durable shape discovered → stop | AR-07; IC-11 |
| PA-07 | `.dockerignore` globs are plan wiring (AR-14), not architecture | §3 |
| PA-08 | Category B CAR includes Architecture Traceability Review | IC-09 |
| PA-09 | Zero Known Failing Tests every commit | IC-08 |

---

## 3. AR-14 wiring (non-architectural)

| Concern | Plan choice |
|---|---|
| Ownership matrix machine artifact | `docs/master-plan/epics/EPIC-10-OWNERSHIP-MATRIX.json` (or equivalent under `tests/domain/contracts/interview_state/`) generated/kept in sync with Contracts §4 — consumed by AT-01 |
| AT-01 test path | `tests/domain/contracts/interview_state/test_epic10_ownership_matrix.py` (extend existing sole-writer suite as needed) |
| AT-03 allowlist path | `tests/infrastructure/architecture/test_epic10_pat06_corollary.py` + allowlist module under `tests/infrastructure/architecture/` |
| AT-02 / AT-05 / AT-07 tests | `tests/infrastructure/architecture/test_epic10_cleanup_architecture.py` |
| `.dockerignore` globs (minimum) | `tests/` (except if runtime needs — **exclude tests from image**); `.git/`; `docs/` (optional keep README only); `data/` local; `*.md` non-runtime; `__pycache__/`; `.venv/`; `htmlcov/`; `.pytest_cache/`; `gradio_app.py` (defense after delete) |
| INDEX Official Patterns section | Amend `docs/master-plan/INDEX.md` — list OP-01…06 + P-08 cross-link; note “five new PATs” = OP-01…04 + P-08 |
| Projection mislabel fix | Replace `PAT-04`→`OP-02` in `domain/contracts/report/scoring_*.py` + ADR-033 / EPIC-01 contracts comments only |
| `asked_question_ids` alignment | In adaptive_navigation_node NEXT path, also append top-level `state.asked_question_ids` (Contracts §4.3) — ownership enforcement |
| TD residual | Register CandidateProfile `dimension_scores` dual-model as TD if absent |
| Baseline report / perf | **Out of scope** |

---

## 4. Governing constraints (non-negotiable)

- Trace every change to Freeze AR / REG / OWN / CLN / AT / IC + Contracts EC-* / I-OM-*.
- No new architecture beyond Freeze + Contracts.
- No feature or performance work.
- Zero Known Failing Tests at every commit and phase end.
- If durable shape impact appears → **stop** (IC-11).
- Category B: CAR must include Architecture Traceability Review.

---

## 5. Work breakdown structure

| WBS | Work package | Freeze / Contracts |
|---|---|---|
| W1 | INDEX Official Patterns + Master Plan wording note | AR-01, AR-02, REG-*, AT-04 |
| W2 | Projection PAT-04 → OP-02 hygiene | AR-09, AT-05 |
| W3 | Ownership matrix artifact + AT-01 tests | AR-03, AR-10, EC-IS-01, AT-01 |
| W4 | `asked_question_ids` write alignment | Contracts §4.3, OWN-*, AT-01 |
| W5 | Delete `progress` + caller fixes | EC-DEL-01, CLN-03, AT-01 |
| W6 | Delete `current_reasoning_decision` + reasoner cleanup | EC-DEL-01, CLN-03, AT-01 |
| W7 | Delete `gradio_app.py` + EvaluationBridgeDetector (+ tests) | CLN-01/02, AT-02 |
| W8 | Retire obsolete MIG/TCP scaffolding tests | CLN-04 |
| W9 | PAT-06 corollary allowlist + scan (AT-03) | AR-05, AT-03 |
| W10 | `.dockerignore` + deploy purity AT-07 | AR-06, AT-07, TD-EP08-001 |
| W11 | Docs pass (MP `report_output`, TD register, Overview) | CLN-07, O-01, O-04 |
| W12 | P-08 regression confirmation (AT-06) + full suite | AT-06; IC-08 |
| W13 | Category B Traceability checklist for CAR | IC-09; Contracts §9 |

---

## 6. Macro structure

| Macro | Phases | Checkpoint | Exit criteria |
|---|---|---|---|
| **A — Governance** | P1 | Checkpoint A after P1 | INDEX OP section + OP-02 hygiene green; AT-04/AT-05 tests pass |
| **B — Ownership & state cleanup** | P2, P3 | Checkpoint B after P3 | AT-01 green; `progress` + `current_reasoning_decision` gone; asked_question_ids aligned |
| **C — Dead code & scaffolding** | P4 | Checkpoint C after P4 | AT-02 green; stubs/scaffolding removed |
| **D — PAT-06 & deploy purity** | P5 | Checkpoint D after P5 | AT-03 + AT-07 green; `.dockerignore` present |
| **E — Certification** | P6, P7 | Checkpoint E after P7 | AT-06 green; full regression ≥ baseline; docs updated; CAR authorized |

---

## 7. Phases and atomic commits

### Pre-P1 — Baseline

| Commit | Work | Test gate | Docs | Depends |
|---|---|---|---|---|
| **Pre-P1** | Full regression; record baseline in Overview | Suite green; count ≥ planning baseline or re-baseline documented | Overview baseline fields | — |

### P1 — Governance (Macro A)

| ID | Commit | Freeze map | Files (indicative) | Test gate | Docs |
|---|---|---|---|---|---|
| **C1** | INDEX Official Patterns + five-new wording | AR-01, AR-02, REG-01…05, AT-04 | `docs/master-plan/INDEX.md` | AT-04 test (may land with C1 or C2) | INDEX |
| **C2** | AT-04/AT-05 arch tests + Projection→OP-02 comment fixes | AR-09, AT-04, AT-05 | `domain/contracts/report/scoring_*.py`; comment fixes in ADR/docs as needed; `tests/infrastructure/architecture/test_epic10_cleanup_architecture.py` (partial) | AT-04, AT-05 green | ADR-033 comment only if touched |

**Checkpoint A:** INDEX lists OP-01…06 + P-08; no Projection-as-PAT-04 in `domain/contracts/report`; AT-04/AT-05 green.

### P2 — Ownership enforcement (Macro B)

| ID | Commit | Freeze map | Files (indicative) | Test gate | Docs |
|---|---|---|---|---|---|
| **C3** | Ownership matrix machine artifact from Contracts §4 | AR-03, EC-IS-01, AT-01 | matrix JSON/YAML under tests or docs | Unit: matrix covers 45 fields | Optional sync note in Contracts if path chosen |
| **C4** | AT-01 ownership coverage + writer-presence tests | AR-10, AT-01, I-OM-* | `tests/domain/contracts/interview_state/test_epic10_ownership_matrix.py` | AT-01 green (may fail until C5 for asked_question_ids — **bridge**: C4 asserts matrix completeness first; writer alignment in C5) | — |
| **C5** | Align `asked_question_ids` top-level writes in adaptive_navigation_node | Contracts §4.3 | `app/graph/nodes/adaptive_navigation_node.py` + focused tests | AT-01 writer checks for field pass; node unit tests | — |

### P3 — State field deletions (Macro B)

| ID | Commit | Freeze map | Files (indicative) | Test gate | Docs |
|---|---|---|---|---|---|
| **C6** | Delete `InterviewState.progress` + fix mapper/validation/tests | EC-DEL-01, CLN-03 | `base.py`, factory, `interview_state_mapper.py`, tests | Targeted + AT-01; no references to state.progress | MP go-live checkbox if lists progress |
| **C7** | Delete `current_reasoning_decision` + reasoner cleanup + tests | EC-DEL-01, CLN-03 | `base.py`, `reasoner_node.py`, tests | Targeted + AT-01 | — |

**Checkpoint B:** AT-01 green for remaining fields; deleted fields absent; asked_question_ids contract satisfied; suite green for touched modules.

### P4 — Dead stubs & scaffolding (Macro C)

| ID | Commit | Freeze map | Files (indicative) | Test gate | Docs |
|---|---|---|---|---|---|
| **C8** | Delete `gradio_app.py` + references | CLN-01, AT-02 | `gradio_app.py`; OPERATIONAL_PROJECT_STATUS / refs | AT-02 partial | Status docs |
| **C9** | Delete EvaluationBridgeDetector + dedicated tests | CLN-02, AT-02 | detector module + `test_evaluation_bridge_detector.py`; registry already clean | AT-02 green | INDEX debt notes if any |
| **C10** | Retire obsolete MIG/TCP transitional scaffolding tests only | CLN-04 | Selected `tests/domain/profile/test_*MIG*` / TCP dual-path tests proven obsolete | Full targeted suite green; **do not** remove live invariant tests | — |

**Checkpoint C:** AT-02 green; stubs gone; scaffolding retired per CLN-04.

### P5 — PAT-06 & deploy purity (Macro D)

| ID | Commit | Freeze map | Files (indicative) | Test gate | Docs |
|---|---|---|---|---|---|
| **C11** | PAT-06 corollary allowlist + scan test | AR-05, AT-03 | `test_epic10_pat06_corollary.py` + allowlist | AT-03 green | Allowlist comment cites AR-05 classes |
| **C12** | Add `.dockerignore` + AT-07 deploy purity test | AR-06, AT-07, TD-EP08-001 | `.dockerignore`; AT-07 assertions | AT-07 green | Close `TD-EP08-001` in technical-debt-register |

**Checkpoint D:** AT-03 + AT-07 green; `TD-EP08-001` CLOSED.

### P6 — Documentation certification (Macro E)

| ID | Commit | Freeze map | Files (indicative) | Test gate | Docs |
|---|---|---|---|---|---|
| **C13** | Docs pass: MP `report_output` wording; TD dual-model; Overview progress | CLN-07, O-01, O-04, W11 | `V13-PRODUCT-MASTER-PLAN.md`; `technical-debt-register.md`; Overview | Docs-only / AT still green | As listed |

### P7 — Full regression & CAR readiness (Macro E)

| ID | Commit | Freeze map | Files (indicative) | Test gate | Docs |
|---|---|---|---|---|---|
| **C14** | Confirm AT-06 (existing P-08 tests) + full regression certification | AT-06, IC-08, W12–W13 | — (run suite); Overview checklist | Full suite ≥ Pre-P1 baseline; AT-01…07 all green | Overview: Checkpoint E / CAR authorized |

**Checkpoint E:** All AT-* green; regression certified; Category B Traceability checklist complete in Overview → authorize CAR.

---

## 8. Checkpoints (summary)

| Checkpoint | After | Must hold |
|---|---|---|
| **A** | P1 / C2 | Governance registry + OP-02 hygiene; AT-04, AT-05 |
| **B** | P3 / C7 | Ownership + state deletes; AT-01 |
| **C** | P4 / C10 | Stub/scaffold cleanup; AT-02 |
| **D** | P5 / C12 | PAT-06 + deploy purity; AT-03, AT-07; TD-EP08-001 closed |
| **E** | P7 / C14 | AT-06 + full regression; CAR authorized |

---

## 9. Mandatory architecture-test gates (binding)

| Gate | Delivered by | CAR blocker |
|---|---|---|
| AT-01 Ownership Matrix coverage | C3–C7 | **Yes** |
| AT-02 Deleted stubs absent | C8–C9 | **Yes** |
| AT-03 PAT-06 corollary scan | C11 | **Yes** |
| AT-04 INDEX OP + P-08 | C1–C2 | **Yes** |
| AT-05 No Projection-as-PAT-04 in report contracts | C2 | **Yes** |
| AT-06 P-08 reconstruction tests green | C14 (confirm) | **Yes** |
| AT-07 Deploy purity + `.dockerignore` | C12 | **Yes** |

---

## 10. Implementation Dependency Validation (§2)

| Check | Result |
|---|---|
| Every commit independently implementable with test gate | **PASS** — C1…C14 each has gate |
| No circular dependencies | **PASS** — linear Pre-P1→C14; C4 completeness before C5 alignment before C6/C7 deletes |
| Bridge for AT-01 | **PASS** — C4 matrix completeness; C5 writer alignment; C6/C7 deletions update matrix |
| Regression baseline declared | **PASS** — 7485 planning; reconfirm Pre-P1 |
| Phase breakdown matches Freeze scope | **PASS** — W1–W13 ⊆ AR/CLN/AT only |
| Contracts / Data Model gates | **PASS** — Contracts APPROVED; Data Model N/A |
| Zero feature / performance scope creep | **PASS** — PA-01, PA-03, §1 |

---

## 11. Traceability summary (Category B)

| Requirement | Plan commits | Verification |
|---|---|---|
| Dual PAT/OP + five-new wording | C1, C2 | AT-04 |
| P-08 identity | C1, C14 | AT-04, AT-06 |
| Ownership Matrix 45 fields | C3–C7 | AT-01 |
| `candidate_profile_v2` ownership only | C3–C4 (matrix row) | AT-01; CAR scope check |
| Delete `progress` / `current_reasoning_decision` | C6, C7 | AT-01 + unit |
| Keep `dimension_signals` | C3–C4 (matrix) | AT-01 |
| Delete stubs | C8, C9 | AT-02 |
| MIG scaffolding retire | C10 | Targeted suite |
| PAT-06 corollary | C11 | AT-03 |
| Deploy purity / TD-EP08-001 | C12 | AT-07 |
| OP-02 hygiene | C2 | AT-05 |
| Docs `report_output` | C13 | Doc review |
| Category B Traceability Review | C14 + CAR | IC-09 |

Full field-level Traceability remains in `EPIC-10-DOMAIN-CONTRACTS.md` §9; this plan maps requirements → commits → AT gates.

---

## 12. Documentation updates by phase

| Phase | Docs |
|---|---|
| Pre-P1 | Overview: implementation baseline |
| P1 | INDEX Official Patterns; AT-04/05 test module |
| P2–P3 | Overview progress; matrix artifact path if externalized |
| P4 | OPERATIONAL / INDEX debt notes; AT-02 |
| P5 | `technical-debt-register.md` close TD-EP08-001 |
| P6 | Master Plan go-live `report_output`; TD dual-model; Overview |
| P7 | Overview Checkpoint E / CAR authorized; regression counts |

---

## 13. Out of scope (rejected if proposed)

- CandidateProfile rename / `dimension_scores` removal
- Multi-writer cluster redesign
- New features / UX / performance work
- SessionHistory durable store
- New ADR (unless Stopping Rule)
- OP renumber as PAT-07+

---

## 14. Plan acceptance

| Criterion | Status |
|---|---|
| Freeze APPROVED | **Yes** |
| Domain Contracts APPROVED | **Yes** |
| Data Model N/A certified | **Yes** |
| Commit boundaries + Dependency Validation | **Yes** (§10) |
| AT-01…07 mapped | **Yes** (§9) |
| Category B Traceability mapped | **Yes** (§11) |
| Docs per phase | **Yes** (§12) |
| No feature/perf scope | **Yes** |

**Implementation Plan: ACCEPTED.**

**Next:** Pre-P1 baseline → C1.

**Stop after Implementation Plan.**
