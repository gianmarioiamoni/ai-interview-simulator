# EPIC-10 — Architecture Freeze

**Status:** APPROVED  
**Date:** 2026-07-21  
**Epic ID:** EPIC-V13-10  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-10; Product Goal P-10  
**Inputs:** `EPIC-10-ARCHITECTURE-DISCOVERY.md`; `EPIC-10-ARCHITECTURE-REVIEW.md` (APPROVED WITH OBSERVATIONS); `EPIC-10-OVERVIEW.md`; ARC-01; Playbook v1.0  
**Authority:** Freezes Architecture Review decisions **AR-01–AR-14**. Introduces **no** new architecture beyond Review-accepted scope.  
**ADR required:** NO (AR-11)  
**Domain Contracts:** **REQUIRED** — structure and obligations frozen here; full Ownership Matrix / deletion table / Traceability delivered in `EPIC-10-DOMAIN-CONTRACTS.md` **before Implementation Plan acceptance**  
**Data Model:** **N/A (frozen default)** — exception only if Contracts prove durable shape impact (AR-07)  
**Implementation authorization:** **CONDITIONAL** — Implementation Plan may be drafted against this Freeze; **acceptance and coding are blocked** until Domain Contracts satisfy Playbook §8.2 / §8.7

**Disambiguation:** Not PRD EPIC-10 (Progress Tracking).

---

## 1. Scope (frozen)

Final Architecture Cleanup / release-gate audit:

- Dual PAT / OP registry formalization + Master Plan “five new PATs” interpretation
- `InterviewState` Ownership Matrix (document authorized writers; no redesign)
- Deprecated / dead / migration-scaffold disposition
- PAT-06 corollary enforcement
- Deploy-artifact dead-code purity (`TD-EP08-001`)
- Mandatory architectural-test gates (AR-10)

**Out of scope (frozen):** new product features; CandidateProfile dual-model / rename redesign; multi-writer cluster redesign; performance optimisation; SessionHistory durable store; renumbering OPs as PAT-07+.

---

## 2. Architectural objectives (frozen)

| ID | Objective |
|---|---|
| AO-01 | INDEX registers OP-01…06 (Official Patterns) + P-08 cross-link; PAT-01…06 unchanged |
| AO-02 | Master Plan “five new PATs” interpreted as OP-01…04 + P-08 |
| AO-03 | Every `InterviewState` field has declared authorized writer set in Ownership Matrix |
| AO-04 | Dead stubs / proven-dead state fields / obsolete MIG scaffolding disposed per AR-04 |
| AO-05 | PAT-06 corollary enforced by allowlist arch tests |
| AO-06 | Deploy artifact purity: delete + `.dockerignore`; close `TD-EP08-001` |
| AO-07 | Zero known constitutional / PAT violations in epic scope at close |
| AO-08 | Preserve ARC-01: P-01, P-04, P-06, P-08, OP-04; no silent ownership redesign |

---

## 3. Frozen decisions (AR-01–AR-14)

### 3.1 Accepted / deferred (binding)

| ID | Frozen decision |
|---|---|
| **AR-01** | Dual namespace: PAT-01…06 = Engineering Pattern Registry; OP-01…06 = Official Patterns (ARC-01). Do **not** renumber OPs as PAT-07+. Amend `INDEX.md` with Official Patterns section listing OP-01…06. Master Plan “five new PATs” = OP-01…04 + P-08. |
| **AR-02** | Reconstruction Completeness remains **ARC-01 P-08** — not a PAT. INDEX cross-links P-08. Master Plan “PAT” wording = historical synonym for P-08. |
| **AR-03** | Authoritative Ownership Matrix (all 45 fields) via Domain Contracts. Document authorized writers as they exist, including authorized multi-writer sets. No navigation/UI control-plane redesign. UI-plane fields may list graph node + named UI handlers. Nav clear/reset of presentation fields = documented privilege, not second sole writer of semantic content. |
| **AR-04** | **Delete:** `gradio_app.py`; `EvaluationBridgeDetector` + dedicated tests; InterviewState fields `progress`, `dimension_signals`, `current_reasoning_decision` **only if** Contracts prove unused beyond orphan writes. **Retire** obsolete MIG/TCP scaffolding tests for transitional dual-paths. **Keep** live TCP production fields (`session_history`, `report`, etc.). Correct stale MP `InterviewState.report_output` wording. |
| **AR-05** | PAT-06 corollary: capability dispatch / node-invoked facades **not** violations; service calls that select workflow branch / lifecycle / workflow-step retry **are** violations. `RecoveryReplanner` capability-internal OK if node owns graph continuation. `start.py` bootstrap OK if not interview workflow routing. Enforce via allowlist + scan (AR-10). |
| **AR-06** | Deploy purity = **delete** confirmed dead production stubs + **`.dockerignore`** for non-runtime paths. Close `TD-EP08-001` when both certified. |
| **AR-07** | Domain Contracts **REQUIRED**. Data Model **N/A** unless Contracts find durable `SessionHistory` / `Report` / `schema_version` impact — then **stop** and author Data Model before Impl Plan acceptance. |
| **AR-08** | `candidate_profile_v2`: ownership declaration only. Out: rename, `dimension_scores` removal, V1.1 semantic migration. Residual dual-model → TD if needed. |
| **AR-09** | Projection-as-PAT-04 mislabels → replace with **OP-02** (docs/comments only). |
| **AR-10** | Seven mandatory CAR arch-test gates (see §7). |
| **AR-14** | Implementation mechanisms (paths, commit boundaries, exact `.dockerignore` globs) → Implementation Plan only. |

