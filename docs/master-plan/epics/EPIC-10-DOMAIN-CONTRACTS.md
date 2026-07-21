# EPIC-10 — Domain Contracts

**Status:** DOMAIN CONTRACTS COMPLETE — APPROVED  
**Date:** 2026-07-21  
**Epic ID:** EPIC-V13-10  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Domain Contracts (Playbook §8.2)  
**Precondition:** `EPIC-10-ARCHITECTURE-FREEZE.md` APPROVED; HEAD `29dad0dc`  
**Governing:** AR-01…AR-14; Freeze OWN-*/CLN-*/AT-*; ARC-01 OP-04 / P-08; Master Plan P-10  
**Authority:** Ownership Matrix, deletion contracts, Traceability. No redesign. No production code. No Implementation Plan.  
**Data Model:** **N/A — CERTIFIED** (§8)

---

## 1. Purpose and scope

Deliver Category B Domain Contracts required by Architecture Freeze:

- Full `InterviewState` Ownership Matrix (45 fields)
- Authorized writer sets (including explicit multi-writer sets)
- Primary readers where required for deletion / enforcement
- `candidate_profile_v2` ownership (no rename / dual-model redesign)
- Removable state-field dispositions
- Deprecated / dead artifact deletion contracts

**Out of scope:** InterviewState redesign; CandidateProfile redesign; PAT-06 scan implementation; deploy/code deletes; Data Model field tables (N/A).

---

## 2. Contract catalog

| ID | Artifact | Kind | Persistence | Notes |
|---|---|---|---|---|
| EC-IS-01 | `InterviewState` Ownership Matrix | State-contract surface | Session runtime only | Authoritative for AT-01 |
| EC-DEL-01 | Removable `InterviewState` fields | Deletion contract | None after delete | §5 |
| EC-DEL-02 | Dead production stubs | Deletion contract | Repo / deploy artifact | §6 |
| EC-DEL-03 | Migration scaffolding tests | Retirement contract | Test tree only | §6 |
| — | Live TCP fields | Existing | Runtime nullable | Keep (`session_history`, `report`, …) |

---

## 3. Ownership invariants (binding)

| ID | Invariant |
|---|---|
| I-OM-01 | Every `InterviewState` field appears exactly once in §4 Matrix |
| I-OM-02 | Only members of the authorized writer set may assign the field |
| I-OM-03 | Clear/reset privileges are listed explicitly; they do not expand semantic sole-writer sets |
| I-OM-04 | Multi-writer sets are intentional and closed (no undeclared writers) |
| I-OM-05 | Factory `create_initial` / `create_empty` may initialize session-init fields listed with Writer role **Factory** |
| I-OM-06 | No ownership redesign of navigation/UI control plane (AR-03 / OWN-04) |
| I-OM-07 | `candidate_profile_v2` rename / `dimension_scores` dual-model redesign forbidden (AR-08) |
| I-OM-08 | Field deletion only per §5 APPROVED rows |

---

## 4. InterviewState Ownership Matrix (EC-IS-01)

**Source of truth:** `domain/contracts/interview_state/base.py` (+ factory/mixins).  
**Legend:** Factory = `InterviewStateFactoryMixin.create_*`; UI = named `app/ui/state_handlers/*`; nodes = `app/graph/nodes/*`.

### 4.1 Session identity / init (Factory)

| Field | Type | Authorized writers | Primary readers | Notes |
|---|---|---|---|---|
| `interview_id` | `str` | Factory | reasoner, session_close, report, export, UI | Immutable after init |
| `role` | `Role` | Factory | adaptive_nav, eval_agg, question, session_close, written_eval, start | |
| `company` | `str` | Factory | session_close | |
| `language` | `str` | Factory | question, session_close, longitudinal | |
| `interview_type` | `InterviewType` | Factory | adaptive_nav, eval_agg, session_close, start | |
| `seniority_level` | `str` | Factory | many nodes, start | |
| `interview_length` | `int` | Factory | start UI | |
| `context_profile` | `InterviewContextProfile` | Factory | adaptive_nav, eval_agg, question, session_close | |
| `enable_humanizer` | `bool` | Factory | question_node | |
| `candidate_identity_id` | `str \| None` | Factory | reasoner, session_close, report, longitudinal, replay, UI | Write-once |

### 4.2 Removable / lifecycle candidates

| Field | Type | Authorized writers | Primary readers | Disposition |
|---|---|---|---|---|
| `progress` | `InterviewProgress` | Factory (SETUP only) | `interview_state_mapper` (weak; `is_completed` preferred); validation mixin | **DELETE** (§5) |
| `dimension_signals` | `Dict[PerformanceDimensionType, float]` | **evaluation_node** | `reasoning_context_builder`; `written_block` presenter | **KEEP** — has production readers |
| `current_reasoning_decision` | `ReasonerDecision \| None` | **reasoner_node** (set + clear) | None outside reasoner_node | **DELETE** (§5) |

### 4.3 Navigation / questions

