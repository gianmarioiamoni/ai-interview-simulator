# EPIC-03 — Replay Engine

**Status:** PLANNING — Category B Architectural Vision  
**Date:** 2026-07-15  
**Epic ID:** EPIC-V13-03  
**Playbook Category:** B — Major Architectural Epic  
**Precondition:** EPIC-01 CLOSED; EPIC-02 CLOSED; regression suite green; working tree clean.  
**Authority:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-03; ARC-01; ADR-033; ADR-034.

---

## 1. Vision

EPIC-03 implements `replay_node` — the closed, non-LLM reconstruction pipeline that transforms a persisted `SessionHistory` into a navigable `ReplaySession` deterministically.

The replay capability is architecturally the closure of the platform's accumulation / closure / projection cycle. EPIC-01 established `Report` as the sole scoring artifact. EPIC-02 established `LongitudinalProfile` as the cross-session accumulation record. EPIC-03 makes every stored session fully inspectable by the candidate without any live computation.

Replay is not a diagnostic or operator tool. It is a candidate-facing product feature: question-by-question navigation of a completed session from stored artifacts. The architecture is designed to guarantee that navigation is deterministic, LLM-free, and isolated from the live runtime.

---

## 2. Product Goals

EPIC-03 delivers the following product goals from V13-PRODUCT-MASTER-PLAN.md:

**P-03 — Replay Engine**  
Implement `replay_node` as a closed, non-LLM reconstruction pipeline. Activate `ReplayFeatureEngine` contracts defined in V1.2. The node consumes `SessionHistory` and produces a `ReplaySession` deterministically. The reconstruction is idempotent.

**P-04 — Replay UI Experience (input contract)**  
`ReplaySession` is the sole input contract for the Replay UI (EPIC-04). EPIC-03 is responsible for the data shape of every field the Replay UI will render. EPIC-04 cannot begin until EPIC-03 Architecture Freeze passes.

Domain invariant I-11 ("Replay never invokes LLM calls") must be enforced by an architectural test produced by this epic.

---

## 3. Current Architecture

### 3.1 What Exists (V1.2 Closure)

The following replay contracts were defined and frozen in V1.2:

| Contract | Location | Status |
|---|---|---|
| `ReplayContext` | `domain/contracts/replay/replay_context.py` | Frozen (ADR-026 §B6) |
| `ReplayResult` | `domain/contracts/replay/replay_result.py` | Frozen (ADR-026 §B6) |
| `ReplayManifest` | `domain/contracts/replay/replay_manifest.py` | Frozen (ADR-026 §D) |
| `ReplaySession` | `domain/contracts/replay/replay_session.py` | Defined — assembly logic present |
| `ReplayValidator` | `domain/contracts/replay/replay_validator.py` | Frozen |
| `ReplayStatistics` | `domain/contracts/replay/replay_statistics.py` | Frozen |
| `ReplayLevel`, `ReplayMode`, `ReplaySourcePriority` | `domain/contracts/replay/replay_enums.py` | Frozen (ADR-026 §B2, §B3, §B5) |
| `CandidateProfileSnapshot` | `domain/contracts/knowledge_snapshot/` | Frozen (ADR-032) |

`ReplaySession` (as currently implemented) assembles a `ReplayResult` from a `ReplayContext` that carries a `KnowledgeSnapshot`. It reads `profile_snapshot`, `narrative`, `coaching_snapshot`, and `policy_versions` directly from the snapshot. No LLM calls. No `FeatureEngine` invocation. No live pipeline access.

### 3.2 What Does Not Exist

| Missing Component | Consequence |
|---|---|
| `replay_node` (LangGraph node) | No replay execution path in the session graph |
| `ReplayFeatureEngine` | Reserved in V1.2 contracts; not activated |
| Per-question replay data path | `ReplayResult` carries `profile_snapshot`, `narrative`, `coaching_snapshot` — but not `question_results` or `scoring_snapshot` from `SessionHistory` v2.0 (introduced by EPIC-01) |
| `ReplaySession` → `SessionHistory` v2.0 integration | `ReplayContext` was designed against V1.2 `KnowledgeSnapshot`; `SessionHistory` v2.0 adds `question_results` and `scoring_snapshot` which are not surfaced in the current `ReplayResult` |
| Architectural test for I-11 | No test asserts that `replay_node` makes zero LLM calls |

