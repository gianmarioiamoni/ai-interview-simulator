# ADR-036 — LanguageCapability Runtime Ownership and Lifecycle

**Status:** Accepted  
**Date:** 2026-07-14  
**Owner:** Arch — Language Independence Layer / Knowledge Construction Layer  
**Epic:** EPIC-02 — Cross-Session Profile Continuity (EPIC-V13-02)  
**Preconditions:** ADR-019 (Language Independence Layer), ADR-020 (FeatureEngine Architecture), ADR-022 (SessionHistory Architecture), ADR-033 (Unified Report Architecture), ADR-034 (Longitudinal Profile Ownership), ADR-035 (LanguageProfile Runtime Lifecycle), ARC-01 (Architecture Constitution), EPIC-02-ARCHITECTURE-FREEZE.md declared, EPIC-02-DOMAIN-CONTRACTS.md frozen.  
**Mini Architecture Freeze:** Mandatory before implementation of any component governed by this ADR.  
**Supersedes:** Nothing  
**Related:** ADR-019, ADR-020, ADR-022, ADR-033, ADR-034, ADR-035

---

## Context

`LanguageCapability` has existed as a session-scoped contract in `domain/contracts/language/language_capability.py` since V1.2. It carries per-language scoring metrics for one session. EPIC-02 activates it for cross-session accumulation via `CrossSessionLanguageCapability` embedded in `LongitudinalProfile`.

The EPIC-02 Domain Contracts specification (§3.2) resolved OI-03: `LanguageCapability` is transient and not embedded in `KnowledgeSnapshot` or `SessionHistory`. However, no ADR has formally declared:

- The runtime ownership and sole production path for session-scoped `LanguageCapability`.
- The runtime placement of `LanguageCapability` in `InterviewState`.
- The lifecycle from creation through consumption, persistence handoff, and retirement.
- The complete set of runtime invariants.

This ADR resolves the gap. It is an architectural document only. No production code is introduced or modified.

---

## SECTION 1 — Purpose and Classification

### 1.1 Definition

`LanguageCapability` is the **session-scoped, language-specific competence summary** for a candidate in one programming language, derived from coding question evaluation signals within that session. It represents the candidate's demonstrated language capability as accumulated by `FeatureEngine` during the live runtime cycle.

It answers one question: **"What is the candidate's demonstrated competence in language X within this session, as of the current reasoning cycle?"**

### 1.2 Classification

`LanguageCapability` is a **Live Session Knowledge Artifact** — it is:

- **Mutable during the session** — it accumulates progressively as `FeatureEngine` processes `LANGUAGE_*` observations across reasoning cycles.
- **Session-scoped** — it does not persist beyond the session close boundary. After `longitudinal_update_node` captures it, the in-session instance expires.
- **Knowledge, not configuration** — it represents demonstrated competence, not session setup.
- **Domain Layer** (ADR-019 Section A): produced by `FeatureEngine`; resides in the Domain layer.

### 1.3 Distinction from Adjacent Artifacts

| Artifact | Classification | What it represents | Relationship to LanguageCapability |
|---|---|---|---|
| `LanguageProfile` | Session Configuration Snapshot (ADR-035) | Which languages are active; executor refs; policy refs — frozen at session start | **Configuration input** for execution context; semantically orthogonal — `LanguageProfile` is setup, `LanguageCapability` is knowledge |
| `LanguageCapabilityFeature` | `ProfileFeature` (Domain, ADR-018/019) | Typed `ProfileFeature` representing idiomatic language competence; carries `language_context` in provenance | Produced by `FeatureEngine` from `LANGUAGE_*` observations; contributes to `LanguageCapability` score aggregation |
| `LanguageConfig` | Application-layer input | User/CLI language configuration (ADR-019 Section C) | Resolved into `LanguageProfile` at session start; no runtime relationship to `LanguageCapability` |
| `Observation` | Evidence artifact (ADR-016/017) | Raw signal with `language_context: Optional[ProgrammingLanguage]` metadata | `LANGUAGE_*` typed `Observation` instances are the **source material** from which `LanguageCapability` is derived |
| `ProfileFeature` | Knowledge unit (ADR-018) | Typed, dimensioned unit of knowledge from `FeatureEngine` | `LanguageCapabilityFeature` (a `ProfileFeature` subtype) is a parallel knowledge artifact; both derive from the same `LANGUAGE_*` observations but serve different consumers (`CandidateProfile` vs. `LanguageCapability`) |

**Critical boundary:** `LanguageCapability` is a session-scoped score aggregate. `LanguageCapabilityFeature` is a `ProfileFeature` with provenance and confidence. They are not the same artifact. Both derive from `LANGUAGE_*` observations but serve different downstream consumers.

---

## SECTION 2 — Ownership

### 2.1 Sole Producer

**`FeatureEngine`** (Knowledge Construction Engine, ADR-020) is the sole producer of session-scoped `LanguageCapability` instances.

Specifically, the `ObservationUpdater` (registered `FeatureUpdater`) produces `LanguageCapabilityFeature` candidates from `LANGUAGE_*` observation types (ADR-019 Section L, ADR-020 Section C). `FeatureEngine` or its coordinate service aggregates these into `LanguageCapability` score summaries per language. No other component may produce a `LanguageCapability` instance for a live session.

