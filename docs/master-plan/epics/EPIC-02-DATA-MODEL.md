# EPIC-02 — Data Model Specification

**Status:** FROZEN  
**Epic ID:** EPIC-V13-02  
**Date:** 2026-07-14  
**Precondition:** EPIC-02-DOMAIN-CONTRACTS.md frozen; ADR-034 accepted.  
**Authority:** This document resolves all open modelling decisions left by the Domain Contracts specification. It freezes complete field tables for all persisted artifacts, specifies the serialization format, verifies replay completeness, and evaluates forward extensibility. Implementation cannot begin before this document and the Architecture Freeze are both declared.

---

## Mandatory Validation Finding

**`FeatureProvenance.language_context` — CONFIRMED.**

Field exists in `domain/contracts/feature/feature_provenance.py` (line 45):

```
language_context: str | None  (default=None)
```

Description: "Programming language context — set only for LanguageCapabilityFeature (the one taxonomy exception per ADR-018 §D)."

The Domain Contracts specification (§3.2, §4.3) references `provenance.language_context` correctly. **No discrepancy.**

---

## 1. LongitudinalProfile — Complete Data Model

### 1.1 Persisted Artifact Structure

`LongitudinalProfile` is the sole persisted cross-session artifact introduced by EPIC-02. It is the unit of storage and the unit of replacement.

**Root object:**

| Field | Python Type | Serialized Type | Required | Default | Notes |
|---|---|---|---|---|---|
| `candidate_identity_id` | `str` | `string` | Yes | — | Primary key for persistence lookup. Never changes. |
| `session_snapshots` | `tuple[LongitudinalSessionEntry, ...]` | `array[LongitudinalSessionEntry]` | Yes | — | Ordered by `interview_index` ascending. |
| `session_count` | `int` | `integer` | Yes | — | Must equal `len(session_snapshots)`. Persisted for O(1) count queries. |
| `language_capability_summary` | `tuple[CrossSessionLanguageCapability, ...]` | `array[CrossSessionLanguageCapability]` | Yes | `[]` | One entry per distinct `language_id`. |
| `knowledge_epoch` | `str` | `string` | Yes | `"1"` | Epoch of most recent session. |
| `schema_version` | `str` | `string` | Yes | `"1.0"` | Schema version of this record. |
| `created_at` | `datetime` | ISO 8601 UTC string | Yes | — | Immutable after first write. |
| `last_updated_at` | `datetime` | ISO 8601 UTC string | Yes | — | Updated on each replacement. `>= created_at`. |
| `metadata` | `dict[str, str]` | `object{string: string}` | No | `{}` | Reserved extensibility slot. |

**Storage invariant:** One record per `candidate_identity_id`. Replace-on-write semantics. No append, no version history at the persistence layer. The persistence layer stores only the current version.

### 1.2 LongitudinalSessionEntry — Field Table

| Field | Python Type | Serialized Type | Required | Default | Notes |
|---|---|---|---|---|---|
| `session_id` | `str` | `string` | Yes | — | From `SessionHistory.session_id`. |
| `interview_index` | `int` | `integer` | Yes | — | From `SessionHistory.interview_index`. Primary sort key. |
| `profile_snapshot` | `CandidateProfileSnapshot` | `object` | Yes | — | Full embedded snapshot. Not a reference — full object value. |
| `session_metadata` | `LongitudinalSessionMetadata` | `object` | Yes | — | Session configuration summary. |
| `contributed_at` | `datetime` | ISO 8601 UTC string | Yes | — | Timestamp of contribution to this profile version. |

**Embedding policy:** `profile_snapshot` is embedded by value (not by reference). This ensures the persisted `LongitudinalProfile` is self-contained and requires no join to `SessionHistory` for reading. This is the Projection Artifact pattern (OP-02): the stored artifact is a snapshot, not a pointer.

### 1.3 LongitudinalSessionMetadata — Field Table

| Field | Python Type | Serialized Type | Required | Default | Notes |
|---|---|---|---|---|---|
| `role` | `str` | `string` | Yes | — | From `SessionHistory.interview_metadata.role`. |
| `seniority` | `str` | `string` | Yes | — | From `SessionHistory.interview_metadata.seniority`. |
| `interview_type` | `str` | `string` | Yes | — | From `SessionHistory.interview_metadata.interview_type`. |
| `question_count` | `int` | `integer` | Yes | — | From `SessionHistory.interview_metadata.question_count`. |
| `session_language` | `str` | `string` | Yes | — | From `SessionHistory.interview_metadata.session_language`. |
| `knowledge_epoch` | `str` | `string` | Yes | — | From `SessionHistory.knowledge_epoch` (property). |
| `total_objectives` | `int` | `integer` | Yes | `0` | From `SessionHistory.knowledge_snapshot.coaching_snapshot.statistics.total_objectives`. OI-01 resolved. |
| `total_narrative_insights` | `int` | `integer` | Yes | `0` | From `SessionHistory.knowledge_snapshot.narrative.insight_count` (property). OI-02 resolved. |
| `language_capabilities` | `tuple[LanguageCapability, ...]` | `array[LanguageCapability]` | Yes | `[]` | Passed by `longitudinal_update_node` from live session state. Not from `SessionHistory`. OI-03 resolved. |

