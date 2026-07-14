# ADR-035 — LanguageProfile Runtime Lifecycle

**Status:** Accepted  
**Date:** 2026-07-14  
**Owner:** Arch — Language Independence Layer  
**Epic:** EPIC-02 — Cross-Session Profile Continuity (EPIC-V13-02)  
**Preconditions:** ADR-019 (Language Independence Layer), ADR-033 (Unified Report Architecture), ADR-034 (Longitudinal Profile Ownership), ARC-01 (Architecture Constitution), EPIC-02-ARCHITECTURE-FREEZE.md declared.  
**Supersedes:** Nothing  
**Related:** ADR-019, ADR-027, ADR-028, ADR-031, ADR-034

---

## Context

The EPIC-02 Domain Discovery Review revealed that `LanguageProfile` — despite being named in ADR-019 Section A as a Domain Layer artifact and being referenced throughout the runtime flow — has no formal runtime lifecycle definition. ADR-019 defines its static responsibilities (session language configuration, immutability, layer placement) but leaves the following unspecified:

- Precise definitional boundary against adjacent artifacts (`InterviewSetup`, `LanguageConfig`, `LanguageCapability`, `LanguageCapabilityFeature`, `SessionHistory`, `KnowledgeSnapshot`)
- Sole producer, sole writer, and reader set at runtime
- Creation trigger, lifetime, immutability invariant, and deprecation rules
- Canonical runtime placement justification with rejected alternatives
- Backward compatibility and schema evolution policy
- Complete set of architectural invariants with verification strategies

`LanguageCapability` implementation is blocked until this lifecycle is frozen. This ADR resolves the gap. It is an architectural document only. No production code is introduced or modified.

---

## SECTION 1 — Purpose and Classification

### 1.1 Definition

`LanguageProfile` is the **immutable session-scoped language configuration artifact** produced at session initialisation. It encodes, for the session lifetime, the complete resolved set of language parameters: which languages are active, the primary language, the session mode, the executor reference(s), and the frozen policy references.

It answers one question and one question only: **"What is the exact language configuration under which this session was conducted?"**

### 1.2 Classification

`LanguageProfile` is a **Session Configuration Snapshot** — a subtype of Projection Artifact (OP-02, ARC-01 §5). Specifically:

- It is **immutable after construction** (`frozen=True`, `extra=forbid`).
- It carries **no live state** — it does not update as the session progresses.
- It represents the **resolved configuration** — not the user intent (that is `LanguageConfig`) and not the capability (that is `LanguageCapability`).
- It is a **Domain Layer artifact** (ADR-019 Section A, Frozen Responsibility Table).

### 1.3 Distinction from Adjacent Artifacts

| Artifact | Layer | What it represents | Relationship to LanguageProfile |
|---|---|---|---|
| `InterviewSetup` | Application | Session initialisation coordinator; consumes `LanguageConfig` and produces `LanguageProfile` | **Producer** of `LanguageProfile`; does not persist it |
| `LanguageConfig` | Application | User/CLI language configuration input; what languages are requested | **Input** to `InterviewSetup`; resolved into `LanguageProfile` at session start; not session-scoped |
| `LanguageCapability` | Domain | Session-scoped observed language competence of the candidate; derived from `FeatureEngine` | **Read** `LanguageProfile.active_language` for context; semantically orthogonal — `LanguageProfile` is configuration, `LanguageCapability` is knowledge |
| `LanguageCapabilityFeature` | Domain | `ProfileFeature` representing idiomatic language competence; produced by `FeatureEngine` | Consumes `language_context` (nullable `ProgrammingLanguage`) from `Observation` provenance; does not read `LanguageProfile` directly |
| `SessionHistory` | Domain | Immutable post-session archive; stores `LanguageProfile` as closed metadata | **Stores** `LanguageProfile` at session close; reads it as frozen metadata only |
| `KnowledgeSnapshot` | Domain | Point-in-time snapshot of accumulated knowledge (`Narrative`, `CoachingSnapshot`, `CandidateProfileSnapshot`) | Semantically disjoint; `KnowledgeSnapshot` carries knowledge derivations; `LanguageProfile` carries configuration; both are embedded in `SessionHistory` |

**Critical boundary:** `LanguageProfile` is configuration. `LanguageCapability` and `LanguageCapabilityFeature` are knowledge. These must never be conflated. Configuration is frozen at session start; knowledge accumulates throughout the session.

