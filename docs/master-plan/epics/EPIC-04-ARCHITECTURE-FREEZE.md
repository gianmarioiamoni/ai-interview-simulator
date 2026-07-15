# EPIC-04 — Replay UI Experience: Architecture Freeze

**Status:** ARCHITECTURE FREEZE APPROVED  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-04  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Architecture Freeze (Playbook §8.5)  
**Precondition:** EPIC-04-DATA-MODEL.md COMPLETE; all Architecture Assumptions resolved  
**Authority:** This document is the formal gate between planning and implementation. Implementation of EPIC-04 may not begin until this document declares APPROVED.

---

## 1. Architecture Decision Summary

### 1.1 New ADR Required

**Decision: No new ADR is required for EPIC-04.**

This decision is recorded here per Playbook §8.4, which states: "If no unresolved decision exists, this step is skipped and that decision is recorded in the Architecture Freeze document."

### 1.2 Rationale

The three existing ADRs fully govern every architectural decision required by EPIC-04:

| ADR | Decisions Governed | EPIC-04 Scope Covered |
|---|---|---|
| ADR-037 — Replay Engine Architecture | D1: `ReplaySession` as sole canonical artifact; D3: field sufficiency guarantee; D4: Replay Graph topology; D5: invariants I-11, I-R01–I-R09 | Sole data source for Replay UI; LLM-free enforcement; read-only constraint; sole writer |
| ADR-003 — State-Driven UI | UI derives from state; no orchestration logic in UI | Navigation state (`current_position`) is UI-scoped cursor governed by ADR-003 without modification; `UIStateMachine` extension via `ReplayContext` is state derivation, not orchestration |
| ADR-033 — Unified Report Architecture | D1: `ScoringSnapshot`; D2: `QuestionResultRecord` in `SessionHistory` | `scoring_snapshot` and `question_results` field sources for Replay UI panels |

**No decision emerged during Architecture Discovery, Domain Contracts, or Data Model authoring that was not already covered by one of these three ADRs.** Specifically:

- Navigation position management (AA-03): governed by ADR-003. No extension required.
- `ReplaySession` field sufficiency (AA-01, AA-04): verified against ADR-037 D3. No gap found.
- Read-only constraint (AA-05): governed by ADR-037 I-R07 + ADR-003.
- Responsive layout (AA-07): Gradio framework; no architectural decision. Implementation detail.
- Performance (AA-08): no architectural decision; profiling gates are implementation-phase verification.
- `UIState.REPLAY` and `ReplayContext` mechanism: UI-layer signal, not a domain contract decision; ADR-003 governs.

**Creating an ADR proactively would violate Playbook §8.4:** "Do not create ADRs proactively."

---

## 2. Architecture Evidence Summary

Every architectural conclusion is traced to its source document and section.

