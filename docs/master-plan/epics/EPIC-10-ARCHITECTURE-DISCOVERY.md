# EPIC-10 — Architecture Discovery

**Status:** COMPLETE  
**Date:** 2026-07-21  
**Epic ID:** EPIC-V13-10  
**Playbook Category:** Category B — Major Architectural Epic (**confirmed**; see §9)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-10; Product Goal P-10  
**Living Overview:** `EPIC-10-OVERVIEW.md`  
**Playbook:** V13 Development Playbook Version 1.0  
**Regression baseline (reference):** 7485 passed / 0 failed (EPIC-09 close-out; suite not re-run)

**Authority:** Findings-only analysis. Does not freeze decisions. Does not authorize implementation. Does not propose solutions.

**Disambiguation:** Not PRD EPIC-10 (Progress Tracking).

---

## 1. Purpose

Inventory architectural cleanup surfaces for EPIC-V13-10 Final Architecture Cleanup: PAT/OP registries, `InterviewState` ownership, deprecated/dead artifacts, PAT-06 corollary impact, migration scaffolding, deploy-artifact purity, risks, and Category A/B confirmation. Identify decisions that require Architecture Review.

---

## 2. Scope inventory (Master Plan)

| Item | Master Plan statement |
|---|---|
| Four emerging PATs | Formalize Cascading Closure, Projection Artifact, Runtime First / Projection Later, Sole-Writer Node |
| Reconstruction Completeness | Declare and enforce (Master Plan calls this a PAT) |
| Six original + five new PATs | All registered, named, enforced by architectural tests where possible |
| Deprecated audit | Every `deprecated` annotation → delete or promote with deletion milestone |
| InterviewState ownership | Every field: declared sole writer + declared readers |
| PAT-06 corollary | Services must not call other services in a way that implements routing logic |
| Dead test scaffolding | Retire V1.2 migration scaffolding |
| Deploy artifact purity | No dead code in deployed build (carry-forward `TD-EP08-001`) |
| Non-goals | New features; test expansion beyond architectural enforcement; performance optimisation |

---

## 3. Authoritative PAT / OP registry (D-01)

### 3.1 Three parallel vocabularies (confirmed)

| Namespace | Authority | IDs | Contents |
|---|---|---|---|
| **PAT** (Engineering Pattern Registry) | `V1.2-PATTERN-FREEZE.md` + `INDEX.md` Pattern Registry | PAT-01…06 | Five-Artifact; Runtime First/Orchestration Second; CPR; TCP; Builder-only; Single Runtime Orchestrator |
| **OP** (Official Patterns) | `ARC-01` §5 + `ARCHITECTURE-GUIDE.md` §8 | OP-01…06 | Cascading Closure; Projection Artifact; Runtime First/Projection Later; Sole Writer Node; Single Builder; Immutable Accumulation |
| **Constitutional principles** | `ARC-01` §2 | P-01…P-08 | Includes **P-08 Reconstruction Completeness** |

**Finding:** `INDEX.md` registers **only PAT-01…06**. OP-01…06 are constitutional/guide patterns but **not** listed in the INDEX Pattern Registry. Numeric IDs collide across namespaces (e.g. PAT-04 = TCP ≠ OP-04 = Sole Writer Node).

### 3.2 Master Plan “five new PATs” mapping (evidence)

| Master Plan phrase | Evidence mapping |
|---|---|
| “six original PATs” | Pattern Freeze **PAT-01…06** |
| “four emerging PATs” | Retrospective names → already **OP-01…04** in ARC-01 |
| “five new PATs” | Four emerging + **Reconstruction Completeness** |
| Reconstruction Completeness | Declared as **ARC-01 P-08**; called “PAT” only in Master Plan / epic prose — **not** in Pattern Freeze / INDEX as a PAT |

### 3.3 Near-duplicates / doc ID misuse

| Finding | Evidence |
|---|---|
| OP-05 ≈ PAT-05 | Single Builder ≈ Builder-only Construction |
| OP-03 related to ≠ PAT-02 | Runtime First/Projection Later vs Runtime First/Orchestration Second |
| Projection Artifact mislabeled `PAT-04` | `domain/contracts/report/scoring_*.py`; `adr-033`; `EPIC-01-DOMAIN-CONTRACTS.md` (collides with TCP) |

