# ADR-026 — Replay Snapshot Model

**Status:** Accepted — V1.2 Architecture (Snapshot Layer Frozen 2026-07-01)
**Date:** 2026-07-01
**Owner:** Domain — Snapshot Layer / Replay Subsystem
**Preconditions:** ADR-016, ADR-016A, ADR-017, ADR-018, ADR-019, ADR-020, ADR-021, ADR-022, ADR-025, ADR-032
**Supersedes:** Nothing
**Superseded by:** Nothing
**Related:** ADR-022, ADR-032, ADR-021, ADR-025, ADR-023

---

## Context

ADR-022 froze Replay Fidelity principles (RF-01 through RF-05) and the Replay Decision Hierarchy. ADR-032 froze the `CandidateProfileSnapshot` as the certified historical knowledge source. The `KnowledgeSnapshot` — containing the snapshot, narrative, coaching plan, and all policy versions — is the self-contained closure artefact.

What remained undefined:

- The formal philosophy of Replay: what it is and what it is not
- The priority-ordered source hierarchy for all replay operations
- The three conceptual Replay Levels and what each covers
- The four Replay Consistency guarantees
- The migration strategy: when it is permitted, how it executes, and what it produces
- The complete runtime flow from SessionHistory to Replay UI
- The `SnapshotManifest` and `ReplayManifest` reserved concepts

This ADR freezes all of the above. No implementation, no contracts, no code.

---

## Decision

**Replay is the deterministic reproduction of historical understanding — not a re-execution of historical events.**

Replay never re-runs the interview. It never re-evaluates answers. It never re-invokes FeatureEngine. It never re-calls NarrativeGenerator. It reads what was concluded at session close and presents it — faithfully, completely, and without silent modification.

---

## SECTION B1 — Purpose: Replay Philosophy

### What Replay Is

Replay is the subsystem responsible for presenting the platform's historical conclusions about a candidate, as they existed at the moment of session close.

Its contract is:

> **Show what was known. Show it exactly as it was known. Show it every time it is requested.**

This contract has three implications:

**1. Replay is a historical viewer, not an analytics engine.**
It does not compute new insights. It does not upgrade conclusions using newer models. It does not fill in gaps using current FeatureEngine capabilities. It presents the stored record.

**2. Replay is deterministic and stable.**
Given the same `SessionHistory`, replay must produce the same output every time — today, next year, after a platform upgrade, after a schema migration. The output of replay is determined entirely by the stored `KnowledgeSnapshot`, not by the current state of the platform.

**3. Replay is transparent.**
Every conclusion displayed by replay must be traceable to a source in `KnowledgeSnapshot`. There are no computed-at-display-time values that could differ between invocations.

### What Replay Is Not

- **Replay is not re-analysis.** It does not invoke any live pipeline component for standard operation.
- **Replay is not re-evaluation.** Answers are not re-scored. Observations are not re-extracted.
- **Replay is not a re-interview.** No questions are asked. No responses are collected.
- **Replay is not a migration.** It does not upgrade stored knowledge to the current schema. Migration is an exceptional, explicitly-triggered operation (Section B5).

---

## SECTION B2 — Replay Sources

### Source Priority Hierarchy

Replay must always prefer the most historically complete and authoritative source available. The following priority order is frozen:

```
Priority 1: KnowledgeSnapshot
    │
    ▼  (if KnowledgeSnapshot unavailable or flagged incomplete)
Priority 2: CandidateProfileSnapshot
    │  (extracted from KnowledgeSnapshot — same tier, accessed directly)
    │
    ▼  (if profile snapshot incomplete or corrupted)
Priority 3: Narrative
    │  (from KnowledgeSnapshot — used for text replay when profile is unavailable)
    │
    ▼  (if Narrative unavailable)
Priority 4: CoachingPlan
    │  (from KnowledgeSnapshot — used for coaching display when narrative is unavailable)
    │
    ▼  (if CoachingPlan unavailable)
Priority 5: Replay metadata
    │  (from SessionHistory.replay_metadata — snapshot completeness flag, 
    │   recomputation_available flag — used to diagnose and report partial availability)
    │
    ▼  (only if Priority 1-5 all unavailable AND explicit migration/recovery is requested)
Priority 6: FeatureEngine recomputation from ObservationStoreSnapshot
    │  (EXCEPTIONAL — requires human operator approval, explicit trigger, full audit log)
    │  (result stored as new artefact; original not modified)
```

