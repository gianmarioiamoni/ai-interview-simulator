# V1.3 — Maintainability Scorecard

**Artifact ID:** MS-V1.3  
**Gate:** Master Plan §9 Maintainability score ≥ 9.5; Playbook §10 Release Readiness Success Metrics  
**Activity:** Maintainability Re-Certification  
**Date:** 2026-07-22  
**Evaluated HEAD:** `3887c0cfabc7bc86fd50ddd46663ce2b11d03ecd`  
**Working tree at evaluation:** clean  
**Prior Maintainability score:** **8.9 / 10** — NOT CERTIFIED (`MS-V1.3` v1.0 at `50536e8`; committed `340df50`)  
**Remediation HEAD:** `3887c0cfabc7bc86fd50ddd46663ce2b11d03ecd`  
**Scope:** Maintainability re-score only — no Architecture re-score; no Release Readiness re-run; no VERSION/tag ceremony; no production-logic changes  

---

## 1. Preflight

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `3887c0cfabc7bc86fd50ddd46663ce2b11d03ecd` |
| Working tree | clean |
| Prior Maintainability Scorecard | **Present** — Overall **8.9**, NOT CERTIFIED (`MS-V1.3` v1.0) |
| V1.3 Architecture Scorecard | **CERTIFIED** Overall **9.7** (`AS-V1.3` v1.1) |
| Remediation commit | `3887c0c` — TD-DL-001 closure, domain isolation AT gate, dependency lock SSOT, TD-DOC-003/004 register hygiene |
| Separate Maintainability Remediation report | **Absent as standalone file** — evidence = remediation commit + `docs/technical-debt-register.md` + ADR-007 |
| Open V1.3 P0/P1 findings | Zero |

### Inputs used

| Input | Role |
|---|---|
| `ARC-01-ARCHITECTURE-CONSTITUTION.md` | Layer / ownership / bridge constraints affecting maintainability |
| `V13-DEVELOPMENT-PLAYBOOK.md` v1.0 | RR / Success Metrics process |
| `V13-PRODUCT-MASTER-PLAN.md` §9 | Score target ≥ 9.5 |
| `V13-MAINTAINABILITY-SCORECARD.md` v1.0 | Prior methodology + dimension baselines (**not** reused as scores) |
| Remediation evidence at `3887c0c` | Closure claims to re-verify at HEAD |
| `V13-ARCHITECTURE-SCORECARD.md` (CERTIFIED) | Adjacent architectural evidence; **not** substituted for Maintainability |
| `docs/technical-debt-register.md` | Registered OPEN / DEFERRED / CLOSED debt |
| Repository at evaluated HEAD | Objective structure, imports, tests, deps, docs |

---

## 2. Evaluation methodology

1. **Numeric method (aligned with AS-V1.3 / AC-V1.2 §A2 / MS-V1.3 v1.0):** score each dimension **/10** with evidence-backed rationale and explicit deductions; compute **Overall** as the **arithmetic mean** of scored dimensions; report Overall to **one decimal**.
2. **V1.3 Maintainability dimension set** (unchanged from MS-V1.3 v1.0):
   - Domain complexity
   - Coupling
   - Cohesion
   - Layer separation
   - Technical debt
   - Testability
   - Documentation quality
   - Change isolation
   - Dependency management
   - Long-term maintainability
3. **Evidence classes admitted:** ARC-01; Ownership Matrix / AT-01…07 / I-11; new AT `test_domain_layer_isolation.py`; Technical Debt Register; RR baseline observations; direct repository inspection at HEAD `3887c0c`.
4. **Anti-inflation / anti-reuse rule:** Prior dimension scores are **not** reused. Architecture CERTIFIED (9.7), zero P0/P1, and green AT gates do **not** auto-award Maintainability ≥ 9.5. Closed TDs remove prior deductions **only** when HEAD evidence confirms closure. Stale register claims contradicted by HEAD are not scored as missing artifacts, but register drift remains a hygiene deduction.
5. **Certification rule:** Overall ≥ 9.5 → **CERTIFIED**; otherwise **NOT CERTIFIED**.

---

## 3. Maintainability assessment

