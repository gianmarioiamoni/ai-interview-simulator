# ADR-037 — Replay Engine Architecture

**Status:** Accepted  
**Date:** 2026-07-15  
**Owner:** Arch  
**Epic:** EPIC-V13-03 — Replay Engine  
**Preconditions:** EPIC-03-REPLAY-ENGINE.md planning frozen; EPIC-01 CLOSED (`SessionHistory` v2.0 active); EPIC-02 CLOSED; ADR-026 (Replay Snapshot Model); ADR-032 (CandidateProfileSnapshot Strategy); ADR-033 (Unified Report Architecture); ADR-034 (Longitudinal Profile Ownership Decision 7); ARC-01 (Architecture Constitution).  
**Supersedes:** Nothing  
**Related:** ADR-026, ADR-032, ADR-033, ADR-034

---

## Context

EPIC-03-REPLAY-ENGINE.md identified four open decisions that must be frozen before Domain Contracts can begin:

- OI-01: `ReplaySession` as extension of `ReplayResult` vs. new artifact.
- OI-02: `ReplayFeatureEngine` scope — read-pass vs. bounded derivation.
- OI-03: `ReplaySession` field set sufficiency for EPIC-04 Replay UI.
- OI-04: `replay_node` graph topology — standalone graph vs. sub-graph.

Additionally, the Master Plan and Architecture Constitution require that all replay-specific invariants be formally declared in a governing ADR before any implementation begins.

This ADR freezes all five decision areas. No decision in this ADR may be overridden without a new ADR that explicitly supersedes the affected decision.

---

## Decision 1 — ReplaySession as the Canonical Replay Artifact

**Decision:** `ReplayResult` (V1.2, ADR-026 §B6) is **superseded** by a new, first-class domain artifact: **`ReplaySession`**.

`ReplayResult` is retained in the codebase only as long as it has active V1.2 test coverage that cannot be migrated atomically. It must be deleted in the same epic as `ReplaySession` is activated as the sole production artifact. No production path may reference both simultaneously.

### 1.1 Artifact Definition

`ReplaySession` is the immutable, self-contained reconstruction artifact produced by `replay_node` from a closed `SessionHistory`. It carries all data required for Replay UI navigation without any further computation.

### 1.2 Constitutional Classification

`ReplaySession` is a **Projection Artifact** (OP-02, ARC-01 §5): a point-in-time, read-only projection of a closed `SessionHistory` captured at replay request time. It contains no new computation — only assembly and formatting of pre-existing persisted data.

It is also a **Reconstruction Artifact**: every field is explicitly sourced from a specific field of `SessionHistory` or its embedded artifacts. No field may be derived, computed, or LLM-generated at reconstruction time.

### 1.3 Ownership

| Dimension | Owner |
|---|---|
| Sole producer | `ReplaySessionBuilder` |
| Sole writer | `replay_node` |
| Declared readers | Replay UI (EPIC-04); `ReplayValidator`; architectural tests |
| `InterviewState` field | None — `ReplaySession` is not written to `InterviewState` |

`ReplaySession` is a cross-invocation artifact: it is not session-resident. It is produced on demand for a completed session and returned to the caller. It is not persisted.

### 1.4 Lifecycle

| Phase | State | Mechanism |
|---|---|---|
| Before request | Does not exist | No record |
| During `replay_node` execution | Constructed | `ReplaySessionBuilder.build()` assembles from `SessionHistory` |
| After `replay_node` returns | Immutable, returned to caller | Read-only; caller (Replay UI, EPIC-04) navigates it |
| After UI session ends | Discarded | No persistence; next request re-runs `replay_node` |

`ReplaySession` is never persisted. Every replay request triggers a fresh reconstruction from the persisted `SessionHistory`. This is constitutionally correct: reconstruction is deterministic, so re-running it produces the same output. Caching is a future performance concern (EPIC-09 / V2) and is not introduced here.

### 1.5 Immutability and Serialization

- `ReplaySession` is `frozen=True`, `extra=forbid`.
- `ReplaySessionBuilder` is the sole permitted construction path. Direct constructor invocation of `ReplaySession` is prohibited in production code.
- `ReplaySession` carries a `schema_version: str` field initialized to `"1.0"` by `ReplaySessionBuilder`. This version is independent of `SessionHistory.schema_version`.
- `ReplaySession` is not serialized to any persistence layer. No serialization contract is required in V1.3.
- Schema evolution in V1.3 is additive only. Any breaking change to `ReplaySession` requires a new ADR.