**Domain Invariant I-02 (ADR-020) confirmed:** `FeatureEngine` is the only permitted producer of `ProfileFeature[]`. The same invariant extends to `LanguageCapability`: no component outside `FeatureEngine` and its registered `FeatureUpdaters` may produce language capability score data during the live session.

### 2.2 Sole Writer to InterviewState

**`reasoner_node`** is the sole writer of `LanguageCapability` instances to `InterviewState`. It writes `InterviewState.language_capabilities: tuple[LanguageCapability, ...]` as part of the normal `FeatureEngine` output cycle. Each `FeatureEngine` cycle produces an updated set of `LanguageCapability` instances which replace the prior set in `InterviewState` (immutable accumulation: OP-06, ARC-01 §5).

### 2.3 Runtime Readers

| Reader | Layer | Purpose |
|---|---|---|
| `reasoner_node` | Application | Reads prior `language_capabilities` from `InterviewState`; passes to `FeatureEngine` for incremental update |
| `longitudinal_update_node` | Application | Reads final `language_capabilities` from `InterviewState` before session expiry; passes as parameter to `LongitudinalProfileBuilder` (OI-03 resolution — EPIC-02-DOMAIN-CONTRACTS.md §3.2) |
| `session_close_node` | Application | Read-only; does not consume `language_capabilities` but must not clear the field before `longitudinal_update_node` executes |

All reads are read-only with respect to the `LanguageCapability` instances themselves (which are `frozen=True`). The field on `InterviewState` is replaced, not mutated.

### 2.4 Persistence Readers

`LanguageCapability` instances are **not persisted in `SessionHistory`** (EPIC-02-DOMAIN-CONTRACTS.md §3.2, OI-03 resolution). They are captured by `longitudinal_update_node` from live `InterviewState` before the session state expires, and embedded as `LongitudinalSessionMetadata.language_capabilities` in `LongitudinalProfile`.

| Persistence Reader | Access Path | Purpose |
|---|---|---|
| `LongitudinalProfileBuilder` | Received as `language_capabilities` parameter from `longitudinal_update_node` | Source for `CrossSessionLanguageCapability` aggregation |
| `LearningProgressBuilder` | Reads from `LongitudinalProfile.language_capability_summary` (already aggregated) | Propagates `CrossSessionLanguageCapability` to `LearningProgress` |

`LanguageCapability` does **not** appear in `SessionHistory`, `KnowledgeSnapshot`, `Report`, or `FinalReportDTO`.

### 2.5 Builder Ownership

There is no `LanguageCapabilityBuilder`. `LanguageCapability` is produced directly by `FeatureEngine` as part of the `CandidateProfile` update cycle. Its construction is an Engine responsibility (P-05: Builders Assemble; Engines Compute). `FeatureEngine` is an Engine — its output includes both `ProfileFeature[]` and the derived `LanguageCapability` score aggregates.

The `LanguageCapability` contract (`frozen=True`, `extra=forbid`) must be constructable only via its declared fields with no bypass. Direct construction in production code is permitted only through `FeatureEngine` output paths.

### 2.6 Ownership Table

| Ownership Role | Owner | Invariant |
|---|---|---|
| Sole producer | `FeatureEngine` | LC-R-01 |
| Sole writer to `InterviewState` | `reasoner_node` | LC-R-02 |
| Capture before expiry | `longitudinal_update_node` | LC-R-03 |
| Cross-session aggregation | `LongitudinalProfileBuilder` | LC-R-04 |
| Runtime reader | `reasoner_node`, `longitudinal_update_node` | Read-only |
| Not persisted in SessionHistory | — | LC-R-05 |
| Not embedded in KnowledgeSnapshot | — | LC-R-06 |

---

## SECTION 3 — Runtime Lifecycle

### 3.1 Creation

**Trigger:** `FeatureEngine` cycle within `reasoner_node`, after the first coding question is evaluated and `LANGUAGE_*` observations are available in `ObservationStore`.

**Mechanism:** `ObservationUpdater` processes `LANGUAGE_IDIOMATIC_USAGE`, `LANGUAGE_TYPE_ERROR_PATTERN`, `LANGUAGE_CONSTRUCT_CONFUSION` (and related) `ObservationType` entries. `FeatureEngine` aggregates the resulting `LanguageCapabilityFeature` candidates by `language_id` and produces one `LanguageCapability` instance per distinct language active in the session.

**First cycle:** If no `LANGUAGE_*` observations exist yet, `InterviewState.language_capabilities` is `()` (empty tuple). This is a valid initial state. No `LanguageCapability` is produced for a language with no coding question observations.

**Precondition:** `LanguageProfile` must be present in `InterviewState` at the time of first `LanguageCapability` production (LP-R-06, ADR-035 Section 7). Any `LanguageCapability.language_id` produced must be a member of `LanguageProfile.enabled_language_ids`.

### 3.2 Accumulation

`LanguageCapability` accumulates progressively across `FeatureEngine` cycles within the session. At each cycle:

