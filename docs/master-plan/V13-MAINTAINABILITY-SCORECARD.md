# V1.3 — Maintainability Scorecard

**Artifact ID:** MS-V1.3  
**Gate:** Master Plan §9 Maintainability score ≥ 9.5; Playbook §10 Release Readiness Success Metrics  
**Activity:** Maintainability Score Certification  
**Date:** 2026-07-22  
**Evaluated HEAD:** `50536e8e4415e60833870a1fb90d0d80c9f5c636`  
**Working tree at evaluation:** clean  
**Prior Maintainability score:** none (V1.2 / V1.3)  
**Scope:** Maintainability score only — no Architecture re-score; no Release Readiness re-run; no VERSION/tag ceremony; no production-logic changes  

---

## 1. Preflight

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `50536e8e4415e60833870a1fb90d0d80c9f5c636` |
| Working tree | clean |
| Prior Maintainability Scorecard | **Absent** (B-RR-02) |
| V1.3 Architecture Scorecard | **CERTIFIED** Overall **9.7** (`AS-V1.3` v1.1; commit `50536e8`) |
| Prior RR Maintainability metric | **UNSATISFIED** — no scorecard (`V13-RELEASE-READINESS-REVIEW.md` §6) |
| Open V1.3 P0/P1 findings | Zero |

### Inputs used

| Input | Role |
|---|---|
| `ARC-01-ARCHITECTURE-CONSTITUTION.md` | Layer / ownership / projection constraints affecting maintainability |
| `V13-DEVELOPMENT-PLAYBOOK.md` v1.0 | RR / Success Metrics process |
| `V13-PRODUCT-MASTER-PLAN.md` §9 | Score target ≥ 9.5 |
| `V13-ARCHITECTURE-SCORECARD.md` (CERTIFIED) | Adjacent architectural evidence; **not** reused as Maintainability scores |
| `V13-RELEASE-READINESS-REVIEW.md` | RR baseline (tests, observations, §9 gaps) |
| `V13-RELEASE-BLOCKER-ASSESSMENT.md` | B-RR-02 classification (methodology + scorecard required) |
| `docs/technical-debt-register.md` | Registered OPEN / DEFERRED / CLOSED debt |
| Repository at evaluated HEAD | Objective structure, imports, tests, deps, docs |

---

## 2. Evaluation methodology

1. **Numeric method (aligned with AS-V1.3 / AC-V1.2 §A2):** score each dimension **/10** with evidence-backed rationale and explicit deductions; compute **Overall** as the **arithmetic mean** of scored dimensions; report Overall to **one decimal**.
2. **V1.3 Maintainability dimension set** (Master Plan §9 maintainability certification; B-RR-02 rubric):
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
3. **Evidence classes admitted:** ARC-01; Ownership Matrix / AT-01…07 / I-11; Technical Debt Register; RR regression + observations; direct repository inspection at HEAD `50536e8` (imports, layouts, manifests, docs presence).
4. **Anti-inflation rule:** Architecture CERTIFIED (9.7), zero P0/P1, and green AT gates do **not** auto-award Maintainability ≥ 9.5. Stale register claims contradicted by HEAD evidence are **not** scored as if still true, but register drift itself is a documentation/debt-hygiene deduction. Closed architectural TDs do not erase remaining High OPEN maintainability debt.
5. **Certification rule:** Overall ≥ 9.5 → **CERTIFIED**; otherwise **NOT CERTIFIED**.

---

## 3. Maintainability assessment

