# EPIC-04 — Replay UI Experience: Architecture Discovery

**Status:** ARCHITECTURE DISCOVERY COMPLETE  
**Date:** 2026-07-15  
**Epic ID:** EPIC-V13-04  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Architecture Discovery (Playbook §8.1)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-04  
**Precondition:** EPIC-V13-03 CLOSED; `ReplaySession` frozen (ADR-037 D3); `replay_node` implemented.

---

## 1. Executive Summary

### 1.1 Business Objective

Deliver a candidate-facing session replay interface backed by `ReplaySession`. Candidates must be able to navigate any completed session question-by-question, inspect answers, scores, and coaching notes, without any LLM calls or answer re-submission.

### 1.2 Architectural Objective

Implement the Replay UI as a strictly read-only, LLM-free presentation layer consuming `ReplaySession` as its sole data source. No UI component may trigger computation, invoke services, or bypass the `ReplaySession` contract. The UI layer is a pure rendering surface driven by a pre-computed projection artifact.

### 1.3 Scope

- Question-by-question navigation (forward / backward controls)
- Per-question display: question text, candidate answer, execution result (coding), dimensional scores, coaching notes
- Session-level summary panel
- Navigation progress indicator
- Responsive layout (mobile, tablet, desktop)
- Zero LLM calls from any UI component
- Read-only, no re-submission controls

### 1.4 Non-Goals

- Side-by-side session comparison (V2)
- Annotation or bookmarking (V2)
- Sharing or exporting replay (V2)
- AI commentary during replay (V2)
- Re-submission of answers in replay mode (explicitly excluded by Master Plan)

### 1.5 Dependencies

| Dependency | Status | Description |
|---|---|---|
| EPIC-V13-03 | CLOSED | `ReplaySession` frozen; `replay_node` implemented, deterministic, LLM-free |
| EPIC-V13-01 | CLOSED | `Report` is the sole scoring artifact; `ReplaySession` reads `Report`-consistent fields |
| EPIC-V13-02 | CLOSED | `LongitudinalProfile` established; cross-session data stable |
| ADR-037 | Accepted | Replay Engine Architecture; governs `ReplaySession` field set (D3) |
| ADR-033 | Accepted | Unified Report Architecture; `ScoringSnapshot`, `QuestionResultRecord` in `SessionHistory` |
| ADR-003 | Accepted | State-Driven UI; governs rendering layer constraints |

### 1.6 Implementation Risks

| Risk | Severity | Current Assessment |
|---|---|---|
| `ReplaySession` field set insufficient for UI requirements | HIGH | RESOLVED — see §6 AA-01: VERIFIED |
| Navigation state requires new ADR not covered by ADR-003 | MEDIUM | Partially resolved — see §6 AA-03: CONDITIONALLY VERIFIED |
| Performance for 20+ question sessions | MEDIUM | UNVERIFIED — profiling required before ship |
| New UI library dependency required | LOW | UNVERIFIED — confirmation required |

---

## 2. Current Architecture

### 2.1 ReplaySession

`ReplaySession` is the V1.3 canonical, immutable Replay Projection Artifact produced by `replay_node` via `ReplaySessionBuilder`. It is `frozen=True`, `extra=forbid`, and is never persisted.

**File:** `domain/contracts/replay/replay_session.py`

**Field inventory (18 fields):**

| Field | Type | Purpose |
|---|---|---|
| `session_id` | `str` | Identity |
| `candidate_identity_id` | `str` | Identity |
| `schema_version` | `str` | Schema provenance (default `"1.0"`) |
| `replay_mode` | `ReplayMode` | STANDARD / MIGRATION / RECOVERY |
| `replay_level` | `ReplayLevel` | PRESENTATION / KNOWLEDGE (REASONING reserved) |
| `profile_snapshot` | `CandidateProfileSnapshot` | Knowledge profile (features, quality, provenance) |
| `narrative` | `Narrative` | NarrativeInsight list (overview_section, insights) |
| `coaching_snapshot` | `CoachingSnapshot` | Deterministic coaching tree (objectives, actions, recommendations) |
| `scoring_snapshot` | `Optional[ScoringSnapshot]` | Scoring data — `None` if no evaluation |
| `question_results` | `tuple[ReplayQuestionRecord, ...]` | Per-question records |
| `timeline` | `ReplayTimeline` | Derived navigation view (entries, positions) |
| `session_metadata` | `ReplaySessionMetadata` | Session context (role, date, index, etc.) |
| `policy_versions` | `PolicyVersions` | Schema provenance |
| `knowledge_epoch` | `str` | Knowledge pipeline epoch |
| `manifest` | `ReplayManifest` | Audit record (sources, timestamps) |
| `is_successful` | `bool` | Reconstruction outcome |
| `failure_reason` | `Optional[str]` | Non-None when `is_successful=False` |
| `observation_store_snapshot` | `Optional[object]` | KNOWLEDGE level only; None for PRESENTATION |

**Validators:** V-RS-01 through V-RS-06 (is_successful/failure_reason pairing, manifest identity matching, REASONING prohibition, observation_store_snapshot PRESENTATION constraint).

### 2.2 ReplayQuestionRecord

