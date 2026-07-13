# EPIC-02 — Domain Contracts Specification

**Status:** FROZEN  
**Epic ID:** EPIC-V13-02  
**Date:** 2026-07-14  
**Precondition:** ADR-034 accepted; EPIC-02-LONGITUDINAL-PROFILE.md frozen.  
**Authority:** This document specifies the complete domain contract field sets, validation invariants, ownership, and lifecycle for all artifacts introduced or modified by EPIC-02. Implementation must not begin until this document and the Data Model Specification are both frozen and Architecture Freeze is declared.

---

## 1. LongitudinalProfile

### 1.1 Role and Scope

`LongitudinalProfile` is the authoritative cross-session accumulation record for a candidate. It is a persistent, candidate-scoped, immutable-at-instantiation artifact. It is not a session artifact, not a report, and not a progress view.

**Governing decisions:** ADR-034 Decisions 1, 2, 8; EPIC-02-LONGITUDINAL-PROFILE.md §§3, 7, 9.

### 1.2 Ownership

| Role | Owner |
|---|---|
| Sole producer | `LongitudinalProfileBuilder` |
| Sole writer (runtime) | `longitudinal_update_node` |
| Persistence | `LongitudinalProfileRepository` (infrastructure layer) |
| Declared readers | `LearningProgressBuilder`, `ProgressTracker`, Unified Report layer (EPIC-05) |

No reader may mutate `LongitudinalProfile`. Direct Pydantic instantiation in production code is prohibited (test layer only).

### 1.3 Complete Field Inventory

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `candidate_identity_id` | `str` | Yes | — | `min_length=1` | Owning candidate (ADR-016A). Immutable. Must match all embedded `CandidateProfileSnapshot.candidate_identity_id`. |
| `session_snapshots` | `tuple[LongitudinalSessionEntry, ...]` | Yes | — | Ordered by `interview_index` ascending; no duplicate `interview_index` values | Ordered accumulation of per-session contributions. One entry per closed session. |
| `session_count` | `int` | Yes | — | `ge=0`; must equal `len(session_snapshots)` | Derived count — validated by `LongitudinalProfileBuilder`. |
| `language_capability_summary` | `tuple[CrossSessionLanguageCapability, ...]` | Yes | `()` | One entry per distinct `language_id`; no duplicates | Accumulated cross-session language capability; empty if no coding sessions. |
| `knowledge_epoch` | `str` | Yes | `"1"` | `min_length=1` | Platform knowledge epoch at last update (ADR-022 §I). Carries the epoch of the most recent session. |
| `schema_version` | `str` | Yes | `"1.0"` | `min_length=1` | Set by `LongitudinalProfileBuilder`; immutable after construction. Versioning policy: ADR-034 Decision 2. |
| `created_at` | `datetime` | Yes | — | UTC | Timestamp of initial creation (first session). Immutable once set. |
| `last_updated_at` | `datetime` | Yes | — | UTC; `last_updated_at >= created_at` | Timestamp of most recent successful update. Set by `LongitudinalProfileBuilder` on each replacement. |
| `metadata` | `dict[str, str]` | No | `{}` | Reserved extensibility slot | Forward-compatibility metadata. Not interpreted by V1.3. |

**Model configuration:** `frozen=True`, `extra=forbid`.

### 1.4 LongitudinalSessionEntry

Each entry in `session_snapshots` represents one closed session's contribution.

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `session_id` | `str` | Yes | — | `min_length=1` | Source `SessionHistory.session_id`. Unique within the profile. |
| `interview_index` | `int` | Yes | — | `ge=0` | Source `SessionHistory.interview_index`. Unique within the profile. Primary ordering key. |
| `profile_snapshot` | `CandidateProfileSnapshot` | Yes | — | `candidate_identity_id` must match parent | The closed knowledge snapshot for this session. |
| `session_metadata` | `LongitudinalSessionMetadata` | Yes | — | — | Session configuration captured at contribution time. |
| `contributed_at` | `datetime` | Yes | — | UTC | Timestamp when this entry was added to the profile. |

**Model configuration:** `frozen=True`, `extra=forbid`.

