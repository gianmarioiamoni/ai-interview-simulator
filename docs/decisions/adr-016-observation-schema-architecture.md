# ADR-016 — Observation Schema & Observation Intelligence Architecture

**Status:** Accepted — V1.2 Architecture (K2 Frozen 2026-07-01)  
**Date:** 2026-07-01  
**Owner:** Domain  
**Preconditions:** ADR-033 (EvidenceSignal), ADR-046 (EvidenceStore), ADR-055 (Observation reservation), ADR-066 (Behavioral Observation migration contract), K0/K1/K2 frozen

---

## Context

V1.1 completed the detection and reasoning pipeline. Ten pattern detectors produce `EvidenceSignal` objects stored in `EvidenceStore`. The `CandidateProfile` accumulates dimensional traces. However, the pipeline stops at the Reasoner — the `CandidateProfile` is built but never consumed downstream.

Three problems prevent V1.2 activation:

1. **No shared interpretation layer.** `EvidenceSignal` is a typed runtime fact (what happened at question N). There is no concept representing the *interpreted meaning* of one or more signals (what it implies about the candidate). NarrativeGenerator and CoachingEngine need interpreted facts, not raw signals.

2. **No temporal lifecycle.** `EvidenceStore` is immutable and append-only but carries no freshness metadata. ADR-039 reserved `EvidenceSource.DERIVED` for freshness weighting; ADR-055 reserved an `Observation` abstraction. Neither was designed. V1.2 requires a concrete design.

3. **No aggregate ownership clarity.** K1 incorrectly placed ObservationStore inside CandidateProfile. K2 corrected this — ObservationStore is an independent Aggregate Root. This ADR freezes that boundary in architecture.

This ADR is the foundational decision for EPIC-02 and unblocks EPIC-01, EPIC-03, EPIC-04, and EPIC-05.

---

## Decision

**Observation is the fundamental interpreted knowledge unit of V1.2.**

The platform introduces three distinct layers with frozen, non-overlapping responsibilities:

```
EvidenceSignal    — runtime evidence (what happened; V1.1 frozen contract)
Observation       — interpreted fact (what it means; NEW in V1.2)
ProfileFeature    — longitudinal knowledge (what the candidate is; V1.2 activation)
```

These three layers form the Observation Intelligence Architecture.

---

## SECTION A — Responsibility Freeze

### EvidenceSignal

**Responsibility:** Runtime atomic evidence. One typed, polarised signal for one dimension at one question index.  
**Ownership:** EvidenceStore (existing, frozen).  
**Mutability:** Immutable (`frozen=True`).  
**Scope:** Single question, single dimension, single source.  
**Language awareness:** None (language-agnostic by design — ADR-033).  
**V1.1 contract:** Frozen. No changes in V1.2. EvidenceSignal schema, EvidenceType catalog, and EvidenceStore contract are **protected assets**.

### Observation

**Responsibility:** Interpreted temporal fact. One typed, named, human-readable summary of one or more EvidenceSignals, representing what was observed about the candidate at a specific moment in the session.  
**Ownership:** ObservationStore (new Aggregate Root).  
**Mutability:** Immutable after creation. Never updated in place.  
**Scope:** One question (or a window of questions for cross-question patterns). Carries question_index and interview_index.  
**Language awareness:** Stores `language_context` (nullable, carries ProgrammingLanguage if the question was a coding question) but does NOT change semantic meaning based on language.

### ProfileFeature

**Responsibility:** Longitudinal derived knowledge. A named, versionable characteristic of the candidate synthesised from one or more Observations by the FeatureEngine.  
**Ownership:** CandidateProfile (the profile aggregate consumes ProfileFeatures only).  
**Mutability:** Immutable per computation cycle; recalculated by FeatureEngine when ObservationStore changes.  
**Scope:** Session-wide (V1.2); cross-session (V1.3+).  
**Language awareness:** None. ProfileFeatures are always language-independent.

---