**File:** `domain/contracts/replay/replay_question_record.py`

Per-question replay projection artifact embedded in `ReplaySession.question_results`. Frozen, `extra=forbid`.

**Fields:** `question_id`, `question_index`, `question_type`, `area_label`, `question_prompt`, `candidate_answer`, `score`, `max_score`, `feedback`, `strengths`, `weaknesses`, `follow_up_question`, `execution_status`, `passed_tests`, `total_tests`, `ai_hint_explanation`, `ai_hint_suggestion`, `attempts`.

**Properties:** `is_coding_question`, `has_hint`, `score_ratio`.

**Validators:** V-RQR-01 (max_score > 0), V-RQR-02 (score ≤ max_score), V-RQR-04 (coding fields co-presence).

### 2.3 ReplayTimeline

**File:** `domain/contracts/replay/replay_timeline.py`

Derived navigation view over `ReplaySession.question_results`. Produced by `ReplaySessionBuilder`. Not persisted.

**Fields:** `entries: tuple[ReplayTimelineEntry, ...]`, `total_positions`, `first_position`, `last_position`, `is_empty`.

`ReplayTimelineEntry`: `position`, `question_id`, `question_index`, `area_label`, `question_type`.

### 2.4 ReplaySessionMetadata

**File:** `domain/contracts/replay/replay_session_metadata.py`

Session-level context assembled by `ReplaySessionBuilder` from `SessionHistory`.

**Fields:** `interview_index`, `session_date`, `role`, `seniority_level`, `interview_mode`, `question_count`, `session_duration_seconds`, `company`.

### 2.5 replay_node and Replay Graph

**Files:** `app/graph/nodes/replay_node.py`, `app/graph/replay_graph.py`

`replay_node` is the sole LangGraph node of the standalone Replay Graph (`replay_node → END`). It is the sole writer of `ReplaySession`. It:
- Loads `SessionHistory` from persistence (read-only, via injected `SessionLoader`)
- Instantiates `ReplayFeatureEngine`
- Calls `ReplaySessionBuilder.build()`
- Returns `ReplayGraphState` with `result` populated

Topology is independent from the live session graph. `ReplayGraphState` does not reference `InterviewState`.

### 2.6 Current Frontend Architecture

The existing UI is a Python-based Gradio/Streamlit application (no dedicated React/Next.js frontend found). Key components:

- **`UIStateMachine`** (`app/ui/state_machine/ui_state_machine.py`): Resolves `UIState` from `InterviewState`. States: SETUP, QUESTION, FEEDBACK, RETRY, COMPLETION, REPORT, PROCESSING. No REPLAY state exists.
- **`UIState`** (`app/ui/ui_state.py`): Enum of UI states. Does not include a REPLAY state.
- **`ReportViewModelBuilder`** (`app/ui/views/report/report_view_model_builder.py`): Builds report view models from `FinalReportDTO` or domain `Report`.
- **`FinalReportDTO`** (`app/ui/dto/final_report_dto.py`): Sole DTO for report presentation (EPIC-01 outcome).
- **View files:** `app/ui/views/report/` contains section-based renderers (coaching, narrative, scoring, etc.).

**Critical gap:** No Replay UI view, state, controller, or navigation component exists. The REPLAY flow is absent from `UIStateMachine`, `UIState`, and all view modules. This is the primary implementation target of EPIC-04.

### 2.7 Existing UI Infrastructure Relevant to EPIC-04

| Infrastructure | File | Relevance |
|---|---|---|
| `UIStateMachine` | `app/ui/state_machine/ui_state_machine.py` | Must be extended to add REPLAY state |
| `UIState` | `app/ui/ui_state.py` | Must add REPLAY enum value |
| Report section renderers | `app/ui/views/report/sections/` | Pattern reference for per-question rendering |
| `ReportViewModelBuilder` | `app/ui/views/report/report_view_model_builder.py` | Pattern reference for view model construction |
| `app/graph/replay_graph.py` | Replay Graph | Sole invocation point for `replay_node` |
| `app/ui/bindings/ui_bindings.py` | UI event bindings | Must add replay entry point |

### 2.8 Relevant ADRs

| ADR | Decision | Relevance to EPIC-04 |
|---|---|---|
| ADR-037 D1 | `ReplaySession` as canonical artifact | Sole data source for Replay UI |
| ADR-037 D3 | Field sufficiency guarantee | All UI panels must be sourced from this field set |
| ADR-037 D4 | Replay Graph topology | Entry mechanism into `replay_node` |
| ADR-037 D5 | Invariants I-11, I-R01–I-R09 | LLM-free, read-only, isolation constraints |
| ADR-033 D1/D2 | `ScoringSnapshot`, `QuestionResultRecord` | Scoring and per-question data in `ReplaySession` |
| ADR-003 | State-Driven UI | Rendering layer must derive from state, no orchestration |

---

## 3. Target Architecture

### 3.1 Major UI Subsystems

The Replay UI is organized into four major subsystems:

**A. Replay Entry Point**
A new UI state (`REPLAY`) is added to `UIStateMachine` and `UIState`. The entry point is triggered from the report view (replay link — ADR-033 D6 intent) or directly from a session history list. It invokes `build_replay_graph(session_loader).invoke(ReplayRequest(...))` and routes the result to the Replay View Controller.