### 1.5 LongitudinalSessionMetadata

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `role` | `str` | Yes | — | `min_length=1` | Role title from `SessionHistory.interview_metadata.role`. |
| `seniority` | `str` | Yes | — | `min_length=1` | Seniority from `SessionHistory.interview_metadata.seniority`. |
| `interview_type` | `str` | Yes | — | `min_length=1` | Interview type from `SessionHistory.interview_metadata.interview_type`. |
| `question_count` | `int` | Yes | — | `ge=0` | Question count from `SessionHistory.interview_metadata.question_count`. |
| `session_language` | `str` | Yes | — | `min_length=1` | UI language from `SessionHistory.interview_metadata.session_language`. |
| `knowledge_epoch` | `str` | Yes | — | `min_length=1` | Knowledge epoch from `SessionHistory.knowledge_epoch`. |
| `total_objectives` | `int` | Yes | `0` | `ge=0` | Count of `CoachingAction` objectives from `SessionHistory.knowledge_snapshot.coaching_snapshot.statistics.total_objectives`. Enables `SessionProgressEntry.total_objectives` without re-reading `SessionHistory`. |
| `total_narrative_insights` | `int` | Yes | `0` | `ge=0` | Count of `NarrativeInsight` items from `SessionHistory.knowledge_snapshot.narrative.insight_count` (property). Enables `SessionProgressEntry.total_narrative_insights` without re-reading `SessionHistory`. |
| `language_capabilities` | `tuple[LanguageCapability, ...]` | Yes | `()` | One entry per distinct `language_id`; `LanguageCapability` is immutable (`frozen=True`). | Session-scoped `LanguageCapability` instances captured at contribution time. Source: passed by `longitudinal_update_node` from live `InterviewState` before session close (see §3.2 — OI-03 resolved). Empty for sessions with no coding questions. |

**Model configuration:** `frozen=True`, `extra=forbid`.

**Import note:** `LongitudinalSessionMetadata` imports `LanguageCapability` from `domain.contracts.language.language_capability`. This is a domain-to-domain import within the contracts layer — no architectural boundary is crossed.

### 1.6 CrossSessionLanguageCapability

Accumulated cross-session `LanguageCapability` for one language. Replaces the session-scoped `LanguageCapability` with a longitudinal view.

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `language_id` | `str` | Yes | — | `min_length=1` | Language identifier (ADR-019). Unique within `language_capability_summary`. |
| `session_count_in_language` | `int` | Yes | — | `ge=1` | Number of sessions in which this language appeared. |
| `total_questions_answered` | `int` | Yes | — | `ge=0` | Total coding questions answered in this language across all sessions. |
| `mean_composite_score` | `float` | Yes | — | `ge=0.0, le=1.0` | Mean of `LanguageCapability.composite_score` across contributing sessions. |
| `mean_idiomatic_score` | `float` | Yes | — | `ge=0.0, le=1.0` | Mean of `LanguageCapability.idiomatic_usage_score` across contributing sessions. |
| `mean_type_error_rate` | `float` | Yes | — | `ge=0.0, le=1.0` | Mean of `LanguageCapability.type_error_rate` across contributing sessions. |
| `trend_direction` | `str` | Yes | `"stable"` | One of: `"improving"`, `"declining"`, `"stable"`, `"insufficient_data"` | Direction of composite score trend across sessions. `"insufficient_data"` when `session_count_in_language < 2`. |
| `schema_version` | `str` | Yes | `"1.0"` | `min_length=1` | Schema version for forward compatibility. |

**Model configuration:** `frozen=True`, `extra=forbid`.

**LanguageCapability activation rule:** `CrossSessionLanguageCapability` is the V1.3 activation of the `LanguageCapability` reserved concept. It is produced by `LongitudinalProfileBuilder` by aggregating `LanguageCapability` values extracted from `CandidateProfileSnapshot.features` where `feature_identity.feature_type_id == "language_capability_feature"`. Sessions with no coding questions contribute no entries to `language_capability_summary`.

### 1.7 Validation Invariants

| ID | Rule |
|---|---|
| LP-V-01 | `session_count == len(session_snapshots)` — enforced by `LongitudinalProfileBuilder.build()` validator. |
| LP-V-02 | All `LongitudinalSessionEntry.profile_snapshot.candidate_identity_id` values equal `LongitudinalProfile.candidate_identity_id`. |
| LP-V-03 | All `LongitudinalSessionEntry.interview_index` values are unique within `session_snapshots`. |
| LP-V-04 | `session_snapshots` is ordered by `interview_index` ascending. |
| LP-V-05 | All `CrossSessionLanguageCapability.language_id` values are unique within `language_capability_summary`. |
| LP-V-06 | `last_updated_at >= created_at`. |
| LP-V-07 | `knowledge_epoch` equals the `knowledge_epoch` of the `LongitudinalSessionEntry` with the highest `interview_index`. |
| LP-V-08 | If `session_count == 0`, `language_capability_summary` is empty. A `LongitudinalProfile` with zero sessions is never persisted (first-session path always produces exactly one entry). |

### 1.8 Lifecycle

| Phase | State |
|---|---|
| Does not exist | Before first session for this `candidate_identity_id` |
| Created | After first session: one `LongitudinalSessionEntry`; `session_count = 1` |
| Replaced | After each subsequent session: new `LongitudinalProfile` instance; prior superseded in persistence |
| Read-only | At progress query time, report render time; never written by readers |

---

## 2. LearningProgress