## SECTION B — Observation Model (Conceptual)

### Purpose

An Observation is a first-class, immutable, typed, timestamped domain object that represents one interpreted fact about a candidate observed during an interview session. It bridges the gap between raw runtime signals (EvidenceSignal) and derived candidate knowledge (ProfileFeature).

### Ownership

ObservationStore — an independent Aggregate Root (K2 amendment A-1). ObservationStore is **not** owned by CandidateProfile.

### Lifecycle

```
Created:   by ObservationExtractor (sole producer) during the reasoning cycle
Stored:    appended to ObservationStore (append-only)
Consumed:  by FeatureEngine (via ObservationStore read interface)
Expired:   by ObservationStore decay function when TTL is exceeded (ADR-021)
Replayed:  read-only from ObservationStore snapshot (never re-created)
```

### Identity

Every Observation has a unique identity composed of:
- `observation_id` — uuid4 assigned at creation; never reused
- `observation_type` — member of ObservationType registry
- `question_index` — the question at which the observation was made
- `interview_index` — session identifier (for future cross-session use)
- `source_signal_ids` — list of EvidenceSignal.id values that produced this Observation

Identity is stable and cannot change after creation.

### Mutability

**Observations are immutable.** This is Domain Invariant I-01 (K1/K2 frozen). No field may change after creation. The `freshness_weight` is a computed property derived from the current clock minus `created_at`; it is never stored in the Observation itself (see Section H).

### Versioning

Observations carry a `schema_version` field (consistent with `EvidenceSignal.schema_version`). FeatureEngine and consumers must handle all stored versions. Version migration is additive only.

### Freshness Metadata

Observations do not store a `freshness_weight` field. Freshness is computed externally by the ObservationStore decay function at query time (ADR-021). The Observation stores only:
- `created_at_question_index` — the question index at creation (proxy for temporal position)
- `interview_index` — session index (future cross-session freshness)

This design preserves immutability while supporting TTL-based freshness without mutating the Observation.

### Temporal Metadata

- `created_at_question_index` — integer; question number within session when this Observation was created
- `interview_index` — integer; session sequence number (starts at 0; always 0 in V1.2 single-session scope)
- `window_size` — integer (nullable); number of questions over which this Observation was derived (1 for single-question observations; N for cross-question pattern observations)

### Language Awareness

- `language_context` — nullable `ProgrammingLanguage`; populated for coding-question observations; null for written/SQL observations
- Language context is stored for audit and replay but **does not change observation semantics**. An observation of type `REASONING_SHALLOW` means the same thing in Python and JavaScript.

### Consumers

- FeatureEngine (primary consumer; reads ObservationStore)
- CalibrationProfile (reads ObservationStore snapshot in aggregate)
- ReplayUpdater (reads frozen ObservationStore snapshot from SessionHistory)

### Producers

- ObservationExtractor — **sole producer**. No other component may create Observations.

### Persistence Policy

- **V1.2:** Observations are session-scoped. They live in memory during the session. A snapshot is stored inside SessionHistory at session close (as an ordered list, not a live ObservationStore).
- **V1.3+:** Cross-session ObservationStore persistence is reserved but not designed here.

### Replay Behaviour

The ObservationStore snapshot stored in SessionHistory enables:
- ReplayUpdater to reconstruct the FeatureEngine input for a past session
- Audit trails (what was observed, in what order, with what freshness at close time)
- Future cross-session feature accumulation (V1.3+)

---

## SECTION C — Observation Taxonomy

The `ObservationType` is a controlled vocabulary of Observation categories. It is a domain registry — not a runtime enum — extended only when a new detector family is introduced and approved by ADR.

### Frozen V1.2 Types