### 3.3 Gap Summary

The V1.2 replay contracts form a structurally correct foundation. The primary gaps are:

1. **LangGraph integration gap:** No `replay_node`. Replay has no presence in the session graph.
2. **SessionHistory v2.0 gap:** `ReplayResult` was designed against `KnowledgeSnapshot`. It does not surface `question_results` (introduced by EPIC-01 ADR-033 Decision 2) or `scoring_snapshot` (ADR-033 Decision 1). The Replay UI (EPIC-04) requires per-question data and scoring for its rendering contract.
3. **ReplayFeatureEngine activation gap:** The `ReplayFeatureEngine` type is referenced in V1.2 contracts but is not implemented as an active component.
4. **Invariant enforcement gap:** Domain invariant I-11 is declared but not tested.

---

## 4. Target Architecture

### 4.1 Architectural Position

`replay_node` is positioned **outside** the live session graph. It is not a step in the interview session close cascade. It is a separate, independently invocable LangGraph node that:

- Is triggered on demand (by the Replay UI, or an operator) for a stored `session_id`.
- Reads from persisted `SessionHistory` only.
- Produces `ReplaySession` as its output artifact.
- Has zero dependency on `InterviewState` live fields.
- Has zero dependency on `LongitudinalProfile` (ADR-034 Decision 7).

### 4.2 Node Contract

```
replay_node
  Input:   session_id (lookup key) → SessionHistory (loaded from persistence)
  Output:  ReplaySession (frozen, immutable reconstruction artifact)

  Invariants:
  - Never invokes FeatureEngine (live)
  - Never invokes NarrativeGenerator
  - Never invokes CoachingEngine
  - Never invokes any LLM-backed service
  - Never writes to SessionHistory
  - Never writes to LongitudinalProfile
  - ReplayFeatureEngine is the only engine permitted
```

### 4.3 ReplaySession Target Shape

`ReplaySession` is the V1.3 output artifact of `replay_node`. It extends or replaces `ReplayResult` (V1.2) to surface all data required by the Replay UI (EPIC-04):

| Section | Source in SessionHistory |
|---|---|
| `profile_snapshot` | `session_history.knowledge_snapshot.profile_snapshot` |
| `narrative` | `session_history.knowledge_snapshot.narrative` |
| `coaching_snapshot` | `session_history.knowledge_snapshot.coaching_snapshot` |
| `scoring_snapshot` | `session_history.scoring_snapshot` (EPIC-01 ADR-033 Decision 1) |
| `question_results` | `session_history.question_results` (EPIC-01 ADR-033 Decision 2) |
| `session_metadata` | `session_history.interview_metadata` |
| `manifest` | `ReplayManifest` (produced by `replay_node`) |
| `policy_versions` | `session_history.knowledge_snapshot.policy_versions` |

**All fields are read-only reconstructions. No field is computed, derived, or LLM-generated at replay time.**

### 4.4 Data Flow

```
Candidate / Operator Request
    │ session_id
    ▼
replay_node
    │
    ├── Load SessionHistory from persistence (read-only)
    │       └── SessionHistory v2.0:
    │           ├── knowledge_snapshot (profile_snapshot, narrative, coaching_snapshot)
    │           ├── scoring_snapshot: Optional[ScoringSnapshot]
    │           ├── question_results: tuple[QuestionResultRecord, ...]
    │           ├── interview_metadata
    │           └── transcript
    │
    ├── ReplayFeatureEngine (read stored features; no recomputation)
    │
    ├── ReplaySessionBuilder
    │       └── assembles ReplaySession from all SessionHistory fields
    │
    ▼
ReplaySession (frozen, immutable)
    │
    ▼
Replay UI (EPIC-04) — read-only navigation, no submission, no LLM calls
```

### 4.5 Node Lifecycle

`replay_node` follows the Cascading Closure pattern (OP-01):

- Non-fatal: if `SessionHistory` cannot be loaded, emits `WARNING` log and returns a failed `ReplaySession` with `is_successful=False`.
- Write-once: `ReplaySession` is produced once per invocation. No incremental updates.
- Idempotent: calling `replay_node` twice for the same `session_id` produces identical `ReplaySession` output.
- LLM-free: enforced by architectural test (I-11).