1. `reasoner_node` reads the prior `InterviewState.language_capabilities` (as context, not as input to `FeatureEngine`).
2. `FeatureEngine` reads `ObservationStore` (freshness-filtered, question_index-ordered) and produces updated `LanguageCapability` instances.
3. `reasoner_node` writes the new `language_capabilities` tuple to `InterviewState` via `model_copy(update={"language_capabilities": new_instances})`.
4. The prior tuple is replaced entirely. No in-place mutation occurs (P-03, OP-06).

Each replacement produces a complete, self-consistent set. No partial state exists between cycles.

### 3.3 Consumption

The final `LanguageCapability` instances (at the point of session close cascade initiation) are consumed by `longitudinal_update_node`:

1. `longitudinal_update_node` reads `InterviewState.language_capabilities` from the session state.
2. It passes the tuple as the `language_capabilities` parameter to `LongitudinalProfileBuilder.build(...)`.
3. `LongitudinalProfileBuilder` embeds them as `LongitudinalSessionMetadata.language_capabilities` and aggregates them into `language_capability_summary`.

This capture must occur **before** `InterviewState` is released or garbage-collected. The ordering constraint in the session close cascade is:

```
session_close_node → report_node → longitudinal_update_node → END
```

`longitudinal_update_node` reads `InterviewState` (including `language_capabilities`) at its execution point. `session_close_node` must not clear `language_capabilities` from `InterviewState` before `longitudinal_update_node` executes (LC-R-03).

### 3.4 Persistence

`LanguageCapability` instances are **not** written to `SessionHistory`, `KnowledgeSnapshot`, or `Report`. Their persistence path is exclusively:

```
InterviewState.language_capabilities
    ↓ [longitudinal_update_node reads]
LongitudinalSessionMetadata.language_capabilities (embedded in LongitudinalProfile)
    ↓ [LongitudinalProfileBuilder aggregates]
LongitudinalProfile.language_capability_summary: tuple[CrossSessionLanguageCapability, ...]
    ↓ [LongitudinalProfileRepository.save()]
Persisted LongitudinalProfile
```

If `longitudinal_update_node` fails (non-fatal, ADR-034 Decision 6), the `LanguageCapability` data for that session is **lost**. This is an accepted limitation for V1.3: the `language_capability_summary` reconstruction gap is documented in EPIC-02-ARCHITECTURE-FREEZE.md §3.12 and EPIC-02-DATA-MODEL.md §6.3. The session report and all other artifacts are unaffected.

### 3.5 Replay

`LanguageCapability` instances are **not accessible** during replay. `replay_node` reconstructs from `SessionHistory`, which does not contain `LanguageCapability`. The replay path produces `ReplayResult` — a session-scoped reconstruction artifact — and does not require `LanguageCapability` for its purpose (ADR-034 Decision 7, LP-11).

Any future requirement to surface per-session language scores in the Replay UI must source them from `LongitudinalProfile.session_snapshots[n].session_metadata.language_capabilities` — not from a replay path that re-derives them. This sourcing path is a UI composition concern (EPIC-04/05), not a replay contract concern.

### 3.6 Retirement

`LanguageCapability` instances in `InterviewState` are implicitly retired when the session state is released after the close cascade completes (`longitudinal_update_node` is the last node in the cascade that reads them). No explicit deletion is required; session state is garbage-collected by the runtime after the cascade.

**Retirement invariant:** After `longitudinal_update_node` completes (successfully or with a failure log), no component may read `InterviewState.language_capabilities` for production purposes. The captured data is now held by `LongitudinalProfile` (or is lost if the update failed). The `InterviewState` instance should be considered expired.

---

## SECTION 4 — Runtime Placement

### 4.1 InterviewState

**Decision:** `LanguageCapability` instances reside in `InterviewState.language_capabilities: tuple[LanguageCapability, ...]`.

**Justification:** `InterviewState` is the authoritative session state container for all session-scoped artifacts (P-02, OP-04). `LanguageCapability` is session-scoped and must be accessible to `reasoner_node` (for incremental update), `session_close_node` (ordering dependency), and `longitudinal_update_node` (capture before expiry). All three are LangGraph nodes that read from `InterviewState`. Centralising the field in `InterviewState` satisfies OP-04 (Sole Writer Node) and keeps the session's language capability data co-located with the rest of the session state.

**Field introduction follows TCP pattern:** `InterviewState.language_capabilities: tuple[LanguageCapability, ...] = ()`. Default is empty tuple. Nodes that depend on this field guard on its content before consuming.

### 4.2 KnowledgeSnapshot

**Decision:** `LanguageCapability` is **not** embedded in `KnowledgeSnapshot`.

**Justification:** `KnowledgeSnapshot` carries knowledge artifacts: `CandidateProfileSnapshot`, `Narrative`, `CoachingSnapshot`. `LanguageCapability` is a score aggregate — not a knowledge artifact in the `ProfileFeature` taxonomy sense. The knowledge representation of language competence in `KnowledgeSnapshot` is via `LanguageCapabilityFeature` instances within `CandidateProfileSnapshot.features` — the canonical `ProfileFeature` path. Embedding `LanguageCapability` separately would create a second, parallel representation of the same underlying signal (dual-source violation, P-02). Furthermore, embedding it in `KnowledgeSnapshot` would require a `SessionHistory` schema change that was explicitly avoided by the OI-03 resolution.