---

## SECTION 2 — Ownership

### 2.1 Sole Producer

**`InterviewSetup`** (Application Layer) is the sole producer of `LanguageProfile`.

`InterviewSetup` resolves `LanguageConfig` → `LanguageProfile` via the following steps:
1. Reads `LanguageConfig.enabled_languages` and resolves each `ProgrammingLanguage` from `LanguageRegistry`.
2. Applies `LanguageConfig.selection_strategy` to produce the frozen question-language sequence (for mixed-mode sessions).
3. Resolves `executor_ref` for each active language (from registered `LanguageExecutor` registry).
4. Freezes `LanguagePolicy` reference(s) for the session.
5. Constructs the immutable `LanguageProfile` via `LanguageProfileBuilder`.

No other component may produce a `LanguageProfile` instance in production paths. Direct Pydantic instantiation is prohibited in production code.

### 2.2 Sole Writer

**`reasoner_node`** (or its equivalent session-start node in the LangGraph session lifecycle) is the sole writer of `LanguageProfile` to `InterviewState`. It writes `InterviewState.language_profile` exactly once — at session initialisation — and never again.

This is a consequence of P-02 (Single Ownership, ARC-01 §2) and OP-04 (Sole Writer Node, ARC-01 §5).

### 2.3 Runtime Readers

| Reader | Layer | Purpose |
|---|---|---|
| `QuestionSelection` | Application | Reads `language_profile.active_language` or `language_profile.question_language_sequence` to route question selection |
| `ExecutionRouting` | Application | Reads `language_profile.executor_ref` to dispatch code execution to the correct `LanguageExecutor` |
| `ReportConfiguration` | Application | Reads `language_profile` to assemble `language_context` metadata in the report |
| `EvaluationEngine` | Application/Domain boundary | Reads `language_profile.evaluation_policy_ref` to apply the correct `LanguagePolicy` |
| `ObservationExtractor` | Domain | Reads `language_profile.active_language` to assign `language_context` to `Observation` instances |
| `longitudinal_update_node` | Application | Reads `InterviewState.language_profile` as part of session closure data passed to `LongitudinalProfileBuilder` |

All reads are read-only. No reader may modify `LanguageProfile` after construction.

### 2.4 Persistence Readers

| Persistence Reader | Access Path | Purpose |
|---|---|---|
| `SessionHistory` | Written into `SessionHistory` by `session_close_node` | Archived as closed metadata; enables replay fidelity |
| `ReplaySession` / `replay_node` | Read from `SessionHistory.language_profile` | Reconstructs the session's language context for controlled replay |
| `LongitudinalSessionMetadata` | Not embedded; `session_language` field carries language id only | Language identity is carried as `session_language: str` in `LongitudinalSessionMetadata`, not as a full `LanguageProfile` |

### 2.5 Ownership Table

| Ownership Role | Owner | Invariant |
|---|---|---|
| Sole producer | `InterviewSetup` (via `LanguageProfileBuilder`) | LP-R-01 |
| Sole writer to `InterviewState` | Session-start node | LP-R-02 |
| Configuration input | `LanguageConfig` | Not a writer; input only |
| Runtime reader (question routing) | `QuestionSelection` | Read-only |
| Runtime reader (execution) | `ExecutionRouting` | Read-only |
| Runtime reader (evaluation) | `EvaluationEngine` | Read-only |
| Runtime reader (observation) | `ObservationExtractor` | Read-only |
| Persistence writer | `session_close_node` (into `SessionHistory`) | LP-R-03 |
| Persistence reader (live) | `ReportConfiguration` (via `Report`) | Read-only |
| Persistence reader (replay) | `replay_node` (via `SessionHistory`) | Read-only |

---

## SECTION 3 — Lifecycle

### 3.1 Creation

**Trigger:** Session initialisation, before the first question is asked.

**Mechanism:** `InterviewSetup` receives `LanguageConfig`, resolves all language references via `LanguageRegistry`, computes the frozen question-language sequence (for mixed-mode), and invokes `LanguageProfileBuilder.build()`.

**Preconditions at creation:**
- `LanguageConfig.enabled_languages` is non-empty and all entries are registered in `LanguageRegistry`.
- `LanguageConfig.primary_language` is one of the enabled languages.
- At least one `LanguageExecutor` is registered for each enabled language.
- A valid `LanguagePolicy` version exists for each enabled language.