### Source Invariants

**SP-01:** `KnowledgeSnapshot` is always the first source queried. No component may skip to a lower priority source without first determining that the higher priority source is unavailable or incomplete.

**SP-02:** Priority 6 (FeatureEngine recomputation) is never reached during standard replay. It is reached only during explicit migration or recovery operations.

**SP-03:** The source used for any given replay operation is always recorded in `ReplayManifest` (Section D). Source selection is auditable.

**SP-04:** Partial availability (e.g., `KnowledgeSnapshot` present but `CandidateProfileSnapshot` corrupted) is handled by descending the hierarchy for the affected component only — not for the entire replay. A replay may display narrative from Priority 3 while displaying profile from Priority 1, as long as each component's source is recorded.

---

## SECTION B3 — Replay Levels

### Three Conceptual Levels

Replay is not monolithic. Different consumers need different depths of historical reproduction. Three levels are frozen.

**Level 1 — Presentation Replay**

The candidate-facing view of session results. Presents:
- Profile display (from `CandidateProfileSnapshot`)
- Narrative sections and insights (from `Narrative`)
- Coaching plan and study recommendations (from `CoachingPlan`)
- Session summary metadata (from `SessionHistory.interview_metadata`)

Level 1 is the standard replay mode. It is fully served by `KnowledgeSnapshot` without any pipeline invocation. It is what the candidate sees when they review their session results.

**Level 2 — Knowledge Replay**

The operator or calibration view of the session's knowledge construction. Presents everything in Level 1, plus:
- Raw ProfileFeature values with confidence, stability, and maturity
- Source Observation IDs per feature (provenance)
- Observation freshness-at-close values (from `ObservationStoreSnapshot`)
- Active policy versions and engine versions at session time

Level 2 enables knowledge audit, calibration review, and LearningProgress analysis. It is fully served by `KnowledgeSnapshot` without any pipeline invocation. It is what calibration tooling and platform operators access.

**Level 3 — Reasoning Replay (Reserved)**

Deep reconstruction of the FeatureEngine computation path. Would present:
- FeatureCandidate evaluation history
- Observation weighting applied at each cycle
- Confidence evolution across the session

Level 3 is reserved. It is not defined for V1.2. The data required for Level 3 (intermediate FeatureEngine cycle state) is not included in `KnowledgeSnapshot` in V1.2. Level 3 requires a future ADR and a new `KnowledgeSnapshot` extension.

### Level Comparison

| Property | Level 1 | Level 2 | Level 3 |
|---|---|---|---|
| Consumer | Candidate | Operator / Calibration | Platform Engineering (future) |
| Source | KnowledgeSnapshot | KnowledgeSnapshot | Reserved (V1.3+) |
| Pipeline invocation | None | None | None (reserved) |
| Provenance access | No | Yes | Full (reserved) |
| V1.2 status | Defined | Defined | Reserved |

---

## SECTION B4 — Replay Consistency Guarantees

### Four Frozen Guarantees

**RC-01: Replay Always Reproduces Stored Knowledge**

Any replay of session S, at any time, using the same `KnowledgeSnapshot`, must produce output that is semantically identical to the output produced at session close. The profile, narrative, coaching, and quality metadata shown are always the values stored in `KnowledgeSnapshot` — not recomputed values.

This guarantee holds across platform versions. A replay executed after a FeatureEngine upgrade must show the pre-upgrade conclusions recorded in `KnowledgeSnapshot`, not the post-upgrade recomputed conclusions.

**RC-02: Replay Never Silently Upgrades**

Replay must never apply the current FeatureEngine schema, current TTL policy, or current LanguagePolicy to historical session data without explicit operator request. Silent upgrades produce historically inaccurate output and violate the platform's audit contract.