### 1.6 Disposition of ReplayResult

`ReplayResult` (V1.2) is **deprecated** as of this ADR. It must be deleted when `ReplaySession` is activated as the sole production artifact, in the same epic increment. No compatibility bridge is permitted. Test code referencing `ReplayResult` must be migrated to `ReplaySession` before the deletion increment is merged.

### Rationale

Extending `ReplayResult` was rejected because `ReplayResult` was designed against V1.2 `KnowledgeSnapshot` only. V1.3 `ReplaySession` must surface `scoring_snapshot` and `question_results` from `SessionHistory` v2.0 — fields that do not map to the `ReplayResult` field set. Extending `ReplayResult` would require backward-incompatible field additions that violate its V1.2 contract semantics, and would leave the V1.2 design vocabulary in place for a structurally different V1.3 artifact. A clean new artifact with a declared V1.3 scope is architecturally preferable.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Extend `ReplayResult` with new fields | `ReplayResult` was designed against `KnowledgeSnapshot` only; adding `scoring_snapshot` and `question_results` breaks its V1.2 contract semantics; creates a mixed-generation artifact |
| Keep `ReplayResult` and produce `ReplaySession` as a wrapper | Dual artifacts for the same concept; violates P-02 (Single Ownership); introduces a compatibility bridge without a removal plan |
| Persist `ReplaySession` to avoid re-reconstruction | Adds persistence complexity without architectural benefit; reconstruction is O(1) and deterministic; persistence is deferred to V2 if needed |

### Consequences

**Positive:**
- Clean V1.3 artifact with a complete, auditable field set.
- No compatibility bridges.
- `ReplayResult` is deleted; codebase has no dual artifact.

**Negative / Risks:**
- V1.2 `ReplayResult` tests must be migrated; increases EPIC-03 test scope.
- `ReplaySession` must carry a sufficient field set for EPIC-04 — verified by Decision 3.

---

## Decision 2 — ReplayFeatureEngine Scope: Read-Pass Only

**Decision:** `ReplayFeatureEngine` is a **strict read-pass** component. It performs no derivation, no computation, and no recomputation of feature values. Its sole responsibility is to read `ProfileFeature` values from a stored `CandidateProfileSnapshot` and expose them through the same interface as the live `FeatureEngine`, enabling components that depend on the `FeatureEngine` interface to operate identically in replay mode.

### 2.1 Precise Scope

`ReplayFeatureEngine` is permitted to:
- Read `ProfileFeature` values from `CandidateProfileSnapshot.features`.
- Expose feature values via the declared `FeatureEngine` interface (read methods only).
- Return stored confidence, stability, maturity, and provenance values as-is.

`ReplayFeatureEngine` is prohibited from:
- Recomputing any `ProfileFeature` value from observations.
- Invoking the live `FeatureEngine` for any purpose.
- Invoking any LLM-backed service.
- Applying TTL decay, freshness weighting, or any transformation to stored values.
- Modifying, enriching, or normalizing stored feature values.
- Reading from `ObservationStore` or `ObservationStoreSnapshot` to recompute features.

### 2.2 Constitutional Position

`ReplayFeatureEngine` does **not** cross the Computation/Projection Boundary (ARC-01 §3). It is classified as a Projection component: it reads pre-computed values and exposes them. No new knowledge is computed. No ADR crossing the Computation/Projection Boundary is required.

If, in a future iteration, `ReplayFeatureEngine` is proposed to perform any derivation from stored observations, that proposal requires a new ADR crossing the Computation/Projection Boundary, and domain invariant I-11 must be re-evaluated.

### 2.3 Interface Contract

`ReplayFeatureEngine` implements a read-only subset of the `FeatureEngine` interface:
- `get_features() -> tuple[ProfileFeature, ...]` — returns stored features from `CandidateProfileSnapshot`.
- `get_feature(identity: FeatureIdentity) -> ProfileFeature | None` — returns a stored feature by identity.

It does not implement any method that computes, updates, or accumulates features. Any call to a computation method on `ReplayFeatureEngine` raises `RuntimeError` (P-06 — Fail Fast).