### 4.3 SessionHistory

**Decision:** `LanguageCapability` is **not** embedded in `SessionHistory`.

**Justification:** Confirmed by OI-03 resolution (EPIC-02-DOMAIN-CONTRACTS.md §3.2). `SessionHistory` v2.0 contract (ADR-033) is preserved unchanged. The language capability data needed for cross-session accumulation is captured by `longitudinal_update_node` from live `InterviewState` before the session state expires — not from the closed `SessionHistory`. This is the accepted architectural solution.

**Consequence:** `LanguageCapability` data is **not** reconstructable from `SessionHistory[]` alone. This is an accepted limitation documented in EPIC-02-ARCHITECTURE-FREEZE.md §5.2 and §3.12.

### 4.4 FeatureEngineContext / FeatureEngine Internal State

`FeatureEngine` produces `LanguageCapability` as part of its output. Internally, the `ObservationUpdater` processes `LANGUAGE_*` observation types and produces `LanguageCapabilityFeature` candidates. Whether `FeatureEngine` maintains intermediate `LanguageCapability` state across cycles or recomputes from `ObservationStore` on each cycle is an internal implementation concern — it is not an architectural placement decision. The observable output is the `LanguageCapability` tuple written to `InterviewState` by `reasoner_node`.

### 4.5 ObservationPipeline

`LanguageCapability` is **not** produced by or stored in the `ObservationPipeline`. The `ObservationPipeline` (including `ObservationExtractor`) produces `Observation` instances with `language_context: Optional[ProgrammingLanguage]` metadata. These `Observation` instances are the upstream source material. `LanguageCapability` is produced downstream by `FeatureEngine`.

---

## SECTION 5 — Relationships with Other Artifacts

### 5.1 LanguageProfile

`LanguageProfile` (ADR-035) and `LanguageCapability` are orthogonal:

- `LanguageProfile` is **configuration**: which languages are active, frozen at session start.
- `LanguageCapability` is **knowledge**: the candidate's demonstrated competence, accumulated during the session.

The only dependency is the consistency constraint (LP-R-06, ADR-035 §7): every `LanguageCapability.language_id` produced for a session must be a member of `LanguageProfile.enabled_language_ids`. `LanguageCapability` does not read `LanguageProfile` directly — the consistency check is enforced by `longitudinal_update_node` before passing to `LongitudinalProfileBuilder`.

### 5.2 EvaluationAggregateNode

`EvaluationAggregateNode` produces `ScoringSnapshot` and `ScoringNarrative` (ADR-033 Decision 6). It does not produce `LanguageCapability`. `EvaluationAggregateNode` operates at the scoring layer (hire decision, percentile, dimension scores). `LanguageCapability` operates at the language-specific knowledge layer. These are independent pipelines with non-overlapping outputs.

### 5.3 FeatureEngine

`FeatureEngine` is the sole producer of `LanguageCapability` (LC-R-01). The production path is:

```
LANGUAGE_* Observations (from ObservationStore)
    ↓ [ObservationUpdater]
LanguageCapabilityFeature candidates
    ↓ [FeatureComposer + FeatureMergePolicy]
LanguageCapabilityFeature[] in CandidateProfile.features
    ↓ [FeatureEngine aggregation by language_id]
LanguageCapability[] (one per active language with LANGUAGE_* observations)
```

`LanguageCapability` is a **derived aggregate** from `LanguageCapabilityFeature` instances, produced as a secondary output of the same `FeatureEngine` cycle that produces `ProfileFeature[]`. It is not produced by a separate engine or pipeline.

### 5.4 ObservationPipeline

`ObservationPipeline` (including `ObservationExtractor`) assigns `language_context: Optional[ProgrammingLanguage]` to each `Observation`. `LANGUAGE_*` observation types carry a non-null `language_context`. These are the upstream source material for `LanguageCapability` production. The `ObservationPipeline` has no knowledge of `LanguageCapability` — it produces `Observation` instances only.

### 5.5 KnowledgePipeline

`KnowledgePipeline` orchestrates the chain from `FeatureEngine` output to `CandidateProfile` update (and, via `NarrativeGenerator` and `CoachingEngine`, to `KnowledgeSnapshot` assembly). `LanguageCapability` is produced as part of the `FeatureEngine` stage of `KnowledgePipeline`. It is not passed to `NarrativeGenerator`, `CoachingEngine`, or `KnowledgeSnapshotBuilder`. It is not part of the `KnowledgeSnapshot` assembly path.

### 5.6 LongitudinalProfile

`LongitudinalProfile` is the first persistence boundary for `LanguageCapability` data. After session close, the only way language capability scores from a session survive is via embedding in `LongitudinalSessionMetadata.language_capabilities` (as frozen snapshots) and aggregation into `LongitudinalProfile.language_capability_summary` (as `CrossSessionLanguageCapability` entries). The `LongitudinalProfile` contract is unchanged by this ADR.

### 5.7 LearningProgress