### 1.4 CrossSessionLanguageCapability — Field Table

| Field | Python Type | Serialized Type | Required | Default | Notes |
|---|---|---|---|---|---|
| `language_id` | `str` | `string` | Yes | — | From `ProfileFeature.provenance.language_context`. Natural key within `language_capability_summary`. |
| `session_count_in_language` | `int` | `integer` | Yes | — | `>= 1`. Incremented on each contributing session. |
| `total_questions_answered` | `int` | `integer` | Yes | — | Running total. Aggregated from `LanguageCapability.questions_answered_in_language` via the session's feature set. |
| `mean_composite_score` | `float` | `number` | Yes | — | `[0.0, 1.0]`. Running mean of `composite_score` across contributing sessions. |
| `mean_idiomatic_score` | `float` | `number` | Yes | — | `[0.0, 1.0]`. Running mean of `idiomatic_usage_score`. |
| `mean_type_error_rate` | `float` | `number` | Yes | — | `[0.0, 1.0]`. Running mean of `type_error_rate`. |
| `trend_direction` | `str` | `string` | Yes | `"stable"` | Enum-like: `"improving"`, `"declining"`, `"stable"`, `"insufficient_data"`. |
| `schema_version` | `str` | `string` | Yes | `"1.0"` | — |

**Language score source:** `CrossSessionLanguageCapability` scores are extracted from `ProfileFeature` values (where `feature_type_id == "language_capability_feature"` and `provenance.language_context == language_id`). The `ProfileFeature.quality.confidence` field provides the confidence signal. The specific mapping from `ProfileFeature.value` to composite/idiomatic/type-error scores is a builder assembly responsibility (Domain Contracts §4.3, step 5) — not a data model decision.

### 1.5 CandidateProfileSnapshot — Embedded Data Model

`CandidateProfileSnapshot` is embedded verbatim in each `LongitudinalSessionEntry`. Its complete field set is defined by ADR-022 and the frozen V1.2 contract. It is reproduced here for completeness of the data model.

| Field | Python Type | Serialized Type | Notes |
|---|---|---|---|
| `candidate_identity_id` | `str` | `string` | Must match `LongitudinalProfile.candidate_identity_id`. |
| `features` | `tuple[ProfileFeature, ...]` | `array[ProfileFeature]` | Full feature set at session close. |
| `closed_at_question_index` | `int` | `integer` | — |
| `source_observation_ids` | `tuple[str, ...]` | `array[string]` | Provenance. |
| `total_feature_count` | `int` | `integer` | Must equal `len(features)`. |
| `mean_confidence` | `float` | `number` | — |
| `profile_schema_version` | `str` | `string` | — |
| `metadata` | `dict[str, str]` | `object{string: string}` | — |

`ProfileFeature` is further composed of `FeatureIdentity`, `FeatureProvenance`, `FeatureQuality`. These are embedded recursively. The full serialized `CandidateProfileSnapshot` is a nested object graph.

**Size consideration:** Embedding the full `CandidateProfileSnapshot` (including all `ProfileFeature` objects with provenance) makes each `LongitudinalSessionEntry` potentially large. For a 20-question session with 11 feature types, the embedded snapshot carries up to 11 `ProfileFeature` records, each with `FeatureProvenance` (including `source_observation_ids`). This is acceptable for V1.3 single-node persistence. If size becomes a P0 concern in EPIC-09, a reference-to-`SessionHistory` model may be evaluated — but requires a new ADR crossing the Ownership Boundary.

### 1.6 Schema Version — Complete Version Map

| Version | Trigger | Migration Required |
|---|---|---|
| `"1.0"` | Initial implementation (EPIC-02) | N/A |
| Future | Any backward-incompatible field change (see ADR-034 Decision 2) | New ADR mandatory before implementation |

**No schema migration exists in V1.3.** Since no production persistence layer exists at the time of this specification, there is no live data migration cost for the initial `"1.0"` schema. Any future version increment requires a migration strategy documented in the triggering ADR.

---

## 2. LearningProgress — Data Model

### 2.1 Not Persisted

`LearningProgress` is never persisted. It has no storage data model. This section specifies its in-memory field model as it is produced by `LearningProgressBuilder` from `LongitudinalProfile`.

### 2.2 LearningProgress — Full Field Table (Post-EPIC-02)

| Field | Python Type | New/Extended | Required | Default | Source |
|---|---|---|---|---|---|
| `candidate_identity_id` | `str` | Existing | Yes | — | `LongitudinalProfile.candidate_identity_id` |
| `session_entries` | `tuple[SessionProgressEntry, ...]` | Existing (source changed) | Yes | `()` | Derived from `LongitudinalProfile.session_snapshots` |
| `schema_version` | `str` | Existing | Yes | `"1.0"` | Fixed by builder |
| `computed_at` | `datetime` | Existing | Yes | — | UTC timestamp at builder invocation |
| `knowledge_epoch` | `str` | Existing | Yes | `"1"` | `LongitudinalProfile.knowledge_epoch` |
| `metadata` | `dict[str, str]` | Existing | No | `{}` | Empty in V1.3 |
| `behavioral_trend` | `BehavioralTrend` | **New** | Yes | — | Derived from `LongitudinalProfile.session_snapshots` |
| `language_capability_summary` | `tuple[CrossSessionLanguageCapability, ...]` | **New** | Yes | `()` | Propagated from `LongitudinalProfile.language_capability_summary` |
| `has_sufficient_data` | `bool` | **New** | Yes | — | `len(session_entries) >= 2` |