### 2.4 Lifecycle

`ReplayFeatureEngine` is instantiated by `replay_node` for the duration of one replay operation. It is initialized with a `CandidateProfileSnapshot` and discarded after `ReplaySessionBuilder.build()` completes. It is stateless across replay operations.

### Rationale

Bounded deterministic derivation was considered — specifically, whether quality score aggregates could be recomputed from stored feature values (confidence × evidence count). This was rejected because: (a) stored quality metadata is already available in `CandidateProfileSnapshot` (ADR-032 §A4); (b) recomputation introduces a divergence risk if quality calculation logic evolves; (c) the V1.3 Replay UI (EPIC-04) does not require recomputed aggregates — it displays stored values; (d) any derivation at replay time crosses into computation territory and requires constitutional justification. A strict read-pass is architecturally simpler, constitutionally cleaner, and sufficient for V1.3.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Bounded derivation (quality aggregates from stored features) | Stored quality metadata already available; derivation introduces divergence risk; crosses Computation/Projection Boundary; unnecessary for V1.3 |
| Full FeatureEngine recomputation from stored observations | Non-deterministic as FeatureEngine evolves (ADR-032 §B); would produce different conclusions for the same session over time; directly violates I-11 intent |
| No ReplayFeatureEngine (direct field reads in ReplaySessionBuilder) | Couples builder to internal feature representation; bypasses the declared interface; prevents future interface-compatible substitution |

---

## Decision 3 — ReplaySession Field Sufficiency

**Decision:** `ReplaySession` must carry the following complete field inventory. This is the frozen field set for V1.3. No field may be added by EPIC-04 without a new ADR amending this decision.

### 3.1 Field Inventory

| Field | Type | Source | Required? |
|---|---|---|---|
| `session_id` | `str` | `session_history.interview_metadata.session_id` | Required |
| `candidate_identity_id` | `str` | `session_history.interview_metadata.candidate_identity_id` | Required |
| `schema_version` | `str` | `ReplaySessionBuilder` (constant `"1.0"`) | Required |
| `replay_mode` | `ReplayMode` | Input to `replay_node` (defaults to `STANDARD`) | Required |
| `replay_level` | `ReplayLevel` | Input to `replay_node` (defaults to `PRESENTATION`) | Required |
| `profile_snapshot` | `CandidateProfileSnapshot` | `session_history.knowledge_snapshot.profile_snapshot` | Required |
| `narrative` | `Narrative` | `session_history.knowledge_snapshot.narrative` | Required |
| `coaching_snapshot` | `CoachingSnapshot` | `session_history.knowledge_snapshot.coaching_snapshot` | Required |
| `scoring_snapshot` | `Optional[ScoringSnapshot]` | `session_history.scoring_snapshot` | Optional — `None` when session completed without evaluation |
| `question_results` | `tuple[QuestionResultRecord, ...]` | `session_history.question_results` | Required — empty tuple if no questions persisted |
| `session_metadata` | `ReplaySessionMetadata` | Assembled from `session_history.interview_metadata` | Required |
| `policy_versions` | `PolicyVersions` | `session_history.knowledge_snapshot.policy_versions` | Required |
| `knowledge_epoch` | `str` | `session_history.knowledge_snapshot.knowledge_epoch` | Required |
| `manifest` | `ReplayManifest` | Produced by `replay_node` at reconstruction time | Required |
| `is_successful` | `bool` | Set by `replay_node` (True on success; False on failure) | Required |
| `failure_reason` | `Optional[str]` | Non-None only when `is_successful=False` | Optional |

### 3.2 ReplaySessionMetadata

`ReplaySessionMetadata` is a new immutable value object assembled by `replay_node` from `SessionHistory.interview_metadata`. It carries:

| Field | Source |
|---|---|
| `interview_index` | `interview_metadata.interview_index` |
| `session_date` | `interview_metadata.session_date` |
| `role` | `interview_metadata.role` |
| `seniority_level` | `interview_metadata.seniority_level` |
| `question_count` | `interview_metadata.question_count` |
| `session_duration_seconds` | `interview_metadata.session_duration_seconds` (if persisted) |