`LearningProgress` receives language capability data from `LongitudinalProfile.language_capability_summary` via `LearningProgressBuilder`. It carries `language_capability_summary: tuple[CrossSessionLanguageCapability, ...]` as a propagated field (EPIC-02-DOMAIN-CONTRACTS.md §2.3). `LearningProgress` never reads `LanguageCapability` directly — it reads the already-aggregated `CrossSessionLanguageCapability` data from `LongitudinalProfile`.

---

## SECTION 6 — Persistence Strategy

### 6.1 InterviewState Field

`InterviewState.language_capabilities: tuple[LanguageCapability, ...] = ()` is introduced as a TCP field.

- Default: `()` (empty tuple).
- Written by: `reasoner_node` only (sole writer, LC-R-02).
- Read by: `reasoner_node` (for incremental context), `longitudinal_update_node` (for capture).
- Clear policy: Never cleared during the session. Retired implicitly when `InterviewState` is garbage-collected after the close cascade.

### 6.2 SessionHistory Persistence

`LanguageCapability` is **not persisted in `SessionHistory`**. The `SessionHistory` v2.0 contract (ADR-033 Decision 5, schema version `"2.0"`) is not extended to include `LanguageCapability`. This is a permanent architectural decision — not a deferral. The OI-03 resolution made this explicit and it is frozen in the EPIC-02-ARCHITECTURE-FREEZE.md.

### 6.3 KnowledgeSnapshot Persistence

`LanguageCapability` is **not embedded in `KnowledgeSnapshot`**. `KnowledgeSnapshot` carries `CandidateProfileSnapshot`, which contains `LanguageCapabilityFeature` instances in `.features` — the canonical knowledge representation. There is no separate `LanguageCapability` path in `KnowledgeSnapshot`.

### 6.4 Schema Evolution

The session-scoped `LanguageCapability` contract (`domain/contracts/language/language_capability.py`) carries `schema_version: str` (initial `"1.0"`). Schema evolution policy:

- Additive field additions with safe defaults do **not** require a version increment.
- Backward-incompatible changes require a `schema_version` increment and a new ADR.
- Because `LanguageCapability` instances are embedded in `LongitudinalSessionMetadata.language_capabilities` at contribution time, any schema change affects the interpretability of historically embedded instances. This is the replay incompatibility risk (§6.5).

### 6.5 Replay Guarantees

`LanguageCapability` provides **no replay guarantee**. It is not archived in `SessionHistory`. A replayed session cannot reconstruct `LanguageCapability` from `SessionHistory` alone. This is an accepted limitation (EPIC-02-ARCHITECTURE-FREEZE.md §5.2, §3.12).

The replay guarantee that is provided: `LongitudinalProfile.session_snapshots[n].session_metadata.language_capabilities` preserves the `LanguageCapability` instances as frozen snapshots at contribution time. These are available for historical display (e.g., Replay UI progress panel) via the `LongitudinalProfile` persistence path — not via the replay path.

---

## SECTION 7 — Architectural Invariants

### LC-R-01 — Sole Producer

`FeatureEngine` is the only component permitted to produce session-scoped `LanguageCapability` instances. No other node, service, builder, or utility may produce `LanguageCapability` in production paths.

**Verification:** Architectural import test asserts no production file outside `FeatureEngine` and its registered `FeatureUpdaters` constructs `LanguageCapability(...)` directly.

---

### LC-R-02 — Sole Writer to InterviewState

`reasoner_node` is the only component that writes `InterviewState.language_capabilities`. No other node may write this field.

**Verification:** Module docstring in `reasoner_node` declares `language_capabilities` as a write target. Architectural test asserts no other node file writes `language_capabilities` to `InterviewState`.

---

### LC-R-03 — Capture Before Expiry

`longitudinal_update_node` must read `InterviewState.language_capabilities` before `InterviewState` is released. The session close cascade order must be:

```
session_close_node → report_node → longitudinal_update_node → END
```

`session_close_node` must not clear or overwrite `language_capabilities`. `longitudinal_update_node` must execute before `InterviewState` is garbage-collected.

**Verification:** Graph topology test asserts `longitudinal_update_node` is positioned after `report_node` and before `END` in the session close cascade. Integration test asserts `language_capabilities` is present in `InterviewState` at `longitudinal_update_node` entry.

---

### LC-R-04 — Aggregation Only via LongitudinalProfileBuilder

Cross-session aggregation of `LanguageCapability` data into `CrossSessionLanguageCapability` may only be performed by `LongitudinalProfileBuilder`. No other component may aggregate language capability scores across sessions.

**Verification:** Architectural test asserts that `CrossSessionLanguageCapability` construction occurs only within `LongitudinalProfileBuilder.build()`.

---

### LC-R-05 — Not Persisted in SessionHistory

`LanguageCapability` instances must not appear as a field in `SessionHistory` or any `SessionHistory` sub-artifact (`KnowledgeSnapshot`, `CandidateProfileSnapshot`, `ScoringSnapshot`, `ScoringNarrative`, `QuestionResultRecord`).

**Verification:** Structural test asserts `SessionHistory` field set does not include any field of type `LanguageCapability` or `tuple[LanguageCapability, ...]`.

---

### LC-R-06 — Not Embedded in KnowledgeSnapshot