### 3.4 Applicable pattern requirements for EPIC-10

| ID | Requirement | Current registration | Enforcement (sample) |
|---|---|---|---|
| PAT-01…06 | Remain operative | INDEX + Pattern Freeze | Partial / scattered |
| OP-01…04 | Master Plan “formalize emerging” | Already in ARC-01; **not** in INDEX PAT registry | Partial (sole-writer tests thin) |
| OP-05 / OP-06 | Official patterns | ARC-01 | Builder tests; OP-06 ↔ P-08 |
| P-08 | Reconstruction Completeness | Constitutional principle | ReplaySession builder tests; longitudinal LP-08; prior epic matrices |
| PAT-06 + corollary | Sole orchestrator + no service routing | PAT registered; corollary in retrospective/MP | Nav configure + session_close no-subgraph only |

### 3.5 Registry inventory Discovery records (no decision)

Discovery records **three layers**, not one renumbered list:

1. Frozen PATs PAT-01…06  
2. Constitutional OPs OP-01…06  
3. Master Plan “five new” intent = OP-01…04 names + P-08 (wording mismatch vs current registry)

---

## 4. InterviewState ownership matrix (D-02)

**Source of truth:** `domain/contracts/interview_state/base.py` (+ mixins/factory). **45 fields.**

### 4.1 Summary

| Metric | Count |
|---|---|
| Total fields | **45** |
| Strong sole-writer declaration (`base.py` / OP-04 / ADR) | **~10** |
| Ownership gap (no OP-04 sole writer + readers, or doc≠code) | **~35** |
| Multi-writer observed | **≥12** |
| Arch-tested node-reference ownership | **3** (`observation_store`, `candidate_profile_v2`, `session_history`) + feedback presentation guard |

### 4.2 Strongly declared (code comments / OP-04)

| Field | Declared sole writer | Arch-tested? |
|---|---|---|
| `scoring_snapshot` | EvaluationAggregateNode | No |
| `scoring_narrative` | EvaluationAggregateNode | No |
| `interview_memory` | InterviewReasoner / reasoner_node (naming drift) | No |
| `candidate_identity_id` | Factory create_* | No |
| `observation_store` | reasoner_node | **Yes** |
| `candidate_profile_v2` | reasoner_node / KP path | **Yes** |
| `session_history` | session_close_node | **Yes** |
| `report` | report_node | No |
| `follow_up_eligible_indices` | FollowUpSelector @ start (write-once) | No |
| `last_feedback_bundle` | feedback_node (AR-11); adaptive_nav clears | Partial |

### 4.3 High-gap / multi-writer clusters (findings)

| Cluster | Fields | Finding |
|---|---|---|
| Control / UI flags | `intent`, `is_processing`, `current_step`, `awaiting_user_input`, `current_progress`, `allowed_actions` | Graph + UI writers; no OP-04 matrix |
| Fan-in results | `results_by_question` | evaluation / execution / written_eval / hint (+ nav clear) |
| Navigation vs UI | `questions`, `answers`, `planned_areas`, `retrieval_memory`, `adaptive_interview_enabled` | Blueprint owners stale vs code |
| Session init | `interview_id`, `role`, `company`, `language`, `interview_type`, `seniority_level`, `interview_length`, `context_profile` | Factory-only; no OP-04 declaration |

### 4.4 Dead / orphan candidates on or near state

| Name | Finding |
|---|---|
| `progress` | Factory sets `SETUP`; never advanced by nodes |
| `dimension_signals` | Written by evaluation_node; no graph readers found |
| `current_reasoning_decision` | Written/cleared by reasoner_node; no production readers outside node |
| `memory_context` / `interview_evaluation` | **Already removed** from state |
| `report_output` | **Not** on `InterviewState`; lives on UI response surface; Master Plan go-live text still mentions state field (stale) |

### 4.5 Stale ownership docs

`V1.2-RUNTIME-INTEGRATION-BLUEPRINT.md` §4 still lists removed fields and wrong owners for several live fields. Not authoritative for EPIC-10 close.

### 4.6 Enforcement paths

