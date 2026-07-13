# ADR-034 — Longitudinal Profile Ownership

**Status:** Accepted  
**Date:** 2026-07-14  
**Owner:** Arch  
**Epic:** EPIC-V13-02 — Cross-Session Profile Continuity  
**Precondition:** EPIC-02-LONGITUDINAL-PROFILE.md frozen; EPIC-01 closed; `SessionHistory` v2.0 active; `CandidateIdentity` (ADR-016A) and `CandidateProfileSnapshot` (ADR-022) frozen.

---

## Context

The architecture planning document (EPIC-02-LONGITUDINAL-PROFILE.md) identified five open decisions that must be frozen before implementation can begin:

1. `LongitudinalProfile` ownership model (producer, sole writer, readers).
2. Artifact lifecycle (creation, update, replacement, persistence boundary).
3. Relationship with `SessionHistory` (source of truth, reconstruction guarantee, immutability).
4. Relationship with `CandidateIdentity` (ownership, V2 migration path, anonymous identity guarantee).
5. `LearningProgress` input source: `SessionHistory[]` or `LongitudinalProfile`.
6. Failure semantics (non-fatal vs fail-fast, observable failure, retry).
7. Replay interaction (whether replay consumes `LongitudinalProfile` or reconstructs exclusively from `SessionHistory`).
8. Persistence boundary (architectural ownership only; no storage implementation decisions).
9. Architectural invariants.

This ADR freezes all nine decisions. No decision in this ADR may be overridden without a new ADR that explicitly supersedes the affected decision.

---

## Decision 1 — LongitudinalProfile Ownership

**Decision:**

- **Sole producer:** `LongitudinalProfileBuilder` — a `frozen=True`, `extra=forbid` Builder that assembles a new `LongitudinalProfile` from a prior profile (or `None` for the first session) and a new `CandidateProfileSnapshot`. The Builder contains no computation logic, no LLM calls, and no conditional derivation (P-05). Its sole responsibility is to collect pre-assembled inputs and construct the immutable artifact.

- **Sole writer (runtime):** `longitudinal_update_node` — a new LangGraph node positioned after `report_node` in the session close cascade. This node is the **only** component permitted to write a `LongitudinalProfile` to the persistence layer or to `InterviewState`. No other node, service, pipeline, or builder may write `LongitudinalProfile` to any store.

- **Declared readers:**
  - `LearningProgressBuilder` (see Decision 5).
  - `ProgressTracker` service — reads `LongitudinalProfile` to derive behavioral trend data.
  - Unified Report layer (EPIC-05) — reads `LongitudinalProfile` for the progress trend panel.
  - No reader may modify `LongitudinalProfile`. All reads are read-only.

- **`CandidateProfileSnapshot` ownership:** Unchanged from V1.2. The sole producer remains `FeatureEngine` (via `CandidateProfileBuilder`) at session close. EPIC-02 only reads it.

- **`InterviewState` field:** `longitudinal_update_node` does not write a `LongitudinalProfile` reference to `InterviewState`. The longitudinal profile is a cross-session artifact persisted outside session state. No `InterviewState` field for `LongitudinalProfile` is introduced. `longitudinal_update_node` reads `InterviewState.session_history` (sole reader, read-only) and produces no new `InterviewState` fields.

### Rationale

Placing the write in a dedicated node satisfies P-02 (Single Ownership) and P-04 (LangGraph as Sole Orchestrator). Keeping `LongitudinalProfile` out of `InterviewState` avoids inflating session state with a candidate-scoped artifact whose lifecycle spans sessions, not the current session. All downstream consumers of `LongitudinalProfile` access it via the persistence layer (read path), not via `InterviewState`.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Embed `LongitudinalProfile` in `InterviewState` | Session state is session-scoped; `LongitudinalProfile` is candidate-scoped; embedding it conflates lifecycles |
| Write from `session_close_node` | `session_close_node` is already the sole writer of `session_history`; adding a second artifact violates SRP and complicates the sole-writer declaration |
| Write from a service called by `report_node` | Violates P-04; services are not orchestrators; calling a persistence write from a service embedded in a node creates hidden orchestration |