**Failure at creation:** A creation failure (invalid config, unregistered language, missing executor) must raise an explicit, descriptive exception before session start. The session must not proceed with an absent or partially constructed `LanguageProfile`. This satisfies P-06 (Fail Fast, ARC-01 §2).

### 3.2 Runtime Lifetime

`LanguageProfile` is **session-scoped**. It is created once at session initialisation and persists for the entire session lifetime. It is never updated, regenerated, or replaced during an active session.

Its runtime lifetime is bounded by:
- **Start:** Construction by `InterviewSetup` at session initialisation.
- **End:** Embedding into `SessionHistory` by `session_close_node` at session close; `InterviewState.language_profile` may be considered expired after `session_close_node` completes.

### 3.3 Immutability

`LanguageProfile` is `frozen=True`, `extra=forbid`. Every field is read-only after construction. No field may be updated in place or via `model_copy` for any purpose after construction.

This is an absolute invariant. No constitutional exception is available for `LanguageProfile` immutability (P-03, ARC-01 §2).

### 3.4 Consumers (Ordered by Session Phase)

| Phase | Consumer | What it consumes |
|---|---|---|
| Question assignment | `QuestionSelection` | `active_language`, `question_language_sequence` (mixed-mode), `session_mode` |
| Code execution | `ExecutionRouting` | `executor_ref` (per language) |
| Evaluation | `EvaluationEngine` | `evaluation_policy_ref` (per language), `active_language` |
| Observation extraction | `ObservationExtractor` | `active_language` → `language_context` assignment |
| Report assembly | `ReportConfiguration` | Full `LanguageProfile` for metadata fields |
| Session close | `session_close_node` | Embeds into `SessionHistory` |
| Longitudinal update | `longitudinal_update_node` | Reads `session_language` (string) from metadata; does not carry full `LanguageProfile` |
| Replay | `replay_node` | Reads from `SessionHistory.language_profile`; reconstructs execution routing |

### 3.5 Persistence

`LanguageProfile` is persisted as an embedded field within `SessionHistory` by `session_close_node`. It is not persisted independently. It is not stored in any separate table, file, or registry. Its persistence lifecycle is governed by `SessionHistory` lifecycle rules (ADR-022).

**Persistence invariant:** The `LanguageProfile` embedded in `SessionHistory` must be identical to the `LanguageProfile` that was active at session runtime. No mutation, enrichment, or recomputation occurs at close time (P-01, ARC-01 §2).

### 3.6 Replay

`LanguageProfile` embedded in `SessionHistory` is the sole source for replay reconstruction of the language context. `replay_node` reads it to reconstruct `ExecutionRouting` and `QuestionSelection` state for the replayed session. No `LanguageProfile` is recreated during replay — the archived instance is used directly.

This is consistent with the Replay Boundary (ARC-01 §3): replay reads from closed artifacts; it does not re-run session initialisation logic.

### 3.7 Deprecation Rules

`LanguageProfile` fields may be deprecated under the following rules only:

1. A field marked deprecated must carry a `schema_version` increment on `LanguageProfile`.
2. The deprecated field must remain present (nullable) for at least one full version lifecycle to preserve replay fidelity for existing `SessionHistory` records.
3. Removal of a deprecated field requires a new ADR declaring the `schema_version` range affected and the replay compatibility impact.
4. No field may be removed if any `SessionHistory` record with a prior `schema_version` depends on it for replay reconstruction.

---

## SECTION 4 — Runtime Placement

### 4.1 Canonical Runtime Location

`LanguageProfile` resides in **`InterviewState.language_profile`** for the duration of the session.

**Justification:**
- `InterviewState` is the authoritative session state container for all session-scoped artifacts (ARC-01 §4, P-02).
- All LangGraph nodes that consume `LanguageProfile` read it from `InterviewState`. Centralising it there satisfies OP-04 (Sole Writer Node) and makes the session's language configuration observable to any node without out-of-band lookups.
- It is set once (at initialisation) and read N times — a pattern that `InterviewState` is specifically designed to host.

### 4.2 Rejected Alternative Locations