| Field | Type | Authorized writers | Primary readers | Notes |
|---|---|---|---|---|
| `questions` | `list[Question]` | Factory; **adaptive_navigation_node** | completion, decision, eval_agg, session_close, UI | Multi-writer set |
| `asked_question_ids` | `list[str]` | Factory (init); **adaptive_navigation_node** (append) | reasoner_node | Contract authorizes nav append; Impl must align top-level writes (today nested `retrieval_memory.asked_question_ids` only) — ownership enforcement, not redesign |
| `current_question_index` | `int` | **adaptive_navigation_node** | completion, decision, question, reasoner, session_close | |
| `last_question_context` | `LastQuestionContext \| None` | **adaptive_navigation_node** | question, reasoner | |
| `planned_areas` | `list[str]` | **start** UI | adaptive_nav, completion, decision | |
| `adaptive_interview_enabled` | `bool` | **start** UI | adaptive_nav, completion, decision | |
| `retrieval_memory` | `InterviewRetrievalMemory` | **start** UI; **adaptive_navigation_node** | adaptive_nav | Multi-writer set |
| `follow_up_eligible_indices` | `FrozenSet[int]` | **start** UI | question_node | Write-once after start |

### 4.4 Answers / results / feedback

| Field | Type | Authorized writers | Primary readers | Notes |
|---|---|---|---|---|
| `answers` | `list[Answer]` | **submit** UI (`add_answer`) | question, session_close | |
| `results_by_question` | `dict[str, QuestionResult]` | **evaluation_node**; **execution_node**; **written_evaluation_node**; **hint_node**; **adaptive_navigation_node** (clear on RETRY) | many nodes, session_close | **Authorized multi-writer set** (fan-in + clear privilege) |
| `last_feedback_bundle` | `FeedbackBundle \| None` | **feedback_node** (semantic sole writer); **adaptive_navigation_node** (clear only) | decision, question, navigation | Clear privilege explicit |
| `chat_history` | `list[str]` | **question_node** | question_node | |
| `events` | `list[InterviewEvent]` | **question_node** | question_node | |
| `question_display_text` | `str \| None` | **question_node**; **adaptive_navigation_node** (clear) | UI display | Clear privilege |
| `follow_up_count` | `int` | **question_node** | question_node | |
| `last_humanizer_follow_up` | `bool` | **question_node** | question_node | |

### 4.5 Scoring / reasoner / closure TCP

| Field | Type | Authorized writers | Primary readers | Notes |
|---|---|---|---|---|
| `scoring_snapshot` | `ScoringSnapshot \| None` | **evaluation_aggregate_node** | eval_agg guard, session_close | |
| `scoring_narrative` | `ScoringNarrative \| None` | **evaluation_aggregate_node** | session_close | |
| `interview_metrics` | `InterviewMetrics \| None` | **evaluation_aggregate_node** | session_close | |
| `interview_cost_metrics` | `InterviewCostMetrics \| None` | **evaluation_aggregate_node** | session_close | |
| `interview_memory` | `InterviewMemory` | **reasoner_node** | reasoner_node | ADR-032 / OP-04 |
| `observation_store` | `ObservationStore \| None` | **reasoner_node** | reasoner, session_close | Arch-tested |
| `candidate_profile_v2` | `CandidateProfile \| None` | **reasoner_node** | reasoner, session_close | **Ownership only** — no rename/redesign (AR-08) |
| `session_history` | `SessionHistory \| None` | **session_close_node** | report, longitudinal, replay loader | Keep (live TCP) |
| `report` | `Report \| None` | **report_node** | UI builders/mapper/state machine | Keep (live TCP) |

### 4.6 Control / UI plane (authorized multi-writer sets)

| Field | Type | Authorized writers | Primary readers | Notes |
|---|---|---|---|---|
| `awaiting_user_input` | `bool` | decision_node; adaptive_navigation_node; start; submit; navigation UI | completion, UI | Documented multi-writer |
| `intent` | `ActionType \| None` | decision_node; adaptive_navigation_node; eval_agg; start; submit; navigation UI | start_processing, eval/exec/feedback | Documented multi-writer |
| `is_processing` | `bool` | start_processing_node; decision_node; report_node; start; submit; navigation UI | UI builders | Documented multi-writer |
| `current_step` | `LoaderStep \| None` | start_processing; execution; evaluation; feedback; adaptive_nav; eval_agg; report; start; submit; navigation UI | UI builders | Documented multi-writer |
| `current_progress` | `int` | start; submit; navigation UI | UI handlers | UI-plane |
| `allowed_actions` | `list[ActionType]` | decision_node; adaptive_navigation_node (clear) | UI navigation | |
| `is_completed` | `bool` | **completion_node** | eval_agg, export | |

**Matrix coverage count:** 45 / 45 fields.

---

## 5. Removable state fields (EC-DEL-01)