---

## Decision 2 — Artifact Lifecycle

**Decision:**

| Phase | State | Mechanism |
|---|---|---|
| Before first session | Does not exist | No record in persistence for `candidate_identity_id` |
| After first session | Created | `longitudinal_update_node` receives `prior_profile=None`; `LongitudinalProfileBuilder` produces a profile with one `CandidateProfileSnapshot`; written to persistence |
| After each subsequent session | Replaced | New `LongitudinalProfile` instance produced with prior snapshots + new snapshot; prior instance superseded in persistence (replace, not append) |
| At report render time | Read-only | Retrieved from persistence by `LearningProgressBuilder` / `ProgressTracker`; never written |
| At replay time | Not accessed | Replay path reconstructs exclusively from `SessionHistory` (see Decision 7) |

**Schema versioning policy:**

- Initial schema version: `"1.0"`.
- A schema version increment is triggered when: (a) the set of fields on `LongitudinalProfile` changes in a backward-incompatible way, or (b) the accumulation unit (`CandidateProfileSnapshot`) adds fields that alter the longitudinal semantics of an existing profile.
- Additive field additions with safe defaults do **not** require a version increment.
- When a version increment is required, a new ADR is mandatory before implementation begins. The ADR must specify the migration path for existing persisted profiles.
- `schema_version` is a required field on `LongitudinalProfile`, initialized to `"1.0"`. It is set by `LongitudinalProfileBuilder` and is immutable after construction.

**ADR-033 review trigger resolved:** ADR-033 noted that EPIC-02 must confirm whether `SessionHistory.scoring_snapshot` field set is sufficient for longitudinal needs. **Decision:** `LongitudinalProfile` does not embed or carry `ScoringSnapshot` data. Its accumulation unit is `CandidateProfileSnapshot` (knowledge features), not scoring data. Scoring trend information (if needed by EPIC-05) is available from `SessionHistory.scoring_snapshot` directly, not via `LongitudinalProfile`. The `ScoringSnapshot` field set is therefore not a constraint on this ADR.

### Rationale

Replace-on-update (rather than append-to-existing) preserves `frozen=True` semantics. Each persisted version is a complete, self-contained snapshot of the candidate's accumulated knowledge at that point. This makes the record queryable, reconstructible, and auditable without joining multiple records.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| Append new snapshots to an existing mutable record | Violates P-03 (Immutable Domain Contracts); in-place mutation of a domain artifact is constitutionally prohibited |
| Persist individual `CandidateProfileSnapshot` records and assemble on read | Increases read-path complexity; the assembled view must be produced at write time to maintain determinism; assembly on read is projection-layer computation (P-01 violation if non-trivial) |

---

## Decision 3 — Relationship with SessionHistory

**Decision:**

- `SessionHistory` is the **authoritative source of truth** for each session's contribution to `LongitudinalProfile`. Every field of `LongitudinalProfile` that is derived from session data must trace to a field of `SessionHistory`.

- `LongitudinalProfile` is **derived from** `SessionHistory`; it does not replace it. If `LongitudinalProfile` is lost or corrupted, it is fully reconstructible from the ordered sequence of `SessionHistory` records for a `candidate_identity_id`.

- **Reconstruction guarantee:** Processing `SessionHistory[]` ordered by `interview_index` ascending, extracting `knowledge_snapshot.profile_snapshot` from each, and applying `LongitudinalProfileBuilder` cumulatively produces a `LongitudinalProfile` identical to the one the normal update path would have produced. This guarantee is constitutional (P-08: Reconstruction Completeness) and must be verified by an architectural test.

- **Immutability boundary:** `longitudinal_update_node` reads `InterviewState.session_history` as a read-only input. It never writes to `SessionHistory`. The `SessionHistory` contract (ADR-022, schema v2.0) is unchanged by EPIC-02.