| Category | Types | Source Detectors |
|---|---|---|
| **Technical** | `KNOWLEDGE_DEPTH_HIGH`, `KNOWLEDGE_DEPTH_LOW`, `KNOWLEDGE_GAP_DETECTED`, `REPEATED_STRENGTH`, `REPEATED_WEAKNESS` | EvaluationSignalDetector, ReasoningDepthDetector |
| **Reasoning** | `REASONING_DEEP`, `REASONING_SHALLOW`, `REASONING_IMPROVING`, `REASONING_STAGNATING` | ReasoningDepthDetector |
| **Engineering Judgment** | `ENGINEERING_JUDGMENT_STRONG`, `ENGINEERING_JUDGMENT_WEAK` | EngineeringJudgmentDetector |
| **Communication** | `COMMUNICATION_CLEAR`, `COMMUNICATION_WEAK`, `COMMUNICATION_INCONSISTENT` | CommunicationDetector |
| **Behavioral** | `BEHAVIORAL_GROWTH`, `BEHAVIORAL_INSTABILITY`, `BEHAVIORAL_PLATEAU`, `CROSS_AREA_CONSISTENT`, `CROSS_AREA_CONTRADICTORY` | BehavioralPatternDetector, ConsistencyAcrossInterviewDetector |
| **Confidence** | `CONFIDENCE_WELL_CALIBRATED`, `CONFIDENCE_OVERCONFIDENT`, `CONFIDENCE_UNDERCONFIDENT`, `CONFIDENCE_UNSTABLE` | ConfidenceCalibrationDetector |
| **Leadership** | `LEADERSHIP_STRONG`, `LEADERSHIP_EMERGING`, `LEADERSHIP_ABSENT` | LeadershipDetector (ADR-066) |
| **Collaboration** | `COLLABORATION_STRONG`, `COLLABORATION_EFFECTIVE`, `COLLABORATION_DEFICIT` | CollaborationDetector (ADR-066) |
| **Adaptability** | `ADAPTABILITY_HIGH`, `ADAPTABILITY_MODERATE`, `ADAPTABILITY_LOW` | AdaptabilityDetector (ADR-066) |
| **Language** | `LANGUAGE_IDIOMATIC_USAGE`, `LANGUAGE_TYPE_ERROR_PATTERN`, `LANGUAGE_CONSTRUCT_CONFUSION` | CodingExecutor + EvaluationSignalDetector (language context only) |
| **Coverage** | `AREA_COVERAGE_STRONG`, `AREA_COVERAGE_WEAK`, `AREA_MISSING` | CoverageDetector |
| **Consistency** | `CONSISTENCY_STABLE`, `CONSISTENCY_DRIFT`, `CONTRADICTION_DETECTED` | ConsistencyDetector |
| **Trend** | `TREND_IMPROVING`, `TREND_DECLINING`, `TREND_FLAT` | TrendDetector |

### Future Types (Reserved)

| Category | Intended V1.3+ Use |
|---|---|
| **Progress** | Cross-session improvement signals |
| **Calibration** | Per-session score distribution deviation signals |
| **Learning** | Study-plan-following behaviour (V1.3+) |

### Extension Policy

New ObservationTypes require:
1. A new or amended ADR naming the type, its source detector, and its FeatureEngine consumption mapping.
2. A corresponding entry in the ObservationType registry.
3. Backward-compatible addition (existing stored Observations are unaffected).

No ObservationType may be removed without a deprecation ADR and a migration period.

---

## SECTION D — ObservationStore

### Frozen Design

**ObservationStore is an independent Aggregate Root. It is NOT owned by CandidateProfile.**