---

## 5. Scope

The following are in scope for EPIC-03:

1. **`replay_node` implementation** — LangGraph node that loads `SessionHistory` and produces `ReplaySession`.
2. **`ReplaySession` contract extension** — extend or replace `ReplayResult` to carry `scoring_snapshot` and `question_results` fields from `SessionHistory` v2.0.
3. **`ReplaySessionBuilder`** — sole builder for `ReplaySession`; `frozen=True`; `extra=forbid`.
4. **`ReplayFeatureEngine` activation** — implement the V1.2-reserved `ReplayFeatureEngine` as a read-only reconstruction component; it reads stored features from `CandidateProfileSnapshot`, never invokes live `FeatureEngine`.
5. **`SessionHistory` v2.0 integration** — surface all fields introduced by EPIC-01 (ADR-033) in the replay output.
6. **Architectural invariant test (I-11)** — test that `replay_node` execution produces zero LLM calls, enforced by mocking all LLM service interfaces.
7. **Reconstruction completeness validation** — test that every field of `ReplaySession` is explicitly populated (Reconstruction Completeness PAT, P-08).

---

## 6. Out of Scope

| Feature | Target | Reason |
|---|---|---|
| Re-submission of answers in replay | V2+ | Read-only replay is the V1.3 commitment |
| Comparative replay (two sessions side by side) | V2+ | Requires cohort context and UX investment beyond V1.3 |
| AI commentary during replay | V2+ | Would introduce LLM call — violates I-11 |
| Replay UI (rendering layer) | EPIC-04 | UI is a separate epic; EPIC-03 delivers the data contract only |
| `LongitudinalProfile` access from replay | Prohibited | ADR-034 Decision 7 — replay reconstructs from SessionHistory only |
| Live `FeatureEngine` invocation during replay | Prohibited | Architectural invariant; constitutional (P-01) |
| Replay-triggered `SessionHistory` mutation | Prohibited | Replay is read-only |
| Replay from incomplete sessions | Out of scope | Only fully closed `SessionHistory` records are replayable |
| `GoalTrack` integration | V2 stretch | Not a V1.3 commitment per Master Plan §6 |

---

## 7. Runtime Topology

### 7.1 Graph Position

`replay_node` is **not** part of the live interview session graph. It is a separate, independently invocable graph path:

```
[Live Session Graph]
start_processing → question → evaluation → reasoner → ... → session_close → report → longitudinal_update → END

[Replay Graph — separate invocation path]
replay_node (input: session_id) → END
```

No node in the live session graph invokes or depends on `replay_node`. No node in `replay_node` reads from `InterviewState` live fields. The graphs are topologically independent.

### 7.2 Isolation Requirements

- `replay_node` must not be registered as a node in the live session graph.
- `replay_node` must not share `InterviewState` with any live session node.
- `replay_node` reads exclusively from the persistence layer (closed `SessionHistory`).
- `replay_node` is the sole writer of `ReplaySession`. No other node may produce or write `ReplaySession`.

### 7.3 Concurrency

Multiple concurrent `replay_node` invocations for different `session_id` values are permitted. All reads are from closed, immutable `SessionHistory` records. No write lock is required. No session-level synchronization is needed.

---

## 8. Replay Lifecycle

```
1. Request arrives with session_id
        ↓
2. replay_node loads SessionHistory from persistence
        ↓ (fail: SessionHistory not found → ReplaySession(is_successful=False, failure_reason=...))
3. ReplayValidator validates SessionHistory completeness
        ↓ (fail: incomplete history → ReplaySession(is_successful=False))
4. ReplayFeatureEngine reads stored features from CandidateProfileSnapshot
        (no recomputation; read-only pass)
        ↓
5. ReplaySessionBuilder assembles ReplaySession:
        - profile_snapshot ← knowledge_snapshot.profile_snapshot
        - narrative ← knowledge_snapshot.narrative
        - coaching_snapshot ← knowledge_snapshot.coaching_snapshot
        - scoring_snapshot ← session_history.scoring_snapshot
        - question_results ← session_history.question_results
        - session_metadata ← session_history.interview_metadata
        - policy_versions ← knowledge_snapshot.policy_versions
        - manifest ← ReplayManifest (constructed by replay_node)
        ↓
6. Reconstruction completeness validation (P-08)
        ↓ (fail: any field missing → RuntimeError, not silent default)
7. Return ReplaySession (frozen, immutable)
        ↓
8. Replay UI (EPIC-04) consumes ReplaySession — read-only
```

