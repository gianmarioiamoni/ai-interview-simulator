# EPIC-04 — Replay UI Experience: Domain Contracts

**Status:** DOMAIN CONTRACTS COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-04  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Domain Contracts (Playbook §8.2)  
**Precondition:** EPIC-04-REPLAY-UI.md (Architecture Discovery) COMPLETE  
**Governing ADRs:** ADR-037, ADR-033, ADR-003  
**Sole Data Source:** `ReplaySession` (frozen, `domain/contracts/replay/replay_session.py`)

---

## 1. Purpose and Scope

This document specifies the complete field-level contracts for every UI component identified in the Architecture Discovery (EPIC-04-REPLAY-UI.md §4). It resolves open issues W-01 and W-02 from the Architecture Discovery. It contains the complete Traceability Matrix and the ReplaySession Consumption Audit.

**Constraints enforced by this document:**
- Every component contract specifies inputs sourced exclusively from `ReplaySession` fields.
- No component may write to any domain artifact.
- No component may invoke a service, pipeline, or LLM-backed operation.
- Navigation position (`current_position`) is the sole mutable UI state; it is not persisted.
- `ReplayAuditPanel` (C-11) is **excluded** from the V1.3 production scope (see §2.11).

---

## 2. Component Contracts

### 2.1 — C-01: ReplayEntryPoint

**Responsibility:** Accepts a replay trigger carrying a `session_id`, invokes the Replay Graph, receives the resulting `ReplaySession`, and routes to `ReplayViewController` (success) or `ReplayErrorBoundary` (failure).

**Sole Data Source:** `session_id` (trigger input); `ReplaySession` (output of Replay Graph).

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `session_id` | `str` | Replay trigger (UI event, report link, or session history list) | Required |

**Outputs:**

| Field | Type | Destination |
|---|---|---|
| `ReplaySession` | `ReplaySession` | `ReplayViewController` (on success) or `ReplayErrorBoundary` (on failure) |

**Invariants:**
- I-C01-01: `session_id` must be non-empty. An empty `session_id` is rejected before Replay Graph invocation; a candidate-facing error is surfaced.
- I-C01-02: `ReplayEntryPoint` may not persist `ReplaySession` or cache it beyond the current UI session.
- I-C01-03: Routing decision is based solely on `ReplaySession.is_successful`. If `is_successful=True`, route to `ReplayViewController`. If `is_successful=False`, route to `ReplayErrorBoundary`.
- I-C01-04: No LLM call, no service invocation other than `build_replay_graph(session_loader).invoke(ReplayRequest(...))`.

**ReplaySession fields consumed:** `is_successful`, `failure_reason` (routing gate only; full `ReplaySession` passed to `ReplayViewController`).

**Read/Write:** Read-only.

---

### 2.2 — C-02: ReplayViewController

**Responsibility:** Owns the navigation position cursor (`current_position: int`). Derives the current `ReplayQuestionRecord` from `ReplaySession.question_results[current_position]`. Distributes `ReplaySession` and `current_record` to all panel renderers.

**Sole Data Source:** `ReplaySession` (received from C-01).

**Navigation State Contract:**

`current_position` is a UI-scoped ephemeral integer cursor. It is:
- Initialised to `0` when `ReplaySession` is received.
- Incremented by 1 on forward navigation (bounded by `timeline.last_position`).
- Decremented by 1 on backward navigation (bounded by `timeline.first_position`).
- Reset to `0` when a new `ReplaySession` replaces the current one.
- Never persisted. Never written to any domain artifact. Not part of `InterviewState`.

**ADR-003 Compliance:** `current_position` is UI-scoped ephemeral cursor state, directly analogous to the `allowed_actions` index in the live session. ADR-003 mandates that the UI derives from state and never owns orchestration logic. `current_position` is a display cursor, not orchestration logic. **ADR-003 governs this without modification. No new ADR is required.**

**Resolution of W-01 (UIState REPLAY state machine extension):**

`UIState.REPLAY` is added as a new enum value to `UIState`. The `UIStateMachine.resolve()` method is extended with a dedicated resolution path. The REPLAY state is triggered by a separate replay trigger signal — **not** by a field in `InterviewState`.

**Mechanism:** A `ReplayContext` object (lightweight UI-layer container, not a domain contract) holds the active `session_id` submitted for replay. `UIStateMachine.resolve()` is extended to accept an optional `ReplayContext` alongside `InterviewState`. When `ReplayContext` is non-None, `UIState.REPLAY` is returned immediately, taking precedence over all other state transitions.

**`InterviewState` extension:** NOT required. `InterviewState` is not modified. The REPLAY flow is driven by a separate `ReplayContext` signal independent of the live session graph. **No new ADR is required for this mechanism.**

