# ADR-017 — ObservationStore Lifecycle & Temporal Semantics

**Status:** Accepted — V1.2 Architecture (K2 Frozen 2026-07-01)  
**Date:** 2026-07-01  
**Owner:** Domain  
**Preconditions:** ADR-016 (Observation Schema & Intelligence Architecture), ADR-016A (CandidateIdentity & Session Ownership), K0/K1/K2 frozen  
**Supersedes:** Nothing  
**Superseded by:** Nothing  
**Related:** ADR-018, ADR-019, ADR-021, ADR-022, ADR-032

---

## Context

ADR-016 froze the Observation schema and the Observation Intelligence Architecture. It established that:

- `Observation` is an immutable, typed, timestamped domain object
- `ObservationStore` is an independent Aggregate Root (not owned by CandidateProfile)
- `ObservationExtractor` is the sole writer
- `FeatureEngine` is the sole consumer that produces `ProfileFeature` objects

ADR-016 froze **what an Observation is** and **what ObservationStore contains**.

It did not freeze:

- The complete lifecycle of an Observation from creation to logical expiration
- The logical states an Observation can occupy
- The quality model for duplicate, conflicting, and complementary Observations
- The temporal semantics governing ordering, freshness, and replay
- The full responsibility boundary of ObservationStore (what it never does)
- Interaction contracts between ObservationStore and FeatureEngine
- Language independence of the lifecycle

This ADR freezes all of the above. It is the required precondition for ADR-018 (ProfileFeature Schema) and ADR-021 (Evidence Freshness TTL Policy).

---

## Decision

**The ObservationStore lifecycle is explicit, immutable-fact-based, and temporally ordered.**

An Observation is a permanent fact. It never changes meaning. Only its **logical usability** changes as the session progresses and time passes. The lifecycle governs usability transitions, not data mutation.

---

## SECTION A — Purpose: Why ObservationStore Requires an Explicit Lifecycle

### The Four-Layer Knowledge Model

The V1.2 platform maintains four distinct knowledge representations with non-overlapping responsibilities:

| Layer | Type | Mutability | Purpose |
|---|---|---|---|
| `EvidenceStore` | Runtime evidence | Append-only, immutable facts | What happened at question N |
| `ObservationStore` | Interpreted knowledge | Append-only, immutable facts | What it means about the candidate at that moment |
| `CandidateProfile` | Derived current knowledge | Recomputed per cycle | What the candidate is, right now |
| `SessionHistory` | Historical record | Write-once, immutable | What happened across a completed session |

### Why Each Layer Has a Different Lifecycle

**EvidenceStore** is a runtime buffer. It holds `EvidenceSignal` objects produced by the detection pipeline. Its lifecycle is bounded by the session. It has no concept of freshness, quality, or logical state — it is a raw append-only log.

**ObservationStore** is a knowledge store. It holds interpreted facts that have meaning beyond a single pipeline cycle. Observations must be:
- Ordered for replay
- Weighted by freshness for FeatureEngine
- Qualified for deduplication and conflict resolution
- Retained for session history assembly

Without an explicit lifecycle, FeatureEngine has no principled basis for deciding which Observations to weight, which to ignore, and which to use for replay. Without temporal semantics, there is no clock interface (required by ADR-021 for testability).

**CandidateProfile** is not a knowledge store — it is a derived view. It holds the current `ProfileFeature[]` computed from ObservationStore by FeatureEngine. It has no independent lifecycle; its lifecycle is governed entirely by FeatureEngine computation cycles.

**SessionHistory** has a write-once lifecycle. It is assembled at session close from snapshots of Narrative, CoachingPlan, and CandidateProfileSnapshot. It is the permanent historical record. It does not participate in the runtime lifecycle of Observations.

### Frozen Responsibility Boundaries

| Layer | Owns | Does NOT Own |
|---|---|---|
| `EvidenceStore` | Raw runtime signals; append-only log | Interpretation, freshness, quality |
| `ObservationStore` | Interpreted facts; lifecycle state; temporal ordering; freshness metadata | Feature production, narrative generation, coaching |
| `CandidateProfile` | Current ProfileFeatures (derived) | Observations, EvidenceSignals, SessionHistory |
| `SessionHistory` | Completed session record | Live runtime state of any kind |

---

## SECTION B — Observation Lifecycle

### Principle

> **An Observation is a permanent fact. It never mutates. It never changes meaning. Only its logical usability transitions.**

The lifecycle below governs usability, not data.

### Lifecycle Stages