`ReplaySessionMetadata` is `frozen=True`, `extra=forbid`. It is produced by `ReplaySessionBuilder`. It is a sub-artifact of `ReplaySession` — it has no independent lifecycle.

### 3.3 ReplayLevel and Field Access

- `ReplayLevel.PRESENTATION` (Level 1): surfaces all fields listed in §3.1. The standard candidate-facing replay mode.
- `ReplayLevel.KNOWLEDGE` (Level 2): additionally exposes `ObservationStoreSnapshot` (read from `KnowledgeSnapshot`) via a separate accessor on `ReplaySession`. This level is for operator / calibration use only.
- `ReplayLevel.REASONING` (Level 3): remains reserved. `replay_node` raises `RuntimeError` if invoked with `ReplayLevel.REASONING` (P-06).

### 3.4 Sufficiency Guarantee

The field set in §3.1 is sufficient for EPIC-04 Replay UI to render:
- Session summary panel (from `session_metadata`, `scoring_snapshot`).
- Question-by-question navigation (from `question_results`).
- Per-question: question prompt, candidate answer, execution result, score, feedback (from `QuestionResultRecord`).
- Profile knowledge panel (from `profile_snapshot`).
- Narrative insights (from `narrative`).
- Coaching objectives (from `coaching_snapshot`).
- Session-level scoring (from `scoring_snapshot` — conditional on `is_successful` and `scoring_snapshot is not None`).
- Policy and versioning metadata (from `policy_versions`, `knowledge_epoch`, `schema_version`).
- Audit trail (from `manifest`).

### 3.5 EPIC-04 Boundary

EPIC-04 (Replay UI) is the sole consumer of `ReplaySession`. EPIC-04 must not request any field not present in §3.1 without an ADR amending this decision. EPIC-04 may choose not to render certain optional fields (e.g., `scoring_snapshot is None`) — that is a UI rendering decision, not a replay contract change.

### Rationale

The field set was derived from:
1. EPIC-04 requirements as stated in the Master Plan: question-by-question navigation, answer display, score display, coaching note display, session-level summary.
2. ADR-033 Decisions 1 and 2: `ScoringSnapshot` and `QuestionResultRecord` are persisted in `SessionHistory` v2.0 and must be surfaced in replay.
3. ADR-026 §B6 `ReplayResult` field set: extended with `scoring_snapshot`, `question_results`, and `session_metadata`.
4. The no-LLM constraint: all fields are read directly from persisted artifacts.

---

## Decision 4 — Replay Graph Topology: Independent Invocation Node

**Decision:** `replay_node` is implemented as a **standalone LangGraph node invocable via an independent graph**, separate from the live interview session graph. It is not a sub-graph of the live session graph, and it is not registered as a node in the live session graph.

### 4.1 Topology

```
[Live Session Graph]
  Nodes: start_processing, question, evaluation, reasoner, session_close, report, longitudinal_update
  Input: InterviewState (session-scoped)
  Trigger: Candidate initiates session

[Replay Graph — separate, independent]
  Nodes: replay_node
  Input: ReplayRequest (session_id, replay_mode, replay_level)
  Output: ReplaySession
  Trigger: Candidate or operator requests replay of a completed session
```

The Replay Graph is a single-node graph: `replay_node → END`. No other node is present. No edge connects the Replay Graph to the Live Session Graph.

### 4.2 Entry Node

`replay_node` is the single entry node and the single exit node of the Replay Graph. There is no predecessor node. There is no successor node (except `END`).

### 4.3 Input Contract

`replay_node` accepts a `ReplayRequest`:
- `session_id: str` — the identifier of the completed session to replay.
- `replay_mode: ReplayMode` — defaults to `STANDARD`.
- `replay_level: ReplayLevel` — defaults to `PRESENTATION`.
- `operator_id: Optional[str]` — required when `replay_mode` is `MIGRATION` or `RECOVERY`.

`ReplayRequest` is `frozen=True`, `extra=forbid`. It is not an `InterviewState` subtype. It carries no live session data.

### 4.4 State Contract

The Replay Graph does **not** use `InterviewState`. It uses a purpose-built `ReplayGraphState` (a minimal LangGraph state container):
- `request: ReplayRequest` — input; immutable throughout graph execution.
- `result: Optional[ReplaySession]` — output; set by `replay_node` before `END`.
- `error: Optional[str]` — set by `replay_node` on failure; `None` on success.