**B. Replay View Controller**
Manages the active `ReplaySession` and the current navigation position. It holds `current_position: int` (driven by forward/backward controls) and derives the current `ReplayQuestionRecord` from `ReplaySession.question_results[current_position]`. No computation occurs here — only index tracking.

**C. Replay Panel Renderers**
Stateless rendering components consuming `ReplaySession` and `ReplayQuestionRecord` fields directly:
- `ReplaySessionSummaryPanel`: renders session-level data from `session_metadata` and `scoring_snapshot`.
- `ReplayQuestionPanel`: renders per-question data from `ReplayQuestionRecord`.
- `ReplayNavigationBar`: renders progress indicator from `ReplayTimeline`; forward/backward controls update `current_position`.
- `ReplayCoachingPanel`: renders `coaching_snapshot` and `narrative` at session level.
- `ReplayScoringPanel`: renders `scoring_snapshot` (conditional on `has_scoring`).

**D. Replay Error Boundary**
Handles `ReplaySession(is_successful=False)` by rendering a candidate-facing error panel sourced from `failure_reason`. Never exposes internal state.

### 3.2 Data Flow

```
Candidate triggers replay
        ↓
ReplayRequest(session_id, replay_mode=STANDARD, replay_level=PRESENTATION)
        ↓
build_replay_graph(session_loader).invoke(request)
        ↓
replay_node → ReplaySessionBuilder.build() → ReplaySession (frozen)
        ↓
Replay View Controller receives ReplaySession
        ↓
current_position: int (starts at 0)
        ↓
ReplayQuestionRecord = session.question_results[current_position]
        ↓
Panel Renderers consume ReplaySession + ReplayQuestionRecord
        ↓
UI renders read-only replay view
```

Navigation events (forward/backward) update `current_position` only. No re-invocation of `replay_node`. No computation.

### 3.3 Ownership Boundaries

| Boundary | Owner | Constraint |
|---|---|---|
| `ReplaySession` production | `replay_node` / `ReplaySessionBuilder` | Sole writer; I-R01 |
| Navigation position state | Replay View Controller | UI-only state; not persisted |
| Panel rendering | Replay Panel Renderers | Read-only; no service calls |
| Error display | Replay Error Boundary | Sources `failure_reason` only |
| `UIState.REPLAY` transition | `UIStateMachine` | Derives from state, not from UI input |

### 3.4 Read-Only Architecture

Every Replay UI component is strictly read-only:
- No write to `InterviewState`, `SessionHistory`, `LongitudinalProfile`, or any domain artifact.
- No invocation of `KnowledgePipeline`, `FeatureEngine`, `CoachingEngine`, or any LLM-backed service.
- No re-submission controls.
- Navigation position is the only mutable state; it is scoped to the current Replay View session and is not persisted.

### 3.5 LLM-Free Enforcement

LLM-freedom is enforced at three layers:
1. **Data layer:** `ReplaySession` fields are all read from persisted `SessionHistory` — no LLM call chain reachable (ADR-037 D5 I-11).
2. **Rendering layer:** Panel renderers are pure functions of `ReplaySession` fields. No service injection allowed.
3. **Architectural test:** An existing test (I-11 enforcement, EPIC-03) verifies zero LLM invocations during `replay_node` execution. EPIC-04 must add a parallel architectural test verifying zero LLM invocations during UI render path traversal.

### 3.6 Interaction with ReplaySession

The UI layer is the sole declared reader of `ReplaySession` (ADR-037 D1 §1.3). It accesses `ReplaySession` fields as follows:

| UI Panel | ReplaySession Fields Consumed |
|---|---|
| Session Summary | `session_metadata`, `scoring_snapshot`, `is_successful`, `schema_version` |
| Navigation Bar | `timeline`, `question_results` (count only via `question_count` property) |
| Question Panel | `question_results[i]` (full `ReplayQuestionRecord`) |
| Coaching Panel | `coaching_snapshot`, `narrative` |
| Scoring Panel | `scoring_snapshot` (conditional on `has_scoring`) |
| Error Boundary | `failure_reason`, `is_successful` |
| Audit/Meta | `manifest`, `policy_versions`, `knowledge_epoch` |

---

## 4. Component Inventory

Every UI component required for EPIC-04 is enumerated below. All components are read-only.

---

### C-01 — ReplayEntryPoint

| Field | Value |
|---|---|
| **Name** | `ReplayEntryPoint` |
| **Responsibility** | Accepts a `session_id`, invokes `build_replay_graph` with the session loader, receives `ReplaySession`, routes to `ReplayViewController` or `ReplayErrorBoundary` |
| **Owner** | EPIC-04 |
| **Input data** | `session_id: str`, injected `session_loader: SessionLoader` |
| **Output** | `ReplaySession` (passed to `ReplayViewController`) |
| **Dependencies** | `build_replay_graph`, `ReplayRequest`, `ReplaySession` |
| **Read/Write** | Read-only (invokes Replay Graph, reads result) |
| **ReplaySession fields consumed** | `is_successful`, `failure_reason` (routing decision) |