### 2.1 Role and Scope

`LearningProgress` is a derived, read-only, never-persisted cross-session progress view. It is computed on demand from `LongitudinalProfile` (ADR-034 Decision 5). It is not a persistence artifact.

**Governing decisions:** ADR-034 Decision 5; EPIC-02-LONGITUDINAL-PROFILE.md §§3, 7.

### 2.2 Ownership

| Role | Owner |
|---|---|
| Sole creation path | `LearningProgressBuilder` |
| Input source | `LongitudinalProfile` (ADR-034 Decision 5 — replaces prior `SessionHistory[]` source) |
| Readers | `ProgressTracker`, Unified Report layer (EPIC-05) |

`LearningProgress` is never persisted. Every call to `LearningProgressBuilder.build(profile)` produces a fresh instance.

### 2.3 Modified Field Inventory

The existing `LearningProgress` contract carries: `candidate_identity_id`, `session_entries: tuple[SessionProgressEntry, ...]`, `schema_version`, `computed_at`, `knowledge_epoch`, `metadata`.

EPIC-02 **adds** the following fields to `LearningProgress`:

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `behavioral_trend` | `BehavioralTrend` | Yes | — | — | Cross-session behavioral feature trend summary. Derived from `LongitudinalProfile.session_snapshots`. |
| `language_capability_summary` | `tuple[CrossSessionLanguageCapability, ...]` | Yes | `()` | Propagated from `LongitudinalProfile.language_capability_summary` | Language capability trend; empty if no coding sessions. |
| `has_sufficient_data` | `bool` | Yes | — | `True` when `session_count >= 2` | Whether trend analysis is valid. `False` suppresses trend panels in the UI. |

**Invariant on source:** `LearningProgressBuilder` reads exclusively from `LongitudinalProfile`. It must not read `SessionHistory[]` under any code path (ADR-034 Decision 5). If `LongitudinalProfile` is absent, the builder returns an empty `LearningProgress` with `has_sufficient_data = False` and `session_entries = ()`.

**Existing fields unchanged:** `candidate_identity_id`, `session_entries`, `schema_version`, `computed_at`, `knowledge_epoch`, `metadata` carry their current definitions. `session_entries` is now derived from `LongitudinalProfile.session_snapshots` rather than `SessionHistory[]`.

### 2.4 Modified SessionProgressEntry

`SessionProgressEntry` is extended with the following fields:

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `behavioral_scores` | `tuple[BehavioralScore, ...]` | Yes | `()` | One entry per `feature_type_id` present in the session's `CandidateProfileSnapshot` | Behavioral dimension scores for this session. |
| `language_ids_present` | `tuple[str, ...]` | Yes | `()` | Language IDs of coding questions answered | Empty if no coding questions. |

**Existing fields unchanged:** `session_id`, `session_index`, `created_at`, `role`, `seniority`, `interview_type`, `question_count`, `knowledge_epoch`, `dimensional_scores`, `mean_confidence`, `total_features`, `total_objectives`, `total_narrative_insights`.

### 2.5 BehavioralTrend

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `candidate_identity_id` | `str` | Yes | — | `min_length=1` | Owning candidate. |
| `feature_trends` | `tuple[FeatureTrend, ...]` | Yes | `()` | One entry per `feature_type_id` observed across sessions | Per-dimension trend across sessions. |
| `overall_trend_direction` | `str` | Yes | `"stable"` | One of: `"improving"`, `"declining"`, `"stable"`, `"insufficient_data"` | Composite trend direction. `"insufficient_data"` when `session_count < 2`. |
| `sessions_analysed` | `int` | Yes | — | `ge=0` | Number of sessions used to compute this trend. |
| `schema_version` | `str` | Yes | `"1.0"` | `min_length=1` | — |

**Model configuration:** `frozen=True`, `extra=forbid`.

### 2.6 FeatureTrend

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `feature_type_id` | `str` | Yes | — | `min_length=1` | Stable cross-session key (ADR-020 §F). |
| `semantic_category` | `str` | Yes | — | `min_length=1` | Human-readable category from `FeatureIdentity`. |
| `trend_direction` | `str` | Yes | `"stable"` | One of: `"improving"`, `"declining"`, `"stable"`, `"insufficient_data"` | Direction of confidence trend for this feature. |
| `earliest_confidence` | `float` | No | `None` | `ge=0.0, le=1.0` if present | Confidence from the first session where this feature appeared. |
| `latest_confidence` | `float` | No | `None` | `ge=0.0, le=1.0` if present | Confidence from the most recent session where this feature appeared. |
| `sessions_observed` | `int` | Yes | — | `ge=1` | Number of sessions where this feature was present. |

**Model configuration:** `frozen=True`, `extra=forbid`.