**Invariants:**
- I-C02-01: `current_position` is always in range `[timeline.first_position, timeline.last_position]`. Out-of-range navigation is a no-op (boundary clamp).
- I-C02-02: When `timeline.is_empty=True`, no navigation events are dispatched.
- I-C02-03: `ReplayViewController` does not invoke `replay_node` or any service. It navigates within the received `ReplaySession` only.
- I-C02-04: `current_record` is derived as `session.question_results[current_position]`. This is pure index access; no computation.

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `ReplaySession` | `ReplaySession` | C-01 `ReplayEntryPoint` | Required |
| `navigation_event` | forward / backward signal | User interaction | Optional |

**Outputs:**

| Field | Type | Destination |
|---|---|---|
| `current_position` | `int` | C-04 `ReplayNavigationBar` |
| `current_record` | `ReplayQuestionRecord` | C-05, C-06 |
| `ReplaySession` | `ReplaySession` | C-03, C-07, C-08 |

**ReplaySession fields consumed:** `question_results` (index access), `timeline` (`first_position`, `last_position`, `is_empty`), `question_count` (property).

**Read/Write:** `current_position` is the only mutable state. All `ReplaySession` access is read-only.

---

### 2.3 — C-03: ReplaySessionSummaryPanel

**Responsibility:** Renders the session-level summary panel. Displays session date, role, seniority level, interview mode, question count, duration, and — when available — the overall score and hire decision.

**Sole Data Source:** `ReplaySession.session_metadata`, `ReplaySession.scoring_snapshot`.

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `session_metadata.interview_index` | `int` | `ReplaySession` | Required |
| `session_metadata.session_date` | `datetime` | `ReplaySession` | Required |
| `session_metadata.role` | `str` | `ReplaySession` | Required |
| `session_metadata.seniority_level` | `str` | `ReplaySession` | Required |
| `session_metadata.interview_mode` | `str` | `ReplaySession` | Required |
| `session_metadata.question_count` | `int` | `ReplaySession` | Required |
| `session_metadata.session_duration_seconds` | `Optional[float]` | `ReplaySession` | Optional |
| `session_metadata.company` | `Optional[str]` | `ReplaySession` | Optional |
| `scoring_snapshot.overall_score` | `float` | `ReplaySession` | Conditional — only when `has_scoring=True` |
| `scoring_snapshot.hire_decision` | `HireDecision` | `ReplaySession` | Conditional — only when `has_scoring=True` |
| `scoring_snapshot.level` | `InterviewLevel` | `ReplaySession` | Conditional — only when `has_scoring=True` |
| `is_successful` | `bool` | `ReplaySession` | Required |

**Invariants:**
- I-C03-01: When `has_scoring=False` (`scoring_snapshot is None`), scoring fields are not displayed; a neutral "score not available" indicator is rendered.
- I-C03-02: When `session_duration_seconds is None`, duration is not rendered (no placeholder or "0s" fallback).
- I-C03-03: When `company is None`, company is not rendered.
- I-C03-04: No computation or formatting logic beyond display formatting (date localisation, unit display). No service calls.

**Read/Write:** Read-only.

---

### 2.4 — C-04: ReplayNavigationBar

**Responsibility:** Renders the navigation progress indicator (current position / total positions) and forward/backward navigation controls. Reflects `current_position` from `ReplayViewController`. Emits navigation events on user interaction.

**Sole Data Source:** `ReplaySession.timeline`, `current_position` (from C-02).

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `timeline.entries` | `tuple[ReplayTimelineEntry, ...]` | `ReplaySession` | Required |
| `timeline.total_positions` | `int` | `ReplaySession` | Required |
| `timeline.first_position` | `int` | `ReplaySession` | Required |
| `timeline.last_position` | `int` | `ReplaySession` | Required |
| `timeline.is_empty` | `bool` | `ReplaySession` | Required |
| `current_position` | `int` | C-02 `ReplayViewController` | Required |

**Outputs:**

| Signal | Condition |
|---|---|
| `navigate_forward` | User presses forward; emitted only when `current_position < timeline.last_position` |
| `navigate_backward` | User presses backward; emitted only when `current_position > timeline.first_position` |

**Invariants:**
- I-C04-01: The forward control is disabled (not hidden) when `current_position == timeline.last_position`.
- I-C04-02: The backward control is disabled (not hidden) when `current_position == timeline.first_position`.
- I-C04-03: When `timeline.is_empty=True`, both controls are disabled and the progress indicator renders "No questions".
- I-C04-04: Progress indicator displays `(current_position + 1) / timeline.total_positions` as a human-readable fraction (e.g., "Question 3 of 10").
- I-C04-05: `ReplayNavigationBar` does not own `current_position`. It receives it as input from C-02 and emits signals.

**ReplaySession fields consumed:** `timeline` (all sub-fields), `question_results` (count indirectly via `timeline.total_positions`).

**Read/Write:** Read-only.

---

### 2.5 — C-05: ReplayQuestionPanel

**Responsibility:** Renders the complete per-question view for the current `ReplayQuestionRecord`. Displays question prompt, area label, question type, candidate answer, score with percentage, max score, feedback text, strengths list, weaknesses list, and — when present — the follow-up question and AI hint. Delegates execution result rendering to C-06.