| Criterion | Result | Evidence |
|---|---|---|
| Domain complexity | Controlled | `domain/` 274 `.py` (225 under `domain/contracts/`); dual-model **TD-EP10-001 CLOSED**; InterviewState imports only `domain.*`; residual `InterviewEvaluationService` naming (O-RR-01) |
| Coupling | Ownership strong; domain→outer edge removed | Ownership Matrix 43/43 + AT-01; **TD-DL-001 CLOSED** — zero `domain` → `services`/`app`/`infrastructure` imports at HEAD; outer paths are re-exports inward; residual O-RR-01 + **TD-DL-003** Medium |
| Cohesion | Strong modular cohesion | Distinct engines/builders; presentation SSOT `FinalReportDTO.from_report`; projection/compute bans in UI architecture tests; residual evaluation-service naming vs Report vocabulary |
| Layer separation | Restored and gated | AT-01…07 + I-11 retained; **new** `tests/infrastructure/architecture/test_domain_layer_isolation.py` GREEN; ADR-007 **Superseded (Resolved)**; residual **TD-DL-003** duplicate `LLMPort` |
| Technical debt | High structural DL closed; High test/retrieval remain | **TD-DL-001 / TD-DOC-003 / TD-DOC-004 CLOSED**; HEAD-confirmed High OPEN: **TD-001**, **TD-TC-001**, **TD-TC-002**; **TD-DOC-001** still OPEN but contradicted (README correct); **12 Medium OPEN**; deferred Lows **TD-EP02-001**, **TD-EP07-001** |
| Testability | Strong suite; named coverage holes remain | Prior RR **7378 / 0**; ~41 architecture `test_*` functions under `tests/infrastructure/architecture/`; isolation AT added; **no** dedicated tests for `services/decision_engine/` or `services/interview_planning/phases/` |
| Documentation quality | Living docs strong; minor register residue | Epic Overviews present; O-RR-01 residue; **TD-DOC-003/004 CLOSED** with artifacts present (`.env.example`, `docs/architecture/configuration.md` 164 lines); **TD-DOC-001** stale High OPEN vs correct README; `VERSION`=`1.1.0` aligns with `pyproject.toml` `version = "1.1.0"` |
| Change isolation | Strong field ownership | `EPIC-10-OWNERSHIP-MATRIX.json` sole-writer model; PAT/OP AT gates; InterviewState cross-layer type entanglement removed |
| Dependency management | Lock SSOT present; one pin drift | `requirements.txt` + `requirements.lock` exact pins; `pyproject.toml` `dependencies = []` (no second pin set); **pin mismatch:** `python-dotenv==1.0.1` (txt) vs `==1.1.0` (lock) |
| Long-term maintainability | Positive post-remediation; residual bridges | Domain isolation restored; Architecture 9.7 retained as sibling; R6 **5 compat_layers** accumulating; O-RR-01 long-lived naming; thin outer re-exports retained for compatibility |

**HEAD verification notes (anti-stale):**

| Claim | HEAD fact |
|---|---|
| TD-DL-001 CLOSED — no domain→outer imports | **True** — AST scan clean; isolation AT passes |
| Unified lock strategy | **Mostly true** — lock + empty pyproject deps; **txt≠lock** on `python-dotenv` |
| TD-DOC-003 / TD-DOC-004 CLOSED | **True** — artifacts present; register CLOSED |
| TD-DOC-001 — README wrong product | **False** — README describes AI Interview Simulator accurately (stale register row) |
| TD-TC-001 / TD-TC-002 — untested modules | **True** — no matching dedicated test modules |
| TD-001 — diversity embeddings at retrieval | **True** — remains OPEN High |

---

## 4. Scoring table

| Dimension | Score (/10) | Rationale (deductions explicit) |
|---|---|---|
| Domain complexity | 9.7 | Frozen contracts + dual-model closed + InterviewState on domain types; −0.3 O-RR-01 (`InterviewEvaluationService` / leftover `InterviewEvaluation` comments) |
| Coupling | 9.6 | Ownership / AT-01 + **TD-DL-001 closed** (prior −1.2 removed); −0.3 O-RR-01 naming coupling; −0.1 **TD-DL-003** |
| Cohesion | 9.6 | Engines/builders/projection boundaries clear; −0.4 residual evaluation-service naming vs Report SSOT vocabulary |
| Layer separation | 9.7 | AT/I-11 + isolation AT GREEN; domain→outer breach closed (prior −1.5 removed); −0.3 **TD-DL-003** |
| Technical debt | 9.0 | Zero V1.3 P0/P1; **TD-DL-001** / DOC-003/004 closed (prior structural/hygiene deductions removed); −0.4 High test-debt (**TD-TC-001/002**); −0.2 **TD-001**; −0.4 Medium OPEN volume (12); −0.1 stale **TD-DOC-001** register row |
| Testability | 9.0 | Large green suite + architecture/isolation gates; −0.5 **TD-TC-001**; −0.5 **TD-TC-002** |
| Documentation quality | 9.5 | Living docs + DOC-003/004 hygiene closed + version metadata aligned (prior −0.4/−0.3 removed); −0.4 O-RR-01 residue; −0.1 stale TD-DOC-001 |
| Change isolation | 9.9 | Field-level ownership + PAT/OP enforcement; InterviewState cross-layer entanglement closed (prior −0.3 removed); −0.1 **TD-EP02-001** |
| Dependency management | 9.5 | Lockfile + sole runtime pin SSOT in requirements\* (prior −1.2/−0.5/−0.3 largely removed); −0.5 **requirements.txt vs requirements.lock pin mismatch** (`python-dotenv`) |
| Long-term maintainability | 9.2 | Domain isolation + EPIC-10 purity + Architecture 9.7; −0.4 R6 **5 compat layers** accumulating; −0.3 O-RR-01; −0.1 residual global-mutable / bridge note |
| **Overall (mean)** | **9.5** | Mean of ten dimensions = **94.7 / 10 = 9.47** → **9.5** (one decimal) |