---

### C-02 — ReplayViewController

| Field | Value |
|---|---|
| **Name** | `ReplayViewController` |
| **Responsibility** | Owns `current_position: int`; derives `current_record: ReplayQuestionRecord = session.question_results[current_position]`; distributes `ReplaySession` and `current_record` to panel renderers |
| **Owner** | EPIC-04 |
| **Input data** | `ReplaySession` (complete), navigation events (forward / backward) |
| **Output** | `current_position`, `current_record`, `ReplaySession` to child panels |
| **Dependencies** | `ReplaySession`, `ReplayQuestionRecord`, `ReplayTimeline` |
| **Read/Write** | Navigation position is the only mutable state; `ReplaySession` is read-only |
| **ReplaySession fields consumed** | `question_results`, `timeline`, `question_count` (property) |

---

### C-03 — ReplaySessionSummaryPanel

| Field | Value |
|---|---|
| **Name** | `ReplaySessionSummaryPanel` |
| **Responsibility** | Renders session-level summary: session date, role, seniority, interview mode, question count, duration, overall score (if available) |
| **Owner** | EPIC-04 |
| **Input data** | `ReplaySessionMetadata`, `Optional[ScoringSnapshot]`, `is_successful: bool` |
| **Output** | Rendered session summary UI |
| **Dependencies** | `ReplaySessionMetadata`, `ScoringSnapshot` |
| **Read/Write** | Read-only |
| **ReplaySession fields consumed** | `session_metadata` (all fields), `scoring_snapshot` (`overall_score`, `hire_decision`, `level`), `is_successful` |

---

### C-04 — ReplayNavigationBar

| Field | Value |
|---|---|
| **Name** | `ReplayNavigationBar` |
| **Responsibility** | Renders progress indicator (current position / total); forward and backward navigation controls; reflects current position from `ReplayViewController` |
| **Owner** | EPIC-04 |
| **Input data** | `ReplayTimeline`, `current_position: int` |
| **Output** | Navigation UI; navigation events to `ReplayViewController` |
| **Dependencies** | `ReplayTimeline`, `ReplayTimelineEntry` |
| **Read/Write** | Read-only (position state owned by `ReplayViewController`) |
| **ReplaySession fields consumed** | `timeline` (`entries`, `total_positions`, `first_position`, `last_position`, `is_empty`) |

---

### C-05 — ReplayQuestionPanel

| Field | Value |
|---|---|
| **Name** | `ReplayQuestionPanel` |
| **Responsibility** | Renders per-question view: question prompt, area label, question type, candidate answer, score, max score, feedback, strengths, weaknesses, follow-up question, execution result (coding only), AI hint (if present) |
| **Owner** | EPIC-04 |
| **Input data** | `ReplayQuestionRecord` (current record from `ReplayViewController`) |
| **Output** | Rendered per-question UI |
| **Dependencies** | `ReplayQuestionRecord` |
| **Read/Write** | Read-only |
| **ReplaySession fields consumed** | `question_results[i]`: `question_prompt`, `area_label`, `question_type`, `candidate_answer`, `score`, `max_score`, `feedback`, `strengths`, `weaknesses`, `follow_up_question`, `execution_status`, `passed_tests`, `total_tests`, `ai_hint_explanation`, `ai_hint_suggestion`, `attempts`, `question_index` |

---

### C-06 — ReplayExecutionResultPanel

| Field | Value |
|---|---|
| **Name** | `ReplayExecutionResultPanel` |
| **Responsibility** | Renders coding question execution result (test pass/fail counts, execution status). Conditional — only rendered when `is_coding_question=True` |
| **Owner** | EPIC-04 |
| **Input data** | `ReplayQuestionRecord` (conditional on `is_coding_question`) |
| **Output** | Rendered execution result UI |
| **Dependencies** | `ReplayQuestionRecord` |
| **Read/Write** | Read-only |
| **ReplaySession fields consumed** | `question_results[i]`: `execution_status`, `passed_tests`, `total_tests` |

---

### C-07 — ReplayScoringPanel

| Field | Value |
|---|---|
| **Name** | `ReplayScoringPanel` |
| **Responsibility** | Renders session-level dimensional scores, hire decision, hiring probability, percentile rank. Conditional — only rendered when `has_scoring=True` |
| **Owner** | EPIC-04 |
| **Input data** | `Optional[ScoringSnapshot]` |
| **Output** | Rendered scoring UI |
| **Dependencies** | `ScoringSnapshot` |
| **Read/Write** | Read-only |
| **ReplaySession fields consumed** | `scoring_snapshot`: `overall_score`, `dimension_scores`, `hire_decision`, `hiring_probability`, `percentile_rank`, `level`, `gating_triggered`, `gating_reason` |

---

### C-08 — ReplayCoachingPanel

| Field | Value |
|---|---|
| **Name** | `ReplayCoachingPanel` |
| **Responsibility** | Renders session-level coaching: deterministic coaching objectives, actions, and study recommendations from `coaching_snapshot`; narrative insights from `narrative` |
| **Owner** | EPIC-04 |
| **Input data** | `CoachingSnapshot`, `Narrative` |
| **Output** | Rendered coaching UI |
| **Dependencies** | `CoachingSnapshot`, `Narrative` |
| **Read/Write** | Read-only |
| **ReplaySession fields consumed** | `coaching_snapshot` (objectives, actions, recommendations), `narrative` (insights, overview_section) |