- `tests/domain/contracts/interview_state/test_interview_state_field_invariants.py` (`TestSoleWriterOwnership`)
- `tests/ui/architecture/test_epic07_hardening_architecture.py` (`TestFeedbackBundleWriterInvariant`)
- Gap: no complete field×writer×reader matrix enforced

---

## 5. Deprecated / dead / migration scaffolding inventory (D-03)

### 5.1 Python deprecation markers

| Marker | Finding |
|---|---|
| `@deprecated` / `deprecated=True` | **None** in production code |
| Explicit deprecate stub | `gradio_app.py` (`SystemExit` + deprecated message) |
| `warnings.warn` deprecation | Test fixtures only (`tests/infrastructure/execution/*`) |

### 5.2 Named remnant inventory

| Artifact | Status | Paths / notes |
|---|---|---|
| `gradio_app.py` | Deprecated stub still on disk | Root; deploy purity candidate (`COPY . .`, **no** `.dockerignore`) |
| `EvaluationBridgeDetector` | File + tests present; registry asserts absent | `services/interview_reasoner/pattern_detection/detectors/evaluation_bridge_detector.py` + tests |
| `InterviewEvaluation` class | Gone | Residue: `services/interview_evaluation_service.py`, packages, comments; TD-EP05-001 import-ban gap |
| `ReplayResult` | Gone | Doc/comment residue; ADR-037 deletion complete in code |
| `memory_context` | Gone | Guard test remains |
| `report_output` (state) | Gone from state | UI `report_output` HTML surface remains (not Master Plan state-field target as written) |
| CandidateProfile V1.1 dual model | Still present | `dimension_scores` + `features`; state field still named `candidate_profile_v2` |
| TCP nullable V1.2 fields | Still present (live) | `candidate_identity_id`, `observation_store`, `candidate_profile_v2`, `session_history`, `report` — not automatically “dead” |
| MIG-* / TCP test scaffolding | Present | e.g. `tests/domain/profile/test_candidate_profile_derivation_*`, session_close/report TCP comments |
| AdaptiveInterviewMemoryBridge | Removed | Logic inlined in adaptive_navigation_node |

### 5.3 Technical debt carry-forward

| ID | Item | Status |
|---|---|---|
| **TD-EP08-001** | Deploy-artifact dead-code purity | **DEFERRED → EPIC-10** |
| TD-EP05-001 | Arch suite missing `InterviewEvaluation` import ban | OPEN (adjacent) |

### 5.4 Deploy artifact purity

| Evidence | Finding |
|---|---|
| `Dockerfile` | `COPY . .` — full tree |
| `.dockerignore` | **Absent** |
| Purity candidates | `gradio_app.py`, unused `EvaluationBridgeDetector` (+ tests), other non-runtime residue TBD at Review |

---

## 6. PAT-06 corollary impact surface (D-04)

### 6.1 Definition (operative)

- **PAT-06:** LangGraph is sole runtime orchestrator (workflow sequence, branching, retries, lifecycle).
- **Corollary (Master Plan / retrospective):** Services must not call other services in a way that implements **routing logic**.
- **Thin Orchestrator:** Node → many services OK; Service → coordinates services for workflow = second orchestrator.

### 6.2 Existing enforcement

| Path | Coverage |
|---|---|
| `tests/graph/nodes/test_navigation_node.py` | Unconfigured nav fail-fast; legacy nav absent |
| `tests/app/graph/nodes/test_session_close_node.py` | No `StateGraph` / langgraph import in node |
| Service→service routing scan | **Absent** (RI-12 CAR audit documented historically; not automated) |

### 6.3 Confirmed vs suspects

| Class | Item |
|---|---|
| **Confirmed historical (resolved)** | `InterviewPipeline` second orchestrator — removed |
| **Confirmed open live violation** | **None** documented in current CAR artifacts |
| **Unverified suspects** | `AreaQuestionBuilder` area→pipeline; `ExecutionEngine` type→executor; `RecoveryReplanner` retry loop; `InterviewEvaluationService` multi-service sequencing; pre-graph bootstrap in `app/ui/state_handlers/start.py` |
| **Intended node-owned routing** | `adaptive_navigation_node` / graph edges (Architecture Guide: keep in node) |

---

## 7. Affected subsystems