### 3.2 Explicitly rejected (binding)

| ID | Rejected |
|---|---|
| **AR-11** | New formal ADR for this epic |
| **AR-12** | Multi-writer cluster redesign |
| **AR-13** | Reclassification to Category A |

---

## 4. Frozen registry model

| Rule | Frozen |
|---|---|
| REG-01 | PAT-01…06 remain sole Engineering Pattern Registry IDs (`V1.2-PATTERN-FREEZE.md` + INDEX) |
| REG-02 | OP-01…06 remain Official Patterns under ARC-01; listed in INDEX **Official Patterns (ARC-01)** section |
| REG-03 | No OP→PAT renumbering; numeric ID collision acknowledged and managed by namespace labels |
| REG-04 | P-08 Reconstruction Completeness = constitutional principle; INDEX cross-link; not PAT-07 |
| REG-05 | Master Plan “six original + five new PATs” satisfied by PAT-01…06 + OP-01…04 + P-08 (wording clarification in INDEX / MP docs pass) |
| REG-06 | Projection Artifact references must use **OP-02**, never PAT-04 (AR-09) |

---

## 5. Frozen Ownership Matrix approach

| Rule | Frozen |
|---|---|
| OWN-01 | Domain Contracts SHALL contain Ownership Matrix covering every `InterviewState` field |
| OWN-02 | Each row: field · type · authorized writer set · primary readers · notes (clear/reset privileges) |
| OWN-03 | Authorized multi-writer sets permitted when intentional and explicit (e.g. `results_by_question`) |
| OWN-04 | No ownership redesign of navigation/UI control plane in EPIC-10 |
| OWN-05 | Field deletion requires Contracts proof of no production readers (beyond orphan writes) |
| OWN-06 | `candidate_profile_v2` ownership declared; rename/dual-model redesign forbidden (AR-08) |
| OWN-07 | Ownership Matrix is the state-contract surface for this epic (Category B) |

---

## 6. Frozen cleanup scope

| Rule | Frozen |
|---|---|
| CLN-01 | Delete `gradio_app.py` |
| CLN-02 | Delete `EvaluationBridgeDetector` module + dedicated tests |
| CLN-03 | Conditionally delete `progress`, `dimension_signals`, `current_reasoning_decision` per Contracts proof |
| CLN-04 | Retire obsolete MIG/TCP scaffolding tests (transitional dual-path only) |
| CLN-05 | Keep live production TCP nullable fields |
| CLN-06 | Deploy purity: delete + `.dockerignore` (AR-06); close `TD-EP08-001` |
| CLN-07 | Docs: remove/correct stale `InterviewState.report_output` go-live claim |
| CLN-08 | No CandidateProfile semantic redesign |

---

## 7. Frozen PAT-06 + architectural-test gates

### 7.1 PAT-06 corollary (frozen classes)

| Class | Examples | Disposition |
|---|---|---|
| Not violation | `ExecutionEngine` type→executor; `AreaQuestionBuilder` area→pipeline; node-invoked facades returning results | Allowlisted |
| Violation | Service selects NEXT/RETRY/report/lifecycle or workflow-step retry | Forbidden |
| Conditional | `RecoveryReplanner`, `start.py` bootstrap | Allowed only within AR-05 bounds |

### 7.2 Mandatory arch-test gates (AR-10) — CAR blockers

| Gate | Requirement |
|---|---|
| AT-01 | Ownership Matrix coverage — every `InterviewState` field has declared authorized writer set |
| AT-02 | Deleted stubs absent (`gradio_app`, `EvaluationBridgeDetector`) |
| AT-03 | PAT-06 corollary allowlist / forbidden-pattern scan |
| AT-04 | INDEX lists OP-01…06 + P-08 cross-ref |
| AT-05 | No Projection-as-PAT-04 in `domain/contracts/report` |
| AT-06 | Existing P-08 reconstruction tests remain green |
| AT-07 | Deploy purity — deleted paths absent + `.dockerignore` present for agreed non-runtime globs |

