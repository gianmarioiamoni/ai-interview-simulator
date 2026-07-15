# EPIC-03 — Domain Contracts

**Status:** FROZEN  
**Date:** 2026-07-15  
**Epic ID:** EPIC-V13-03  
**Governing ADR:** ADR-037 (Replay Engine Architecture)  
**Preconditions:** EPIC-03-REPLAY-ENGINE.md frozen; ADR-037 accepted; EPIC-01 CLOSED; EPIC-02 CLOSED.  
**Authority:** This document translates ADR-037 decisions into precise, field-level immutable contract specifications. Implementation is mechanical against this document. No architectural choices are made here — every decision traces to ADR-037.

---

## Preamble: Document Responsibilities

| Responsibility | Document |
|---|---|
| Architectural decisions, ownership, invariants | ADR-037 |
| Field-level specification, types, validators, lifecycle | **This document** |
| Field tables, serialization rules, replay completeness | EPIC-03-DATA-MODEL.md (next) |

No field in this document may be added, removed, or changed in type without a new ADR amending ADR-037 Decision 3.

---

## Section 0 — Naming Collision Resolution

### 0.1 The Conflict

The V1.2 replay layer contains a class named `ReplaySession` in `domain/contracts/replay/replay_session.py`. This class is a **runtime orchestrator** — it is not a domain contract. Its `run(context: ReplayContext) -> ReplayResult` method assembles a `ReplayResult` from a `ReplayContext`.

ADR-037 Decision 1 declares `ReplaySession` as the canonical V1.3 frozen Projection Artifact — the immutable output of `replay_node`. The two uses of the name `ReplaySession` are semantically incompatible.

### 0.2 Resolution Decision

**The V1.2 `ReplaySession` class is renamed to `ReplayOrchestrator` as a migration-only bridge.**

| Artifact | Action | Timing |
|---|---|---|
| `ReplaySession` (V1.2 runtime orchestrator in `replay_session.py`) | Renamed to `ReplayOrchestrator` | Phase 1 of EPIC-03 implementation — before any V1.3 artifact is introduced |
| `ReplayError` (defined in the same file) | Retained; moved to `replay_orchestrator.py` alongside `ReplayOrchestrator` | Same phase |
| `domain/contracts/replay/replay_session.py` | Renamed to `domain/contracts/replay/replay_orchestrator.py` | Same phase |
| `domain/contracts/replay/__init__.py` | Updated: exports `ReplayOrchestrator` and `ReplayError` from new module | Same phase |
| All test files referencing `ReplaySession` (orchestrator) | Updated to `ReplayOrchestrator` | Same phase |

**`ReplayOrchestrator` is a migration bridge. It carries no V1.3 design intent. It must be deleted in the same epic increment that `ReplaySession` (V1.3 Projection Artifact) is activated as the sole production artifact.**

No compatibility shim maps `ReplayOrchestrator` to `ReplaySession`. No code may import both simultaneously. The rename is a one-way, one-phase migration with a hard deletion target.

### 0.3 Additional Naming Conflicts Discovered

During audit of the V1.2 replay layer, two additional migration concerns were identified:

| Artifact | Issue | Resolution |
|---|---|---|
| `ReplayStatistics` (`replay_statistics.py`) | Currently derives from `ReplayResult`. After `ReplayResult` is deleted, `ReplayStatistics` must derive from `ReplaySession` (V1.3). The field set changes materially (adds `scoring_snapshot`, `question_results`). | `ReplayStatistics` is extended in EPIC-03 to derive from `ReplaySession` (V1.3). The `from_result(result: ReplayResult)` factory is replaced with `from_session(session: ReplaySession)`. The old factory is deleted in the same increment as `ReplayResult`. |
| `ReplayValidator` (`replay_validator.py`) | Currently validates `ReplayContext` + `ReplayResult`. `validate_result(result: ReplayResult, context: ReplayContext)` imports `ReplayResult` directly. | `ReplayValidator` is extended with a new method `validate_session(session: ReplaySession)`. The old `validate_result` is deleted in the same increment as `ReplayResult`. |

No further naming conflicts were identified. The `ReplayContext`, `ReplayManifest`, `ReplayEnums`, `MigrationMetadata`, and `ReplayValidationResult` names are all retained unchanged.

---

## Section 1 — ReplaySession (V1.3 Canonical Replay Artifact)

### 1.1 Purpose

`ReplaySession` is the immutable, self-contained Projection Artifact produced by `replay_node` from a closed `SessionHistory`. It carries all data required for Replay UI navigation (EPIC-04) without any further computation. (ADR-037 Decision 1.)

### 1.2 Classification