**Trend direction rule:** `"improving"` when `latest_confidence > earliest_confidence + 0.05`; `"declining"` when `latest_confidence < earliest_confidence - 0.05`; `"stable"` otherwise. `"insufficient_data"` when `sessions_observed < 2`. This rule is applied by `LearningProgressBuilder` — it is not a domain invariant, it is a builder responsibility.

### 2.7 BehavioralScore

| Field | Type | Required | Default | Constraints | Description |
|---|---|---|---|---|---|
| `feature_type_id` | `str` | Yes | — | `min_length=1` | Stable feature key (ADR-020 §F). |
| `semantic_category` | `str` | Yes | — | `min_length=1` | Human-readable category. |
| `confidence` | `float` | Yes | — | `ge=0.0, le=1.0` | Feature confidence at this session's closure. |
| `session_index` | `int` | Yes | — | `ge=0` | Source session `interview_index`. |

**Model configuration:** `frozen=True`, `extra=forbid`.

### 2.8 Validation Invariants

| ID | Rule |
|---|---|
| LP-LP-01 | `LearningProgress.session_entries` length equals `LongitudinalProfile.session_count` when derived from a non-empty profile. |
| LP-LP-02 | `session_entries` is ordered by `session_index` ascending. |
| LP-LP-03 | `has_sufficient_data == (len(session_entries) >= 2)`. |
| LP-LP-04 | `BehavioralTrend.sessions_analysed == len(session_entries)`. |
| LP-LP-05 | All `FeatureTrend.feature_type_id` values within `BehavioralTrend.feature_trends` are unique. |
| LP-LP-06 | `LearningProgress` is never persisted. Any persistence of `LearningProgress` to any store is a violation. |
| LP-LP-07 | `LearningProgressBuilder` accepts only `LongitudinalProfile` as its input. Accepting `SessionHistory[]` is a violation (ADR-034 Decision 5). |

### 2.9 Lifecycle

`LearningProgress` is computed on demand. It has no persistence lifecycle. It is produced at:
- Report render time (Unified Report progress panel — EPIC-05).
- Progress view query time.
- Any consumer that requests a current progress snapshot.

Each production is independent. There is no caching of `LearningProgress` in V1.3.

---

## 3. LanguageCapability — Cross-Session Activation

### 3.1 Current State (V1.2)

`LanguageCapability` (in `domain/contracts/language/language_capability.py`) is session-scoped. It carries: `language_id`, `questions_answered_in_language`, `composite_score`, `idiomatic_usage_score`, `type_error_rate`, `schema_version`. It represents a candidate's language capability **within one session**.

In V1.2, `LanguageCapability` is derived from evaluation signals for coding questions and associated with `FeatureType.LANGUAGE_CAPABILITY` (`feature_type_id = "language_capability_feature"`) in the `ProfileFeature` layer.

### 3.2 Activation in EPIC-02

EPIC-02 activates `LanguageCapability` for cross-session accumulation. This activation does not modify the existing `LanguageCapability` contract — it adds the cross-session view via `CrossSessionLanguageCapability` (specified in §1.6).

**OI-03 resolution (pre-freeze investigation):** `LanguageCapability` is a transient session-scoped object. It is **not** embedded in `KnowledgeSnapshot`, `SessionHistory`, or any closed artifact. It exists only in `domain/contracts/language/language_capability.py` and is produced during the live session. It is not persisted beyond session close. Therefore, `LongitudinalProfileBuilder` cannot extract `LanguageCapability` instances from `SessionHistory` alone.

**Resolution:** `LanguageCapability` instances are captured in `LongitudinalSessionMetadata.language_capabilities` at contribution time. `longitudinal_update_node` receives the live `InterviewState` language capability data (available in session state before or at close) and passes it to `LongitudinalProfileBuilder` as part of the `session_history` contribution. Specifically, `longitudinal_update_node` reads `LanguageCapability` instances from the session and embeds them in the builder input before the live state expires. The builder receives them as part of the `LongitudinalSessionMetadata` assembly.

**No `SessionHistory` contract change is required.** `LanguageCapability` is captured by the `longitudinal_update_node` from the live session, not from the closed `SessionHistory`. This preserves the `SessionHistory` v2.0 contract (ADR-033).

**Activation rules:**

- `CrossSessionLanguageCapability` aggregate scores (`mean_composite_score`, `mean_idiomatic_score`, `mean_type_error_rate`, `total_questions_answered`) are derived from `LongitudinalSessionMetadata.language_capabilities` embedded at contribution time.
- The `language_id` for each `CrossSessionLanguageCapability` entry is the `LanguageCapability.language_id` field (consistent with ADR-019).
- A session contributes a language entry to `CrossSessionLanguageCapability` only when `LongitudinalSessionMetadata.language_capabilities` is non-empty for that session.
- Sessions with no coding questions produce an empty `language_capabilities` tuple and contribute no entries.
- `ProfileFeature.provenance.language_context` remains the secondary confirmation source (consistent with ADR-018 §L) but is not the primary extraction path for scores.