| Evidence Item | Source Document | Section | Status |
|---|---|---|---|
| Component Inventory (10 active components, C-11 excluded) | EPIC-04-RELAY-UI.md | §4 | PASS |
| Traceability Matrix (17 requirements, all satisfied) | EPIC-04-REPLAY-UI.md | §5 | PASS |
| ReplaySession Consumption Audit (18 root fields; 10 consumed, 8 excluded with rationale) | EPIC-04-DOMAIN-CONTRACTS.md | §5 | PASS |
| UI State Ownership Matrix (8 state entries; no duplication, no persistence, no mutation) | EPIC-04-DATA-MODEL.md | §2 | PASS |
| Rendering Ownership Matrix (all rendered fields; single-owner verified; no duplication) | EPIC-04-DATA-MODEL.md | §3 | PASS |
| Architecture Assumptions Register (8 assumptions; all VERIFIED or CONDITIONALLY VERIFIED) | EPIC-04-OVERVIEW.md | §9 | PASS |
| ADR-037 D3 field sufficiency (AA-01, AA-04) | EPIC-04-REPLAY-UI.md | §6 AA-01, AA-04 | PASS |
| ADR-003 navigation state governance (AA-03) | EPIC-04-DOMAIN-CONTRACTS.md | §2.2 | PASS |
| Read-only constraint (AA-05) | EPIC-04-DOMAIN-CONTRACTS.md | §6 | PASS |
| No LLM reachable from UI render path (AA-02) | EPIC-04-REPLAY-UI.md | §3.5; ADR-037 D5 I-11 | CONDITIONALLY PASS — enforcement test required in implementation |
| `ReplaySession` produced on demand; no UI caching (AA-06) | ADR-037 | D1 §1.4 | PASS |
| Responsive layout (AA-07) — Gradio stack confirmed | EPIC-04-DATA-MODEL.md | §6 | PASS |
| Performance model (AA-08) — O(1) navigation confirmed | EPIC-04-DATA-MODEL.md | §7 | CONDITIONALLY PASS — profiling gates required in Implementation Plan |
| ADR review outcome — no new ADR required | EPIC-04-ARCHITECTURE-FREEZE.md | §1 | PASS |
| Replay completeness — all UI panels sourced from `ReplaySession` | EPIC-04-DATA-MODEL.md | §8 | PASS |
| `InterviewState` extension NOT required | EPIC-04-DOMAIN-CONTRACTS.md | §2.2, §2.10 | PASS |
| C-11 `ReplayAuditPanel` excluded from V1.3 scope | EPIC-04-DOMAIN-CONTRACTS.md | §2.11 | PASS |
| No field gap in `ReplaySession` for EPIC-04 requirements | EPIC-04-REPLAY-UI.md | §5 | PASS |

**Evidence completeness:** All 18 evidence items are traceable to a frozen planning document. No architectural conclusion is undocumented. No contradiction exists between any two planning documents.

---

## 3. Freeze Certification

Each item is evaluated as **PASS** or **BLOCKER**. A single BLOCKER prevents Architecture Freeze approval.

| Item | Criterion | Verdict |
|---|---|---|
| Architecture Discovery | DoD §8.1 satisfied; current state vs. target state complete; Component Inventory complete; Assumptions Register populated; no code produced | **PASS** |
| Component Inventory | 10 active components (C-01 through C-10); C-11 excluded with rationale; all components have responsibility, owner, inputs, outputs, read/write capability, and `ReplaySession` fields consumed | **PASS** |
| Traceability Matrix | 17 Master Plan requirements; every requirement linked to ≥1 `ReplaySession` field, ≥1 consuming component, ≥1 verification artifact; no requirement unmet; no dead field | **PASS** |
| Domain Contracts | DoD §8.2 satisfied; all 10 components have field-level contracts; sole writer declared (`replay_node`); declared readers (Replay UI); lifecycle specified; W-01 and W-02 resolved; C-11 binary decision made | **PASS** |
| Data Model | DoD §8.3 satisfied; all open modelling questions resolved; field tables frozen (9 view models); replay completeness verified; extensibility evaluated; AA-07 VERIFIED; AA-08 CONDITIONALLY VERIFIED | **PASS** |
| ADR Review | Evaluated per Playbook §8.4; no genuine unresolved decision after Domain Contracts and Data Model; no ADR proactively created; skip decision recorded in §1 | **PASS** |
| Architecture Assumptions | 8 assumptions total; AA-01, AA-03, AA-04, AA-05, AA-06, AA-07: VERIFIED; AA-02, AA-08: CONDITIONALLY VERIFIED; none UNVERIFIED; none INVALIDATED | **PASS** |
| No BLOCKER findings | EPIC-04-RELAY-UI.md §7: zero BLOCKER findings; five WARNING findings from Architecture Discovery (W-01, W-02 resolved in Domain Contracts; W-03 resolved in Data Model as AA-07; W-04 partially resolved as AA-08 CONDITIONALLY VERIFIED; W-05 resolved in Domain Contracts §5.4) | **PASS** |
| All WARNING findings resolved or deferred | W-01: RESOLVED; W-02: RESOLVED; W-03: RESOLVED (AA-07 VERIFIED); W-04: profiling gates deferred to Implementation Plan (not a freeze blocker); W-05: RESOLVED | **PASS** |
| Exit Criteria checklist | All 8 Architecture Exit Criteria from Playbook §8.6 (minus Implementation Plan, which follows Freeze) are satisfied | **PASS** |
| Architectural contradiction check | No contradiction found across EPIC-04-REPLAY-UI.md, EPIC-04-DOMAIN-CONTRACTS.md, EPIC-04-DATA-MODEL.md, ADR-037, ADR-033, ADR-003 | **PASS** |