---

### C-09 — ReplayErrorBoundary

| Field | Value |
|---|---|
| **Name** | `ReplayErrorBoundary` |
| **Responsibility** | Renders candidate-facing error panel when `is_successful=False`. Sources only `failure_reason`. Never exposes internal state or stack traces. |
| **Owner** | EPIC-04 |
| **Input data** | `ReplaySession` (`is_successful=False`, `failure_reason`) |
| **Output** | Rendered error UI (candidate-friendly) |
| **Dependencies** | `ReplaySession` |
| **Read/Write** | Read-only |
| **ReplaySession fields consumed** | `is_successful`, `failure_reason` |

---

### C-10 — UIStateMachine (extended)

| Field | Value |
|---|---|
| **Name** | `UIStateMachine` (REPLAY state extension) |
| **Responsibility** | Add `REPLAY` state transition logic. A replay is entered when a `session_id` is submitted for replay. Exits on cancel or session end. |
| **Owner** | EPIC-04 (extension of existing component) |
| **Input data** | `InterviewState` (or replay trigger signal) |
| **Output** | `UIState.REPLAY` |
| **Dependencies** | `UIState`, `InterviewState` (for state resolution) |
| **Read/Write** | Read-only (state derivation only; ADR-003) |
| **ReplaySession fields consumed** | None directly — `UIStateMachine` does not consume `ReplaySession` |

---

### C-11 — ReplayAuditPanel (optional)

| Field | Value |
|---|---|
| **Name** | `ReplayAuditPanel` |
| **Responsibility** | Renders audit metadata: `manifest` (replay timestamp, engine version, source provenance), `policy_versions`, `knowledge_epoch`, `schema_version`. Optional candidate-facing metadata display. |
| **Owner** | EPIC-04 |
| **Input data** | `ReplayManifest`, `PolicyVersions`, `knowledge_epoch`, `schema_version` |
| **Output** | Rendered audit/metadata UI |
| **Dependencies** | `ReplayManifest`, `PolicyVersions` |
| **Read/Write** | Read-only |
| **ReplaySession fields consumed** | `manifest`, `policy_versions`, `knowledge_epoch`, `schema_version` |

---

## 5. Initial Traceability Matrix

This is the first version of the Traceability Matrix. It links every Master Plan EPIC-V13-04 requirement to `ReplaySession` fields and consuming UI components.

| Master Plan Requirement | ReplaySession Field(s) | Consuming UI Component | Verification Artifact |
|---|---|---|---|
| Question-by-question navigation (forward/backward controls) | `timeline`, `question_results` | C-04 `ReplayNavigationBar`, C-02 `ReplayViewController` | Navigation integration test: forward/backward advances position |
| Display question text per question | `question_results[i].question_prompt` | C-05 `ReplayQuestionPanel` | Unit test: question prompt rendered from `ReplayQuestionRecord` |
| Display candidate answer per question | `question_results[i].candidate_answer` | C-05 `ReplayQuestionPanel` | Unit test: candidate answer rendered |
| Display execution result (coding questions) | `question_results[i].execution_status`, `passed_tests`, `total_tests` | C-06 `ReplayExecutionResultPanel` | Unit test: execution panel visible iff `is_coding_question=True` |
| Display dimensional scores per question | `question_results[i].score`, `max_score` | C-05 `ReplayQuestionPanel` | Unit test: score and max_score rendered |
| Display coaching notes per question | `question_results[i].feedback`, `strengths`, `weaknesses` | C-05 `ReplayQuestionPanel` | Unit test: feedback rendered from `ReplayQuestionRecord` |
| Session-level summary panel | `session_metadata`, `scoring_snapshot` | C-03 `ReplaySessionSummaryPanel` | Integration test: summary panel populated from `ReplaySessionMetadata` |
| Navigation progress indicator | `timeline.total_positions`, current position | C-04 `ReplayNavigationBar` | Unit test: progress indicator reflects position |
| Responsive layout (mobile, tablet, desktop) | N/A | All panel renderers | Responsive layout test (CSS/layout) |
| Zero LLM calls from any UI component | N/A (enforced at data layer) | All components | Architectural test: mock LLM services; assert zero invocations during render path |
| Read-only, no re-submission controls | N/A | C-05, C-06, C-02 | Architectural test: no write call reachable from any replay render path |
| Production-quality UX (no placeholder states) | `is_successful`, `failure_reason` | C-09 `ReplayErrorBoundary` | E2E test: error boundary renders candidate-facing message |
| Session metadata display (role, date, index) | `session_metadata.role`, `session_date`, `interview_index` | C-03 `ReplaySessionSummaryPanel` | Unit test: metadata fields rendered |
| Session scoring display (overall score, hire decision) | `scoring_snapshot.overall_score`, `hire_decision` | C-07 `ReplayScoringPanel` | Unit test: scoring panel visible iff `has_scoring=True` |
| Session coaching display (coaching objectives, narrative) | `coaching_snapshot`, `narrative` | C-08 `ReplayCoachingPanel` | Unit test: coaching panel rendered from `CoachingSnapshot` and `Narrative` |
| Follow-up question display | `question_results[i].follow_up_question` | C-05 `ReplayQuestionPanel` | Unit test: follow-up rendered when non-None |
| AI hint display | `question_results[i].ai_hint_explanation`, `ai_hint_suggestion` | C-05 `ReplayQuestionPanel` | Unit test: hint rendered when `has_hint=True` |