- **Gap detection:** When `LongitudinalProfile.session_count` is less than the number of `SessionHistory` records for the same `candidate_identity_id`, the profile is out-of-sync. The persistence layer must expose a query that enables this comparison. Detection triggers an observable warning (P-06) and enables operator-initiated reconstruction.

### Rationale

Deriving `LongitudinalProfile` from `SessionHistory` rather than treating it as an independent primary record ensures that `SessionHistory` remains the single system of record for session knowledge. If the two diverge, `SessionHistory` wins. This is consistent with V1.2's "Deletion Is Completion" principle — no derived artifact supersedes its source.

---

## Decision 4 — Relationship with CandidateIdentity

**Decision:**

- **Ownership:** `LongitudinalProfile` belongs to exactly one `CandidateIdentity`. The relationship is declared by `candidate_identity_id` (a required, immutable field on `LongitudinalProfile`). No `LongitudinalProfile` may exist without a valid `candidate_identity_id`. The reverse is also true: a `CandidateIdentity` may have zero or one `LongitudinalProfile` (zero before the first session; one thereafter).

- **Anonymous identity guarantee:** `CandidateIdentity` in V1.3 is anonymous — it is a uuid4 with no external authentication backing. `LongitudinalProfile` inherits this property. The `candidate_identity_id` is treated as an opaque, stable key. No component may assume that this key maps to an external user identity. No authentication check is implied by its presence.

- **V1.3 invariant:** `candidate_identity_id` is assigned once at session creation (by `InterviewStateFactory`), is immutable for the session lifetime, and is propagated unchanged to `SessionHistory` and `LongitudinalProfile`. It is never re-assigned or re-generated between sessions for the same candidate.

- **V2 migration strategy:** V2 is expected to introduce an authenticated identity layer (login, external identity provider). The V2 migration path is:
  1. Introduce an `external_identity_id: Optional[str]` field on `CandidateIdentity` (additive; no breaking change).
  2. Link `external_identity_id` to `candidate_identity_id` via a mapping table in the V2 identity layer.
  3. `LongitudinalProfile` continues to use `candidate_identity_id` as its primary key; the V2 identity layer maps external identities to `candidate_identity_id` for cross-session queries.
  4. No `LongitudinalProfile` field changes are required for this migration. The schema version does not increment.
  
  This migration path is documented here but **not implemented** in V1.3. Any V1.3 component that assumes `candidate_identity_id` equals an external user identifier is constitutionally incorrect.

### Rationale

Treating `candidate_identity_id` as opaque and stable allows `LongitudinalProfile` to survive the V2 identity migration without a breaking schema change. The V2 mapping layer sits between the authenticated identity and the `candidate_identity_id`, leaving the knowledge layer unchanged. This is consistent with the Master Plan's explicit deferral of `CandidateIdentity` federation to V2.

---

## Decision 5 — LearningProgress Input Source

**Decision:** `LearningProgress` is derived from **`LongitudinalProfile`**, not from `SessionHistory[]`.

`LearningProgressBuilder` reads the persisted `LongitudinalProfile` for a `candidate_identity_id` and assembles `LearningProgress` from the embedded `CandidateProfileSnapshot` sequence. It no longer reads `SessionHistory[]` directly.

**Boundary condition:** If no `LongitudinalProfile` exists for a `candidate_identity_id` (first session in progress, or update failure), `LearningProgressBuilder` returns an empty `LearningProgress` with `session_count = 0`. It does not fall back to `SessionHistory[]`. This fail-fast behaviour is observable.

**`LearningProgress` structural extension:** `LearningProgress` is extended to carry behavioral trend fields derived from `CandidateProfileSnapshot.features` across sessions. The field set extension is a Domain Contracts specification concern (next planning document) and is not decided here. The architectural decision is that `LongitudinalProfile` is the input source.

### Rationale