**Sole Data Source:** `ReplayQuestionRecord` (current record from C-02).

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `question_id` | `str` | `ReplayQuestionRecord` | Required (internal reference) |
| `question_index` | `int` | `ReplayQuestionRecord` | Required |
| `question_type` | `str` | `ReplayQuestionRecord` | Required |
| `area_label` | `str` | `ReplayQuestionRecord` | Required |
| `question_prompt` | `str` | `ReplayQuestionRecord` | Required |
| `candidate_answer` | `str` | `ReplayQuestionRecord` | Required (may be empty string) |
| `score` | `float` | `ReplayQuestionRecord` | Required |
| `max_score` | `float` | `ReplayQuestionRecord` | Required |
| `score_ratio` | `float` | `ReplayQuestionRecord.score_ratio` (property) | Required |
| `feedback` | `str` | `ReplayQuestionRecord` | Required |
| `strengths` | `tuple[str, ...]` | `ReplayQuestionRecord` | Required (may be empty) |
| `weaknesses` | `tuple[str, ...]` | `ReplayQuestionRecord` | Required (may be empty) |
| `follow_up_question` | `Optional[str]` | `ReplayQuestionRecord` | Optional |
| `ai_hint_explanation` | `Optional[str]` | `ReplayQuestionRecord` | Optional |
| `ai_hint_suggestion` | `Optional[str]` | `ReplayQuestionRecord` | Optional |
| `attempts` | `int` | `ReplayQuestionRecord` | Required |
| `is_coding_question` | `bool` | `ReplayQuestionRecord.is_coding_question` (property) | Required (controls C-06 delegation) |
| `has_hint` | `bool` | `ReplayQuestionRecord.has_hint` (property) | Required (controls hint section visibility) |

**Invariants:**
- I-C05-01: When `candidate_answer` is an empty string, a neutral "No answer recorded" indicator is rendered.
- I-C05-02: When `strengths` is empty, the strengths section is not rendered (no empty list placeholder).
- I-C05-03: When `weaknesses` is empty, the weaknesses section is not rendered.
- I-C05-04: `follow_up_question` section is rendered only when `follow_up_question is not None`.
- I-C05-05: AI hint section is rendered only when `has_hint=True` (`ai_hint_explanation is not None`). Both `ai_hint_explanation` and `ai_hint_suggestion` are displayed when `has_hint=True`.
- I-C05-06: `is_coding_question=True` causes C-06 `ReplayExecutionResultPanel` to be included in the rendered view.
- I-C05-07: No re-submission control is rendered. No editable field. No submit button.
- I-C05-08: Score is displayed as both raw value and percentage (`score_ratio * 100`). No rounding beyond display formatting.

**Read/Write:** Read-only.

---

### 2.6 — C-06: ReplayExecutionResultPanel

**Responsibility:** Renders the coding question execution result. Conditional component — only rendered when `is_coding_question=True`. Displays test pass/fail counts and execution status.

**Sole Data Source:** `ReplayQuestionRecord` (when `is_coding_question=True`).

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `execution_status` | `str` | `ReplayQuestionRecord` | Required (non-None when `is_coding_question=True`) |
| `passed_tests` | `int` | `ReplayQuestionRecord` | Required (non-None when `is_coding_question=True`) |
| `total_tests` | `int` | `ReplayQuestionRecord` | Required (non-None when `is_coding_question=True`) |

**Invariants:**
- I-C06-01: This component is never rendered when `is_coding_question=False`.
- I-C06-02: `execution_status`, `passed_tests`, and `total_tests` are always co-present (enforced by V-RQR-04 on `ReplayQuestionRecord`). No null-safety handling needed within this component.
- I-C06-03: Pass rate displayed as `passed_tests / total_tests`. No re-execution. No service calls.
- I-C06-04: `execution_status` is rendered as a status badge (e.g., "Passed", "Failed", "Error"). No interpretation logic beyond display.

**Read/Write:** Read-only.

---

### 2.7 — C-07: ReplayScoringPanel

**Responsibility:** Renders the session-level dimensional scores, hire decision, hiring probability, percentile rank, and gating information. Conditional — only rendered when `has_scoring=True`.

**Sole Data Source:** `ReplaySession.scoring_snapshot`.

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `scoring_snapshot.overall_score` | `float` | `ReplaySession` | Conditional |
| `scoring_snapshot.scoring_dimensions` | `tuple[ScoringDimension, ...]` | `ReplaySession` | Conditional |
| `scoring_snapshot.dimension_scores` | `dict[str, float]` | `ReplaySession` | Conditional |
| `scoring_snapshot.hire_decision` | `HireDecision` | `ReplaySession` | Conditional |
| `scoring_snapshot.hiring_probability` | `float` | `ReplaySession` | Conditional |
| `scoring_snapshot.percentile_rank` | `float` | `ReplaySession` | Conditional |
| `scoring_snapshot.percentile_explanation` | `str` | `ReplaySession` | Conditional |
| `scoring_snapshot.level` | `InterviewLevel` | `ReplaySession` | Conditional |
| `scoring_snapshot.gating_triggered` | `bool` | `ReplaySession` | Conditional |
| `scoring_snapshot.gating_reason` | `Optional[str]` | `ReplaySession` | Conditional |
| `has_scoring` | `bool` | `ReplaySession.has_scoring` (property) | Required |