**Missing field assessment:** No Master Plan requirement has a missing source field in `ReplaySession`. AA-01 is VERIFIED (see §6).

---

## 6. Architecture Assumptions Register

All assumptions from `EPIC-04-OVERVIEW.md §9` are evaluated below. Status updated from UNVERIFIED where Architecture Discovery can verify.

---

### AA-01 — ReplaySession Field Sufficiency

| Field | Value |
|---|---|
| **ID** | AA-01 |
| **Description** | `ReplaySession` field set (ADR-037 D3) is sufficient to render all UI panels defined in Master Plan §4 EPIC-V13-04 |
| **Status** | **VERIFIED** |
| **Rationale** | Architecture Discovery maps every Master Plan requirement to a `ReplaySession` field in §5. All 17 requirements have at least one source field. `ReplayQuestionRecord` covers all per-question requirements. `session_metadata` covers all session-level metadata. `scoring_snapshot` covers scoring (conditional). `coaching_snapshot` and `narrative` cover coaching. `timeline` covers navigation. No field gap identified. |
| **Verification Document** | EPIC-04-REPLAY-UI.md §5 (Traceability Matrix) |

---

### AA-02 — No LLM Call Reachable from Replay UI Render Path

| Field | Value |
|---|---|
| **ID** | AA-02 |
| **Description** | No LLM call is reachable from any Replay UI component render path |
| **Status** | **CONDITIONALLY VERIFIED** |
| **Rationale** | Architecture Discovery confirms that `ReplaySession` is a pre-computed projection artifact containing no LLM computation (ADR-037 D1 §1.2). Panel renderers are specified as pure functions of `ReplaySession` fields (§3.5). No service injection is permitted. However, full verification requires an architectural test that mocks LLM service interfaces and asserts zero invocations during UI render traversal. This test is part of implementation, not discovery. The architectural constraint is sound; the enforcement test is a required implementation artifact. |
| **Verification Document** | EPIC-04-ARCHITECTURE-FREEZE.md (enforcement test mandate) |

---

### AA-03 — ADR-003 Governs Navigation State Without New ADR

| Field | Value |
|---|---|
| **ID** | AA-03 |
| **Description** | ADR-003 (State-Driven UI) governs replay navigation state without requiring a new ADR |
| **Status** | **CONDITIONALLY VERIFIED** |
| **Rationale** | ADR-003 mandates that the UI derives entirely from state and must never own orchestration logic. The Replay UI satisfies this: `ReplaySession` is the authoritative state; panel renderers derive from it; `ReplayViewController` owns only navigation position (a lightweight UI-scoped index, not a domain state). The key question is whether `current_position: int` is a UI state (governed by ADR-003 without needing a new ADR) or a new domain concept requiring an ADR. Architecture Discovery assessment: `current_position` is UI-scoped ephemeral state equivalent to a cursor in a list — it is directly analogous to `allowed_actions` in the live session (a derived UI state). ADR-003 governs this without modification. **No new ADR is required for navigation state.** However, this must be confirmed in the Domain Contracts document. |
| **Verification Document** | EPIC-04-DOMAIN-CONTRACTS.md (navigation state contract) |

---

### AA-04 — ADR-037 Requires No Modification

| Field | Value |
|---|---|
| **ID** | AA-04 |
| **Description** | ADR-037 requires no modification to satisfy EPIC-04 UI requirements |
| **Status** | **VERIFIED** |
| **Rationale** | The Traceability Matrix in §5 confirms that every Master Plan requirement for EPIC-04 is satisfied by the existing `ReplaySession` field set (ADR-037 D3 §3.1). No additional field is required. No modification to `ReplaySession`, `ReplaySessionBuilder`, or `replay_node` is necessary. ADR-037 D3 §3.5 explicitly declares EPIC-04 as the sole consumer and states that no ADR amendment is required unless a missing field is discovered. No missing field was discovered. |
| **Verification Document** | EPIC-04-REPLAY-UI.md §5 (Traceability Matrix) |

---

### AA-05 — Replay UI Is Fully Read-Only

| Field | Value |
|---|---|
| **ID** | AA-05 |
| **Description** | Replay UI is fully read-only; no write path to `InterviewState`, `SessionHistory`, or any domain artifact |
| **Status** | **VERIFIED** (architecturally) |
| **Rationale** | Architecture Discovery establishes that all components in §4 are read-only by design. Navigation position is the only mutable state and is scoped to the UI session — not persisted. Panel renderers have no service injection. `ReplayViewController` does not write to any domain artifact. Structural read-only enforcement requires an architectural test (implementation artifact). The design constraint is sound. |
| **Verification Document** | EPIC-04-DOMAIN-CONTRACTS.md (read-only constraint specification) |