| Alternative | Rejected Because |
|---|---|
| Embedded in `LanguageConfig` | `LanguageConfig` is Application-layer input, not session state. It may be destroyed or replaced between sessions. It is not available to Domain-layer nodes. |
| Embedded in `InterviewSetup` as instance state | `InterviewSetup` is a stateless Application-layer coordinator. Retaining state there violates SRP and makes `LanguageProfile` inaccessible to nodes that do not hold an `InterviewSetup` reference. |
| Passed as a parameter to each consuming node | Creates implicit coupling between the graph topology and the parameter-passing mechanism. Violates the LangGraph state-as-sole-communication-channel principle. |
| Stored in a session-scoped registry (separate from `InterviewState`) | Introduces a second session state container; creates dual-source risk; violates P-02 (Single Ownership). |
| Reconstructed from `LanguageConfig` on every access | `LanguageConfig` may not be available during the session (it is a pre-session input). Reconstruction on every access is computation in projection (violates P-01). |
| Embedded in `CandidateProfile` or `ObservationStore` | Category error. `LanguageProfile` is configuration; `CandidateProfile` and `ObservationStore` are knowledge accumulation artifacts. Conflating them violates SRP. |

---

## SECTION 5 — Relationships with Other Artifacts

### 5.1 InterviewState

`LanguageProfile` is a field of `InterviewState` (`InterviewState.language_profile`). It is written once by the session-start node and read by multiple downstream nodes. No node writes a new `LanguageProfile` to `InterviewState` after initialisation.

### 5.2 InterviewSetup

`InterviewSetup` is the sole producer of `LanguageProfile`. It is an Application-layer stateless coordinator. After producing `LanguageProfile`, `InterviewSetup` has no further relationship with it.

### 5.3 LanguageConfig

`LanguageConfig` is the input from which `LanguageProfile` is derived. The relationship is:

```
LanguageConfig (Application, pre-session input)
    ↓  [resolved by InterviewSetup via LanguageRegistry]
LanguageProfile (Domain, session-scoped, immutable)
```

`LanguageProfile` is not a superset of `LanguageConfig`. It is the **resolved** version: abstract language references replaced by concrete `ProgrammingLanguage` instances, `executor_ref` populated, mixed-mode sequence computed, policy references frozen.

### 5.4 Question

`LanguageProfile` determines which language a `Question` is sourced in. `QuestionSelection` reads `language_profile.active_language` (single-language session) or `language_profile.question_language_sequence` (mixed-mode session) to select from the correct language bucket in `QuestionRepository`. The `Question` artifact itself is not modified by `LanguageProfile` — the profile influences selection, not content.

### 5.5 ExecutionResult

`ExecutionResult` carries `language_id` which must match `LanguageProfile.active_language` for the question being evaluated. The correspondence is enforced by `ExecutionRouting`, which reads `LanguageProfile.executor_ref` to dispatch to the correct `LanguageExecutor`. `ExecutionResult` does not import or reference `LanguageProfile`.

### 5.6 QuestionResult

`QuestionResult` (session-scoped per-question result) carries the outcome of evaluation for one question. It does not directly reference `LanguageProfile`. The language context of a `QuestionResult` is traceable through `ExecutionResult.language_id`, which is derived from `LanguageProfile.active_language` at execution time.

### 5.7 SessionHistory

`SessionHistory` stores `LanguageProfile` as a closed metadata field (`session_history.language_profile`). This is a write-once archive — the same `LanguageProfile` instance active during the session is embedded at close time. `SessionHistory` is the only persistence boundary for `LanguageProfile`.

Per ADR-033 (Decision 5) and ADR-034 (Decision 3), `SessionHistory` is the authoritative source for replay reconstruction. The archived `LanguageProfile` enables replay to reconstruct the exact execution routing and question sequencing of the original session.

### 5.8 KnowledgeSnapshot

`KnowledgeSnapshot` (embedded in `SessionHistory`) carries `CandidateProfileSnapshot`, `Narrative`, and `CoachingSnapshot` — knowledge artifacts. `LanguageProfile` is configuration, not knowledge. They coexist in `SessionHistory` without overlap. `KnowledgeSnapshot` does not reference `LanguageProfile`. `LanguageProfile` does not reference `KnowledgeSnapshot`.

### 5.9 FeatureEngine