| Attribute | Value |
|---|---|
| Ownership | Independent Aggregate Root |
| Sole writer | ObservationExtractor |
| Mutation rules | Append-only. No updates, no manual removals. Expiry is the only removal mechanism. |
| Ordering | Maintained by `created_at_question_index` ascending (deterministic replay) |
| Capacity policy | Maximum capacity is configurable (default: 500 Observations per session). Capacity overflow raises a domain error; it does not silently drop observations. |
| Deduplication | An Observation with the same `(observation_type, question_index, source_signal_ids)` tuple is rejected as a duplicate. Deduplication is the ObservationStore's responsibility. |
| Freshness | ObservationStore computes freshness weights at query time using the decay function (ADR-021). Freshness is a computed view, not a stored field. |
| TTL expiry | Observations beyond configured TTL are excluded from query results but retained in the store for replay (they are marked `expired=True` on snapshot). |
| Replay | At session close, ObservationStore produces an immutable snapshot (ordered list of Observations with final freshness weights computed at close time). This snapshot is stored in SessionHistory. |
| Persistence | Session-scoped in V1.2. Snapshot stored in SessionHistory. |
| Cross-aggregate references | None. ObservationStore does not reference CandidateProfile, Narrative, or SessionHistory. |

### Explicit Statement

> **ObservationStore is NOT owned by CandidateProfile.**  
> CandidateProfile consumes ProfileFeatures only.  
> FeatureEngine reads ObservationStore and writes ProfileFeatures to CandidateProfile.  
> These are three distinct objects with distinct responsibilities.

---

## SECTION E — ObservationExtractor

### Frozen Boundary

ObservationExtractor is the **sole producer** of Observations.

### Responsibility

Transforms one or more `EvidenceSignal` objects from the `EvidenceStore` into one `Observation` object, applying:
- Type mapping (`EvidenceType` → `ObservationType`)
- Normalisation (strength normalisation, polarity consolidation)
- Description generation (human-readable summary of the interpreted fact)
- Identity assignment (uuid4)
- Temporal metadata assignment (question_index, interview_index)
- Language context assignment (nullable)

### What ObservationExtractor NEVER does

| Forbidden action | Reason |
|---|---|
| Creates ProfileFeatures | ProfileFeatures are the FeatureEngine's exclusive responsibility |
| Updates CandidateProfile | CandidateProfile is only updated by FeatureEngine |
| Creates Narrative content | Narrative is NarrativeGenerator's exclusive responsibility |
| Creates CoachingActions | CoachingEngine's exclusive responsibility |
| Calls LLM | ObservationExtractor is a deterministic, pure transformation |
| Reads ObservationStore | ObservationExtractor writes; it never reads back |

### Rationale

Separating extraction (ObservationExtractor) from storage (ObservationStore) from derivation (FeatureEngine) enforces single responsibility at every stage. Each boundary can be tested independently. The extraction logic can evolve (new ObservationTypes, new normalisation rules) without touching FeatureEngine or CandidateProfile.

---

## SECTION F — FeatureEngine Boundary

### Frozen Design

FeatureEngine is the **sole producer of ProfileFeatures**. No other component may write to `CandidateProfile.features`.

| Attribute | Value |
|---|---|
| Input | ObservationStore (read-only) |
| Output | ProfileFeature[] — written exclusively to CandidateProfile.features |
| Composition | Orchestrates one or more Updaters; each Updater handles a specific subset of ObservationTypes |
| Invocation | Per reasoning cycle (same cadence as PatternDetectorPipeline) and at session close |
| Statefulness | Stateless per invocation; reads current ObservationStore; produces current ProfileFeatures |

### Known Updaters (V1.2)

| Updater | Responsibility |
|---|---|
| `ObservationUpdater` | Derives ProfileFeatures from current ObservationStore (primary path) |
| `ReplayUpdater` | Derives ProfileFeatures from a SessionHistory ObservationStore snapshot (replay path) |
| `CalibrationUpdater` | Validates ProfileFeature values against CalibrationProfile; flags deviations |
| `LearningUpdater` | Reserved — derives ProfileFeatures from cross-session learning signals (V1.3+) |

### Invariant

> **FeatureEngine is the ONLY permitted producer of ProfileFeatures.**  
> This invariant may not be violated without a new ADR explicitly superseding ADR-016.

---

## SECTION G — Canonical Runtime Flow