| Criterion | `SessionHistory[]` source | `LongitudinalProfile` source |
|---|---|---|
| Read cost | O(n sessions) records read per query | O(1) record read per query |
| Consistency | Requires re-assembly on every read; risk of divergence if assembly logic changes | Pre-assembled; consistent with the persisted accumulation |
| Single source of truth | `LearningProgressBuilder` becomes a second assembler of the same data as `LongitudinalProfile` | `LearningProgress` is derived from `LongitudinalProfile`, which is itself derived from `SessionHistory`; one assembly chain |
| Replay compatibility | `SessionHistory[]` is always available; no dependency on longitudinal persistence | Requires longitudinal persistence to be functional |

The performance argument is decisive for V1.3: as session count grows, re-reading all `SessionHistory` records for a progress query is O(n). Reading a single `LongitudinalProfile` record is O(1). The reconstruction guarantee (Decision 3) ensures that if `LongitudinalProfile` is unavailable, it can be rebuilt from `SessionHistory[]` as an operator action — not as a normal read path.

The consistency argument is equally decisive: if two components independently assemble "the longitudinal view" from `SessionHistory[]`, any change to assembly logic must be applied in both places. Deriving from a single pre-assembled artifact eliminates this coupling.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| `LearningProgressBuilder` reads `SessionHistory[]` | O(n) read cost; dual assembly path (same data assembled in two places); coupling between `LearningProgressBuilder` and `SessionHistory` schema |
| `LearningProgressBuilder` reads both | Violates single-source principle; inconsistency risk if the two sources diverge |

---

## Decision 6 — Failure Semantics

**Decision:**

- **`longitudinal_update_node` is non-fatal.** If the node fails for any reason (persistence unavailable, `LongitudinalProfileBuilder` validation failure, schema mismatch, I/O error), the node emits a structured log at `WARNING` level minimum and returns without modifying `InterviewState`. The session lifecycle continues to `END`. No rollback of `SessionHistory` or `Report`. No exception propagates to the session layer.

- **Observable failure invariant:** Every failure path in `longitudinal_update_node` must emit a structured log event containing: `candidate_identity_id`, `interview_index`, `session_id`, failure reason, and timestamp. Silent failure is a constitutional violation (P-06). A failure that does not emit this event is a bug, not a design choice.

- **Retry semantics:** No automatic retry within the session lifecycle. A failed update is detectable via logs and via the gap detection mechanism (Decision 3). Retry is an operator action: the reconstruction procedure reads `SessionHistory[]` for the candidate and produces a fresh `LongitudinalProfile`. This reconstruction is the retry mechanism.

- **`LearningProgressBuilder` failure semantics:** If `LongitudinalProfile` is unavailable or absent, `LearningProgressBuilder` returns an empty `LearningProgress` (`session_count = 0`, empty `session_entries`). It emits a structured log at `WARNING` level. It does not fall back to `SessionHistory[]` reads. The empty `LearningProgress` is surfaced in the UI as "Insufficient session data" — never as a runtime error visible to the candidate.

- **`ProgressTracker` failure semantics:** If `LongitudinalProfile` is unavailable, `ProgressTracker` returns `LearningProgress.is_empty = True`. Observable. Non-fatal. The report renders with a progress panel in the "Insufficient data" state.

### Rationale

Non-fatal semantics for `longitudinal_update_node` protects session delivery from infrastructure failures. The session close sequence — `session_close_node → report_node` — is complete before the longitudinal update runs. A candidate whose session completes successfully must receive their report regardless of longitudinal persistence state. The longitudinal update is a best-effort operation at the tail of the close cascade.

The prohibition on `SessionHistory[]` fallback in `LearningProgressBuilder` is deliberate: falling back silently would make the failure of `longitudinal_update_node` invisible to operators. Surfacing "Insufficient data" makes the failure detectable without exposing internal state to the candidate.

---

## Decision 7 — Replay Interaction

**Decision:** Replay **does not consume `LongitudinalProfile`**. Replay reconstructs exclusively from `SessionHistory` (specifically `SessionHistory.knowledge_snapshot`).

`ReplaySession`, `replay_node` (EPIC-03), and all replay contracts (`ReplayContext`, `ReplayResult`, `ReplayManifest`) have no dependency on `LongitudinalProfile`. The replay path is constitutionally session-scoped: it reconstructs one session at a time from its closed `SessionHistory`.