| Criterion | Result | Evidence |
|---|---|---|
| Domain complexity | Controlled, residual naming load | `domain/` 268 `.py` (219 under `domain/contracts/`); dual-model **TD-EP10-001 CLOSED** (`features` authoritative); no `InterviewEvaluation` class; residual `InterviewEvaluationService` (O-RR-01) |
| Coupling | Ownership strong; domain→outer coupling remains | Ownership Matrix 43/43 + AT-01 GREEN; **TD-DL-001 OPEN High** — `domain/contracts/interview_state/base.py` imports `services/` + `app/`; also `question_bank_item.py`, `question_runtime_lineage.py`, `business_context.py` → outer layers |
| Cohesion | Strong modular cohesion | Distinct engines/builders (`feature_engine`, `knowledge_pipeline`, `coaching_engine`, `report_builder`, `candidate_profile_builder`); presentation SSOT `FinalReportDTO.from_report`; projection/compute bans in UI architecture tests |
| Layer separation | Enforced in places; violated at InterviewState contracts | AT-01…07 + I-11 present (`tests/infrastructure/architecture/test_epic10_cleanup_architecture.py`, replay invariants); **TD-DL-001** confirmed at HEAD; **TD-DL-003** duplicate `LLMPort` Medium OPEN |
| Technical debt | No V1.3 P0/P1; High OPEN cluster remains | Register: **7 High OPEN** listed; HEAD-confirmed High burden includes **TD-DL-001**, **TD-001**, **TD-TC-001**, **TD-TC-002**; **12 Medium OPEN**; V1.3 epic Lows remaining: **TD-EP02-001**, **TD-EP07-001** DEFERRED; TD-EP05/08/10 CLOSED |
| Testability | Strong suite; coverage holes in named modules | RR: **7378 / 0**; ~130 architecture `test_*` functions; **no** dedicated tests under `tests/` for `services/decision_engine/` or `services/interview_planning/phases/` (TD-TC-001/002) |
| Documentation quality | V1.3 living docs strong; debt SSOT drift | RR §5 docs sync PASS; Overviews EPIC-01…10 present; O-RR-01 naming/comment residue; **TD-DOC-003/004 still OPEN in register but contradicted at HEAD** (`.env.example` exists; `docs/architecture/configuration.md` exists) — register hygiene defect; `VERSION`=`1.1.0` vs `pyproject.toml` `0.1.0` |
| Change isolation | Strong field ownership | `EPIC-10-OWNERSHIP-MATRIX.json` sole-writer model; PAT-06 / OP registry AT-03/AT-04; residual multi-concern `InterviewState` surface via outer-type imports |
| Dependency management | Weak reproducibility | `requirements.txt` + `pyproject.toml` both present; **no** `poetry.lock` / `uv.lock` / requirements lockfile; pin styles diverge (exact vs `>=` ranges) |
| Long-term maintainability | Positive post-EPIC-10; residual bridges | AT-02/AT-07 dead-code / deploy purity; R6 scorecard: 0 confirmed dead-code, **5 compat_layers** “accumulating”; dual-model remediation retained at HEAD |

**HEAD verification notes (anti-stale):**

| Register claim | HEAD fact |
|---|---|
| TD-DOC-003 — no `.env.example` | **False** — `.env.example` present |
| TD-DOC-004 — no configuration reference | **False** — `docs/architecture/configuration.md` present (164 lines) |
| TD-DOC-001 — README wrong product | **Not sustained** — README describes AI Interview Simulator accurately |
| TD-DL-001 — domain imports outer layers | **True** — imports verified in listed domain contract files |
| TD-TC-001 / TD-TC-002 — untested modules | **True** — no matching test modules found |

---

## 4. Scoring table