### 2.3 SessionProgressEntry — Full Field Table (Post-EPIC-02)

| Field | Python Type | New/Extended | Required | Default | Source |
|---|---|---|---|---|---|
| `session_id` | `str` | Existing | Yes | — | `LongitudinalSessionEntry.session_id` |
| `session_index` | `int` | Existing | Yes | — | `LongitudinalSessionEntry.interview_index` |
| `created_at` | `datetime` | Existing | Yes | — | `LongitudinalSessionEntry.contributed_at` |
| `role` | `str` | Existing | Yes | — | `LongitudinalSessionEntry.session_metadata.role` |
| `seniority` | `str` | Existing | Yes | — | `LongitudinalSessionEntry.session_metadata.seniority` |
| `interview_type` | `str` | Existing | Yes | — | `LongitudinalSessionEntry.session_metadata.interview_type` |
| `question_count` | `int` | Existing | Yes | — | `LongitudinalSessionEntry.session_metadata.question_count` |
| `knowledge_epoch` | `str` | Existing | Yes | — | `LongitudinalSessionEntry.session_metadata.knowledge_epoch` |
| `dimensional_scores` | `tuple[DimensionalScore, ...]` | Existing | Yes | `()` | Derived from `LongitudinalSessionEntry.profile_snapshot.features` |
| `mean_confidence` | `float` | Existing | Yes | `0.0` | `LongitudinalSessionEntry.profile_snapshot.mean_confidence` |
| `total_features` | `int` | Existing | Yes | `0` | `LongitudinalSessionEntry.profile_snapshot.total_feature_count` |
| `total_objectives` | `int` | Existing | Yes | `0` | From `LongitudinalSessionEntry.session_metadata.total_objectives` (resolved: OI-01). Source: `SessionHistory.knowledge_snapshot.coaching_snapshot.statistics.total_objectives`. |
| `total_narrative_insights` | `int` | Existing | Yes | `0` | From `LongitudinalSessionEntry.session_metadata.total_narrative_insights` (resolved: OI-02). Source: `SessionHistory.knowledge_snapshot.narrative.insight_count`. |
| `behavioral_scores` | `tuple[BehavioralScore, ...]` | **New** | Yes | `()` | Derived from `LongitudinalSessionEntry.profile_snapshot.features` |
| `language_ids_present` | `tuple[str, ...]` | **New** | Yes | `()` | From `language_capability_feature` entries in `profile_snapshot.features[*].provenance.language_context` |

**Resolution (OI-01, OI-02 — CLOSED):** `total_objectives` and `total_narrative_insights` are populated from `LongitudinalSessionMetadata` fields added in the pre-freeze update. Sources: `SessionHistory.knowledge_snapshot.coaching_snapshot.statistics.total_objectives` and `SessionHistory.knowledge_snapshot.narrative.insight_count` respectively. Both are accessible from the closed `SessionHistory` without LLM calls. `LearningProgressBuilder` reads these values from `LongitudinalSessionEntry.session_metadata` — no `SessionHistory[]` fallback required.

### 2.4 BehavioralTrend — Field Table

| Field | Python Type | Required | Default | Source |
|---|---|---|---|---|
| `candidate_identity_id` | `str` | Yes | — | `LongitudinalProfile.candidate_identity_id` |
| `feature_trends` | `tuple[FeatureTrend, ...]` | Yes | `()` | Derived per `feature_type_id` across all `session_snapshots` |
| `overall_trend_direction` | `str` | Yes | `"stable"` | Computed from `feature_trends`: majority direction, or `"insufficient_data"` |
| `sessions_analysed` | `int` | Yes | — | `LongitudinalProfile.session_count` |
| `schema_version` | `str` | Yes | `"1.0"` | Fixed |

**`overall_trend_direction` computation rule:** If `has_sufficient_data == False` (i.e., `session_count < 2`), value is `"insufficient_data"`. Otherwise: majority of `feature_trends[*].trend_direction` values (excluding `"insufficient_data"` entries); ties resolve to `"stable"`. This rule is a builder responsibility (Domain Contracts §2.6).

### 2.5 FeatureTrend — Field Table

| Field | Python Type | Required | Default | Source |
|---|---|---|---|---|
| `feature_type_id` | `str` | Yes | — | `ProfileFeature.feature_identity.feature_type_id` |
| `semantic_category` | `str` | Yes | — | `ProfileFeature.feature_identity.semantic_category` |
| `trend_direction` | `str` | Yes | `"stable"` | Computed by builder from `earliest_confidence` / `latest_confidence` |
| `earliest_confidence` | `float \| None` | No | `None` | From first session where feature appeared: `ProfileFeature.quality.confidence` |
| `latest_confidence` | `float \| None` | No | `None` | From most recent session where feature appeared: `ProfileFeature.quality.confidence` |
| `sessions_observed` | `int` | Yes | — | Count of sessions where this `feature_type_id` was present |