---

### AA-06 — ReplaySession Produced On Demand; No UI-Layer Caching Needed

| Field | Value |
|---|---|
| **ID** | AA-06 |
| **Description** | `ReplaySession` is produced on demand per request; no caching or persistence is needed at the UI layer |
| **Status** | **VERIFIED** |
| **Rationale** | ADR-037 D1 §1.4 confirms `ReplaySession` is never persisted. Every replay request triggers a fresh reconstruction. Architecture Discovery confirms that the Replay UI receives a `ReplaySession` instance from `replay_node` and navigates it in memory — no caching layer is needed or appropriate. Performance implications for long sessions are flagged under AA-08. |
| **Verification Document** | ADR-037 D1 §1.4; EPIC-04-REPLAY-UI.md §6 AA-08 |

---

### AA-07 — Responsive Layout Within Existing Frontend Stack

| Field | Value |
|---|---|
| **ID** | AA-07 |
| **Description** | Responsive layout (mobile, tablet, desktop) is achievable within the existing frontend stack without new dependencies |
| **Status** | **UNVERIFIED** |
| **Rationale** | The existing UI is a Python-based application (Gradio or Streamlit pattern inferred from `app/ui/` structure). Architecture Discovery confirms no React/Next.js frontend exists. Responsive layout in the existing stack depends on the specific framework in use. This assumption cannot be verified at the Architecture Discovery level without profiling the current UI framework's responsive capabilities. Must be verified in the Implementation Plan. |
| **Verification Document** | EPIC-04-IMPLEMENTATION-PLAN.md |

---

### AA-08 — Performance Acceptable for 20+ Question Sessions

| Field | Value |
|---|---|
| **ID** | AA-08 |
| **Description** | Performance is acceptable for sessions of 20+ questions without architectural changes |
| **Status** | **UNVERIFIED** |
| **Rationale** | Architecture Discovery identifies no architectural blocker for performance — `ReplaySession` is loaded once and navigation is index-based (O(1) per step). However, the Master Plan explicitly flags this as a risk requiring a 20-question fixture profiling run before shipping. This cannot be verified by architecture analysis alone. Requires an implementation-phase profiling gate. |
| **Verification Document** | EPIC-04-IMPLEMENTATION-PLAN.md |

---

**Summary of status changes:**

| ID | Previous Status | New Status | Changed By |
|---|---|---|---|
| AA-01 | UNVERIFIED | VERIFIED | Architecture Discovery §5 Traceability Matrix |
| AA-02 | UNVERIFIED | CONDITIONALLY VERIFIED | Architecture Discovery §3.5 |
| AA-03 | UNVERIFIED | CONDITIONALLY VERIFIED | Architecture Discovery §3.2, ADR-003 review |
| AA-04 | UNVERIFIED | VERIFIED | Architecture Discovery §5 Traceability Matrix |
| AA-05 | UNVERIFIED | VERIFIED (architecturally) | Architecture Discovery §4 Component Inventory |
| AA-06 | UNVERIFIED | VERIFIED | ADR-037 D1 §1.4 confirmed |
| AA-07 | UNVERIFIED | UNVERIFIED | Requires framework-specific implementation verification |
| AA-08 | UNVERIFIED | UNVERIFIED | Requires profiling fixture run |

**Note:** AA-07 and AA-08 remain UNVERIFIED and must be resolved before Architecture Freeze. They are not blockers for Domain Contracts authoring.

---

## 7. Open Issues

### BLOCKER

None identified. All Master Plan requirements have source fields in `ReplaySession`.

---

### WARNING

**W-01 — `UIState.REPLAY` State Machine Extension**

- **Type:** WARNING
- **Description:** `UIStateMachine` currently resolves states from `InterviewState`. Adding `UIState.REPLAY` requires a new transition path. It is unclear whether the REPLAY state is driven by a field in `InterviewState` (e.g., an active `session_id` submitted for replay) or by a separate state container.
- **Risk:** If REPLAY state requires a field in `InterviewState`, the `InterviewState` contract must be extended, which requires a new ADR or amendment. If it is driven by a separate mechanism, the `UIStateMachine` resolution logic must handle a mixed signal.
- **Resolution path:** Domain Contracts document must specify the navigation state contract and confirm whether `InterviewState` is extended or bypassed.
- **ADR candidate:** Yes, if `InterviewState` extension is required.

**W-02 — Replay Entry Trigger Integration**

- **Type:** WARNING
- **Description:** How the Replay UI is entered (from report view, from session history list, or from a direct URL) is not specified in the Master Plan. The `build_replay_graph` invocation point requires a defined entry mechanism in the UI layer.
- **Risk:** Without a defined entry point, the Domain Contracts cannot specify the navigation state contract completely.
- **Resolution path:** Domain Contracts document must define the entry trigger mechanism.

**W-03 — AA-07 (Responsive Layout) Unverified**

- **Type:** WARNING
- **Description:** The existing frontend stack's responsive layout capability is unverified. If the stack cannot support responsive layout without new dependencies, a new dependency must be introduced and justified before Architecture Freeze.
- **Resolution path:** EPIC-04-IMPLEMENTATION-PLAN.md must confirm stack capability.