`LanguageCapability` must not be embedded in `KnowledgeSnapshot`. The language capability knowledge representation in `KnowledgeSnapshot` is exclusively via `LanguageCapabilityFeature` instances in `CandidateProfileSnapshot.features`.

**Verification:** Structural test asserts `KnowledgeSnapshot` field set does not include `LanguageCapability`.

---

### LC-R-07 — Language Consistency with LanguageProfile

Every `LanguageCapability.language_id` present in `InterviewState.language_capabilities` must be a member of `LanguageProfile.enabled_language_ids`. A `LanguageCapability` may not be produced for a language that was not active in the session's `LanguageProfile`.

**Verification:** `longitudinal_update_node` validates this before invoking `LongitudinalProfileBuilder`. Violation emits a `WARNING` log and excludes the offending entry from the builder input (P-06). Unit test asserts the validation and log emission.

---

### LC-R-08 — Immutability

`LanguageCapability` is `frozen=True`, `extra=forbid`. No mutation occurs after construction. The tuple in `InterviewState.language_capabilities` is replaced entirely at each `FeatureEngine` cycle — individual instances within it are never mutated.

**Verification:** `frozen=True` enforcement by Pydantic. Architectural test asserts no code path calls `model_copy` on a `LanguageCapability` instance.

---

### LC-R-09 — Empty Tuple for No-Coding Sessions

For sessions with no coding questions, `InterviewState.language_capabilities` is `()` at session close. `longitudinal_update_node` passes `language_capabilities=()` to `LongitudinalProfileBuilder`, which produces no new `CrossSessionLanguageCapability` entries for that session.

**Verification:** Unit test asserts that a session with no `LANGUAGE_*` observations produces `language_capabilities = ()` and no `CrossSessionLanguageCapability` entries in the resulting `LongitudinalProfile`.

---

### LC-R-10 — Non-Fatal Capture Failure

If `longitudinal_update_node` fails to capture `language_capabilities` (e.g., `InterviewState` is unavailable, validation fails), the node emits a structured `WARNING` log containing `candidate_identity_id`, `session_id`, and failure reason. The session report and `SessionHistory` are unaffected. The `language_capability_summary` for this session is not updated. Silent failure is a constitutional violation (P-06).

**Verification:** Unit test with mocked `InterviewState` access failure asserts `WARNING` log emission and non-fatal continuation.

---

## SECTION 8 — Consequences

### 8.1 Positive Consequences

- **`LanguageCapability` implementation is unblocked.** Runtime ownership, sole producer, sole writer, and lifecycle are formally frozen.
- **SessionHistory contract is preserved.** The OI-03 resolution is reinforced as an architectural invariant (LC-R-05), preventing future drift.
- **Cross-session aggregation path is complete.** `LanguageCapability` → `LongitudinalSessionMetadata.language_capabilities` → `CrossSessionLanguageCapability` is fully traceable and owned.
- **Language consistency is enforceable.** LC-R-07 provides a verifiable consistency gate between `LanguageProfile` configuration and `LanguageCapability` knowledge.
- **Constitution compliance confirmed.** All eight constitutional principles (P-01 through P-08) are satisfied.

### 8.2 Trade-offs

- **`LanguageCapability` data is not reconstructable from `SessionHistory[]` alone.** This is an accepted, documented limitation (EPIC-02-ARCHITECTURE-FREEZE.md §5.2). Reconstruction produces `language_capability_summary = []` for a reconstructed `LongitudinalProfile`. Architectural tests must assert this explicitly.
- **Capture failure is permanent loss.** If `longitudinal_update_node` fails, the session's language capability contribution is lost. No retry path exists within the session lifecycle (ADR-034 Decision 6). Operator-initiated reconstruction from `SessionHistory[]` cannot recover this data (due to the non-persistence in `SessionHistory`).
- **`InterviewState` gains a new field.** All `InterviewState` construction and reconstruction paths must be updated when `language_capabilities` is activated (P-08). This is bounded and predictable.

### 8.3 Explicit Non-Goals

- **This ADR does not define `LanguageCapability` field set.** The contract field inventory (`language_id`, `questions_answered_in_language`, `composite_score`, `idiomatic_usage_score`, `type_error_rate`, `schema_version`) is already specified in the existing V1.2 contract and referenced in EPIC-02-DOMAIN-CONTRACTS.md §3.1. No new fields are introduced by this ADR.
- **This ADR does not define `CrossSessionLanguageCapability` field set.** That is frozen in EPIC-02-DOMAIN-CONTRACTS.md §1.6.
- **This ADR does not modify `FeatureEngine` architecture.** The production mechanism is governed by ADR-020 and the existing `ObservationUpdater` design.
- **This ADR does not change `SessionHistory` schema.** The v2.0 contract (ADR-033) is preserved unchanged.
- **This ADR does not address V2 `LanguageCapability` replay recovery.** If V2 requires reconstructable language scores from `SessionHistory`, a new ADR crossing the `SessionHistory` Ownership Boundary (ARC-01 §3) is required.
- **This ADR does not address multi-language session `LanguageCapability` ordering.** The selection of the correct `LanguageCapability` instance for a given question in a mixed-mode session is governed by `LanguageProfile.question_language_sequence` and the `ExecutionRouting` path — not by this ADR.