**Confidence source:** `ProfileFeature.quality.confidence` (from `FeatureQuality`). The `FeatureQuality` contract carries `confidence: float` — confirmed from the V1.2 feature layer.

### 2.6 BehavioralScore — Field Table

| Field | Python Type | Required | Default | Source |
|---|---|---|---|---|
| `feature_type_id` | `str` | Yes | — | `ProfileFeature.feature_identity.feature_type_id` |
| `semantic_category` | `str` | Yes | — | `ProfileFeature.feature_identity.semantic_category` |
| `confidence` | `float` | Yes | — | `ProfileFeature.quality.confidence` |
| `session_index` | `int` | Yes | — | `LongitudinalSessionEntry.interview_index` |

---

## 3. LanguageCapability — Persisted Structure and Aggregation Model

### 3.1 Persisted Structure

`CrossSessionLanguageCapability` is embedded within `LongitudinalProfile.language_capability_summary`. It is not separately persisted. Its storage lifecycle is identical to `LongitudinalProfile`.

### 3.2 Aggregation Model

Each `CrossSessionLanguageCapability` entry is produced by aggregating `ProfileFeature` values across sessions. The aggregation is cumulative: on each session update, the prior `CrossSessionLanguageCapability` for a given `language_id` is combined with the new session's signal.

**Aggregation inputs per session:**
From the new `CandidateProfileSnapshot.features`, select all `ProfileFeature` where:
- `feature_identity.feature_type_id == "language_capability_feature"`
- `provenance.language_context` is not `None`

For each such feature, `provenance.language_context` provides the `language_id`.

**Score extraction:** The `ProfileFeature.value` field carries a string representation of the capability level (e.g., `"HIGH"`, `"MODERATE"`, `"LOW"`). The `ProfileFeature.quality.confidence` field carries the numeric confidence. The specific mapping from `value`/`confidence` to `composite_score`, `idiomatic_usage_score`, and `type_error_rate` represents a data model gap: `ProfileFeature` does not natively carry structured `LanguageCapability` scores (composite/idiomatic/type-error) — those live on the session-scoped `LanguageCapability` contract.

**OI-03 — RESOLVED (pre-freeze investigation):**

`LanguageCapability` (`domain/contracts/language/language_capability.py`) is a **transient session-scoped object**. It is not embedded in `CandidateProfileSnapshot`, `KnowledgeSnapshot`, or `SessionHistory`. It is not persisted beyond session close. This was confirmed by codebase inspection: `LanguageCapability` appears only in `domain/contracts/language/` and has no presence in `domain/contracts/session_history/` or `domain/contracts/knowledge_snapshot/`.

**Resolution:** `language_capabilities: tuple[LanguageCapability, ...]` (default `()`) is added to `LongitudinalSessionMetadata` (Domain Contracts pre-freeze update). `longitudinal_update_node` receives the live session language capability data **before** the session state expires and passes it as an explicit input parameter to `LongitudinalProfileBuilder`. The builder embeds it in `LongitudinalSessionMetadata` at contribution time.

**No `SessionHistory` contract change is required.** `SessionHistory` v2.0 (ADR-033) is unchanged. Freeze Integrity Check on ADR-033 is **not** required.

`LongitudinalProfileBuilder` extracts `CrossSessionLanguageCapability` aggregates from `LongitudinalSessionMetadata.language_capabilities` (not from `ProfileFeature.provenance.language_context`). The `provenance.language_context` field remains a secondary confirmation source but is not the primary score extraction path.

### 3.3 Evolution Rules

| Rule | Description |
|---|---|
| EV-LC-01 | `CrossSessionLanguageCapability.schema_version` increments only on backward-incompatible field changes (same policy as `LongitudinalProfile`). |
| EV-LC-02 | Adding a new `language_id` is always valid (additive accumulation). No schema version required. |
| EV-LC-03 | Removing an existing `language_id` entry from `language_capability_summary` is never valid in V1.3. Once a language is accumulated, it persists in the profile. |
| EV-LC-04 | If `FeatureType.LANGUAGE_CAPABILITY` is extended or replaced, a new ADR is required before EPIC-02 implementation. |

---

## 4. Repository Payload Model

### 4.1 Persisted Artifact

The persistence layer stores exactly one artifact per candidate: `LongitudinalProfile`. The payload for a `save` operation is the complete serialized `LongitudinalProfile` object. The payload for a `get` operation returns `Optional[LongitudinalProfile]`.

**Serialized payload structure:**