**Progress panel in Replay UI (EPIC-04):** The Replay UI may display a progress trend panel. If it does, that panel's data is sourced from `LearningProgress` (derived from `LongitudinalProfile`), not from the replay path itself. The replay path produces session-scoped knowledge (`ReplayResult`). The progress trend is a separate query to the persistence layer. These are two independent data fetches — the replay path does not orchestrate both. This is a concern for EPIC-04/05 UI design, not for the replay or longitudinal contracts.

**Invariant:** No replay contract may import or reference `LongitudinalProfile`. No `LongitudinalProfile` contract may import or reference any replay contract. The boundary is clean and bidirectional.

### Rationale

Replay is constitutionally session-scoped (Architecture Constitution §5, Replay Boundary). The Replay Boundary separates the live computation path from the controlled reconstruction path. `LongitudinalProfile` spans sessions — it crosses the Replay Boundary by definition. Introducing a dependency from replay to `LongitudinalProfile` would require crossing that boundary with an ADR. There is no architectural benefit from this coupling: the progress trend panel is a UI composition concern, not a replay concern.

### Alternatives Considered

| Option | Rejected Because |
|---|---|
| `replay_node` reads `LongitudinalProfile` and embeds it in `ReplayResult` | Couples session-scoped replay to candidate-scoped persistence; crosses Replay Boundary without justification; violates single-responsibility of `ReplayResult` |
| `ReplayContext` carries `LongitudinalProfile` as optional | Makes `LongitudinalProfile` an optional input to replay; callers must then decide whether to populate it; adds accidental coupling with no replay-specific benefit |

---

## Decision 8 — Persistence Boundary

**Decision:**

- `LongitudinalProfile` is owned by the **domain layer** (domain contract) and persisted by the **infrastructure layer** (persistence adapter). The boundary between these layers is a repository interface declared in the domain layer (`LongitudinalProfileRepository`) and implemented in the infrastructure layer.

- The domain layer declares: the contract (`LongitudinalProfile`), the builder (`LongitudinalProfileBuilder`), and the repository interface (`LongitudinalProfileRepository` with `get(candidate_identity_id: str) → Optional[LongitudinalProfile]` and `save(profile: LongitudinalProfile) → None`).

- The infrastructure layer owns: the concrete storage implementation (technology choice, schema, file/table layout). The infrastructure choice — SQLite extension, file store, or other — is **not decided by this ADR**. It is decided in the Domain Contracts specification document (next planning artifact) after the field set is frozen.

- **Single persistence record per candidate:** At any given time, there is at most one persisted `LongitudinalProfile` per `candidate_identity_id`. The persistence layer must enforce this uniqueness constraint. The `save` operation replaces any existing record for the same `candidate_identity_id`.

- **No distributed state:** V1.3 is single-node, single-process. No distributed locking, no optimistic concurrency, no multi-writer scenarios. A single `longitudinal_update_node` instance processes one session close at a time. Concurrency assumptions are not required.

- **No caching layer:** `LongitudinalProfile` is read from persistence on every read. No in-process cache is introduced in V1.3. If read performance becomes a P0 issue (EPIC-09), a caching layer may be evaluated — but requires a new ADR.

### Rationale

Declaring a repository interface in the domain layer preserves the Dependency Inversion Principle: the domain does not import infrastructure. `longitudinal_update_node` depends on `LongitudinalProfileRepository` (abstract interface); the concrete implementation is injected. This is consistent with the architecture of existing V1.2 repositories.

---

## Decision 9 — Architectural Invariants

The following invariants are mandatory for `LongitudinalProfile` and its surrounding architecture. Each invariant must be enforceable by an architectural test or a runtime guard.

**LP-01 — Sole Writer.**  
`longitudinal_update_node` is the only component that calls `LongitudinalProfileRepository.save(...)`. No other node, service, builder, or test fixture may call `save` in production paths. Verified by architectural test (import graph analysis or mock assertion).