```
Observation
    │
    ▼ [Created]
    ObservationExtractor produces a new Observation object.
    Fields are populated from one or more EvidenceSignals.
    The Observation is frozen at creation (immutable).
    Timestamp, question_index, interview_index are assigned at creation.
    These values never change.
    │
    ▼ [Stored]
    ObservationStore accepts the Observation.
    Deduplication check runs before acceptance.
    If a duplicate exists → rejected (not stored); existing Observation is unchanged.
    If a conflict exists → stored; conflict is recorded; superseding logic applies.
    If neither → appended.
    The store assigns no ID at creation; the (observation_type, source_question_index,
    interview_index, candidate_identity_id) tuple is the natural identity.
    │
    ▼ [Consumed]
    FeatureEngine reads ObservationStore.
    The Observation is consumed (read, not modified).
    It contributes to ProfileFeature computation.
    Consumption is idempotent — reading never changes the Observation.
    Multiple consumers may read the same Observation independently.
    │
    ▼ [Referenced]
    NarrativeGenerator, CoachingEngine read ProfileFeatures (not Observations directly).
    The Observation is referenced indirectly via ProfileFeature provenance.
    The Observation itself is unchanged.
    │
    ▼ [Snapshotted]
    At session close, ObservationStore state is captured into a CandidateProfileSnapshot.
    The snapshot is a point-in-time read; the Observation is not moved or modified.
    The original Observation remains in ObservationStore.
    │
    ▼ [Archived]
    SessionHistory is assembled. The Observation record is included in the session archive
    (via CandidateProfileSnapshot). The Observation in ObservationStore is now
    logically post-session. It may be retained for replay or cross-session processing.
    In V1.2, ObservationStore is session-scoped; archival = session end.
    │
    ▼ [Expired — logical]
    Freshness metadata marks the Observation as beyond its TTL.
    The Observation is NOT deleted. Its data is preserved.
    It is invisible to freshness-weighted FeatureEngine queries.
    It remains available for replay and audit queries.
    │
    ▼ [Ignored by freshness]
    FeatureEngine freshness filter excludes this Observation from active feature computation.
    The Observation continues to exist. It may be re-included if TTL policy changes.
    In replay mode, expired Observations are still used (replay is temporal, not freshness-filtered).
```

### Frozen Lifecycle Invariants

1. **Observations are never deleted** (in V1.2; archival policy is a V1.3 decision).
2. **Observations are never mutated** — no field may change after creation.
3. **Logical expiration is metadata-driven** — a flag or timestamp in the Observation's freshness record, not a structural change to the Observation itself.
4. **Superseding does not delete** — a superseded Observation remains stored; the superseding relationship is a separate record.
5. **Consumption is idempotent** — FeatureEngine may re-read any Observation at any time without side effects.

---

## SECTION C — Observation Logical States

### State Definitions

An Observation occupies exactly one logical state at any point in time. States are derived from metadata, not from the Observation's own fields.

---

### State: Active

**Purpose:** The Observation is fresh, valid, and eligible for FeatureEngine consumption.

**Transition into:** Any new Observation that passes deduplication and conflict checks enters Active state immediately upon storage.

**Transition out of:** Becomes `Referenced` when FeatureEngine reads it. May become `Superseded` if a later Observation of the same type covers the same evidence. May become `Expired` when TTL is exceeded.

**Consumers:** FeatureEngine (primary), CalibrationUpdater (secondary).

**Persistence implications:** Fully retained. Included in all FeatureEngine queries.

---

### State: Referenced

**Purpose:** The Observation has been read by FeatureEngine and contributed to at least one ProfileFeature computation cycle.

**Transition into:** FeatureEngine read event marks the Observation as referenced (metadata update only — the Observation itself is not changed; a separate read-log record is maintained by ObservationStore).

**Transition out of:** Returns to effective `Active` behavior on the next FeatureEngine cycle (referenced state does not exclude from future reads). May become `Expired` or `Archived` via the normal lifecycle.

**Consumers:** FeatureEngine (continues to read), ReplayUpdater (uses referenced history for ordering).

**Persistence implications:** Fully retained. The referenced-at timestamp provides FeatureEngine with consumption history for calibration.

---

### State: Superseded

**Purpose:** A later Observation of the same type and candidate provides a more authoritative interpretation of the same or related evidence. The earlier Observation is no longer the primary source for FeatureEngine, but it is preserved.