**W-04 — AA-08 (Performance for 20+ Questions) Unverified**

- **Type:** WARNING
- **Description:** Performance acceptability for 20+ question sessions is unverified. The Master Plan explicitly flags this as a risk.
- **Resolution path:** Implementation Plan must include a profiling gate with a 20-question fixture.

**W-05 — `ScoringSnapshot` Field Subset for Session Summary**

- **Type:** WARNING
- **Description:** `ReplayScoringPanel` (C-07) consumes a subset of `ScoringSnapshot` fields. The Domain Contracts document must specify which fields are rendered and which are not surfaced in the Replay UI, to avoid dead field findings in the Traceability Matrix.
- **Resolution path:** Domain Contracts Traceability Matrix must enumerate all consumed and unconsumed `ScoringSnapshot` fields with justification.

---

### INFORMATION

**I-01 — `ReplayLevel.KNOWLEDGE` and `ReplayLevel.REASONING` Are Out of Scope**

All EPIC-04 UI components operate at `ReplayLevel.PRESENTATION` only. KNOWLEDGE-level fields (`observation_store_snapshot`) are not consumed by any UI component. REASONING is reserved. This is consistent with ADR-037 D3 §3.3.

**I-02 — `ReplayStatistics` Is Not a UI Consumer**

`ReplayStatistics` (`domain/contracts/replay/replay_statistics.py`) is a derived aggregate for testing and observability, not a UI component. It is not in scope for EPIC-04 UI rendering.

**I-03 — `ReplayManifest` / `ReplayAuditPanel` Is Optional**

C-11 `ReplayAuditPanel` is flagged as optional. The Master Plan does not explicitly require audit metadata display in the candidate-facing replay UI. This component may be scoped out of the production MVP. Domain Contracts must make a binary decision.

**I-04 — No Frontend Framework Migration Implied**

EPIC-04 does not introduce a new frontend framework. The Replay UI is built within the existing Python-based UI layer. A React/Next.js frontend is not in scope for V1.3 (referenced in user rules but not relevant to this epic's implementation target).

**I-05 — `ReplaySession.timeline` Provides All Navigation Data**

`ReplayTimeline` (including `entries`, `total_positions`, `first_position`, `last_position`, `is_empty`) fully covers the navigation progress indicator requirement without additional derivation. This confirms the navigation bar implementation is trivially satisfiable.

---

## 8. Recommendation

### Next Architecture Document

**Proceed to:** `EPIC-04-DOMAIN-CONTRACTS.md`

**Rationale:**
- AA-01 (field sufficiency) and AA-04 (ADR-037 unchanged) are VERIFIED. No new ADR is required at this stage.
- AA-05 (read-only constraint) is architecturally confirmed and needs only a formal contract specification.
- AA-03 (ADR-003 navigation state) is CONDITIONALLY VERIFIED. The Domain Contracts document must formalize the navigation state contract and confirm ADR-003 sufficiency.
- Open issues W-01 and W-02 (state machine extension, entry trigger) are the primary open decisions to resolve in Domain Contracts.
- AA-07 and AA-08 remain UNVERIFIED but are not blockers for Domain Contracts — they are resolved in the Implementation Plan.

**Domain Contracts document must include:**
1. Navigation state contract (`current_position`, entry trigger, state machine extension)
2. Per-component field contracts (all C-01 through C-11 inputs formally specified)
3. Traceability Matrix (complete — every `ReplaySession` field mapped or justified as unconsumed)
4. Read-only constraint specification (AA-05 formal verification)
5. Resolution of W-01 (UIState extension) and W-02 (entry trigger)
6. Binary decision on C-11 `ReplayAuditPanel` (include or exclude)

**ADR authoring:** Not required at this stage. ADR-003 and ADR-037 are sufficient as evaluated. Conditional: if Domain Contracts reveal that `InterviewState` must be extended to support the REPLAY state transition (W-01), a new ADR is required before Architecture Freeze.

---

## Validation

This document satisfies Architecture Discovery DoD (Playbook §8.1):

- [x] Current state vs. target state analysis is complete (§2, §3)
- [x] All affected subsystems are identified (§2.6, §3.1)
- [x] All confirmed decisions are listed with their governing ADR (§2.8, §3)
- [x] All missing decisions are listed as open items (§7)
- [x] All risks are identified and classified (§7)
- [x] Component Inventory section is complete (§4 — 11 components)
- [x] Architecture Assumptions Register is populated — all 8 assumptions evaluated; 4 VERIFIED, 2 CONDITIONALLY VERIFIED, 2 UNVERIFIED (none missing)
- [x] No code is produced or modified

**Every ReplaySession field evaluated:** Yes (§2.1, §4, §5)  
**Every Master Plan requirement in Traceability Matrix:** Yes (§5 — 17 requirements)  
**Every UI component in Component Inventory:** Yes (§4 — C-01 through C-11)  
**Every assumption reviewed:** Yes (§6 — all 8 assumptions)  
**All findings classified:** Yes (§7 — BLOCKER / WARNING / INFORMATION)  
**No implementation decisions made:** Confirmed