**LP-02 — Sole Builder.**  
`LongitudinalProfileBuilder` is the only construction path for `LongitudinalProfile`. Direct Pydantic instantiation of `LongitudinalProfile` is prohibited in production code. Permitted only in test fixtures.

**LP-03 — No LLM Calls.**  
The `longitudinal_update_node` and `LongitudinalProfileBuilder` must not invoke any LLM-backed service, `FeatureEngine`, `NarrativeGenerator`, `CoachingEngine`, or `KnowledgePipeline`. The update is pure assembly from pre-computed data. Verified by architectural test (analogous to domain invariant I-11 for replay).

**LP-04 — Immutability.**  
`LongitudinalProfile` is `frozen=True`, `extra=forbid`. Every field is read-only after construction. No mutation permitted at any point in any path.

**LP-05 — Identity Binding.**  
`LongitudinalProfile.candidate_identity_id` must equal `SessionHistory.candidate_identity_id` for every `CandidateProfileSnapshot` in its `profile_snapshots` tuple. A `LongitudinalProfile` may not contain snapshots from multiple candidates.

**LP-06 — Ordered Accumulation.**  
`profile_snapshots` within `LongitudinalProfile` are ordered by `CandidateProfileSnapshot.closed_at_question_index` descending (most recent first) and by `interview_index` ascending as a secondary sort. The `session_count` field must equal `len(profile_snapshots)`. Verified by `LongitudinalProfileBuilder.build()` validator.

**LP-07 — Idempotency.**  
Re-executing `longitudinal_update_node` for the same `session_id` / `interview_index` must not create a duplicate `CandidateProfileSnapshot` entry. The node guards on: if `interview_index` is already present in the persisted profile, the update is a no-op with an INFO-level log. Verified by unit test.

**LP-08 — Reconstruction Completeness.**  
`LongitudinalProfile` is fully reconstructable from `SessionHistory[]` ordered by `interview_index` ascending. The reconstruction must produce a `LongitudinalProfile` equal to the one produced by the normal update path. Verified by architectural test over a synthetic 10-session dataset.

**LP-09 — Non-Fatal Failure Observability.**  
Every failure path in `longitudinal_update_node` must emit a structured log event at `WARNING` or above. Silent failure is a constitutional violation (P-06). Verified by unit test with mocked persistence failure.

**LP-10 — Schema Version.**  
`LongitudinalProfile.schema_version` is always present, always `"1.0"` at initial implementation, and is set by `LongitudinalProfileBuilder`. It is immutable after construction. Any backward-incompatible change to the schema requires a version increment and a new ADR.

**LP-11 — Replay Independence.**  
No replay contract (`ReplayContext`, `ReplayResult`, `ReplayManifest`, `ReplaySession`, `replay_node`) may import or reference `LongitudinalProfile` or `LongitudinalProfileRepository`. No `LongitudinalProfile` contract may import or reference any replay contract. Verified by architectural import test.

**LP-12 — SessionHistory Supremacy.**  
If `LongitudinalProfile.session_count` differs from the count of `SessionHistory` records for the same `candidate_identity_id`, `SessionHistory` is authoritative. The discrepancy is detected by the gap detection mechanism and surfaced as a `WARNING` log. No component resolves this discrepancy by modifying `SessionHistory`.

---

## Review Trigger

This ADR must be revisited if:

- A V2 authentication layer is introduced and `CandidateIdentity` federation is scoped (see Decision 4 V2 migration path).
- `LongitudinalProfile` schema is changed in a backward-incompatible way (new ADR required before implementation).
- The `LearningProgressBuilder` input source decision (Decision 5) produces a P0 performance or consistency issue not anticipated here.
- A multi-writer scenario is introduced (e.g., background reconstruction job that also calls `LongitudinalProfileRepository.save` — this would violate LP-01 and requires a new ADR crossing the Ownership Boundary).
- `LongitudinalProfile` is extended to carry `ScoringSnapshot` or scoring trend data (currently out of scope per Decision 2).
- EPIC-03 (Replay Engine) implementation reveals a need for replay to access longitudinal data (currently prohibited by Decision 7 and LP-11).