- **Type:** Projection Artifact (OP-02, ARC-01 §5)
- **Immutability:** `frozen=True`, `extra=forbid`
- **Construction:** `ReplaySessionBuilder` only (sole construction path — P-05)
- **Lifecycle:** Not persisted. Produced on demand; discarded after use.
- **Schema version:** `"1.0"` (set by builder; immutable after construction)

### 1.3 Field Specification

| Field | Type | Required | Default | Source | Invariants |
|---|---|---|---|---|---|
| `session_id` | `str` | Yes | — | `session_history.interview_metadata.session_id` | Non-empty; matches `manifest.session_id` |
| `candidate_identity_id` | `str` | Yes | — | `session_history.interview_metadata.candidate_identity_id` | Non-empty; matches `manifest.candidate_identity_id` |
| `schema_version` | `str` | Yes | `"1.0"` | Set by `ReplaySessionBuilder` | Non-empty; `"1.0"` in V1.3 |
| `replay_mode` | `ReplayMode` | Yes | `STANDARD` | Input to `replay_node` | Valid `ReplayMode` enum value |
| `replay_level` | `ReplayLevel` | Yes | `PRESENTATION` | Input to `replay_node` | Not `REASONING` (reserved — ADR-037 I-R09) |
| `profile_snapshot` | `CandidateProfileSnapshot` | Yes | — | `session_history.knowledge_snapshot.profile_snapshot` | Not None; object identity from `KnowledgeSnapshot` |
| `narrative` | `Narrative` | Yes | — | `session_history.knowledge_snapshot.narrative` | Not None; object identity from `KnowledgeSnapshot` |
| `coaching_snapshot` | `CoachingSnapshot` | Yes | — | `session_history.knowledge_snapshot.coaching_snapshot` | Not None; object identity from `KnowledgeSnapshot` |
| `scoring_snapshot` | `Optional[ScoringSnapshot]` | No | `None` | `session_history.scoring_snapshot` | `None` when session completed without evaluation |
| `question_results` | `tuple[ReplayQuestionRecord, ...]` | Yes | `()` | Assembled from `session_history.question_results` | Empty tuple when no questions persisted; immutable tuple |
| `session_metadata` | `ReplaySessionMetadata` | Yes | — | Assembled from `session_history.interview_metadata` | Not None |
| `policy_versions` | `PolicyVersions` | Yes | — | `session_history.knowledge_snapshot.policy_versions` | Not None; object identity from `KnowledgeSnapshot` |
| `knowledge_epoch` | `str` | Yes | — | `session_history.knowledge_snapshot.knowledge_epoch` | Non-empty |
| `manifest` | `ReplayManifest` | Yes | — | Produced by `replay_node` at reconstruction time | Not None; `manifest.session_id == session_id` |
| `is_successful` | `bool` | Yes | `True` | Set by `replay_node` | `False` iff reconstruction failed |
| `failure_reason` | `Optional[str]` | No | `None` | Set by `replay_node` | Non-None only when `is_successful=False` |
| `observation_store_snapshot` | `Optional[ObservationStoreSnapshot]` | No | `None` | `session_history.knowledge_snapshot.observation_store_snapshot` | Present only when `replay_level == KNOWLEDGE` |

### 1.4 Model Validators

- **V-RS-01:** `is_successful=False` requires `failure_reason` to be a non-empty string.
- **V-RS-02:** `is_successful=True` requires `failure_reason` is `None`.
- **V-RS-03:** `manifest.session_id` must equal `session_id`.
- **V-RS-04:** `manifest.candidate_identity_id` must equal `candidate_identity_id`.
- **V-RS-05:** `replay_level` must not be `ReplayLevel.REASONING`.
- **V-RS-06:** `observation_store_snapshot` must be `None` when `replay_level == PRESENTATION`.

### 1.5 Properties (read-only)

| Property | Type | Semantics |
|---|---|---|
| `is_standard` | `bool` | `replay_mode == ReplayMode.STANDARD` |
| `has_scoring` | `bool` | `scoring_snapshot is not None` |
| `has_provenance` | `bool` | `replay_level == ReplayLevel.KNOWLEDGE` |
| `question_count` | `int` | `len(question_results)` |

### 1.6 Module Location

`domain/contracts/replay/replay_session_v13.py`

The `_v13` suffix is a migration artifact only. Once `ReplayOrchestrator` (formerly `ReplaySession`) is deleted, this module is renamed to `replay_session.py`. The rename is performed in the same increment as the `ReplayOrchestrator` deletion.

---

## Section 2 — ReplayQuestionRecord

### 2.1 Purpose