`FeatureEngine` does not read `LanguageProfile` directly. It reads `ObservationStore`, where each `Observation` carries `language_context: Optional[ProgrammingLanguage]` derived during `ObservationExtractor` processing. `ObservationExtractor` reads `LanguageProfile.active_language` to assign `language_context` to each extracted `Observation`. Thus `LanguageProfile` influences `FeatureEngine` output indirectly via `language_context` in `Observation` provenance — but `FeatureEngine` itself is language-blind (ADR-019 Section H).

### 5.10 ObservationPipeline

`ObservationExtractor` (within the `ObservationPipeline` or its equivalent) reads `LanguageProfile.active_language` to assign `language_context` as nullable metadata on each `Observation`. This is the last point in the pipeline where `LanguageProfile` has any direct influence. After this assignment, language identity travels only as `language_context` on `Observation` instances — not as a reference to `LanguageProfile`.

### 5.11 LanguageCapability

`LanguageCapability` is the session-scoped observed competence of the candidate in a specific language. It is produced by `FeatureEngine` from language-typed `Observation` instances. It is **semantically orthogonal** to `LanguageProfile`:

- `LanguageProfile` is **configuration** — it is set before the session starts, is language-independent of the candidate's performance, and never changes.
- `LanguageCapability` is **knowledge** — it accumulates from evidence during the session and reflects the candidate's demonstrated competence.

`LanguageCapability` reads `language_id` from `Observation.language_context.language_id` — it does not read `LanguageProfile` directly.

The `language_id` values that appear in `LanguageCapability` must be a subset of the `language_id` values in `LanguageProfile.enabled_languages`. This is a session consistency invariant (LP-R-06), not a runtime dependency.

---

## SECTION 6 — Backward Compatibility

### 6.1 Nullable Introduction Strategy

When `LanguageProfile` is introduced as a new field on `InterviewState`, it follows the TCP (Typed, Conditional, Progressive) field introduction pattern (ARC-01 §7):

1. `InterviewState.language_profile: Optional[LanguageProfile] = None` is introduced as a nullable field in a first increment.
2. In the same or immediately following increment, the session-start node is updated to produce and write `LanguageProfile` at session initialisation.
3. Any node that reads `language_profile` from `InterviewState` must guard on `language_profile is not None` and emit a `WARNING` log if it is absent (P-06).
4. Once all nodes are updated and the field is populated in all production paths, the `Optional` wrapper may be removed in a subsequent increment with a `schema_version` increment.

### 6.2 Migration Policy

`LanguageProfile` is a new artifact in V1.3 (not present in V1.2). No V1.2 `SessionHistory` records contain `LanguageProfile`. Migration policy:

- V1.2 `SessionHistory` records without `language_profile` are valid. Replay of V1.2 sessions must not require `language_profile`.
- V1.3 `SessionHistory` records include `language_profile` as a required embedded field.
- `SessionHistory.schema_version` must be incremented (to `"3.0"` if V1.3 follows the `"2.0"` increment from ADR-033) when `language_profile` is added as a required field.

### 6.3 Replay Compatibility

- V1.2 replay: `LanguageProfile` is absent from `SessionHistory`. `replay_node` treats `session_history.language_profile` as `None` and defaults to the original V1.2 single-language behaviour (Python-only implicit). This default must be documented in `replay_node` as an explicit guard clause, not a silent fallback (P-06).
- V1.3+ replay: `LanguageProfile` is present. `replay_node` reads it directly.

The V1.2 replay compatibility default must not be a permanent feature. It must carry a deletion ticket tied to the V2 migration that retires V1.2 `SessionHistory` support (P-07, ARC-01 §2).

### 6.4 Schema Evolution

`LanguageProfile` carries `schema_version: str` (initial value `"1.0"`). The versioning policy mirrors ADR-034 Decision 2:

- Additive field additions with safe defaults do **not** require a `schema_version` increment.
- Backward-incompatible changes (field removal, type change, semantic change to an existing field) require a `schema_version` increment and a new ADR before implementation.
- Replay correctness is the primary constraint on schema evolution: any change that would break replay of an existing `SessionHistory` record is backward-incompatible by definition.

---

## SECTION 7 — Architectural Invariants

### LP-R-01 — Sole Producer

`LanguageProfileBuilder` (invoked by `InterviewSetup`) is the only permitted construction path for `LanguageProfile` in production code. Direct Pydantic instantiation is prohibited in production paths.

**Verification:** Architectural import test asserts no production file constructs `LanguageProfile(...)` directly.

---