| Subsystem | Relevance |
|---|---|
| Pattern registries (INDEX / Pattern Freeze / ARC-01 / Guide) | Registry formalization |
| `InterviewState` + graph nodes + UI state handlers | Ownership matrix |
| Reasoner detectors / evaluation services | Dead detector; scoring residue |
| Deploy / Docker image composition | TD-EP08-001 |
| Architectural test suites | Enforcement gaps |
| Technical debt register | Close/defer dispositions |
| Prior epic Freezes (08/09) | Release-gate carry-forwards |

**UI-bearing:** No new UI feature scope. Component Inventory **N/A** (cleanup/governance epic). Presentation touched only if dead UI entrypoints deleted.

---

## 8. Current vs target state

| Area | Current | Master Plan target (EPIC-10) |
|---|---|---|
| PAT registry | PAT-01…06 in INDEX; OP-01…06 in ARC-01; P-08 separate | “Six + five” registered/named/enforced — wording unresolved |
| InterviewState ownership | ~10 declared; ~35 gaps; thin arch tests | Zero fields without declared owner |
| Deprecated markers | Almost none; stubs/files remain | Zero deprecated without deletion milestone |
| Dead code / deploy | Full-tree Docker copy; known stubs | No dead code in deployed build |
| PAT-06 corollary | Partial node guards; no service scan | Corollary enforced |
| Migration scaffolding | MIG/TCP tests + dual CandidateProfile fields remain | Scaffolding retired where dead |

---

## 9. Category recommendation

**Confirmed: Category B — Major Architectural Epic.**

| Criterion | Applies? |
|---|---|
| State contracts (`InterviewState` owners / write order) | **Yes** — Master Plan audit + observed multi-writer gaps |
| Domain contracts / persistent shape | **Conditional** — required if Review mandates field deletion or ownership reassignment that changes frozen contracts; documentation + arch-test-only path may keep Contracts/Data Model **N/A** |
| Report / replay / longitudinal structures | Not primary; residue only |
| Deploy / pattern governance | Yes — in scope |

**Escalate within Category B:** If Review requires stored-shape / `schema_version` changes, Domain Contracts + Data Model become mandatory before Freeze.

---

## 10. Architecture Assumptions Register

| ID | Description | Status | Verification Document | Notes |
|---|---|---|---|---|
| AA-01 | Full Phase 5 audit can close without introducing new product features. | **VERIFIED** | This Discovery §2 non-goals | |
| AA-02 | Domain Contracts / Data Model required only if ownership or stored-shape changes are proven necessary. | **VERIFIED** (conditional rule) | This Discovery §9 | Final necessity → Architecture Review |
| AA-03 | Existing ARC-01 + PAT-01…06 + OP-* are sufficient starting inputs for registry reconciliation. | **VERIFIED** | This Discovery §3 | Decision on unification deferred to Review |
| AA-04 | EPIC-V13-01 closure removed scoring-residue blockers that prevent audit start. | **VERIFIED** | EPIC-01 CLOSED; `InterviewEvaluation` class absent | Residue services/comments remain in-scope cleanup |
| AA-05 | `TD-EP08-001` deploy-artifact dead-code purity is in EPIC-10 scope. | **VERIFIED** | TD register; EPIC-08 AR-16; this §5.4 | |
| AA-06 | Phase 1 governance does not by itself satisfy Phase 5 full-audit close. | **VERIFIED** | This Discovery §3 — OP exist but INDEX/PAT formalization + ownership gaps remain | |
| AA-07 | Reconstruction Completeness enforcement can build on prior epic evidence without reopening closed feature epics. | **VERIFIED** | EPIC-02/03/06 matrices; P-08 tests exist | Registry naming still open (P-08 vs PAT) |
| AA-08 | Master Plan “five new PATs” = OP-01…04 + P-08 (not five new Pattern Freeze IDs). | **VERIFIED** (mapping finding) | This Discovery §3.2 | Registration *action* still requires Review |
| AA-09 | No open confirmed live PAT-06 corollary violation is documented today. | **VERIFIED** | This Discovery §6.3 | Suspects remain UNVERIFIED pending Review classification |
| AA-10 | Complete OP-04 ownership matrix does not exist for all 45 fields. | **VERIFIED** | This Discovery §4 | Core EPIC-10 gap |