**Every step is fail-fast (P-06). No silent fallbacks. No partial reconstructions.**

---

## 9. Ownership Model

| Artifact | Sole Producer | Sole Writer | Declared Readers |
|---|---|---|---|
| `ReplaySession` | `ReplaySessionBuilder` | `replay_node` | Replay UI (EPIC-04), architectural tests |
| `ReplayManifest` | `replay_node` (assembles `ReplayManifest`) | `replay_node` | Embedded in `ReplaySession` |
| `ReplayFeatureEngine` output | `ReplayFeatureEngine` | `replay_node` (passed to builder) | `ReplaySessionBuilder` |

**`replay_node` is constitutionally required to be the sole writer of `ReplaySession`.** No other node, service, or pipeline may produce or write a `ReplaySession`.

`replay_node` is **read-only** with respect to all other artifacts:
- It reads `SessionHistory` from persistence — never writes it.
- It reads `CandidateProfileSnapshot` — never writes it.
- It has zero `InterviewState` fields declared as write targets.
- It has zero dependency on `LongitudinalProfile`.

---

## 10. Replay Boundaries

### 10.1 Computation / Projection Boundary (ARC-01 P-01)

Replay is a controlled exception to P-01. It is permitted to perform bounded recomputation under the following strict conditions (ARC-01 §7):

- Uses `ReplayFeatureEngine` exclusively — not the live `FeatureEngine`.
- Reads only from closed `SessionHistory` artifacts.
- Does not write to `InterviewState` fields owned by live nodes.
- Context declares `is_replay=True`.
- Introduction is governed by an ADR crossing the Replay Boundary.

In V1.3, `ReplayFeatureEngine` reads stored features from `CandidateProfileSnapshot`. It does not run the live feature derivation algorithm. It is a read-pass, not a computation pass. This keeps replay within the spirit of P-01: no LLM calls, no live knowledge computation.

### 10.2 Replay Boundary (ARC-01 §3)

The Replay Boundary separates the live computation path from the controlled reconstruction path. EPIC-03 must not cross this boundary in either direction:

- No live-path engine (`FeatureEngine`, `NarrativeGenerator`, `CoachingEngine`) may be invoked on historical data.
- No replay-path engine (`ReplayFeatureEngine`) may be invoked on live session data.
- The `ReplayContext` must carry `is_replay=True` when surfaced in any API.

### 10.3 Longitudinal Boundary (ADR-034 Decision 7)

`replay_node` and all replay contracts must have **zero dependency** on `LongitudinalProfile`. The boundary is bidirectional:

- No replay contract may import or reference `LongitudinalProfile`.
- No `LongitudinalProfile` contract may import or reference any replay contract.

If the Replay UI (EPIC-04) displays a progress trend panel, that data is sourced separately from `LearningProgress` — never through the replay path.

### 10.4 Isolation from Runtime Mutation

`replay_node` may not:
- Write to any `InterviewState` field.
- Trigger any live session pipeline.
- Produce any artifact that could be consumed by a live session node.

Any violation of this boundary is a constitutional violation (P-02, P-01).

---

## 11. Dependencies

### 11.1 Hard Dependencies (blockers)

| Dependency | Why Required | Status |
|---|---|---|
| EPIC-01 CLOSED | `ReplaySession` must surface `scoring_snapshot` (ADR-033 Decision 1) and `question_results` (ADR-033 Decision 2) from `SessionHistory` v2.0. These fields do not exist in `SessionHistory` v1.x. | CLOSED |
| `SessionHistory` v2.0 (`schema_version = "2.0"`) | Required field set (see §4.3) | Active (EPIC-01 delivered) |
| `CandidateProfileSnapshot` (ADR-032) | `ReplayFeatureEngine` reads from it | Frozen |
| `KnowledgeSnapshot` (ADR-022) | Primary source for profile, narrative, coaching in replay | Frozen |
| `ReplayContext`, `ReplayResult`, `ReplayManifest` (ADR-026) | V1.2 replay contracts — foundation for V1.3 extension | Frozen |
| ARC-01 Architecture Constitution | Governs all constraints | Active |