If the platform detects that a stored `KnowledgeSnapshot` was produced under an older schema, it must:
- Display the stored values faithfully
- Optionally note (not modify) the schema version mismatch in replay metadata
- Never alter the displayed values to match current schema

**RC-03: Replay Never Silently Recalculates**

No value shown in a standard replay may be computed at display time from raw data. Every value must be a direct read from `KnowledgeSnapshot`. There are no on-the-fly calculations in the standard replay path.

This excludes `LearningProgress` — which is, by design, derived at query time across `SessionHistory[]`. But `LearningProgress` is not part of session replay; it is a cross-session view. Within single-session replay, RC-03 holds unconditionally.

**RC-04: Replay Always Preserves Historical Meaning**

A `ProfileFeature` value stored in `CandidateProfileSnapshot` carries the meaning it had under the schema version that produced it. Future consumers must interpret it using that schema version — not the current schema. `profile_schema_version` (embedded in `KnowledgeSnapshot`) provides the interpretation key.

If a feature label has been renamed in a newer schema version, replay must show the original label from the stored schema version. Aliasing for display is permitted only if it is explicitly noted and never alters the stored value.

---

## SECTION B5 — Migration Strategy

### When Migration Is Permitted

Migration — rebuilding knowledge from raw data under a new FeatureEngine or schema — is permitted only under the following conditions:

1. **Snapshot unavailable:** `KnowledgeSnapshot` is absent from `SessionHistory` (data loss scenario).
2. **Snapshot corrupted:** `KnowledgeSnapshot` fails integrity verification.
3. **Explicit operator request:** A human operator explicitly triggers migration for a specific session or batch, with a documented reason.

Migration is **never triggered automatically** by normal platform operation (replay requests, progress queries, calibration jobs).

### Migration Creates a New Snapshot

When migration is triggered, the result is a new `CandidateProfileSnapshot` (and optionally a new `KnowledgeSnapshot`) stored **alongside** the original. The migration output:

- Carries `reconstruction_context`: migration timestamp, FeatureEngine version used, reason for migration
- Carries a `is_reconstructed: true` marker distinguishing it from the original
- Is stored in a designated migration slot in `SessionHistory` — not in the primary `knowledge_snapshot` field
- Never replaces or overwrites the original `KnowledgeSnapshot`

### Original Snapshot Always Preserved

The original `KnowledgeSnapshot` — including the original `CandidateProfileSnapshot` — is never deleted during migration. This is unconditional.

Data retention decisions (whether to eventually delete very old records) are separate from migration policy and require a dedicated ADR.

### Migration Policy Freeze

**MP-01:** Migration may only be triggered explicitly. No automated migration pipeline.

**MP-02:** Migration produces a new artifact alongside the original. The original is never modified.

**MP-03:** Migration output is labelled as reconstructed. `is_reconstructed: true` + `reconstruction_context` fields are mandatory.

**MP-04:** Migration may produce a different profile than the original. This is expected. The original remains the authoritative historical record. Migration output is a best-effort reconstruction under the current engine.

**MP-05:** Original snapshots are never deleted by migration. Data retention is governed separately.

**MP-06:** Migration is auditable. Every migration action is logged with trigger reason, operator identity, FeatureEngine version used, and produced artefact identifier.

---

## SECTION B6 — Runtime

### Canonical Replay Runtime Flow

```
SessionHistory (durable, write-once)
    │
    ▼  [replay requested — Level 1 or Level 2]
KnowledgeSnapshot
    │  (validate completeness; check replay_metadata flags)
    │
    ├──→ CandidateProfileSnapshot
    │       (ProfileFeatures + Confidence + Stability + Maturity + Provenance)
    │
    ├──→ Narrative
    │       (NarrativeSections + NarrativeInsights)
    │
    ├──→ CoachingPlan
    │       (LearningObjectives + CoachingActions + StudyRecommendations)
    │
    ├──→ Policy Versions
    │       (feature_engine_version, language_policy_version, ttl_policy_version,
    │        profile_schema_version, narrative_schema_version, coaching_schema_version)
    │
    └──→ ObservationStoreSnapshot [Level 2 only]
            (Observations + freshness_at_close)
    │
    ▼  [assembled by: Replay subsystem — no pipeline invocation]
ReplayManifest
    (replay_mode, replay_level, source used per component,
     migration_metadata if applicable, replay_timestamp, replay_engine_version)
    │
    ▼
Replay UI
    (displays profile, narrative, coaching as recorded;
     ReplayManifest available for audit access)
```