```
Answer submitted
    │
    ▼  [writer: EvaluationEngine]
EvaluationResult
    │
    ▼  [writer: EvaluationSignalWriter]
EvidenceSignal  ──────────────► EvidenceStore (append-only; V1.1 frozen contract)
    │
    ▼  [writer: ObservationExtractor — SOLE OBSERVATION PRODUCER]
Observation  ─────────────────► ObservationStore (append-only; Independent Aggregate Root)
    │
    ▼  [writer: ReasonerService]
ReasonerDecision  (advisory, transient; ADR-030, ADR-035)
    │
    ▼  [writer: PatternDetectorPipeline via ReasonerService]
PatternMatch[]  ──────────────► ReasoningHistory (session-scoped; ADR-041)
    │
    ▼  [writer: FeatureEngine — SOLE PROFILEFEATURE PRODUCER]
ProfileFeature[]  ────────────► CandidateProfile.features (session-scoped)
    │
    ├────────────────────────────────────────────────────────────┐
    ▼  [writer: NarrativeGenerator]                             │
Narrative                                              KnowledgeGapEngine
(NarrativeSections + NarrativeInsights)                (reads EvaluationResults)
Reads: CandidateProfile.features                               │
NEVER reads: ObservationStore, Detectors                       ▼
(ADR-050 boundary)                                    KnowledgeGap[]
    │                                                          │
    │                                              [writer: CoachingEngine]
    │                                              CoachingPlan
    │                                              Reads: KnowledgeGap[] + ProfileFeatures
    │                                              NEVER reads: Detectors, ObservationStore
    │                                              (ADR-067 boundary)
    │                                                          │
    └──────────────────────────┬───────────────────────────────┘
                               ▼  [writer: ReportBuilder]
                          Report (assembled)
                               │
                               ▼  [writer: session completion pipeline]
                          CandidateProfileSnapshot  (point-in-time profile view)
                               │
                               ▼  [writer: session completion pipeline — SOLE WRITER]
                          SessionHistory  (immutable; written once)
                          Stores: ObservationStore snapshot, ProfileFeatures snapshot,
                                  Narrative, CoachingPlan, EvaluationResults, LanguageProfile
                               │
               ┌───────────────┼──────────────────┐
               ▼               ▼                  ▼
          Replay UI      ProgressTracker    CalibrationProfile
         (read-only)     (read-only)        (read-only aggregate)
```

### Validation

| Property | Status |
|---|---|
| Single ownership | ✓ Each stage has exactly one named writer |
| Single writer per aggregate | ✓ EvidenceStore←EvaluationSignalWriter; ObservationStore←ObservationExtractor; CandidateProfile.features←FeatureEngine; SessionHistory←session completion pipeline |
| Immutability | ✓ EvidenceSignal, Observation, SessionHistory, Narrative, CoachingPlan all immutable after creation |
| No upward dependencies | ✓ Nothing in Narrative, Coaching, or SessionHistory writes back to ObservationStore or EvidenceStore |
| No circular dependencies | ✓ The flow is a directed acyclic graph |
| Extension points | ✓ ObservationExtractor: new ObservationTypes without downstream changes; FeatureEngine: new Updaters without CandidateProfile interface changes; CoachingEngine: new ranking strategy via configuration |

---

## SECTION H — Temporal Semantics

### Why Observations Are Immutable

An Observation is a historical fact. It records what was observed at a specific point in the session. Mutating it would destroy the audit trail and break the replay model. All temporal reasoning (freshness, recency weighting) is performed at query time by the ObservationStore, not by mutating the Observation.

### Temporal Fields (Frozen)

| Field | Type | Purpose |
|---|---|---|
| `created_at_question_index` | `int` | Question number when the Observation was created |
| `interview_index` | `int` | Session sequence number (always 0 in V1.2) |
| `window_size` | `int` (nullable) | Number of questions over which the pattern was observed |
| `schema_version` | `str` | Forward-compatible versioning |

### How TTL Operates Without Mutating Observation