### 3.3 Ownership

| Role | Owner |
|---|---|
| Session-scoped `LanguageCapability` producer | `FeatureEngine` (unchanged from V1.2) |
| Cross-session aggregation | `LongitudinalProfileBuilder` — reads from `CandidateProfileSnapshot.features` and produces `CrossSessionLanguageCapability` entries |
| `language_capability_summary` writer | `longitudinal_update_node` (via `LongitudinalProfileBuilder`) |

The existing `LanguageCapability` contract (`domain/contracts/language/language_capability.py`) is **not modified** by EPIC-02.

### 3.4 Validation Invariants

| ID | Rule |
|---|---|
| LC-V-01 | Each `CrossSessionLanguageCapability.language_id` within `LongitudinalProfile.language_capability_summary` is unique. |
| LC-V-02 | `session_count_in_language >= 1` for every `CrossSessionLanguageCapability` entry. |
| LC-V-03 | `trend_direction == "insufficient_data"` when `session_count_in_language < 2`. |
| LC-V-04 | `0.0 <= mean_composite_score <= 1.0`, `0.0 <= mean_idiomatic_score <= 1.0`, `0.0 <= mean_type_error_rate <= 1.0`. |
| LC-V-05 | `language_id` references a registered `ProgrammingLanguage` (ADR-019 I-20). This constraint is validated at `LongitudinalProfileBuilder.build()` time. |

### 3.5 Lifecycle

`CrossSessionLanguageCapability` is embedded in `LongitudinalProfile`. It follows the same lifecycle as `LongitudinalProfile` (§1.8): created on first session with coding content; updated on each subsequent session that contributes a language capability signal.

---

## 4. LongitudinalProfileBuilder — Responsibilities

### 4.1 Governing Principle

`LongitudinalProfileBuilder` is a pure assembly component (P-05: Builders Assemble; Engines Compute). It holds no business logic. It applies no scoring, derivation, or LLM invocation. Its sole responsibility is to collect pre-computed inputs and construct a valid, immutable `LongitudinalProfile`.

### 4.2 Mandatory Inputs

| Input | Type | Required | Source |
|---|---|---|---|
| `prior_profile` | `Optional[LongitudinalProfile]` | No | Persistence layer (via `longitudinal_update_node`). `None` for first-session path. |
| `session_history` | `SessionHistory` | Yes | `InterviewState.session_history` (closed). |
| `language_capabilities` | `tuple[LanguageCapability, ...]` | Yes | Passed by `longitudinal_update_node` from live session state (resolved: OI-03). Default `()`. |
| `current_timestamp` | `datetime` | Yes | UTC timestamp of this invocation. |

The builder does not call the persistence layer. It does not read `InterviewState` directly. It receives pre-fetched inputs from `longitudinal_update_node`. The `language_capabilities` parameter is provided by the node from the session's language evaluation data before the live session state expires.

### 4.3 Responsibilities

1. **Validate inputs:** Confirm `session_history.candidate_identity_id` matches `prior_profile.candidate_identity_id` (if prior profile is not `None`). Raise `ValueError` if mismatch.

2. **Guard idempotency:** If `prior_profile` already contains an entry for `session_history.interview_index`, return `prior_profile` unchanged. Emit no error — this is a no-op path (LP-07 invariant).

3. **Assemble `LongitudinalSessionEntry`:** Extract `profile_snapshot` from `session_history.knowledge_snapshot.profile_snapshot`. Extract `session_metadata` fields from `session_history.interview_metadata` plus: `total_objectives` from `session_history.knowledge_snapshot.coaching_snapshot.statistics.total_objectives`; `total_narrative_insights` from `session_history.knowledge_snapshot.narrative.insight_count`; `language_capabilities` from the `language_capabilities` input parameter. Set `contributed_at = current_timestamp`.

4. **Assemble `session_snapshots`:** Append new `LongitudinalSessionEntry` to prior `session_snapshots` (or initialize from empty tuple). Sort by `interview_index` ascending.

5. **Aggregate `language_capability_summary`:** For each `LanguageCapability` in the `language_capabilities` input parameter, use `language_id` as the key. Merge into the prior `language_capability_summary`: create new entry if `language_id` is not present; update existing entry by recalculating running means (`mean_composite_score`, `mean_idiomatic_score`, `mean_type_error_rate`), incrementing `session_count_in_language`, incrementing `total_questions_answered`, and recalculating `trend_direction`. Apply invariant LC-V-03 for trend direction. If `language_capabilities` is empty, `language_capability_summary` is unchanged (no new entries added).

6. **Set `knowledge_epoch`:** Equal to `session_history.knowledge_epoch`.