`ReplayQuestionRecord` is the per-question data record embedded in `ReplaySession.question_results`. It carries all data required for question-by-question navigation in the Replay UI. It is assembled by `ReplaySessionBuilder` from `QuestionResultRecord` (persisted in `SessionHistory` v2.0 by EPIC-01).

`ReplayQuestionRecord` is not `QuestionResultRecord`. It is a replay-layer projection of it — stripped of any fields that are internal to the session close pipeline and not needed for Replay UI rendering.

### 2.2 Classification

- **Type:** Value Object (sub-artifact of `ReplaySession`)
- **Immutability:** `frozen=True`, `extra=forbid`
- **Owner:** `ReplaySession` — no independent lifecycle
- **Construction:** `ReplaySessionBuilder` (via loop over `SessionHistory.question_results`)

### 2.3 Field Specification

| Field | Type | Required | Source (`QuestionResultRecord`) | Notes |
|---|---|---|---|---|
| `question_id` | `str` | Yes | `question_result_record.question_id` | Non-empty |
| `question_index` | `int` | Yes | `question_result_record.question_index` | ≥ 0 |
| `question_type` | `str` | Yes | `question_result_record.question_type` | Non-empty |
| `area_label` | `str` | Yes | `question_result_record.area_label` | Non-empty |
| `question_prompt` | `str` | Yes | `question_result_record.question_prompt` | Non-empty |
| `candidate_answer` | `str` | Yes | `question_result_record.candidate_answer` | May be empty string if no answer submitted |
| `score` | `float` | Yes | `question_result_record.score` | ≥ 0.0 |
| `max_score` | `float` | Yes | `question_result_record.max_score` | > 0.0 |
| `feedback` | `str` | Yes | `question_result_record.feedback` | May be empty string |
| `strengths` | `tuple[str, ...]` | Yes | `question_result_record.strengths` | Immutable tuple; may be empty |
| `weaknesses` | `tuple[str, ...]` | Yes | `question_result_record.weaknesses` | Immutable tuple; may be empty |
| `execution_status` | `Optional[str]` | No | `question_result_record.execution_status` | Non-None for coding questions |
| `passed_tests` | `Optional[int]` | No | `question_result_record.passed_tests` | Non-None for coding questions |
| `total_tests` | `Optional[int]` | No | `question_result_record.total_tests` | Non-None for coding questions |
| `ai_hint_explanation` | `Optional[str]` | No | `question_result_record.ai_hint_explanation` | Non-None when hint was shown |
| `ai_hint_suggestion` | `Optional[str]` | No | `question_result_record.ai_hint_suggestion` | Non-None when hint was shown |
| `attempts` | `int` | Yes | `question_result_record.attempts` | ≥ 1 |

### 2.4 Model Validators

- **V-RQR-01:** `max_score > 0.0`.
- **V-RQR-02:** `score ≥ 0.0` and `score ≤ max_score`.
- **V-RQR-03:** `attempts ≥ 1`.
- **V-RQR-04:** `passed_tests`, `total_tests`, and `execution_status` must be all-None or all-non-None (they are co-present for coding questions only).

### 2.5 Properties

| Property | Type | Semantics |
|---|---|---|
| `is_coding_question` | `bool` | `execution_status is not None` |
| `has_hint` | `bool` | `ai_hint_explanation is not None` |
| `score_ratio` | `float` | `score / max_score` |

### 2.6 Module Location

`domain/contracts/replay/replay_question_record.py`

---

## Section 3 — ReplaySessionMetadata

### 3.1 Purpose

`ReplaySessionMetadata` is a value object assembled by `ReplaySessionBuilder` from `SessionHistory.interview_metadata`. It carries session-level context for Replay UI header and summary panel rendering.

### 3.2 Classification

- **Type:** Value Object (sub-artifact of `ReplaySession`)
- **Immutability:** `frozen=True`, `extra=forbid`
- **Owner:** `ReplaySession` — no independent lifecycle

### 3.3 Field Specification

| Field | Type | Required | Source | Notes |
|---|---|---|---|---|
| `interview_index` | `int` | Yes | `interview_metadata.interview_index` | ≥ 1 |
| `session_date` | `datetime` | Yes | `interview_metadata.session_date` | UTC |
| `role` | `str` | Yes | `interview_metadata.role` | Non-empty |
| `seniority_level` | `str` | Yes | `interview_metadata.seniority_level` | Non-empty |
| `question_count` | `int` | Yes | `interview_metadata.question_count` | ≥ 0 |
| `session_duration_seconds` | `Optional[float]` | No | `interview_metadata.session_duration_seconds` | `None` when not persisted |

### 3.4 Module Location

`domain/contracts/replay/replay_session_metadata.py`

---

## Section 4 — ReplayTimeline

### 4.1 Purpose

