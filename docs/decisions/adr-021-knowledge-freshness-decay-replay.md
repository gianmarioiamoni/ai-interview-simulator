# ADR-021 — Knowledge Freshness, Temporal Decay & Replay Strategy

**Status:** Accepted — V1.2 Architecture (K2 Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Knowledge Construction Layer
**Preconditions:** ADR-016, ADR-016A, ADR-017, ADR-018, ADR-019, ADR-020, K0/K1/K2 frozen
**Supersedes:** ADR-039 reservation (EvidenceSource.DERIVED freshness placeholder — formally superseded by this document)
**Superseded by:** Nothing
**Related:** ADR-022, ADR-023, ADR-025, ADR-026, ADR-032

---

## Context

ADR-016 established that `Observation` is immutable and freshness is computed externally by ObservationStore at query time. ADR-017 froze the ObservationStore lifecycle and reserved the clock interface and freshness metadata structure. ADR-020 confirmed that FeatureEngine receives freshness-weighted Observations from ObservationStore and that confidence computation depends on freshness weighting.

What remained undefined:

- The conceptual freshness model across all five knowledge layers (Evidence, Observation, ProfileFeature, CandidateProfile, SessionHistory)
- The temporal decay stages and what each stage means for knowledge usability
- The TTL philosophy — what TTL does and explicitly does not do
- The complete freshness metadata definition
- The `FeatureCandidate` concept frozen relative to freshness
- The Replay strategy — when to use snapshot vs. recomputation
- The engineering invariants that guarantee freshness never corrupts history

This ADR freezes all of the above. No implementation, no contracts, no code.

---

## Decision

**Freshness belongs to the Knowledge Model. Only knowledge usability changes. Knowledge itself never mutates.**

Freshness is a property of how useful an interpreted fact is for current knowledge construction — not a property of the fact's truth value. An observation made at question 2 remains true at question 12; it is merely less useful for characterising the candidate's current state.

---

## SECTION A — Purpose: Why Freshness Belongs to the Knowledge Model

### The Fundamental Principle

Knowledge has two orthogonal properties:

1. **Truth** — did this happen? Was this observed? This never changes. An `Observation` of `REASONING_DEEP` at question 3 is permanently true. The candidate did demonstrate deep reasoning at question 3.

2. **Usability** — how much should this fact inform our current understanding of the candidate? This changes as the session progresses. By question 12, question-3 evidence may be less representative of the candidate's current state than question-10 evidence.

Freshness governs **usability**, not truth. This distinction is the foundation of the entire freshness model.

### Why Freshness Is a Knowledge Model Concern

Freshness is not an infrastructure concern (it is not about storage cost or cache expiry). It is not an application concern (it is not about UI display logic). It is a **domain concern** because:

1. **Knowledge construction depends on it.** FeatureEngine's confidence computation is directly affected by freshness weighting. Without a formal freshness model, confidence values are undefined.

2. **It must be versioned alongside knowledge.** When replaying a historical session, the freshness model that was active at session time must be honoured — not the current one. Freshness policy is part of the session's knowledge construction contract.

3. **It must not corrupt history.** Freshness decay must never delete observations, never mutate facts, and never affect replay or audit queries. These are domain guarantees, not infrastructure concerns.

### Freshness Across the Five Knowledge Layers

| Layer | What freshness means | Can age? | Deleted by freshness? |
|---|---|---|---|
| `EvidenceSignal` | Not applicable — signals are atomic runtime facts | No | No |
| `Observation` | How representative the interpreted fact is of the candidate's current state | Yes — usability degrades | Never |
| `ProfileFeature` | Inherited from supporting Observations; reflects how current the synthesis is | Yes — confidence affected | Never |
| `CandidateProfile` | How current the overall profile is; derived from current cycle | Yes — recomputed per cycle | N/A — never persisted directly |
| `SessionHistory` | Historical record — freshness is permanently archived at close time | No — frozen at session close | Never |
| `LearningProgress` | Derived at query time from SessionHistory; reflects progress over time | No — derived, not stored | N/A |
| `Replay` | Reads preserved snapshots; TTL does not apply | No — operates on history | Never |

---

## SECTION B — Freshness Model

### Observation Freshness

An Observation's freshness reflects how representative it is of the candidate's current state, relative to the current `question_index` in the session.

**What ages:** The usability weight of an Observation decreases as the session progresses and newer Observations of the same type accumulate.

**What never ages:** The Observation's content, type, timestamp, and source_signal_ids. These are permanent facts.

**What becomes ignored:** Observations beyond their TTL threshold are excluded from FeatureEngine's freshness-filtered query. They become invisible to knowledge construction — but not to replay or audit.

**What remains historically valid:** All Observations, regardless of freshness state, remain valid for:
- Replay (reads all Observations, ignoring TTL)
- Audit (full provenance chain requires all Observations)
- SessionHistory snapshot (captures all Observations at session close, including expired ones, with their TTL state recorded)

### Feature Freshness

A ProfileFeature's freshness is **inherited** — it reflects the aggregate freshness of its `source_observation_ids`.

- A ProfileFeature derived entirely from observations from the first three questions of a twelve-question session has lower freshness than one derived from the last three questions.
- FeatureEngine incorporates freshness weighting when computing confidence: fresher source Observations contribute more to the confidence value.
- A ProfileFeature is never independently expired. It is recomputed from whatever Observations are currently usable.

### CandidateProfile Freshness

`CandidateProfile` is always current — it is the output of the most recent FeatureEngine computation cycle. Its "freshness" is defined by when it was last computed (`computed_at_question_index`). It has no independent TTL.

### Session Freshness

At session close, a snapshot is taken. The snapshot captures the freshness state of all Observations at that moment — recording `freshness_score` for each Observation as a historical fact. After session close, freshness is permanently frozen inside the snapshot. No further decay occurs in SessionHistory.

### LearningProgress Freshness

`LearningProgress` is derived at query time from `SessionHistory[]`. It compares `CandidateProfileSnapshot` records across sessions. Freshness within LearningProgress refers to how recent the most recent session is — a candidate who has not had a new session in six months has a stale LearningProgress. This is a cross-session temporal concern, not an intra-session freshness concern.

---

## SECTION C — Temporal Decay

### Decay Stage Model

```
Observation usability over session time:

Created (question N)
    │
    ▼  [immediately after creation]
Fresh
    │  The Observation was just made. It is highly representative.
    │  FeatureEngine weights it at maximum contribution.
    │
    ▼  [as session progresses; configurable threshold]
Relevant
    │  The Observation is still active in knowledge construction.
    │  Freshness score is above the active threshold.
    │  Full contribution to FeatureEngine confidence.
    │
    ▼  [approaching TTL boundary]
Aging
    │  The Observation's freshness score is declining.
    │  It contributes to FeatureEngine with reduced weight.
    │  NarrativeGenerator may note reduced confidence in associated features.
    │
    ▼  [TTL boundary exceeded]
Stale
    │  The Observation is at the boundary of usability.
    │  FeatureEngine may still include it with minimal weight.
    │  Confidence contribution approaches zero.
    │
    ▼  [beyond TTL threshold — logical expiration]
Ignored
    │  The Observation is excluded from freshness-filtered FeatureEngine queries.
    │  It does NOT contribute to current ProfileFeature computation.
    │  It DOES remain in ObservationStore.
    │  It IS included in Replay and Audit queries.
    │  It IS included in SessionHistory snapshot (marked expired).
```

### What Decay Affects

| Concern | Affected by decay? |
|---|---|
| FeatureEngine confidence computation | **Yes** — fresher Observations weighted higher |
| FeatureEngine query result | **Yes** — Ignored observations excluded from freshness-filtered queries |
| Knowledge construction output | **Yes** — profile reflects only currently usable evidence |
| Coaching priority | **Yes** — stale evidence produces lower-confidence features which affect CoachingEngine ranking |
| NarrativeGenerator confidence signals | **Yes** — low-confidence features may trigger hedged prose |
| Observation content | **No** — never modified |
| Observation existence | **No** — never deleted |
| SessionHistory | **No** — frozen at session close |
| Replay queries | **No** — replay reads all Observations regardless of decay state |
| Audit queries | **No** — audit requires the full historical record |
| FeatureIdentity | **No** — identity is stable; decay does not change what a feature is |
| Provenance | **No** — provenance records are immutable |

### History Is Never Deleted by Freshness

**This is a hard invariant.** Freshness decay is a usability filter, not a deletion policy. The platform does not delete Observations when they expire. Deletion decisions (if any) are a data retention concern and require a separate ADR with explicit justification. Within V1.2, no data is ever deleted by freshness mechanisms.

---

## SECTION D — TTL Policy

### TTL Philosophy

TTL (Time-To-Live) in this platform means: **the maximum distance in question indices after which an Observation is no longer considered usable for current knowledge construction.**

This is explicitly **not** wall-clock TTL. Freshness is session-domain time (question_index), not wall-clock time, because:

1. Sessions vary in duration. A 10-minute session and a 2-hour session at the same question index represent the same amount of interview evidence, regardless of elapsed clock time.
2. Question index is the natural temporal unit for interview knowledge. A reasoning observation at question 3 is "old" relative to question 8 in the same way regardless of real time elapsed.
3. Wall-clock time is infrastructure metadata. Session position is domain metadata. Freshness is a domain concern.

### TTL Invariants

**T-01:** TTL never deletes an Observation. An Observation beyond its TTL is marked `freshness_state = IGNORED` in the freshness metadata record. The Observation itself is unchanged.

**T-02:** TTL never mutates an Observation. The Observation's fields (`observation_type`, `content`, `source_signal_ids`, timestamps) are frozen at creation. TTL affects only the freshness metadata record maintained by ObservationStore.

**T-03:** TTL only determines whether an Observation participates in knowledge construction. An Observation with `freshness_state = IGNORED` is excluded from FeatureEngine's freshness-filtered queries. It is not excluded from replay, audit, or SessionHistory snapshot queries.

**T-04:** Replay ignores TTL. `ReplayUpdater` and the snapshot-based replay path receive the full Observation history, including expired Observations. Replay must reconstruct the knowledge state as it was — not as filtered by current TTL policy.

**T-05:** Audit ignores TTL. The full provenance chain (ProfileFeature → Observation → EvidenceSignal) must be reconstructable from SessionHistory regardless of which Observations were expired at session close.

**T-06:** TTL policy is configurable, not hard-coded. The TTL threshold (in question-index units) is a parameter of the clock interface. Changing TTL policy does not require schema migration or code changes beyond configuration.

**T-07:** TTL policy version is stored in SessionHistory. Replay must honour the TTL policy active at original session time when performing knowledge reconstruction (V1.3+ full replay). In V1.2, replay uses the stored CandidateProfileSnapshot — TTL policy at session time is already encoded in the snapshot's confidence values.

---

## SECTION E — Freshness Metadata

### Conceptual Metadata Definition

Freshness metadata is maintained by ObservationStore for each Observation. It is a separate record — not embedded in the Observation itself (preserving immutability).

| Field | Description | Ownership |
|---|---|---|
| `created_at` | Wall-clock UTC timestamp when the Observation was created | Observation (immutable) |
| `question_index` | Session position when the Observation was created; primary temporal ordering key | Observation (immutable) |
| `interview_index` | Session sequence number for the CandidateIdentity | Observation (immutable) |
| `candidate_identity_id` | The owning candidate (ADR-016A) | Observation (immutable) |
| `freshness_state` | Current usability state: `FRESH` \| `RELEVANT` \| `AGING` \| `STALE` \| `IGNORED` | Freshness metadata record (computed) |
| `freshness_score` | Numeric score [0.0, 1.0] representing current usability; computed from decay function | Freshness metadata record (computed) |
| `logical_expiration` | The question_index at which this Observation transitions to `IGNORED`; derived from TTL policy | Freshness metadata record (computed) |
| `last_consumed_at` | The question_index at which FeatureEngine last included this Observation | Freshness metadata record (updated on read) |
| `freshness_at_close` | Final `freshness_score` recorded at session close; stored in SessionHistory snapshot | Snapshot metadata (immutable after close) |

### Ownership

- The first four fields (`created_at`, `question_index`, `interview_index`, `candidate_identity_id`) are owned by the Observation itself. They are immutable.
- The remaining fields (`freshness_state`, `freshness_score`, `logical_expiration`, `last_consumed_at`) are owned by ObservationStore's freshness layer. They are computed and maintained by ObservationStore, not by the Observation.
- `freshness_at_close` is written once at session close by the session completion pipeline. It is immutable thereafter.

### Decay Function

The decay function maps `(current_question_index - created_at_question_index)` to a `freshness_score`. The shape of the decay function is a policy concern (linear, exponential, step-function, etc.). The shape is defined by TTL policy configuration. This ADR freezes the metadata structure and the principle; the specific decay function shape is a configuration parameter.

---

## SECTION F — FeatureCandidate

### Conceptual Definition

A `FeatureCandidate` is a proposal for knowledge. It is an intermediate object produced by a `FeatureUpdater` and consumed by `FeatureComposer`. It is never persisted. It never becomes a domain fact.

```
Observation[]  (from ObservationStore freshness-filtered query)
    │
    ▼  [FeatureUpdater produces]
FeatureCandidate
    │  A draft feature value with:
    │  - feature_identity
    │  - candidate_value
    │  - candidate_confidence (incorporating freshness weighting)
    │  - source_observation_ids[]
    │  - computed_at_question_index
    │  - updater_id
    │
    ▼  [FeatureComposer resolves]
ProfileFeature  (committed knowledge)
```

### FeatureCandidate Is NOT Knowledge

**This distinction is frozen.**

| Property | FeatureCandidate | ProfileFeature |
|---|---|---|
| Status | Proposal | Knowledge |
| Persistence | Never | Via CandidateProfileSnapshot in SessionHistory |
| Provenance | Carries source_observation_ids for composition | Carries source_observation_ids as permanent record |
| Conflict status | May conflict with other candidates | Resolved — no conflicts |
| Lifecycle | Ephemeral (lives within one FeatureEngine cycle) | Persistent for session duration |
| Consumer | FeatureComposer only | CandidateProfile, NarrativeGenerator, CoachingEngine, ReportBuilder |

### Only FeatureComposer Creates ProfileFeatures

**Frozen invariant:** No component other than `FeatureComposer` (within FeatureEngine) may create `ProfileFeature` objects. `FeatureUpdater` produces `FeatureCandidate` objects — never `ProfileFeature` objects.

This separation ensures:
- Conflict resolution always happens at the composition stage, never within an Updater.
- Provenance is always assembled from all contributing candidates, not from a single Updater's perspective.
- Quality metadata (confidence, stability, maturity) is always computed from the fully composed view, not from a partial candidate.

### Freshness in FeatureCandidate

`FeatureCandidate.candidate_confidence` incorporates freshness weighting from its source Observations. An Updater that produces a candidate from `AGING` Observations assigns a lower `candidate_confidence` than one from `FRESH` Observations. This freshness signal propagates through composition to the final `ProfileFeature.confidence`.

---

## SECTION G — Feature Freshness

### Inheritance Principle

`ProfileFeature` inherits freshness from its `source_observation_ids`. A ProfileFeature is as fresh as the freshness-weighted aggregate of the Observations it was derived from.

### Freshness Affects

**Confidence:** Confidence is the primary channel through which freshness influences ProfileFeature quality. Lower freshness → lower confidence.

**Stability:** A feature computed from a mix of fresh and stale Observations may show lower stability across cycles as stale Observations drop out and fresh ones enter. The transition from stale-inclusive to stale-excluded computation can appear as an instability cycle.

**Recomputation priority:** When FeatureEngine performs incremental recomputation, features whose source Observations are transitioning into `STALE` or `IGNORED` are flagged for priority recomputation. This ensures the profile does not silently degrade without a recomputation cycle.

### Freshness Does NOT Affect

**FeatureIdentity:** Freshness decay never changes what a feature is. A `ReasoningFeature` computed from aging evidence is still a `ReasoningFeature`. Its identity is stable.

**Provenance:** The `source_observation_ids` on a ProfileFeature are never modified by freshness. The provenance record preserves all contributing Observations, including those that are now expired. The audit chain is always complete.

**Feature existence:** A ProfileFeature is not deleted or removed from `CandidateProfile` when its source Observations expire. Its confidence decreases toward zero. FeatureEngine may produce a very low-confidence feature rather than no feature — consumers use their confidence threshold to decide how to handle it.

### Frozen Invariants

**F-01:** Freshness never changes `FeatureIdentity`.

**F-02:** Freshness never modifies provenance records.

**F-03:** A ProfileFeature is never deleted from CandidateProfile due to freshness. Its confidence value reflects freshness degradation.

**F-04:** FeatureComposer always incorporates freshness-weighted confidence from FeatureCandidates. A FeatureCandidate produced from `IGNORED` Observations contributes zero confidence to the composed ProfileFeature.

---

## SECTION H — Replay Strategy

### Decision Tree

```
Replay requested for session S
    │
    ▼
Is a valid CandidateProfileSnapshot available in SessionHistory for session S?
    │
    ├──[YES]──→ Use CandidateProfileSnapshot directly.
    │           No FeatureEngine invocation.
    │           No ObservationStore query.
    │           No TTL filtering.
    │           Replay displays the profile as it was at session close.
    │
    └──[NO]───→ Is this a migration / schema evolution scenario?
                    │
                    ├──[YES]──→ Invoke ReplayUpdater with ObservationStore snapshot.
                    │           ReplayUpdater applies current FeatureEngine schema.
                    │           TTL is IGNORED — all Observations used.
                    │           Produces reconstructed ProfileFeature[].
                    │           Store reconstructed snapshot alongside original metadata.
                    │
                    └──[NO]───→ Report missing snapshot.
                                Do not silently reconstruct.
                                Flag as data integrity issue.
```

### Frozen Replay Principles

**R-01:** Replay must never recompute when a valid snapshot exists. The snapshot is the authoritative record of what the platform knew at session close. Recomputing from Observations would produce a different result if the FeatureEngine schema or TTL policy has changed — this would misrepresent the historical session.

**R-02:** Replay recomputation is reserved for: schema migration, schema evolution, missing snapshots, corrupted snapshots. These are exceptional cases, not operational cases.

**R-03:** When `ReplayUpdater` recomputes, it uses all Observations — TTL is ignored. The reconstruction must reflect the full evidence, not the evidence that was "fresh" at some arbitrary point in time.

**R-04:** A reconstructed profile (from `ReplayUpdater`) is stored as a separate artefact alongside the original snapshot. It does not replace or modify the original snapshot.

**R-05:** In V1.2, the snapshot-based replay path is the only operational path. `ReplayUpdater` full activation is V1.3+.

### Rationale

The preference for snapshot over recomputation is rooted in the principle that **SessionHistory is the authoritative historical record, not a reconstruction input**. If the platform's understanding of the candidate at session close was X, then replaying that session should show X — not a recomputation of X under today's schema.

Recomputation is a reconciliation tool, not a display tool.

---

## SECTION I — Current CandidateProfile Relationship

### Three Distinct Objects

| Object | Mutability | Persistence | Temporal scope |
|---|---|---|---|
| `Current CandidateProfile` | Mutable — updated by FeatureEngine per cycle | Never persisted directly | Live session |
| `CandidateProfileSnapshot` | Immutable after creation | Persisted in SessionHistory | Session close point-in-time |
| `LearningProgress` | N/A — derived, not stored | Never persisted | Cross-session derived view |

### Frozen Invariants

**C-01:** `Current CandidateProfile` may evolve. FeatureEngine updates it on every computation cycle. It reflects the current best understanding of the candidate.

**C-02:** `CandidateProfileSnapshot` never evolves. Once created at session close, it is a permanent, immutable record. No process may modify a stored snapshot.

**C-03:** `LearningProgress` always derives from `SessionHistory`. It is computed at query time from the set of `CandidateProfileSnapshot` records in `SessionHistory[]` for a given `CandidateIdentity`. It never derives from `Current CandidateProfile`.

**Rationale for C-03:** Deriving `LearningProgress` from the current session's `CandidateProfile` would conflate an in-progress, potentially incomplete view with the historical record. Progress is measured between completed sessions — not between the last snapshot and the current live state.

**C-04:** `CandidateProfile` is replaceable. Given the same `ObservationStore` state, FeatureEngine produces the same profile. If the live profile is lost (process crash, restart), full recomputation from `ObservationStore` restores it.

**C-05:** The live `CandidateProfile` is never written to `SessionHistory` directly. Only `CandidateProfileSnapshot` (an immutable point-in-time capture) is persisted.

---

## SECTION J — Runtime Behaviour

### Canonical Runtime with Freshness

```
ObservationStore
    │  [all Observations for this session; ordered by question_index]
    │
    ▼  [Freshness Filter — applied by ObservationStore at query time]
    │  Evaluates freshness_score per Observation using decay function.
    │  Excludes Observations with freshness_state = IGNORED.
    │  Passes Active, Referenced, Aging, Stale Observations (with their scores).
    │
    ▼  [FeatureEngine pull — receives freshness-weighted Observation[]]
FeatureEngine
    │
    ├──→ ObservationUpdater → FeatureCandidate[]
    │    (freshness_score propagated into candidate_confidence)
    │
    ├──→ CalibrationUpdater → validation flags
    │
    └──→ [other registered Updaters]
    │
    ▼  [FeatureComposer]
    │  Resolves conflicts; computes final confidence, stability, maturity.
    │
    ▼  [Commit]
Current CandidateProfile (ProfileFeature[]; confidence reflects freshness)
    │
    ▼  [session close — session completion pipeline]
CandidateProfileSnapshot
    │  Records freshness_at_close for each source Observation in provenance.
    │  Immutable after creation.
    │
    ▼  [single writer: session completion pipeline]
SessionHistory (write-once; immutable)
```

### Replay Path (bypasses Freshness Filter)

```
SessionHistory
    │  [CandidateProfileSnapshot available]
    │
    ▼  [Replay — reads snapshot directly]
CandidateProfileSnapshot
    │  No FeatureEngine invocation.
    │  No ObservationStore query.
    │  No Freshness Filter.
    │
    ▼
Replay display (profile as it was at session close)
```

### Runtime Invariants

| Invariant | Status |
|---|---|
| Freshness Filter is applied by ObservationStore, not by FeatureEngine | ✓ — ObservationStore is responsible for freshness evaluation; FeatureEngine receives pre-filtered results |
| Replay bypasses the Freshness Filter | ✓ — replay reads snapshot or full Observation history; TTL not applied |
| Current CandidateProfile always reflects freshness-weighted evidence | ✓ — FeatureEngine receives freshness-scored Observations |
| SessionHistory is never affected by freshness | ✓ — write-once after session close; freshness state is archived, not active |
| FeatureCandidate is ephemeral | ✓ — not written to any store; lives within one FeatureEngine cycle |

---

## SECTION K — Language Independence

### Freshness Is Language-Independent

Freshness decay is a function of session time (question_index delta) and nothing else. It does not depend on:

- `ProgrammingLanguage` — a Python Observation and a Java Observation at the same `question_index` age identically.
- `LanguageFamily` — Dynamic-family and JVM-family Observations follow the same decay function.
- `ObservationType` — all Observation types age at the same rate under a given TTL policy (V1.2 default). Type-specific TTL policies are reserved for V1.3+ if evidence warrants differential decay rates.

### Language Only Affects Observation Metadata

`language_context` on an Observation is stored as metadata. The freshness computation accesses only `question_index` and `created_at` — neither of which is language-dependent.

### Frozen Invariants

**L-01:** Freshness must never depend on `ProgrammingLanguage`.

**L-02:** Freshness must never depend on `LanguageFamily`.

**L-03:** TTL policy is uniform across all `ObservationType` values in V1.2. Differential TTL (per type) is reserved and requires a separate ADR.

**L-04:** Knowledge freshness remains universal. A fresh `ReasoningFeature` derived from Python Observations and a fresh `ReasoningFeature` derived from Java Observations have the same freshness semantics.

---

## SECTION L — Future Compatibility

### ADR-022 (SessionHistory Schema Versioning & Migration Policy)

**Directly informed.** The freshness metadata `freshness_at_close` is stored per-Observation in the `CandidateProfileSnapshot`. ADR-022 must account for this field when designing the snapshot schema and versioning strategy. The `ttl_policy_version` field (recording which TTL policy was active at session time) must also be preserved for future replay fidelity.

### ADR-023 (NarrativeGenerator Profile-Feature-Aware Prompt Design)

**Compatible.** NarrativeGenerator reads `CandidateProfile.features`. Confidence values on ProfileFeatures already encode freshness. NarrativeGenerator does not need to know about TTL or decay functions — it uses confidence as its quality signal. Low-confidence features (produced from stale evidence) may trigger hedged prose per NarrativeGenerator's threshold policy.

### ADR-025 (CoachingEngine Ranking Algorithm)

**Compatible.** CoachingEngine reads `KnowledgeGap[]` + `CandidateProfile.features`. Feature confidence (which encodes freshness) feeds into the gap severity × IRS impact formula. ADR-025 may use confidence as a ranking input without needing to know about freshness internals.

### ADR-026 (Replay Snapshot Model)

**Directly informed.** Section H defines the replay decision tree. ADR-026 governs the full snapshot model; it must implement the R-01 through R-05 principles frozen here.

### ADR-032 (CandidateProfileSnapshot Strategy)

**Directly informed.** The snapshot must capture `freshness_at_close` per source Observation in the provenance records. ADR-032 must specify the snapshot fields that encode this freshness state.

### Knowledge Graph (V2 candidate)

**Compatible.** A knowledge graph edge between ProfileFeature and Observation would carry `freshness_at_close` as a temporal weight. The freshness model defined here is graph-compatible without redesign.

### Calibration

**Directly informed.** The calibration framework (ADR-024) must account for freshness when comparing feature confidence distributions. A session late in the question sequence produces different freshness profiles than one early — calibration baselines must be freshness-aware.

### Future Adaptive Freshness

V1.3+ may introduce adaptive TTL — per-ObservationType TTL values based on empirical evidence of how quickly different evidence types become unrepresentative. This is a configuration extension: the `ttl_policy_version` field and the decay function interface are designed to support this without schema changes.

### V1.1 Compatibility

**Confirmed. No frozen V1.1 asset requires change.**

| V1.1 Asset | Status |
|---|---|
| `EvidenceSignal` schema | Protected. Unchanged. Freshness is an Observation-layer concern. |
| `EvidenceStore` contract | Protected. Unchanged. |
| `CandidateProfile` V1.1 fields | Protected. Unchanged. |
| Pattern detectors (10 existing) | Protected. Unchanged. |
| `ReasonerService` | Protected. Unchanged. |
| `EvaluationEngine` | Protected. Unchanged. |

---

## SECTION M — Engineering Invariants

The following invariants are frozen and permanent. They govern the entire freshness and temporal model of the platform.

| Invariant | Statement |
|---|---|
| **M-01** | `Observation` never mutates. All fields are frozen at creation. Freshness is a property of ObservationStore's metadata layer, not of the Observation itself. |
| **M-02** | Knowledge usability changes; knowledge truth does not. Freshness affects whether an Observation participates in current knowledge construction — not whether the Observation represents a true historical fact. |
| **M-03** | History is immutable. `SessionHistory`, `CandidateProfileSnapshot`, and all Observation records in SessionHistory are write-once. No freshness mechanism may alter them. |
| **M-04** | Replay preserves history. Replay reads what was recorded — not what would be computed today. Snapshots are preferred. Recomputation is an exceptional recovery path. |
| **M-05** | Snapshots are preferred over recomputation. When a valid `CandidateProfileSnapshot` exists, replay uses it directly. Recomputation is reserved for migration, schema evolution, and data recovery. |
| **M-06** | `FeatureIdentity` never changes. Freshness decay does not change what a feature is, only how confidently it is known. A `ReasoningFeature` computed from stale evidence is still a `ReasoningFeature`. |
| **M-07** | `FeatureCandidate` never becomes persistent. It is an ephemeral intermediate object produced by FeatureUpdater and consumed by FeatureComposer within a single FeatureEngine cycle. It is never written to any store. |
| **M-08** | Freshness never deletes data. No Observation, EvidenceSignal, ProfileFeature, or SessionHistory record is deleted by freshness mechanisms. The `IGNORED` state means "excluded from current knowledge construction" — not "deleted". |
| **M-09** | TTL policy is versioned and stored with the session. `SessionHistory` records the `ttl_policy_version` active at session time. This enables future replay to understand the freshness contract that governed the original session. |
| **M-10** | `LearningProgress` derives from `SessionHistory`, never from `Current CandidateProfile`. Progress is a cross-session, historical view — not a comparison between the historical record and the current in-progress session. |

---

## SECTION N — ADR Backlog Update

### ADR-021 Status

**Accepted.** This document. Knowledge Freshness model, Temporal Decay, TTL Philosophy, and Replay Strategy frozen.

### Updated Backlog

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-021 | Knowledge Freshness, Temporal Decay & Replay Strategy | NEXT MILESTONE (P0) | **ACCEPTED** |
| ADR-022 | SessionHistory Schema Versioning & Migration Policy | P1 — requires ADR-016A (done) | **NEXT MILESTONE — P1** |
| ADR-023 | NarrativeGenerator Profile-Feature-Aware Prompt Design | UNBLOCKED | Unchanged — P1; parallel |
| ADR-025 | CoachingEngine Ranking Algorithm | UNBLOCKED | Unchanged — P2; parallel |
| ADR-026 | Replay Snapshot Model | P2 — requires ADR-022 | Unchanged — requires ADR-022 |
| ADR-032 | CandidateProfileSnapshot Strategy | P1 — requires ADR-022 | Unchanged — requires ADR-022 |

### ADR-022 as Next Milestone

**ADR-022 (SessionHistory Schema Versioning & Migration Policy)** is the next milestone.

Rationale:
- All persistence-layer decisions (CandidateProfileSnapshot, Observation snapshot, freshness_at_close fields, ttl_policy_version) are now fully defined by ADR-016 through ADR-021.
- ADR-022 is the last P1 architecture decision before EPIC-01 and EPIC-09 persistence work can begin.
- ADR-026 (Replay Snapshot Model) and ADR-032 (CandidateProfileSnapshot Strategy) both depend on ADR-022.

### Remaining Roadmap

```
ADR-021 ACCEPTED (this document)
    │
    ├──→ ADR-022 (SessionHistory Schema Versioning) — NEXT MILESTONE; P1
    │
    ├──→ ADR-023 (NarrativeGenerator Design) — P1; parallel; unblocked
    │
    ├──→ ADR-025 (CoachingEngine Ranking) — P2; parallel; unblocked
    │
    └──→ ADR-024 (Calibration CI Gate) — P1; parallel; informed by ADR-021
```

After ADR-022:
- ADR-026 (Replay Snapshot Model) — unblocked
- ADR-032 (CandidateProfileSnapshot Strategy) — unblocked

---

## SECTION O — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ Knowledge Freshness model frozen | **FROZEN** — Section A/B: freshness across all 5 knowledge layers; truth vs. usability distinction |
| ✓ Temporal decay frozen | **FROZEN** — Section C: 5 decay stages (Fresh → Relevant → Aging → Stale → Ignored); decay impact table |
| ✓ TTL philosophy frozen | **FROZEN** — Section D: 7 TTL invariants (T-01 through T-07); session-domain time (question_index), not wall-clock |
| ✓ Freshness metadata frozen | **FROZEN** — Section E: 8 metadata fields with ownership; decay function principle |
| ✓ FeatureCandidate concept frozen | **FROZEN** — Section F: proposal vs. knowledge distinction; FeatureComposer as sole ProfileFeature creator; freshness propagation |
| ✓ Feature freshness frozen | **FROZEN** — Section G: inheritance principle; 4 invariants (F-01 through F-04); confidence as primary freshness channel |
| ✓ Replay strategy frozen | **FROZEN** — Section H: snapshot preference; 5 replay principles (R-01 through R-05); recomputation as exceptional path |
| ✓ CandidateProfile relationship frozen | **FROZEN** — Section I: 5 invariants (C-01 through C-05); three-object distinction (Current / Snapshot / LearningProgress) |
| ✓ Runtime validated | **VALIDATED** — Section J: freshness-aware live path; replay bypass path; 5 runtime invariants |
| ✓ Language independence confirmed | **CONFIRMED** — Section K: 4 invariants (L-01 through L-04); freshness is language-agnostic |
| ✓ Engineering invariants confirmed | **CONFIRMED** — Section M: 10 invariants (M-01 through M-10) |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section L: no frozen V1.1 asset requires change |

---

## Final Recommendation

**ADR-021 is ACCEPTED.**

The Knowledge Freshness model is frozen. Temporal decay stages, TTL philosophy, freshness metadata, `FeatureCandidate` distinction, replay strategy, and all engineering invariants are permanently defined.

**Immediate next action: ADR-022 (SessionHistory Schema Versioning & Migration Policy).** ADR-022 is the last architecture decision needed before persistence implementation can begin.

---

## Rationale

Freshness as a usability property (not a truth property) is the minimal model that satisfies all V1.2 requirements:

- **Knowledge quality** requires that FeatureEngine weight recent evidence more heavily — freshness scores enable this without mutating Observations.
- **Replay fidelity** requires that the historical record is never altered by freshness — snapshot preference and TTL bypass in replay enforce this.
- **Audit completeness** requires that all evidence is traceable regardless of expiry state — the `IGNORED` state hides Observations from FeatureEngine but preserves them for audit.
- **Determinism** requires that freshness is a function of session position (question_index), not wall-clock time — enabling deterministic replay without real-time dependency.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Wall-clock TTL (seconds since creation) | Non-deterministic replay; sessions of different durations would produce incomparable freshness; not a domain-meaningful unit |
| Storing freshness_score inside Observation | Violates immutability (ADR-016 Domain Invariant I-01); creates non-deterministic replay |
| Deleting expired Observations | Destroys audit trail; prevents replay; violates M-08 |
| Rebuilding profile from Observations for all replay | Produces different results if schema has evolved; misrepresents history; violates R-01 |
| Type-specific TTL in V1.2 | Premature complexity; insufficient empirical basis; reserved for V1.3+ with ADR |

## Consequences

### Positive

- Complete freshness model with no data loss guarantees
- Deterministic, question-index-based decay enables deterministic replay
- Snapshot-preference replay is always fast and correct for standard cases
- `FeatureCandidate` clarity prevents accidental persistence of draft knowledge
- All V1.1 assets unchanged — zero regression risk

### Negative / Risks

- `freshness_at_close` per-Observation in CandidateProfileSnapshot adds storage overhead; acceptable given 500-Observation cap per session (ADR-016)
- TTL policy version management (T-07) adds bookkeeping to SessionHistory schema — ADR-022 must accommodate
- `FeatureMergePolicy` and `FeatureReplacementPolicy` must handle zero-confidence candidates (from fully expired source Observations) without producing NaN or undefined confidence values

## Implementation Evidence

Architecture only. No production files modified.
ADR-039 (EvidenceSource.DERIVED reservation) formally superseded by this document.
Relevant existing assets (unchanged):
- `domain/contracts/reasoning/evidence_signal.py` (frozen)
- `domain/contracts/reasoning/evidence_store.py` (frozen)
- `domain/profile/candidate_profile.py` (unchanged)