`ReplayGraphState` is not shared with any live session graph node. It does not extend `InterviewState`.

### 4.5 Termination Semantics

`replay_node` is non-fatal. On failure, it sets `ReplayGraphState.result` to a `ReplaySession` with `is_successful=False` and `failure_reason` populated. It does not raise an exception that propagates to the caller. The caller receives a failed `ReplaySession` and handles it (EPIC-04 UI).

Exceptions that indicate programming errors (e.g., `ReplayLevel.REASONING` requested) are still raised as `RuntimeError` (P-06).

### 4.6 Runtime Isolation

The Replay Graph is invoked by the API layer (or the Replay UI backend). It runs independently of any live session. No live session can trigger the Replay Graph. No Replay Graph execution can affect any live session. Concurrent Replay Graph executions for different `session_id` values are safe: all reads are from immutable, closed `SessionHistory` records.

### 4.7 LangGraph Compliance

The Replay Graph satisfies ARC-01 P-04 (LangGraph Is the Sole Runtime Orchestrator): all control flow is expressed as LangGraph edges. `replay_node` returns a result — it does not invoke the next node directly.

### Rationale

A sub-graph embedded in the live session graph was rejected because: (a) it would require the live session graph to expose a replay entry point, coupling two topologically independent flows; (b) it would risk sharing `InterviewState` between live and replay contexts; (c) the isolation invariant (replay must not affect live sessions, and live sessions must not trigger replay) is more easily enforced with a fully separate graph. A standalone single-node graph is the minimal viable topology that satisfies P-04 while maintaining full isolation.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| `replay_node` as a node in the live session graph | Couples live and replay topologies; risks `InterviewState` contamination; live sessions could inadvertently enter replay path |
| `replay_node` as a conditional branch off `session_close_node` | Semantically incorrect — replay is not a close-time operation; it is on-demand; would require `is_replay` flag in `InterviewState` |
| `replay_node` invoked directly (no LangGraph) | Violates P-04 (LangGraph Is the Sole Runtime Orchestrator) |
| Replay as a sub-graph of a parent graph | Unnecessary complexity; no advantage over a standalone single-node graph |

---

## Decision 5 — Replay Runtime Invariants

**Decision:** The following invariants govern all replay operations in V1.3. All are constitutionally grounded. All must be verified by architectural tests where noted.

### I-11 — LLM Prohibition (Domain Invariant, Master Plan)

Replay never invokes LLM calls. `replay_node`, `ReplayFeatureEngine`, and `ReplaySessionBuilder` must not invoke any LLM-backed service — including but not limited to `NarrativeGenerator`, `CoachingEngine`, `InterviewEvaluationService`, or any adapter that calls an external model API.

**Enforcement:** Architectural test mocks all LLM service interfaces and asserts zero invocations during `replay_node` execution across all test fixtures.

### I-R01 — Sole Writer

`replay_node` is the sole writer of `ReplaySession`. No other node, service, pipeline, or builder may produce or persist a `ReplaySession`. `ReplaySessionBuilder` is the sole producer (construction path). Both invariants are simultaneously required.

**Enforcement:** Architectural test verifies that no production module other than `replay_node` instantiates or calls `ReplaySessionBuilder.build()`.

### I-R02 — Immutable Contracts

`ReplaySession`, `ReplayRequest`, `ReplayGraphState`, `ReplaySessionMetadata`, `ReplayManifest`, and `ReplayContext` are `frozen=True`, `extra=forbid`. Post-construction mutation of any replay artifact is constitutionally prohibited (P-03). Any attempt to mutate a frozen replay artifact must raise `ValidationError`.

**Enforcement:** Contract test verifies that `frozen=True` is set on each artifact and that attempted field assignment raises `ValidationError`.

### I-R03 — Replay Isolation

The Replay Graph has no access to `InterviewState`. `replay_node` reads no field from any live session's `InterviewState`. The Replay Graph's state container (`ReplayGraphState`) does not inherit from or reference `InterviewState`. No live session node imports or references `replay_node`.

**Enforcement:** Architectural test verifies that `replay_node` module imports no live session node. Architectural test verifies that `ReplayGraphState` does not reference `InterviewState`.

