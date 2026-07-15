# EPIC-03 — Data Model Specification

**Status:** FROZEN  
**Date:** 2026-07-15  
**Epic ID:** EPIC-V13-03  
**Governing ADR:** ADR-037 (Replay Engine Architecture)  
**Preconditions:** EPIC-03-DOMAIN-CONTRACTS.md frozen; ADR-037 accepted; EPIC-01 CLOSED; EPIC-02 CLOSED.  
**Authority:** This document freezes the serialization model, field tables, source traceability, reconstruction completeness, and schema versioning for all EPIC-03 artifacts. It resolves all open modelling questions left by EPIC-03-DOMAIN-CONTRACTS.md.

---

## Preamble: Document Responsibilities

| Responsibility | Document |
|---|---|
| Architectural decisions, invariants | ADR-037 |
| Field-level contract specification, types, validators | EPIC-03-DOMAIN-CONTRACTS.md |
| Field tables, serialization, traceability, schema versioning | **This document** |

This document does not re-specify invariants (that is the Domain Contracts' job). It does not make architectural decisions (that is the ADR's job). It resolves modelling questions, verifies traceability, and freezes the complete field tables.

---

## Section 1 — Reconstruction Gap Audit

Before freezing the field tables, this section audits every `ReplaySessionMetadata` field declared in EPIC-03-DOMAIN-CONTRACTS.md §3.3 against the actual persisted `InterviewMetadata` contract.

### 1.1 InterviewMetadata — Actual Persisted Fields

`InterviewMetadata` (live in `domain/contracts/session_history/session_history.py`) carries:

| Field | Type | Present in InterviewMetadata |
|---|---|---|
| `role` | `str` | Yes |
| `seniority` | `str` | Yes (field name: `seniority`, not `seniority_level`) |
| `interview_type` | `str` | Yes |
| `interview_mode` | `str` | Yes |
| `session_language` | `str` | Yes |
| `question_count` | `int` | Yes |
| `company` | `Optional[str]` | Yes |

Fields declared in EPIC-03-DOMAIN-CONTRACTS.md §3.3 for `ReplaySessionMetadata` that are **not** in `InterviewMetadata`:

| Field Declared in Domain Contracts | Actual Source | Classification |
|---|---|---|
| `interview_index` | `SessionHistory.interview_index` (top-level field — not in `InterviewMetadata`) | Source correction — field exists; source is `session_history.interview_index`, not `interview_metadata.interview_index` |
| `session_date` | Does not exist in `InterviewMetadata` or `SessionHistory` as a named field. `SessionHistory.created_at` is the closest equivalent (UTC timestamp of session close). | **Reconstruction Gap RG-01** |
| `session_duration_seconds` | Does not exist in `InterviewMetadata`. Present in `QuestionTimelineEntry.duration_seconds` (per-question). Session total is derivable by summing `question_timeline` entries. | **Reconstruction Gap RG-02** |
| `seniority_level` | Field name mismatch: the persisted field is `seniority`, not `seniority_level` | Source correction — field exists under different name |

### 1.2 Reconstruction Gap Register

| ID | Gap | Severity | Classification |
|---|---|---|---|
| RG-01 | `session_date` is not persisted as a named field. `SessionHistory.created_at` (UTC datetime of session close) is the authoritative proxy. | Low | **Data Model Extension** — `ReplaySessionMetadata.session_date` maps to `SessionHistory.created_at`. No new field is required; source is corrected. |
| RG-02 | `session_duration_seconds` is not persisted as a session-level field. It is derivable by summing `QuestionTimelineEntry.duration_seconds` values across all entries, but this sum is not always complete (individual durations are `Optional`). | Medium | **Data Model Extension** — `ReplaySessionMetadata.session_duration_seconds` maps to the sum of `question_timeline[*].duration_seconds` when all values are non-None; otherwise `None`. No recomputation of knowledge — this is a metadata aggregation from persisted records. Acceptable under ADR-037 Decision 2 (read-pass scope). |

### 1.3 QuestionResultRecord — Audit Against ReplayQuestionRecord

`QuestionResultRecord` (live in `domain/contracts/session_history/question_result_record.py`) carries:

| Field in QuestionResultRecord | In ReplayQuestionRecord (Domain Contracts §2.3)? | Action |
|---|---|---|
| `question_id` | Yes | Consistent |
| `question_index` | Yes | Consistent |
| `question_type` | Yes | Consistent |
| `area_label` | Yes | Consistent |
| `question_prompt` | Yes | Consistent |
| `score` | Yes — but Domain Contracts declares `float` without range; actual range is `0.0–100.0` | Clarification required — see §1.4 |
| `max_score` | Yes — actual constraint is `gt=0.0` | Consistent; Domain Contracts said `> 0.0` |
| `feedback` | Yes | Consistent |
| `strengths` | Yes | Consistent |
| `weaknesses` | Yes | Consistent |
| `follow_up_question` | **Missing from ReplayQuestionRecord** | **Reconstruction Gap RG-03** |
| `passed_tests` | Yes | Consistent |
| `total_tests` | Yes | Consistent |
| `execution_status` | Yes | Consistent |
| `attempts` | Yes | Consistent |
| `ai_hint_explanation` | Yes | Consistent |
| `ai_hint_suggestion` | Yes | Consistent |
| `schema_version` | Not carried into `ReplayQuestionRecord` | Intentional — `schema_version` is a persistence artifact; `ReplayQuestionRecord` carries `ReplaySession.schema_version` instead |

### 1.4 Score Range Clarification

`QuestionResultRecord.score` uses range `0.0–100.0` (percentage scale). `QuestionResultRecord.max_score` uses `gt=0.0` (also percentage scale). `ReplayQuestionRecord` must preserve this scale verbatim — no normalization.

Domain Contracts §2.3 declared `score: float` and `max_score: float` without explicit range. This document freezes:
- `ReplayQuestionRecord.score`: `float`, `ge=0.0`, `le=100.0`
- `ReplayQuestionRecord.max_score`: `float`, `gt=0.0`
- `ReplayQuestionRecord.score_ratio`: computed as `score / max_score` (property; not a stored field)

No `score_ratio` normalization to `[0, 1]` is applied at reconstruction time. The raw values are read verbatim.

### 1.5 Reconstruction Gap RG-03

| ID | Gap | Classification | Resolution |
|---|---|---|---|
| RG-03 | `QuestionResultRecord.follow_up_question` is persisted in `SessionHistory` but not declared in `ReplayQuestionRecord` (EPIC-03-DOMAIN-CONTRACTS.md §2.3). | **Domain Contracts Extension** — `follow_up_question` is a persisted field that the Replay UI (EPIC-04) may need to display (a follow-up question shown during the session is session-relevant). | `follow_up_question: Optional[str]` is added to `ReplayQuestionRecord` in this Data Model. Domain Contracts §2.3 is extended by this document. This is a Data Model extension, not an architectural change — no ADR amendment is required. |

### 1.6 question_count Consistency Gap

`SessionHistory.question_count` is defined as `len(transcript)` (a property). `len(question_results)` may differ from `len(transcript)` if a question had no result persisted (e.g., an unanswered question at session close). This affects `ReplaySessionMetadata.question_count` and `ReplayTimeline.total_positions`.

**Resolution:**
- `ReplaySessionMetadata.question_count` maps to `len(session_history.question_results)` — the count of questions with persisted results, not `session_history.question_count` (which counts transcript entries).
- `ReplayTimeline.total_positions` maps to `len(session_history.question_results)`.
- This is the correct source for replay: the Replay UI navigates questions that have results. Questions in the transcript without a result record are not navigable.

No new field is required. Source correction only.

---

## Section 2 — ReplaySession Field Table (Complete)

Full field table incorporating all source corrections and gap resolutions from Section 1.