### 11.2 Soft Dependencies (informational)

| Dependency | Nature |
|---|---|
| EPIC-02 | No data dependency; `replay_node` does not read `LongitudinalProfile`. EPIC-02 and EPIC-03 may proceed in parallel. |
| EPIC-04 (Replay UI) | EPIC-04 depends on `ReplaySession` contract from EPIC-03. EPIC-04 cannot begin Architecture Freeze until EPIC-03 Architecture Freeze passes. |
| EPIC-05 (Unified Report) | May link to `ReplaySession` (as a replay entry point in the report). Dependency is unidirectional: EPIC-05 reads EPIC-03 output. |

### 11.3 ADR Dependencies

| ADR | Content Relevant to EPIC-03 |
|---|---|
| ADR-026 | Replay Snapshot Model — defines `ReplayContext`, `ReplayResult`, `ReplayManifest`, source priority hierarchy |
| ADR-032 | `CandidateProfileSnapshot` — the primary knowledge artifact read by replay |
| ADR-033 (Decision 1, 2) | `ScoringSnapshot` and `question_results` — fields EPIC-03 must surface in `ReplaySession` |
| ADR-034 (Decision 7) | Explicit prohibition on replay consuming `LongitudinalProfile` |

---

## 12. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `ReplaySession` field set is insufficient for EPIC-04 Replay UI rendering | Medium | High — blocks EPIC-04 | Define `ReplaySession` contract in Domain Contracts document with explicit sign-off from EPIC-04 requirements; review against Replay UI wireframes before Architecture Freeze |
| `ReplayFeatureEngine` scope exceeds "read-pass" and introduces live computation | Low | High — constitutional violation | Explicitly constrain `ReplayFeatureEngine` in ADR to read-only access of stored `CandidateProfileSnapshot` fields; enforce by architectural test |
| `question_results` field set from `SessionHistory` v2.0 is incomplete for per-question display | Low | Medium | Verify `QuestionResultRecord` field set (ADR-033 Decision 2) covers all Replay UI question-level rendering requirements before Domain Contracts are frozen |
| Replay reconstruction non-determinism (stored feature values are ambiguous) | Low | High | Require explicit field-level declaration for every `ReplaySession` reconstruction path (P-08 — Reconstruction Completeness); enforce by test that verifies all fields are explicitly populated |
| `replay_node` accidentally shares context with live session nodes | Low | High — constitutional violation | Architectural test verifies `replay_node` module imports no live session node; `ReplayContext.is_replay=True` assertion enforced at entry |
| `SessionHistory` v2.0 `scoring_snapshot` is `Optional` — replay for sessions without scoring data | Medium | Low | `ReplaySession.scoring_snapshot` is `Optional[ScoringSnapshot]`; Replay UI (EPIC-04) must handle `None` with a defined fallback state; this is an EPIC-04 rendering concern, not a reconstruction concern |
| ADR-026 `ReplayLevel.REASONING` reserved status creates confusion | Low | Low | Document explicitly in EPIC-03 Domain Contracts that `ReplayLevel.REASONING` remains reserved in V1.3; `replay_node` supports `PRESENTATION` and `KNOWLEDGE` levels only |

---

## 13. Success Criteria

EPIC-03 is complete when all of the following are satisfied:

### Architecture
- [ ] `replay_node` is implemented as a LangGraph node with a declared sole write target (`ReplaySession`).
- [ ] `replay_node` is not registered in the live session graph.
- [ ] `ReplaySession` is `frozen=True`, `extra=forbid`, with a single builder (`ReplaySessionBuilder`).
- [ ] `ReplayFeatureEngine` is implemented as a read-only reconstruction component; no live `FeatureEngine` invocation.
- [ ] Every `ReplaySession` field is explicitly populated by `ReplaySessionBuilder` (Reconstruction Completeness, P-08).
- [ ] `ReplaySession` surfaces `scoring_snapshot` and `question_results` from `SessionHistory` v2.0.
- [ ] No replay contract imports or references `LongitudinalProfile` (ADR-034 Decision 7).
- [ ] No `LongitudinalProfile` contract imports or references any replay contract.