**BLOCKER count: 0**  
**PASS count: 11**  
**CONDITIONALLY PASS count: 0** (all conditions are implementation-phase requirements, not freeze blockers)

---

## 4. Architecture Freeze Decision

### ARCHITECTURE FREEZE: APPROVED

**Implementation of EPIC-04 may begin.**

All Architecture Exit Criteria are satisfied. No BLOCKER finding exists. All assumptions are VERIFIED or CONDITIONALLY VERIFIED. The planning document set is internally consistent. The frozen architecture is traceable to accepted ADRs. No open architectural question remains.

**Freeze scope:** All decisions documented in EPIC-04-RELAY-UI.md, EPIC-04-DOMAIN-CONTRACTS.md, and EPIC-04-DATA-MODEL.md are frozen as of this document. No modification to these documents may occur during implementation without triggering a Freeze Integrity Check (Playbook §9).

**Frozen decisions (summary):**
- `ReplaySession` is the sole data source for all Replay UI components.
- 10 active UI components (C-01 through C-10); C-11 excluded.
- Navigation state is UI-scoped ephemeral cursor (`current_position`); not persisted.
- `ReplayContext` is a UI-layer signal; `InterviewState` is not extended.
- `UIState.REPLAY` added to `UIState` enum; `UIStateMachine.resolve()` extended.
- Entry paths: report view button; session history list action.
- Responsive layout: Gradio `gr.Row`, `gr.Column`, custom CSS — no new dependency.
- 9 frozen view models (§4 of Data Model).
- 8 `ReplaySession` fields intentionally unconsumed; freeze-invariant applied.

---

## 5. Implementation Readiness

### 5.1 Prerequisites

All prerequisites are satisfied before implementation begins:

| Prerequisite | Status |
|---|---|
| `ReplaySession` frozen (`frozen=True`, `extra=forbid`, ADR-037 D3) | SATISFIED — EPIC-03 CLOSED |
| `replay_node` implemented, deterministic, LLM-free, regression-tested | SATISFIED — EPIC-03 CLOSED |
| `build_replay_graph` available and compiled | SATISFIED — `app/graph/replay_graph.py` confirmed |
| ADR-037, ADR-033, ADR-003 accepted | SATISFIED |
| No open P0/P1 findings from prior epics affecting replay contracts | SATISFIED — no findings reported |
| Architecture Freeze APPROVED | SATISFIED — this document |
| Implementation Plan accepted (§8.6 DoD) | PENDING — `EPIC-04-IMPLEMENTATION-PLAN.md` is the next required document |

### 5.2 Remaining Implementation Risks