```
LongitudinalProfile {
    candidate_identity_id: string           -- lookup key
    session_count: integer
    knowledge_epoch: string
    schema_version: string
    created_at: ISO8601-UTC-string
    last_updated_at: ISO8601-UTC-string
    metadata: {string: string}
    session_snapshots: [
        LongitudinalSessionEntry {
            session_id: string
            interview_index: integer        -- ordering key
            contributed_at: ISO8601-UTC-string
            profile_snapshot: CandidateProfileSnapshot { ... }  -- full embedded object
            session_metadata: LongitudinalSessionMetadata {
                role: string
                seniority: string
                interview_type: string
                question_count: integer
                session_language: string
                knowledge_epoch: string
                total_objectives: integer           -- from SessionHistory.knowledge_snapshot.coaching_snapshot.statistics.total_objectives
                total_narrative_insights: integer   -- from SessionHistory.knowledge_snapshot.narrative.insight_count
                language_capabilities: [LanguageCapability]  -- from live session state (not SessionHistory); empty if no coding questions
            }
        }
        ...
    ]
    language_capability_summary: [
        CrossSessionLanguageCapability {
            language_id: string
            session_count_in_language: integer
            total_questions_answered: integer
            mean_composite_score: number
            mean_idiomatic_score: number
            mean_type_error_rate: number
            trend_direction: string
            schema_version: string
        }
        ...
    ]
}
```

### 4.2 Query Model

| Operation | Input | Output | Notes |
|---|---|---|---|
| `get` | `candidate_identity_id: str` | `Optional[LongitudinalProfile]` | Returns `None` if no profile exists. |
| `save` | `LongitudinalProfile` | `None` | Replace-on-write. Idempotent for same `candidate_identity_id`. |
| `exists` | `candidate_identity_id: str` | `bool` | Used by `longitudinal_update_node` for gap detection. |

No batch operations, no pagination, no list queries in V1.3. The V2 analytics layer will extend this interface.

### 4.3 No Storage Technology Decision

The concrete storage technology (SQLite, JSON file, binary format) is not decided in this document. The payload model above is technology-agnostic: it describes the logical structure, not the physical representation. The infrastructure layer maps this logical structure to physical storage. The choice of storage technology must satisfy:

- Single-record-per-candidate semantics (replace-on-write).
- Serialization of `tuple[T, ...]` as ordered arrays.
- Serialization of `datetime` as ISO 8601 UTC strings.
- Deserialization back to `frozen=True` Pydantic instances.
- No JSON-level schema migration in V1.3 (schema version `"1.0"` only).

---

## 5. SessionHistory Contribution Mapping — Complete Traceability Table

Every field in the persisted `LongitudinalProfile` must be traceable to one or more `SessionHistory` fields, to a builder-computed value, or to a system constant. This table is the definitive traceability record.

| LongitudinalProfile field path | Source | Traceability |
|---|---|---|
| `candidate_identity_id` | `SessionHistory.candidate_identity_id` | Direct copy |
| `session_count` | Builder-computed | `len(assembled_session_snapshots)` |
| `knowledge_epoch` | `SessionHistory.knowledge_epoch` | Property: `session_history.knowledge_snapshot.knowledge_epoch` |
| `schema_version` | Builder constant | `"1.0"` |
| `created_at` | Builder-computed | UTC timestamp of first call; carried from `prior_profile.created_at` on subsequent calls |
| `last_updated_at` | Builder-computed | UTC timestamp of this call |
| `metadata` | Builder constant | `{}` in V1.3 |
| `session_snapshots[i].session_id` | `SessionHistory.session_id` | Direct copy |
| `session_snapshots[i].interview_index` | `SessionHistory.interview_index` | Direct copy |
| `session_snapshots[i].contributed_at` | Builder-computed | UTC timestamp of this contribution |
| `session_snapshots[i].profile_snapshot` | `SessionHistory.knowledge_snapshot.profile_snapshot` | Direct value copy (full `CandidateProfileSnapshot` embedded) |
| `session_snapshots[i].session_metadata.role` | `SessionHistory.interview_metadata.role` | Direct copy |
| `session_snapshots[i].session_metadata.seniority` | `SessionHistory.interview_metadata.seniority` | Direct copy |
| `session_snapshots[i].session_metadata.interview_type` | `SessionHistory.interview_metadata.interview_type` | Direct copy |
| `session_snapshots[i].session_metadata.question_count` | `SessionHistory.interview_metadata.question_count` | Direct copy |
| `session_snapshots[i].session_metadata.session_language` | `SessionHistory.interview_metadata.session_language` | Direct copy |
| `session_snapshots[i].session_metadata.knowledge_epoch` | `SessionHistory.knowledge_epoch` | Property copy |
| `session_snapshots[i].session_metadata.total_objectives` | `SessionHistory.knowledge_snapshot.coaching_snapshot.statistics.total_objectives` | Direct field read (OI-01 resolved) |
| `session_snapshots[i].session_metadata.total_narrative_insights` | `SessionHistory.knowledge_snapshot.narrative.insight_count` | Property read (OI-02 resolved) |
| `session_snapshots[i].session_metadata.language_capabilities` | Live session state (passed by `longitudinal_update_node`) | Not from `SessionHistory` — captured before session state expires (OI-03 resolved) |
| `language_capability_summary[j].language_id` | `session_metadata.language_capabilities[k].language_id` | From `LanguageCapability` instances embedded at contribution time |
| `language_capability_summary[j].session_count_in_language` | Builder-accumulated | Count of sessions contributing this `language_id` |
| `language_capability_summary[j].total_questions_answered` | `session_metadata.language_capabilities[k].questions_answered_in_language` | Running total (OI-02/OI-03 resolved) |
| `language_capability_summary[j].mean_composite_score` | `session_metadata.language_capabilities[k].composite_score` | Running mean (OI-03 resolved) |
| `language_capability_summary[j].mean_idiomatic_score` | `session_metadata.language_capabilities[k].idiomatic_usage_score` | Running mean (OI-03 resolved) |
| `language_capability_summary[j].mean_type_error_rate` | `session_metadata.language_capabilities[k].type_error_rate` | Running mean (OI-03 resolved) |
| `language_capability_summary[j].trend_direction` | Builder-computed | From composite score trend across sessions; `"insufficient_data"` when `session_count_in_language < 2` |
| `language_capability_summary[j].schema_version` | Builder constant | `"1.0"` |