**Invariants:**
- I-C07-01: This component is never rendered when `has_scoring=False` (`scoring_snapshot is None`).
- I-C07-02: `gating_reason` section is rendered only when `gating_triggered=True`. Enforced by V-SS-01.
- I-C07-03: `dimension_scores` is rendered as a per-dimension score list. No re-weighting or re-computation.
- I-C07-04: `decision_explanation`, `dimension_signals`, `weighted_breakdown`, `raw_score`, `adjusted_score`, `confidence`, `schema_version` from `ScoringSnapshot` are **not consumed** by this component (see Consumption Audit §5).

**Read/Write:** Read-only.

---

### 2.8 — C-08: ReplayCoachingPanel

**Responsibility:** Renders the session-level coaching view in two distinct sections: (A) narrative insights from `Narrative`; (B) deterministic coaching objectives, actions, and study recommendations from `CoachingSnapshot`.

**Sole Data Source:** `ReplaySession.coaching_snapshot`, `ReplaySession.narrative`.

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `narrative.insights` | `tuple[NarrativeInsight, ...]` | `ReplaySession` | Required (may be empty) |
| `narrative.overview_section` | `NarrativeSection` | `ReplaySession` | Optional |
| `coaching_snapshot.collection.objectives` | `tuple[LearningObjective, ...]` | `ReplaySession` | Required (may be empty) |
| `coaching_snapshot.collection.recommendations` | `tuple[StudyRecommendation, ...]` | `ReplaySession` | Required (may be empty) |

**Invariants:**
- I-C08-01: Section A (narrative insights) and Section B (coaching objectives) are rendered as distinct visual sections. Labels must clearly communicate the semantic distinction (e.g., "Session Narrative" vs "Study Plan").
- I-C08-02: When `narrative.insights` is empty, Section A renders a neutral "No narrative insights recorded" indicator.
- I-C08-03: When `coaching_snapshot.collection.objectives` is empty, Section B renders a neutral "No coaching objectives recorded" indicator.
- I-C08-04: `overview_section` is displayed if non-None (distinct from scoring narrative — this is the knowledge-pipeline narrative overview, not the LLM hiring summary). The section must be labelled to avoid confusion with `ScoringNarrative`.
- I-C08-05: No LLM call. No `ScoringNarrative` fields consumed here (those are exclusively in `FinalReportDTO` scope, not in `ReplaySession`).

**ReplaySession fields consumed:** `narrative` (`insights`, `overview_section`), `coaching_snapshot` (`collection.objectives`, `collection.recommendations`).

**Read/Write:** Read-only.

---

### 2.9 — C-09: ReplayErrorBoundary

**Responsibility:** Renders a candidate-facing error panel when `ReplaySession.is_successful=False`. Surfaces a generic, non-technical message derived from `failure_reason` pattern. Never exposes internal state, stack traces, or domain identifiers.

**Sole Data Source:** `ReplaySession.is_successful`, `ReplaySession.failure_reason`.

**Inputs:**

| Field | Type | Source | Mandatory |
|---|---|---|---|
| `is_successful` | `bool` | `ReplaySession` | Required |
| `failure_reason` | `Optional[str]` | `ReplaySession` | Required when `is_successful=False` |

**Invariants:**
- I-C09-01: This component is only rendered when `is_successful=False`.
- I-C09-02: `failure_reason` is used internally to classify the error category for message selection. The raw `failure_reason` string is never displayed verbatim to the candidate.
- I-C09-03: Failure categories and their candidate-facing messages:
  - `"SessionHistory not found"` → "This session is no longer available."
  - `"Persistence layer I/O error"` → "Unable to load session. Please try again."
  - Any other reason → "An error occurred loading the session. Please try again or contact support."
- I-C09-04: The error panel includes a single call-to-action: "Return to Report" or "Return to Session List", depending on the entry context.
- I-C09-05: No service call. No retry logic. No auto-reload.

**Read/Write:** Read-only.

---

### 2.10 — C-10: UIStateMachine (REPLAY Extension)

**Responsibility:** Adds `UIState.REPLAY` enum value and extends `UIStateMachine.resolve()` to detect and route the replay flow. The REPLAY state is driven by a `ReplayContext` signal independent of `InterviewState`.

**Resolution of W-01 (UIState REPLAY state machine extension):** RESOLVED.

The REPLAY state is triggered by a `ReplayContext` — a lightweight, UI-layer container (not a domain contract) that carries:

| Field | Type | Description |
|---|---|---|
| `session_id` | `str` | The session to replay |
| `is_active` | `bool` | True when a replay session is in progress |

`ReplayContext` is not a Pydantic model, not a domain contract, and is not persisted. It is a UI-layer signal.

**`UIStateMachine.resolve()` extension:**

```
resolve(state: InterviewState | None, replay_context: ReplayContext | None = None) -> UIState
```