1. Each Observation stores `created_at_question_index`.
2. The ObservationStore decay function (ADR-021) computes a freshness weight at query time: `freshness = f(current_question_index - created_at_question_index)`.
3. Observations beyond TTL threshold are excluded from FeatureEngine queries but remain in the store.
4. At session close, the ObservationStore snapshot marks each Observation with a final `freshness_at_close` computed value (this is stored only in the snapshot, not in the live Observation object).

This design means TTL can be changed by configuration without requiring stored Observation migration.

---

## SECTION I — Language Independence

### Frozen Responsibilities

| Concept | Layer | Language-dependent? |
|---|---|---|
| `ProgrammingLanguage` | Domain (abstract concept + registry) | No — the abstraction is language-agnostic |
| `LanguageExecutor` | Infrastructure (execution adapter) | Yes — each language has a concrete executor |
| `language_context` on Observation | Domain (nullable metadata) | Stored but does not change semantics |
| `EvidenceSignal` | Domain (frozen) | No — semantics are language-agnostic (ADR-033) |
| `ProfileFeature` | Domain (derived) | No — features are always language-independent |

### Adding Go, Rust, Java, C# — Observation Layer Impact

| Component | Change required? |
|---|---|
| ObservationType registry | No — existing types cover all language-agnostic patterns |
| Observation schema | No — `language_context` already nullable ProgrammingLanguage |
| ObservationExtractor | No — extraction logic is language-agnostic |
| ObservationStore | No |
| FeatureEngine | No |
| ProfileFeature taxonomy | No |
| LanguageExecutor | ✓ — new concrete executor required |
| LanguagePolicy artifact | ✓ — new policy artifact required |
| Question repository | ✓ — questions in new language required |

**Zero Observation domain redesign required for any new language.**

---

## SECTION J — CandidateProfileSnapshot

### Conceptual Definition

A `CandidateProfileSnapshot` is a point-in-time, immutable copy of `CandidateProfile.features` at session close. It is not a live object; it is a serialisable value object stored inside `SessionHistory`.

### Purpose

| Use case | How snapshot enables it |
|---|---|
| Session replay | ReplayUpdater reads the snapshot to reconstruct the profile view for that session |
| Historical comparison | Two snapshots from different sessions can be compared (Progress Tracking) |
| Progress tracking | LearningProgress is derived from a series of snapshots |
| Version compatibility | Each snapshot carries `schema_version`; consumers handle all versions |

### Why SessionHistory Stores Snapshots (Not Live Objects)

- **Isolation:** The live `CandidateProfile` evolves during a session. SessionHistory must not hold a reference to it — only a frozen copy.
- **Replay correctness:** Replay must reconstruct what the profile looked like at close time, not at replay time.
- **Cross-session comparison:** Comparing two profiles requires two isolated values, not two references into a shared aggregate.
- **Serializability:** A snapshot is a plain value object with no runtime dependencies. A live profile cannot be safely serialised to SQLite without losing behavioural semantics.

---

## SECTION K — Compatibility Analysis

### ADR-039 (Evidence Freshness — Reservation)

**Compatible.** ADR-039 reserved `EvidenceSource.DERIVED` and noted that a freshness weighting mechanism would be designed in V1.2. ADR-016 introduces the Observation layer as the carrier of freshness metadata. The `EvidenceSource.DERIVED` value is activated by ObservationExtractor when it produces a derived Observation from multiple source signals. No EvidenceStore contract changes required.

### ADR-048 (ProfileFeature Abstraction — V1.2 Extension Point)

**Compatible.** ADR-048 reserved `CandidateProfile.features: dict[str, ProfileFeature]` with `default_factory=dict`. ADR-016 confirms that FeatureEngine is the sole writer of this field. The constraint that V1.1 code must not reference `ProfileFeature` is preserved — ADR-016 is an architecture document only; no V1.1 files are modified.

### ADR-050 (NarrativeGenerator Consumes ProfileFeatures, Not Detector Outputs)