**Traceability verdict:** All fields are fully traceable. OI-01 (`total_objectives`), OI-02 (`total_narrative_insights`), and OI-03 (`language_capabilities`) are all resolved. No field requires LLM calls or live computation. `language_capabilities` is the one field sourced from live session state rather than closed `SessionHistory` — this is architecturally correct: the data is captured at contribution time by `longitudinal_update_node` and embedded permanently in `LongitudinalSessionMetadata`. Once embedded, it is part of the closed `LongitudinalProfile` artifact and requires no live state for subsequent reads or reconstruction.

---

## 6. Replay Completeness Verification

### 6.1 Claim

`LongitudinalProfile` can be fully reconstructed from `SessionHistory[]` without LLM calls. This is the reconstruction guarantee mandated by ADR-034 Decision 3 and constitutional principle P-08.

### 6.2 Reconstruction Procedure

Given: ordered sequence `SessionHistory[]` for `candidate_identity_id`, ordered by `interview_index` ascending.

```
LongitudinalProfile reconstruction:
  prior_profile = None
  for session_history in sorted(SessionHistory[], by=interview_index):
      prior_profile = LongitudinalProfileBuilder(
          prior_profile=prior_profile,
          session_history=session_history,
          current_timestamp=session_history.created_at  (* determinism: use close time)
      ).build()
  return prior_profile  (* None if SessionHistory[] is empty)
```

Note: `current_timestamp` is set to `session_history.created_at` during reconstruction (not the actual `contributed_at` which may differ from a live run). This means `created_at` and `last_updated_at` will differ between a live profile and a reconstructed one. **This is acceptable**: these are audit timestamps, not semantically significant for any functional query. The knowledge content (snapshots, capability summary) is identical.

### 6.3 Replay Completeness Traceability Table

For each field of the reconstructed `LongitudinalProfile`, verify it is derivable from `SessionHistory` without LLM calls:

| Field | LLM required? | Deterministic? | Notes |
|---|---|---|---|
| `candidate_identity_id` | No | Yes | Direct from `SessionHistory.candidate_identity_id` |
| `session_count` | No | Yes | `len(SessionHistory[])` |
| `knowledge_epoch` | No | Yes | `SessionHistory[-1].knowledge_epoch` (last session) |
| `schema_version` | No | Yes | Constant `"1.0"` |
| `created_at` | No | Yes* | Uses `SessionHistory[0].created_at`; differs from live value if update timestamps differ |
| `last_updated_at` | No | Yes* | Uses `SessionHistory[-1].created_at`; differs from live value |
| `metadata` | No | Yes | Constant `{}` |
| `session_snapshots[i].*` | No | Yes | All fields derive from `SessionHistory[i]` fields directly |
| `profile_snapshot.*` | No | Yes | Verbatim copy from `SessionHistory[i].knowledge_snapshot.profile_snapshot` |
| `session_metadata.*` (base fields) | No | Yes | From `SessionHistory[i].interview_metadata` and `knowledge_epoch` |
| `session_metadata.total_objectives` | No | Yes | From `SessionHistory[i].knowledge_snapshot.coaching_snapshot.statistics.total_objectives` (OI-01 resolved) |
| `session_metadata.total_narrative_insights` | No | Yes | From `SessionHistory[i].knowledge_snapshot.narrative.insight_count` (OI-02 resolved) |
| `session_metadata.language_capabilities` | No | **No*** | *Reconstruction gap: `LanguageCapability` is transient — not in `SessionHistory`. Reconstructed profile will have `language_capabilities = ()` for all sessions, causing `language_capability_summary = []`. See reconstruction note below. |
| `language_capability_summary[j].*` | No | **Partial** | Reconstructable only if `language_capabilities` is reconstructable (see above) |

**Reconstruction verdict:** `LongitudinalProfile` is **substantially reconstructable** from `SessionHistory[]` without LLM calls. All knowledge fields (`profile_snapshot`, session metadata, `total_objectives`, `total_narrative_insights`) are reconstructable. Timestamps differ from live values (acceptable — audit fields only).

**Reconstruction gap — `language_capability_summary`:** `LanguageCapability` is a transient object not persisted in `SessionHistory`. A profile reconstructed from `SessionHistory[]` will have `language_capability_summary = []` (empty). This means language capability trend data is **not reconstructable** from `SessionHistory` alone — it requires the original `LongitudinalProfile` persistence. If the profile is lost and reconstructed, language capability trend history is lost.