---

## 11. Risks

| ID | Risk | Severity | Classification |
|---|---|---|---|
| R-01 | Registry unification creates dual-authority PAT/OP confusion if unresolved | High | Process / docs |
| R-02 | Declaring ownership freezes incorrect multi-writer reality | High | Architecture |
| R-03 | Dead-field deletion breaks latent consumers | High | Implementation |
| R-04 | PAT-06 corollary over-classifies capability dispatch as routing | Medium | Architecture |
| R-05 | Deploy purity via delete vs exclude diverges (no `.dockerignore`) | Medium | Ops |
| R-06 | Scope creep into CandidateProfile V1.1 semantic redesign | Medium | Scope |
| R-07 | Thin arch-test coverage leaves “enforced where possible” unmet | Medium | Verification |
| R-08 | Stale Master Plan go-live (`InterviewState.report_output`) misguides cleanup | Low | Docs |

---

## 12. Confirmed decisions (existing — reuse)

| Decision | Governing artifact |
|---|---|
| LangGraph sole orchestrator | PAT-06; ARC-01 P-04 |
| Sole Writer Node pattern | OP-04; ARC-01 |
| Reconstruction Completeness principle | ARC-01 P-08 |
| Deletion completes migration | ARC-01 (deprecate-without-delete anti-pattern) |
| EPIC-10 owns deploy dead-code purity | EPIC-08 AR-16 / `TD-EP08-001` |
| Emerging patterns named in ARC-01 OP-01…04 | ARC-01 §5 |

---

## 13. Missing decisions → Architecture Review

| ID | Open decision | Why Review |
|---|---|---|
| ARD-01 | How to satisfy Master Plan “register five new PATs” given OP-01…04 already exist and P-08 is constitutional | Registry authority / INDEX |
| ARD-02 | Whether Reconstruction Completeness remains P-08-only or also enters Pattern Registry | Naming / enforcement identity |
| ARD-03 | Authoritative `InterviewState` ownership matrix: document current writers vs redesign multi-writer clusters | State contracts |
| ARD-04 | Disposition list for dead candidates (`progress`, `dimension_signals`, `current_reasoning_decision`, `gradio_app.py`, `EvaluationBridgeDetector`, MIG scaffolding) | Delete vs keep |
| ARD-05 | PAT-06 corollary classification of suspects (capability dispatch vs workflow routing) | Boundary |
| ARD-06 | Deploy-artifact purity mechanism (delete-from-repo vs image exclude) | Ops / TD-EP08-001 |
| ARD-07 | Whether Domain Contracts + Data Model are mandatory or N/A | Category B workflow path |
| ARD-08 | `candidate_profile_v2` naming / `dimension_scores` dual-model — in or out of EPIC-10 | Scope |
| ARD-09 | Fix Projection-as-PAT-04 mislabels as docs-only vs governance | Doc hygiene |
| ARD-10 | Minimum architectural-test set for “enforced where possible” | DoD / CAR |

**ADR policy:** No new ADR at Discovery. Author ADR only if Review finds a genuine unresolved decision not covered by ARC-01 / existing ADRs.

---

## 14. Open items for next planning steps

| ID | Item | Owner step |
|---|---|---|
| OI-01 | Draft ownership matrix for all 45 fields (Review input) | Architecture Review |
| OI-02 | Classify PAT-06 corollary suspects | Architecture Review |
| OI-03 | Produce deletion milestone table for §5 inventory | Architecture Review → Freeze |
| OI-04 | Confirm Contracts/Data Model N/A or required | Architecture Review |
| OI-05 | Registry amendment plan (INDEX / Pattern Freeze / Guide) | Architecture Review |

---

## 15. Discovery outcome

| Item | Result |
|---|---|
| Architecture Discovery | **COMPLETE** |
| Category | **Category B confirmed** |
| Domain Contracts / Data Model | **Conditional** — Review (ARD-07) |
| Component Inventory | **N/A** (non-UI-bearing cleanup) |
| Assumptions | AA-01…AA-10 populated (§10) |
| Next activity | **Architecture Review** (conditional ADR) → then Freeze path |
| Code / implementation | **Not started** |

**Stop after Architecture Discovery.**