Precedence:
1. If `replay_context is not None and replay_context.is_active=True` → return `UIState.REPLAY` (takes priority over all other states).
2. Otherwise: existing resolution logic unchanged.

**`InterviewState` extension:** NOT required. No field is added to `InterviewState`. The live session state machine is not modified.

**Resolution of W-02 (Replay Entry Trigger Integration):** RESOLVED.

The replay entry is triggered by a UI event (button click on report view or session history list) that sets `ReplayContext(session_id=<id>, is_active=True)` and passes it to `UIStateMachine.resolve()`. Exiting replay clears `ReplayContext` (sets `is_active=False` or `replay_context=None`).

Entry paths:
1. **From report view:** A "Replay Session" button in the report view triggers the replay with the current session's `session_id`.
2. **From session history list:** A "Replay" action on any listed completed session triggers the replay with the selected session's `session_id`.

Both paths create a `ReplayContext` and pass it to `UIStateMachine.resolve()`.

**ADR-003 Compliance:** `UIStateMachine.resolve()` continues to derive state from inputs — it does not own orchestration logic. Adding an optional `ReplayContext` parameter preserves the state-derivation contract. No new ADR is required.

**Invariants:**
- I-C10-01: `UIState.REPLAY` takes precedence over all other `UIState` values when `ReplayContext.is_active=True`.
- I-C10-02: Exiting replay (user cancels or session ends) clears `ReplayContext`. `UIStateMachine.resolve()` then returns to the prior state (typically `UIState.REPORT`).
- I-C10-03: `UIStateMachine` does not invoke `replay_node` or the Replay Graph. It only resolves state.
- I-C10-04: `UIState` enum gains one new value: `REPLAY = "replay"`.

**Read/Write:** Read-only (state derivation only).

---

### 2.11 — C-11: ReplayAuditPanel — EXCLUDED FROM V1.3 SCOPE

**Decision:** `ReplayAuditPanel` (C-11) is **excluded** from the V1.3 production scope.

**Rationale:** The Master Plan EPIC-V13-04 does not enumerate audit metadata display as a required deliverable. The five mandatory deliverables (`policy_versions`, `knowledge_epoch`, `schema_version`, `manifest`) are provenance fields relevant to operator-level inspection, not to the candidate-facing replay experience. Including them would add implementation scope without satisfying any stated requirement.

**Impact on Consumption Audit:** `policy_versions`, `knowledge_epoch`, `schema_version`, and `manifest` are intentionally not consumed by any EPIC-04 UI component. This is justified in §5.

---

## 3. Navigation State Contract

### 3.1 NavigationState (UI-layer value)

`NavigationState` is not a domain contract. It is a UI-layer ephemeral value held by `ReplayViewController`.

| Field | Type | Lifecycle | Constraint |
|---|---|---|---|
| `current_position` | `int` | Initialised to `0`; updated on navigation events; discarded when replay exits | Always in `[timeline.first_position, timeline.last_position]` |
| `is_at_first` | `bool` | Derived: `current_position == timeline.first_position` | Display-only; controls backward button enabled state |
| `is_at_last` | `bool` | Derived: `current_position == timeline.last_position` | Display-only; controls forward button enabled state |

### 3.2 ReplayContext (UI-layer signal)

`ReplayContext` is not a domain contract. It is a UI-layer signal passed to `UIStateMachine.resolve()`.

| Field | Type | Lifecycle | Constraint |
|---|---|---|---|
| `session_id` | `str` | Set on replay trigger; cleared on replay exit | Non-empty |
| `is_active` | `bool` | `True` while replay is in progress; `False` when cleared | When `True`, `UIState.REPLAY` is returned |

**Neither `NavigationState` nor `ReplayContext` is persisted, serialised, or written to any domain artifact.**

---

## 4. Traceability Matrix (Complete)

Every Master Plan EPIC-V13-04 requirement is linked to its `ReplaySession` field(s), consuming component(s), and verification artifact.