`ReplayTimeline` is a derived, ordered view of `ReplaySession.question_results`, providing sequential navigation state for the Replay UI. It is not persisted. It is produced by `ReplaySessionBuilder` from `question_results` and embedded in `ReplaySession`.

`ReplayTimeline` answers: "Given this `ReplaySession`, what is the ordered sequence of navigable positions, and what is the valid navigation range?"

### 4.2 Classification

- **Type:** Derived Value Object (sub-artifact of `ReplaySession`)
- **Immutability:** `frozen=True`, `extra=forbid`
- **Owner:** `ReplaySession` — no independent lifecycle
- **Construction:** `ReplaySessionBuilder` (derived from `question_results`)

### 4.3 Field Specification

| Field | Type | Required | Notes |
|---|---|---|---|
| `entries` | `tuple[ReplayTimelineEntry, ...]` | Yes | Ordered by `question_index`; one per `ReplayQuestionRecord` |
| `total_positions` | `int` | Yes | `len(entries)`; ≥ 0 |
| `first_position` | `int` | Yes | `0` when `total_positions > 0`; `-1` when empty |
| `last_position` | `int` | Yes | `total_positions - 1` when `total_positions > 0`; `-1` when empty |
| `is_empty` | `bool` | Yes | `total_positions == 0` |

### 4.4 ReplayTimelineEntry

Each `ReplayTimelineEntry` represents one navigable position in the replay:

| Field | Type | Required | Notes |
|---|---|---|---|
| `position` | `int` | Yes | 0-based navigation index |
| `question_id` | `str` | Yes | Matches `ReplayQuestionRecord.question_id` at this position |
| `question_index` | `int` | Yes | Original session question index |
| `area_label` | `str` | Yes | For navigation label rendering |
| `question_type` | `str` | Yes | For navigation icon rendering |
| `is_coding_question` | `bool` | Yes | Derived from `question_type` |

`ReplayTimelineEntry` is `frozen=True`, `extra=forbid`.

### 4.5 ReplayTimeline field addition to ReplaySession

`ReplaySession` carries `timeline: ReplayTimeline` as a required field. This field is populated by `ReplaySessionBuilder` from `question_results`. It is not listed in ADR-037 Decision 3 §3.1 by name, but is constitutionally permitted as a derived sub-artifact under Decision 3 §3.4 (EPIC-04 sufficiency guarantee — navigation state is required for question-by-question navigation). No ADR amendment is required: `ReplayTimeline` is assembled from `question_results` with no additional source data.

### 4.6 Module Location

`domain/contracts/replay/replay_timeline.py`

---

## Section 5 — ReplaySessionBuilder (Ownership and Contract)

### 5.1 Purpose

`ReplaySessionBuilder` is the sole construction path for `ReplaySession`. It is a fluent, stateless assembly component (P-05). It contains no computation logic, no LLM calls, and no conditional derivation.

### 5.2 Ownership

| Dimension | Value |
|---|---|
| Sole producer of `ReplaySession` | `ReplaySessionBuilder` |
| Caller (sole writer of `ReplaySession`) | `replay_node` |
| Direct constructor invocation in production | Prohibited |

### 5.3 Builder Interface

`ReplaySessionBuilder` exposes the following fluent setters, each returning `self`:

| Setter | Argument Type | Sets Field |
|---|---|---|
| `with_session_history(history)` | `SessionHistory` | Populates: `session_id`, `candidate_identity_id`, `session_metadata`, `profile_snapshot`, `narrative`, `coaching_snapshot`, `policy_versions`, `knowledge_epoch`, `scoring_snapshot`, `question_results`, `observation_store_snapshot`, `timeline` |
| `with_request(request)` | `ReplayRequest` | Sets: `replay_mode`, `replay_level` |
| `with_manifest(manifest)` | `ReplayManifest` | Sets: `manifest` |
| `with_schema_version(version)` | `str` | Sets: `schema_version` — defaults to `"1.0"` |

`build()` validates all mandatory fields and constructs the frozen `ReplaySession`. If any mandatory field is absent, `build()` raises `ValueError` with a descriptive message (P-06).

### 5.4 Build-Time Invariants

During `build()`, the following are enforced before the `ReplaySession` is constructed:

- **RC-B-01:** All required fields present (Reconstruction Completeness, P-08).
- **RC-B-02:** `manifest.session_id == session_id`.
- **RC-B-03:** `manifest.candidate_identity_id == candidate_identity_id`.
- **RC-B-04:** `replay_level != ReplayLevel.REASONING`.
- **RC-B-05:** `question_results` ordering: entries ordered by `question_index` ascending.
- **RC-B-06:** `timeline.total_positions == len(question_results)`.
- **RC-B-07:** `is_successful=True` iff `failure_reason is None`.