### Runtime Validation

| Property | Validation |
|---|---|
| **No live pipeline invocation** | FeatureEngine, NarrativeGenerator, CoachingEngine are not called during standard replay. ✓ |
| **Single knowledge source** | All display values read from `KnowledgeSnapshot`. No secondary live queries. ✓ |
| **Deterministic output** | Same `KnowledgeSnapshot` → same Replay UI output, unconditionally. ✓ |
| **Source traceability** | `ReplayManifest` records the source used for each component. ✓ |
| **Version awareness** | Policy versions embedded in `KnowledgeSnapshot` are available to Replay UI for fidelity display. ✓ |
| **Migration isolation** | Reconstructed artefacts stored alongside original; never in the primary `knowledge_snapshot` slot. ✓ |
| **No upward write** | Replay never writes to `SessionHistory`, `ObservationStore`, `CandidateProfile`, or any pipeline component. ✓ |

---

## SECTION C — Shared Snapshot Layer Validation

### Seven Snapshot Layer Properties

**1. Single Writer**
Each object in the snapshot hierarchy has exactly one designated writer. FeatureEngine is the sole creator of `CandidateProfileSnapshot`. The session completion pipeline is the sole writer of `SessionHistory` and `KnowledgeSnapshot`. No other component writes to any snapshot object.

**2. Single Ownership**
Every snapshot object is owned by a unique parent in the hierarchy. `CandidateProfileSnapshot` → `KnowledgeSnapshot` → `SessionHistory` → `CandidateIdentity`. No shared ownership, no orphaned snapshots.

**3. Immutable History**
Once written, no snapshot object — `CandidateProfileSnapshot`, `KnowledgeSnapshot`, `SessionHistory` — may be modified. History is permanently immutable.

**4. Replay Determinism**
The same `KnowledgeSnapshot` always produces the same replay output. This is guaranteed by RC-01 through RC-04 and by the absence of live pipeline invocation in the standard replay path.

**5. Auditability**
Every ProfileFeature value can be traced to source Observations via `source_observation_ids`. Every replay operation is logged in `ReplayManifest`. Every migration is logged with trigger, reason, and output artefact.

**6. Version Compatibility**
All snapshot objects carry version metadata. Future consumers can always determine the schema version, engine version, and policy versions that governed a stored snapshot. No consumer needs to guess context.

**7. Knowledge Preservation**
`KnowledgeSnapshot` is self-contained. It carries all knowledge, provenance, policy versions, and engine versions needed to present the session's conclusions without any live dependency. Knowledge survives platform evolution.

**8. Future Migration Compatibility**
Migration produces new artefacts alongside originals. Original snapshots are never deleted by migration. The migration output carries `reconstruction_context`. Future migration tooling has a clean, consistent protocol to follow.

**9. KnowledgeEpoch Compatibility**
`knowledge_epoch` (ADR-022) is embedded in `KnowledgeSnapshot`. Replay respects the epoch boundary — it reads epoch-specific field values using epoch-appropriate interpretation rules. Cross-epoch LearningProgress comparison uses `knowledge_epoch` to apply correct translation logic.

**10. No V1.1 Changes**
No frozen V1.1 asset is modified by the Snapshot Layer architecture. All V1.1 contracts — `EvidenceSignal`, `EvidenceStore`, pattern detectors, `ReasonerService`, `EvaluationEngine`, `CandidateProfile` V1.1 fields — are fully preserved.

---

## SECTION D — Future Concepts

### SnapshotManifest (Reserved)

`SnapshotManifest` is a reserved concept. No implementation is defined for V1.2.

