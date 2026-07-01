# ADR-020 — FeatureEngine: Knowledge Construction Engine Architecture

**Status:** Accepted — V1.2 Architecture (K2 Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Knowledge Construction Layer
**Preconditions:** ADR-016, ADR-016A, ADR-017, ADR-018, ADR-019, K0/K1/K2 frozen
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-021, ADR-022, ADR-023, ADR-025, ADR-026, ADR-027, ADR-028, ADR-032

---

## Context

ADR-016 through ADR-019 established the full foundation of the V1.2 knowledge model:

- `EvidenceSignal` → `Observation` → `ObservationStore` (ADR-016/017)
- `ProfileFeature` taxonomy, versioning, provenance, quality model (ADR-018)
- Language Independence Layer; `FeatureIdentity` concept (ADR-019)

What remained undefined:

- The internal architecture of FeatureEngine as the Knowledge Construction Engine
- The Updater model and orchestration strategy
- The FeatureCandidate → FeatureComposer → merge/replace pipeline
- Conflict resolution policies (merge, replace, supersede)
- The plugin/extension model for new Updaters
- Recomputation strategy (full, partial, incremental, replay)
- The `LanguageFamily` concept and its role in the knowledge model
- Observability and performance invariants

This ADR freezes all of the above. No implementation, no contracts, no code.

---

## Decision

**FeatureEngine is the Knowledge Construction Engine of the platform. It is not a transformation component.**

Its role is to construct and maintain the platform's current understanding of the candidate — synthesising interpreted facts (Observations) into durable knowledge (ProfileFeatures) using deterministic, traceable, language-independent algorithms.

---

## SECTION A — Purpose: Knowledge Construction Engine

### The Three Platform Engines

The V1.2 platform has three distinct engines at different stages of the pipeline:

```
Reasoning Engine           — interprets what happened
                             (Reasoner, PatternDetectorPipeline, ObservationExtractor)
                             Input: EvidenceSignal[]
                             Output: Observation[]

Knowledge Construction     — constructs what the candidate is
Engine (FeatureEngine)      Input: Observation[]
                             Output: ProfileFeature[] → CandidateProfile

Action Engine              — decides what should be communicated
                             (NarrativeGenerator, CoachingEngine, KnowledgeGapEngine)
                             Input: CandidateProfile
                             Output: Narrative, CoachingPlan
```

### Why FeatureEngine Is Not Merely a Transformation Component

A transformation component maps inputs to outputs in a stateless, one-to-one fashion. `FeatureEngine` does more:

1. **Synthesis** — multiple Observations from different question positions are combined into a single ProfileFeature. The output is not a transformation of one input; it is a synthesis of many.

2. **Knowledge accumulation** — FeatureEngine maintains `CandidateProfile` as a living knowledge state across multiple computation cycles within a session. It is stateful in its output.

3. **Quality modelling** — FeatureEngine computes confidence, stability, maturity, freshness-awareness, and consistency for each ProfileFeature. These are emergent properties of the synthesis process, not properties of any single Observation.

4. **Provenance tracking** — FeatureEngine maintains the complete lineage from ProfileFeature back to source ObservationId[]. This is a record-keeping responsibility, not a transformation.

5. **Conflict resolution** — when two Observations produce conflicting implications for the same ProfileFeature, FeatureEngine applies a merge or supersede policy. This is reasoning, not mapping.

### Responsibility Freeze

| Engine | Responsibility | Input | Output |
|---|---|---|---|
| Reasoning Engine | Interprets what happened at a question | `EvidenceSignal[]` | `Observation[]` |
| Knowledge Construction Engine (FeatureEngine) | Constructs what the candidate is | `Observation[]` (via ObservationStore) | `ProfileFeature[]` → `CandidateProfile` |
| Action Engine | Decides what to communicate | `CandidateProfile` | `Narrative`, `CoachingPlan` |

---

## SECTION B — FeatureEngine Responsibilities

### What FeatureEngine Does

| Responsibility | Description |
|---|---|
| **Reads ObservationStore** | Sole consumer of ObservationStore for feature production. Freshness-filtered, question_index-ordered. |
| **Constructs ProfileFeatures** | Synthesises Observation[] into typed, versioned, confidence-weighted ProfileFeature objects. |
| **Maintains CandidateProfile** | Holds and updates the current `CandidateProfile.features` map. The profile is always in a valid, complete state after each FeatureEngine cycle. |
| **Computes derived knowledge** | Computes confidence, stability, maturity, freshness-awareness, and cross-feature consistency for each ProfileFeature. |
| **Tracks provenance** | Records `source_observation_ids` for every produced ProfileFeature. The full lineage is preserved. |
| **Orchestrates Updaters** | Invokes registered FeatureUpdaters in a defined order; collects FeatureCandidates; composes into final ProfileFeatures. |
| **Resolves conflicts** | Applies FeatureMergePolicy or FeatureReplacementPolicy when Updaters produce conflicting candidates for the same feature type. |

### What FeatureEngine NEVER Does

These are frozen invariants. No future extension may add these responsibilities.

| Prohibited | Invariant |
|---|---|
| Creates Observations | ObservationExtractor is the sole Observation producer. |
| Creates Narrative content | NarrativeGenerator's exclusive responsibility. |
| Creates CoachingActions | CoachingEngine's exclusive responsibility. |
| Creates Reports | ReportBuilder's exclusive responsibility. |
| Executes candidate code | Infrastructure (LanguageExecutor) responsibility. |
| Evaluates answers | EvaluationEngine responsibility. |
| Writes to ObservationStore | FeatureEngine is read-only with respect to ObservationStore. |
| Invokes LLM calls | FeatureEngine is deterministic; no LLM dependency. |
| Reads EvidenceStore directly | FeatureEngine operates at the Observation layer, not the EvidenceSignal layer. |
| Reads SessionHistory | SessionHistory is a write-once archive; FeatureEngine has no dependency on it at runtime. |

**Domain Invariant I-02 (confirmed):** `FeatureEngine` is the ONLY permitted producer of `ProfileFeature[]`. This invariant may not be violated without a new ADR explicitly superseding ADR-020.

---

## SECTION C — Internal Architecture

### Conceptual Architecture

```
FeatureEngine
    │
    ├──[1. Pull]──→  ObservationStore.query(freshness_filtered=True, ordered_by=question_index)
    │                Returns: Observation[]
    │
    ├──[2. Dispatch]──→  FeatureUpdater[] (registered, ordered)
    │                    Each Updater receives: Observation[]
    │                    Each Updater produces: FeatureCandidate[]
    │
    ├──[3. Collect]──→  FeatureCandidate[] (all candidates from all Updaters)
    │
    ├──[4. Compose]──→  FeatureComposer
    │                    Applies: FeatureMergePolicy | FeatureReplacementPolicy
    │                    Produces: ProfileFeature[] (one per FeatureIdentity)
    │
    └──[5. Commit]──→  CandidateProfile.features = ProfileFeature[]
```

### FeatureUpdater

**Responsibility:** Reads a subset of Observations from the ObservationStore query result. Produces `FeatureCandidate[]` — draft feature values with provenance and confidence estimates, not yet merged or committed.

**Properties:**
- Each Updater handles a defined subset of `ObservationType` values.
- Updaters are independent — they do not read each other's output.
- Updaters are stateless per invocation — they receive the full Observation[] query result and produce candidates without retaining state.
- Updaters never modify Observations.
- Updaters never write to any aggregate.

**Known V1.2 Updaters:**

| Updater | Input | Output | Status |
|---|---|---|---|
| `ObservationUpdater` | All freshness-filtered Observations | FeatureCandidate[] for all 11 V1.2 feature types | Active |
| `CalibrationUpdater` | CandidateProfile.features + CalibrationProfile baselines | Validation flags (not new features) | Active |
| `ReplayUpdater` | SessionHistory ObservationStore snapshot | FeatureCandidate[] for historical session reconstruction | V1.2 interface reserved; full activation V1.3+ |
| `LearningUpdater` | Cross-session ObservationStore (persistent) | ProgressFeature, LearningPaceFeature candidates | Reserved V1.3+ |

### FeatureComposer

**Responsibility:** Receives all `FeatureCandidate[]` from all Updaters for a given computation cycle. Applies `FeatureMergePolicy` or `FeatureReplacementPolicy` to resolve conflicts. Produces the final `ProfileFeature[]` that will be committed to `CandidateProfile`.

**Properties:**
- FeatureComposer is stateless — it receives all candidates and produces a complete output set.
- FeatureComposer applies policies; it does not implement policy logic itself (policy objects are injected).
- FeatureComposer enforces that every `FeatureIdentity` present in the output has exactly one resolved `ProfileFeature`.
- FeatureComposer assigns final quality metadata: confidence, stability, maturity.

### FeatureMergePolicy

**Responsibility:** When two Updaters produce `FeatureCandidate` objects for the same `FeatureIdentity`, `FeatureMergePolicy` combines them into a single `ProfileFeature`.

**Merge semantics:**
- Confidence: weighted average of candidate confidences, weighted by Observation count.
- Value: the candidate with higher confidence takes precedence if both are directional. If contradictory, the `FeatureReplacementPolicy` is invoked instead.
- Provenance: union of both candidates' `source_observation_ids`.
- Stability: derived from the merged result's consistency across cycles.

### FeatureReplacementPolicy

**Responsibility:** When two candidates for the same `FeatureIdentity` are contradictory (e.g., one says HIGH, one says LOW with equal confidence), `FeatureReplacementPolicy` selects one candidate and discards the other.

**Replacement semantics:**
- The candidate with the higher Observation count wins.
- Tie-break: the candidate produced from more recent Observations (higher `computed_at_question_index`) wins.
- The discarded candidate's `source_observation_ids` are recorded in the provenance record as `superseded_by` — never lost.

---

## SECTION D — Updater Model

### Orchestration Principle

FeatureEngine orchestrates Updaters in a defined, deterministic order. Order matters because:
- `CalibrationUpdater` must run after `ObservationUpdater` (it validates what ObservationUpdater produced).
- `ReplayUpdater` runs in a distinct mode (replay path, not live path) and is never co-invoked with `ObservationUpdater`.

**Live path invocation order:**
1. `ObservationUpdater` (primary feature production)
2. `CalibrationUpdater` (validation; does not produce features)
3. *(Future)* `LearningUpdater` (cross-session enrichment; V1.3+)

**Replay path invocation order:**
1. `ReplayUpdater` (reconstructs features from SessionHistory snapshot)
2. `CalibrationUpdater` (optional; validation against current CalibrationProfile)

### Updater Independence Invariants

1. **Updaters do not read each other's output.** Each Updater receives the same `Observation[]` query result from FeatureEngine. No Updater depends on another Updater's `FeatureCandidate[]`.
2. **Updaters do not modify Observations.** Updaters are read-only consumers of ObservationStore data.
3. **Updaters do not write to any aggregate.** All writes are performed by FeatureEngine after FeatureComposer has resolved all candidates.
4. **Updaters are replaceable.** A new Updater can be registered without modifying FeatureEngine's orchestration logic (Section J — Plugin Architecture).

### Future Custom Updaters

Future Updaters may be introduced for:
- Cross-session feature enrichment (`LearningUpdater`)
- Specialised domain-area features (e.g., a `SystemDesignUpdater` for architectural reasoning)
- Calibration-aware feature adjustment

Each new Updater requires a registry entry and an ADR naming its `ObservationType` input set and `ProfileFeature` output set.

---

## SECTION E — Knowledge Construction Pipeline

### Pipeline Definition

```
Observation[]  (freshness-filtered, question_index-ordered from ObservationStore)
    │
    ▼  [FeatureUpdater.produce(observations)]
FeatureCandidate[]
    │  Each FeatureCandidate carries:
    │  - feature_identity (FeatureIdentity)
    │  - candidate_value
    │  - candidate_confidence
    │  - source_observation_ids[]
    │  - computed_at_question_index
    │  - updater_id (which Updater produced this)
    │
    ▼  [FeatureComposer.compose(candidates)]
    │  Applies: FeatureMergePolicy (compatible candidates)
    │           FeatureReplacementPolicy (contradictory candidates)
    │
ProfileFeature[]
    │  Each ProfileFeature carries:
    │  - feature_identity
    │  - schema_version
    │  - value
    │  - confidence  ← quality: derived from candidate count + freshness
    │  - stability   ← quality: derived from cycle-over-cycle consistency
    │  - maturity    ← quality: derived from Observation count milestone
    │  - source_observation_ids[]  ← provenance
    │  - computed_at_question_index
    │  - feature_engine_version
    │
    ▼  [CandidateProfile.update(features)]
Current CandidateProfile
```

### Why Knowledge Construction is Deterministic

**Determinism requirement:** Given the same `ObservationStore` state and the same `LanguageConfig`, `FeatureEngine` must produce the same `ProfileFeature[]` every time it is invoked.

Determinism is guaranteed by:

1. **Ordered input.** ObservationStore delivers Observations sorted by `(question_index ASC, created_at ASC)`. The input order is deterministic.
2. **Stateless Updaters.** Each Updater is a pure function of its Observation[] input. No side effects, no random values, no clock dependency in feature value computation. (Clock is used only by ObservationStore for freshness TTL — outside FeatureEngine.)
3. **Deterministic composition.** FeatureComposer applies policies with explicit tie-breaking rules (Section C). No random selection.
4. **Replay guarantee.** Replay produces the same `ProfileFeature[]` from the same `ObservationStore` snapshot every time, enabling deterministic session reconstruction.

Determinism is a platform invariant. Any Updater or policy that introduces non-determinism (random values, current-time dependencies inside feature value computation) violates the architectural contract and is rejected.

---

## SECTION F — FeatureIdentity

### Conceptual Definition

`FeatureIdentity` represents the **semantic identity** of a ProfileFeature across schema versions, computation cycles, and sessions.

Two ProfileFeatures with the same `FeatureIdentity` represent the same conceptual characteristic of the candidate — regardless of when they were computed, under what schema version, or in what session.

### Composition

```
FeatureIdentity
    │
    ├── feature_type_id      — stable string key (e.g. "reasoning_feature")
    │                          NEVER changes across schema versions.
    │                          Defined at feature type introduction time.
    │
    └── semantic_category    — the conceptual dimension this feature represents
                               (e.g. "analytical_reasoning", "communication_clarity")
                               Groups related feature types for cross-feature analysis.
```

`FeatureIdentity = (feature_type_id, semantic_category)`. The `schema_version` qualifies the representation but is not part of the identity.

### Schema Evolution Invariant

**Frozen invariant:** Schema evolution must never change `FeatureIdentity`.

When `ReasoningFeature` evolves from schema v1 to schema v3:
- `feature_type_id` = `"reasoning_feature"` — unchanged
- `semantic_category` = `"analytical_reasoning"` — unchanged
- `schema_version` changes from `"1.0"` to `"3.0"`

The feature is the same knowledge concept. The representation has evolved.

### FeatureIdentity Enables

1. **Cross-session comparison** — `LearningProgress` compares ProfileFeatures from different sessions. `FeatureIdentity` is the common key.
2. **Replay fidelity** — `ReplayUpdater` maps a historical ProfileFeature to the current `FeatureIdentity` for display and comparison.
3. **Migration safety** — Schema migration can safely transform `v1` features to `v2` without losing identity linkage.
4. **Plugin isolation** — A new Updater that produces a feature with an existing `FeatureIdentity` replaces (or merges with) the existing feature. A new `FeatureIdentity` adds a new feature to the profile without conflict.

### FeatureIdentity Registry

All `FeatureIdentity` values are registered at feature type introduction time. The registry is a static domain artifact (part of `domain/language/`). No `FeatureIdentity` may be created at runtime.

---

## SECTION G — Provenance

### Provenance Chain

```
ObservationId[]
    │  (stored in ProfileFeature.source_observation_ids)
    ▼
FeatureIdentity
    │  (carried through FeatureCandidate → ProfileFeature)
    ▼
Current CandidateProfile
    │  (lives in memory; updated per cycle)
    ▼
CandidateProfileSnapshot
    │  (point-in-time capture at session close)
    ▼
SessionHistory
    │  (immutable; stored permanently)
    ▼
LearningProgress
    │  (derived at query time; reads SessionHistory[])
    ▼
Audit / Replay
```

### Provenance Requirements

Every `ProfileFeature` produced by FeatureEngine must carry:

| Field | Description |
|---|---|
| `source_observation_ids` | List of `ObservationId` values from which this feature was derived |
| `feature_identity` | `FeatureIdentity` — stable across schema versions |
| `schema_version` | The version of the feature schema used at computation time |
| `computed_at_question_index` | Session position at which this feature was computed |
| `feature_engine_version` | FeatureEngine version — for forward compatibility of stored features |
| `updater_id` | Which Updater(s) contributed to this feature |

### Audit Guarantees

The provenance chain provides three audit guarantees:

1. **Feature → Observation traceability.** For any ProfileFeature in any CandidateProfileSnapshot, the complete set of source Observations can be identified via `source_observation_ids`.

2. **Observation → EvidenceSignal traceability.** For any Observation in the SessionHistory snapshot, the source EvidenceSignals can be identified via `Observation.source_signal_ids`.

3. **Feature → EvidenceSignal full chain.** The complete chain from a ProfileFeature value back to the atomic EvidenceSignal that contributed to it is recoverable from SessionHistory alone (without re-executing any pipeline).

These guarantees hold as long as SessionHistory is intact. They enable:
- Debugging unexpected ProfileFeature values
- Validating that FeatureEngine logic is correct
- Investigating scoring calibration issues
- Supporting V1.3+ replay and progress comparison

---

## SECTION H — Recomputation Strategy

### Four Recomputation Modes

#### Full Recomputation

**When used:** Session close; CalibrationUpdater validation; after ObservationStore TTL expiry sweep.

**Behaviour:** FeatureEngine queries the entire ObservationStore (all non-expired Observations, ordered by question_index). All Updaters are invoked. FeatureComposer produces a complete ProfileFeature set. CandidateProfile is fully replaced.

**Rationale:** Full recomputation is the authoritative strategy. It guarantees consistency. It is used whenever correctness is more important than speed.

#### Partial Recomputation

**When used:** When a new Observation is appended to ObservationStore mid-session and FeatureEngine is invoked incrementally.

**Behaviour:** FeatureEngine identifies which `FeatureIdentity` values are affected by the new Observation (via `ObservationType → FeatureIdentity` mapping). Only the affected Updaters are invoked for affected feature types. Unaffected ProfileFeatures are retained from the prior cycle.

**Rationale:** Partial recomputation is faster for mid-session incremental updates. It is safe only when the ObservationStore append is the only change since the prior cycle.

#### Incremental Recomputation

**When used:** After each question answer submission during a live session (the primary operational mode).

**Behaviour:** FeatureEngine is invoked with the delta — the new Observation(s) appended since the last invocation. It computes candidates only for the affected feature types and merges them with the existing CandidateProfile.

**Rationale:** Incremental is the default live-session mode. It minimises latency per question. It is safe because ObservationStore is append-only — prior Observations never change.

#### Replay Recomputation

**When used:** When `ReplayUpdater` reconstructs a CandidateProfile from a historical `SessionHistory` ObservationStore snapshot.

**Behaviour:** `ReplayUpdater` receives the full Observation[] from the SessionHistory snapshot (ordered by question_index). It produces FeatureCandidates using the current FeatureEngine schema version. FeatureComposer composes a reconstructed ProfileFeature set.

**Note:** In V1.2, replay uses the stored `CandidateProfileSnapshot` directly — it does not re-invoke `ReplayUpdater`. In V1.3+, `ReplayUpdater` enables per-question-index profile reconstruction from the Observation history.

### Recomputation Determinism

All four modes must produce the same `ProfileFeature[]` given the same `ObservationStore` state. This is not a goal — it is a hard invariant. Any recomputation mode that produces different results from a full recomputation for the same input is a bug.

### CandidateProfile Replaceability

**Frozen invariant:** `CandidateProfile` is always replaceable. It is a derived view. Full recomputation can rebuild it at any time from ObservationStore. This means:

- CandidateProfile need not be persisted defensively during a session.
- If FeatureEngine crashes and restarts mid-session, full recomputation from ObservationStore restores the profile.
- The profile's value is the current ObservationStore state — nothing more.

---

## SECTION I — Conflict Resolution

### Conflict Classes

#### Feature Replacement

**When:** Two `FeatureCandidate` objects for the same `FeatureIdentity` have contradictory directional values (e.g., `TechnicalSkillFeature HIGH` and `TechnicalSkillFeature LOW`) and cannot be merged.

**Policy:** The candidate with the higher Observation count wins. Tie-break: more recent `computed_at_question_index`. The losing candidate's provenance is recorded in `superseded_by`.

**Result:** One `ProfileFeature` with the winning value; provenance includes both candidate sets.

#### Feature Merge

**When:** Two `FeatureCandidate` objects for the same `FeatureIdentity` are directionally compatible (both HIGH, or one HIGH and one MODERATE).

**Policy:** Values are merged by confidence-weighted combination. Provenance is unioned. Confidence is the weighted average. Stability is derived from the merged result.

**Result:** One `ProfileFeature` that represents the synthesis of both candidates.

#### Feature Superseding

**When:** A new `FeatureCandidate` from a later computation cycle produces a value that supersedes the prior `ProfileFeature` for the same `FeatureIdentity`.

**Policy:** The prior `ProfileFeature` is replaced by the new one. The prior value is not retained in `CandidateProfile` — but its provenance (which Observations it was derived from) is available via the ObservationStore history.

**Result:** CandidateProfile holds only the current value. Prior values are reconstructable from history.

### Feature Confidence

Confidence is computed per `ProfileFeature` as a function of:
- Number of source Observations (more → higher potential confidence)
- Consistency of source Observations (same direction → higher; contradictory → lower)
- Freshness weighting (recent Observations weighted higher per ADR-021 decay function)
- Observation quality (confidence values on source Observations propagate upward)

Confidence is **not a stored field** — it is recomputed on every FeatureEngine cycle from the current ObservationStore state.

### Feature Stability

Stability reflects how consistent the ProfileFeature value has been across the last N FeatureEngine computation cycles.

States: `stable` | `unstable` | `emerging`

- `stable`: Direction unchanged across last N cycles (N = configurable; default 3).
- `unstable`: Direction has oscillated across recent cycles.
- `emerging`: Fewer than N prior cycles available (early in the session).

Stability is a derived quality attribute computed by FeatureComposer by comparing the current candidate with the prior ProfileFeature value in CandidateProfile.

### Feature Maturity

Maturity reflects the stage of evidence accumulation for a ProfileFeature.

Stages:
- `nascent`: 1–2 source Observations.
- `developing`: 3–5 source Observations.
- `mature`: 6+ source Observations with consistent direction.

Maturity is a milestone-based property computed from `len(source_observation_ids)` and consistency.

---

## SECTION J — Plugin Architecture

### Extension Model

FeatureEngine supports a registry-based plugin model for Updaters. No engine modification is required to add a new Updater.

```
New FeatureUpdater (authored externally)
    │
    ▼
UpdaterRegistry (static domain configuration)
    │  Entry: { updater_id, updater_ref, observation_type_set, feature_identity_set, invocation_order }
    │
    ▼
FeatureEngine (reads UpdaterRegistry at initialisation)
    │  Invokes registered Updaters in invocation_order
    │
    ▼
FeatureComposer (receives all FeatureCandidate[] from all Updaters)
    │
    ▼
Current CandidateProfile
```

### Extension Policy

Adding a new Updater requires:
1. Author the Updater (reads Observation[], produces FeatureCandidate[]).
2. Define the `observation_type_set` (which ObservationTypes this Updater handles).
3. Define the `feature_identity_set` (which FeatureIdentities this Updater produces).
4. Register in `UpdaterRegistry` with an explicit `invocation_order`.
5. An ADR amendment naming the Updater, its inputs, and its outputs.

**No modification to FeatureEngine orchestration logic is required.**

### Conflict Avoidance

If two Updaters declare overlapping `feature_identity_set` values, `FeatureComposer` resolves the conflict using `FeatureMergePolicy` or `FeatureReplacementPolicy`. Overlap is not an error — it is handled by the composition layer. Updater authors should document expected overlaps in their ADR amendment.

### Updater Isolation

Updaters are isolated:
- They cannot read other Updaters' FeatureCandidates.
- They cannot modify the Observation[] input.
- They cannot access CandidateProfile directly.
- They produce only FeatureCandidates — they never commit to CandidateProfile.

All inter-Updater coordination happens in FeatureComposer, not in the Updaters themselves.

---

## SECTION K — Observability

### Conceptual Diagnostics Model

FeatureEngine emits diagnostic records for every computation cycle. These are not stored in SessionHistory by default — they are available for live monitoring, debugging, and calibration.

#### Feature Computation Trace

Per cycle, FeatureEngine records:
- Which Updaters were invoked.
- Which Observations each Updater received (by ObservationId).
- Which FeatureCandidates were produced (by FeatureIdentity and value).
- Which merge/replace policies were applied and why.
- The final ProfileFeature[] emitted.

#### Feature Provenance Trace

Per ProfileFeature, the provenance trace shows the full chain:
`ProfileFeature → FeatureCandidate → ObservationId[] → EvidenceSignal[]`

This is always reconstructable from `source_observation_ids` and the ObservationStore.

#### Execution Timing

Per cycle:
- Total FeatureEngine cycle duration (ms).
- Per-Updater duration.
- FeatureComposer duration.
- CandidateProfile commit duration.

#### Feature Statistics

Aggregate per session:
- Distribution of confidence values across all ProfileFeatures.
- Distribution of stability states.
- Count of merge vs. replace resolutions.
- Observation coverage per FeatureIdentity.

#### Replay Diagnostics

When `ReplayUpdater` is invoked:
- Comparison of reconstructed ProfileFeature[] vs. stored CandidateProfileSnapshot features.
- Delta report: which features differ, and why (schema version change, policy change, Updater logic change).

#### Audit Diagnostics

On-demand audit report:
- For a given CandidateProfileSnapshot, the full provenance chain for each ProfileFeature.
- The Observation sequence that contributed to each feature, in question_index order.

---

## SECTION L — Performance Goals

### Frozen Performance Invariants

**P-01: Deterministic execution.** Given the same ObservationStore state, FeatureEngine produces the same ProfileFeature[] every time. No randomness, no clock dependency in feature values, no environmental variation.

**P-02: Single pass whenever possible.** ObservationStore is queried once per FeatureEngine cycle. Updaters receive the same query result — there is no re-querying per Updater.

**P-03: Incremental updates preferred.** In the live session path, incremental recomputation is the default mode. Full recomputation is used only when correctness requires it (session close, calibration, crash recovery).

**P-04: No quadratic algorithms.** No Updater may implement an O(n²) algorithm where n = number of Observations. The maximum acceptable complexity per Updater per cycle is O(n log n). FeatureComposer operates on FeatureCandidates (a small set — at most one per FeatureIdentity per Updater), not on Observations directly.

**P-05: Memory growth bounded.** `CandidateProfile` holds at most one ProfileFeature per FeatureIdentity (11 in V1.2). Its memory footprint is O(|feature_types|), not O(|observations|). ObservationStore holds at most 500 Observations (ADR-016 capacity policy). FeatureEngine does not accumulate unbounded state.

**P-06: Replay deterministic.** `ReplayUpdater` applied to the same Observation[] snapshot must produce the same ProfileFeature[] every time, regardless of when replay is invoked.

---

## SECTION M — Language Independence

### FeatureEngine Language Independence

FeatureEngine is fully language-independent. It operates on abstract `ObservationType` values and `FeatureIdentity` values. It never branches on a concrete language name.

### LanguageFamily: New Domain Concept

**Purpose:** `LanguageFamily` groups related `ProgrammingLanguage` values that share paradigm characteristics. It enables future coaching and feature interpretation across related languages without FeatureEngine changes.

```
LanguageFamily
    │
    ├── Dynamic family:     Python, JavaScript, Ruby, PHP
    ├── TypedScript family: TypeScript (extends JavaScript family)
    ├── JVM family:         Java, Kotlin, Scala, Clojure
    ├── Systems family:     Rust, Go, C, C++
    ├── CLR family:         C#, F#, VB.NET
    └── Functional family:  Haskell, Erlang, Elixir (future)
```

**V1.2 registered families:**

| LanguageFamily | Members (V1.2 active) | Members (V1.3+ planned) |
|---|---|---|
| `dynamic` | Python, JavaScript | Ruby, PHP |
| `typescript_family` | TypeScript | — |
| `jvm` | — | Java, Kotlin |
| `systems` | — | Rust, Go |
| `clr` | — | C# |

**LanguageFamily is a Domain concept.** It is defined in the Language Independence Layer alongside `ProgrammingLanguage`. It is:
- Abstract — no concrete language name is referenced in FeatureEngine logic.
- Registered — families are static registry entries.
- Used in provenance — `LanguageCapabilityFeature` provenance may carry `language_family` alongside `language_context` for cross-family coaching.

**What LanguageFamily enables:**
- NarrativeGenerator can reference language family when generating coaching prose: "this pattern is common across dynamic languages" rather than "this is a Python-specific pattern".
- CoachingEngine can recommend cross-language resources for a `LanguageCapabilityFeature` when the candidate is transitioning between languages in the same family.
- LearningProgress (V1.3+) can compare `LanguageCapabilityFeature` values across sessions in the same LanguageFamily.

**FeatureEngine remains language-independent.** `LanguageFamily` metadata is available in `Observation.language_context` extended metadata. FeatureEngine forwards it to `LanguageCapabilityFeature` provenance via type dispatch — no branching on family name.

### Language Independence Verification

| FeatureEngine Component | Language branch present? |
|---|---|
| ObservationStore query | No — queries by ObservationType; language_context is a filter option only |
| ObservationUpdater | No — maps ObservationType → FeatureIdentity; language_context forwarded to provenance |
| ReplayUpdater | No — processes Observation[] snapshot identically regardless of language |
| CalibrationUpdater | No — validates feature values against baselines; language is a calibration key only |
| FeatureComposer | No — merges/replaces by FeatureIdentity; language has no role in composition logic |
| CandidateProfile update | No — stores ProfileFeature[]; language is provenance metadata only |

**FeatureEngine never branches on concrete language names. Knowledge remains universal.**

---

## SECTION N — Runtime Validation

### Canonical Runtime Flow

```
Evaluation (answer submitted)
    │
    ▼  [single writer: EvaluationEngine]
EvidenceSignal  ──→  EvidenceStore (V1.1 frozen)
    │
    ▼  [single writer: ObservationExtractor]
Observation  ──→  ObservationStore (Independent Aggregate Root; ADR-016/017)
    │
    ▼  [pull: FeatureEngine — sole consumer for feature production]
ObservationStore.query(freshness_filtered, ordered)
    │
    ▼  [FeatureEngine — SOLE PRODUCER of ProfileFeatures]
    ├──→ ObservationUpdater → FeatureCandidate[]
    ├──→ CalibrationUpdater → validation flags
    └──→ (ReplayUpdater — replay path only)
    │
    ▼  [FeatureComposer]
ProfileFeature[]  ──→  CandidateProfile.features (current; session-resident)
    │
    ├──────────────────────────────────────────────────────────────────┐
    ▼  [single writer: NarrativeGenerator]                            │
Narrative (reads CandidateProfile.features)              KnowledgeGapEngine
    │                                                    (reads EvaluationResults)
    │                                                                  │
    │                                               [single writer: CoachingEngine]
    │                                               CoachingPlan
    │                                               (reads KnowledgeGap[] + CandidateProfile.features)
    │                                                                  │
    └──────────────────────────┬───────────────────────────────────────┘
                               ▼  [single writer: ReportBuilder]
                          Report
                               ▼  [single writer: session completion pipeline]
                          CandidateProfileSnapshot
                          (immutable; carries ProfileFeature[] + provenance + schema_version)
                               ▼
                          SessionHistory (write-once)
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         Replay UI      ProgressTracker   CalibrationProfile
        (read-only)     (LearningProgress  (read-only aggregate)
                         derived; never
                         persisted)
```

### Validation

| Property | Status |
|---|---|
| **Single writer per aggregate** | EvidenceStore ← EvaluationEngine. ObservationStore ← ObservationExtractor. CandidateProfile ← FeatureEngine. Narrative ← NarrativeGenerator. CoachingPlan ← CoachingEngine. SessionHistory ← session completion pipeline. ✓ |
| **Single ownership** | Each aggregate has exactly one named producer. ✓ |
| **Determinism** | FeatureEngine produces the same ProfileFeature[] from the same ObservationStore state. No randomness, no clock dependency in feature values. ✓ |
| **Knowledge isolation** | FeatureEngine reads only ObservationStore. It has no dependency on NarrativeGenerator, CoachingEngine, EvidenceStore, or SessionHistory. ✓ |
| **No circular dependencies** | Flow is DAG: EvidenceStore → ObservationStore → FeatureEngine → CandidateProfile → Actions → SessionHistory. ✓ |
| **Immutable facts** | EvidenceSignal, Observation, Narrative, CoachingPlan, CandidateProfileSnapshot, SessionHistory — all immutable after creation. ✓ |
| **Derived knowledge** | CandidateProfile and LearningProgress are always derived, never primary sources of truth. ✓ |

---

## SECTION O — Future Compatibility

### ADR-021 (Evidence Freshness — TTL Policy, Decay Function Shape, Clock Interface)

**Compatible and directly enabled.** ADR-021 defines the freshness decay function consumed by ObservationStore at query time. FeatureEngine receives freshness-weighted Observations from ObservationStore — it does not implement freshness itself. ADR-021 is unblocked by ADR-020 (FeatureEngine design is now stable).

### ADR-022 (SessionHistory Schema Versioning)

**Compatible.** `CandidateProfileSnapshot` carries `schema_version` for each ProfileFeature (ADR-018). ADR-022 governs how SessionHistory stores and migrates these snapshots. FeatureEngine's `feature_engine_version` field on each ProfileFeature enables ADR-022 to build a complete versioning strategy.

### ADR-023 (NarrativeGenerator Profile-Feature-Aware Prompt Design)

**Directly unblocked.** NarrativeGenerator reads `CandidateProfile.features`. The complete ProfileFeature contract is now frozen across ADR-018 + ADR-020. ADR-023 may proceed immediately.

### ADR-025 (CoachingEngine Ranking Algorithm)

**Directly unblocked.** CoachingEngine reads `KnowledgeGap[]` + `CandidateProfile.features`. The complete ProfileFeature contract is frozen. ADR-025 may proceed.

### ADR-027 (LanguageExecutor Abstraction) / ADR-028 (Language Selection Policy)

**Compatible.** FeatureEngine is language-independent. Neither ADR affects the FeatureEngine architecture.

### Knowledge Graph (V2 candidate)

**Compatible.** A future Knowledge Graph would consume `CandidateProfile.features` and `SessionHistory`. FeatureEngine's provenance model (`source_observation_ids` → `ObservationId[]` → `EvidenceSignal[]`) provides the edge data needed to build a knowledge graph without redesigning the pipeline.

### Replay (ADR-026)

**Compatible.** `ReplayUpdater` interface is defined in Section D. V1.2 replay uses `CandidateProfileSnapshot`. V1.3+ full replay activation uses `ReplayUpdater` with the ObservationStore snapshot from SessionHistory. No redesign required.

### Progress Tracking

**Compatible.** `LearningProgress` is derived at query time from `SessionHistory[]`. Each `SessionHistory` entry contains a `CandidateProfileSnapshot` with `FeatureIdentity`-keyed ProfileFeatures. Cross-session progress comparison uses `FeatureIdentity` as the stable key.

### Multi-language (ADR-028)

**Compatible.** Mixed-mode sessions produce `LanguageCapabilityFeature` instances with different `language_context` values. FeatureEngine handles them via type dispatch. No architectural change required.

### Future Feature Types

Compatible per Section J (Plugin Architecture). New feature types require a registry entry and an ADR amendment. No FeatureEngine core changes.

### V1.1 Compatibility

**Confirmed. No frozen V1.1 asset requires change.**

| V1.1 Asset | Status |
|---|---|
| `EvidenceSignal` schema | Protected. Unchanged. |
| `EvidenceStore` contract | Protected. Unchanged. |
| `CandidateProfile` V1.1 fields | Protected. `features` field additive (ADR-048). |
| Pattern detectors (10 existing) | Protected. Unchanged. |
| `ReasonerService` | Protected. Unchanged. |
| `EvaluationEngine` | Protected. Unchanged. |

---

## SECTION P — ADR Backlog Update

### ADR-020 Status

**Accepted.** This document. FeatureEngine Knowledge Construction Engine architecture frozen.

### Updated Backlog

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-020 | FeatureEngine Architecture | FULLY UNBLOCKED | **ACCEPTED** |
| ADR-021 | Evidence Freshness TTL Policy | UNBLOCKED (ADR-017) | **NEXT MILESTONE — P0** |
| ADR-023 | NarrativeGenerator Design | UNBLOCKED (ADR-018) | **ADDITIONALLY UNBLOCKED by ADR-020** |
| ADR-025 | CoachingEngine Ranking Algorithm | UNBLOCKED (ADR-018) | **ADDITIONALLY UNBLOCKED by ADR-020** |

### ADR-021 as Next Milestone

**ADR-021 (Evidence Freshness — TTL Policy, Decay Function Shape, Clock Interface)** is the next milestone.

Rationale:
- ADR-021 defines the freshness decay function that ObservationStore applies before FeatureEngine reads it.
- FeatureEngine's confidence computation (Section I) depends on freshness-weighted Observations.
- Without ADR-021, FeatureEngine receives Observations without freshness weighting — reducing knowledge quality.
- ADR-021 is the last P0 blocker before EPIC-01 and EPIC-05 can begin implementation.

### Critical Path After ADR-020

```
ADR-020 ACCEPTED
    │
    ├──→ ADR-021 (Evidence Freshness) — NEXT MILESTONE; P0; unblocked now
    │
    ├──→ ADR-023 (NarrativeGenerator) — P1; unblocked now; parallel to ADR-021
    │
    ├──→ ADR-025 (CoachingEngine Ranking) — P2; unblocked now; parallel
    │
    └──→ ADR-022 (SessionHistory Schema) — P1; still requires ADR-016A (done) + time
```

---

## SECTION Q — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ FeatureEngine responsibilities frozen | **FROZEN** — Section B: 7 responsibilities + 11 prohibited actions; Domain Invariant I-02 confirmed |
| ✓ Internal architecture frozen | **FROZEN** — Section C: FeatureUpdater, FeatureComposer, FeatureMergePolicy, FeatureReplacementPolicy defined |
| ✓ Updater model frozen | **FROZEN** — Section D: 4 known Updaters; orchestration order; independence invariants; extension policy |
| ✓ Knowledge construction pipeline frozen | **FROZEN** — Section E: Observation → FeatureCandidate → FeatureComposer → ProfileFeature → CandidateProfile; determinism proven |
| ✓ FeatureIdentity frozen | **FROZEN** — Section F: `(feature_type_id, semantic_category)`; schema evolution invariant; registry requirement |
| ✓ Provenance propagation frozen | **FROZEN** — Section G: full chain ObservationId → CandidateProfile → SessionHistory; 3 audit guarantees |
| ✓ Recomputation strategy frozen | **FROZEN** — Section H: full / partial / incremental / replay; determinism invariant; CandidateProfile replaceability |
| ✓ Conflict policies frozen | **FROZEN** — Section I: replacement, merge, superseding policies; confidence, stability, maturity defined |
| ✓ Plugin architecture frozen | **FROZEN** — Section J: registry-based extension; 5-step process; updater isolation invariants |
| ✓ Observability model frozen | **FROZEN** — Section K: 6 diagnostic record types (computation trace, provenance, timing, statistics, replay, audit) |
| ✓ Performance goals frozen | **FROZEN** — Section L: 6 invariants (determinism, single-pass, incremental preference, no O(n²), bounded memory, replay determinism) |
| ✓ Language independence confirmed | **CONFIRMED** — Section M: per-component verification; FeatureEngine never branches on language name |
| ✓ LanguageFamily concept introduced | **FROZEN** — Section M: Dynamic, TypeScript, JVM, Systems, CLR families; domain concept; registry-based; enables cross-family coaching |
| ✓ Runtime validated | **VALIDATED** — Section N: single writer, single ownership, determinism, knowledge isolation, DAG structure |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section O: no frozen V1.1 asset requires change |

---

## Final Recommendation

**ADR-020 is ACCEPTED.**

FeatureEngine is frozen as the Knowledge Construction Engine. The five-step pipeline (Pull → Dispatch → Collect → Compose → Commit), the Updater model, `FeatureIdentity`, provenance chain, recomputation strategy, conflict policies, plugin architecture, and `LanguageFamily` concept are all frozen.

**Immediate next action: ADR-021 (Evidence Freshness — TTL Policy, Decay Function Shape, Clock Interface).** ADR-021 is the last P0 blocker before EPIC-01 and EPIC-05 implementation can begin.

---

## Rationale

The five-stage pipeline (Pull → Dispatch → Collect → Compose → Commit) is the minimal architecture that satisfies all knowledge construction requirements:

- **Synthesis** requires multiple Updaters contributing candidates — not a single transformation.
- **Determinism** requires ordered input and stateless Updaters — not ad-hoc processing.
- **Extensibility** requires a registry-based plugin model — not hard-coded Updater invocations.
- **Conflict resolution** requires an explicit composition stage — not first-writer-wins.
- **Provenance** requires candidate-level tracking from Updater through Composer to ProfileFeature.

The `LanguageFamily` concept is introduced here because it is the first point in the architecture where cross-language knowledge relationships become relevant — specifically in FeatureEngine's handling of `LanguageCapabilityFeature` provenance.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Single monolithic Updater | Violates SRP; becomes a God Object as new feature types are added; no extension point |
| Updaters reading each other's FeatureCandidates | Creates inter-Updater coupling; prevents independent testing; violates updater isolation invariant |
| FeatureComposer as part of each Updater | Each Updater would need to know about all other Updaters' outputs to resolve conflicts; creates circular dependencies |
| LLM-based feature derivation | Non-deterministic; violates P-01; unreplayable; cannot guarantee provenance |
| Event-driven ObservationStore push | ObservationStore would need to know about FeatureEngine; violates the passive-store principle (ADR-017) |

## Consequences

### Positive

- Plugin architecture allows new FeatureUpdaters without FeatureEngine core changes
- `FeatureIdentity` enables correct cross-session comparison and migration-safe schema evolution
- `LanguageFamily` enables cross-language coaching prose without FeatureEngine changes
- Five-stage pipeline is independently testable at each stage
- All V1.1 assets unchanged — zero regression risk

### Negative / Risks

- The `FeatureCandidate` intermediate object adds a stage between Observation and ProfileFeature — implementation must ensure this does not add significant latency
- `FeatureMergePolicy` and `FeatureReplacementPolicy` are defined conceptually here; their concrete logic must be specified in implementation with careful edge case coverage
- `LanguageFamily` registry must be kept in sync with `LanguageRegistry` — a language added to `LanguageRegistry` without a `LanguageFamily` assignment is an incomplete registration

## Implementation Evidence

Architecture only. No production files modified.
Relevant existing assets (unchanged):
- `domain/contracts/reasoning/evidence_signal.py` (frozen)
- `domain/contracts/reasoning/evidence_store.py` (frozen)
- `domain/profile/candidate_profile.py` (features field additive; unchanged)

## Review Trigger

- When a new FeatureUpdater is proposed (requires ADR amendment)
- When `FeatureMergePolicy` or `FeatureReplacementPolicy` requires concrete specification beyond the conceptual model
- When `LanguageFamily` membership changes (requires LanguageRegistry ADR amendment)
- When incremental recomputation boundary conditions are found to produce inconsistent results vs. full recomputation