### Testing
- [ ] Architectural test verifies domain invariant I-11: zero LLM service calls during `replay_node` execution across all test fixtures.
- [ ] Architectural test verifies Reconstruction Completeness: every field of `ReplaySession` is explicitly enumerated in `ReplaySessionBuilder.build()`.
- [ ] `replay_node` reconstructs stored sessions deterministically across ≥ 20 test fixtures.
- [ ] Failure paths are tested: missing `SessionHistory`, incomplete `KnowledgeSnapshot`, `None` `scoring_snapshot`.
- [ ] Full regression suite passes with zero failures.

### Product
- [ ] `ReplaySession` field set is sufficient for all EPIC-04 Replay UI rendering requirements (verified by review before Architecture Freeze).
- [ ] Reconstruction is idempotent: calling `replay_node` twice for the same `session_id` produces identical `ReplaySession`.

---

## 14. Architectural Review Triggers

The following events require an Architecture Review or ADR before implementation may continue:

| Trigger | Required Action |
|---|---|
| Any proposed addition of LLM call inside `replay_node` or any component it invokes | Full ADR crossing the Computation/Projection Boundary + constitutional exception (invariant I-11 must be updated) |
| Any proposed access to `LongitudinalProfile` from replay contracts | Full ADR crossing the Replay Boundary; ADR-034 Decision 7 must be explicitly amended |
| Any proposed mutation of `SessionHistory` by `replay_node` | Full ADR crossing the Ownership Boundary |
| Addition of a second builder for `ReplaySession` | Full ADR crossing the Builder Boundary (P-05 violation without ADR) |
| Registration of `replay_node` in the live session graph | Full ADR with isolation analysis |
| Any `ReplaySession` field sourced from `InterviewState` live fields (not `SessionHistory`) | Full ADR — violates replay isolation invariant |
| Discovery that `SessionHistory` v2.0 `question_results` is structurally insufficient for EPIC-04 | Stop immediately; return to ADR phase; do not add workaround fields to `ReplaySession` |
| Any unresolved architectural question during implementation | Stopping Rule applies (V13-DEVELOPMENT-PLAYBOOK.md §8) |

---

## 15. Relationship with Previous EPICs

### EPIC-01 (Scoring Pipeline Migration) — CLOSED

EPIC-03 depends on EPIC-01 in two structural ways:

1. **`scoring_snapshot` field:** `ReplaySession` must surface `SessionHistory.scoring_snapshot: Optional[ScoringSnapshot]` — a field introduced by EPIC-01 (ADR-033 Decision 1). This field does not exist in `SessionHistory` v1.x. EPIC-03 requires EPIC-01 to be closed before its Domain Contracts can be finalized.

2. **`question_results` field:** `ReplaySession` must surface per-question data from `SessionHistory.question_results: tuple[QuestionResultRecord, ...]` — introduced by EPIC-01 (ADR-033 Decision 2). The Replay UI depends on this for question-by-question navigation with full data.

EPIC-01 is CLOSED. Both fields are active. EPIC-03 may proceed to the Architecture Governance step.

### EPIC-02 (Cross-Session Profile Continuity) — CLOSED

EPIC-03 has **no data dependency** on EPIC-02. ADR-034 Decision 7 explicitly prohibits replay from consuming `LongitudinalProfile`. The replay path is constitutionally session-scoped.

EPIC-02 and EPIC-03 may proceed in parallel (Master Plan §8 Phase 2). EPIC-02 is CLOSED. EPIC-03 inherits no debt from EPIC-02.

### Relationship with Downstream EPICs

| Epic | Relationship |
|---|---|
| EPIC-04 (Replay UI) | EPIC-04 consumes `ReplaySession`. EPIC-04 Architecture Freeze cannot begin until EPIC-03 Architecture Freeze passes. |
| EPIC-05 (Unified Report) | EPIC-05 links to replay via a `ReplaySession` entry point in the report. EPIC-05 does not read `ReplaySession` contents — it links to it. |
| EPIC-09 (Performance Baseline) | Replay load SLO: < 1s for any stored session (Master Plan EPIC-V13-09). EPIC-03 must not introduce reconstruction that violates this SLO. |