Violations raise `ValueError` (not `RuntimeError`). `RuntimeError` is reserved for programming errors (P-06).

### 5.5 Failure Path

When `replay_node` determines that reconstruction has failed (e.g., `SessionHistory` not found), it does not call `ReplaySessionBuilder.build()`. Instead, it constructs a minimal failed `ReplaySession` directly using the builder's `as_failed(session_id, failure_reason)` class method — the only permitted alternate construction path:

```
ReplaySessionBuilder.as_failed(session_id: str, candidate_identity_id: str, failure_reason: str) -> ReplaySession
```

This factory method produces a `ReplaySession` with `is_successful=False`, `failure_reason` populated, and all other fields set to type-safe empty defaults. It is the only place where non-full construction is permitted.

### 5.6 Module Location

`domain/contracts/replay/replay_session_builder.py`

---

## Section 6 — ReplayRequest

### 6.1 Purpose

`ReplayRequest` is the immutable input contract for `replay_node`. It carries the caller's intent without any session-resident data.

### 6.2 Field Specification

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `session_id` | `str` | Yes | — | Non-empty; identifies the completed session to replay |
| `replay_mode` | `ReplayMode` | No | `STANDARD` | Valid `ReplayMode` enum value |
| `replay_level` | `ReplayLevel` | No | `PRESENTATION` | Not `REASONING` (reserved) |
| `operator_id` | `Optional[str]` | No | `None` | Required when `replay_mode` is `MIGRATION` or `RECOVERY` |

### 6.3 Model Validators

- **V-RRQ-01:** `replay_level != ReplayLevel.REASONING` — raises `ValueError`.
- **V-RRQ-02:** `replay_mode in (MIGRATION, RECOVERY)` requires `operator_id` non-empty.

### 6.4 Module Location

`domain/contracts/replay/replay_request.py`

---

## Section 7 — ReplayGraphState

### 7.1 Purpose

`ReplayGraphState` is the LangGraph state container for the Replay Graph. It does not extend `InterviewState`. It contains no live session data.

### 7.2 Field Specification

| Field | Type | Required | Notes |
|---|---|---|---|
| `request` | `ReplayRequest` | Yes | Input; immutable throughout graph execution |
| `result` | `Optional[ReplaySession]` | No | Set by `replay_node`; `None` until the node completes |

`ReplayGraphState` is a `TypedDict` (LangGraph convention for state containers). It does not use `frozen=True` — LangGraph state containers are mutable by design. However, `request` is never overwritten after graph entry, and `result` is written exactly once.

### 7.3 Isolation Invariant

`ReplayGraphState` must not reference `InterviewState` or any type from the live session graph state contracts. This invariant is enforced by architectural test (ADR-037 I-R03).

### 7.4 Module Location

`domain/contracts/replay/replay_graph_state.py`

---

## Section 8 — ReplayFeatureEngine

### 8.1 Purpose

`ReplayFeatureEngine` is the read-only replay-layer equivalent of `FeatureEngine`. It reads stored `ProfileFeature` values from a `CandidateProfileSnapshot` and exposes them through a read-only interface. It performs no computation (ADR-037 Decision 2).

### 8.2 Classification

- **Type:** Read-only adapter (not a domain contract — no `frozen=True`)
- **Permitted operations:** Read stored features from `CandidateProfileSnapshot`
- **Prohibited operations:** Recompute, derive, accumulate, or LLM-augment features

### 8.3 Interface

| Method | Return Type | Behavior |
|---|---|---|
| `get_features()` | `tuple[ProfileFeature, ...]` | Returns all stored features from `CandidateProfileSnapshot` |
| `get_feature(identity: FeatureIdentity)` | `Optional[ProfileFeature]` | Returns stored feature by identity; `None` if not present |

Any method that computes, updates, or accumulates features raises `RuntimeError` (P-06). `ReplayFeatureEngine` must not expose any method signature that implies mutation or computation.

### 8.4 Lifecycle

Instantiated by `replay_node` with a `CandidateProfileSnapshot`. Discarded after `ReplaySessionBuilder.build()` completes. Stateless across replay operations.

### 8.5 Module Location

`domain/contracts/replay/replay_feature_engine.py`

---

## Section 9 — Validation Invariants

The following invariants govern all contracts in this epic. They extend and refine ADR-037 Decision 5.

### 9.1 Structural Invariants