---

## Mini Architecture Freeze Verification

This ADR was introduced as an additive ADR during EPIC-02 implementation (triggered by Domain Discovery Review). The following Mini Architecture Freeze verification is mandatory before implementation begins.

| Check | Result |
|---|---|
| No contradiction with ADR-019 | PASS — `LanguageCapability` as Domain artifact confirmed; language-blind boundary above evaluation reaffirmed |
| No contradiction with ADR-020 | PASS — `FeatureEngine` as sole producer confirmed (I-02 extended); no new competing production path |
| No contradiction with ADR-022 | PASS — `SessionHistory` contract unchanged; no `LanguageCapability` persistence in `SessionHistory` |
| No contradiction with ADR-033 | PASS — `SessionHistory` v2.0 schema unchanged; `ScoringSnapshot` / `ScoringNarrative` paths unaffected |
| No contradiction with ADR-034 | PASS — `LongitudinalProfileBuilder` as sole aggregator; `longitudinal_update_node` capture path aligns with Decision 1 and LP-03 |
| No contradiction with ADR-035 | PASS — `LanguageProfile`/`LanguageCapability` boundary explicitly confirmed; LC-R-07 consistency constraint aligns with LP-R-06 |
| No contradiction with ARC-01 | PASS — all P-01 through P-08 verified (see §8.1) |
| No contradictions with EPIC-02 Architecture Freeze | PASS — no frozen document is modified; additive ADR only |
| No duplicated ownership | PASS — sole producer (LC-R-01), sole writer (LC-R-02), sole aggregator (LC-R-04) |
| No replay conflict | PASS — replay does not consume `LanguageCapability`; LP-11 (ADR-034) unaffected |
| No builder conflict | PASS — no `LanguageCapabilityBuilder` introduced; production is Engine responsibility (P-05) |
| No freeze violation | PASS — all frozen documents remain internally consistent |

**Mini Architecture Freeze: PASS.**

---

## Validation Against Referenced Documents

### ADR-019 Consistency

ADR-019 Section A classifies `LanguageCapabilityFeature` as Domain Layer. ADR-019 Section H confirms `FeatureEngine` is language-independent (no branching on language name; type dispatch only). This ADR confirms `LanguageCapability` production by `FeatureEngine` follows the same type-dispatch mechanism. **No contradiction.**

### ADR-020 Consistency

ADR-020 Domain Invariant I-02 declares `FeatureEngine` as the only permitted producer of `ProfileFeature[]`. This ADR extends the same principle to `LanguageCapability` (LC-R-01). ADR-020 Section C describes `ObservationUpdater` processing `LANGUAGE_*` observation types — this is the upstream path for `LanguageCapability` production. **No contradiction.**

### ADR-022 Consistency

ADR-022 defines `SessionHistory` as write-once, self-contained, and the authoritative historical record. This ADR preserves that definition — `LanguageCapability` is explicitly excluded from `SessionHistory` (LC-R-05). **No contradiction.**

### ADR-033 Consistency

ADR-033 Decision 5 replaces `SessionHistory.evaluation_result` with `scoring_snapshot`. This ADR adds no new fields to `SessionHistory`. The `SessionHistory` v2.0 schema is unchanged. **No contradiction.**

### ADR-034 Consistency

ADR-034 Decision 1 declares `LongitudinalProfileBuilder` as sole producer and `longitudinal_update_node` as sole writer. This ADR confirms `LongitudinalProfileBuilder` as the sole cross-session aggregator of `LanguageCapability` (LC-R-04) and `longitudinal_update_node` as the capture node (LC-R-03). ADR-034 LP-03 prohibits LLM calls in `longitudinal_update_node` — this ADR requires none. **No contradiction.**

### ADR-035 Consistency

ADR-035 LP-R-06 requires `LanguageCapability.language_id` values to be a subset of `LanguageProfile.enabled_language_ids`. This ADR formalises this as LC-R-07 with an explicit verification strategy. The two invariants are complementary and non-contradictory. **No contradiction.**

### ARC-01 Architecture Constitution

| Principle | Compliance |
|---|---|
| P-01 (Runtime Computes; Projection Never Computes) | `LanguageCapability` produced during live `FeatureEngine` cycles in `reasoner_node`; never recomputed at session close or report generation |
| P-02 (Single Ownership) | Sole producer (LC-R-01), sole writer (LC-R-02), sole aggregator (LC-R-04) |
| P-03 (Immutable Domain Contracts) | `frozen=True`, `extra=forbid` (LC-R-08); tuple replaced not mutated |
| P-04 (LangGraph Is Sole Orchestrator) | All write and capture operations occur in LangGraph nodes; no service-chain orchestration |
| P-05 (Builders Assemble; Engines Compute) | No `LanguageCapabilityBuilder`; `FeatureEngine` (an Engine) produces `LanguageCapability`; `LongitudinalProfileBuilder` (a Builder) assembles the cross-session aggregate |
| P-06 (Fail Fast Over Silent Fallback) | Creation failure: `LanguageProfile` absence is fatal (LP-R-07, ADR-035); capture failure: non-fatal with `WARNING` log (LC-R-10); language consistency violation: `WARNING` log + exclusion (LC-R-07) |
| P-07 (Delete Legacy Code) | No legacy paths introduced; existing V1.2 `LanguageCapability` contract is unchanged |
| P-08 (Reconstruction Completeness) | `InterviewState.language_capabilities` field must be enumerated in all `InterviewState` reconstruction paths; `FeatureEngine` full recompute produces a complete `language_capabilities` tuple |