`SnapshotManifest` would provide a declarative description of a `CandidateProfileSnapshot` — metadata about the snapshot's composition and generation context, independent of the snapshot's knowledge content. Conceptual contents:

| Component | Description |
|---|---|
| `feature_engine_version` | Version of FeatureEngine that produced the snapshot |
| `language_policy_version` | Version(s) of LanguagePolicy active at session time |
| `ttl_policy_version` | Version of TTL/freshness policy active at session time |
| `schema_versions` | Dict of all schema versions active at session time (profile, narrative, coaching, session) |
| `knowledge_epoch` | KnowledgeEpoch marker for this snapshot |
| `integrity_hash` | Hash of the snapshot's content for integrity verification (future) |
| `creation_metadata` | Timestamp, session_id, candidate_identity_id, interview_index |
| `reserved` | Reserved dict for future additive fields |

`SnapshotManifest` would enable snapshot integrity verification, cross-epoch analytics, and automated migration tooling without requiring full snapshot deserialization. It is reserved for a future ADR.

### ReplayManifest (Reserved / Partial V1.2 Use)

`ReplayManifest` is a reserved concept with partial operational use in V1.2.

In V1.2, `ReplayManifest` is produced at replay time and logged for audit access. It is not a stored domain object; it is a runtime record of a specific replay operation. Conceptual contents:

| Component | Description |
|---|---|
| `replay_mode` | Standard, Migration, or Recovery |
| `replay_level` | Level 1 (Presentation) or Level 2 (Knowledge) |
| `migration_metadata` | Present only if replay_mode = Migration; includes trigger reason, operator identity, FeatureEngine version used |
| `replay_timestamp` | UTC timestamp of the replay operation |
| `replay_engine_version` | Version of the Replay subsystem that processed this operation |
| `source_per_component` | Dict recording which source priority level was used for each component (profile, narrative, coaching) |
| `reserved` | Reserved dict for future additive fields |

`ReplayManifest` enables full audit of what was shown in any replay session and how it was derived. Its full formalization (as a persisted domain object vs. a logged record) is reserved for a future ADR.

---

## SECTION E — ADR Backlog Update

### ADR-026 Status

**Accepted.** This document. Replay philosophy frozen. Source priority hierarchy frozen. Three Replay Levels frozen. Four Consistency Guarantees frozen. Migration policy frozen. Runtime flow validated. `SnapshotManifest` and `ReplayManifest` introduced as reserved concepts.

### Updated Backlog

| ID | Subject | Prior Status | New Status |
|---|---|---|---|
| ADR-032 | CandidateProfileSnapshot Strategy | Unblocked | **ACCEPTED** |
| ADR-026 | Replay Snapshot Model | Unblocked | **ACCEPTED** |
| ADR-027 | LanguageExecutor Abstraction | P1 | **NEXT MILESTONE** |
| ADR-028 | Language Selection Policy | P1 | **NEXT MILESTONE (parallel with ADR-027)** |
| ADR-030 | StudyRecommendation Resource Library | P2 | Unchanged |

### Next Milestones

**ADR-027 (LanguageExecutor Abstraction)** and **ADR-028 (Language Selection Policy)** are the next milestones. Both are P1, both are unblocked by ADR-019, and both can proceed in parallel. They complete the language independence layer (EPIC-00) required before Phase 2 implementation begins.

**ADR-030 (StudyRecommendation Resource Library Governance)** is P2 and may proceed in parallel with EPIC-00 completion.

---

## SECTION F — Acceptance Checklist