| ID | Invariant | Enforcement |
|---|---|---|
| SI-01 | `ReplaySession.session_id` matches `ReplayManifest.session_id` | V-RS-03; ReplayValidator |
| SI-02 | `ReplaySession.candidate_identity_id` matches `ReplayManifest.candidate_identity_id` | V-RS-04; ReplayValidator |
| SI-03 | `ReplaySession.question_count == len(question_results)` | Property + builder RC-B-06 |
| SI-04 | `ReplayTimeline.total_positions == ReplaySession.question_count` | Builder RC-B-06 |
| SI-05 | `ReplayTimelineEntry.position` values are contiguous from 0 to `total_positions - 1` | Builder validation |
| SI-06 | `ReplaySession.is_successful=False` requires `failure_reason` non-empty | V-RS-01 |
| SI-07 | `observation_store_snapshot` is None for `PRESENTATION` level | V-RS-06 |

### 9.2 Source Invariants (Reconstruction Completeness, P-08)

Every `ReplaySession` field must trace to an explicit source. No field may use a computed default or implicit carry-forward:

| Field | Explicit Source Requirement |
|---|---|
| `profile_snapshot` | Must be the exact object reference from `KnowledgeSnapshot.profile_snapshot` |
| `narrative` | Must be the exact object reference from `KnowledgeSnapshot.narrative` |
| `coaching_snapshot` | Must be the exact object reference from `KnowledgeSnapshot.coaching_snapshot` |
| `policy_versions` | Must be the exact object reference from `KnowledgeSnapshot.policy_versions` |
| `scoring_snapshot` | Must be taken verbatim from `SessionHistory.scoring_snapshot` |
| `question_results` | Each `ReplayQuestionRecord` must be assembled from the corresponding `QuestionResultRecord` |
| `session_metadata` | Every field must be explicitly populated from `interview_metadata` |
| `knowledge_epoch` | Must be taken verbatim from `KnowledgeSnapshot.knowledge_epoch` |

### 9.3 Prohibition Invariants

| ID | Prohibition |
|---|---|
| PI-01 | No replay contract may import or reference `LongitudinalProfile` (ADR-037 I-R06) |
| PI-02 | No `LongitudinalProfile` contract may import or reference any replay contract (ADR-037 I-R06) |
| PI-03 | `ReplayFeatureEngine` may not invoke any method on the live `FeatureEngine` (ADR-037 Decision 2) |
| PI-04 | `ReplayGraphState` may not reference `InterviewState` (ADR-037 I-R03) |
| PI-05 | `ReplaySessionBuilder.build()` may not use wildcard copies (`**obj.dict()`, `model_copy` without explicit fields) |
| PI-06 | No replay artifact may be persisted (ADR-037 Decision 1 §1.4) |
| PI-07 | `ReplayLevel.REASONING` must not be accepted by any contract without raising `ValueError` or `RuntimeError` |

---

## Section 10 — Serialization Rules

All replay contracts in EPIC-03 follow these serialization rules:

1. **No persistence.** `ReplaySession` and all sub-artifacts are not serialized to any persistence layer in V1.3. No `model_dump()` for storage; no schema migrations required.

2. **API serialization.** When `ReplaySession` is returned by the Replay API layer (EPIC-04), serialization via `model_dump(mode="json")` is permitted. Enum values serialize as their string value (e.g., `"standard"`, `"level_1_presentation"`). `datetime` fields serialize as ISO 8601 UTC strings.

3. **`frozenset` fields.** Any `frozenset` field (e.g., from `CandidateProfileSnapshot`) serializes as a sorted list in JSON output. On deserialization, the API layer does not reconstruct `ReplaySession` from JSON — it always calls `replay_node` directly.

4. **`Optional` fields.** Serialized as `null` in JSON. EPIC-04 UI must handle `null` gracefully for `scoring_snapshot`, `failure_reason`, `session_duration_seconds`, `ai_hint_explanation`, `ai_hint_suggestion`.

5. **`tuple` fields.** Serialize as JSON arrays. On construction, `tuple` is enforced by `model_config = {"frozen": True}` — no in-place mutation.

6. **Schema version.** `ReplaySession.schema_version = "1.0"` is a sentinel for API consumers to detect format changes in future versions.

---

## Section 11 — Artifact Relationships