**Full Architecture Constitution compliance confirmed.**

---

## Acceptance Checklist

| # | Criterion | Status |
|---|---|---|
| 1 | `LanguageCapability` classified as Live Session Knowledge Artifact | FROZEN — Section 1.2 |
| 2 | Distinction from `LanguageProfile`, `LanguageCapabilityFeature`, `LanguageConfig`, `Observation`, `ProfileFeature` | FROZEN — Section 1.3 |
| 3 | Sole producer declared | FROZEN — Section 2.1 |
| 4 | Sole writer to `InterviewState` declared | FROZEN — Section 2.2 |
| 5 | Runtime readers declared | FROZEN — Section 2.3 |
| 6 | Persistence readers declared | FROZEN — Section 2.4 |
| 7 | Builder ownership declared (Engine, no separate Builder) | FROZEN — Section 2.5 |
| 8 | Ownership table complete | FROZEN — Section 2.6 |
| 9 | Creation trigger and mechanism defined | FROZEN — Section 3.1 |
| 10 | Accumulation pattern defined | FROZEN — Section 3.2 |
| 11 | Consumption (capture by `longitudinal_update_node`) defined | FROZEN — Section 3.3 |
| 12 | Persistence strategy defined (not in SessionHistory) | FROZEN — Section 3.4 |
| 13 | Replay access defined (not accessible) | FROZEN — Section 3.5 |
| 14 | Retirement defined | FROZEN — Section 3.6 |
| 15 | `InterviewState` placement justified | FROZEN — Section 4.1 |
| 16 | `KnowledgeSnapshot` exclusion justified | FROZEN — Section 4.2 |
| 17 | `SessionHistory` exclusion justified | FROZEN — Section 4.3 |
| 18 | `FeatureEngineContext` placement defined | FROZEN — Section 4.4 |
| 19 | `ObservationPipeline` placement defined | FROZEN — Section 4.5 |
| 20 | Relationship with `LanguageProfile` defined | FROZEN — Section 5.1 |
| 21 | Relationship with `EvaluationAggregateNode` defined | FROZEN — Section 5.2 |
| 22 | Relationship with `FeatureEngine` defined | FROZEN — Section 5.3 |
| 23 | Relationship with `ObservationPipeline` defined | FROZEN — Section 5.4 |
| 24 | Relationship with `KnowledgePipeline` defined | FROZEN — Section 5.5 |
| 25 | Relationship with `LongitudinalProfile` defined | FROZEN — Section 5.6 |
| 26 | Relationship with `LearningProgress` defined | FROZEN — Section 5.7 |
| 27 | `InterviewState` field strategy defined | FROZEN — Section 6.1 |
| 28 | `SessionHistory` non-persistence confirmed | FROZEN — Section 6.2 |
| 29 | `KnowledgeSnapshot` non-persistence confirmed | FROZEN — Section 6.3 |
| 30 | Schema evolution policy defined | FROZEN — Section 6.4 |
| 31 | Replay guarantee defined (none; accepted) | FROZEN — Section 6.5 |
| 32 | 10 architectural invariants with verification strategies | FROZEN — Section 7 |
| 33 | Positive consequences listed | FROZEN — Section 8.1 |
| 34 | Trade-offs listed | FROZEN — Section 8.2 |
| 35 | Non-goals explicitly declared | FROZEN — Section 8.3 |
| 36 | Mini Architecture Freeze verification passed | PASS — Mini Architecture Freeze section |
| 37 | Consistency with ADR-019 verified | PASS — Validation section |
| 38 | Consistency with ADR-020 verified | PASS — Validation section |
| 39 | Consistency with ADR-022 verified | PASS — Validation section |
| 40 | Consistency with ADR-033 verified | PASS — Validation section |
| 41 | Consistency with ADR-034 verified | PASS — Validation section |
| 42 | Consistency with ADR-035 verified | PASS — Validation section |
| 43 | Consistency with ARC-01 (P-01 through P-08) verified | PASS — Validation section |
| 44 | Consistency with EPIC-02 Architecture Freeze verified | PASS — Validation section |

**All 44 acceptance criteria satisfied.**

---

## Open Issues

None.

---

## Implementation Evidence

Architecture only. No production files modified. No tests modified.

**Review Trigger:**
- When `InterviewState.language_capabilities` field is introduced (TCP increment).
- When `FeatureEngine` is updated to produce `LanguageCapability` as a named output of the `FeatureEngine` cycle.
- When `longitudinal_update_node` is implemented and its `language_capabilities` capture path is established.
- When LC-R-07 consistency validation is implemented.
- When V2 requires `LanguageCapability` replay recovery (requires a new ADR crossing the `SessionHistory` Ownership Boundary).