**Compatible and strengthened.** ADR-016 adds a second boundary: NarrativeGenerator also must not read ObservationStore. The only profile input to NarrativeGenerator remains `CandidateProfile.features`. ADR-050 is preserved.

### ADR-055 (Observation Abstraction — Reserved for V1.2)

**Supersedes the sketch in ADR-055 for architecture.** ADR-055 showed `Observation → EvidenceSignal → PatternMatch` (signal-then-observation). ADR-016 corrects this to `EvidenceSignal → ObservationExtractor → Observation`. EvidenceSignals pre-exist; Observations are derived from them. The `ObservationType` taxonomy in ADR-016 supersedes the partial list in ADR-055. ADR-055 remains the historical reservation record; ADR-016 is the authoritative design.

### ADR-066 (Behavioral Observation Model — V1.2 Extension Contract)

**Compatible.** ADR-066 defines the V1.2 migration contract: V1.1 Analyzer stat objects become Observation subclasses by adding `description: str`. The `ObservationType` values `LEADERSHIP_STRONG/EMERGING/ABSENT`, `COLLABORATION_STRONG/EFFECTIVE/DEFICIT`, `ADAPTABILITY_HIGH/MODERATE/LOW` are incorporated into the ADR-016 taxonomy. No conflict.

### ADR-067 (Behavioral Coaching Pipeline — Detector-to-CoachingEngine Decoupling)

**Compatible.** ADR-067 freezes the coaching pipeline: `Detector → EvidenceSignal → ProfileFeature → CoachingEngine → CoachingRecommendation`. ADR-016 inserts `Observation` between `EvidenceSignal` and `ProfileFeature`, making the full chain: `Detector → EvidenceSignal → ObservationExtractor → Observation → FeatureEngine → ProfileFeature → CoachingEngine`. The decoupling intent of ADR-067 is preserved and strengthened.

### No Frozen V1.1 Asset Changes Required

The following V1.1 contracts are **unchanged** by ADR-016:

- `EvidenceSignal` (frozen — ADR-033)
- `EvidenceStore` (frozen — ADR-046)
- `EvidenceType` (frozen; additive extension permitted by ADR-016 ObservationType mapping)
- `EvidenceSource` (frozen; `DERIVED` is now activated by ObservationExtractor)
- `CandidateProfile` (V1.1 fields unchanged; `features` field is additive per ADR-048)
- All 10 pattern detectors (no interface changes required)
- `ReasonerService` (no changes required)
- `PatternDetectorPipeline` (no changes required)

---

## SECTION L — ADR Backlog Update

### ADR-016 Status

**Accepted.** This document. Foundational architecture for the Observation Intelligence Layer.

### Addition: Feature Snapshot Strategy (P1)

**Justified.** The `CandidateProfileSnapshot` concept introduced in Section J requires a formal ADR to define:
- The exact fields included in a snapshot (features only, or also dimension_scores?)
- The schema versioning strategy for snapshots
- The snapshot's position in SessionHistory vs. as a standalone persistence artifact
- How ReplayUpdater reconstructs a profile from a snapshot

**Added to backlog as ADR-032 (candidate).**

### Revised ADR Backlog (affected entries only)