| Risk | Classification | Mitigation |
|---|---|---|
| AA-02 — LLM invocation from Replay UI render path not yet covered by enforcement test | LOW — architectural constraint is sound; enforcement is an implementation artifact | Architectural test must be written in Phase 1: mock all LLM service interfaces; assert zero invocations during render path traversal |
| AA-08 — Load time ≤ 1s for 20-question session not yet profiled | MEDIUM — no architectural blocker identified; O(1) navigation confirmed | Implementation Plan must include a dedicated profiling phase with 20-question fixture; gate: load ≤ 1s, navigation step ≤ 100ms, memory ≤ 500 KB |
| Gradio layout rendering quality at mobile breakpoint | LOW — Gradio's CSS Flexbox handles most cases; custom CSS injection available | Implementation must verify layout at 320px viewport; fix any Gradio stacking edge case with CSS |
| `UIStateMachine.resolve()` signature change breaking existing callers | LOW — extension is additive (`replay_context=None` default) | Implementation Plan must include a regression test verifying all existing state resolution paths pass unchanged |

### 5.3 Implementation Constraints (Frozen)

The following constraints are constitutionally binding on all implementation increments:

1. **No modification to `ReplaySession`** — ADR-037 D3 §3.5; any required field addition triggers an ADR amendment and a Freeze Integrity Check.
2. **No LLM invocation from any Replay UI render path** — I-11 (ADR-037 D5); violation is a P0 architectural finding.
3. **No write to any domain artifact from any Replay UI component** — I-R07 (ADR-037 D5); read-only constraint is absolute.
4. **No persistence of `ReplaySession`, `current_position`, or `ReplayContext`** — AA-06, Data Model §2.
5. **No invocation of `replay_node` during navigation** — `ReplaySession` is held in memory for the session lifetime; re-invocation is an architectural violation.
6. **`InterviewState` must not be modified** — Domain Contracts §2.10; `ReplayContext` is the REPLAY state signal.
7. **`UIStateMachine.resolve()` extension is additive only** — the `replay_context=None` default must preserve all existing resolution paths without modification.
8. **C-11 `ReplayAuditPanel` must not be implemented** — excluded from V1.3 scope; Domain Contracts §2.11.
9. **`profile_snapshot`, `observation_store_snapshot`, `policy_versions`, `knowledge_epoch`, `manifest`, `candidate_identity_id`, `replay_mode`, `replay_level`, `schema_version` must not be rendered** — Data Model §5 freeze invariant.
10. **All implementation commits must leave the regression suite green** — Playbook §2 Zero Known Failing Tests.

### 5.4 Regression Baseline Preparation

The Implementation Plan must declare the regression baseline — the number of passing tests at the start of EPIC-04 implementation — in its first line. This is a mandatory prompt element per Playbook §10.

The baseline is derived from the regression suite state at EPIC-03 close. The Implementation Plan author must run the full test suite before authoring the commit boundary table and record the passing count.

### 5.5 Architecture Checkpoint Mandate

Per Playbook §9 and the Macro Phase Lifecycle (§3), an Architecture Checkpoint is mandatory after every completed macro phase. Each checkpoint:
- Reviews the completed phase against this Freeze document.
- Produces PASS / WARNING / BLOCKER findings.
- Explicitly authorises the next macro phase.

The Implementation Plan must define macro phase boundaries such that Architecture Checkpoints can be meaningfully applied.

---

## 6. Validation

Architecture Freeze DoD (Playbook §8.5):

- [x] All Architecture Exit Criteria satisfied (§3 Freeze Certification — all PASS)
- [x] Freeze document explicitly records that no new ADR was required and why (§1)
- [x] All Architecture Assumptions have status VERIFIED or CONDITIONALLY VERIFIED (§2 evidence table; EPIC-04-DATA-MODEL.md §10)
- [x] Traceability Matrix complete and referenced (EPIC-04-REPLAY-UI.md §5; EPIC-04-DOMAIN-CONTRACTS.md §4)
- [x] Component Inventory complete and referenced (EPIC-04-RELAY-UI.md §4)
- [x] No open issues remain as BLOCKERs in any planning document (§3)
- [x] Architecture Freeze decision explicitly declared (§4)
- [x] Implementation prerequisites stated (§5.1)
- [x] Implementation constraints frozen (§5.3)
- [x] Regression baseline preparation required (§5.4)