```
ReplayRequest (input to replay_node)
    │
    ▼
replay_node
    │
    ├── loads SessionHistory (from persistence — read-only)
    │       └── SessionHistory v2.0:
    │           ├── knowledge_snapshot
    │           │       ├── profile_snapshot     → ReplaySession.profile_snapshot
    │           │       ├── narrative             → ReplaySession.narrative
    │           │       ├── coaching_snapshot     → ReplaySession.coaching_snapshot
    │           │       ├── policy_versions       → ReplaySession.policy_versions
    │           │       ├── knowledge_epoch       → ReplaySession.knowledge_epoch
    │           │       └── observation_store_snapshot → ReplaySession (KNOWLEDGE level only)
    │           ├── scoring_snapshot              → ReplaySession.scoring_snapshot
    │           ├── question_results              → ReplaySession.question_results (via ReplayQuestionRecord)
    │           └── interview_metadata            → ReplaySession.session_metadata (via ReplaySessionMetadata)
    │
    ├── ReplayFeatureEngine (reads profile_snapshot.features; no computation)
    │
    ├── ReplaySessionBuilder
    │       ├── assembles ReplayQuestionRecord[] from question_results
    │       ├── assembles ReplaySessionMetadata from interview_metadata
    │       ├── assembles ReplayTimeline from question_results
    │       └── build() → ReplaySession (frozen, immutable)
    │
    └── ReplayManifest (produced by replay_node; embedded in ReplaySession)

ReplaySession (output — read-only)
    ├── profile_snapshot: CandidateProfileSnapshot
    ├── narrative: Narrative
    ├── coaching_snapshot: CoachingSnapshot
    ├── scoring_snapshot: Optional[ScoringSnapshot]
    ├── question_results: tuple[ReplayQuestionRecord, ...]
    ├── timeline: ReplayTimeline
    ├── session_metadata: ReplaySessionMetadata
    ├── policy_versions: PolicyVersions
    ├── knowledge_epoch: str
    └── manifest: ReplayManifest

    ↓ consumed by EPIC-04 (Replay UI) — read-only, no submission, no LLM calls
```

### Isolation Boundaries

```
[Replay Contract Layer]          ↔        [Live Session Contract Layer]
  ReplaySession                           InterviewState
  ReplayRequest                           CandidateProfile (live)
  ReplayGraphState                        ObservationStore (live)
  ReplayFeatureEngine                     FeatureEngine (live)
  ReplaySessionBuilder                    KnowledgePipeline
  ReplayTimeline                          SessionClosePipeline

No import crosses this boundary in either direction (I-R03, I-R06).
Exception: replay contracts MAY import closed immutable artifacts:
  CandidateProfileSnapshot, KnowledgeSnapshot, SessionHistory (read-only),
  Narrative, CoachingSnapshot, PolicyVersions, ScoringSnapshot,
  QuestionResultRecord — because these are closed projection artifacts,
  not live session components.
```

---

## Section 12 — Cross-Contract Invariants

These invariants govern interactions between contracts in this epic and contracts in prior epics:

| ID | Invariant | Source |
|---|---|---|
| XCI-01 | `ReplaySession.scoring_snapshot` must be populated from `SessionHistory.scoring_snapshot` verbatim — never from `InterviewEvaluation` (deleted in EPIC-01) | ADR-033 Decision 1, ADR-037 Decision 3 |
| XCI-02 | `ReplayQuestionRecord` fields are sourced exclusively from `QuestionResultRecord` — never from live `InterviewState.results_by_question` | ADR-033 Decision 2, ADR-037 Decision 3 |
| XCI-03 | `ReplaySession` has no dependency on `LongitudinalProfile` or `LearningProgress` | ADR-034 Decision 7, ADR-037 I-R06 |
| XCI-04 | `ReplayFeatureEngine` reads only from `CandidateProfileSnapshot` — never invokes live `FeatureEngine` | ADR-032 EI-02, ADR-037 Decision 2 |
| XCI-05 | `ReplaySession.profile_snapshot` carries the `CandidateProfileSnapshot` at session close — never a recomputed profile | ADR-032 EI-01, ADR-037 Decision 3 |
| XCI-06 | `LanguageProfile` and `LanguageCapability` are not surfaced in `ReplaySession` — they are session-close configuration artifacts not required for replay rendering | ADR-035, ADR-036 |

---

## Section 13 — Migration Rules for Legacy V1.2 Replay Artifacts

The following V1.2 artifacts are affected by EPIC-03. Each carries a declared deletion target.

| Artifact | File | Migration Action | Deletion Trigger |
|---|---|---|---|
| `ReplaySession` (V1.2 orchestrator class) | `replay_session.py` | Renamed to `ReplayOrchestrator`; file renamed to `replay_orchestrator.py` | Deleted in the same increment that `ReplaySession` (V1.3) is activated as sole production artifact |
| `ReplayError` | `replay_session.py` | Moved to `replay_orchestrator.py` alongside `ReplayOrchestrator` | Retained if still needed; deleted if no V1.3 replay path raises it |
| `ReplayResult` | `replay_result.py` | Deprecated — no new V1.3 production code may reference it | Deleted in the same increment as `ReplaySession` (V1.3) activation |
| `ReplayStatistics` | `replay_statistics.py` | Extended: `from_session(session: ReplaySession)` factory added; `from_result(result: ReplayResult)` deleted | `from_result` deleted with `ReplayResult`; `ReplayStatistics` is retained |
| `ReplayValidator` | `replay_validator.py` | Extended: `validate_session(session: ReplaySession)` added; `validate_result(...)` deleted | `validate_result` deleted with `ReplayResult` |
| `domain/contracts/replay/__init__.py` | `__init__.py` | Updated: exports `ReplayOrchestrator` (not `ReplaySession`) until V1.3 activation; then exports `ReplaySession` (V1.3) | Updated in each phase |