| # | Field | Type | Required | Default | Authoritative Source | Notes |
|---|---|---|---|---|---|---|
| 1 | `session_id` | `str` | Yes | — | `session_history.session_id` | Non-empty; min_length=1 |
| 2 | `candidate_identity_id` | `str` | Yes | — | `session_history.candidate_identity_id` | Non-empty; min_length=1 |
| 3 | `schema_version` | `str` | Yes | `"1.0"` | Set by `ReplaySessionBuilder` | Constant in V1.3 |
| 4 | `replay_mode` | `ReplayMode` | Yes | `STANDARD` | `ReplayRequest.replay_mode` | Enum: STANDARD / MIGRATION / RECOVERY |
| 5 | `replay_level` | `ReplayLevel` | Yes | `PRESENTATION` | `ReplayRequest.replay_level` | Not REASONING |
| 6 | `profile_snapshot` | `CandidateProfileSnapshot` | Yes | — | `session_history.knowledge_snapshot.profile_snapshot` | Object identity from `KnowledgeSnapshot` |
| 7 | `narrative` | `Narrative` | Yes | — | `session_history.knowledge_snapshot.narrative` | Object identity from `KnowledgeSnapshot` |
| 8 | `coaching_snapshot` | `CoachingSnapshot` | Yes | — | `session_history.knowledge_snapshot.coaching_snapshot` | Object identity from `KnowledgeSnapshot` |
| 9 | `scoring_snapshot` | `Optional[ScoringSnapshot]` | No | `None` | `session_history.scoring_snapshot` | None when session completed without evaluation |
| 10 | `question_results` | `tuple[ReplayQuestionRecord, ...]` | Yes | `()` | Assembled from `session_history.question_results` | Ordered by `question_index` |
| 11 | `timeline` | `ReplayTimeline` | Yes | — | Derived from `question_results` by builder | See §4 |
| 12 | `session_metadata` | `ReplaySessionMetadata` | Yes | — | Assembled from `session_history` fields | See §3 |
| 13 | `policy_versions` | `PolicyVersions` | Yes | — | `session_history.knowledge_snapshot.policy_versions` | Object identity from `KnowledgeSnapshot` |
| 14 | `knowledge_epoch` | `str` | Yes | — | `session_history.knowledge_snapshot.knowledge_epoch` | Verbatim from `KnowledgeSnapshot` |
| 15 | `manifest` | `ReplayManifest` | Yes | — | Produced by `replay_node` at reconstruction time | Audit record |
| 16 | `is_successful` | `bool` | Yes | `True` | Set by `replay_node` | False iff reconstruction failed |
| 17 | `failure_reason` | `Optional[str]` | No | `None` | Set by `replay_node` | Non-None only when `is_successful=False` |
| 18 | `observation_store_snapshot` | `Optional[ObservationStoreSnapshot]` | No | `None` | `session_history.knowledge_snapshot.observation_store_snapshot` | Present only when `replay_level == KNOWLEDGE` |

**Total fields: 18.** Every field has exactly one authoritative source. No field lacks a declared source.

---

## Section 3 — ReplaySessionMetadata Field Table (Complete)

Source corrections applied from Section 1.1.

| # | Field | Type | Required | Default | Authoritative Source | Source Correction |
|---|---|---|---|---|---|---|
| 1 | `interview_index` | `int` | Yes | — | `session_history.interview_index` | Source is top-level `SessionHistory` field, not `InterviewMetadata` |
| 2 | `session_date` | `datetime` | Yes | — | `session_history.created_at` | RG-01 resolved: `created_at` is the UTC session-close timestamp |
| 3 | `role` | `str` | Yes | — | `session_history.interview_metadata.role` | Consistent |
| 4 | `seniority_level` | `str` | Yes | — | `session_history.interview_metadata.seniority` | RG-field: persisted field name is `seniority`; `ReplaySessionMetadata` exposes it as `seniority_level` for UI clarity |
| 5 | `interview_mode` | `str` | Yes | — | `session_history.interview_metadata.interview_mode` | Consistent |
| 6 | `question_count` | `int` | Yes | — | `len(session_history.question_results)` | Source correction from §1.6: uses `question_results` length, not `transcript` length |
| 7 | `session_duration_seconds` | `Optional[float]` | No | `None` | Sum of `session_history.question_timeline[*].duration_seconds` when all non-None; otherwise `None` | RG-02 resolved |
| 8 | `company` | `Optional[str]` | No | `None` | `session_history.interview_metadata.company` | Added field: present in `InterviewMetadata` but not declared in Domain Contracts §3.3 — added here |

**Note on `company` field:** `InterviewMetadata.company` is a persisted field not declared in EPIC-03-DOMAIN-CONTRACTS.md §3.3. It is added in this Data Model. No ADR amendment required — this is a metadata field with no architectural implications.

**Note on `seniority_level` naming:** `ReplaySessionMetadata.seniority_level` is the replay-layer name for `InterviewMetadata.seniority`. The field rename is a projection concern only; no persistence change is required.

---

## Section 4 — ReplayQuestionRecord Field Table (Complete)

Extended from Domain Contracts §2.3. RG-03 resolution applied.