| ID | Subject | Priority | Status |
|---|---|---|---|
| ADR-016 | Observation Schema & Observation Intelligence Architecture | P0 | **ACCEPTED** |
| ADR-017 | ObservationStore Lifecycle — Append-Only Contract & Expiry Interface | P0 | Pending (unblocked by ADR-016) |
| ADR-018 | ProfileFeature Schema Freeze & Versioning Policy | P0 | Pending (unblocked by ADR-016) |
| ADR-019 | LanguageConfig Design — ProgrammingLanguage as Abstract Concept | P0 | Pending (parallel) |
| ADR-020 | FeatureEngine Architecture — Orchestrator + Updater Composition | P1 | Pending (unblocked by ADR-016, ADR-018) |
| ADR-021 | Evidence Freshness — TTL Policy, Decay Function Shape, Clock Interface | P1 | Pending (unblocked by ADR-016, ADR-017) |
| ADR-022 | SessionHistory Schema Versioning & Migration Policy | P1 | Pending |
| ADR-023 | NarrativeGenerator Profile-Feature-Aware Prompt Design | P1 | Pending (unblocked by ADR-018) |
| ADR-024 | Calibration Framework CI Gate Design | P1 | Pending |
| ADR-025 | CoachingEngine Ranking Algorithm | P2 | Pending |
| ADR-026 | Replay Snapshot Model | P2 | Pending |
| ADR-027 | LanguageExecutor Abstraction | P2 | Pending |
| ADR-028 | Language Selection Policy | P2 | Pending |
| ADR-029 | Enterprise Extensibility — TenantContext Placeholder | P2 | Pending |
| ADR-030 | StudyRecommendation Resource Library Governance | P3 | Pending |
| ADR-031 | LanguagePolicy Governance | P3 | Pending |
| **ADR-032** | **CandidateProfileSnapshot Strategy** | **P1** | **NEW — Pending** |

---

## Rationale

The three-layer separation (EvidenceSignal / Observation / ProfileFeature) is the minimal architecture that satisfies all V1.2 requirements:

- **NarrativeGenerator** needs interpreted facts, not raw signals → Observation + ProfileFeature
- **CoachingEngine** needs ranked knowledge gaps, not raw signals → ProfileFeature
- **Freshness / TTL** needs a lifecycle layer → ObservationStore with decay
- **Replay** needs immutable temporal records → Observation append-only store
- **Language independence** needs semantics decoupled from execution → language_context as nullable metadata

Collapsing any two layers would re-introduce the coupling problems that K2 identified. Separating all three makes each boundary independently testable, independently evolvable, and independently versionable.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Derive ProfileFeatures directly from EvidenceSignals (skip Observation) | EvidenceSignal has no interpreted description, no decay lifecycle, no cross-signal composition model. Feature derivation would need to re-implement all of these inline, producing a God Object. |
| Store freshness weight inside Observation (mutable field) | Violates Domain Invariant I-01 (immutability). Creates non-deterministic replay and untestable decay logic. |
| Keep ObservationStore inside CandidateProfile | Two distinct aggregates (temporal facts vs. derived profile) would share ownership, creating an ambiguous write boundary. K2 corrected this. |
| Use EvidenceSource.DERIVED directly as the Observation concept | EvidenceSource is a classifier on EvidenceSignal. Overloading it as an Observation carrier would require changing the frozen EvidenceSignal schema — a breaking change to a V1.1 protected asset. |

## Consequences

### Positive

- Complete separation of concerns across the three layers: no component handles more than one responsibility
- All V1.1 assets unchanged — zero regression risk
- New ObservationTypes can be added without touching FeatureEngine or downstream consumers
- Observation immutability enables deterministic replay and audit
- Language independence is structurally guaranteed by design

### Negative / Risks

- ObservationExtractor is a new component requiring its own test suite
- The three-layer translation (EvidenceSignal → Observation → ProfileFeature) adds one pipeline stage compared to a direct derivation approach
- ObservationStore capacity policy (max 500) must be validated against worst-case session sizes before implementation

## Implementation Evidence

Architecture only. No production files modified.  
Relevant existing assets (unchanged):
- `domain/contracts/reasoning/evidence_signal.py` (frozen)
- `domain/contracts/reasoning/evidence_store.py` (frozen)
- `domain/contracts/reasoning/evidence_type.py` (frozen; additive extension reserved)
- `domain/contracts/reasoning/evidence_source.py` (`DERIVED` value now activated)

## Review Trigger

- When ObservationStore capacity policy (500) proves insufficient under production session data
- When cross-session ObservationStore persistence is introduced (V1.3)
- When a new ObservationType family requires a new source layer