### LP-R-02 — Sole Writer to InterviewState

The session-start node is the only component that writes `InterviewState.language_profile`. No other node may write this field after initialisation.

**Verification:** Architectural test asserts no other node module writes `language_profile` to `InterviewState`. Confirmed by sole-writer documentation in the node's module docstring.

---

### LP-R-03 — Sole Persistence Writer

`session_close_node` is the only component that embeds `LanguageProfile` into `SessionHistory`. No other node, service, or builder may write `LanguageProfile` to any persistence artifact.

**Verification:** Architectural test asserts `LanguageProfile` appears in `SessionHistory` only via `session_close_node` write path.

---

### LP-R-04 — Immutability

`LanguageProfile` is `frozen=True`, `extra=forbid`. No mutation occurs after construction. No `model_copy(update=...)` call may target `LanguageProfile` at any phase of the session lifecycle.

**Verification:** `frozen=True` enforcement by Pydantic at runtime. Architectural test asserts no code path calls `model_copy` on a `LanguageProfile` instance.

---

### LP-R-05 — Write-Once to InterviewState

`InterviewState.language_profile` is written exactly once (at session initialisation). Any code path that would write `language_profile` a second time to `InterviewState` is a constitutional violation of P-02.

**Verification:** Unit test confirms that attempting to write `language_profile` after initialisation raises a detectable assertion or guard error.

---

### LP-R-06 — Language Consistency with LanguageCapability

If `LanguageCapability` instances are produced for a session, every `LanguageCapability.language_id` must be a member of `LanguageProfile.enabled_language_ids`. A `LanguageCapability` may not appear for a language that was not active in the session's `LanguageProfile`.

**Verification:** `longitudinal_update_node` validates this consistency before invoking `LongitudinalProfileBuilder`. A violation emits a `WARNING` log (P-06).

---

### LP-R-07 — Creation Failure is Fatal

If `LanguageProfileBuilder.build()` fails (invalid config, unregistered language, missing executor), the failure must raise an explicit exception that prevents session start. Silent fallback to a default language configuration is a constitutional violation of P-06.

**Verification:** Unit test asserts creation failure raises a descriptive exception before any `InterviewState` is constructed.

---

### LP-R-08 — Replay Archive Fidelity

The `LanguageProfile` embedded in `SessionHistory` must be byte-for-byte equivalent to the `LanguageProfile` that was active at session runtime. No enrichment, recomputation, or substitution is permitted at session close time (P-01).

**Verification:** Integration test asserts that `session_history.language_profile == interview_state.language_profile` after `session_close_node` completes.

---

### LP-R-09 — No Language-Specific Logic After Evaluation Boundary

No component above the evaluation boundary (as defined in ADR-019 Section H) may branch on `LanguageProfile.active_language` or any `language_id` field for structural logic. `LanguageProfile` may be read for metadata display (e.g., report language context) but not for branching.

**Verification:** Code review gate. Architectural test asserts that no file under `domain/features/`, `domain/knowledge/`, `services/narrative/`, `services/coaching/`, or `app/ui/` imports `LanguageProfile` for conditional branching purposes.

---

### LP-R-10 — Schema Version Immutability After Construction

`LanguageProfile.schema_version` is set by `LanguageProfileBuilder` and is immutable after construction. It must never be overwritten by any consumer, reader, or serialisation step.

**Verification:** `frozen=True` enforcement. Unit test asserts `schema_version` is identical before and after serialisation/deserialisation round-trip.

---

## SECTION 8 — Consequences

### 8.1 Positive Consequences

- **`LanguageCapability` implementation is unblocked.** The formal lifecycle makes the boundary between `LanguageProfile` (configuration) and `LanguageCapability` (knowledge) unambiguous.
- **Replay fidelity is guaranteed.** The archive invariant (LP-R-08) ensures that replayed sessions use the exact same language routing as the original.
- **Language consistency is verifiable.** LP-R-06 ensures that any `LanguageCapability` produced in a session is traceable to an active `LanguageProfile` entry.
- **Single-source clarity.** All consumers of session language configuration read from one location (`InterviewState.language_profile`); no lookup, no recomputation, no ambiguity.
- **Constitution compliance confirmed.** All eight constitutional principles (P-01 through P-08) are satisfied without exception.

### 8.2 Trade-offs