| # | Field | Type | Required | Default | Source (`QuestionResultRecord`) | Constraint |
|---|---|---|---|---|---|---|
| 1 | `question_id` | `str` | Yes | — | `question_id` | min_length=1 |
| 2 | `question_index` | `int` | Yes | — | `question_index` | ge=0 |
| 3 | `question_type` | `str` | Yes | — | `question_type` | min_length=1 |
| 4 | `area_label` | `str` | Yes | — | `area_label` | min_length=1 |
| 5 | `question_prompt` | `str` | Yes | — | `question_prompt` | min_length=1 |
| 6 | `candidate_answer` | `str` | Yes | — | Assembled from `session_history.transcript` entry matching `question_id` — `TranscriptEntry.answer_content` | May be empty string |
| 7 | `score` | `float` | Yes | — | `score` | ge=0.0, le=100.0 (percentage scale) |
| 8 | `max_score` | `float` | Yes | — | `max_score` | gt=0.0 |
| 9 | `feedback` | `str` | Yes | — | `feedback` | min_length=1 |
| 10 | `strengths` | `tuple[str, ...]` | Yes | `()` | `strengths` | Immutable tuple |
| 11 | `weaknesses` | `tuple[str, ...]` | Yes | `()` | `weaknesses` | Immutable tuple |
| 12 | `follow_up_question` | `Optional[str]` | No | `None` | `follow_up_question` | **RG-03 addition** |
| 13 | `execution_status` | `Optional[str]` | No | `None` | `execution_status` | Non-None for coding questions |
| 14 | `passed_tests` | `Optional[int]` | No | `None` | `passed_tests` | ge=0; co-present with `total_tests` |
| 15 | `total_tests` | `Optional[int]` | No | `None` | `total_tests` | gt=0; co-present with `passed_tests` |
| 16 | `ai_hint_explanation` | `Optional[str]` | No | `None` | `ai_hint_explanation` | Non-None when hint shown |
| 17 | `ai_hint_suggestion` | `Optional[str]` | No | `None` | `ai_hint_suggestion` | Non-None when `ai_hint_explanation` present |
| 18 | `attempts` | `int` | Yes | — | `attempts` | ge=1 |

**Total fields: 18.** `candidate_answer` sourced from `TranscriptEntry` (not from `QuestionResultRecord` directly — see §5 traceability).

### 4.1 candidate_answer Source Resolution

`QuestionResultRecord` does **not** carry `candidate_answer`. The answer text is persisted in `TranscriptEntry.answer_content` (in `SessionHistory.transcript`). `ReplaySessionBuilder` must join `question_results` with `transcript` by `question_id` to populate `candidate_answer`.

Join logic: for each `QuestionResultRecord`, find `TranscriptEntry` where `TranscriptEntry.question_id == question_result.question_id`. If no matching `TranscriptEntry` exists, `candidate_answer` defaults to `""` (empty string — no answer was submitted). This join is a read-pass over persisted records; it is not computation and does not require an ADR.

---

## Section 5 — SessionHistory → ReplaySession Traceability Matrix

Complete field-level traceability. Every `ReplaySession` field traces to exactly one authoritative `SessionHistory` sub-artifact.

| ReplaySession Field | SessionHistory Source Path | Sub-Artifact Type |
|---|---|---|
| `session_id` | `session_history.session_id` | `str` (top-level) |
| `candidate_identity_id` | `session_history.candidate_identity_id` | `str` (top-level) |
| `schema_version` | Constant `"1.0"` set by builder | Builder constant |
| `replay_mode` | `ReplayRequest.replay_mode` | Input parameter |
| `replay_level` | `ReplayRequest.replay_level` | Input parameter |
| `profile_snapshot` | `session_history.knowledge_snapshot.profile_snapshot` | `CandidateProfileSnapshot` |
| `narrative` | `session_history.knowledge_snapshot.narrative` | `Narrative` |
| `coaching_snapshot` | `session_history.knowledge_snapshot.coaching_snapshot` | `CoachingSnapshot` |
| `scoring_snapshot` | `session_history.scoring_snapshot` | `Optional[ScoringSnapshot]` |
| `question_results[*]` | `session_history.question_results[*]` joined with `session_history.transcript[*]` | `QuestionResultRecord` + `TranscriptEntry` |
| `timeline` | Derived from `question_results` order | Builder derivation (read-pass) |
| `session_metadata.interview_index` | `session_history.interview_index` | `int` (top-level) |
| `session_metadata.session_date` | `session_history.created_at` | `datetime` (top-level) |
| `session_metadata.role` | `session_history.interview_metadata.role` | `InterviewMetadata` |
| `session_metadata.seniority_level` | `session_history.interview_metadata.seniority` | `InterviewMetadata` |
| `session_metadata.interview_mode` | `session_history.interview_metadata.interview_mode` | `InterviewMetadata` |
| `session_metadata.question_count` | `len(session_history.question_results)` | Derived count (read-pass) |
| `session_metadata.session_duration_seconds` | Sum of `session_history.question_timeline[*].duration_seconds` | `Optional[float]` (aggregation) |
| `session_metadata.company` | `session_history.interview_metadata.company` | `InterviewMetadata` |
| `policy_versions` | `session_history.knowledge_snapshot.policy_versions` | `PolicyVersions` |
| `knowledge_epoch` | `session_history.knowledge_snapshot.knowledge_epoch` | `str` (property) |
| `manifest` | Produced by `replay_node` | Builder-produced |
| `is_successful` | Set by `replay_node` | Runtime flag |
| `failure_reason` | Set by `replay_node` on failure | Runtime flag |
| `observation_store_snapshot` | `session_history.knowledge_snapshot.observation_store_snapshot` | `Optional[ObservationStoreSnapshot]` |