---

## 8. Domain Contracts & Data Model (frozen obligations)

| Artifact | Freeze status | Binding rule |
|---|---|---|
| Domain Contracts | **REQUIRED** | Must deliver Ownership Matrix + deletion specs + Traceability (P-10) before Impl Plan **acceptance** |
| Data Model | **N/A (frozen)** | No durable shape change expected. If Contracts detect `SessionHistory` / `Report` / `schema_version` impact → **stop**; author Data Model; amend Freeze before Impl Plan acceptance |
| Traceability Matrix | **REQUIRED** (inside Contracts) | Every Master Plan P-10 / EPIC-10 requirement → contract surface → verification artifact (AT-* / deletion) |
| Component Inventory | **N/A** | Non-UI-bearing cleanup epic (Discovery) |

---

## 9. Category B implementation constraints

| ID | Constraint |
|---|---|
| IC-01 | No architectural choices during coding beyond this Freeze + accepted Domain Contracts |
| IC-02 | No new ADR unless Stopping Rule triggered |
| IC-03 | No OP renumber into PAT namespace |
| IC-04 | No ownership redesign; only document / test / delete per AR-03/AR-04 |
| IC-05 | No CandidateProfile dual-model redesign |
| IC-06 | No compute-in-projection; no second LangGraph orchestrator |
| IC-07 | Deletion completes cleanup — no new long-lived `deprecated` without milestone |
| IC-08 | Zero Known Failing Tests at every commit boundary |
| IC-09 | CAR includes Architecture Traceability Review (Category B) |
| IC-10 | Impl Plan acceptance blocked until Domain Contracts complete (§8.7) |
| IC-11 | If durable shape impacted → Data Model mandatory before coding |
| IC-12 | Mechanism details deferred to Impl Plan (AR-14) only within frozen scope |

---

## 10. Assumptions (frozen VERIFIED)

| ID | Status |
|---|---|
| AA-01 … AA-10 | **VERIFIED** per Architecture Review — retained |

---

## 11. ADR skip rationale (frozen)

**New ADR: NO.** Authority: ARC-01 (OP-01…06, P-04, P-08, deletion principle); `V1.2-PATTERN-FREEZE.md` PAT-01…06; EPIC-08 AR-16; this Freeze AR-01–AR-14. Field deletions and ownership documentation proceed via Domain Contracts, not a new ADR.

---

## 12. Architecture Exit Criteria (§8.7) — Freeze evaluation

| Criterion | Status |
|---|---|
| Architecture Discovery complete | **PASS** |
| Component Inventory (UI-bearing) | **N/A** |
| Traceability Matrix complete | **PENDING** — Domain Contracts |
| Domain Contracts frozen | **PENDING** — structure frozen (AR-07); document not yet authored |
| Data Model frozen | **N/A (PASS default)** — exception path documented |
| Assumptions VERIFIED | **PASS** |
| No BLOCKER findings | **PASS** (Contracts pending is gate, not Review blocker) |
| ADR decisions complete | **PASS** — ADR skipped (AR-11) |
| Architecture Freeze declared | **PASS** — this document |
| Implementation Plan accepted | **NOT YET** |

**Freeze declaration:** Architecture decisions are **FROZEN**.  
**Implementation start:** **BLOCKED** until Domain Contracts (§8.2) and Traceability are complete; then Impl Plan acceptance may proceed.

---

## 13. Observations carried into Freeze

| ID | Observation | Handling |
|---|---|---|
| O-01 | Stale MP `report_output` text | CLN-07 / docs pass |
| O-02 | Exact `.dockerignore` globs | Implementation Plan |
| O-03 | Multi-writer sets must be explicit in Contracts | OWN-03; CAR AT-01 |
| O-04 | `dimension_scores` dual-model residual | TD if needed (AR-08) |
| O-05 | Corollary scan false positives | Impl Plan allowlist tuning within AR-05 |

---

## 14. Freeze summary

| Item | Result |
|---|---|
| Verdict | **APPROVED** — decision Freeze |
| Category | **Category B** |
| ADR | **SKIP** |
| Domain Contracts | **REQUIRED** before Impl Plan acceptance |
| Data Model | **N/A** (default; exception documented) |
| Next | Author `EPIC-10-DOMAIN-CONTRACTS.md` → Implementation Plan |
| Production code | **Not authorized yet** (IC-10) |

**Stop after Architecture Freeze.**