- **`InterviewState` gains a new required field.** All `InterviewState` construction paths must be updated when `language_profile` is activated (P-08). This is bounded and predictable.
- **`SessionHistory.schema_version` must increment.** Embedding `language_profile` as a required field in `SessionHistory` is a breaking schema change; this must be coordinated with ADR-033 Decision 5 migration increments.
- **V1.2 replay compatibility requires an explicit guard.** The V1.2 `SessionHistory` records without `language_profile` require a documented default in `replay_node`. This guard carries a deletion ticket (P-07).

### 8.3 Explicit Non-Goals

- **This ADR does not define `LanguageProfileBuilder` field set.** The complete field inventory of `LanguageProfile` is a Domain Contracts specification concern, not an ADR concern.
- **This ADR does not define `LanguageCapability` contracts.** That is the subject of the EPIC-02 Domain Contracts specification (EPIC-02-DOMAIN-CONTRACTS.md) and the implementation artifacts derived from it.
- **This ADR does not modify `LanguageConfig`.** `LanguageConfig` is frozen in ADR-019 Section E. No fields are added or removed.
- **This ADR does not change the mixed-mode selection policy.** That is frozen in ADR-019 Section F and ADR-028.
- **This ADR does not introduce `LanguageProfile` storage.** `LanguageProfile` is not persisted independently; its persistence lifecycle is governed entirely by `SessionHistory`.
- **This ADR does not define the `schema_version` increment coordinate.** That is a Domain Contracts and migration ticket concern tied to the implementation increment.

---

## Validation Against Referenced Documents

### ADR-019 Consistency

ADR-019 Section A names `LanguageProfile` as a Domain Layer artifact with the responsibility "Immutable session language configuration." This ADR is fully consistent with that declaration and provides the lifecycle depth that ADR-019 deferred.

ADR-019 Section C states: "`InterviewSetup` consumes `LanguageConfig`, produces `LanguageProfile` (immutable session config)." This ADR formalises that production relationship as LP-R-01 and LP-R-02.

ADR-019 Section J (Runtime Architecture Validation) shows `LanguageProfile` in the runtime flow. This ADR confirms the same flow with formal lifecycle annotations.

**No contradiction with ADR-019.**

### ADR-033 Consistency

ADR-033 Decision 5 states `SessionHistory.evaluation_result` is replaced by `SessionHistory.scoring_snapshot`. This ADR adds `language_profile` as a further `SessionHistory` field. These are additive and non-contradictory.

ADR-033 Decision 6 defines the `SessionHistory v2.0` schema. The addition of `language_profile` as a required field (this ADR) requires a further `schema_version` increment (to `"3.0"` or the next declared version). This is anticipated by ADR-033's migration framework and does not contradict it.

**No contradiction with ADR-033.**

### ADR-034 Consistency

ADR-034 Decision 3 states: "Every field of `LongitudinalProfile` that is derived from session data must trace to a field of `SessionHistory`." The `language_id` carried in `LongitudinalSessionMetadata.session_language` traces to `SessionHistory.language_profile.active_language`. This is consistent.

ADR-034 EPIC-02-ARCHITECTURE-FREEZE.md §3.10 notes that `LanguageCapability` lifecycle is architecturally coherent, with `longitudinal_update_node` capturing session-scoped `LanguageCapability` instances from live `InterviewState` before session close. This ADR confirms (LP-R-06) that `LanguageCapability.language_id` values must be a subset of `LanguageProfile.enabled_language_ids` — a consistency constraint that `longitudinal_update_node` can enforce.

**No contradiction with ADR-034.**

### ARC-01 Architecture Constitution Consistency

| Principle | Compliance |
|---|---|
| P-01 (Runtime Computes; Projection Never Computes) | `LanguageProfile` is constructed at session start (runtime); never recomputed at session close or projection. LP-R-08 enforces archive fidelity. |
| P-02 (Single Ownership) | Sole producer (LP-R-01), sole writer to `InterviewState` (LP-R-02), sole persistence writer (LP-R-03). |
| P-03 (Immutable Domain Contracts) | `frozen=True`, `extra=forbid` (LP-R-04). |
| P-04 (LangGraph Is Sole Orchestrator) | `LanguageProfile` is written by a LangGraph node (session-start); all consumers are nodes or node-invoked services. |
| P-05 (Builders Assemble; Engines Compute) | `LanguageProfileBuilder` contains no computation; `InterviewSetup` computes the resolved configuration and passes pre-computed inputs to the builder. |
| P-06 (Fail Fast Over Silent Fallback) | Creation failure is fatal (LP-R-07); absent `language_profile` on `InterviewState` emits `WARNING`; replay default is documented and deletion-ticketed. |
| P-07 (Delete Legacy Code) | V1.2 replay compatibility guard carries a deletion ticket (§6.3). |
| P-08 (Reconstruction Completeness) | `InterviewState` reconstruction paths must enumerate `language_profile` explicitly; all fields are tracked. |