**Traceability verdict: COMPLETE.** Every `ReplaySession` field has exactly one authoritative source. No field is unaccounted for.

---

## Section 6 — Reconstruction Completeness Matrix

Verifies that every `ReplaySession` field can be reconstructed from persisted `SessionHistory` without LLM calls, live pipeline invocation, or runtime recomputation.

| Field | Reconstruction Path | LLM-Free? | Deterministic? | Complete? |
|---|---|---|---|---|
| `session_id` | Direct read | Yes | Yes | Yes |
| `candidate_identity_id` | Direct read | Yes | Yes | Yes |
| `schema_version` | Builder constant | Yes | Yes | Yes |
| `replay_mode` | Input parameter | Yes | Yes | Yes |
| `replay_level` | Input parameter | Yes | Yes | Yes |
| `profile_snapshot` | Object reference from `KnowledgeSnapshot` | Yes | Yes | Yes |
| `narrative` | Object reference from `KnowledgeSnapshot` | Yes | Yes | Yes |
| `coaching_snapshot` | Object reference from `KnowledgeSnapshot` | Yes | Yes | Yes |
| `scoring_snapshot` | Direct read from `SessionHistory` | Yes | Yes | Yes |
| `question_results` | Read `QuestionResultRecord[]` + join with `TranscriptEntry[]` by `question_id` | Yes | Yes | Yes |
| `timeline` | Sort `question_results` by `question_index` | Yes | Yes | Yes |
| `session_metadata.interview_index` | Direct read from `SessionHistory.interview_index` | Yes | Yes | Yes |
| `session_metadata.session_date` | Direct read from `SessionHistory.created_at` | Yes | Yes | Yes |
| `session_metadata.role` | Direct read from `InterviewMetadata` | Yes | Yes | Yes |
| `session_metadata.seniority_level` | Direct read from `InterviewMetadata.seniority` | Yes | Yes | Yes |
| `session_metadata.interview_mode` | Direct read from `InterviewMetadata` | Yes | Yes | Yes |
| `session_metadata.question_count` | `len(question_results)` | Yes | Yes | Yes |
| `session_metadata.session_duration_seconds` | Sum `question_timeline[*].duration_seconds` | Yes | Conditionally (None if any entry is None) | Yes |
| `session_metadata.company` | Direct read from `InterviewMetadata` | Yes | Yes | Yes |
| `policy_versions` | Object reference from `KnowledgeSnapshot` | Yes | Yes | Yes |
| `knowledge_epoch` | Direct read from `KnowledgeSnapshot` | Yes | Yes | Yes |
| `manifest` | Produced at replay time (timestamps vary; knowledge fields are deterministic) | Yes | Knowledge fields: Yes | Yes |
| `observation_store_snapshot` | Object reference from `KnowledgeSnapshot` (KNOWLEDGE level) | Yes | Yes | Yes |

**Reconstruction verdict: COMPLETE.** All fields are LLM-free, all knowledge fields are deterministic, all fields are complete. `session_duration_seconds` is conditionally populated — `None` when any `question_timeline` entry has `duration_seconds=None`. This is correct and observable (not a silent failure).

---

## Section 7 — ReplayTimeline Serialization Model

`ReplayTimeline` is a derived ordering structure. It is never persisted independently. It is assembled by `ReplaySessionBuilder` from `question_results`.

### 7.1 ReplayTimeline Fields

| Field | Type | Constraint | Source |
|---|---|---|---|
| `entries` | `tuple[ReplayTimelineEntry, ...]` | Ordered by `position` (0-based) | Assembled from `question_results` sorted by `question_index` |
| `total_positions` | `int` | ge=0; equals `len(entries)` | `len(question_results)` |
| `first_position` | `int` | 0 when non-empty; -1 when empty | Computed by builder |
| `last_position` | `int` | `total_positions - 1` when non-empty; -1 when empty | Computed by builder |
| `is_empty` | `bool` | `total_positions == 0` | Computed by builder |