| # | Master Plan Requirement | ReplaySession Field(s) | Consuming Component | Verification Artifact |
|---|---|---|---|---|
| R-01 | Question-by-question navigation (forward/backward) | `timeline`, `question_results` | C-02, C-04 | Integration test: forward/backward advances `current_position`; `current_record` changes |
| R-02 | Display question text | `question_results[i].question_prompt` | C-05 | Unit test: `question_prompt` rendered from `ReplayQuestionRecord` |
| R-03 | Display candidate answer | `question_results[i].candidate_answer` | C-05 | Unit test: `candidate_answer` rendered; empty string shows neutral indicator |
| R-04 | Display execution result (coding questions) | `question_results[i].execution_status`, `passed_tests`, `total_tests` | C-06 | Unit test: C-06 rendered iff `is_coding_question=True`; absent otherwise |
| R-05 | Display dimensional scores per question | `question_results[i].score`, `max_score`, `score_ratio` | C-05 | Unit test: score, max_score, percentage rendered |
| R-06 | Display coaching notes per question | `question_results[i].feedback`, `strengths`, `weaknesses` | C-05 | Unit test: feedback, strengths, weaknesses rendered |
| R-07 | Session-level summary panel | `session_metadata` (all fields), `scoring_snapshot` (conditional) | C-03 | Integration test: summary panel populated from `ReplaySessionMetadata` |
| R-08 | Navigation progress indicator | `timeline.total_positions`, `timeline.entries`, `current_position` | C-04 | Unit test: progress indicator shows `(current_position + 1) / total_positions` |
| R-09 | Responsive layout (mobile, tablet, desktop) | N/A | All panel renderers | Layout test: panels render correctly at mobile (320px), tablet (768px), desktop (1280px) breakpoints |
| R-10 | Zero LLM calls from any UI component | N/A (enforced at data layer + architectural test) | All components | Architectural test: mock all LLM service interfaces; assert zero invocations during UI render traversal |
| R-11 | Read-only, no re-submission controls | N/A | C-02, C-05, C-06 | Architectural test: no write call reachable from any replay render path; no submit/edit control in C-05 |
| R-12 | Production-quality UX (no placeholder states, no internal error surfaces) | `is_successful`, `failure_reason` | C-09 | E2E test: C-09 renders candidate-facing message; raw `failure_reason` not exposed |
| R-13 | Session metadata display (role, date, index, mode) | `session_metadata.role`, `session_date`, `interview_index`, `interview_mode` | C-03 | Unit test: all four metadata fields rendered |
| R-14 | Session scoring display (overall score, hire decision) | `scoring_snapshot.overall_score`, `hire_decision`, `level` | C-03, C-07 | Unit test: C-07 visible iff `has_scoring=True`; overall score and hire decision rendered |
| R-15 | Session coaching display (coaching objectives, narrative) | `coaching_snapshot`, `narrative` | C-08 | Unit test: Section A (narrative insights) and Section B (coaching objectives) rendered |
| R-16 | Follow-up question display | `question_results[i].follow_up_question` | C-05 | Unit test: follow-up rendered when non-None; absent when None |
| R-17 | AI hint display | `question_results[i].ai_hint_explanation`, `ai_hint_suggestion` | C-05 | Unit test: hint rendered when `has_hint=True`; absent when False |

**Status:** All 17 requirements have source fields in `ReplaySession`. No missing field. No unmet requirement.

---

## 5. ReplaySession Consumption Audit

This section audits every `ReplaySession` field against its consuming UI component(s). Every field must be either consumed or explicitly justified as intentionally unconsumed.

### 5.1 ReplaySession Root Fields

| Field | Type | Consuming Component(s) | Consumed? | Rationale |
|---|---|---|---|---|
| `session_id` | `str` | C-01 (routing gate) | YES — internally | Used for replay trigger identification; not displayed directly in UI |
| `candidate_identity_id` | `str` | None | NOT CONSUMED | Intentionally excluded: candidate identity is not displayed in the self-facing replay UI; would surface PII without purpose |
| `schema_version` | `str` | None | NOT CONSUMED | Intentionally excluded: provenance field for operators; not relevant to candidate-facing view; excluded with C-11 scope decision |
| `replay_mode` | `ReplayMode` | None | NOT CONSUMED | Intentionally excluded: always `STANDARD` for candidate-facing replay; not a display-relevant field |
| `replay_level` | `ReplayLevel` | None | NOT CONSUMED | Intentionally excluded: always `PRESENTATION` for EPIC-04; not a display-relevant field |
| `profile_snapshot` | `CandidateProfileSnapshot` | None | NOT CONSUMED | Intentionally excluded: `profile_snapshot` carries knowledge-pipeline feature data (features, quality, maturity). The Replay UI does not display raw feature data — it displays scoring (`scoring_snapshot`) and coaching (`coaching_snapshot`, `narrative`). Feature data is appropriate for KNOWLEDGE-level replay (operator context), not PRESENTATION-level (candidate context). Not a dead field — it is the source for KNOWLEDGE-level replay in future epics. |
| `narrative` | `Narrative` | C-08 | YES | `narrative.insights` and `narrative.overview_section` consumed by `ReplayCoachingPanel` |
| `coaching_snapshot` | `CoachingSnapshot` | C-08 | YES | `coaching_snapshot.collection.objectives` and `coaching_snapshot.collection.recommendations` consumed by `ReplayCoachingPanel` |
| `scoring_snapshot` | `Optional[ScoringSnapshot]` | C-03, C-07 | YES (conditional) | Consumed when `has_scoring=True`; absent handling in C-03 and C-07 |
| `question_results` | `tuple[ReplayQuestionRecord, ...]` | C-02, C-04, C-05, C-06 | YES | Full per-question rendering pipeline |
| `timeline` | `ReplayTimeline` | C-02, C-04 | YES | Navigation cursor and progress indicator |
| `session_metadata` | `ReplaySessionMetadata` | C-03 | YES | All 8 metadata fields consumed (see §5.2) |
| `policy_versions` | `PolicyVersions` | None | NOT CONSUMED | Intentionally excluded: provenance field for operators; excluded with C-11 scope decision |
| `knowledge_epoch` | `str` | None | NOT CONSUMED | Intentionally excluded: provenance field for operators; excluded with C-11 scope decision |
| `manifest` | `ReplayManifest` | None | NOT CONSUMED | Intentionally excluded: audit record for operators; excluded with C-11 scope decision |
| `is_successful` | `bool` | C-01, C-03, C-09 | YES | Routing gate (C-01), conditional display (C-03), error boundary (C-09) |
| `failure_reason` | `Optional[str]` | C-01, C-09 | YES (conditional) | Routing gate and error message classification |
| `observation_store_snapshot` | `Optional[object]` | None | NOT CONSUMED | Intentionally excluded: KNOWLEDGE-level only field; always `None` at PRESENTATION level (V-RS-06); not applicable to EPIC-04 candidate-facing UI |