| Dimension | Score (/10) | Rationale (deductions explicit) |
|---|---|---|
| Domain complexity | 9.5 | Frozen contracts + dual-model closed; −0.3 O-RR-01 (`InterviewEvaluationService`); −0.2 InterviewState outer-type surface increases cognitive load |
| Coupling | 8.4 | Ownership Matrix / AT-01 strong; −1.2 **TD-DL-001** confirmed domain→`services`/`app` coupling; −0.3 O-RR-01 naming coupling; −0.1 **TD-DL-003** |
| Cohesion | 9.6 | Engines/builders/projection boundaries clear; −0.4 residual evaluation-service naming vs Report SSOT vocabulary |
| Layer separation | 8.2 | AT/I-11 gates strong; −1.5 **TD-DL-001** High OPEN multi-file domain layer breach; −0.3 **TD-DL-003** duplicate port |
| Technical debt | 8.2 | Zero V1.3 P0/P1; epic architectural Lows mostly closed; −0.5 confirmed High structural (**TD-DL-001**); −0.4 High test-debt (**TD-TC-001/002**); −0.2 **TD-001**; −0.4 Medium OPEN volume (12); −0.3 register hygiene (stale High DOC rows) |
| Testability | 9.0 | 7378/0 + 130 architecture tests + injectable seams; −0.5 **TD-TC-001**; −0.5 **TD-TC-002** |
| Documentation quality | 8.9 | Master-plan / epic living docs aligned (RR PASS); −0.4 O-RR-01 residue; −0.4 stale TD-DOC High rows vs HEAD; −0.3 `VERSION`/`pyproject` version drift |
| Change isolation | 9.6 | Field-level ownership + PAT/OP enforcement; −0.3 InterviewState cross-layer type entanglement; −0.1 **TD-EP02-001** reconstructability deferral |
| Dependency management | 8.0 | Manifests present; −1.2 **no lockfile**; −0.5 dual-manifest pin divergence risk; −0.3 package version metadata drift (`0.1.0` vs `1.1.0`) |
| Long-term maintainability | 9.2 | EPIC-10 purity + dual-model removal + Architecture 9.7; −0.4 R6 **5 compat layers** accumulating; −0.3 O-RR-01 long-lived naming debt; −0.1 R6 global mutable residual note |
| **Overall (mean)** | **8.9** | Mean of ten dimensions = **88.6 / 10 = 8.86** → **8.9** (one decimal) |

---

## 5. Final Maintainability Score

| Field | Value |
|---|---|
| **Final Maintainability Score** | **8.9 / 10** |
| Master Plan §9 target | ≥ 9.5 |
| Delta to target | **−0.6** |
| Prior Maintainability score | none |
| Sibling Architecture score (not substituted) | 9.7 / 10 CERTIFIED |

---

## 6. Certification decision

# NOT CERTIFIED

**Rule applied:** Overall **8.9** &lt; **9.5**.

### Exact maintainability criteria preventing certification

The Overall mean is held below 9.5 primarily by these under-target dimensions (each &lt; 9.5 with HEAD evidence):

1. **Layer separation (8.2)** — **TD-DL-001** OPEN High: domain contracts import `services/` / `app/` / `infrastructure/` (verified in `domain/contracts/interview_state/base.py` and related files).
2. **Coupling (8.4)** — same structural domain→outer dependency edge; plus O-RR-01 naming coupling to retired `InterviewEvaluation` vocabulary.
3. **Technical debt (8.2)** — confirmed High OPEN maintainability burden (**TD-DL-001**, **TD-TC-001**, **TD-TC-002**, **TD-001**) plus Medium OPEN volume and stale High DOC register rows.
4. **Dependency management (8.0)** — no reproducible lockfile; dual manifests with divergent pin policy.
5. **Documentation quality (8.9)** — not sole blocker, but contributes: O-RR-01 residue, TD-register drift, version metadata inconsistency.

Secondary contributors still &lt; 9.5 but smaller gap: **Testability (9.0)** (decision engine / planning phases untested), **Long-term maintainability (9.2)** (compat-layer accumulation).

No inflation applied: Architecture CERTIFIED status was not transferred to Maintainability.

---

## 7. Remaining observations

| ID | Note | Blocks Maintainability Score ≥ 9.5? |
|---|---|---|
| TD-DL-001 | Domain→outer imports | **Yes** (primary — Layer separation / Coupling / Technical debt) |
| TD-TC-001 / TD-TC-002 | Untested decision_engine / planning phases | **Yes** (contributes — Testability / Technical debt) |
| — | No dependency lockfile | **Yes** (primary — Dependency management) |
| TD-DOC-001/003/004 | Register still OPEN High; HEAD contradicts 003/004 (and not 001) | Contributes via register hygiene; do not treat missing `.env.example` / config doc as current fact |
| O-RR-01 | `InterviewEvaluationService` naming / comments | Contributes (not sole) |
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