### 7.2 ReplayTimelineEntry Fields

| Field | Type | Source |
|---|---|---|
| `position` | `int` (ge=0) | 0-based index assigned by builder |
| `question_id` | `str` | `ReplayQuestionRecord.question_id` |
| `question_index` | `int` | `ReplayQuestionRecord.question_index` |
| `area_label` | `str` | `ReplayQuestionRecord.area_label` |
| `question_type` | `str` | `ReplayQuestionRecord.question_type` |
| `is_coding_question` | `bool` | `ReplayQuestionRecord.execution_status is not None` |

### 7.3 Assembly Rule

`ReplayTimeline.entries` is constructed by sorting `question_results` by `question_index` ascending, then assigning `position` values 0, 1, 2, ... in order. The assignment is deterministic and reproducible.

---

## Section 8 — ReplayGraphState Serialization Boundaries

`ReplayGraphState` is a LangGraph `TypedDict`. It is never serialized to a persistence layer. It exists only within the lifetime of a single Replay Graph execution.

### 8.1 Serialization Rules

| Dimension | Rule |
|---|---|
| Persistence | None — `ReplayGraphState` is not persisted |
| Cross-request state | None — each `replay_node` invocation creates a fresh `ReplayGraphState` |
| Logging | `ReplayGraphState.request.session_id` and `ReplayGraphState.result.is_successful` are logged at INFO level on graph exit |
| Error propagation | `ReplayGraphState.error` is logged at WARNING level when non-None |

### 8.2 State Boundaries

`ReplayGraphState` must not be serialized as a LangGraph checkpoint. If LangGraph checkpointing is enabled at the infrastructure level, the Replay Graph must be configured to **disable checkpointing**. Persisting `ReplayGraphState` would create a non-authoritative secondary record of a `ReplaySession` — a violation of ADR-037 Decision 1 §1.4 (ReplaySession is not persisted).

---

## Section 9 — Serialization Rules

All EPIC-03 contracts follow these serialization rules, extending EPIC-03-DOMAIN-CONTRACTS.md §10.

### 9.1 No Persistence for ReplaySession

`ReplaySession` and all sub-artifacts (`ReplayQuestionRecord`, `ReplaySessionMetadata`, `ReplayTimeline`, `ReplayTimelineEntry`, `ReplayManifest`) are not persisted to any storage layer in V1.3.

### 9.2 API Serialization

When serialized to JSON for the Replay UI (EPIC-04) API response:

| Type | JSON Serialization Rule |
|---|---|
| `str` | String |
| `int` | Number (integer) |
| `float` | Number (float); score values retain 1 decimal place |
| `bool` | Boolean |
| `datetime` | ISO 8601 UTC string (e.g., `"2026-07-15T01:27:00Z"`) |
| `Optional[T]` | `null` when `None`; serialized value when non-None |
| `tuple[T, ...]` | JSON array |
| `frozenset[str]` | JSON array (sorted for determinism) |
| `ReplayMode` | String value (e.g., `"standard"`) |
| `ReplayLevel` | String value (e.g., `"level_1_presentation"`) |
| `ReplaySourcePriority` | Integer value |
| `dict[str, str]` | JSON object |

### 9.3 Nested Artifacts

`ReplaySession` serializes all sub-artifacts recursively. The nesting hierarchy in JSON output:

```
ReplaySession
  ├── session_metadata: ReplaySessionMetadata
  ├── question_results: [ ReplayQuestionRecord, ... ]
  ├── timeline:
  │     ├── entries: [ ReplayTimelineEntry, ... ]
  │     └── (scalar fields)
  ├── manifest: ReplayManifest
  │     └── migration_metadata: MigrationMetadata | null
  ├── profile_snapshot: CandidateProfileSnapshot (opaque — serialized by its own contract)
  ├── narrative: Narrative (opaque — serialized by its own contract)
  ├── coaching_snapshot: CoachingSnapshot (opaque — serialized by its own contract)
  ├── scoring_snapshot: ScoringSnapshot | null (opaque — serialized by its own contract)
  ├── policy_versions: PolicyVersions
  └── observation_store_snapshot: ObservationStoreSnapshot | null (KNOWLEDGE level only)
```

### 9.4 `candidate_answer` Serialization

`ReplayQuestionRecord.candidate_answer` may be an empty string (`""`). This is a valid serialization representing a question with no submitted answer. The API must serialize it as `""`, not as `null`. EPIC-04 must treat `""` as "no answer submitted" and render accordingly.