### 5.2 ReplaySessionMetadata Fields

| Field | Consuming Component | Consumed? | Notes |
|---|---|---|---|
| `interview_index` | C-03 | YES | Displayed as session number |
| `session_date` | C-03 | YES | Displayed with date formatting |
| `role` | C-03 | YES | Displayed as role label |
| `seniority_level` | C-03 | YES | Displayed as seniority label |
| `interview_mode` | C-03 | YES | Displayed as mode label |
| `question_count` | C-03 | YES | Displayed as question count |
| `session_duration_seconds` | C-03 | YES (conditional) | Displayed when non-None |
| `company` | C-03 | YES (conditional) | Displayed when non-None |

All 8 fields consumed.

### 5.3 ReplayQuestionRecord Fields

| Field | Consuming Component | Consumed? | Notes |
|---|---|---|---|
| `question_id` | C-05 (internal) | YES | Internal reference only; not displayed verbatim |
| `question_index` | C-05 | YES | Displayed as question number |
| `question_type` | C-05 | YES | Displayed as question type badge |
| `area_label` | C-05 | YES | Displayed as knowledge area label |
| `question_prompt` | C-05 | YES | Displayed as question text |
| `candidate_answer` | C-05 | YES | Displayed as candidate's answer |
| `score` | C-05 | YES | Displayed as raw score |
| `max_score` | C-05 | YES | Displayed alongside score |
| `feedback` | C-05 | YES | Displayed as evaluation feedback |
| `strengths` | C-05 | YES | Displayed as strengths list |
| `weaknesses` | C-05 | YES | Displayed as weaknesses list |
| `follow_up_question` | C-05 | YES (conditional) | Displayed when non-None |
| `execution_status` | C-06 | YES (conditional) | Displayed when `is_coding_question=True` |
| `passed_tests` | C-06 | YES (conditional) | Displayed when `is_coding_question=True` |
| `total_tests` | C-06 | YES (conditional) | Displayed when `is_coding_question=True` |
| `ai_hint_explanation` | C-05 | YES (conditional) | Displayed when `has_hint=True` |
| `ai_hint_suggestion` | C-05 | YES (conditional) | Displayed when `has_hint=True` |
| `attempts` | C-05 | YES | Displayed as attempt count |

All 18 fields consumed or conditionally consumed. No dead fields.

### 5.4 ScoringSnapshot Fields (consumed subset)

| Field | Consuming Component | Consumed? | Notes |
|---|---|---|---|
| `overall_score` | C-03, C-07 | YES | Session summary and scoring panel |
| `scoring_dimensions` | C-07 | YES | Dimension-level score rendering |
| `dimension_scores` | C-07 | YES | Per-dimension scores dict |
| `hire_decision` | C-03, C-07 | YES | Summary and scoring panel |
| `hiring_probability` | C-07 | YES | Scoring panel |
| `percentile_rank` | C-07 | YES | Scoring panel |
| `percentile_explanation` | C-07 | YES | Scoring panel |
| `level` | C-03, C-07 | YES | Summary and scoring panel |
| `gating_triggered` | C-07 | YES | Scoring panel (conditional gating section) |
| `gating_reason` | C-07 | YES (conditional) | Displayed when `gating_triggered=True` |
| `raw_score` | None | NOT CONSUMED | Internal scoring detail; not candidate-relevant in replay context |
| `adjusted_score` | None | NOT CONSUMED | Internal scoring detail; not candidate-relevant in replay context |
| `dimension_signals` | None | NOT CONSUMED | Feature-signal-level data; not appropriate for candidate-facing replay |
| `weighted_breakdown` | None | NOT CONSUMED | Internal scoring calculation detail; not candidate-relevant |
| `decision_explanation` | None | NOT CONSUMED | Internal decision detail dict; not surfaced in replay (available in full report via EPIC-05) |
| `confidence` | None | NOT CONSUMED | Internal scoring confidence; not candidate-relevant in replay context |
| `schema_version` | None | NOT CONSUMED | Provenance field; excluded with C-11 scope decision |

**10 fields consumed. 7 fields intentionally not consumed.** All unconsumed fields are justified. No accidental dead field.

### 5.5 ReplayTimeline Fields

