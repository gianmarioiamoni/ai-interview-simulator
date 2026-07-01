# ADR-018 — ProfileFeature Knowledge Model & Versioning

**Status:** Accepted — V1.2 Architecture (K2 Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain
**Preconditions:** ADR-016 (Observation Schema & Intelligence Architecture), ADR-016A (CandidateIdentity & Session Ownership), ADR-017 (ObservationStore Lifecycle & Temporal Semantics), K0/K1/K2 frozen
**Supersedes:** ADR-048 (ProfileFeature Abstraction — V1.2 Extension Point) — architecture superseded; reservation record remains
**Superseded by:** Nothing
**Related:** ADR-019, ADR-020, ADR-021, ADR-022, ADR-023, ADR-025, ADR-032

---

## Context

ADR-016 established that ProfileFeature is the derived knowledge layer — the output of FeatureEngine from ObservationStore. ADR-017 froze the ObservationStore lifecycle and confirmed the FeatureEngine read interface.

Neither ADR answered:

- What is a ProfileFeature, conceptually and architecturally?
- What is the complete Feature taxonomy for V1.2?
- How does versioning work across schema evolution, replay, and cross-session comparison?
- What quality properties govern a ProfileFeature?
- How does provenance link a ProfileFeature back to its source Observations?
- Why is ProfileFeature — not Observation — the central knowledge unit of V1.2?

This ADR answers all of the above. It freezes the ProfileFeature Knowledge Model. No implementation, no contracts, no code.

---

## Decision

**ProfileFeature is the central knowledge unit of V1.2.**

It is the boundary between raw interpreted facts (Observations) and downstream actions (Narrative, Coaching, Reports). Every consumer that needs to understand what the candidate knows, how they reason, or how they communicate must read ProfileFeatures — never Observations, never EvidenceSignals.

---

## SECTION A — Purpose: Why ProfileFeature is the Central Knowledge Unit

### The Knowledge Hierarchy

The V1.2 platform maintains a strict three-layer knowledge hierarchy:

```
Facts          →   EvidenceSignal + Observation
                   (what happened; what it means at one moment)

Knowledge      →   ProfileFeature + CandidateProfile
                   (what the candidate is; longitudinal characterisation)

Actions        →   Narrative + Coaching + Reports
                   (what should be communicated and recommended)
```

Each layer depends only on the one above it. No layer reaches past its immediate predecessor.

### Why Facts Are Not Enough for Actions

**EvidenceSignal** is atomic and question-scoped. A single signal says: "at question 4, a strong positive reasoning signal was detected." It carries no interpretation, no cross-question synthesis, no temporal history.

**Observation** adds interpretation: "the candidate demonstrated deep reasoning at question 4." It is timestamped, typed, and traceable. But it is still moment-scoped. An Observation at question 4 does not tell NarrativeGenerator whether that represents a pattern or an outlier.

**ProfileFeature** answers: "the candidate consistently demonstrates deep reasoning across multiple questions." It synthesises multiple Observations over the session lifetime into a named, versionable, confidence-weighted characteristic.

NarrativeGenerator cannot write meaningful coaching prose from an Observation — it cannot tell if question 4 is representative. It can write precise, candidate-specific prose from a ProfileFeature because a ProfileFeature already encodes the synthesis.

### Why Knowledge Must Be Separated From Actions

**Actions are consumption artefacts.** Narrative prose and CoachingPlan directives are generated once, stored immutably, and consumed by display layers. They cannot be regenerated from first principles at query time.

**Knowledge is recomputable.** A ProfileFeature can always be recomputed from its source Observations. CandidateProfile can always be recomputed from the full ObservationStore. This makes the knowledge layer testable, replayable, and independent of the specific action generators that consume it.

Collapsing Knowledge into Actions would make NarrativeGenerator aware of raw Observations — violating ADR-050. Collapsing Knowledge into Facts would require every action consumer to independently re-implement feature synthesis — producing N God Objects.

### Responsibility Freeze

| Concept | Responsibility | Immutable? | Persisted? |
|---|---|---|---|
| `EvidenceSignal` | Atomic runtime evidence (one signal, one question, one dimension) | Yes | Yes (EvidenceStore) |
| `Observation` | Interpreted fact (one or more signals, one session moment) | Yes | Via SessionHistory snapshot |
| `ProfileFeature` | Longitudinal knowledge (one named characteristic, session-wide synthesis) | Per cycle | Via CandidateProfileSnapshot |
| `CandidateProfile` | Current knowledge state (all ProfileFeatures for this session) | Recomputed | No — snapshot only |
| `LearningProgress` | Cross-session derived view (computed from SessionHistory[]) | N/A | Never |
| `Narrative` | Coaching prose (generated from ProfileFeatures) | Yes | Via SessionHistory |
| `CoachingPlan` | Study directives (generated from KnowledgeGaps + ProfileFeatures) | Yes | Via SessionHistory |

---

## SECTION B — Knowledge Model

### Facts → Knowledge → Actions

```
Facts
├── EvidenceSignal     (runtime atomic evidence — ADR-033; V1.1 frozen)
└── Observation        (interpreted fact — ADR-016; new in V1.2)
        │
        ▼  [FeatureEngine — sole producer]
Knowledge
├── ProfileFeature     (named characteristic — THIS ADR)
└── CandidateProfile   (current aggregate of all ProfileFeatures)
        │
        ▼  [NarrativeGenerator, CoachingEngine, ReportBuilder]
Actions
├── Narrative          (coaching prose)
├── CoachingPlan       (study directives)
└── Report             (assembled candidate report)
```

### Layer Dependency Principle

**Each layer depends only on the previous one.**

- Actions depend on Knowledge only. NarrativeGenerator reads `CandidateProfile.features`. It does not read ObservationStore. It does not read EvidenceStore.
- Knowledge depends on Facts only. FeatureEngine reads ObservationStore. It does not read EvidenceStore directly. It does not invoke NarrativeGenerator.
- Facts depend on nothing above them. EvidenceSignal is produced by the evaluation pipeline. Observation is produced by ObservationExtractor from EvidenceSignals. Neither layer knows about ProfileFeatures, Narratives, or CoachingPlans.

This one-way dependency chain means:
- Any layer can be evolved without touching layers above it.
- Any action consumer can be replaced without affecting the knowledge model.
- Replay reconstructs knowledge from preserved facts without rebuilding actions.
- Tests for each layer are isolated from the others.

---

## SECTION C — ProfileFeature: Conceptual Definition

### Purpose

A ProfileFeature is a named, versionable, confidence-weighted characteristic of a candidate, synthesised by FeatureEngine from one or more Observations over the session lifetime. It represents the platform's current best understanding of one dimension of the candidate's capability or behaviour.

### Ownership

FeatureEngine is the sole producer. CandidateProfile holds the current collection of ProfileFeatures. No other component may create or mutate ProfileFeatures.

**Invariant:** `CandidateProfile.features` is written exclusively by FeatureEngine. This invariant may not be violated without a new ADR explicitly superseding ADR-018.

### Identity

A ProfileFeature is identified by:
- `feature_type` — a member of the ProfileFeature taxonomy (see Section D)
- `schema_version` — the version of the feature schema used at computation time
- `candidate_identity_id` — the owning candidate (from ADR-016A)
- `computed_at_question_index` — the session position at which this feature was last computed

Together these form the natural identity of a ProfileFeature. Two ProfileFeatures of the same `feature_type` computed at different question indices are distinct versions of the same characteristic at different points in the session.

### Versioning

Every ProfileFeature carries a `schema_version` field. Versioning is addressed fully in Section G.

### Lifecycle

```
Computed:   by FeatureEngine (sole producer) from ObservationStore contents
Held:       in CandidateProfile.features for the session lifetime
Updated:    by FeatureEngine on each computation cycle (replacing the prior value)
Snapshotted: at session close into CandidateProfileSnapshot
Archived:   stored immutably inside SessionHistory via CandidateProfileSnapshot
Replayed:   read-only from CandidateProfileSnapshot (never re-derived at replay time in V1.2)
```

### Persistence

**ProfileFeatures are NOT independently persisted.** They exist as the current state of CandidateProfile during the session. At session close, CandidateProfile is captured as CandidateProfileSnapshot and stored inside SessionHistory. The ProfileFeatures survive as part of that snapshot.

**Invariant:** CandidateProfile is never persisted directly. Only CandidateProfileSnapshot (an immutable point-in-time capture) is persisted.

### Consumers

| Consumer | What they read | Why |
|---|---|---|
| NarrativeGenerator | `CandidateProfile.features` | Produces coaching prose from synthesised characteristics |
| CoachingEngine | `CandidateProfile.features` + KnowledgeGap[] | Produces ranked CoachingActions |
| ReportBuilder | `CandidateProfile.features` | Assembles the candidate report |
| CalibrationUpdater | `CandidateProfile.features` | Validates feature values against CalibrationProfile baselines |
| ReplayUpdater (V1.3+) | `CandidateProfileSnapshot.features` | Reconstructs profile for cross-session replay |

### Producers

- **FeatureEngine** — sole producer in all operational paths.
- **No other component** may produce or mutate ProfileFeatures.

### Mutability

A ProfileFeature is immutable per computation cycle. When FeatureEngine recomputes a feature (on the next cycle), it replaces the prior value in CandidateProfile with a new, independently immutable ProfileFeature. The prior value is discarded (the history is preserved implicitly by the Observation sequence in ObservationStore).

**Frozen invariant:** No ProfileFeature field may be mutated after FeatureEngine emits it. Recalculation produces a new object, not a mutation of the prior one.

### Confidence

Every ProfileFeature carries a `confidence` value in [0.0, 1.0] representing FeatureEngine's certainty about the characteristic.

Confidence is:
- Computed from the number, freshness, and consistency of source Observations.
- Not a static field — it is always the result of the most recent FeatureEngine computation.
- Available to all consumers to qualify their use of the feature (e.g., NarrativeGenerator may suppress a feature from prose if confidence is below threshold).

A ProfileFeature with confidence below 0.3 is considered **low-confidence**. Consumers may use such features with caveats or suppress them depending on their threshold policy.

### Stability

A ProfileFeature is **stable** when its value has been consistent across multiple FeatureEngine computation cycles. Stability is a derived quality attribute:

- `stable` — value has not changed direction across the last N cycles (N defined by ADR-020)
- `unstable` — value has oscillated across recent cycles
- `emerging` — feature is new and has been computed in fewer than the stability threshold of cycles

Stability is communicated to consumers alongside confidence. NarrativeGenerator uses stability to qualify how definitively a characteristic is presented.

### Freshness Awareness

ProfileFeature is computed from Observations. Observations have freshness weights (ADR-017, ADR-021). FeatureEngine incorporates freshness weighting when computing ProfileFeatures, giving higher weight to recent Observations.

ProfileFeature itself is **freshness-aware but not freshness-bearing**. It does not store freshness metadata. Its freshness is implicit in when it was last computed (the `computed_at_question_index` field). Consumers should treat a ProfileFeature computed at an early question_index as potentially stale if they are operating near the end of the session.

### Language Independence

ProfileFeatures are always language-independent. A ReasoningFeature computed from Python coding questions and a ReasoningFeature computed from Java coding questions are instances of the same feature type. The `language_context` of the source Observations is available in the provenance record but does not change the feature's type, value, or semantics.

**Invariant:** No ProfileFeature type name may reference a programming language. `PythonReasoningFeature` is not a valid type. `ReasoningFeature` derived from Python observations is.

### Temporal Behaviour

A ProfileFeature reflects the candidate's characteristic as synthesised from all relevant Observations up to the current question_index, weighted by freshness. It is session-scoped in V1.2. In V1.3+, it may incorporate cross-session Observations from persistent ObservationStore.

### Replay Behaviour

In V1.2, replay uses `CandidateProfileSnapshot` — the frozen set of ProfileFeatures computed at session close. Replay does not re-execute FeatureEngine. It displays the profile as it was at close time.

In V1.3+, `ReplayUpdater` may re-derive ProfileFeatures from the Observation history stored in SessionHistory, enabling per-question-index profile reconstruction.

---

## SECTION D — Feature Taxonomy

The ProfileFeature taxonomy is a controlled vocabulary of characteristic types. It is a domain registry — not a runtime enum — extended only when a new capability domain is identified and approved by ADR.

### V1.2 Frozen Taxonomy

#### TechnicalSkillFeature

**Purpose:** Represents the candidate's domain knowledge depth and breadth in a technical area.
**Produced from:** `KNOWLEDGE_DEPTH_HIGH`, `KNOWLEDGE_DEPTH_LOW`, `KNOWLEDGE_GAP_DETECTED`, `REPEATED_STRENGTH`, `REPEATED_WEAKNESS` observations.
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes. A `TechnicalSkillFeature` in Python and Java describes the same knowledge dimension.

#### ReasoningFeature

**Purpose:** Represents the candidate's analytical reasoning quality — depth, clarity, and progression.
**Produced from:** `REASONING_DEEP`, `REASONING_SHALLOW`, `REASONING_IMPROVING`, `REASONING_STAGNATING` observations.
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes. Reasoning quality is universal.

#### CommunicationFeature

**Purpose:** Represents the clarity, consistency, and effectiveness of the candidate's communication.
**Produced from:** `COMMUNICATION_CLEAR`, `COMMUNICATION_WEAK`, `COMMUNICATION_INCONSISTENT` observations.
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes. Communication is not language-execution-specific.

#### LeadershipFeature

**Purpose:** Represents the candidate's demonstrated leadership behaviours and patterns.
**Produced from:** `LEADERSHIP_STRONG`, `LEADERSHIP_EMERGING`, `LEADERSHIP_ABSENT` observations (ADR-066).
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes.

#### CollaborationFeature

**Purpose:** Represents the candidate's demonstrated collaboration and teamwork behaviours.
**Produced from:** `COLLABORATION_STRONG`, `COLLABORATION_EFFECTIVE`, `COLLABORATION_DEFICIT` observations (ADR-066).
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes.

#### AdaptabilityFeature

**Purpose:** Represents the candidate's capacity to adapt reasoning and approach across question types and difficulty.
**Produced from:** `ADAPTABILITY_HIGH`, `ADAPTABILITY_MODERATE`, `ADAPTABILITY_LOW` observations (ADR-066).
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes.

#### LearningFeature

**Purpose:** Represents evidence of in-session learning — the candidate improving their responses based on feedback or prior questions.
**Produced from:** `BEHAVIORAL_GROWTH`, `REASONING_IMPROVING`, `TREND_IMPROVING` observations (composite).
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes.

#### ConfidenceFeature

**Purpose:** Represents the candidate's confidence calibration — the alignment between self-assessed confidence and demonstrated capability.
**Produced from:** `CONFIDENCE_WELL_CALIBRATED`, `CONFIDENCE_OVERCONFIDENT`, `CONFIDENCE_UNDERCONFIDENT`, `CONFIDENCE_UNSTABLE` observations.
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes.

#### LanguageCapabilityFeature

**Purpose:** Represents language-specific idiomatic proficiency patterns — not general reasoning, but command of the specific language's idioms, constructs, and type system.
**Produced from:** `LANGUAGE_IDIOMATIC_USAGE`, `LANGUAGE_TYPE_ERROR_PATTERN`, `LANGUAGE_CONSTRUCT_CONFUSION` observations.
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Partial exception — this feature carries `language_context` in its provenance because its meaning is language-relative. A `LanguageCapabilityFeature` derived from Python observations is semantically different from one derived from Java observations, even though the feature type is the same. The feature value describes idiomatic competence within the specific language. The taxonomy type is still language-independent; the interpretation is language-contextual.
**Note:** This is the only feature type where `language_context` in provenance affects consumer interpretation. All other feature types are fully language-independent.

#### CoverageFeature

**Purpose:** Represents the breadth of topic coverage demonstrated by the candidate across the session.
**Produced from:** `AREA_COVERAGE_STRONG`, `AREA_COVERAGE_WEAK`, `AREA_MISSING` observations.
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes.

#### TrendFeature

**Purpose:** Represents a directional trend in the candidate's performance over the session — improving, declining, or flat.
**Produced from:** `TREND_IMPROVING`, `TREND_DECLINING`, `TREND_FLAT`, `BEHAVIORAL_GROWTH`, `BEHAVIORAL_PLATEAU` observations.
**Ownership:** FeatureEngine via ObservationUpdater.
**Language independence:** Yes.

### Reserved Future Types (V1.3+)

| Feature Type | Intended Use |
|---|---|
| `ProgressFeature` | Cross-session improvement signal derived from SessionHistory[] |
| `CalibrationFeature` | Per-session score distribution deviation from CalibrationProfile |
| `LearningPaceFeature` | Speed of concept acquisition across sessions |
| `CrossDomainTransferFeature` | Knowledge transfer patterns across different technical domains |
| `EngineeringJudgmentFeature` | System design and trade-off reasoning quality |

### Extension Policy

New ProfileFeature types require:
1. A new or amended ADR naming the type, its source ObservationTypes, its FeatureEngine Updater mapping, and its consumer contract.
2. A corresponding entry in the ProfileFeature type registry.
3. A new `schema_version` assignment.
4. Backward-compatible addition — existing stored ProfileFeatures (in CandidateProfileSnapshots) are unaffected.

No ProfileFeature type may be removed without a deprecation ADR and a migration period during which both versions are supported.

**No classes are defined here.** This taxonomy is a domain vocabulary. Implementation follows in ADR-020 (FeatureEngine Architecture).

---

## SECTION E — FeatureEngine Boundary

### Frozen Invariants

FeatureEngine is the **sole producer of ProfileFeatures**. This is Domain Invariant I-02.

```
ObservationStore  ──[read-only]──→  FeatureEngine  ──[write]──→  CandidateProfile.features
```

| FeatureEngine does | FeatureEngine does NOT do |
|---|---|
| Reads ObservationStore (freshness-filtered, ordered) | Create Observations |
| Produces ProfileFeature[] | Create Narrative content |
| Updates CandidateProfile.features | Create CoachingActions |
| Orchestrates Updaters (ObservationUpdater, CalibrationUpdater, ReplayUpdater) | Write to ObservationStore |
| Handles provenance (links ProfileFeature → source Observations) | Read EvidenceStore directly |
| Applies freshness weighting (from ADR-021 policy) | Invoke LLM calls |
| Computes confidence and stability values | Write to SessionHistory |

### Invariant Statement

> **FeatureEngine ONLY reads ObservationStore.**
> **FeatureEngine ONLY produces ProfileFeatures.**
> **FeatureEngine updates Current CandidateProfile.**
> **FeatureEngine NEVER creates Observations.**
> **FeatureEngine NEVER creates Narrative.**
> **FeatureEngine NEVER creates Coaching.**

This invariant is permanent. Violation requires a new ADR explicitly superseding ADR-018.

### Updater Composition

FeatureEngine orchestrates Updaters. Each Updater handles a specific subset of ObservationTypes and produces a specific subset of ProfileFeature types:

| Updater | Input | Output | Status |
|---|---|---|---|
| `ObservationUpdater` | ObservationStore (freshness-filtered) | ProfileFeature[] (all types) | V1.2 active |
| `CalibrationUpdater` | CandidateProfile.features + CalibrationProfile | Validation flags (not new features) | V1.2 active |
| `ReplayUpdater` | SessionHistory ObservationStore snapshot | ProfileFeature[] for a historical session | V1.2 interface reserved; full activation V1.3+ |
| `LearningUpdater` | Cross-session ObservationStore (persistent) | ProgressFeature, LearningPaceFeature | Reserved for V1.3+ |

The internal composition model is the subject of ADR-020. This ADR freezes only the outer boundary.

---

## SECTION F — Feature Provenance

### Provenance Principle

> **Every ProfileFeature must be traceable to its source Observations.**

Provenance is a first-class property of the knowledge model. It enables:
- Audit of what evidence produced a given characteristic
- Replay reconstruction of the evidence chain
- Consumer qualification of feature claims
- Debugging of unexpected feature values

### Provenance Chain

```
ProfileFeature
    │
    └──→ Generated From
              │
              └──→ Observation[]
                        │
                        └──→ ObservationId[]
                                  │
                                  └──→ EvidenceSignal[]
                                            (via source_signal_ids on each Observation)
```

### Provenance Requirements

Every ProfileFeature must carry:
- `source_observation_ids` — the list of `ObservationId` values from which this feature was derived
- `schema_version` — the version of the feature schema used at computation time
- `computed_at_question_index` — the session position at which this provenance record was assembled
- `feature_engine_version` — the version of FeatureEngine that produced this feature (for forward compatibility)

Provenance is immutable once FeatureEngine emits the ProfileFeature. When FeatureEngine recomputes a feature on a subsequent cycle, a new ProfileFeature is produced with updated provenance. The prior provenance is not mutated — it is discarded with the prior ProfileFeature object.

### Provenance and Replay

The provenance chain enables V1.3+ replay to reconstruct the exact evidence basis for any characteristic at any session position. Given:
1. A `CandidateProfileSnapshot` with provenance records
2. The corresponding `ObservationStore` snapshot in `SessionHistory`
3. The original `EvidenceStore` records

A complete audit trail is recoverable: from final ProfileFeature value back to the atomic EvidenceSignal that contributed to it.

**No implementation.** Provenance is a conceptual property frozen here. The implementation fields are defined in ADR-020 (FeatureEngine Architecture).

---

## SECTION G — Feature Versioning

### Why Versioning Belongs to ProfileFeature

ProfileFeatures are persisted (via CandidateProfileSnapshot inside SessionHistory). A session from six months ago has a ProfileFeature computed under an older schema. When that session is replayed, progress-tracked, or compared cross-session, the consumer must know what version of the schema it is reading.

Versioning belongs to ProfileFeature — not to Observation, not to CandidateProfile — because:

1. **Observations are typed facts.** They do not change shape based on how downstream consumers interpret them. Observation versioning is independent (ADR-016).
2. **CandidateProfile is not persisted.** It is session-resident. Its schema is always the current one.
3. **ProfileFeatures are persisted in snapshots.** They outlive the session. A snapshot written today may be read under a future schema. The version must travel with the feature.
4. **Cross-session comparison requires version awareness.** LearningProgress compares ProfileFeatures from different sessions. If `ReasoningFeature_v1` and `ReasoningFeature_v2` have different field structures, the comparison layer must know.

### Feature Schema Version

Every ProfileFeature carries `schema_version` — a string identifier (e.g., `"1.0"`, `"1.1"`, `"2.0"`).

Version semantics:
- Minor version increments (`1.0` → `1.1`): additive changes only (new optional fields). Backward-compatible. All readers of v1.0 can read v1.1 by ignoring unknown fields.
- Major version increments (`1.x` → `2.0`): breaking changes. Prior versions are no longer guaranteed compatible. A migration policy is required.

### Forward Compatibility

Consumers (NarrativeGenerator, CoachingEngine, ReportBuilder, ReplayUpdater) must be designed to handle feature schemas they have not seen before, by:
- Ignoring unknown fields (additive changes are safe)
- Treating missing optional fields as absent (not as errors)
- Using the `schema_version` field to branch behaviour when major version differences exist

### Backward Compatibility

FeatureEngine emits the current schema version. Older stored versions remain valid. No retroactive migration of stored CandidateProfileSnapshots is required for minor version changes.

For major version changes:
- A migration ADR is required.
- FeatureEngine must be capable of reading all stored versions that are still referenced by active SessionHistory records.
- A deprecation schedule must be defined.

### Migration Policy

1. A new major version is introduced by a new ADR.
2. The new version is emitted by FeatureEngine from the migration release forward.
3. Old versions remain readable by all consumers for a defined support window.
4. After the support window, a migration script converts stored snapshots from the old version to the new (or marks them as legacy-read-only).
5. No migration may be destructive — the original snapshot must be preserved alongside the migrated one until the support window closes.

### Feature Evolution

Adding a new field to a ProfileFeature type (e.g., adding `maturity` to `ReasoningFeature`) is a minor version change. The new field is optional and absent from older snapshots.

Renaming a field, changing a field's type, or changing the semantics of a field's value is a major version change requiring migration.

Adding a new ProfileFeature type (e.g., `EngineeringJudgmentFeature`) is additive — it requires a registry entry and a minor or major version increment depending on whether it affects cross-session comparison assumptions.

### Replay Compatibility

Replay always uses the `CandidateProfileSnapshot` stored in `SessionHistory`. The snapshot carries its own `schema_version`. The replay system must read the version it was stored with — it does not re-derive the profile from current schema.

**Invariant:** Replay never recomputes a ProfileFeature from source Observations at read time (in V1.2). What was stored is what is displayed.

### Profile Reconstruction

Cross-session profile reconstruction (V1.3+) requires the `ReplayUpdater` to re-derive ProfileFeatures from the preserved Observation history. When doing so:
- The `schema_version` used is the current one at reconstruction time.
- The reconstructed features may differ from the originally stored features if the FeatureEngine logic or schema has evolved.
- Both the original stored feature and the reconstructed feature are available: the original from CandidateProfileSnapshot; the reconstructed from ReplayUpdater output.
- LearningProgress uses the stored originals for consistency. Reconstructed features are for audit and validation only.

---

## SECTION H — Current CandidateProfile

### Definition

Current CandidateProfile is the live, session-resident aggregate that holds the current state of all ProfileFeatures for the active session.

It represents **the current knowledge about the candidate** — not historical knowledge, not a prediction, not a report. It is the platform's best answer to "what do we know about this candidate right now?"

### Properties

| Property | Value |
|---|---|
| Derived | Yes — produced entirely by FeatureEngine from ObservationStore |
| Mutable | Yes — FeatureEngine updates it on each computation cycle |
| Recomputable | Yes — given the same ObservationStore state, FeatureEngine produces the same profile |
| Session-resident | Yes — lives in memory for the duration of the session |
| Never persisted directly | Yes — only CandidateProfileSnapshot (an immutable copy) is persisted |

### Frozen Invariant

> **Current CandidateProfile is NEVER persisted directly.**
> **Only CandidateProfileSnapshot (a point-in-time immutable capture) is persisted.**

Rationale:
- The live profile evolves during the session. Persisting it directly would create a stale-reference problem.
- Its value at session close is captured precisely by the snapshot mechanism.
- Storing the live object would conflate the mutable runtime state with the immutable historical record.

### Sole Writer

FeatureEngine is the sole writer to `CandidateProfile.features`. No component may write ProfileFeatures directly to CandidateProfile. This is Domain Invariant I-02 (shared with the FeatureEngine boundary invariant).

---

## SECTION I — CandidateProfileSnapshot

### Relationship Model

```
Current CandidateProfile
    │
    │  [session close event — sole writer: session completion pipeline]
    ▼
CandidateProfileSnapshot
    │
    │  [stored inside SessionHistory — write-once]
    ▼
SessionHistory
    │
    │  [derived at query time — never persisted]
    ▼
LearningProgress
```

### Snapshot Properties

| Property | Value |
|---|---|
| Immutable | Yes — a snapshot is a frozen value object; no field may change after creation |
| Point-in-time | Yes — captures the state of CandidateProfile at session close |
| Persisted | Yes — stored inside SessionHistory |
| Versioned | Yes — carries `schema_version` of the ProfileFeature schema used |
| Self-contained | Yes — the snapshot carries all information needed to display or compare the profile without re-deriving it |

### Frozen Principles

**Principle 1:** Snapshots are immutable.
A snapshot is a permanent historical record. No process may update a stored snapshot. If a re-computation is needed (e.g., for audit purposes), a new, separate value is produced alongside the original — never replacing it.

**Principle 2:** Snapshots preserve history.
Every completed session produces exactly one snapshot. The snapshot is the authoritative record of what the platform concluded about the candidate at that session close.

**Principle 3:** Replay uses snapshots.
In V1.2, the replay subsystem reads the `CandidateProfileSnapshot` from `SessionHistory`. Replay does not re-execute FeatureEngine. The snapshot is the replay input for profile display.

**Principle 4:** Current profile never becomes history.
The live `CandidateProfile` object is not the same object as the `CandidateProfileSnapshot`. The live profile is discarded at session end. The snapshot is what is preserved.

**Principle 5:** History never becomes current profile.
Reading a `CandidateProfileSnapshot` from `SessionHistory` never populates the live `CandidateProfile` for a new session. A new session always starts with an empty profile, populated by FeatureEngine from the new session's ObservationStore.

---

## SECTION J — Knowledge Quality Model

### Feature Confidence

**Definition:** The degree to which FeatureEngine trusts the current value of a ProfileFeature.

**Range:** [0.0, 1.0]

**Inputs to confidence:**
- Number of source Observations (more observations → higher potential confidence)
- Consistency of source Observations (consistent direction → higher confidence; contradictory → lower)
- Freshness of source Observations (recent observations weighted higher — ADR-021)
- Observation quality (confidence values on source Observations propagate upward)

**Consumer use:** Consumers may suppress features below their threshold, qualify narrative prose, or present confidence bands in reports. Confidence does not block feature production — low-confidence features are still valid, just less certain.

### Feature Stability

**Definition:** The degree to which a feature's value has been consistent across multiple FeatureEngine computation cycles within the session.

**States:** `stable`, `unstable`, `emerging`

- `stable`: Value direction has not changed in the last N computation cycles (N defined in ADR-020).
- `unstable`: Value direction has oscillated across recent cycles.
- `emerging`: Feature has been computed fewer than the stability threshold of times.

**Consumer use:** NarrativeGenerator uses stability to qualify how definitively a characteristic is presented. An `unstable` ReasoningFeature warrants hedged prose. A `stable` one warrants a definitive statement.

### Feature Maturity

**Definition:** The stage of a feature's development within the session lifecycle.

**Stages:**
- `nascent`: Derived from 1–2 Observations. Insufficient basis for strong claims.
- `developing`: Derived from 3–5 Observations. Pattern is forming.
- `mature`: Derived from 6+ Observations with consistent direction. High confidence warranted.

**Consumer use:** ReportBuilder may defer presenting features in the `nascent` stage, or present them with explicit caveats.

### Feature Freshness Awareness

**Definition:** The degree to which the source Observations for a ProfileFeature are temporally recent within the session.

A ProfileFeature is **freshness-aware** but not freshness-bearing. It reflects the freshness of its inputs through its confidence value (fresher inputs → higher confidence, all else equal). It does not independently track its own freshness.

**Consumer use:** Consumers may compare `computed_at_question_index` against the current question index to assess how stale a feature is. A feature computed at question 3 that has not been recomputed by question 12 may reflect an outdated state.

### Feature Consistency

**Definition:** The degree to which a feature's value is consistent with related features.

A `ConfidenceFeature` of `OVERCONFIDENT` is inconsistent with a `TechnicalSkillFeature` of `HIGH` (a highly skilled candidate who is overconfident is unusual). CalibrationUpdater flags cross-feature inconsistencies for FeatureEngine to review.

**Consumer use:** Consistency flags are available to NarrativeGenerator for identifying unusual candidate profiles that warrant specific prose handling.

### Feature Completeness

**Definition:** The proportion of expected feature types for which values have been computed.

A session with 12 questions should, under normal conditions, produce values for all 11 V1.2 feature types. If only 6 feature types have values (e.g., because question coverage was narrow), the profile is incomplete. Completeness is a property of CandidateProfile, not of individual ProfileFeatures.

**Consumer use:** ReportBuilder uses completeness to decide whether to present a full report or a partial report with explicit coverage gaps.

### Quality Relationships

```
Confidence  ←── (Observation count, Observation consistency, Observation freshness)
Stability   ←── (Confidence trend across cycles)
Maturity    ←── (Observation count milestone)
Freshness   ←── (computed_at_question_index vs. current question_index)
Consistency ←── (cross-feature logical coherence, via CalibrationUpdater)
Completeness ←── (count of feature types with computed values vs. expected)
```

All six quality properties are derived — none are stored independently. They are computed by FeatureEngine at each cycle and carried by the emitted ProfileFeature objects.

---

## SECTION K — Observation Relationship

### One-Way Dependency

```
ObservationId
    │
    ▼
Observation  ──→  ObservationStore
    │
    ▼  [FeatureEngine reads]
ProfileFeature  ──→  CandidateProfile
```

**Observations never depend on ProfileFeatures.**
**ProfileFeatures always depend on Observations.**

This is a one-way dependency. It is not bidirectional.

### Frozen Invariant

> **An Observation is created by ObservationExtractor from EvidenceSignals.**
> **An Observation does not know about ProfileFeatures.**
> **An Observation does not know about CandidateProfile.**
> **An Observation does not know about Narrative or CoachingPlan.**

> **A ProfileFeature is created by FeatureEngine from Observations.**
> **A ProfileFeature knows about its source Observations (via provenance).**
> **A ProfileFeature does not write back to ObservationStore.**
> **A ProfileFeature does not modify the Observations it was derived from.**

The one-way dependency ensures:
- ObservationStore can be queried, extended, or decayed without any awareness of the downstream profile.
- ProfileFeature schema can evolve without changing the Observation schema.
- New ProfileFeature types can be added without changing ObservationExtractor.

---

## SECTION L — Language Independence

### Principle

ProfileFeatures are always language-independent. Programming language is context; knowledge is universal.

### Demonstration

```
Python question → REASONING_DEEP observation
                → ReasoningFeature(value=HIGH, confidence=0.85)

Java question   → REASONING_DEEP observation
                → ReasoningFeature(value=HIGH, confidence=0.85)
```

The same `ReasoningFeature` type and value is produced regardless of source language. The source Observation carries `language_context=PYTHON` or `language_context=JAVA`, but the derived feature does not.

```
Python question → LANGUAGE_IDIOMATIC_USAGE observation (language_context=PYTHON)
                → LanguageCapabilityFeature(language_context=PYTHON, value=HIGH)

Java question   → LANGUAGE_IDIOMATIC_USAGE observation (language_context=JAVA)
                → LanguageCapabilityFeature(language_context=JAVA, value=MODERATE)
```

`LanguageCapabilityFeature` is the one exception where language context travels into the feature for consumer interpretation. Even so, the feature **type** is identical. Only the provenance `language_context` differs. This does not violate language independence — it is a qualified result within a universally-typed feature.

### Rationale

1. **Candidate knowledge is portable.** A candidate who reasons well in Python reasons well because of analytical skill, not because of Python. The platform must characterise that skill universally.
2. **Cross-language comparison requires a common vocabulary.** If `ReasoningFeature` were language-specific, cross-session progress tracking (comparing Python session to Java session) would be impossible without a translation layer.
3. **Adding a new language must not require new feature types.** This is the architectural guarantee: adding Go, Rust, or C# requires only a new `LanguageExecutor` and `LanguagePolicy`. Zero feature taxonomy changes.

---

## SECTION M — Future Compatibility

### ADR-019 (LanguageConfig Design — ProgrammingLanguage as Abstract Concept)

**Compatible.** ProfileFeature taxonomy is language-independent. `LanguageCapabilityFeature` carries `language_context` from the abstract `ProgrammingLanguage` domain concept. ADR-019 defines that concept; ADR-018 uses it. No conflict.

### ADR-021 (Evidence Freshness — TTL Policy, Decay Function Shape, Clock Interface)

**Compatible.** ProfileFeature is freshness-aware through its confidence value. ADR-021 defines the decay function and TTL policy applied by FeatureEngine when weighting source Observations. ADR-018 freezes the freshness-awareness property; ADR-021 fills the mechanism. No conflict.

### ADR-022 (SessionHistory Schema Versioning & Migration Policy)

**Compatible.** `CandidateProfileSnapshot` is stored inside `SessionHistory`. Its `schema_version` (frozen here) governs how ReplayUpdater and ProgressTracker read it. ADR-022 governs the SessionHistory schema container. No conflict; ADR-022 must align its versioning policy with the ProfileFeature `schema_version` strategy frozen here.

### ADR-023 (NarrativeGenerator Profile-Feature-Aware Prompt Design)

**Directly unblocked by ADR-018.** NarrativeGenerator reads `CandidateProfile.features`. ADR-018 defines what features are available and their quality properties. ADR-023 may now design the prompt injection contract for all 11 V1.2 feature types.

### ADR-032 (CandidateProfileSnapshot Strategy)

**Directly unblocked by ADR-018.** ADR-032 defines the snapshot structure and versioning. ADR-018 defines the ProfileFeature schema and version field. These are the two inputs ADR-032 needs. Proceed to ADR-032 after ADR-022.

### Future Feature Types

The extension policy in Section D ensures that future feature types (V1.3+) can be added by:
1. A new ADR naming the type and its source ObservationTypes.
2. A new registry entry.
3. A minor or major version increment.
4. Zero changes to existing consumers (they ignore unknown feature types until they explicitly adopt them).

### Narrative, Coaching, Replay, Progress, Knowledge Graph

All confirmed compatible per ADR-016 and ADR-017 analysis. ProfileFeature is the universal input to all action consumers. No action consumer reaches past ProfileFeature into Observations or EvidenceSignals.

### V1.1 Compatibility

**Confirmed. No frozen V1.1 asset requires change.**

| V1.1 Asset | Status |
|---|---|
| `EvidenceSignal` schema | Protected. Unchanged. |
| `EvidenceStore` contract | Protected. Unchanged. |
| `EvidenceType` catalog | Protected. Unchanged. |
| `CandidateProfile` V1.1 fields | Protected. `features` field is additive (default_factory=dict, reserved by ADR-048). |
| Pattern detectors (10 existing) | Protected. Unchanged. |
| `ReasonerService` | Protected. Unchanged. |
| `EvaluationEngine` | Protected. Unchanged. |

---

## SECTION N — Runtime Validation

### Canonical Runtime Flow

```
Evaluation (answer submitted)
    │
    ▼  [single writer: EvaluationEngine]
EvaluationSignalWriter
    │
    ▼
EvidenceSignal  ──→  EvidenceStore (append-only; V1.1 frozen contract)
    │
    ▼  [single writer: ObservationExtractor — SOLE OBSERVATION PRODUCER]
Observation  ──→  ObservationStore (append-only; Independent Aggregate Root; ADR-016/017)
    │
    ▼  [single writer: FeatureEngine — SOLE PROFILEFEATURE PRODUCER]
ProfileFeature[]  ──→  CandidateProfile.features (session-resident; recomputed per cycle)
    │
    ├─────────────────────────────────────────────────────────────────────┐
    ▼  [single writer: NarrativeGenerator]                               │
Narrative                                                      KnowledgeGapEngine
(reads CandidateProfile.features only)                         (reads EvaluationResults)
NEVER reads: ObservationStore, EvidenceStore, Detectors                   │
(ADR-050 boundary)                                                        ▼
    │                                                          KnowledgeGap[]
    │                                                                     │
    │                                                 [single writer: CoachingEngine]
    │                                                 CoachingPlan
    │                                                 (reads KnowledgeGap[] + CandidateProfile.features)
    │                                                 NEVER reads: ObservationStore, EvidenceStore
    │                                                 (ADR-067 boundary)
    │                                                                     │
    └──────────────────────────┬──────────────────────────────────────────┘
                               ▼  [single writer: ReportBuilder]
                          Report (assembled)
                               │
                               ▼  [single writer: session completion pipeline]
                          CandidateProfileSnapshot
                          (immutable; carries ProfileFeature[] with schema_version)
                               │
                               ▼  [single writer: session completion pipeline — SOLE WRITER]
                          SessionHistory (write-once, immutable)
                          Stores: CandidateProfileSnapshot, Narrative, CoachingPlan,
                                  ObservationStore snapshot, EvaluationResults, LanguageProfile
                               │
                   ┌───────────┼──────────────────┐
                   ▼           ▼                  ▼
              Replay UI  ProgressTracker    CalibrationProfile
             (read-only)  (LearningProgress   (read-only aggregate)
                           derived; never
                           persisted)
```

### Runtime Property Verification

| Property | Verification |
|---|---|
| **Single writer per aggregate** | EvidenceStore ← EvaluationSignalWriter. ObservationStore ← ObservationExtractor. CandidateProfile.features ← FeatureEngine. Narrative ← NarrativeGenerator. CoachingPlan ← CoachingEngine. SessionHistory ← session completion pipeline. ✓ |
| **Single ownership** | Each aggregate has exactly one named producer. ✓ |
| **Immutable facts** | EvidenceSignal (frozen). Observation (frozen at creation). Narrative (write-once). CoachingPlan (write-once). SessionHistory (write-once). CandidateProfileSnapshot (write-once). ✓ |
| **Derived knowledge** | CandidateProfile (derived by FeatureEngine per cycle). LearningProgress (derived at query time). Neither is a source of truth. ✓ |
| **Action consumers** | NarrativeGenerator, CoachingEngine, ReportBuilder are terminal. They do not write back to any upstream aggregate. ✓ |
| **No circular dependencies** | Flow is a DAG: EvidenceStore → ObservationStore → FeatureEngine → CandidateProfile → {Narrative, CoachingPlan} → SessionHistory. No upward references. ✓ |

---

## SECTION O — ADR Backlog Update

### ADR-018 Status

**Accepted.** This document. ProfileFeature Knowledge Model and Versioning frozen.

### Updated Backlog (status changes only)

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-016 | Observation Schema & Intelligence Architecture | ACCEPTED | Unchanged ✓ |
| ADR-016A | CandidateIdentity & Session Ownership | ACCEPTED | Unchanged ✓ |
| ADR-017 | ObservationStore Lifecycle & Temporal Semantics | ACCEPTED | Unchanged ✓ |
| ADR-018 | ProfileFeature Schema Freeze & Versioning Policy | UNBLOCKED | **ACCEPTED** |
| ADR-019 | LanguageConfig Design | Pending (parallel) | Unchanged — independent track |
| ADR-020 | FeatureEngine Architecture | Blocked on ADR-016, ADR-018 | **UNBLOCKED** — proceed to ADR-020 |
| ADR-021 | Evidence Freshness TTL Policy | UNBLOCKED (ADR-017) | Unchanged — independent track |
| ADR-022 | SessionHistory Schema Versioning | Pending | Unchanged |
| ADR-023 | NarrativeGenerator Profile-Feature-Aware Design | Blocked on ADR-018 | **UNBLOCKED** — proceed after ADR-020 |
| ADR-025 | CoachingEngine Ranking Algorithm | Blocked on ADR-018 | **UNBLOCKED** — proceed after ADR-020 |
| ADR-032 | CandidateProfileSnapshot Strategy | P1 | Unchanged — requires ADR-022 |

### ADR-019 Confirmed as Next Milestone

ADR-019 (LanguageConfig Design — ProgrammingLanguage as Abstract Concept) is the next milestone. It is parallel to ADR-018 and unblocked by it. ADR-019 remains on its own track and may proceed immediately.

However, the **critical implementation path** after ADR-018 is:

```
ADR-018 ACCEPTED
    │
    ├──→ ADR-020 (FeatureEngine Architecture) — HIGHEST PRIORITY
    │
    ├──→ ADR-019 (LanguageConfig) — parallel, independent
    │
    └──→ ADR-021 (Freshness TTL) — parallel, independent
```

ADR-020 is now the primary blocker for EPIC-01 implementation.

---

## SECTION P — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ Knowledge Model frozen | **FROZEN** — Section B defines Facts/Knowledge/Actions with explicit layer dependencies |
| ✓ Facts / Knowledge / Actions responsibilities frozen | **FROZEN** — Section A freezes all seven concept responsibilities |
| ✓ ProfileFeature frozen | **FROZEN** — Section C defines Purpose, Ownership, Identity, Versioning, Lifecycle, Persistence, Consumers, Producers, Mutability, Confidence, Stability, Freshness awareness, Language independence, Temporal behaviour, Replay behaviour |
| ✓ Feature taxonomy frozen | **FROZEN** — Section D defines 11 V1.2 types + reserved future types + extension policy |
| ✓ FeatureEngine boundary frozen | **FROZEN** — Section E defines all invariants; sole producer pattern confirmed |
| ✓ Provenance frozen | **FROZEN** — Section F defines the ProfileFeature → Observation[] → ObservationId[] chain |
| ✓ Versioning frozen | **FROZEN** — Section G defines schema_version, forward/backward compatibility, migration policy, replay compatibility, profile reconstruction |
| ✓ CandidateProfile frozen | **FROZEN** — Section H defines derived/mutable/recomputable/session-resident/never-persisted |
| ✓ Snapshot relationship frozen | **FROZEN** — Section I defines Current Profile → Snapshot → SessionHistory with all 5 frozen principles |
| ✓ Feature quality model frozen | **FROZEN** — Section J defines Confidence, Stability, Maturity, Freshness awareness, Consistency, Completeness |
| ✓ Observation dependency invariant frozen | **FROZEN** — Section K confirms one-way dependency; Observation never depends on ProfileFeature |
| ✓ Language independence confirmed | **CONFIRMED** — Section L; only LanguageCapabilityFeature carries language context in provenance; all other types fully language-independent |
| ✓ Runtime validated | **VALIDATED** — Section N confirms single writer, single ownership, immutable facts, derived knowledge, action consumers, DAG structure |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section M; no frozen V1.1 asset requires change |

---

## Final Recommendation

**ADR-018 is ACCEPTED.**

The ProfileFeature Knowledge Model is frozen. All 11 V1.2 feature types are defined. FeatureEngine boundary invariants are set. Versioning strategy is established. The Facts → Knowledge → Actions hierarchy is locked.

**Immediate next action:** Proceed to ADR-020 (FeatureEngine Architecture — Orchestrator + Updater Composition). All preconditions are met. ADR-020 is the primary blocker for EPIC-01 implementation.

**ADR-019 (LanguageConfig) and ADR-021 (Freshness TTL)** may proceed in parallel on independent tracks.

**ADR-023 (NarrativeGenerator)** and **ADR-025 (CoachingEngine Ranking)** are now unblocked and may be scheduled after ADR-020.

---

## Rationale

The three-layer Facts → Knowledge → Actions model is the minimal architecture that supports all V1.2 requirements without coupling:

- NarrativeGenerator needs synthesised candidate characteristics, not raw signals → ProfileFeature
- CoachingEngine needs ranked knowledge gaps anchored to candidate characteristics → ProfileFeature
- Replay needs a stable, versioned record of what was known at close time → CandidateProfileSnapshot
- Progress Tracking needs cross-session comparison on a common vocabulary → language-independent ProfileFeature types
- Language independence must be structurally guaranteed → feature taxonomy with no language references

ProfileFeature as the central knowledge unit is the minimal abstraction that satisfies all five requirements simultaneously.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| NarrativeGenerator reads Observations directly | Violates ADR-050. NarrativeGenerator would need to re-implement feature synthesis independently. |
| ProfileFeature includes freshness metadata as a stored field | Freshness is a computed view, not a stored property. Storing it would violate immutability and create TTL-policy coupling. |
| CandidateProfile is persisted directly | CandidateProfile is a live object. Persisting it creates a stale-reference problem and conflates mutable runtime state with immutable history. |
| Feature types are language-specific (`PythonReasoningFeature`) | Prevents cross-language comparison. Requires feature taxonomy changes for every new language. Architecturally unsustainable. |
| Single version for all features (no schema_version) | Prevents safe SessionHistory migration and cross-session comparison when feature schemas evolve. |

## Consequences

### Positive

- Complete decoupling of interpretation (Observation) from characterisation (ProfileFeature) from communication (Narrative/Coaching)
- 11 well-defined feature types with clear Observation mappings enable systematic FeatureEngine implementation
- Versioning strategy prevents silent schema incompatibilities across session history
- Language independence is structurally guaranteed — no new languages require feature taxonomy changes
- All V1.1 assets unchanged — zero regression risk

### Negative / Risks

- 11 feature types require 11 Observation-to-feature mappings in FeatureEngine — implementation scope is significant
- Quality model (confidence, stability, maturity, freshness, consistency, completeness) adds computational overhead per FeatureEngine cycle
- LanguageCapabilityFeature's partial language-context exception requires careful handling in consumers to avoid treating it as a fully language-independent feature

## Implementation Evidence

Architecture only. No production files modified.
Relevant existing assets (unchanged):
- `domain/contracts/reasoning/evidence_signal.py` (frozen)
- `domain/contracts/reasoning/evidence_store.py` (frozen)
- `domain/profile/candidate_profile.py` (`features` field additive per ADR-048; unchanged)

## Review Trigger

- When a new feature type family is introduced requiring a new source layer
- When cross-session feature accumulation is activated (V1.3) and `schema_version` migration is required
- When FeatureEngine computation cost requires quality model simplification
- When a consumer needs a feature type not covered by the V1.2 taxonomy