---

## Section 10 — Schema Versioning Strategy

### 10.1 ReplaySession Schema Version

| Version | Trigger | Current |
|---|---|---|
| `"1.0"` | Initial V1.3 version | **Active** |

A schema version increment is triggered when:
- The set of fields on `ReplaySession` changes in a backward-incompatible way (field removed, type changed, required field added).
- The set of fields on `ReplayQuestionRecord` changes in a backward-incompatible way.
- A new required sub-artifact is added to `ReplaySession`.

Additive field additions with safe defaults (`Optional[T]` with default `None`, or `tuple[T, ...]` with default `()`) do **not** require a version increment.

When a version increment is required, a new ADR amending ADR-037 is mandatory before implementation begins. The ADR must specify whether in-flight replays are affected (they are not, since `ReplaySession` is not persisted).

### 10.2 SessionHistory Schema Version Dependency

`ReplaySession` depends on `SessionHistory` at schema version `"2.0"`. If `SessionHistory` schema version is incremented (e.g., for a new EPIC adding fields to `SessionHistory`), `replay_node` must be updated in the same epic to surface any new fields in `ReplaySession`. A `SessionHistory` schema version increment without a corresponding `ReplaySession` review is a deferred technical debt item (P2).

### 10.3 ReplayManifest Schema Version

`ReplayManifest` carries `replay_engine_version` (the version of the `replay_node` / Replay Engine subsystem). Initial value: `"1.0"`. This field is set by `replay_node` from a module-level constant. It is not the same as `ReplaySession.schema_version`.

---

## Section 11 — Cross-Contract Validation

### 11.1 At Build Time (ReplaySessionBuilder)

| Check | Enforcement |
|---|---|
| `session_id` matches `manifest.session_id` | RC-B-02 |
| `candidate_identity_id` matches `manifest.candidate_identity_id` | RC-B-03 |
| `question_results` sorted by `question_index` ascending | RC-B-05 |
| `timeline.total_positions == len(question_results)` | RC-B-06 |
| `profile_snapshot.session_id == session_id` (if carried by `CandidateProfileSnapshot`) | Cross-artifact identity check |
| `knowledge_snapshot.session_id == session_id` (validated before builder is called) | Validated by `replay_node` before constructing builder |
| `scoring_snapshot` and `scoring_narrative` paired invariant (V-SH-01) | Verified at `SessionHistory` load time — not repeated in builder |

### 11.2 At Validation Time (ReplayValidator.validate_session)

`ReplayValidator.validate_session(session: ReplaySession)` replaces `validate_result` (deleted with `ReplayResult`). It enforces:

| Check ID | Invariant |
|---|---|
| RS-V-01 | `session.manifest.session_id == session.session_id` |
| RS-V-02 | `session.manifest.candidate_identity_id == session.candidate_identity_id` |
| RS-V-03 | `session.is_successful=True` requires `session.failure_reason is None` |
| RS-V-04 | `session.is_successful=False` requires `session.failure_reason` non-empty |
| RS-V-05 | `session.replay_level != ReplayLevel.REASONING` |
| RS-V-06 | `session.observation_store_snapshot is None` when `replay_level == PRESENTATION` |
| RS-V-07 | `len(session.question_results) == session.timeline.total_positions` |
| RS-V-08 | All `ReplayQuestionRecord` `question_index` values are unique within the session |
| RS-V-09 | `ReplayTimelineEntry.position` values are contiguous 0..N-1 |
| RS-V-10 | Source priority in manifest: no `FEATURE_ENGINE_RECOMPUTATION` in `STANDARD` mode |

---

## Section 12 — Migration Model for Legacy Replay Artifacts

Extends EPIC-03-DOMAIN-CONTRACTS.md §13 with data model specifics.

### 12.1 ReplayResult Deletion Impact

When `ReplayResult` is deleted:
- `ReplayStatistics.from_result(result: ReplayResult)` is deleted.
- `ReplayStatistics.from_session(session: ReplaySession)` is introduced with an extended field set (adds `question_count`, `has_scoring`).
- `ReplayValidator.validate_result(...)` is deleted.
- `ReplayValidator.validate_session(...)` is introduced (checks defined in §11.2).
- All `ReplayStatistics` fields that were derived from `ReplayResult.profile_snapshot`, `ReplayResult.narrative`, `ReplayResult.coaching_snapshot` continue to be derived from the corresponding `ReplaySession` fields.

### 12.2 New ReplayStatistics Fields (from_session additions)