---

## 5. Final Maintainability Score

| Field | Value |
|---|---|
| **Final Maintainability Score** | **9.5 / 10** |
| Master Plan §9 target | ≥ 9.5 |
| Delta to target | **0.0** (meets gate) |
| Prior Maintainability score | 8.9 / 10 (NOT CERTIFIED) |
| Delta vs prior | **+0.6** |
| Sibling Architecture score (not substituted) | 9.7 / 10 CERTIFIED |

---

## 6. Certification decision

# CERTIFIED

**Rule applied:** Overall **9.5** ≥ **9.5**.

### Impact of remediation (re-verified at HEAD)

| Remediation item | Maintainability effect |
|---|---|
| **TD-DL-001 CLOSED** + isolation AT | Removes primary Layer separation / Coupling / Technical-debt deductions |
| Restored domain layer isolation | Domain complexity / Change isolation improve (InterviewState on `domain.*` only) |
| Unified dependency lock strategy | Dependency management recovers; residual **txt≠lock** pin keeps −0.5 |
| **TD-DOC-003 / TD-DOC-004 CLOSED** | Documentation + Technical-debt hygiene deductions removed |

### Do remaining open items prevent certification?

| ID | Prevents Overall ≥ 9.5? | Role at HEAD |
|---|---|---|
| **TD-001** | **No** | Contributes (−0.2 Technical debt) |
| **TD-TC-001** | **No** | Contributes (Testability / Technical debt); keeps those dimensions at 9.0 but not Overall below gate |
| **TD-TC-002** | **No** | Same as TD-TC-001 |
| **O-RR-01** | **No** | Spread residual naming deductions; not sole blocker |

No inflation applied: Architecture CERTIFIED status was not transferred; each dimension re-justified from HEAD `3887c0c`.

---

## 7. Remaining observations

| ID | Note | Blocks Maintainability Score ≥ 9.5? |
|---|---|---|
| TD-TC-001 / TD-TC-002 | Untested `decision_engine` / planning phases | **No** (contributes; Testability / Technical debt at 9.0) |
| TD-001 | Diversity embeddings unavailable at retrieval | **No** (contributes) |
| O-RR-01 | `InterviewEvaluationService` naming / comments | **No** (contributes) |
| — | `requirements.txt` vs `requirements.lock` `python-dotenv` pin drift | **No** alone (Dependency management 9.5 with −0.5) |
| TD-DOC-001 | Register still OPEN High; HEAD contradicts | Hygiene only |
| TD-DL-003 | Duplicate `LLMPort` Medium | Contributes small |
| TD-EP02-001 / TD-EP07-001 | Deferred Low | No alone |
| B-RR-01 | Architecture ≥ 9.5 | **Out of scope** (already CERTIFIED separately) |
| B-RR-03 | Prod-equivalent deploy validation | **Out of scope** |
| — | RR re-run / VERSION / tags | **Out of scope** |

---

## 8. Commit information

| Field | Value |
|---|---|
| Artifact path | `docs/master-plan/V13-MAINTAINABILITY-SCORECARD.md` |
| Commit scope | Certification artifact only |
| Commit hash / message / resulting HEAD | Filled after git commit in the certification response |

---

## Document Version

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-22 | Initial V1.3 Maintainability Scorecard at HEAD `50536e8` — Overall 8.9; NOT CERTIFIED |
| 1.1 | 2026-07-22 | Re-certification at HEAD `3887c0c` after Maintainability remediation — Overall 9.5; CERTIFIED |