### I-R04 — Deterministic Execution

Given the same `session_id` and the same persisted `SessionHistory`, two invocations of `replay_node` must produce identical `ReplaySession` output. No random element, timestamp dependency (except `manifest.replay_timestamp`, which is informational only), or external query may affect the reconstruction of knowledge fields.

**Enforcement:** Determinism test invokes `replay_node` twice for the same fixture and asserts field-level equality on all knowledge fields (`profile_snapshot`, `narrative`, `coaching_snapshot`, `scoring_snapshot`, `question_results`, `policy_versions`, `knowledge_epoch`). `manifest` fields are excluded from determinism assertion (timestamps are legitimately different).

### I-R05 — Reconstruction Completeness (P-08)

Every field of `ReplaySession` must be explicitly enumerated in `ReplaySessionBuilder.build()`. No field may be populated by a wildcard copy, a default value, or an implicit carry-forward from a prior object. The absence of a field in the explicit enumeration is a bug.

**Enforcement:** Architectural test asserts that `ReplaySessionBuilder.build()` references every declared field of `ReplaySession` by name. This test must be updated whenever a field is added to `ReplaySession`.

### I-R06 — Longitudinal Isolation (ADR-034 Decision 7)

No replay contract (`ReplaySession`, `ReplayRequest`, `ReplayContext`, `ReplayManifest`, `ReplayGraphState`, `ReplaySessionMetadata`, `ReplayFeatureEngine`) may import or reference `LongitudinalProfile`. No `LongitudinalProfile` contract may import or reference any replay contract. The boundary is bidirectional and absolute.

**Enforcement:** Architectural test (import graph analysis) verifies zero cross-references between the replay contract module set and the longitudinal contract module set.

### I-R07 — Runtime Mutation Prohibition

`replay_node` is read-only with respect to all persistence artifacts. It may not write to `SessionHistory`, `CandidateProfileSnapshot`, `KnowledgeSnapshot`, `LongitudinalProfile`, or any `InterviewState` field. Any persistence write from `replay_node` is a constitutional violation (P-02).

**Enforcement:** Architectural test mocks the persistence layer and asserts zero write calls during `replay_node` execution.

### I-R08 — Fail Fast on Unrecoverable States

The following conditions must raise `RuntimeError` immediately, not be silently degraded:
- `ReplayLevel.REASONING` requested.
- `SessionHistory` found but `KnowledgeSnapshot` is `None` or invalid.
- `ReplaySessionBuilder.build()` detects any required field is missing.

The following conditions produce a failed `ReplaySession` (`is_successful=False`) with a structured log at `WARNING` level, not a raised exception:
- `SessionHistory` not found for the given `session_id`.
- Persistence layer I/O error.
- `ReplayValidator` reports context violation.

**Enforcement:** Unit tests verify the fail-fast paths raise `RuntimeError`. Unit tests verify the non-fatal paths return `ReplaySession(is_successful=False)` with an observable log event.

### I-R09 — ReplayLevel.REASONING Reserved

`ReplayLevel.REASONING` is reserved for V1.3+. `replay_node` must raise `RuntimeError` if invoked with `replay_level=ReplayLevel.REASONING`. The reservation is unchanged from V1.2 (ADR-026 §B3) and is reaffirmed here for V1.3.

**Enforcement:** Unit test verifies `RuntimeError` raised when `replay_level=ReplayLevel.REASONING` is passed.

---

## Implementation Evidence

Artifacts to be created or modified (owned by EPIC-03 unless noted):