**Mitigation:** This gap is acceptable in V1.3 for two reasons: (1) `LanguageCapability` trend data is supplementary — its loss does not affect core knowledge scoring or behavioral trend data; (2) in V1.3 there is no production persistence layer with real data. If language capability reconstruction becomes a V2 requirement, `LanguageCapability` persistence in `SessionHistory` or `KnowledgeSnapshot` can be added via a new ADR.

**Domain invariant I-LP-REC (amended):** `LongitudinalProfile` for any candidate is reconstructable from their ordered `SessionHistory[]` for all fields **except** `language_capability_summary` (which will be empty in a reconstructed profile). This limitation is accepted for V1.3. The architectural test (EPIC-02 success criterion §12.8) must verify reconstruction completeness for all reconstructable fields and explicitly assert `language_capability_summary == []` for a reconstructed profile.

---

## 7. Serialization Rules — Complete Specification

### 7.1 Format

The serialization format for `LongitudinalProfile` is **JSON**. JSON is chosen because:
- All V1.2 persistent artifacts (`SessionHistory`) use JSON-serializable Pydantic models.
- Pydantic v2 provides native JSON serialization with `model.model_dump_json()` / `model.model_validate_json()`.
- Debuggable without tooling.
- Compatible with SQLite (JSON column or TEXT column) and file-based storage.

The concrete persistence format (column type, file encoding, etc.) is left to the infrastructure layer. The domain layer only specifies that the serialization round-trip must be lossless.

### 7.2 Tuples

All `tuple[T, ...]` fields serialize as JSON arrays. Deserializing a JSON array into a `tuple[T, ...]` is handled by Pydantic v2 natively. The ordering of elements in the serialized array must be preserved on deserialization.

### 7.3 Enums and Enum-like Strings

EPIC-02 does not introduce new `Enum` types. `trend_direction` is serialized as a plain string (one of `"improving"`, `"declining"`, `"stable"`, `"insufficient_data"`). No enum binding is required for this field. Deserialization validates against the allowed set via Pydantic field validator.

### 7.4 Datetime

All `datetime` fields serialize as ISO 8601 strings with UTC timezone designator:
- Format: `YYYY-MM-DDTHH:MM:SS.ssssssZ` (microsecond precision, `Z` suffix).
- Pydantic v2 with `model_config = {"ser_json_timedelta": "iso8601"}` is consistent with this format.
- Deserialized `datetime` instances must be timezone-aware (`tzinfo = UTC`). Naive datetimes are a validation error.

### 7.5 Optional Values

Fields typed `T | None` serialize as JSON `null` when `None`. Deserialization of JSON `null` produces `None`. Fields with `default=None` are omitted from serialization only when explicitly configured (Pydantic `exclude_none` is **not** set by default — all fields including `null` values are serialized to preserve schema completeness).

### 7.6 Schema Version Compatibility Rules

| Rule | Description |
|---|---|
| SR-01 | A serialized record with `schema_version == "1.0"` must deserialize without error into the V1.3 `LongitudinalProfile` model. |
| SR-02 | A serialized record with an unknown `schema_version` must be rejected with a structured error (not silently ignored). |
| SR-03 | Adding an optional field with a safe default to the Pydantic model does not require a `schema_version` increment (Pydantic v2 applies defaults for missing fields on deserialization). |
| SR-04 | Removing a field from the Pydantic model when `extra=forbid` is set will cause deserialization failure for records that carry the removed field. This constitutes a breaking change and requires a version increment. |
| SR-05 | `extra=forbid` is set on all contracts in this specification. Unknown fields in a serialized record raise a validation error. This is intentional: it prevents silent data loss and forces explicit schema evolution. |

### 7.7 Nested Object Serialization

`CandidateProfileSnapshot` and `ProfileFeature` (which contains `FeatureIdentity`, `FeatureProvenance`, `FeatureQuality`) are serialized as nested JSON objects. Pydantic v2 handles nested model serialization natively. No custom serializer is required for these types.

`FeatureProvenance.language_context: str | None` serializes as a JSON string or `null`. When `null`, the language context is absent (non-coding session or no language feature). When a string, it carries the `language_id`.

### 7.8 Forward Compatibility

`metadata: dict[str, str]` on `LongitudinalProfile` is the forward compatibility slot. Future minor extensions may add structured information to `metadata` keys without changing `schema_version`. This mechanism is intentionally limited to `dict[str, str]` — no nested objects, no typed values. If a structured extension requires typed fields, a formal field addition (with optional default) is required.

---

## 8. Cross-Contract Validation

### 8.1 ADR-034 — Data Model Consistency Check