| Criterion | Status |
|---|---|
| ✓ ADR-032 frozen | **FROZEN** — see adr-032-candidate-profile-snapshot-strategy.md |
| ✓ ADR-026 frozen | **FROZEN** — this document |
| ✓ Snapshot strategy frozen | **FROZEN** — ADR-032: seven principles, creation policy, engineering invariants |
| ✓ Replay architecture frozen | **FROZEN** — Section B1: philosophy; B2: source hierarchy; B3: levels; B4: consistency guarantees |
| ✓ Snapshot lifecycle frozen | **FROZEN** — ADR-032 Section A5: lifecycle from session close to downstream consumers |
| ✓ Replay levels frozen | **FROZEN** — Section B3: Level 1 (Presentation), Level 2 (Knowledge), Level 3 (Reserved) |
| ✓ Migration policy frozen | **FROZEN** — Section B5: MP-01 through MP-06 |
| ✓ SnapshotManifest concept introduced | **INTRODUCED** — Section D: conceptual contents; reserved; no implementation |
| ✓ ReplayManifest concept introduced | **INTRODUCED** — Section D: conceptual contents; partial V1.2 operational use; reserved for full formalization |
| ✓ Runtime validated | **VALIDATED** — Section B6: full runtime flow; seven runtime invariants |
| ✓ Engineering invariants confirmed | **CONFIRMED** — ADR-032 Section A6: EI-01 through EI-04; this ADR RC-01 through RC-04, MP-01 through MP-06 |
| ✓ Future compatibility confirmed | **CONFIRMED** — Section C: ten Snapshot Layer properties; KnowledgeEpoch compatibility |
| ✓ V1.1 compatibility confirmed | **CONFIRMED** — Section C, Property 10: no frozen V1.1 asset requires change |

---

## Final Recommendation

**ADR-026 is ACCEPTED.**

The Replay Snapshot Model is frozen. Replay is the deterministic reproduction of historical understanding — not re-execution, not re-analysis, not re-computation. Source priority hierarchy, three Replay Levels, four Consistency Guarantees, and Migration Policy (MP-01 through MP-06) are all defined. `SnapshotManifest` and `ReplayManifest` are introduced as reserved concepts. The Snapshot Layer is validated against all ten architectural properties.

**Next milestones: ADR-027 and ADR-028 (LanguageExecutor Abstraction and Language Selection Policy).** The Snapshot Layer is complete. The Language Independence Layer (EPIC-00) is the next architectural gate before Phase 2 implementation begins.

---

## Rationale

Replay-as-historical-viewer eliminates the largest class of silent data corruption risk in the platform: re-analysis producing different results than the original session. By treating `KnowledgeSnapshot` as the unconditional source for standard replay, the platform guarantees that what a candidate was told at session close is what they will see when they review their results — regardless of platform upgrades.

The source priority hierarchy makes partial availability explicit and auditable. A platform that silently falls back to recomputation when a snapshot is incomplete produces misleading results; the hierarchy + `ReplayManifest` makes every fallback visible.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Recompute profile from ObservationStoreSnapshot for all replays | Non-deterministic as FeatureEngine evolves; violates RC-01; high replay latency |
| Single replay level (no Level 1/Level 2 distinction) | Calibration and audit need provenance access; mixing candidate-facing and operator-facing data in one level creates over-exposure risk |
| Mutable KnowledgeSnapshot (patch on schema upgrade) | Destroys historical accuracy; audit trail broken; RC-02 violated |
| Migration as part of normal replay path | Introduces silent upgrades; violates RC-02; calibration cannot distinguish original from reconstructed data |

## Consequences

### Positive
- Replay is always historically accurate, regardless of platform version at replay time
- Source hierarchy makes partial availability explicit and auditable rather than silent
- Migration is safe, explicit, and non-destructive
- `ReplayManifest` creates a complete audit trail for every replay operation
- `SnapshotManifest` reservation enables future integrity verification at zero current cost

### Negative / Risks
- Level 3 Replay requires a `KnowledgeSnapshot` extension — intermediate FeatureEngine cycle state must be stored at session close for Level 3 to be possible; this increases storage cost (deferred to V1.3+)
- `ReplayManifest` full formalization (persisted vs. logged) is deferred — replay audit trail in V1.2 is log-based only

## Implementation Evidence

Architecture only. No production files modified.
Relevant existing assets (unchanged):
- `domain/contracts/reasoning/evidence_signal.py` (frozen)
- `domain/profile/candidate_profile.py` (unchanged)
- All V1.1 evaluation pipeline files (unchanged)