| Artifact | Action | Notes |
|---|---|---|
| `domain/contracts/replay/replay_session_v13.py` | **Create** `ReplaySession` (V1.3) | Replaces `ReplayResult` as production artifact |
| `domain/contracts/replay/replay_session_builder.py` | **Create** `ReplaySessionBuilder` | Sole construction path for `ReplaySession` |
| `domain/contracts/replay/replay_session_metadata.py` | **Create** `ReplaySessionMetadata` | Sub-artifact of `ReplaySession` |
| `domain/contracts/replay/replay_request.py` | **Create** `ReplayRequest` | Input contract for `replay_node` |
| `domain/contracts/replay/replay_graph_state.py` | **Create** `ReplayGraphState` | LangGraph state for Replay Graph |
| `domain/contracts/replay/replay_feature_engine.py` | **Create** `ReplayFeatureEngine` | Read-only; reads from `CandidateProfileSnapshot` |
| `app/graph/nodes/replay_node.py` | **Create** | Sole writer of `ReplaySession`; reads `SessionHistory` from persistence |
| `app/graph/replay_graph.py` | **Create** | Standalone Replay Graph: `replay_node → END` |
| `domain/contracts/replay/replay_result.py` | **Delete** | In the same increment that `ReplaySession` is activated |
| `domain/contracts/replay/replay_session.py` | **Repurpose or delete** | Rename / replace; V1.2 `ReplaySession` class conflicts with V1.3 artifact name; resolution in Domain Contracts |
| `tests/domain/contracts/replay/` | **Migrate** | All V1.2 `ReplayResult` tests migrated to `ReplaySession` before deletion increment |

---

## Review Triggers

This ADR must be revisited if:

- EPIC-04 (Replay UI) requires a field not present in Decision 3 §3.1.
- A proposal is made to persist `ReplaySession` (requires new ADR — adds lifecycle and ownership complexity).
- A proposal is made to invoke any LLM-backed service from `replay_node` (requires new ADR crossing Computation/Projection Boundary + I-11 amendment).
- `ReplayLevel.REASONING` is proposed for activation (requires new ADR).
- A second construction path for `ReplaySession` is proposed (requires new ADR crossing Builder Boundary).
- Any replay contract is proposed to import `LongitudinalProfile` (requires new ADR crossing the Longitudinal Boundary; ADR-034 Decision 7 must be explicitly amended).
- `ReplayFeatureEngine` is proposed to perform any derivation from stored observations (requires new ADR crossing Computation/Projection Boundary).

---

## Acceptance Checklist

| Criterion | Status |
|---|---|
| OI-01 resolved: `ReplaySession` vs `ReplayResult` | **FROZEN** — Decision 1: `ReplaySession` is the new first-class artifact; `ReplayResult` is deprecated and deleted |
| OI-02 resolved: `ReplayFeatureEngine` scope | **FROZEN** — Decision 2: strict read-pass; no derivation; no LLM; read-only interface |
| OI-03 resolved: `ReplaySession` field sufficiency | **FROZEN** — Decision 3: complete field inventory with sources; EPIC-04 sufficiency guarantee |
| OI-04 resolved: graph topology | **FROZEN** — Decision 4: standalone single-node Replay Graph; independent from live session graph |
| Replay invariants declared | **FROZEN** — Decision 5: I-11, I-R01 through I-R09 |
| ARC-01 P-01 compliance | **CONFIRMED** — `ReplayFeatureEngine` is read-pass (Decision 2); no computation in projection |
| ARC-01 P-02 compliance | **CONFIRMED** — `replay_node` sole writer; `ReplaySessionBuilder` sole producer (I-R01) |
| ARC-01 P-03 compliance | **CONFIRMED** — all artifacts `frozen=True`, `extra=forbid` (I-R02) |
| ARC-01 P-04 compliance | **CONFIRMED** — Replay Graph is a LangGraph graph; `replay_node` does not invoke next node directly (Decision 4) |
| ARC-01 P-05 compliance | **CONFIRMED** — `ReplaySessionBuilder` assembles; `ReplayFeatureEngine` reads; no mixing (Decisions 1, 2) |
| ARC-01 P-06 compliance | **CONFIRMED** — fail-fast on unrecoverable states; observable failure for non-fatal paths (I-R08) |
| ARC-01 P-08 compliance | **CONFIRMED** — Reconstruction Completeness enforced (I-R05) |
| ADR-033 D1/D2 integration | **CONFIRMED** — `scoring_snapshot` and `question_results` in `ReplaySession` field set (Decision 3 §3.1) |
| ADR-034 D7 compliance | **CONFIRMED** — bidirectional longitudinal isolation declared and enforced (I-R06) |
| Domain invariant I-11 enforcement | **CONFIRMED** — LLM prohibition stated; architectural test mandated (I-11) |
| No compatibility bridges | **CONFIRMED** — `ReplayResult` deleted in same increment as `ReplaySession` activated; no bridge permitted |
| No production code modified | **CONFIRMED** — architecture only |