**Transition into:** When ObservationStore receives a new Observation that is declared to supersede an existing one (determined by ObservationStore's superseding policy — see Section D), the existing Observation is marked Superseded (metadata record; the Observation is not changed).

**Transition out of:** Never — superseding is permanent (the later Observation may itself be superseded, creating a chain; the earlier remains Superseded).

**Consumers:** FeatureEngine excludes Superseded Observations from active computation by default. ReplayUpdater includes them (replay is chronological and must reflect the state at each point in time). Audit consumers may query the full chain.

**Persistence implications:** Fully retained. Not included in freshness-weighted FeatureEngine queries. Included in replay queries.

---

### State: Archived

**Purpose:** The Observation's contributing session is complete. The Observation is no longer part of the live runtime store.

**Transition into:** Session close event. ObservationStore session scope ends.

**Transition out of:** In V1.2, Archived is terminal within the session scope. In V1.3+, cross-session ObservationStore may promote archived Observations into a historical read layer.

**Consumers:** ReplayUpdater (reads historical archive). No runtime FeatureEngine access in V1.2 (session-scoped).

**Persistence implications:** Retained in CandidateProfileSnapshot as part of SessionHistory. The session-scoped ObservationStore is deallocated at session close (V1.2).

---

### State: Expired (logical)

**Purpose:** The Observation is beyond its freshness TTL. It is no longer authoritative for current profile computation.

**Transition into:** TTL expiry check (evaluated by ObservationStore freshness layer, governed by ADR-021 clock interface). The Observation is marked expired in the freshness metadata record.

**Transition out of:** TTL policy changes (ADR-021) may un-expire Observations retroactively (this is a policy decision, not a state rollback). In V1.2, expiry is not retroactively reversed.

**Consumers:** FeatureEngine (excludes from freshness-weighted queries). ReplayUpdater (includes regardless of expiry — replay is temporal).

**Persistence implications:** Fully retained. Freshness record carries the expired_at timestamp. The Observation data is unchanged.

---

### State: Replay-only

**Purpose:** The Observation is excluded from live FeatureEngine computation (Superseded or Expired) but is available to the replay subsystem.

**Transition into:** When an Observation is Superseded or Expired, it automatically enters Replay-only for purposes of the replay subsystem.

**Transition out of:** Never (within V1.2).

**Consumers:** ReplayUpdater exclusively. No live FeatureEngine access.

**Persistence implications:** Fully retained. Queryable by replay interface only.

---

### State Transition Summary

```
New Observation
    │
    ▼ (deduplication pass)
[Active]
    │
    ├──→ [Referenced]      — FeatureEngine has read it (non-exclusive; can still be Active)
    │        │
    │        └──→ [Archived]    — session close
    │
    ├──→ [Superseded]      — later Observation supersedes this one
    │        │
    │        └──→ [Replay-only] — excluded from live FeatureEngine; available to ReplayUpdater
    │
    ├──→ [Expired]         — TTL exceeded
    │        │
    │        └──→ [Replay-only]
    │
    └──→ [Archived]        — session close (if still Active/Referenced)
```

---

## SECTION D — Observation Quality Model

### Principle

> **ObservationStore maintains quality through metadata and policy records. It never mutates existing Observations.**

All quality decisions are recorded as separate metadata objects (deduplication records, superseding records, conflict records). The Observations themselves are never modified.

---

### Duplicate Observation

**Definition:** Two Observations are duplicates when they have identical `(observation_type, source_signals, question_index, interview_index, candidate_identity_id)` values and produce identical content under the current schema.

**Deduplication policy:**
- ObservationStore checks for exact-match duplicates before appending.
- If a duplicate is detected → the new Observation is **rejected** (not stored).
- The existing Observation is unchanged.
- ObservationExtractor is notified of the rejection (no error; deduplication is expected behavior).
- No data loss: the existing Observation already represents the same fact.

**Invariant:** Duplicate rejection never mutates the existing Observation.

---

### Equivalent Observation

**Definition:** Two Observations are equivalent when they have the same semantic meaning but differ in metadata (e.g., generated by different extraction paths, different timestamps, slightly different source_signal sets, but identical `observation_type` and `description` content).

**Equivalence policy:**
- Equivalence is more permissive than deduplication.
- ObservationStore stores both.
- FeatureEngine applies an equivalence-deduplication pass during feature computation (consumes the first; de-weights duplicates by recency, not by exclusion).
- The policy for equivalence weighting is defined in ADR-021 (freshness model).

**Invariant:** Both Observations are stored. Neither is mutated.

---

### Conflicting Observation

**Definition:** Two Observations have the same `observation_type` and `question_index` but contradictory content (e.g., `CONFIDENCE_HIGH` and `CONFIDENCE_LOW` for the same question).

**Conflict policy:**
- Both Observations are stored.
- ObservationStore records a conflict metadata entry linking the two Observations.
- FeatureEngine receives both and applies its conflict resolution strategy (defined in ADR-020: FeatureEngine Architecture).
- ObservationStore itself does not resolve conflicts — conflict resolution is a FeatureEngine concern.
- The Observation with the later timestamp is considered the superseding candidate (but the final decision is FeatureEngine's).

**Invariant:** Both Observations are stored. Neither is deleted. The conflict record is the resolution artifact.

---

### Complementary Observation

**Definition:** Two Observations have different `observation_type` values for the same `question_index` and together provide richer context than either alone (e.g., `COMMUNICATION_CLARITY` and `CONFIDENCE_CALIBRATION` at question 3 are complementary).

**Merge policy:**
- Both Observations are stored independently.
- No merge record is created at the ObservationStore level.
- FeatureEngine receives both and may synthesise a compound ProfileFeature from the set.
- The compound ProfileFeature carries provenance to both source Observations.

**Invariant:** Both Observations are stored as independent facts. No merge operation occurs. The compound knowledge lives in ProfileFeature, not in ObservationStore.

---

### Incomplete Observation

**Definition:** An Observation is incomplete when required fields are present but confidence is below the acceptance threshold (defined in ADR-016: minimum confidence 0.3), or when optional evidence fields are absent.

**Policy:**
- Observations below the confidence threshold are **rejected by ObservationExtractor** before reaching ObservationStore (ObservationStore never sees sub-threshold Observations).
- Observations with absent optional fields are accepted (absent is a valid value, not an error).
- ObservationStore does not validate completeness — this is ObservationExtractor's responsibility.

**Invariant:** ObservationStore only stores Observations that have passed ObservationExtractor validation.

---

## SECTION E — ObservationStore Responsibilities

### What ObservationStore Does

| Responsibility | Description |
|---|---|
| **Stores** | Accepts Observations from ObservationExtractor (sole writer). Appends to the store; never overwrites. |
| **Orders** | Maintains Observations in question_index order within each interview_index. Provides ordered iteration. |
| **Indexes** | Maintains indexes on (observation_type, question_index, interview_index) for efficient retrieval by FeatureEngine. |
| **Retrieves** | Provides read interfaces for FeatureEngine (freshness-filtered), ReplayUpdater (temporal, unfiltered), and CalibrationUpdater (full store). |
| **Supports replay** | Provides a temporal snapshot interface that returns Observations in strict question_index order, including Superseded and Expired entries, with all metadata intact. |
| **Supports FeatureEngine** | Provides a freshness-filtered, active-only interface for current feature computation. |
| **Supports freshness** | Maintains freshness metadata per Observation. Evaluates TTL against the clock interface (ADR-021). Marks Observations as Expired in metadata. |
| **Supports snapshots** | Provides a point-in-time snapshot interface for CandidateProfileSnapshot assembly. The snapshot includes all Observations (all states) with their metadata. |
| **Enforces deduplication** | Runs duplicate check before appending. Rejects exact duplicates. Records equivalence candidates. |
| **Records quality metadata** | Maintains conflict records, superseding records, and freshness records as separate metadata objects. |

### What ObservationStore Does NOT Do

These are frozen invariants. No future extension may add these responsibilities to ObservationStore.

| Prohibited | Reason |
|---|---|
| **Creates Features** | FeatureEngine is the sole producer of ProfileFeatures. ObservationStore is an input to FeatureEngine, not a producer of derived knowledge. |
| **Creates Narrative** | NarrativeGenerator reads CandidateProfile (ProfileFeatures). It does not read ObservationStore. |
| **Creates Coaching** | CoachingEngine reads KnowledgeGaps and ProfileFeatures. It does not read ObservationStore. |
| **Updates CandidateProfile** | CandidateProfile is updated solely by FeatureEngine. |
| **Invokes FeatureEngine** | ObservationStore is a passive store. It does not push to consumers. Consumers pull from it. |
| **Reads EvidenceStore** | ObservationStore operates at the Observation layer. EvidenceSignal-to-Observation translation is ObservationExtractor's concern. |
| **Reads SessionHistory** | SessionHistory is a write-once archive. ObservationStore has no dependency on it. |
| **Resolves conflicts** | Conflict records are stored; resolution is a FeatureEngine strategy. |
| **Invokes LLM calls** | ObservationStore is pure domain logic. No external calls. |
| **Writes to SessionHistory** | SessionHistory is assembled by the session completion pipeline, not by ObservationStore. |

---

## SECTION F — Temporal Semantics

### Frozen Temporal Model

#### Observation Timestamp

Each Observation carries a `created_at` wall-clock timestamp (UTC ISO-8601). This timestamp:
- Is assigned by ObservationExtractor at creation.
- Is immutable after creation.
- Represents the moment the interpretation was made, not the moment the EvidenceSignal was produced.
- Is used by the freshness layer (ADR-021) to compute TTL expiry.
- Is NOT used for ordering within a session (question_index governs ordering).

The distinction between `created_at` and question_index is critical:
- `created_at` is a wall-clock fact — "this interpretation was made at 14:32:07 UTC".
- `question_index` is a session-domain fact — "this interpretation was made at question 3 of this session".

Wall-clock time is infrastructure metadata. Session position is domain metadata.

#### Question Index

`question_index` is the primary ordering key for Observations within a session.

- Assigned by ObservationExtractor from the source EvidenceSignal's `question_index`.
- Immutable after creation.
- Governs FeatureEngine iteration order.
- Governs ReplayUpdater replay order (replay is by question_index, not by wall-clock time).
- Two Observations at the same `question_index` are ordered by `created_at` (secondary sort key).

#### Interview Sequence (interview_index)

`interview_index` is the session identifier within a CandidateIdentity's history.

- Assigned at session start by the session management layer.
- Carried by the Observation.
- Enables cross-session querying (V1.3+).
- In V1.2 (session-scoped ObservationStore), all Observations in one store instance share the same `interview_index`.

#### CandidateIdentity Ownership

Every Observation carries a `candidate_identity_id` (from ADR-016A).

- Assigned by ObservationExtractor from the session context.
- Immutable after creation.
- Required for all ObservationStore queries (scoped by identity in V1.3+ cross-session store).
- Prevents cross-candidate data leakage.

#### Replay Ordering

Replay is always ordered by `(interview_index ASC, question_index ASC, created_at ASC)`.

- Replay does not filter by logical state — all Observations (Active, Superseded, Expired) are included.
- Replay does not apply freshness filters.
- Replay reconstructs the knowledge state as it existed at each question_index, using the Observations that were present at that point in time.

#### Freshness Metadata

Each Observation carries a freshness record (maintained by ObservationStore, not embedded in the Observation itself):

| Field | Description |
|---|---|
| `observation_id` | Natural identity tuple |
| `created_at` | From the Observation |
| `ttl_seconds` | Policy-defined TTL (ADR-021) |
| `expires_at` | `created_at + ttl_seconds` (computed, not stored) |
| `expired_flag` | Set to True when ObservationStore evaluates freshness via clock interface |
| `last_consumed_at` | Timestamp of last FeatureEngine read |

The `expired_flag` is maintained by ObservationStore, not by the Observation. The Observation does not know it is expired.

#### Logical Expiration

Logical expiration is:
- Driven by the clock interface (ADR-021) — a testable, injectable clock dependency.
- Evaluated lazily (on FeatureEngine query) or eagerly (on a freshness sweep, policy TBD in ADR-021).
- Non-destructive — the Observation is not deleted or modified.
- Reversible by policy change — if TTL policy changes, the `expired_flag` can be re-evaluated (V1.2 does not require reversal; this is a V1.3 capability).

#### Historical Retention

In V1.2:
- ObservationStore is session-scoped.
- All Observations are retained for the duration of the session.
- At session close, ObservationStore state is captured in CandidateProfileSnapshot.
- The session-scoped store is then deallocated.
- Historical Observations are accessible only through CandidateProfileSnapshot and SessionHistory.

In V1.3+:
- ObservationStore may be persistent and cross-session.
- Historical retention policy is deferred to a future ADR.

#### Temporal Consistency

**Invariant:** Within one session, the sequence of `(interview_index, question_index)` values in ObservationStore must be monotonically non-decreasing in the order of `created_at` timestamps.

This means: an Observation for question 5 cannot have a `created_at` earlier than an Observation for question 3 in the same session (barring clock skew, which the clock interface must handle — ADR-021).

### Why Time Belongs to Observation Rather Than Feature

Time is an intrinsic property of the Observation because:

1. **Observations are facts about specific moments.** An Observation of type `CONFIDENCE_HIGH` at question 3 is a different fact from the same type at question 7. Removing the temporal anchor would make them indistinguishable.

2. **Freshness is a property of the evidence, not the derived knowledge.** A ProfileFeature reflects the current state of the candidate. Whether that state was derived from fresh or stale Observations is a question about the Observations, not about the feature. The feature itself does not age — it is always the most recent computation. The Observations it was derived from may age.

3. **Replay requires temporal provenance.** To reconstruct the candidate profile state at question 5, the replay subsystem must know which Observations existed at that point. This requires each Observation to carry its own temporal position. If time lived only in ProfileFeature, replay would be impossible.

4. **Conflict resolution requires temporal ordering.** When two conflicting Observations exist, the resolution strategy (FeatureEngine's concern) may use temporal ordering as a tiebreaker. This requires the Observations themselves to carry timestamps — not their derived Features.

5. **LearningProgress (V1.3+) is cross-session temporal.** Progress is measured by comparing Observations (or their derived Features) across sessions at specific question positions. Without temporal anchoring in the Observation, cross-session comparison has no coordinate system.

---

## SECTION G — CandidateIdentity Integration

### Ownership Chain (Frozen)

```
CandidateIdentity
    │  (owns all knowledge produced for this candidate)
    │
    ├──→ ObservationStore (session-scoped in V1.2; identity-scoped in V1.3+)
    │       │
    │       ▼ [FeatureEngine reads ObservationStore]
    │   FeatureEngine
    │       │
    │       ▼ [FeatureEngine writes ProfileFeatures to CandidateProfile]
    │   CandidateProfile (current session state)
    │       │
    │       ▼ [session close: snapshot assembled by session completion pipeline]
    │   CandidateProfileSnapshot
    │       │
    │       ▼ [stored in SessionHistory]
    │   SessionHistory (write-once, immutable)
    │       │
    │       ▼ [derived at query time; never persisted]
    │   LearningProgress (V1.3+)
```

### Frozen Distinctions

| Concept | Definition | Persisted? | Mutable? |
|---|---|---|---|
| `CandidateProfile` | The **current** derived state of the candidate. Holds `ProfileFeature[]` computed by FeatureEngine for the active session. | No (session-resident, not independently persisted) | Yes — recomputed by FeatureEngine |
| `CandidateProfileSnapshot` | A **point-in-time capture** of `CandidateProfile` at a specific moment (typically session close). Stored inside `SessionHistory`. | Yes (inside SessionHistory) | No — immutable after creation |
| `SessionHistory` | The **complete historical record** of one completed session — transcript, answers, Narrative, CoachingPlan, CandidateProfileSnapshot, LanguageProfile. | Yes (durable, write-once) | No — write-once |
| `LearningProgress` | A **derived cross-session view** computed from multiple `SessionHistory` records for one `CandidateIdentity`. Represents growth over time. | No — derived at query time | N/A — derived, never stored |

### Ownership Invariants

1. **`CandidateIdentity` is the root owner** of all persisted knowledge. Every `SessionHistory` carries a `candidate_identity_id`. Every `CandidateProfileSnapshot` carries a `candidate_identity_id`.

2. **`ObservationStore` is scoped by `CandidateIdentity`** — every Observation carries `candidate_identity_id`. In V1.2 (session-scoped store), this is inherited from the session context. In V1.3+ (persistent store), it enables cross-session queries.

3. **`CandidateProfile` is NOT persisted independently.** It is a live, session-resident object. Its state is captured via `CandidateProfileSnapshot` at session close and stored in `SessionHistory`.

4. **`LearningProgress` is NEVER persisted.** It is always computed on demand from `SessionHistory[]` for a given `CandidateIdentity`. Persisting it would create a derived-knowledge consistency problem (the computed value must always reflect the latest `SessionHistory` entries).

5. **`FeatureEngine` is the only writer to `CandidateProfile`.** No component may write `ProfileFeature[]` to `CandidateProfile` except `FeatureEngine`.

---

## SECTION H — Replay & Progress

### Frozen Replay Principles

> **Replay never rebuilds history. Replay consumes preserved snapshots.**

#### What Replay Does

Replay reconstructs the experience of a completed session by consuming:
- `CandidateProfileSnapshot` — the candidate's profile state at session close
- Narrative sections stored in `SessionHistory`
- CoachingPlan stored in `SessionHistory`
- The session transcript (questions and answers) stored in `SessionHistory`

Replay does NOT:
- Re-execute the FeatureEngine pipeline
- Re-execute the detection pipeline
- Re-read live ObservationStore (the session is closed; ObservationStore is session-scoped)
- Rebuild CandidateProfile from Observations

#### Replay and ObservationStore

In V1.2, ObservationStore is session-scoped. When the session closes, the ObservationStore is deallocated. Replay uses the `CandidateProfileSnapshot` (which was assembled from ObservationStore state at session close) as its profile input.

In V1.3+, if ObservationStore becomes persistent, `ReplayUpdater` may use the historical Observation record to perform more granular per-question-index replay (reconstructing the profile state as it was at each question). This is the `ReplayUpdater` concern (ADR-026).

#### LearningProgress is Derived. Never Persisted.

**Frozen principle:** `LearningProgress` is a derived cross-session view. It is computed at query time from `SessionHistory[]` for one `CandidateIdentity`. It is never stored.

Rationale:
1. Storing a derived value creates a consistency obligation — the stored value must be invalidated whenever a `SessionHistory` record is added or corrected.
2. The computation is cheap relative to the consistency risk.
3. In V1.3+, if computation cost grows, a caching layer may be introduced — but the cached value must be treated as a cache (evictable), never as a source of truth.

---

## SECTION I — FeatureEngine Interaction

### Frozen Interaction Contract

```
ObservationExtractor
    │
    │ [creates Observation — sole writer]
    ▼
ObservationStore
    │
    │ [read: freshness-filtered, ordered by question_index]
    ▼
FeatureEngine
    │
    ├──→ ObservationUpdater   [derives ProfileFeatures from current ObservationStore]
    ├──→ ReplayUpdater         [derives features from SessionHistory snapshots — V1.3+ full activation]
    └──→ CalibrationUpdater   [validates features against CalibrationProfile]
    │
    │ [writes ProfileFeature[] — sole writer]
    ▼
CandidateProfile
```

### Interaction Invariants

| Invariant | Description |
|---|---|
| **ObservationExtractor creates only** | ObservationExtractor's sole responsibility is to transform EvidenceSignals into Observations and append them to ObservationStore. It does not read ObservationStore. |
| **FeatureEngine consumes only** | FeatureEngine reads from ObservationStore. It does not write to it. |
| **ObservationStore never invokes FeatureEngine** | ObservationStore is a passive store. There is no event push, no observer registration, no callback. FeatureEngine pulls from ObservationStore on its own computation cycle. |
| **FeatureEngine never mutates Observation** | FeatureEngine is a read-only consumer of ObservationStore. It may record `last_consumed_at` metadata via the ObservationStore API (a write to the freshness record, not to the Observation). |
| **No circular dependency** | ObservationStore has no reference to FeatureEngine. FeatureEngine has no reference to ObservationExtractor. The dependency graph is strictly one-directional: ExtractorExtractor → Store → Engine → Profile. |

### FeatureEngine Internal Orchestration

FeatureEngine may internally orchestrate the following Updaters:

- `ObservationUpdater` — primary. Derives ProfileFeatures from the current ObservationStore content.
- `ReplayUpdater` — derives features from SessionHistory Observation snapshots (cross-session, V1.3+ full activation; V1.2 interface reserved).
- `CalibrationUpdater` — validates computed ProfileFeature values against CalibrationProfile baselines.
- `LearningUpdater` — reserved for V1.3+ (cross-session learning signal integration).

The composition and orchestration model of these Updaters is the subject of ADR-020 (FeatureEngine Architecture). This ADR does not prescribe how FeatureEngine orchestrates internally — only the boundary between ObservationStore and FeatureEngine.

---

## SECTION J — Language Independence

### Lifecycle Verification Matrix

The Observation lifecycle is identical regardless of programming language.

| Lifecycle Stage | Python | JavaScript | Go | Java | Rust | C# |
|---|---|---|---|---|---|---|
| Created | Identical | Identical | Identical | Identical | Identical | Identical |
| Stored | Identical | Identical | Identical | Identical | Identical | Identical |
| Consumed | Identical | Identical | Identical | Identical | Identical | Identical |
| Referenced | Identical | Identical | Identical | Identical | Identical | Identical |
| Snapshotted | Identical | Identical | Identical | Identical | Identical | Identical |
| Archived | Identical | Identical | Identical | Identical | Identical | Identical |
| Expired | Identical | Identical | Identical | Identical | Identical | Identical |
| Replay-only | Identical | Identical | Identical | Identical | Identical | Identical |

### Language Metadata, Not Semantics

Language **only** affects the `language_context` metadata field on an Observation (from ADR-016):

- `language_context` carries `ProgrammingLanguage` when the source question was a coding question.
- `language_context` is `null` for non-coding questions.
- The **lifecycle, logical states, quality model, and temporal semantics** are identical regardless of `language_context` value.

### Frozen Principles

1. `ProgrammingLanguage` is an abstract domain concept (K2 amendment A-5). Observations reference it by abstract concept, not by concrete language name.
2. `LanguageExecutor` is an infrastructure concern. It has no role in the Observation lifecycle.
3. Adding support for a new language (Go, Java, Rust, C#) requires:
   - A new entry in `LanguageRegistry`
   - A new `LanguageExecutor` adapter
   - A new `LanguagePolicy` artifact
   - Zero changes to the Observation lifecycle, ObservationStore, or FeatureEngine

---

## SECTION K — Future Compatibility

### ADR Compatibility Validation

| Future ADR | Compatibility | Notes |
|---|---|---|
| **ADR-018 (ProfileFeature Schema)** | ✓ Fully compatible | ADR-018 defines what FeatureEngine produces from ObservationStore. This ADR freezes the ObservationStore side; ADR-018 freezes the FeatureEngine output side. No conflict. ADR-018 is now unblocked. |
| **ADR-019 (LanguageConfig)** | ✓ Fully compatible | LanguageConfig defines ProgrammingLanguage as an abstract domain concept. This ADR's language_context field carries the abstract concept. No conflict. |
| **ADR-021 (Freshness TTL Policy)** | ✓ Fully compatible | ADR-021 will define the TTL values, decay function shape, and clock interface. This ADR reserves the freshness metadata structure and the clock interface hook. ADR-021 fills the TTL and decay values. |
| **ADR-022 (SessionHistory Schema)** | ✓ Fully compatible | SessionHistory receives CandidateProfileSnapshot at session close. This ADR defines what ObservationStore contributes to the snapshot. No conflict. |
| **ADR-032 (CandidateProfileSnapshot Strategy)** | ✓ Fully compatible | ADR-032 defines how CandidateProfileSnapshot is assembled and versioned. This ADR defines what ObservationStore state is available at snapshot time. ADR-032 remains P1. |
| **ObservationModel extensions** | ✓ Compatible | New ObservationTypes may be added via ObservationExtractor without changing lifecycle or store. |
| **Replay (full V1.3+ activation)** | ✓ Compatible | ReplayUpdater interface is reserved. Full cross-session replay requires V1.3 persistent ObservationStore — no V1.2 redesign. |
| **Progress Tracking** | ✓ Compatible | LearningProgress is derived from SessionHistory. ObservationStore contributes via CandidateProfileSnapshot → SessionHistory. No direct dependency. |
| **Coaching** | ✓ Compatible | CoachingEngine reads KnowledgeGaps and ProfileFeatures. It does not read ObservationStore. No change required. |
| **Narrative** | ✓ Compatible | NarrativeGenerator reads ProfileFeatures. It does not read ObservationStore. No change required. |
| **Knowledge Graph (V2 candidate)** | ✓ Compatible | A future Knowledge Graph would consume ProfileFeatures and SessionHistory. ObservationStore would contribute via existing interfaces. |

### V1.1 Asset Compatibility

**No frozen V1.1 asset requires change.**

| V1.1 Asset | Status |
|---|---|
| `EvidenceSignal` schema | Protected. Unchanged. |
| `EvidenceStore` contract | Protected. Unchanged. |
| `EvidenceType` catalog | Protected. Unchanged. |
| `CandidateProfile` V1.1 fields | Protected. ProfileFeature[] is additive (default_factory=dict). |
| Pattern detectors (10 existing) | Protected. Unchanged. |
| `ReasonerService` | Protected. Unchanged. |
| `EvaluationEngine` | Protected. Unchanged. |

---

## SECTION L — Runtime Flow Validation

### Canonical Runtime Flow

```
Evaluation (answer submitted, test results, dimension scores)
    │
    ▼  [single writer: EvaluationEngine]
EvidenceSignalWriter
    │
    ▼
EvidenceSignal  ──→  EvidenceStore (append-only; V1.1 frozen contract)
    │
    ▼  [single writer: ObservationExtractor]
Observation  ──→  ObservationStore
                 (deduplication → Active state → freshness metadata)
    │
    ▼  [consumer: FeatureEngine — sole writer of ProfileFeatures]
FeatureEngine
    ├── ObservationUpdater (reads ObservationStore: freshness-filtered, question_index ordered)
    ├── CalibrationUpdater (reads CalibrationProfile)
    └── ReplayUpdater (reserved; reads SessionHistory snapshots in V1.3+)
    │
    ▼  [single writer: FeatureEngine]
ProfileFeature[]
    │
    ▼  [single writer: FeatureEngine update call]
CandidateProfile (current session state; ProfileFeatures only)
    │
    ├────────────────────────────────────────────────────────┐
    ▼                                                        ▼
NarrativeGenerator                               KnowledgeGapEngine
(reads ProfileFeatures + KnowledgeGaps)          (reads EvaluationResults)
    │                                                        │
    ▼  [single writer: NarrativeGenerator]                  ▼
Narrative                                        KnowledgeGap[]
(NarrativeSections + NarrativeInsights)                     │
    │                                                        ▼
    │                                             CoachingEngine
    │                                    (reads KnowledgeGaps + ProfileFeatures)
    │                                                        │
    │                                                        ▼  [single writer: CoachingEngine]
    │                                             CoachingPlan
    │                                                        │
    └─────────────────────────┬──────────────────────────────┘
                              ▼  [single writer: ReportBuilder]
                         ReportBuilder
                              │
                              ▼  [snapshot: session completion pipeline]
                         CandidateProfileSnapshot (from CandidateProfile + ObservationStore metadata)
                              │
                              ▼  [single writer: session completion pipeline]
                         SessionHistory (write-once, immutable; carries Narrative + CoachingPlan + Snapshot)
                              │
                 ┌────────────┼──────────────┐
                 ▼            ▼              ▼
             Replay UI  ProgressTracker  CalibrationProfile
            (read-only)  (LearningProgress  (read-only aggregate)
                          derived; never
                          persisted)
```

### Runtime Invariant Verification

| Property | Verification |
|---|---|
| **Single writer** | EvidenceStore ← EvaluationEngine only. ObservationStore ← ObservationExtractor only. CandidateProfile ← FeatureEngine only. Narrative ← NarrativeGenerator only. CoachingPlan ← CoachingEngine only. SessionHistory ← session completion pipeline only. ✓ |
| **Single ownership** | Each aggregate has exactly one named writer. No two components write to the same aggregate. ✓ |
| **No circular dependencies** | Flow is strictly: EvidenceStore → ObservationStore → FeatureEngine → CandidateProfile → {Narrative, CoachingPlan} → SessionHistory. No upward references. ✓ |
| **Immutable facts** | EvidenceSignal (frozen=True). Observation (frozen at creation). Narrative (write-once). CoachingPlan (write-once). SessionHistory (write-once). CandidateProfileSnapshot (write-once). ✓ |
| **Derived knowledge** | CandidateProfile (derived by FeatureEngine from ObservationStore). LearningProgress (derived at query time from SessionHistory). Neither is a source of truth. ✓ |
| **Action consumers** | NarrativeGenerator, CoachingEngine, ReportBuilder are terminal consumers. They do not write back to any upstream aggregate. ✓ |

---

## SECTION M — ADR Backlog Update

### ADR-017 Status

**ADR-017: ObservationStore Lifecycle & Temporal Semantics — ACCEPTED (2026-07-01)**

### Dependencies Updated

| ADR | Previous Status | Updated Status |
|---|---|---|
| ADR-016 | ACCEPTED | Unchanged — precondition for ADR-017 ✓ |
| ADR-016A | ACCEPTED | Unchanged — precondition for ADR-017 ✓ |
| ADR-017 | Pending | **ACCEPTED** |
| ADR-018 | Blocked on ADR-016, ADR-016A | **UNBLOCKED** — all preconditions met |
| ADR-021 | Blocked on ADR-017 | **UNBLOCKED** — freshness metadata structure and clock interface hook defined |
| ADR-032 | P1 | **Remains P1** — CandidateProfileSnapshot strategy; ADR-017 defines what ObservationStore contributes to the snapshot |

### ADR-018 Unblock Confirmation

ADR-018 (ProfileFeature Schema Freeze & Versioning Policy) is now fully unblocked:
- ADR-016: Observation schema frozen ✓
- ADR-016A: CandidateIdentity ownership frozen ✓
- ADR-017: ObservationStore lifecycle frozen (FeatureEngine read interface defined) ✓

ADR-018 may proceed immediately.

### ADR-032 Status: P1 Retained

ADR-032 (CandidateProfileSnapshot Strategy) remains P1. This ADR defines:
- How ObservationStore state is captured at session close
- How CandidateProfileSnapshot is assembled and versioned
- How ReplayUpdater consumes historical snapshots

ADR-017 has resolved the ObservationStore side of ADR-032's dependencies. ADR-032 still requires ADR-022 (SessionHistory Schema) to proceed.

---

## SECTION N — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ Observation lifecycle frozen | **FROZEN** — Section B defines all 8 lifecycle stages with frozen invariants |
| ✓ Logical states frozen | **FROZEN** — Section C defines 6 states (Active, Referenced, Superseded, Archived, Expired, Replay-only) with transition rules, consumers, and persistence implications |
| ✓ Observation quality model frozen | **FROZEN** — Section D defines Duplicate, Equivalent, Conflicting, Complementary, and Incomplete Observations with deduplication, superseding, conflict, and merge policies |
| ✓ Temporal semantics frozen | **FROZEN** — Section F defines timestamp, question_index, interview_index, CandidateIdentity ownership, replay ordering, freshness metadata, logical expiration, historical retention, and temporal consistency |
| ✓ CandidateIdentity integration validated | **VALIDATED** — Section G defines the complete ownership chain and distinguishes CandidateProfile, CandidateProfileSnapshot, SessionHistory, and LearningProgress |
| ✓ Current CandidateProfile distinguished from CandidateProfileSnapshot | **DISTINGUISHED** — Section G: CandidateProfile is live/derived/not-persisted; CandidateProfileSnapshot is point-in-time/immutable/persisted-in-SessionHistory |
| ✓ Replay principles frozen | **FROZEN** — Section H: replay consumes snapshots; never rebuilds history; ReplayUpdater uses CandidateProfileSnapshot |
| ✓ LearningProgress confirmed derived-only | **CONFIRMED** — Section G + H: LearningProgress is never persisted; derived at query time from SessionHistory[] |
| ✓ Runtime validated | **VALIDATED** — Section L verifies single writer, single ownership, no circular dependencies, immutable facts, derived knowledge, action consumers |
| ✓ Language independence confirmed | **CONFIRMED** — Section J: lifecycle is identical for Python, JavaScript, Go, Java, Rust, C#; language is metadata only |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section K: no frozen V1.1 asset requires change |

---

## Final Recommendation

**ADR-017 is ACCEPTED.**

The ObservationStore lifecycle, temporal semantics, and all interaction invariants are frozen. No ambiguity remains in the boundary between ObservationStore, FeatureEngine, CandidateProfile, CandidateProfileSnapshot, SessionHistory, and LearningProgress.

**Immediate next action:** Proceed to ADR-018 (ProfileFeature Schema Freeze & Versioning Policy). All preconditions are met.

**ADR-032 (CandidateProfileSnapshot Strategy) remains P1** and should be scheduled after ADR-022 (SessionHistory Schema Versioning).
