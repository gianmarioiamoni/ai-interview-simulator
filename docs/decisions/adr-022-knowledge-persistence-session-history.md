# ADR-022 — Knowledge Persistence & SessionHistory Architecture

**Status:** Accepted — V1.2 Architecture (K2 Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Knowledge Persistence Layer
**Preconditions:** ADR-016, ADR-016A, ADR-017, ADR-018, ADR-019, ADR-020, ADR-021, K0/K1/K2 frozen
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-023, ADR-025, ADR-026, ADR-029, ADR-032

---

## Context

ADR-016 through ADR-021 froze the complete V1.2 knowledge model — from raw EvidenceSignal through Observation, FeatureEngine, ProfileFeature, CandidateProfile, freshness, and replay strategy. Every concept that needs to be persisted has been defined.

What remained undefined:

- Why `SessionHistory` is the platform's historical memory, not merely a persistence store
- The formal distinction between `Current CandidateProfile`, `CandidateProfileSnapshot`, `KnowledgeSnapshot`, `SessionHistory`, and `LearningProgress`
- The `KnowledgeSnapshot` concept — the self-contained session closure artefact
- The schema versioning strategy: what must be recorded, what it enables, how migration works
- The `KnowledgeEpoch` concept — a reserved generational marker for future cross-version analytics
- The runtime persistence flow and all invariants governing it

This ADR freezes all of the above. No implementation, no contracts, no code.

---

## Decision

**`SessionHistory` is the historical memory of the platform — not a database table.**

It is a write-once, immutable, self-contained record of what the platform knew about a candidate at the end of a session. Every subsequent action the platform takes on behalf of that candidate — replay, progress tracking, coaching, calibration — reads from `SessionHistory`. Nothing writes back.

---

## SECTION A — Purpose: SessionHistory as Historical Memory

### Why SessionHistory Is Not Merely Persistence

A persistence store is an operational component — it holds current state, supports updates, and serves queries. `SessionHistory` is something different:

1. **It is write-once.** No field, no record, no nested object may be updated after the session closes. The session completion pipeline is the sole writer, and it writes exactly once.

2. **It is self-contained.** A `SessionHistory` record must be sufficient to reproduce the complete session experience — replay, coaching, progress comparison — without any live pipeline invocation. It is not a pointer to live data; it is a frozen copy of everything the platform knew.

3. **It is the authoritative historical record.** When there is a discrepancy between what `SessionHistory` records and what FeatureEngine would compute today (due to schema evolution), `SessionHistory` wins. The historical record is not a draft; it is a fact.

4. **It carries its own version context.** Every `SessionHistory` record embeds the schema versions, policy versions, and engine versions that were active when it was written. Future consumers can always interpret it correctly without guessing the context.

### Responsibility Freeze: Five Distinct Objects

| Object | Responsibility | Mutable? | Persisted? |
|---|---|---|---|
| `Current CandidateProfile` | Live knowledge state for the active session; updated per FeatureEngine cycle | Yes | No — session-resident |
| `CandidateProfileSnapshot` | Point-in-time immutable capture of `CandidateProfile` at session close | No | Yes — inside KnowledgeSnapshot |
| `KnowledgeSnapshot` | Self-contained closure artefact: snapshot + narrative + coaching + all policy versions | No | Yes — inside SessionHistory |
| `SessionHistory` | Complete historical memory of one completed session | No | Yes — durable, write-once |
| `LearningProgress` | Cross-session derived view computed at query time from `SessionHistory[]` | N/A | No — derived, never stored |

---

## SECTION B — Knowledge Persistence Model

### Ownership Chain

```
CandidateIdentity
    │  (root owner of all persistent knowledge — ADR-016A)
    │
    └──→ SessionHistory[]    (one per completed session; write-once)
              │
              └──→ KnowledgeSnapshot   (one per SessionHistory; immutable)
                        │
                        └──→ CandidateProfileSnapshot  (one per KnowledgeSnapshot; immutable)
                        └──→ Narrative                 (one per KnowledgeSnapshot; immutable)
                        └──→ CoachingPlan              (one per KnowledgeSnapshot; immutable)
                        └──→ Policy Versions           (recorded at session close; immutable)
                        └──→ Engine Versions           (recorded at session close; immutable)
```

### Write-Once Philosophy

**Frozen invariant:** `SessionHistory` is written exactly once — at session close by the session completion pipeline. After that write, no component may:

- Add fields to the record
- Update existing fields
- Delete the record
- Append to nested collections

The only permitted operation on a completed `SessionHistory` is **reading**. This is not a convention — it is the foundational invariant of the persistence layer.

### LearningProgress Derivation

`LearningProgress` is computed on demand from `SessionHistory[]` for a given `CandidateIdentity`. It compares `CandidateProfileSnapshot` records across sessions using `FeatureIdentity` as the stable key (ADR-020). It is never stored.

If computation cost grows in V1.3+, a caching layer is permitted — but the cache must be treated as evictable, not as a source of truth. The only source of truth for LearningProgress is the `SessionHistory[]` it was derived from.

---

## SECTION C — KnowledgeSnapshot

### Definition

`KnowledgeSnapshot` is the self-contained session closure artefact. It contains everything needed to reproduce the platform's knowledge state at the end of the session — without invoking any live pipeline component.

### Principle

> **A `KnowledgeSnapshot` must be sufficient to reproduce the session.**

This means: given only the `KnowledgeSnapshot` and the session transcript, an external system can:
- Display the candidate's profile as it was at session close
- Replay the narrative and coaching
- Compare this session to any other session (cross-session progress)
- Audit any ProfileFeature value back to its source Observations

No live FeatureEngine invocation, no live ObservationStore query, no live NarrativeGenerator call is required.

### Contents

| Component | Description | Source |
|---|---|---|
| `CandidateProfileSnapshot` | Immutable copy of `CandidateProfile.features` at session close; includes full provenance (`source_observation_ids`) and all quality metadata | FeatureEngine final cycle |
| `ObservationStoreSnapshot` | Ordered list of all Observations (all lifecycle states) with their final `freshness_at_close` values | ObservationStore snapshot at session close |
| `Narrative` | Complete NarrativeSections and NarrativeInsights as generated | NarrativeGenerator |
| `CoachingPlan` | Complete CoachingPlan with ranked CoachingActions and LearningObjectives | CoachingEngine |
| `feature_engine_version` | Version of FeatureEngine that produced the CandidateProfileSnapshot | FeatureEngine |
| `language_policy_version` | Version of LanguagePolicy active at session time (per enabled language) | LanguageProfile |
| `ttl_policy_version` | Version of TTL/freshness policy active at session time (ADR-021) | ObservationStore configuration |
| `evaluation_policy_version` | Version of EvaluationPolicy active at session time | EvaluationEngine configuration |
| `narrative_schema_version` | Schema version of the Narrative structure | NarrativeGenerator |
| `coaching_schema_version` | Schema version of the CoachingPlan structure | CoachingEngine |
| `profile_schema_version` | Schema version of ProfileFeature objects in CandidateProfileSnapshot | FeatureEngine |
| `knowledge_epoch` | The KnowledgeEpoch marker for this session (see Section I); initially `"1"` | Platform configuration |
| `metadata` | Reserved dict for future additive fields | — |

### Immutability

`KnowledgeSnapshot` is immutable after creation. No field may be updated. The `metadata` dict is populated at creation time and not modified thereafter (V1.2 logic ignores unknown keys in `metadata` for forward compatibility).

---

## SECTION D — CandidateProfileSnapshot

### Definition

`CandidateProfileSnapshot` is an immutable point-in-time capture of `CandidateProfile.features` at session close.

### Relationship to Current CandidateProfile

| Property | `Current CandidateProfile` | `CandidateProfileSnapshot` |
|---|---|---|
| Mutability | Mutable — updated per FeatureEngine cycle | Immutable after creation |
| Persistence | Never persisted directly | Persisted in KnowledgeSnapshot |
| Lifecycle | Session-resident; discarded at session end | Permanent historical record |
| Recomputability | Always recomputable from ObservationStore | Self-contained; recomputation is exceptional |
| Consumer | NarrativeGenerator, CoachingEngine, ReportBuilder during live session | Replay, LearningProgress, Calibration |

### Frozen Invariants

**D-01:** Snapshot is immutable. No process may update, patch, or extend a stored `CandidateProfileSnapshot` after session close.

**D-02:** Current CandidateProfile is recomputable. Given the same `ObservationStore` state, FeatureEngine always produces the same profile. Snapshots are not the only path to the profile value during a live session.

**D-03:** Snapshot never updates. If a post-session analysis produces a different profile (e.g., after schema migration), the result is a **new artefact stored alongside the original** — the original snapshot is never modified.

**D-04:** Current CandidateProfile may evolve. During a live session, FeatureEngine updates the profile after each question. This evolution is ephemeral — only the final state at session close is captured in the snapshot.

**D-05:** Snapshot carries full provenance. Every ProfileFeature in the snapshot includes `source_observation_ids` — the complete chain back to source Observations. The ObservationStoreSnapshot in `KnowledgeSnapshot` provides the Observation records referenced by this provenance.

---

## SECTION E — SessionHistory

### Definition

`SessionHistory` is the complete historical memory of one completed interview session. It is write-once and immutable.

### Contents

| Field | Description |
|---|---|
| `session_id` | Unique session identifier (uuid4) |
| `candidate_identity_id` | Owning candidate (ADR-016A) |
| `knowledge_snapshot` | The `KnowledgeSnapshot` for this session (immutable) |
| `transcript` | Ordered question-and-answer sequence for the session |
| `question_timeline` | Per-question metadata: question_index, language, category, difficulty, timing |
| `evaluation_results` | EvaluationResult records per question (dimension scores, pass/fail) |
| `interview_metadata` | Session configuration: role, seniority, mode, language, question count |
| `language_profile` | The `LanguageProfile` active for this session (frozen at session start) |
| `replay_metadata` | Replay access hints: snapshot completeness flag, recomputation_available flag |
| `schema_version` | Schema version of the SessionHistory record itself |
| `created_at` | UTC timestamp of session close |
| `interview_index` | Sequential session number for this `CandidateIdentity` (0-based) |

### Ownership

`CandidateIdentity` is the root owner. Every `SessionHistory` record carries `candidate_identity_id`. The session completion pipeline is the sole writer.

### Write-Once Policy

**Frozen invariant:** The session completion pipeline writes `SessionHistory` exactly once. After that write:
- No field is updated.
- No record is deleted.
- No new field is appended.
- Schema additions in future platform versions are additive only — old records are never retroactively modified.

Additive schema evolution means: new `SessionHistory` records written after a schema update carry new optional fields. Old records do not carry those fields — consumers must treat absent optional fields as `None`, not as errors.

---

## SECTION F — Replay Fidelity

### Principle

> **Replay must reproduce what happened — not what would happen today.**

The purpose of replay is to show the candidate what the platform concluded about them at the end of their session. It is not a re-analysis tool. It is a historical viewer.

If the platform's FeatureEngine has evolved since that session, the replay must still show the original conclusions — not recomputed ones. The original conclusions are captured in `KnowledgeSnapshot`. Replay reads from there.

### Replay Decision Hierarchy

```
Replay requested for session S
    │
    ▼
Is KnowledgeSnapshot.CandidateProfileSnapshot valid and complete?
    │
    ├──[YES]──→ Use KnowledgeSnapshot directly.
    │           No FeatureEngine invocation.
    │           No ObservationStore query.
    │           No freshness filtering.
    │           Display: original profile, narrative, coaching as recorded.
    │
    └──[NO]───→ Is this an explicit migration or recovery request?
                    │
                    ├──[YES]──→ Invoke ReplayUpdater with ObservationStoreSnapshot.
                    │           Apply current FeatureEngine schema.
                    │           TTL ignored — all Observations used.
                    │           Store result as a separate reconstructed artefact.
                    │           Do NOT overwrite original KnowledgeSnapshot.
                    │
                    └──[NO]───→ Report missing/corrupted snapshot.
                                Flag for data integrity review.
                                Do not silently reconstruct.
```

### Frozen Fidelity Invariants

**RF-01:** `KnowledgeSnapshot` is the replay source. FeatureEngine is not invoked for standard replay.

**RF-02:** Replay is deterministic. Given the same `KnowledgeSnapshot`, replay always produces the same output.

**RF-03:** Replay never rewrites history. A reconstructed profile (from `ReplayUpdater`) is stored as a separate artefact. The original `KnowledgeSnapshot` is never modified.

**RF-04:** All policy versions in `KnowledgeSnapshot` are for fidelity audit — they tell the reader what rules governed the original session. They are never re-applied at replay time (except in explicit migration scenarios).

**RF-05:** `KnowledgeSnapshot` is preferred over recomputation for all standard replay paths. Recomputation is reserved for migration, recovery, and explicit re-analysis scenarios.

---

## SECTION G — Schema Versioning

### What Must Be Recorded

Every `SessionHistory` record must include the following version fields to enable correct interpretation by future consumers:

| Version Field | What it identifies | Stored Where |
|---|---|---|
| `schema_version` | Version of the SessionHistory schema itself | `SessionHistory.schema_version` |
| `feature_engine_version` | FeatureEngine version that produced the ProfileFeatures | `KnowledgeSnapshot.feature_engine_version` |
| `profile_schema_version` | Schema version of ProfileFeature objects | `KnowledgeSnapshot.profile_schema_version` |
| `language_policy_version` | Per-language LanguagePolicy version active at session time | `KnowledgeSnapshot.language_policy_version` |
| `ttl_policy_version` | TTL/freshness decay policy version (ADR-021) | `KnowledgeSnapshot.ttl_policy_version` |
| `evaluation_policy_version` | EvaluationPolicy version active at session time | `KnowledgeSnapshot.evaluation_policy_version` |
| `narrative_schema_version` | Schema version of Narrative structure | `KnowledgeSnapshot.narrative_schema_version` |
| `coaching_schema_version` | Schema version of CoachingPlan structure | `KnowledgeSnapshot.coaching_schema_version` |
| `knowledge_epoch` | Knowledge generation marker (Section I) | `KnowledgeSnapshot.knowledge_epoch` |

### Forward Compatibility

All version fields are strings. Consumers must:
- Ignore unknown `metadata` dict keys.
- Treat absent optional fields as `None`.
- Use `schema_version` to branch behaviour when major version differences exist.
- Never fail on an unknown `knowledge_epoch` value — log and proceed with best-effort interpretation.

### Migration Philosophy

Schema migration is additive and non-destructive:

1. **New minor version:** New optional fields added. Existing records remain valid. Consumers treat absent optional fields as `None`. No migration required.

2. **New major version:** Breaking changes. Existing records remain stored and readable using the version-branching logic. A migration script may produce upgraded records stored **alongside** originals — never replacing them. The `schema_version` of the upgraded record differs from the original.

3. **No silent migrations.** A migration that alters stored knowledge must be explicit, logged, and auditable. The original record is preserved.

4. **No retroactive schema changes.** The schema of a stored record is the schema at the time it was written. Future readers adapt to the stored schema using version-branching — not by altering the record.

---

## SECTION H — Migration Strategy

### Principles

**MS-01:** Replay always prefers stored knowledge. A valid `KnowledgeSnapshot` is the authoritative source. It is never replaced by recomputation.

**MS-02:** Migration may rebuild knowledge only when: snapshot unavailable, snapshot corrupted (failed integrity check), or migration explicitly requested by a human operator.

**MS-03:** No silent migrations. Every migration action is explicitly triggered, logged with a reason, and produces a new artefact alongside the original. Automated migration without human approval is forbidden.

**MS-04:** Reconstructed knowledge is labelled. A ProfileFeature or CandidateProfileSnapshot produced by `ReplayUpdater` carries a `reconstruction_context` field marking it as reconstructed, with the reconstruction timestamp and FeatureEngine version used.

**MS-05:** Original records are never deleted during migration. The migration output is additive. Data retention decisions are separate and require an explicit policy ADR.

**MS-06:** Migration does not guarantee equivalence. A profile reconstructed from Observations under a newer FeatureEngine schema may differ from the original. This is expected and acceptable — the original remains the authoritative historical record.

---

## SECTION I — KnowledgeEpoch (Reserved Concept)

### Definition

`KnowledgeEpoch` is a generational marker for the knowledge model. It is distinct from `schema_version`.

```
KnowledgeEpoch         ≠        schema_version

A generational           A version of a specific
identifier for the        schema (ProfileFeature,
entire knowledge          SessionHistory, etc.)
model paradigm.           that evolves within
                          a KnowledgeEpoch.
```

### What KnowledgeEpoch Represents

`KnowledgeEpoch` marks a fundamental shift in how the platform understands and models candidate knowledge — not just a schema field change.

Examples of epoch-changing events (future, not V1.2):
- Introduction of the Observation Intelligence Layer itself (V1.2 → Epoch 1)
- Introduction of cross-session knowledge accumulation (V1.3 → Epoch 2)
- Introduction of a Knowledge Graph (V2 → Epoch 3)

Within a single epoch, `schema_version` values evolve freely. Comparing knowledge across epochs requires explicit translation logic — not just schema migration.

### V1.2 Epoch Assignment

All V1.2 `KnowledgeSnapshot` records carry `knowledge_epoch = "1"`. This is the first epoch — the V1.2 Observation Intelligence Layer era.

### Why KnowledgeEpoch Is Recorded Now

Even though epoch transitions are future events, recording the epoch value from the first V1.2 session ensures:
1. All V1.2 sessions can be identified as Epoch 1 records in future analytics.
2. The migration path from Epoch 1 to Epoch 2 has a clean starting point.
3. Cross-epoch comparison (e.g., LearningProgress spanning two epochs) can use the `knowledge_epoch` field to apply the correct interpretation rules.

### Reserved Status

`KnowledgeEpoch` is a reserved concept. No production logic beyond recording the value acts on it in V1.2. Its interpretation logic is deferred to the ADR that introduces the second epoch.

**Frozen invariant:** `KnowledgeEpoch` is never inferred. It is explicitly recorded by the session completion pipeline from the platform's current epoch configuration. If the epoch value is absent from a `KnowledgeSnapshot`, the record is treated as `epoch = "1"` (backward-compatible default for pre-ADR-022 records).

---

## SECTION J — Runtime Architecture

### Canonical Persistence Flow

```
Interview Session
    │
    ▼  [live: FeatureEngine per cycle]
Current CandidateProfile
    │  (session-resident; never persisted directly)
    │
    ▼  [session close event — session completion pipeline]
    │
    ├──[FeatureEngine final cycle]──→ CandidateProfileSnapshot
    │                                 (ProfileFeature[] + provenance + quality metadata)
    │
    ├──[ObservationStore snapshot]──→ ObservationStoreSnapshot
    │                                 (all Observations + freshness_at_close)
    │
    ├──[NarrativeGenerator]──────────→ Narrative (complete sections + insights)
    │
    ├──[CoachingEngine]──────────────→ CoachingPlan (ranked actions + objectives)
    │
    ├──[Platform configuration]─────→ Policy Versions + Engine Versions
    │
    └──[All above assembled]──→ KnowledgeSnapshot (immutable; write-once)
                                     │
                                     ▼  [single writer: session completion pipeline]
SessionHistory (write-once; durable)
    │  Contains: KnowledgeSnapshot, Transcript, Evaluation Results,
    │            LanguageProfile, Interview Metadata, Schema Versions
    │
    ├──────────────────────────────────────────────┐
    ▼                                              ▼
Replay                                    LearningProgress
(reads KnowledgeSnapshot;                 (derived at query time from
 no live pipeline;                         SessionHistory[]; never stored)
 deterministic)
    │
    ▼
Display (profile, narrative, coaching as recorded)
```

### Runtime Invariant Validation

| Property | Status |
|---|---|
| **Single writer** | Session completion pipeline is the sole writer of `SessionHistory`. No other component writes to it after session close. ✓ |
| **Single ownership** | `CandidateIdentity` owns all `SessionHistory` records. `candidate_identity_id` is present on every record. ✓ |
| **Immutable history** | `SessionHistory` and `KnowledgeSnapshot` are write-once. No update operations permitted. ✓ |
| **Knowledge preservation** | `KnowledgeSnapshot` is self-contained. All knowledge, provenance, policy versions, and engine versions are embedded. ✓ |
| **Replay determinism** | `KnowledgeSnapshot` → display is deterministic. Same snapshot, same output, always. ✓ |
| **LearningProgress derivation** | `LearningProgress` derives from `SessionHistory[]` only, never from `Current CandidateProfile`. ✓ |
| **No circular dependencies** | `SessionHistory` has no reference to live pipeline components. Live pipeline has no reference to `SessionHistory` during active session. ✓ |

---

## SECTION K — Engineering Invariants

| Invariant | Statement |
|---|---|
| **K-01** | `SessionHistory` never mutates. It is written once and never modified. |
| **K-02** | `KnowledgeSnapshot` never mutates. It is immutable after creation. |
| **K-03** | Replay never rewrites history. A reconstructed artefact is stored alongside the original — never replacing it. |
| **K-04** | `LearningProgress` derives from `SessionHistory` only. It is never computed from `Current CandidateProfile` and never stored independently. |
| **K-05** | Snapshots are preferred over recomputation for all replay operations. Recomputation is reserved for migration and recovery. |
| **K-06** | Policy versions are always preserved. `language_policy_version`, `ttl_policy_version`, `evaluation_policy_version` are embedded in `KnowledgeSnapshot` at session close and never modified. |
| **K-07** | Schema versions are always preserved. `schema_version`, `feature_engine_version`, `profile_schema_version` are embedded at session close. |
| **K-08** | `KnowledgeEpoch` is never inferred. It is explicitly assigned by the session completion pipeline from the platform's current epoch configuration. |
| **K-09** | `KnowledgeEpoch` is explicitly recorded in every `KnowledgeSnapshot`. Absent epoch field defaults to `"1"` for backward compatibility with pre-ADR-022 records. |
| **K-10** | Schema additions are additive only. No existing `SessionHistory` field is removed or renamed. New fields are optional and absent from older records. |

---

## SECTION L — Future Compatibility

### ADR-023 (NarrativeGenerator Profile-Feature-Aware Prompt Design)

**Compatible and directly unblocked.** `NarrativeGenerator` reads `CandidateProfile.features`. Its output (`Narrative`) is stored in `KnowledgeSnapshot`. ADR-023 may now design the prompt and output contract knowing exactly where Narrative lives in the persistence model.

### ADR-025 (CoachingEngine Ranking Algorithm)

**Compatible.** `CoachingPlan` is stored in `KnowledgeSnapshot`. ADR-025 defines the ranking algorithm; ADR-022 defines where the result lives.

### ADR-026 (Replay Snapshot Model)

**Directly unblocked.** ADR-026 defines the full operational replay subsystem. This ADR defines the `KnowledgeSnapshot` source that replay reads. ADR-026 must implement the RF-01 through RF-05 principles frozen here.

### ADR-032 (CandidateProfileSnapshot Strategy)

**Directly unblocked.** ADR-032 defines the snapshot assembly and versioning in detail. This ADR defines where `CandidateProfileSnapshot` lives (inside `KnowledgeSnapshot`) and what it must contain (Section D).

### ADR-029 (Enterprise Extensibility — TenantContext Placeholder)

**Compatible.** `SessionHistory` carries a `metadata` dict reserved for additive fields. `TenantContext` may be added as an optional `metadata` field without modifying the `SessionHistory` schema. ADR-029 must use this extension point.

### Progress Tracking

**Compatible.** `LearningProgress` is derived from `SessionHistory[].knowledge_snapshot.candidate_profile_snapshot`. The `FeatureIdentity`-keyed ProfileFeatures provide the cross-session comparison keys. `knowledge_epoch` enables epoch-aware progress comparison in V1.3+.

### Replay

**Directly defined.** Section F and Section H freeze the complete replay strategy. ADR-026 implements; ADR-022 architects.

### NarrativeGenerator / CoachingEngine

**Both compatible.** Their outputs (`Narrative`, `CoachingPlan`) are stored in `KnowledgeSnapshot`. Their inputs (`CandidateProfile.features`, `KnowledgeGap[]`) are consumed during the live session — not from `SessionHistory`.

### Calibration

**Compatible.** `CalibrationProfile` reads `SessionHistory[]` in aggregate (read-only). The `evaluation_policy_version` and `language_policy_version` fields in `KnowledgeSnapshot` enable per-policy-version calibration baselines.

### Knowledge Graph (V2 candidate)

**Compatible.** A Knowledge Graph would consume `KnowledgeSnapshot.candidate_profile_snapshot.source_observation_ids` for edge data. The `knowledge_epoch` field enables epoch-partitioned graph queries.

### Multi-language (ADR-027, ADR-028)

**Compatible.** `language_profile` is stored in `SessionHistory`. `language_policy_version` (per enabled language) is in `KnowledgeSnapshot`. Multi-language sessions store both policy versions. No schema change required.

### V1.1 Compatibility

**Confirmed. No frozen V1.1 asset requires change.**

| V1.1 Asset | Status |
|---|---|
| `EvidenceSignal` schema | Protected. Unchanged. |
| `EvidenceStore` contract | Protected. Unchanged. |
| `CandidateProfile` V1.1 fields | Protected. Unchanged. |
| Pattern detectors (10 existing) | Protected. Unchanged. |
| `ReasonerService` | Protected. Unchanged. |
| `EvaluationEngine` | Protected. Unchanged. |

---

## SECTION M — ADR Backlog Update

### ADR-022 Status

**Accepted.** This document. Knowledge Persistence architecture, `KnowledgeSnapshot`, `SessionHistory`, Replay Fidelity, Schema Versioning, Migration Philosophy, and `KnowledgeEpoch` concept frozen.

### Updated Backlog

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-022 | Knowledge Persistence & SessionHistory Architecture | NEXT MILESTONE (P1) | **ACCEPTED** |
| ADR-023 | NarrativeGenerator Profile-Feature-Aware Prompt Design | UNBLOCKED (ADR-018/020) | **NEXT MILESTONE — P1** |
| ADR-025 | CoachingEngine Ranking Algorithm | UNBLOCKED (ADR-018/020) | Unchanged — P2; parallel |
| ADR-026 | Replay Snapshot Model | Blocked on ADR-022 | **UNBLOCKED** |
| ADR-029 | Enterprise Extensibility — TenantContext Placeholder | Blocked on ADR-022 | **UNBLOCKED** |
| ADR-032 | CandidateProfileSnapshot Strategy | Blocked on ADR-016A + ADR-022 | **UNBLOCKED** — all preconditions met |

### ADR-023 as Next Milestone

**ADR-023 (NarrativeGenerator Profile-Feature-Aware Prompt Design)** is the next milestone.

Rationale:
- All knowledge model architecture (ADR-016 through ADR-022) is now frozen.
- NarrativeGenerator is the first **action consumer** in the pipeline after knowledge construction.
- ADR-023 defines the ProfileFeature injection contract — how FeatureEngine output becomes NarrativeGenerator input.
- Without ADR-023, EPIC-03 (NarrativeGenerator V2) cannot begin implementation.

### Critical Path After ADR-022

```
ADR-022 ACCEPTED (this document)
    │
    ├──→ ADR-023 (NarrativeGenerator Design) — NEXT MILESTONE; P1
    │
    ├──→ ADR-025 (CoachingEngine Ranking) — P2; parallel
    │
    ├──→ ADR-026 (Replay Snapshot Model) — P2; unblocked
    │
    └──→ ADR-032 (CandidateProfileSnapshot Strategy) — P1; unblocked
```

---

## SECTION N — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ Knowledge Persistence architecture frozen | **FROZEN** — Section A/B: SessionHistory as historical memory; write-once philosophy; ownership chain |
| ✓ SessionHistory responsibilities frozen | **FROZEN** — Section E: 13 fields defined; write-once policy; additive schema evolution |
| ✓ KnowledgeSnapshot frozen | **FROZEN** — Section C: 13 components; self-sufficiency principle; immutability |
| ✓ CandidateProfileSnapshot frozen | **FROZEN** — Section D: 5 invariants (D-01 through D-05); relationship to Current CandidateProfile |
| ✓ Replay fidelity frozen | **FROZEN** — Section F: decision hierarchy; 5 fidelity invariants (RF-01 through RF-05) |
| ✓ Schema versioning frozen | **FROZEN** — Section G: 9 version fields; forward compatibility rules; migration philosophy |
| ✓ Migration philosophy frozen | **FROZEN** — Section H: 6 principles (MS-01 through MS-06); no silent migrations; originals preserved |
| ✓ Runtime validated | **VALIDATED** — Section J: full persistence flow; 7 runtime invariants |
| ✓ Engineering invariants confirmed | **CONFIRMED** — Section K: 10 invariants (K-01 through K-10) |
| ✓ KnowledgeEpoch concept introduced | **FROZEN** — Section I: generational marker distinct from schema_version; V1.2 = Epoch 1; reserved concept |
| ✓ Future compatibility confirmed | **CONFIRMED** — Section L: ADR-023/025/026/029/032, Progress, Replay, Calibration, Knowledge Graph all compatible |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section L: no frozen V1.1 asset requires change |

---

## Final Recommendation

**ADR-022 is ACCEPTED.**

The Knowledge Persistence architecture is frozen. `SessionHistory` is the historical memory of the platform. `KnowledgeSnapshot` is the self-contained session closure artefact. Replay fidelity is guaranteed by snapshot preference. Schema versioning, migration philosophy, and `KnowledgeEpoch` are all defined.

**Immediate next action: ADR-023 (NarrativeGenerator Profile-Feature-Aware Prompt Design).** The knowledge model is fully frozen (ADR-016 through ADR-022). ADR-023 begins the action layer — the first architecture decision about how knowledge becomes communication.

---

## Rationale

`KnowledgeSnapshot` as a self-contained closure artefact is the minimal design that satisfies all replay, progress tracking, and audit requirements without live pipeline dependency. The alternative — storing raw data and recomputing knowledge at replay time — would produce different results as the platform evolves, misrepresenting the historical session. Write-once `SessionHistory` and snapshot-preference replay guarantee that what the platform said at session close is permanently what replay shows.

`KnowledgeEpoch` is introduced now because the cost of retrofitting a generational marker to thousands of stored sessions is high. Recording `knowledge_epoch = "1"` from the first session costs nothing and enables clean cross-epoch analytics when V1.3 introduces cross-session knowledge accumulation.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Storing only raw Observations and recomputing at replay time | Recomputation produces different results as FeatureEngine evolves; misrepresents history; replay latency is high |
| Mutable SessionHistory (allowing post-session patches) | Destroys audit trail; makes LearningProgress inconsistent; creates race conditions in concurrent access |
| KnowledgeSnapshot without version fields | Future consumers cannot interpret stored records correctly; calibration cannot be policy-version-aware |
| Deferring KnowledgeEpoch to V1.3 | Retrofitting an epoch marker to all existing sessions requires a full migration; introducing it now is costless |
| LearningProgress stored in database | Creates consistency obligation — stored value must be invalidated when SessionHistory changes; derived-only is simpler and correct |

## Consequences

### Positive

- Write-once `SessionHistory` enables reliable, lock-free concurrent reads
- `KnowledgeSnapshot` self-sufficiency eliminates live pipeline dependency at replay time
- All version fields enable future migration, calibration, and cross-epoch analytics without guesswork
- `KnowledgeEpoch` provides a future-proof generational boundary at zero current cost
- ADR-026, ADR-029, ADR-032 are all unblocked

### Negative / Risks

- `KnowledgeSnapshot` storage overhead is higher than storing only raw data — acceptable for V1.2 SQLite deployment; must be reviewed at V1.3 scale
- Session completion pipeline is a single point of failure for knowledge persistence — if it fails mid-write, `SessionHistory` may be incomplete; requires atomic write semantics or a two-phase commit strategy (implementation concern)
- `ObservationStoreSnapshot` embedded in `KnowledgeSnapshot` duplicates data already in `EvidenceStore` — this duplication is intentional (self-sufficiency) but increases storage size

## Implementation Evidence

Architecture only. No production files modified.
Relevant existing assets (unchanged):
- `domain/contracts/reasoning/evidence_signal.py` (frozen)
- `domain/profile/candidate_profile.py` (unchanged)
- All V1.1 evaluation pipeline files (unchanged)

## Review Trigger

- When `SessionHistory` storage size exceeds expected bounds at scale
- When a second `KnowledgeEpoch` is introduced (V1.3+)
- When `TenantContext` is added via `metadata` field (ADR-029)
- When the atomic write strategy for session completion pipeline is specified (implementation ADR)