7. **Set timestamps:** `created_at = prior_profile.created_at` if prior profile exists, else `current_timestamp`. `last_updated_at = current_timestamp`.

8. **Compute `session_count`:** `len(assembled_session_snapshots)`.

9. **Set `schema_version`:** `"1.0"`.

10. **Validate and construct:** Apply all invariants from §1.7 and §3.4 before returning. Raise `ValueError` with a descriptive message on any invariant violation.

### 4.4 What the Builder Must Never Do

- Call `LongitudinalProfileRepository` or any persistence layer.
- Call any LLM-backed service, `FeatureEngine`, `NarrativeGenerator`, or `KnowledgePipeline`.
- Read `InterviewState` directly.
- Apply scoring logic, weighting, or conditional derivation beyond the prescribed `trend_direction` rule (§2.6).
- Produce any artifact other than `LongitudinalProfile`.

---

## 5. Interview Contribution Model

### 5.1 Contribution Unit

A single `SessionHistory` contributes to `LongitudinalProfile` exactly once, at the moment `longitudinal_update_node` executes after session close. The contribution is atomic: either the full session contributes, or it does not contribute at all (failure semantics: ADR-034 Decision 6).

### 5.2 Contribution Fields

From a single `SessionHistory`, the following fields are extracted:

| LongitudinalProfile field | Source in SessionHistory |
|---|---|
| `LongitudinalSessionEntry.session_id` | `session_history.session_id` |
| `LongitudinalSessionEntry.interview_index` | `session_history.interview_index` |
| `LongitudinalSessionEntry.profile_snapshot` | `session_history.knowledge_snapshot.profile_snapshot` |
| `LongitudinalSessionEntry.session_metadata.role` | `session_history.interview_metadata.role` |
| `LongitudinalSessionEntry.session_metadata.seniority` | `session_history.interview_metadata.seniority` |
| `LongitudinalSessionEntry.session_metadata.interview_type` | `session_history.interview_metadata.interview_type` |
| `LongitudinalSessionEntry.session_metadata.question_count` | `session_history.interview_metadata.question_count` |
| `LongitudinalSessionEntry.session_metadata.session_language` | `session_history.interview_metadata.session_language` |
| `LongitudinalSessionEntry.session_metadata.knowledge_epoch` | `session_history.knowledge_epoch` (property) |
| `LongitudinalSessionEntry.session_metadata.total_objectives` | `session_history.knowledge_snapshot.coaching_snapshot.statistics.total_objectives` |
| `LongitudinalSessionEntry.session_metadata.total_narrative_insights` | `session_history.knowledge_snapshot.narrative.insight_count` (property) |
| `LongitudinalSessionEntry.session_metadata.language_capabilities` | Live session state passed by `longitudinal_update_node` (not from closed `SessionHistory` — OI-03 resolution) |
| `language_capability_summary` (delta) | `LongitudinalSessionMetadata.language_capabilities` (each entry's `language_id`, `composite_score`, `idiomatic_usage_score`, `type_error_rate`, `questions_answered_in_language`) |
| `knowledge_epoch` (profile-level) | `session_history.knowledge_epoch` (most recent session value) |

**Fields not extracted from `SessionHistory`:** `scoring_snapshot`, `scoring_narrative`, `question_results`, `transcript`, `question_timeline`. These are session-specific artifacts; they do not accumulate in `LongitudinalProfile` (ADR-034 Decision 2: `LongitudinalProfile` does not carry `ScoringSnapshot` data).

### 5.3 Contribution Boundary

`LongitudinalProfileBuilder` reads only from `SessionHistory`. It does not read `InterviewState`, `Report`, or any live runtime artifact. This preserves the computation/projection boundary (P-01): the longitudinal update is pure assembly from a closed artifact.

---

## 6. Artifact Relationships

### 6.1 Primary Chain

```
CandidateIdentity (anchor — ADR-016A)
    │
    │ owns (1:1)
    ▼
LongitudinalProfile  [frozen=True, extra=forbid, schema_version="1.0"]
    │
    │ accumulates (1:n, ordered by interview_index ascending)
    ▼
LongitudinalSessionEntry [frozen=True, extra=forbid]
    │
    │ carries (1:1)
    ▼
CandidateProfileSnapshot  [frozen=True, extra=forbid — ADR-022]
    │
    │ derived from (1:1 per session)
    ▼
SessionHistory v2.0  [frozen=True, extra=forbid — ADR-022/ADR-033]
```

### 6.2 Derived View Chain

```
LongitudinalProfile (persisted)
    │
    │ read by
    ▼
LearningProgressBuilder
    │
    │ produces (never persisted)
    ▼
LearningProgress [frozen=True, extra=forbid]
    ├── session_entries: tuple[SessionProgressEntry, ...]
    ├── behavioral_trend: BehavioralTrend
    └── language_capability_summary: tuple[CrossSessionLanguageCapability, ...]
```

### 6.3 Future Analytics Boundary (V2)

`LongitudinalProfile` is candidate-scoped and single-candidate in V1.3. In V2, cohort-level aggregation reads from `LongitudinalProfile[]` across candidates via a dedicated analytics layer. The V1.3 `LongitudinalProfile` contract must not be modified for this purpose — the V2 analytics layer adapts to the V1.3 contract.

No V1.3 component may anticipate V2 analytics requirements by adding cohort or organisational fields to `LongitudinalProfile` or `LearningProgress`.

### 6.4 Replay Isolation (ADR-034 Decision 7, LP-11)

`LongitudinalProfile` has no relationship with any replay contract (`ReplayContext`, `ReplayResult`, `ReplayManifest`, `ReplaySession`). The boundary is bidirectional and clean. No replay contract may import `LongitudinalProfile`. No `LongitudinalProfile` contract may import any replay contract.

---

## 7. Serialization Rules

### 7.1 Versioning

- `LongitudinalProfile.schema_version = "1.0"` at initial implementation.
- `LongitudinalSessionEntry` does not carry an independent `schema_version`; it inherits the parent profile's version context.
- `CrossSessionLanguageCapability.schema_version = "1.0"` at initial implementation.
- `LearningProgress.schema_version = "1.0"` at initial implementation (this field already exists).
- `BehavioralTrend.schema_version = "1.0"` at initial implementation.

**Version increment triggers (ADR-034 Decision 2):**
- Adding a field with no safe default (required field addition) → version increment required; new ADR mandatory.
- Removing or renaming any field → version increment required; new ADR mandatory.
- Changing the type or semantics of an existing field → version increment required; new ADR mandatory.
- Adding a field with a safe default value (optional field addition) → no version increment; no ADR required.

### 7.2 Immutability

All artifacts in this specification are `frozen=True`. Serialization for persistence must not rely on object mutation. Deserialization from persistence must produce a `frozen=True` instance directly. No intermediate mutable representation is permitted.

### 7.3 Datetime Serialization

All `datetime` fields are UTC. Serialization format: ISO 8601 with timezone designator (`Z` suffix or `+00:00`). No naive datetimes are permitted in any contract in this specification.

### 7.4 Tuple vs List

All sequence fields in this specification use `tuple[T, ...]`, not `list[T]`. This is consistent with V1.2 frozen contracts (e.g., `CandidateProfileSnapshot.features`, `SessionHistory.transcript`) and enforces structural immutability.

### 7.5 Forward Compatibility

The `metadata: dict[str, str]` field on `LongitudinalProfile` is a reserved extensibility slot. All V1.3 implementations must serialize and deserialize `metadata` without loss. Future versions may add structured meaning to `metadata` keys without a schema version increment, provided the values remain `str`.

### 7.6 No Storage Technology Decision

This document specifies serialization rules at the domain layer. The concrete persistence format (SQLite schema, JSON file, binary encoding) is decided in the Data Model Specification. No storage technology assumption is made here.

---

## 8. Validation Rules

### 8.1 Consolidated Invariant Table

| ID | Artifact | Rule | Enforcement |
|---|---|---|---|
| LP-V-01 | `LongitudinalProfile` | `session_count == len(session_snapshots)` | `LongitudinalProfileBuilder.build()` validator |
| LP-V-02 | `LongitudinalProfile` | All `session_snapshots[*].profile_snapshot.candidate_identity_id == candidate_identity_id` | `LongitudinalProfileBuilder.build()` validator |
| LP-V-03 | `LongitudinalProfile` | All `interview_index` values in `session_snapshots` are unique | `LongitudinalProfileBuilder.build()` validator |
| LP-V-04 | `LongitudinalProfile` | `session_snapshots` ordered by `interview_index` ascending | `LongitudinalProfileBuilder.build()` validator |
| LP-V-05 | `LongitudinalProfile` | All `language_id` in `language_capability_summary` are unique | `LongitudinalProfileBuilder.build()` validator |
| LP-V-06 | `LongitudinalProfile` | `last_updated_at >= created_at` | `LongitudinalProfileBuilder.build()` validator |
| LP-V-07 | `LongitudinalProfile` | `knowledge_epoch` equals the epoch of the highest-`interview_index` session | `LongitudinalProfileBuilder.build()` validator |
| LP-V-08 | `LongitudinalProfile` | `session_count == 0` profiles are never persisted | `longitudinal_update_node` guard |
| LC-V-01 | `CrossSessionLanguageCapability` | `language_id` unique within `language_capability_summary` | LP-V-05 covers this |
| LC-V-02 | `CrossSessionLanguageCapability` | `session_count_in_language >= 1` | `LongitudinalProfileBuilder.build()` validator |
| LC-V-03 | `CrossSessionLanguageCapability` | `trend_direction == "insufficient_data"` when `session_count_in_language < 2` | `LongitudinalProfileBuilder` assembly logic |
| LC-V-04 | `CrossSessionLanguageCapability` | Scores in `[0.0, 1.0]` | Pydantic field constraints |
| LC-V-05 | `CrossSessionLanguageCapability` | `language_id` registered (ADR-019) | `LongitudinalProfileBuilder.build()` validator |
| LP-LP-01 | `LearningProgress` | `len(session_entries) == LongitudinalProfile.session_count` (when non-empty) | `LearningProgressBuilder.build()` validator |
| LP-LP-02 | `LearningProgress` | `session_entries` ordered by `session_index` ascending | `LearningProgressBuilder.build()` validator |
| LP-LP-03 | `LearningProgress` | `has_sufficient_data == (len(session_entries) >= 2)` | `LearningProgressBuilder.build()` validator |
| LP-LP-04 | `LearningProgress` | `BehavioralTrend.sessions_analysed == len(session_entries)` | `LearningProgressBuilder.build()` validator |
| LP-LP-05 | `LearningProgress` | `FeatureTrend.feature_type_id` values unique within `feature_trends` | `LearningProgressBuilder.build()` validator |
| LP-LP-06 | `LearningProgress` | Never persisted | Architectural test (import analysis) |
| LP-LP-07 | `LearningProgressBuilder` | Input must be `LongitudinalProfile`, not `SessionHistory[]` | Architectural test (ADR-034 Decision 5) |

### 8.2 Cross-Contract Invariants

| ID | Rule |
|---|---|
| XC-01 | `LongitudinalProfile.candidate_identity_id` must match `CandidateIdentity.candidate_identity_id` for the same candidate across all sessions. |
| XC-02 | `LongitudinalSessionEntry.interview_index` must match the corresponding `SessionHistory.interview_index` exactly. |
| XC-03 | `LongitudinalSessionEntry.profile_snapshot` must be identical (by value) to `SessionHistory.knowledge_snapshot.profile_snapshot` for the same session. |
| XC-04 | `LongitudinalProfile.session_count` must never exceed the count of `SessionHistory` records for the same `candidate_identity_id`. Excess sessions not in `LongitudinalProfile` indicate missed updates; this is the gap detection mechanism (ADR-034 Decision 3). |
| XC-05 | No replay contract imports `LongitudinalProfile` (LP-11); no `LongitudinalProfile` contract imports any replay contract (LP-11). Verified by architectural import test. |

---

## New Contracts Summary

| Contract | Location | New or Extended |
|---|---|---|
| `LongitudinalProfile` | `domain/contracts/longitudinal/longitudinal_profile.py` | New |
| `LongitudinalSessionEntry` | `domain/contracts/longitudinal/longitudinal_profile.py` | New (embedded) |
| `LongitudinalSessionMetadata` | `domain/contracts/longitudinal/longitudinal_profile.py` | New (embedded) |
| `CrossSessionLanguageCapability` | `domain/contracts/longitudinal/longitudinal_profile.py` | New (embedded) |
| `LongitudinalProfileBuilder` | `domain/contracts/longitudinal/longitudinal_profile_builder.py` | New |
| `LearningProgress` | `domain/contracts/progress/learning_progress.py` | Extended |
| `SessionProgressEntry` | `domain/contracts/progress/learning_progress.py` | Extended |
| `BehavioralTrend` | `domain/contracts/progress/learning_progress.py` | New (added to existing module) |
| `FeatureTrend` | `domain/contracts/progress/learning_progress.py` | New (added to existing module) |
| `BehavioralScore` | `domain/contracts/progress/learning_progress.py` | New (added to existing module) |

---

*This document is the frozen domain contract specification for EPIC-02. Implementation of any contract defined here may not begin until the Data Model Specification is also frozen and Architecture Freeze is declared. Any change to this document after Architecture Freeze requires a Freeze Integrity Check per V13-DEVELOPMENT-PLAYBOOK.md §9.*

*Revision 2026-07-14: Initial frozen draft. Produced after ADR-034 acceptance.*

*Revision 2026-07-14 (pre-freeze update): Added `total_objectives`, `total_narrative_insights`, `language_capabilities` to `LongitudinalSessionMetadata` (OI-01, OI-02 resolution). Updated `LongitudinalProfileBuilder` inputs and step 3/5. Resolved OI-03: `LanguageCapability` is not in `SessionHistory`; captured from live session by `longitudinal_update_node`. No `SessionHistory` contract change required. `LongitudinalProfileBuilder` receives `language_capabilities` as a direct input parameter. Freeze Integrity Check: additive-only changes; no architectural decision changed; no ADR required; no schema version increment.*