| ADR-034 Decision | Data Model Compliant? | Notes |
|---|---|---|
| Decision 1: sole producer `LongitudinalProfileBuilder` | Yes | Builder is the only component that produces `LongitudinalProfile` instances. |
| Decision 1: sole writer `longitudinal_update_node` | Yes | Repository `save` called only by `longitudinal_update_node`. |
| Decision 1: `LongitudinalProfile` not in `InterviewState` | Yes | No `InterviewState` field defined for `LongitudinalProfile`. |
| Decision 2: replace-on-write semantics | Yes | Persistence payload model §4.1 specifies single-record-per-candidate with replace. |
| Decision 2: `schema_version = "1.0"` initial | Yes | All contracts carry `schema_version = "1.0"`. |
| Decision 2: ADR-033 review trigger resolved | Yes | `ScoringSnapshot` not embedded in `LongitudinalProfile` (§1.1 field table). |
| Decision 3: `SessionHistory` as source of truth | Yes | All fields traceable to `SessionHistory` in §5. |
| Decision 4: `candidate_identity_id` as opaque anchor | Yes | Field is `str`, no typed reference to external identity system. |
| Decision 5: `LearningProgress` from `LongitudinalProfile` | Yes | `SessionProgressEntry` source changed to `LongitudinalProfile.session_snapshots`. |
| Decision 5: no `SessionHistory[]` fallback | Yes | No `SessionHistory` input in `LearningProgressBuilder` data model. Empty `LearningProgress` returned when profile absent. |
| Decision 6: non-fatal failure semantics | Yes | Data model does not affect failure path; this is a node implementation concern. |
| Decision 7: replay isolation | Yes | No replay contracts referenced in any EPIC-02 artifact. |
| Decision 8: repository interface in domain layer | Yes | §4.2 specifies repository query model at domain level only; no infrastructure technology specified. |
| Decision 9: LP-01 through LP-12 invariants | Yes | All 12 invariants traceable to §5 field traceability, §6 reconstruction, §7 serialization. |

### 8.2 Domain Contracts — Data Model Consistency Check

| Domain Contract requirement | Data Model compliant? | Notes |
|---|---|---|
| `LongitudinalProfile` `frozen=True`, `extra=forbid` | Yes | Specified in §1.1. |
| `session_count == len(session_snapshots)` (LP-V-01) | Yes | Persisted as a field; validated by builder. |
| All `interview_index` unique (LP-V-03) | Yes | Uniqueness enforced by idempotency guard in builder. |
| `session_snapshots` ordered by `interview_index` ascending (LP-V-04) | Yes | Ordering enforced by builder assembly; preserved in serialized array. |
| `last_updated_at >= created_at` (LP-V-06) | Yes | Builder sets both; constraint enforced by validator. |
| `LearningProgress` never persisted (LP-LP-06) | Yes | §2.1 explicitly states no storage data model for `LearningProgress`. |
| `FeatureProvenance.language_context` field name | **CONFIRMED** | Field exists (line 45 of `feature_provenance.py`). Domain Contracts §3.2 reference is correct. |
| `total_objectives` / `total_narrative_insights` gap | **CLOSED** | OI-01 / OI-02 resolved: fields added to `LongitudinalSessionMetadata`; sources confirmed in `SessionHistory.knowledge_snapshot`. |
| `language_capabilities` source gap | **CLOSED** | OI-03 resolved: `LanguageCapability` is transient; captured from live session by `longitudinal_update_node`; embedded in `LongitudinalSessionMetadata`; no `SessionHistory` change required. Reconstruction gap accepted (§6). |

### 8.3 Resolved Pre-Freeze Issues

All pre-freeze open issues are closed. No further issues require resolution before Architecture Freeze.

| # | Issue | Status | Resolution Summary |
|---|---|---|---|
| OI-01 | `total_objectives` and `total_narrative_insights` not derivable from `LongitudinalProfile` alone | **CLOSED** | Added to `LongitudinalSessionMetadata` with safe defaults (`0`). Sources: `coaching_snapshot.statistics.total_objectives` and `narrative.insight_count` — both available in closed `SessionHistory`. No ADR. No version increment. |
| OI-02 | Same as OI-01 (tracking item for `total_narrative_insights` specifically) | **CLOSED** | Merged with OI-01 resolution. |
| OI-03 | `LanguageCapability` accessibility from `SessionHistory` | **CLOSED** | `LanguageCapability` is transient (not in any closed artifact). Captured from live session by `longitudinal_update_node`. No `SessionHistory` change. Freeze Integrity Check on ADR-033 **not required**. Reconstruction gap accepted for V1.3 (`language_capability_summary = []` in reconstructed profiles). |

---

*This document is the frozen data model specification for EPIC-02. All open issues (§8.3) must be resolved and this document updated before Architecture Freeze is declared. Any change to this document after Architecture Freeze requires a Freeze Integrity Check per V13-DEVELOPMENT-PLAYBOOK.md §9.*

*Revision 2026-07-14: Initial frozen draft. `FeatureProvenance.language_context` confirmed (line 45, `feature_provenance.py`). Three open issues identified (OI-01, OI-02, OI-03).*

*Revision 2026-07-14 (pre-freeze update): OI-01 resolved — `total_objectives`, `total_narrative_insights` added to `LongitudinalSessionMetadata`; sources confirmed in `SessionHistory.knowledge_snapshot`. OI-02 resolved — merged with OI-01. OI-03 resolved — `LanguageCapability` is transient; captured from live session by node; no `SessionHistory` change; Freeze Integrity Check on ADR-033 not required. Reconstruction gap documented for `language_capability_summary` (accepted for V1.3). All open issues closed. Architecture Freeze may now be declared.*