| Field | Proof | Decision | Durable shape impact |
|---|---|---|---|
| `progress` | Never advanced past SETUP; production completion uses `is_completed`; mapper equality is stale | **DELETE APPROVED** | **None** — not on SessionHistory/Report |
| `dimension_signals` | Production readers: reasoner context builder + written feedback presenter | **KEEP** (overturns Freeze conditional delete) | N/A |
| `current_reasoning_decision` | Written/cleared only by reasoner_node; no outside production readers | **DELETE APPROVED** | **None** — transient runtime only |

**Impl obligations on DELETE:** remove field + fix compile/test breakages; update mapper off `progress`; remove orphan reasoner write of `current_reasoning_decision` (or delete with field).

---

## 6. Deprecated / dead artifacts (EC-DEL-02 / EC-DEL-03)

| Artifact | Authorized “owner” (disposition) | Decision | Notes |
|---|---|---|---|
| `gradio_app.py` | EPIC-10 cleanup (CLN-01) | **DELETE** | Deploy purity |
| `EvaluationBridgeDetector` + dedicated tests | EPIC-10 cleanup (CLN-02) | **DELETE** | Registry already excludes |
| Obsolete MIG/TCP scaffolding tests (transitional dual-path only) | EPIC-10 cleanup (CLN-04) | **RETIRE** | Keep tests that still guard live invariants |
| Live TCP fields (`session_history`, `report`, `observation_store`, `candidate_profile_v2`, `candidate_identity_id`) | Existing node owners (§4.5) | **KEEP** | |
| `InterviewState.report_output` (docs claim) | N/A — not on state | **DOCS CORRECT** (CLN-07) | UI `report_output` HTML surface unrelated |
| CandidateProfile `dimension_scores` dual-model | Out of scope (AR-08) | **KEEP / TD** | Not EPIC-10 delete |

---

## 7. `candidate_profile_v2` ownership (binding)

| Aspect | Contract |
|---|---|
| Field | `InterviewState.candidate_profile_v2: CandidateProfile \| None` |
| Authorized writer | **reasoner_node** only (via KnowledgePipeline / CandidateProfileBuilder path) |
| Primary readers | reasoner_node; session_close_node |
| Lifecycle | Session-scoped; nullable until first successful KP cycle; updated each reasoner cycle |
| Forbidden | Rename; remove `dimension_scores`; dual-model semantic migration (AR-08) |

---

## 8. Data Model decision — N/A CERTIFIED

| Check | Result |
|---|---|
| Do APPROVED deletions participate in `SessionHistory`? | **No** |
| Do APPROVED deletions participate in `Report` / `schema_version`? | **No** |
| Does Ownership Matrix change durable serialization? | **No** |
| Stub/scaffolding deletes change stored shape? | **No** |

**Certification:** **Data Model = N/A** for EPIC-V13-10.  
**Exception path (Freeze AR-07):** If implementation discovers durable-shape coupling, **stop** and author Data Model before Impl Plan acceptance.

---

## 9. Traceability Matrix

| Master Plan / Freeze requirement | Contract | Consuming / enforcing component | Verification |
|---|---|---|---|
| P-10 / zero fields without declared owner | EC-IS-01 §4 | All graph nodes + UI state handlers | AT-01 |
| OP-04 Sole Writer (authorized sets) | I-OM-02…04 | Ownership Matrix | AT-01 |
| Formalize emerging patterns / five new | AR-01/02 (Freeze REG-*) | INDEX Official Patterns | AT-04 |
| Reconstruction Completeness | P-08 (reuse prior) | Replay/longitudinal builders | AT-06 |
| Deprecated without milestone → delete | EC-DEL-01/02 | Repo + deploy | AT-02, AT-07 |
| PAT-06 corollary | Freeze §7.1 | Services allowlist | AT-03 |
| Deploy dead-code purity TD-EP08-001 | EC-DEL-02 + AR-06 | Docker / `.dockerignore` | AT-07 |
| `candidate_profile_v2` ownership | §7 | reasoner_node | AT-01 |
| No CandidateProfile redesign | I-OM-07 / AR-08 | Impl Plan scope | CAR Traceability |
| Projection ≠ PAT-04 | AR-09 | `domain/contracts/report` | AT-05 |
| Delete `progress` / `current_reasoning_decision` | EC-DEL-01 | InterviewState + callers | AT-01 + unit/regression |
| Keep `dimension_signals` | §4.2 / §5 | evaluation_node + readers | AT-01 |

---

## 10. Assumptions touched

| ID | Status after Contracts |
|---|---|
| AA-02 | **VERIFIED** — Contracts delivered; Data Model N/A certified |
| AA-10 | **VERIFIED** — Matrix complete 45/45 |
| Freeze CLN-03 | **Amended by evidence** — `dimension_signals` KEEP; other two DELETE APPROVED |

---

## 11. Approval decision

| Item | Result |
|---|---|
| Domain Contracts | **APPROVED** |
| Ownership Matrix | **COMPLETE** (45/45) |
| Data Model | **N/A — CERTIFIED** |
| Redesign | **None** |
| Next | Implementation Plan (acceptance now unblocked for Contracts gate; coding still requires accepted Impl Plan) |
| Production code | **Not modified** |

**Stop after Domain Contracts.**