### Migration Sequencing

Phase 1 (before any V1.3 artifact is introduced):
1. Rename `replay_session.py` → `replay_orchestrator.py`.
2. Rename class `ReplaySession` → `ReplayOrchestrator` within the file.
3. Update `__init__.py` to export `ReplayOrchestrator`.
4. Update all test files referencing `ReplaySession` (orchestrator) to `ReplayOrchestrator`.
5. Run full regression suite — must be green before Phase 2 begins.

Phase 2 (V1.3 artifacts introduced):
1. Create all new contracts defined in Sections 1–8.
2. Implement `replay_node` and Replay Graph.
3. Extend `ReplayStatistics` and `ReplayValidator`.
4. All new tests pass; full regression suite green.

Phase 3 (deletion increment):
1. Delete `ReplayResult` (`replay_result.py`).
2. Delete `ReplayOrchestrator` (`replay_orchestrator.py`).
3. Delete `validate_result` from `ReplayValidator`.
4. Delete `from_result` from `ReplayStatistics`.
5. Rename `replay_session_v13.py` → `replay_session.py`.
6. Update `__init__.py` to export `ReplaySession` (V1.3).
7. Full regression suite green.

**No phase may be skipped. No compatibility bridge between phases may survive Phase 3.**

---

## Acceptance Checklist

| Criterion | Status |
|---|---|
| Naming collision resolved: V1.2 `ReplaySession` → `ReplayOrchestrator` | **FROZEN** — Section 0 |
| Additional conflicts identified and resolved | **FROZEN** — Section 0.3: `ReplayStatistics`, `ReplayValidator` migrations declared |
| `ReplaySession` contract specified | **FROZEN** — Section 1 |
| `ReplayQuestionRecord` contract specified | **FROZEN** — Section 2 |
| `ReplaySessionMetadata` contract specified | **FROZEN** — Section 3 |
| `ReplayTimeline` contract specified | **FROZEN** — Section 4 |
| `ReplaySessionBuilder` ownership and interface specified | **FROZEN** — Section 5 |
| `ReplayRequest` specified | **FROZEN** — Section 6 |
| `ReplayGraphState` specified | **FROZEN** — Section 7 |
| `ReplayFeatureEngine` scope and interface specified | **FROZEN** — Section 8 |
| Validation invariants declared | **FROZEN** — Section 9 |
| Serialization rules frozen | **FROZEN** — Section 10 |
| Artifact relationships diagrammed | **FROZEN** — Section 11 |
| Cross-contract invariants declared | **FROZEN** — Section 12 |
| Migration rules for all legacy artifacts | **FROZEN** — Section 13 |
| No compatibility bridge survives Architecture Freeze | **CONFIRMED** — Section 13 Phase 3 |
| `ReplaySession` is canonical replay artifact (ADR-037 D1) | **CONFIRMED** — Section 1 |
| `ReplayFeatureEngine` is read-pass only (ADR-037 D2) | **CONFIRMED** — Section 8 |
| `ReplaySession` field set sufficient (ADR-037 D3) | **CONFIRMED** — Section 1.3; EPIC-04 sufficiency stated |
| Graph topology: standalone Replay Graph (ADR-037 D4) | **CONFIRMED** — Section 7 |
| Invariants I-11, I-R01 through I-R09 traceable | **CONFIRMED** — Sections 9.2, 9.3 |
| ADR-033 D1/D2 integration | **CONFIRMED** — XCI-01, XCI-02 |
| ADR-034 D7 (longitudinal isolation) | **CONFIRMED** — XCI-03, PI-01, PI-02 |
| No production code modified | **CONFIRMED** — planning document only |

---

## Open Issues

None. All open issues from EPIC-03-REPLAY-ENGINE.md (OI-01 through OI-04) and ADR-037 are resolved by this document.

The one issue noted in ADR-037 (V1.2 `ReplaySession` naming collision) is resolved in Section 0 of this document.

---

*This document is the authoritative Domain Contracts specification for EPIC-03. Amendments require a recorded rationale and a Freeze Integrity Check per V13-DEVELOPMENT-PLAYBOOK.md §9.*