**Full Architecture Constitution compliance confirmed.**

### EPIC-02 Architecture Freeze Consistency

The EPIC-02 Architecture Freeze (EPIC-02-ARCHITECTURE-FREEZE.md) was declared on 2026-07-14 for the longitudinal profile planning set. This ADR is additive — it does not modify any frozen document. It resolves a gap identified by the Domain Discovery Review that was outside the EPIC-02 frozen set. It does not require a Freeze Integrity Check against the frozen set.

**No conflict with EPIC-02 Architecture Freeze.**

---

## Acceptance Checklist

| # | Criterion | Status |
|---|---|---|
| 1 | `LanguageProfile` classified as Session Configuration Snapshot | FROZEN — Section 1.2 |
| 2 | Distinction from `InterviewSetup`, `LanguageConfig`, `LanguageCapability`, `LanguageCapabilityFeature`, `SessionHistory`, `KnowledgeSnapshot` | FROZEN — Section 1.3 |
| 3 | Sole producer declared | FROZEN — Section 2.1 |
| 4 | Sole writer to `InterviewState` declared | FROZEN — Section 2.2 |
| 5 | Runtime readers declared | FROZEN — Section 2.3 |
| 6 | Persistence readers declared | FROZEN — Section 2.4 |
| 7 | Ownership table complete | FROZEN — Section 2.5 |
| 8 | Creation trigger and preconditions defined | FROZEN — Section 3.1 |
| 9 | Runtime lifetime bounded | FROZEN — Section 3.2 |
| 10 | Immutability invariant stated | FROZEN — Section 3.3 |
| 11 | Consumer sequence (ordered by session phase) defined | FROZEN — Section 3.4 |
| 12 | Persistence boundary defined | FROZEN — Section 3.5 |
| 13 | Replay lifecycle defined | FROZEN — Section 3.6 |
| 14 | Deprecation rules defined | FROZEN — Section 3.7 |
| 15 | Canonical runtime placement declared with justification | FROZEN — Section 4.1 |
| 16 | Alternative placements explicitly rejected | FROZEN — Section 4.2 |
| 17 | Relationships with all 11 required artifacts defined | FROZEN — Section 5 |
| 18 | Nullable introduction strategy defined | FROZEN — Section 6.1 |
| 19 | Migration policy defined | FROZEN — Section 6.2 |
| 20 | Replay compatibility defined | FROZEN — Section 6.3 |
| 21 | Schema evolution policy defined | FROZEN — Section 6.4 |
| 22 | 10 architectural invariants defined with verification strategies | FROZEN — Section 7 |
| 23 | Positive consequences listed | FROZEN — Section 8.1 |
| 24 | Trade-offs listed | FROZEN — Section 8.2 |
| 25 | Non-goals explicitly declared | FROZEN — Section 8.3 |
| 26 | Consistency with ADR-019 verified | PASS — Validation section |
| 27 | Consistency with ADR-033 verified | PASS — Validation section |
| 28 | Consistency with ADR-034 verified | PASS — Validation section |
| 29 | Consistency with ARC-01 verified (P-01 to P-08) | PASS — Validation section |
| 30 | Consistency with EPIC-02 Architecture Freeze verified | PASS — Validation section |

**All 30 acceptance criteria satisfied.**

---

## Open Issues

None.

---

## Implementation Evidence

Architecture only. No production files modified. No tests modified.

**Review Trigger:**
- When `LanguageProfileBuilder` field set is specified (Domain Contracts increment).
- When `LanguageCapability` implementation begins (LP-R-06 verification path is established).
- When `InterviewState.language_profile` field is introduced (TCP increment).
- When `SessionHistory` schema is incremented to include `language_profile` as a required field.
- When V1.2 replay compatibility default is deleted (P-07 deletion ticket resolved).