| New Field | Type | Source | Notes |
|---|---|---|---|
| `question_count` | `int` | `len(session.question_results)` | New in V1.3 |
| `has_scoring` | `bool` | `session.scoring_snapshot is not None` | New in V1.3 |
| `total_follow_up_questions` | `int` | Count of non-None `follow_up_question` in `question_results` | New in V1.3 |

### 12.3 Deletion Sequence (from Domain Contracts §13)

All three migration phases apply without change. Every phase must leave the regression suite green before the next begins.

---

## Section 13 — Replay Determinism Verification Model

### 13.1 Determinism Definition

A replay operation is deterministic when: given the same `session_id` and the same persisted `SessionHistory`, two invocations of `replay_node` produce `ReplaySession` instances that are field-equal on all knowledge fields.

Knowledge fields (determinism-assertable):

| Field | Deterministic? | Notes |
|---|---|---|
| `session_id` | Yes | Constant |
| `candidate_identity_id` | Yes | Constant |
| `schema_version` | Yes | Builder constant |
| `replay_mode` | Yes | Same input |
| `replay_level` | Yes | Same input |
| `profile_snapshot` | Yes | Same persisted object |
| `narrative` | Yes | Same persisted object |
| `coaching_snapshot` | Yes | Same persisted object |
| `scoring_snapshot` | Yes | Same persisted object |
| `question_results` | Yes | Same persisted records + same join |
| `timeline` | Yes | Deterministic sort |
| `session_metadata` | Yes | Same persisted fields |
| `policy_versions` | Yes | Same persisted object |
| `knowledge_epoch` | Yes | Same persisted value |
| `is_successful` | Yes | Same `SessionHistory` availability |
| `failure_reason` | Yes | Same failure path |
| `observation_store_snapshot` | Yes | Same persisted object |

Non-deterministic fields (excluded from determinism assertion):

| Field | Non-Deterministic Element |
|---|---|
| `manifest.replay_timestamp` | UTC timestamp at invocation time |
| `manifest.replay_engine_version` | May change across deployments |

### 13.2 Determinism Test Protocol

The determinism test must:

1. Load a fixed `SessionHistory` fixture (same persisted data).
2. Invoke `replay_node` twice with identical `ReplayRequest`.
3. Assert field-level equality for all knowledge fields listed in §13.1 as deterministic.
4. Explicitly exclude `manifest.replay_timestamp` and `manifest.replay_engine_version` from the equality assertion.
5. Repeat for ≥ 20 distinct `SessionHistory` fixtures (Master Plan go-live checklist).
6. Include fixtures with: `scoring_snapshot=None`, `question_results=()`, `replay_level=KNOWLEDGE`, all `question_types`.

### 13.3 Non-Determinism Failure Classification

If a determinism test fails on a knowledge field, the failure is classified as:

- **P0** if it affects `profile_snapshot`, `narrative`, `coaching_snapshot`, or `scoring_snapshot` — core knowledge artifacts.
- **P1** if it affects `question_results`, `timeline`, or `session_metadata`.
- **P2** if it affects `policy_versions`, `knowledge_epoch`, or `schema_version`.

P0 and P1 failures block EPIC-03 from closing. P2 failures are registered in the Technical Debt Register.

---

## Open Issues

No open issues remain. All reconstruction gaps (RG-01, RG-02, RG-03) are resolved within this document:

| Gap | Resolution | Classification |
|---|---|---|
| RG-01 — `session_date` not in `InterviewMetadata` | Maps to `SessionHistory.created_at` | Data Model Extension (source correction) |
| RG-02 — `session_duration_seconds` not persisted | Aggregated from `question_timeline[*].duration_seconds` | Data Model Extension (aggregation of persisted records) |
| RG-03 — `follow_up_question` missing from `ReplayQuestionRecord` | Added to `ReplayQuestionRecord` field table | Domain Contracts Extension (no ADR required) |

Additional findings resolved:
- Score range clarification: `score` is `0.0–100.0` (percentage scale) — §1.4.
- `candidate_answer` source: `TranscriptEntry.answer_content` joined by `question_id` — §4.1.
- `question_count` source: `len(question_results)`, not `len(transcript)` — §1.6.
- `company` field added to `ReplaySessionMetadata` — §3.
- `seniority` field name mapped to `seniority_level` in projection — §3.

All findings are resolvable within the Data Model layer. No architectural change is required. No ADR amendment is required.

---

*This document is the authoritative Data Model Specification for EPIC-03. Amendments require a recorded rationale and a Freeze Integrity Check per V13-DEVELOPMENT-PLAYBOOK.md §9.*