| Field | Consuming Component | Consumed? | Notes |
|---|---|---|---|
| `entries` | C-04 | YES | Full entry list for progress indicator |
| `total_positions` | C-04 | YES | Total count for progress fraction |
| `first_position` | C-02, C-04 | YES | Navigation boundary |
| `last_position` | C-02, C-04 | YES | Navigation boundary |
| `is_empty` | C-02, C-04 | YES | Empty session guard |

All 5 fields consumed.

### 5.6 Audit Completeness Statement

- **Total `ReplaySession` root fields:** 18
- **Consumed by at least one component:** 10
- **Intentionally not consumed:** 8
- **Accidental dead fields:** 0
- **Every field reviewed:** Confirmed

**No UI component consumes data outside `ReplaySession`.** All rendering is sourced exclusively from `ReplaySession` fields and their sub-artifacts.

---

## 6. Read-Only Constraint Specification (AA-05 Formal Verification)

**AA-05 status:** VERIFIED (formally).

Every component in EPIC-04 satisfies the following read-only constraints:

| Constraint | Governs | Verified By |
|---|---|---|
| No write to `InterviewState` | All components | `InterviewState` is not modified; `ReplayContext` is a separate UI-layer signal |
| No write to `SessionHistory` | All components | `replay_node` is read-only w.r.t. persistence (I-R07); UI layer reads `ReplaySession` only |
| No write to `LongitudinalProfile` | All components | No longitudinal profile reference anywhere in EPIC-04 (I-R06) |
| No write to any domain artifact | All components | All outputs are rendered UI; `current_position` is ephemeral UI state not persisted |
| No service invocation from renderers | C-03 through C-09 | All panel renderers are pure rendering functions of their input data |
| No LLM invocation from UI layer | All components | Data layer guarantee (ADR-037 I-11); enforcement test required in implementation |
| `current_position` not persisted | C-02 | UI-layer ephemeral state; discarded when replay exits |
| `ReplayContext` not persisted | C-10 | UI-layer ephemeral signal; discarded when replay exits |

---

## 7. Open Issues Resolution

### W-01 — RESOLVED

`UIState.REPLAY` state machine extension resolved in §2.10 and §3.2. `InterviewState` is not extended. No new ADR is required. `ReplayContext` is a UI-layer signal.

### W-02 — RESOLVED

Replay entry trigger mechanism resolved in §2.10. Two entry paths defined: from report view ("Replay Session" button) and from session history list ("Replay" action). Both paths create a `ReplayContext` and pass it to `UIStateMachine.resolve()`.

### W-03 — OPEN (AA-07)

Responsive layout stack capability unverified. Deferred to Implementation Plan.

### W-04 — OPEN (AA-08)

Performance for 20+ question sessions unverified. Deferred to Implementation Plan with 20-question fixture profiling gate.

### W-05 — RESOLVED

`ScoringSnapshot` field subset resolved in Consumption Audit §5.4. All 17 `ScoringSnapshot` fields audited; 10 consumed, 7 intentionally not consumed with documented rationale. No dead field.

---

## 8. Architecture Assumptions Status Update

Following Domain Contracts authoring:

| ID | Previous Status | New Status | Changed By |
|---|---|---|---|
| AA-03 | CONDITIONALLY VERIFIED | **VERIFIED** | §2.2 — navigation position confirmed as UI-scoped ephemeral state; ADR-003 governs without modification; no new ADR required |
| AA-05 | VERIFIED (architecturally) | **VERIFIED** (formally) | §6 — read-only constraint table formally verified |

All other assumptions unchanged from EPIC-04-REPLAY-UI.md §6.

**Current assumption status summary:**

| ID | Status |
|---|---|
| AA-01 | VERIFIED |
| AA-02 | CONDITIONALLY VERIFIED — enforcement test required in implementation |
| AA-03 | VERIFIED |
| AA-04 | VERIFIED |
| AA-05 | VERIFIED |
| AA-06 | VERIFIED |
| AA-07 | UNVERIFIED — Implementation Plan |
| AA-08 | UNVERIFIED — Implementation Plan |

---

## 9. Domain Contracts DoD Checklist (Playbook §8.2)

- [x] Every new or changed artifact has a complete field specification (§2 — all 10 components)
- [x] Every artifact has a declared sole writer, declared readers, and a declared lifecycle (§2 — all components; `ReplaySession` writer is `replay_node`, sole reader is Replay UI)
- [x] Traceability Matrix is complete: every Master Plan requirement linked to at least one domain field, one consuming component, and one verification artifact (§4 — 17 requirements)
- [x] No field is untraced — dead field (§5 — Consumption Audit confirms no accidental dead fields)
- [x] No requirement is unmet — missing field (§4 — all 17 requirements satisfied)
- [x] Does not contain alternatives evaluation (alternatives belong in ADRs)
- [x] W-01 and W-02 resolved (§7)
- [x] C-11 binary decision made: EXCLUDED from V1.3 scope (§2.11)
- [x] AA-03 and AA-05 formally verified (§8)
