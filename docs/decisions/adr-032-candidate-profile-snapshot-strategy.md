# ADR-032 — CandidateProfileSnapshot Strategy

**Status:** Accepted — V1.2 Architecture (Snapshot Layer Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Snapshot Layer
**Preconditions:** ADR-016, ADR-016A, ADR-017, ADR-018, ADR-019, ADR-020, ADR-021, ADR-022, ADR-025
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-022, ADR-026, ADR-021, ADR-020, ADR-018

---

## Context

ADR-022 froze `SessionHistory` as the platform's historical memory and established that `CandidateProfileSnapshot` is an immutable point-in-time capture of `CandidateProfile.features` at session close, stored inside `KnowledgeSnapshot`.

What remained undefined:

- Why `CandidateProfileSnapshot` is not simply a serialized `CandidateProfile`
- The precise ownership and relationship between all five objects in the knowledge hierarchy
- The seven canonical snapshot principles and what each means in domain terms
- The complete conceptual contents of a snapshot — what it must contain and why
- The creation policy — who creates it, when, and under what lifecycle rules
- The engineering invariants that prevent any component from misusing or recreating snapshots

This ADR freezes all of the above. No implementation, no contracts, no code.

---

## Decision

**`CandidateProfileSnapshot` is a certified historical knowledge state — not a serialized runtime object.**

A serialized `CandidateProfile` is an operational snapshot of a mutable object. A `CandidateProfileSnapshot` is a permanent, certified record of what the platform knew about a candidate at the exact moment of session close — a knowledge artifact with its own identity, provenance, and completeness guarantees.

---

## SECTION A1 — Purpose: Why CandidateProfileSnapshot Is Not a Serialized CandidateProfile

### The Core Distinction

`CandidateProfile` is a **live domain aggregate** — it changes with each FeatureEngine cycle, reflects the current accumulation of Observations, and is session-resident. It is never persisted directly. It exists only to serve the active pipeline.

`CandidateProfileSnapshot` is a **certified historical knowledge state**. It is:

1. **Not a cache.** A cache can be evicted and recomputed. A snapshot is permanent and authoritative.

2. **Not a serialization.** Serialization captures object state at a point in time. A snapshot captures certified knowledge state — including provenance, quality, policy context, and generation metadata.

3. **Not recomputable as equivalent.** If the same Observations are fed to a newer FeatureEngine, the result is a different profile — semantically and computationally distinct. The snapshot is the result of the exact FeatureEngine version, TTL policy, and language policy that governed the session.

4. **A freeze of responsibility.** The snapshot certifies: "This is what FeatureEngine concluded, under these policies, at this moment." No subsequent event — schema evolution, TTL change, new observations — can alter that conclusion.

### Freeze Responsibilities

| Responsibility | `CandidateProfile` | `CandidateProfileSnapshot` |
|---|---|---|
| Mutability | Mutable per FeatureEngine cycle | Immutable after session close |
| Persistence | Never | Always (inside KnowledgeSnapshot) |
| Consumer | Active pipeline (Narrative, Coaching, Report) | Replay, LearningProgress, Calibration, Audit |
| Recomputability | Always recomputable | Self-contained; recomputation is exceptional |
| Policy binding | Reflects current active policies | Binds the policies at time of creation |
| Knowledge authority | Current best estimate | Permanent certified conclusion |

---

## SECTION A2 — Relationship

### Ownership Chain

```
CandidateIdentity          (root owner — ADR-016A)
    │
    └──→ SessionHistory[]  (one per completed session; write-once)
              │
              └──→ KnowledgeSnapshot      (self-contained session closure artefact — ADR-022)
                        │
                        ├──→ CandidateProfileSnapshot   (THIS ADR)
                        ├──→ ObservationStoreSnapshot
                        ├──→ Narrative
                        ├──→ CoachingPlan
                        └──→ Policy Versions + Engine Versions
```

### Five-Object Responsibility Freeze

| Object | Responsibility | Mutable? | Persisted? | Writer |
|---|---|---|---|---|
| `Current CandidateProfile` | Live knowledge state for the active session; updated per FeatureEngine cycle | Yes | No — session-resident | FeatureEngine (sole) |
| `CandidateProfileSnapshot` | Point-in-time certified knowledge state at session close | No | Yes — inside KnowledgeSnapshot | FeatureEngine final cycle (sole) |
| `KnowledgeSnapshot` | Self-contained closure artefact: snapshot + narrative + coaching + all policy versions | No | Yes — inside SessionHistory | Session completion pipeline (sole) |
| `SessionHistory` | Complete historical memory of one completed session | No | Yes — durable, write-once | Session completion pipeline (sole) |
| `LearningProgress` | Cross-session derived view computed at query time from SessionHistory[] | N/A | No — derived, never stored | Derived at query time; no persistent writer |

### Ownership Invariants

- `CandidateIdentity` owns all persistent knowledge. No `SessionHistory`, `KnowledgeSnapshot`, or `CandidateProfileSnapshot` exists without an owning `CandidateIdentity`.
- `CandidateProfileSnapshot` is always owned by exactly one `KnowledgeSnapshot`.
- `KnowledgeSnapshot` is always owned by exactly one `SessionHistory`.
- `LearningProgress` is derived from `SessionHistory[]`; it has no independent owner and no independent persistence.

---

## SECTION A3 — Snapshot Principles

### Seven Canonical Principles

**1. Immutable**

Once created at session close, no field in `CandidateProfileSnapshot` may be updated, patched, or extended. The snapshot is an artifact of record. Any post-session analysis that produces a different profile must create a new artifact alongside the original — never modifying the original.

*Why this matters:* LearningProgress comparisons, audit trails, and replay fidelity all depend on the guarantee that the historical snapshot reflects exactly what was known at session close — not what would be known today.

**2. Complete**

`CandidateProfileSnapshot` must contain the full set of `ProfileFeature[]` values that `CandidateProfile` held at session close. No ProfileFeature may be omitted, summarized, or projected. Partial snapshots are not valid snapshots.

*Why this matters:* Replay must be able to reconstruct the full profile display without invoking FeatureEngine. Calibration must be able to examine every feature without live pipeline access.

**3. Self-consistent**

All ProfileFeature values in the snapshot must have been produced by the same FeatureEngine cycle — the final cycle of the session. There must be no feature value from an earlier cycle mixed with values from the final cycle.

*Why this matters:* A snapshot that mixes values from different computation cycles is internally inconsistent. Cross-feature correlations (used in LearningProgress analysis) would be meaningless.

**4. Deterministic**

Given the same `ObservationStore` state and the same FeatureEngine version, the snapshot must always produce the same set of ProfileFeature values. There must be no random element, timestamp dependency, or external query in the snapshot creation logic.

*Why this matters:* Audit, calibration, and replay are only meaningful if the snapshot can be verified against its inputs. Non-deterministic snapshots cannot be verified.

**5. Versioned**

`CandidateProfileSnapshot` must carry the `feature_engine_version` and `profile_schema_version` that governed its creation. These versions are embedded in `KnowledgeSnapshot` (ADR-022) and are inseparable from the snapshot.

*Why this matters:* Schema evolution is inevitable. Future consumers must know which version of the ProfileFeature schema to apply when interpreting the snapshot — not guess it.

**6. Auditable**

Every ProfileFeature in the snapshot must include `source_observation_ids` — the full provenance chain back to the Observations that produced it. The corresponding `ObservationStoreSnapshot` (also in `KnowledgeSnapshot`) provides the Observation records referenced by this provenance.

*Why this matters:* Candidates, operators, and calibration tooling must be able to trace every profile conclusion back to specific observed behaviours. Unauditable profiles are opaque and cannot be challenged or corrected.

**7. Self-contained**

`CandidateProfileSnapshot`, together with the `KnowledgeSnapshot` that contains it, must be sufficient to reproduce the complete profile view without any live pipeline invocation — no FeatureEngine query, no ObservationStore query, no NarrativeGenerator call.

*Why this matters:* Session data may outlive the platform version that produced it. Replay must remain functional as the platform evolves. Self-containment is the guarantee that historical data never becomes orphaned.

---

## SECTION A4 — Snapshot Contents

### Conceptual Contents

`CandidateProfileSnapshot` contains the following conceptual components. No implementation is defined here.

**ProfileFeatures**
The complete set of `ProfileFeature[]` values from the final FeatureEngine cycle. Indexed by `FeatureIdentity` (ADR-020) as the stable cross-session key. No ProfileFeature is excluded.

**Feature Provenance**
For each ProfileFeature: `source_observation_ids[]` — the ordered list of Observation identifiers that contributed to this feature value. Provenance is complete: every feature can be traced back to its source Observations.

**Confidence**
For each ProfileFeature: the confidence value computed by FeatureEngine at the final cycle. Confidence reflects the combined freshness, evidence weight, and stability of supporting Observations (ADR-021). Confidence is a property of the snapshot, not a derivative of it.

**Stability**
For each ProfileFeature: a stability indicator reflecting how consistent the feature value has been across the session's FeatureEngine cycles. Stability distinguishes a feature that was consistently demonstrated from one that fluctuated.

**Maturity**
For each ProfileFeature: a maturity indicator reflecting how many qualifying Observations contributed to the feature value. A feature with a single supporting Observation is less mature than one supported by five qualifying Observations.

**Knowledge Quality**
Aggregate quality metadata for the snapshot as a whole: total Observations that contributed, proportion of ACTIVE vs. DECAYED Observations at snapshot time, overall confidence distribution.

**Language Profile**
The `LanguageProfile` active at session close — the language(s) assessed, per-language feature partitions (if applicable), and per-language evidence distribution.

**Quality Metadata**
Per-feature quality indicators: evidence count, freshness-at-close values for contributing Observations, whether any feature was produced from a single evidence source (low-confidence flag).

**Reserved Future Metadata**
A reserved `metadata` dict for future additive fields. Populated at creation time. Not modified after creation. Consumers must ignore unknown keys for forward compatibility.

---

## SECTION A5 — Snapshot Creation Policy

### Exactly One Creator

`FeatureEngine` is the sole creator of `CandidateProfileSnapshot`. No other component — not the session completion pipeline, not NarrativeGenerator, not CoachingEngine, not Replay — may create or synthesize a `CandidateProfileSnapshot`.

The session completion pipeline invokes FeatureEngine's final cycle and receives the resulting `CandidateProfileSnapshot`. It does not assemble or modify it.

### Created Once at Session Completion

`CandidateProfileSnapshot` is created exactly once — at session close, during the final FeatureEngine cycle. This is not the last cycle of the interview loop; it is a dedicated closure invocation that:

1. Applies the final TTL policy state
2. Computes the final freshness weights
3. Executes the final feature computation
4. Emits the `CandidateProfileSnapshot` with full provenance and quality metadata

No intermediate FeatureEngine cycle during the live session produces a `CandidateProfileSnapshot`. Those cycles produce `ProfileFeature[]` updates to `CandidateProfile`. The snapshot is not accumulated over the session; it is computed once, from the full Observation history, at close.

### Never Modified

After creation, `CandidateProfileSnapshot` is handed to the session completion pipeline, which embeds it in `KnowledgeSnapshot` and persists it in `SessionHistory`. At that point, the snapshot is immutable. No component may:

- Update any ProfileFeature value
- Add a ProfileFeature not present at creation
- Remove a ProfileFeature present at creation
- Update confidence, stability, maturity, or provenance values

### Never Regenerated During Normal Execution

`CandidateProfileSnapshot` is never regenerated as part of normal platform execution (replay, progress tracking, coaching plan generation, calibration). These consumers read the stored snapshot; they do not invoke FeatureEngine.

The only scenario in which a new snapshot is generated from existing session data is **explicit migration or recovery** — triggered by a human operator, logged, and stored as a new artifact alongside the original (ADR-022 invariant MS-02 through MS-05).

### Lifecycle

```
Interview Session (live)
    │
    │  [FeatureEngine cycles — produce CandidateProfile updates only]
    │
    ▼
Session Close Event
    │
    ▼  [sole creator: FeatureEngine — final closure cycle]
CandidateProfileSnapshot
    │  (complete, certified, versioned, auditable)
    │
    ▼  [assembled by: session completion pipeline]
KnowledgeSnapshot
    │
    ▼  [written by: session completion pipeline — once]
SessionHistory
    │
    ├──→ Replay (reads snapshot; never recomputes for standard replay)
    ├──→ LearningProgress (reads across SessionHistory[]; never stored)
    └──→ Calibration (reads aggregate; never writes back)
```

---

## SECTION A6 — Engineering Invariants

### Invariant EI-01: Snapshot Never Changes

A stored `CandidateProfileSnapshot` is permanently equal to its state at creation. No post-creation operation — schema migration, reanalysis, pipeline upgrade — may alter a stored snapshot. All consumers operate on the stored form.

### Invariant EI-02: Snapshot Never Recomputes

Standard replay, progress tracking, and coaching plan generation never invoke FeatureEngine to reconstruct a snapshot. The stored snapshot is authoritative. FeatureEngine is invoked only for live session knowledge construction and explicit migration/recovery.

### Invariant EI-03: Snapshot Never References Live Runtime Objects

`CandidateProfileSnapshot` contains no reference to:
- Live `ObservationStore` (it carries `source_observation_ids`, not live references)
- Live `CandidateProfile` (it is a copy of the final feature state, not a pointer)
- Any session-resident pipeline component

The snapshot is fully self-referential within the `KnowledgeSnapshot` boundary.

### Invariant EI-04: Snapshot Contains Only Immutable Knowledge

Every value in `CandidateProfileSnapshot` — ProfileFeature values, confidence, stability, maturity, provenance IDs — was computed and frozen at session close. There are no computed-on-read fields, no lazy properties, and no fields that change between reads.

---

## SECTION B — Knowledge Quality Model

### Quality Hierarchy

Knowledge quality in `CandidateProfileSnapshot` is expressed at three levels:

**Feature-level quality:** confidence + stability + maturity per ProfileFeature. Reflects the evidence quality for that specific capability domain.

**Snapshot-level quality:** aggregate quality metadata across all features. Reflects the overall reliability of the session's knowledge conclusions.

**Provenance-level quality:** `source_observation_ids` per feature. Enables external audit of any quality claim.

### Quality Is Preserved, Not Reinterpreted

When replay or LearningProgress accesses `CandidateProfileSnapshot`, the quality values are read as recorded. No consumer reinterprets, recalibrates, or adjusts quality values. The snapshot's quality metadata is a historical record, not a live computation.

---

## SECTION C — ADR Backlog Update

### ADR-032 Status

**Accepted.** This document. `CandidateProfileSnapshot` as certified historical knowledge state. Seven snapshot principles frozen. Creation policy frozen. Engineering invariants frozen.

### Updated Backlog

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-032 | CandidateProfileSnapshot Strategy | Unblocked (ADR-022 accepted) | **ACCEPTED** |
| ADR-026 | Replay Snapshot Model | Unblocked (ADR-022 accepted) | **NEXT MILESTONE** |
| ADR-027 | LanguageExecutor Abstraction | Unblocked | Unchanged — P1 |
| ADR-028 | Language Selection Policy | Unblocked | Unchanged — P1 |
| ADR-030 | StudyRecommendation Resource Library | Pending | Unchanged — P2 |

---

## SECTION D — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ CandidateProfileSnapshot distinguished from serialized CandidateProfile | **FROZEN** — Section A1: certified historical knowledge state |
| ✓ Freeze responsibilities defined | **FROZEN** — Section A1: full comparison table |
| ✓ Ownership chain frozen | **FROZEN** — Section A2: five-object hierarchy with ownership invariants |
| ✓ Seven snapshot principles frozen | **FROZEN** — Section A3: Immutable, Complete, Self-consistent, Deterministic, Versioned, Auditable, Self-contained |
| ✓ Snapshot contents frozen | **FROZEN** — Section A4: ProfileFeatures, Provenance, Confidence, Stability, Maturity, Knowledge Quality, Language Profile, Quality Metadata, Reserved Future Metadata |
| ✓ Creation policy frozen | **FROZEN** — Section A5: FeatureEngine sole creator; created once at session close; never modified; never regenerated |
| ✓ Lifecycle frozen | **FROZEN** — Section A5: lifecycle diagram from session close to downstream consumers |
| ✓ Engineering invariants frozen | **FROZEN** — Section A6: EI-01 through EI-04 |
| ✓ Knowledge quality model frozen | **FROZEN** — Section B: three-level quality hierarchy; quality preserved not reinterpreted |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — no V1.1 asset modified |

---

## Final Recommendation

**ADR-032 is ACCEPTED.**

`CandidateProfileSnapshot` is a certified historical knowledge state. It is not a serialized runtime object. FeatureEngine is the sole creator. It is created once at session close, never modified, never regenerated in normal execution. Seven canonical snapshot principles govern its form. Engineering invariants prevent any component from misusing or recreating it.

**Immediate next action: ADR-026 (Replay Snapshot Model).** All snapshot layer preconditions are now met.

---

## Rationale

The distinction between serialization and certification is not philosophical — it is architectural. A serialized `CandidateProfile` is valid only for the FeatureEngine version that produced it. A certified `CandidateProfileSnapshot` carries the version metadata needed for any future consumer to interpret it correctly. Without this distinction, replay accuracy, LearningProgress cross-session comparison, and calibration policy-version-awareness all degrade silently as the platform evolves.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| `CandidateProfile` serialization as snapshot | No version metadata; no quality metadata; no provenance; ambiguous authority |
| Snapshot rebuilt from ObservationStoreSnapshot at replay time | Non-deterministic as FeatureEngine evolves; replay shows different conclusions on the same session over time |
| Snapshot without confidence/stability/maturity | Replay cannot display knowledge quality; LearningProgress cannot compare evidence reliability across sessions |
| Multiple snapshots per session (per cycle) | Storage overhead; only the final state has meaning for history; intermediate states are transient |

## Consequences

### Positive
- Replay is always deterministic and historically accurate
- LearningProgress comparison has stable, certified knowledge states to compare
- Calibration has policy-version-aware feature values
- Audit can trace every conclusion to source Observations
- Schema evolution does not corrupt historical snapshots

### Negative / Risks
- FeatureEngine closure cycle adds latency at session close — acceptable for V1.2; must be measured
- Storage overhead from quality metadata — acceptable for V1.2 SQLite; review at scale

## Implementation Evidence

Architecture only. No production files modified.