---

## 16. Expected Implementation Phases (High-Level)

This section is indicative only. Detailed commit boundary planning follows in the Implementation Plan (produced after Architecture Freeze).

### Phase 1 — Architecture Governance

Author and accept the EPIC-03 ADR set. Identify all decisions not already covered by ADR-026, ADR-032, ADR-033, ADR-034. Specifically:

- Decision: exact shape of `ReplaySession` (extending `ReplayResult` vs. new artifact).
- Decision: `ReplayFeatureEngine` scope and read-only constraint.
- Decision: `ReplayLevel.REASONING` continued reservation.
- Decision: `replay_node` graph topology (separate graph vs. independent invocation).

### Phase 2 — Domain Contracts

Specify `ReplaySession`, `ReplaySessionBuilder`, and any `ReplaySession`-specific validator contracts. Verify `SessionHistory` v2.0 field set sufficiency. Freeze replay-specific field additions if any are needed.

### Phase 3 — Data Model Specification

Freeze the field tables for `ReplaySession`. Verify replay completeness (every `ReplaySession` field traces to a `SessionHistory` field). Verify EPIC-04 rendering requirements against the frozen `ReplaySession` field set.

### Phase 4 — Architecture Freeze

Formal gate: all decisions frozen, all contracts frozen, all data model decisions closed. No implementation begins before this gate passes.

### Phase 5 — Implementation (incremental)

Ordered by dependency:
1. `ReplayFeatureEngine` (foundation — no LangGraph dependency).
2. `ReplaySessionBuilder` + `ReplaySession` contract (foundation — no LangGraph dependency).
3. `replay_node` (depends on builder and feature engine).
4. Architectural tests (I-11, Reconstruction Completeness, idempotency, determinism).
5. Integration with session graph (registration as independent invocation path).

Every phase must satisfy the Zero Known Failing Tests rule (V13-DEVELOPMENT-PLAYBOOK.md §2).

### Phase 6 — CAR + Regression + Epic Close

Construction Architecture Review against ARC-01 and EPIC-03 ADRs. Full regression suite. Documentation update. Final Review. Epic Close.

---

## Open Issues

At the time of this planning document, the following issues require resolution before Architecture Freeze:

| ID | Issue | Resolution Path |
|---|---|---|
| OI-01 | Whether `ReplaySession` extends `ReplayResult` (V1.2) or replaces it as a new artifact. Extending preserves V1.2 test coverage but may require backward-incompatible field additions. Replacing enables a clean V1.3 definition but requires migration of V1.2 replay tests. | Resolved by EPIC-03 ADR (Phase 1). |
| OI-02 | Whether `ReplayFeatureEngine` performs any derivation (e.g., quality score recomputation from stored feature values) or is strictly a read-pass of stored fields. This affects whether `ReplayFeatureEngine` crosses the Computation/Projection Boundary. | Resolved by EPIC-03 ADR (Phase 1). If any derivation is introduced, an ADR crossing the Computation/Projection Boundary is required. |
| OI-03 | The exact set of `ReplaySession` fields required by EPIC-04 Replay UI rendering. The current plan assumes `scoring_snapshot`, `question_results`, `narrative`, `coaching_snapshot`, `profile_snapshot`, and `session_metadata`. Unverified against EPIC-04 wireframes. | Resolved by Domain Contracts review (Phase 2), signed off before Architecture Freeze. |
| OI-04 | Whether `replay_node` is registered as a standalone LangGraph graph or as a node in a replay-specific sub-graph. The topology affects how EPIC-04 triggers replay and how errors propagate. | Resolved by EPIC-03 ADR (Phase 1). |

**No open issue may remain unresolved at Architecture Freeze.** All OI items must be closed in the ADR or Domain Contracts documents before the freeze is declared.

---

*This document is the authoritative planning vision for EPIC-03 — Replay Engine. It governs all subsequent EPIC-03 planning documents (ADR, Domain Contracts, Data Model, Architecture Freeze). Amendments to this document require a recorded rationale.*
