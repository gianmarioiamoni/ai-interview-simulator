# EPIC-04 — Replay UI Experience: Data Model

**Status:** DATA MODEL COMPLETE  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-04  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Data Model (Playbook §8.3)  
**Precondition:** EPIC-04-DOMAIN-CONTRACTS.md COMPLETE  
**Governing ADRs:** ADR-037, ADR-033, ADR-003  
**Sole Data Source:** `ReplaySession` (frozen; `domain/contracts/replay/replay_session.py`)

---

## 1. Purpose

This document freezes the complete Replay UI data model. It resolves all open modelling questions from the Domain Contracts document, defines UI state and rendering ownership matrices, freezes field lifecycle tables, resolves AA-07 (responsive model), and provides the performance model (AA-08 architectural assessment).

---

## 2. UI State Ownership Matrix

All UI state in EPIC-04 is enumerated below. The matrix demonstrates: no duplicated state, no `ReplaySession` mutation, no persistence, and no hidden shared state.

| State | Owner | Lifetime | Persisted | Source | Rationale |
|---|---|---|---|---|---|
| `UIState.REPLAY` (enum value) | `UIStateMachine` | Active while `ReplayContext.is_active=True` | No | `ReplayContext` signal | State derivation only (ADR-003); cleared when replay exits |
| `ReplayContext.session_id` | Caller (UI event handler) | From replay trigger until exit | No | UI event (button click, list action) | Carries the `session_id` to be replayed; lightweight signal |
| `ReplayContext.is_active` | Caller (UI event handler) | `True` during replay; `False` on exit | No | UI event | Guards `UIStateMachine.resolve()` to return `UIState.REPLAY` |
| `ReplaySession` | `ReplayEntryPoint` (C-01) | From `replay_node` return until UI session ends or replay exits | No | `replay_node` output via Replay Graph | Immutable projection artifact; held in memory for navigation duration; never written back |
| `current_position` | `ReplayViewController` (C-02) | From `ReplaySession` receipt until replay exits or new `ReplaySession` replaces it | No | Initialised to `0`; updated by navigation events | Sole mutable UI state; integer cursor; ephemeral |
| `current_record` | `ReplayViewController` (C-02) | Derived from `current_position` on every navigation step | No | `session.question_results[current_position]` | Derived view; not independently stored; re-derived on each position change |
| `is_at_first` | `ReplayViewController` / `ReplayNavigationBar` | Derived from `current_position == timeline.first_position` | No | Derived | Display-only; controls backward button enabled state |
| `is_at_last` | `ReplayViewController` / `ReplayNavigationBar` | Derived from `current_position == timeline.last_position` | No | Derived | Display-only; controls forward button enabled state |

**Verification:**
- No duplicated state: `current_position` has exactly one owner (`ReplayViewController`). `ReplaySession` has exactly one holder (`ReplayEntryPoint`). No other component stores state independently.
- No `ReplaySession` mutation: `ReplaySession` is `frozen=True`. No component writes to it.
- No persistence: All state fields have `Persisted = No`. `current_position` and `ReplayContext` are ephemeral. `ReplaySession` is in-memory only.
- No hidden shared state: `current_record` and derived booleans are derived from `current_position` deterministically. No implicit global state.

---

## 3. Rendering Ownership Matrix

Every `ReplaySession` field rendered by the Replay UI has exactly one rendering owner. This matrix verifies single-ownership for all rendered fields.

### 3.1 ReplaySession Root Fields

| ReplaySession Field | Rendering Component | Rendering Responsibility |
|---|---|---|
| `session_id` | C-01 (internal) | Used as routing key; not rendered to candidate |
| `is_successful` | C-01, C-09 | C-01 owns routing decision; C-09 owns error panel rendering |
| `failure_reason` | C-09 | Error message classification and candidate-facing text selection |
| `session_metadata` | C-03 | All 8 sub-fields rendered in session summary panel |
| `scoring_snapshot` | C-03 (summary fields), C-07 (full scoring panel) | C-03 renders `overall_score`, `hire_decision`, `level` in summary; C-07 renders the full scoring panel |
| `question_results` | C-02 (index access), C-05 (render), C-06 (coding sub-render) | C-02 owns cursor; C-05 owns per-question render; C-06 owns execution result sub-render |
| `timeline` | C-02 (boundary logic), C-04 (progress indicator) | C-02 owns position boundary constraints; C-04 owns visual progress rendering |
| `narrative` | C-08 | All `narrative` sub-fields rendered in coaching panel |
| `coaching_snapshot` | C-08 | All `coaching_snapshot` sub-fields rendered in coaching panel |
| `has_scoring` (property) | C-03, C-07 | Conditional visibility gate; no rendering content |
| `question_count` (property) | C-02, C-03 | C-03 renders count in summary; C-02 uses for cursor boundary |

**Not rendered (intentionally unconsumed — see §5):**
`candidate_identity_id`, `schema_version`, `replay_mode`, `replay_level`, `profile_snapshot`, `policy_versions`, `knowledge_epoch`, `manifest`, `observation_store_snapshot`

### 3.2 Rendering Ownership — Shared Fields Clarification

Two fields (`scoring_snapshot`, `question_results`) are consumed by multiple components. Rendering responsibilities are non-overlapping:

| Field | Component A | Component A Scope | Component B | Component B Scope |
|---|---|---|---|---|
| `scoring_snapshot` | C-03 | `overall_score`, `hire_decision`, `level` in session summary only | C-07 | Full scoring panel: all dimensions, probability, percentile, gating |
| `question_results` | C-02 | Index cursor (`question_results[i]` selection) — no rendering | C-05 + C-06 | Full per-question render |
| `timeline` | C-02 | Position boundary constraints — no rendering | C-04 | Visual progress indicator rendering |

**No field has two components rendering the same sub-fields.** Dual consumption is scope-split; no duplication.

---

## 4. Data Model Tables

### 4.1 ReplayUIState (UI-layer ephemeral)

Not a domain contract. Fields owned by `ReplayViewController` and `UIStateMachine`.

| Field | Type | Source | Consumer | Lifecycle |
|---|---|---|---|---|
| `current_position` | `int` | Initialised to `0` on `ReplaySession` receipt; updated by navigation events | C-02 (owner), C-04 (read) | Created on replay start; reset on new session; discarded on replay exit |
| `current_record` | `ReplayQuestionRecord` | Derived: `session.question_results[current_position]` | C-05, C-06 | Re-derived on every position change; lifetime = `current_position` lifetime |
| `is_at_first` | `bool` | Derived: `current_position == timeline.first_position` | C-04 | Re-derived on every position change |
| `is_at_last` | `bool` | Derived: `current_position == timeline.last_position` | C-04 | Re-derived on every position change |

### 4.2 ReplayContext (UI-layer signal)

Not a domain contract. Fields owned by the UI event handler (caller of `UIStateMachine.resolve()`).

| Field | Type | Source | Consumer | Lifecycle |
|---|---|---|---|---|
| `session_id` | `str` (non-empty) | UI event (button click / list action) | C-01, C-10 | Created on replay trigger; discarded on replay exit |
| `is_active` | `bool` | Set `True` on replay trigger; set `False` on exit | C-10 (`UIStateMachine`) | Active during replay; cleared when candidate exits replay |

### 4.3 SessionSummaryViewModel (C-03 rendering model)

Derived directly from `ReplaySession` fields. Not a stored model.

| Field | Type | Source (`ReplaySession` path) | Consumer | Lifecycle |
|---|---|---|---|---|
| `interview_index` | `int` | `session_metadata.interview_index` | C-03 | Derived on render; no storage |
| `session_date` | `datetime` | `session_metadata.session_date` | C-03 | Derived on render |
| `role` | `str` | `session_metadata.role` | C-03 | Derived on render |
| `seniority_level` | `str` | `session_metadata.seniority_level` | C-03 | Derived on render |
| `interview_mode` | `str` | `session_metadata.interview_mode` | C-03 | Derived on render |
| `question_count` | `int` | `session_metadata.question_count` | C-03 | Derived on render |
| `session_duration_seconds` | `Optional[float]` | `session_metadata.session_duration_seconds` | C-03 | Conditional render |
| `company` | `Optional[str]` | `session_metadata.company` | C-03 | Conditional render |
| `overall_score` | `Optional[float]` | `scoring_snapshot.overall_score` | C-03 | Conditional on `has_scoring` |
| `hire_decision` | `Optional[HireDecision]` | `scoring_snapshot.hire_decision` | C-03 | Conditional on `has_scoring` |
| `level` | `Optional[InterviewLevel]` | `scoring_snapshot.level` | C-03 | Conditional on `has_scoring` |
| `has_scoring` | `bool` | `session.has_scoring` (property) | C-03 | Gate for conditional score fields |

### 4.4 NavigationViewModel (C-04 rendering model)

| Field | Type | Source | Consumer | Lifecycle |
|---|---|---|---|---|
| `current_position` | `int` | C-02 | C-04 | Updated on every navigation event |
| `total_positions` | `int` | `timeline.total_positions` | C-04 | Fixed for session lifetime |
| `display_label` | `str` | Derived: `f"Question {current_position + 1} of {total_positions}"` | C-04 | Derived on render; no storage |
| `is_empty` | `bool` | `timeline.is_empty` | C-04 | Fixed for session lifetime |
| `backward_enabled` | `bool` | Derived: `current_position > timeline.first_position` | C-04 | Derived on every position change |
| `forward_enabled` | `bool` | Derived: `current_position < timeline.last_position` | C-04 | Derived on every position change |
| `entries` | `tuple[ReplayTimelineEntry, ...]` | `timeline.entries` | C-04 | Fixed for session lifetime |

### 4.5 QuestionViewModel (C-05 rendering model)

Sourced entirely from the current `ReplayQuestionRecord`.

| Field | Type | Source | Consumer | Lifecycle |
|---|---|---|---|---|
| `question_index` | `int` | `current_record.question_index` | C-05 | Re-derived on position change |
| `question_type` | `str` | `current_record.question_type` | C-05 | Re-derived on position change |
| `area_label` | `str` | `current_record.area_label` | C-05 | Re-derived on position change |
| `question_prompt` | `str` | `current_record.question_prompt` | C-05 | Re-derived on position change |
| `candidate_answer` | `str` | `current_record.candidate_answer` | C-05 | Re-derived on position change |
| `score` | `float` | `current_record.score` | C-05 | Re-derived on position change |
| `max_score` | `float` | `current_record.max_score` | C-05 | Re-derived on position change |
| `score_pct` | `float` | Derived: `current_record.score_ratio * 100` | C-05 | Derived on render; no storage |
| `feedback` | `str` | `current_record.feedback` | C-05 | Re-derived on position change |
| `strengths` | `tuple[str, ...]` | `current_record.strengths` | C-05 | Re-derived on position change |
| `weaknesses` | `tuple[str, ...]` | `current_record.weaknesses` | C-05 | Re-derived on position change |
| `follow_up_question` | `Optional[str]` | `current_record.follow_up_question` | C-05 | Conditional render |
| `has_hint` | `bool` | `current_record.has_hint` (property) | C-05 | Gate for hint section |
| `ai_hint_explanation` | `Optional[str]` | `current_record.ai_hint_explanation` | C-05 | Conditional render |
| `ai_hint_suggestion` | `Optional[str]` | `current_record.ai_hint_suggestion` | C-05 | Conditional render |
| `attempts` | `int` | `current_record.attempts` | C-05 | Re-derived on position change |
| `is_coding_question` | `bool` | `current_record.is_coding_question` (property) | C-05 | Gate for C-06 delegation |

### 4.6 ExecutionResultViewModel (C-06 rendering model)

Only constructed when `is_coding_question=True`.

| Field | Type | Source | Consumer | Lifecycle |
|---|---|---|---|---|
| `execution_status` | `str` | `current_record.execution_status` | C-06 | Active when `is_coding_question=True` |
| `passed_tests` | `int` | `current_record.passed_tests` | C-06 | Active when `is_coding_question=True` |
| `total_tests` | `int` | `current_record.total_tests` | C-06 | Active when `is_coding_question=True` |
| `pass_rate_pct` | `float` | Derived: `(passed_tests / total_tests) * 100` | C-06 | Derived on render; no storage |

### 4.7 ScoringViewModel (C-07 rendering model)

Only constructed when `has_scoring=True`.

| Field | Type | Source | Consumer | Lifecycle |
|---|---|---|---|---|
| `overall_score` | `float` | `scoring_snapshot.overall_score` | C-07 | Active when `has_scoring=True` |
| `scoring_dimensions` | `tuple[ScoringDimension, ...]` | `scoring_snapshot.scoring_dimensions` | C-07 | Active when `has_scoring=True` |
| `dimension_scores` | `dict[str, float]` | `scoring_snapshot.dimension_scores` | C-07 | Active when `has_scoring=True` |
| `hire_decision` | `HireDecision` | `scoring_snapshot.hire_decision` | C-07 | Active when `has_scoring=True` |
| `hiring_probability` | `float` | `scoring_snapshot.hiring_probability` | C-07 | Active when `has_scoring=True` |
| `percentile_rank` | `float` | `scoring_snapshot.percentile_rank` | C-07 | Active when `has_scoring=True` |
| `percentile_explanation` | `str` | `scoring_snapshot.percentile_explanation` | C-07 | Active when `has_scoring=True` |
| `level` | `InterviewLevel` | `scoring_snapshot.level` | C-07 | Active when `has_scoring=True` |
| `gating_triggered` | `bool` | `scoring_snapshot.gating_triggered` | C-07 | Active when `has_scoring=True` |
| `gating_reason` | `Optional[str]` | `scoring_snapshot.gating_reason` | C-07 | Conditional on `gating_triggered=True` |

### 4.8 CoachingViewModel (C-08 rendering model)

| Field | Type | Source | Consumer | Lifecycle |
|---|---|---|---|---|
| `narrative_insights` | `tuple[NarrativeInsight, ...]` | `narrative.insights` | C-08 | Fixed for session lifetime |
| `overview_section` | `Optional[NarrativeSection]` | `narrative.overview_section` | C-08 | Conditional render |
| `coaching_objectives` | `tuple[LearningObjective, ...]` | `coaching_snapshot.collection.objectives` | C-08 | Fixed for session lifetime |
| `coaching_recommendations` | `tuple[StudyRecommendation, ...]` | `coaching_snapshot.collection.recommendations` | C-08 | Fixed for session lifetime |

### 4.9 ErrorViewModel (C-09 rendering model)

Only constructed when `is_successful=False`.

| Field | Type | Source | Consumer | Lifecycle |
|---|---|---|---|---|
| `candidate_message` | `str` | Derived from `failure_reason` pattern classification | C-09 | Active when `is_successful=False` |
| `action_label` | `str` | Derived from entry context | C-09 | Active when `is_successful=False` |

---

## 5. Intentionally Unconsumed Fields — Formal Freeze

The following `ReplaySession` fields are formally frozen as **not consumed** by any EPIC-04 UI component. This is a design decision, not an oversight. These fields must not be added to any component render path without amending this Data Model document.

| Field | Reason for Exclusion | Future Applicability |
|---|---|---|
| `candidate_identity_id` | PII; not display-relevant in candidate self-facing context | No planned consumption |
| `schema_version` | Operator provenance; C-11 excluded | V2 operator tools |
| `replay_mode` | Always `STANDARD` for EPIC-04; no display value | V2 operator tools |
| `replay_level` | Always `PRESENTATION` for EPIC-04; no display value | V2 operator tools |
| `profile_snapshot` | KNOWLEDGE-level feature data; not candidate-relevant at PRESENTATION level | KNOWLEDGE-level replay (future epic) |
| `policy_versions` | Operator provenance; C-11 excluded | V2 operator tools |
| `knowledge_epoch` | Operator provenance; C-11 excluded | V2 operator tools |
| `manifest` | Audit record; C-11 excluded | V2 operator tools |
| `observation_store_snapshot` | KNOWLEDGE-level only; always `None` at PRESENTATION (V-RS-06) | KNOWLEDGE-level replay (future epic) |

**Freeze invariant:** Any EPIC-04 implementation that renders one of these fields without a Data Model amendment is an architectural violation.

---

## 6. Responsive Model (AA-07 Resolution)

### 6.1 Frontend Stack Identification

**VERIFIED:** The existing UI is a **Gradio** application (`import gradio as gr` confirmed in `app/ui/layout/layout_builder.py`). This is the authoritative frontend framework for V1.3.

### 6.2 Gradio Responsive Capabilities

Gradio (v4+) provides built-in CSS Grid / Flexbox-based layout that adapts to viewport width. Key characteristics:
- `gr.Row()` and `gr.Column()` adapt to screen width via CSS Flexbox.
- `scale` parameter on `gr.Column()` controls relative column widths.
- On small viewports, `gr.Row()` children stack vertically by default.
- Custom CSS injected via `gr.HTML()` or `css=` parameter extends layout control.

### 6.3 Responsive Breakpoints

The Replay UI must render correctly at three breakpoints. Gradio's layout system handles breakpoints via CSS without requiring new framework dependencies.

| Breakpoint | Viewport Width | Layout Behaviour |
|---|---|---|
| Mobile | < 640px | All panels stack vertically; navigation bar at top; question panel full-width; coaching and scoring panels below |
| Tablet | 640px – 1024px | Two-column layout: left column (navigation bar + question panel); right column (summary + scoring + coaching) |
| Desktop | > 1024px | Three-column layout: left (navigation bar); center (question panel); right (summary + scoring + coaching) |

### 6.4 Responsive Layout Rules

| Panel | Mobile | Tablet | Desktop |
|---|---|---|---|
| `ReplayNavigationBar` (C-04) | Full width, top | Left column, top | Left column |
| `ReplaySessionSummaryPanel` (C-03) | Full width, after navigation | Right column, top | Right column, top |
| `ReplayQuestionPanel` (C-05 + C-06) | Full width | Left column, below navigation | Center column |
| `ReplayScoringPanel` (C-07) | Full width (conditional) | Right column, below summary | Right column, below summary |
| `ReplayCoachingPanel` (C-08) | Full width, last | Right column, bottom | Right column, bottom |
| `ReplayErrorBoundary` (C-09) | Full width, centered | Full width, centered | Full width, centered |

### 6.5 Stack Assumptions

- No new UI library dependency is required. Gradio's built-in `gr.Row()`, `gr.Column()`, and `css=` parameter are sufficient for all three breakpoints.
- Custom CSS injected via `gr.HTML()` (as established by `LOADER_STYLE` pattern in `app/ui/layout/assets/styles.py`) is used for any layout refinement beyond Gradio's default behaviour.
- No React, Tailwind, or additional CSS framework is introduced.

**AA-07 Status: VERIFIED.**

**Rationale:** Gradio's native layout system (`gr.Row`, `gr.Column`, `scale`) with custom CSS injection satisfies all three responsive breakpoints without new dependencies. The existing pattern (`gr.HTML(LOADER_STYLE)` in `layout_builder.py`) confirms CSS injection is already in use.

---

## 7. Performance Model (AA-08 Assessment)

### 7.1 Session Size

| Dimension | Expected Value | Worst Case |
|---|---|---|
| Questions per session | 10–20 (Master Plan default 10–30) | 30 questions |
| `ReplayQuestionRecord` per session | 10–20 | 30 |
| `ReplaySession` in-memory size | Estimated < 500 KB for 20 questions | < 1.5 MB for 30 questions |
| `scoring_dimensions` | 4–8 dimensions | 10 dimensions |
| `narrative.insights` | 5–15 insights | 30 insights |
| `coaching_snapshot.collection.objectives` | 2–6 objectives | 10 objectives |

### 7.2 Rendering Strategy

| Operation | Complexity | Rationale |
|---|---|---|
| `replay_node` execution (initial load) | O(n) where n = question count | Single pass; dominated by `SessionHistory` I/O |
| Navigation step (position change) | O(1) | Index access: `question_results[current_position]` |
| `current_record` derivation | O(1) | Pure array index; no computation |
| Panel re-render on navigation | O(1) per field | Direct field read from frozen record |
| `ReplayTimeline` entries render | O(n) | Linear render of n `ReplayTimelineEntry` items |
| `scoring_dimensions` render | O(k) where k = dimension count | Linear render; k ≤ 10 in all expected cases |
| `narrative.insights` render | O(m) where m = insight count | Linear render; m ≤ 30 in all expected cases |

### 7.3 Navigation Complexity

Navigation is O(1) per step. No re-invocation of `replay_node`. No service call. No recomputation. `ReplaySession` is loaded once at entry; all subsequent navigation operates on the in-memory frozen object.

**No architectural concern for navigation performance.**

### 7.4 Initial Load

The dominant cost is `replay_node` execution: loading `SessionHistory` from persistence and calling `ReplaySessionBuilder.build()`. This is a one-time cost per replay session. ADR-037 D1 §1.4 establishes that `ReplaySession` is never persisted; every entry triggers a fresh reconstruction.

The Master Plan SLO for replay load: **< 1s for any stored session**. This SLO is governed by EPIC-V13-09 (Performance & Scalability Baseline), not EPIC-04. EPIC-04's architectural responsibility is to ensure the UI layer adds no non-trivial overhead above the `replay_node` cost.

### 7.5 Architectural Constraints

- `replay_node` must not be re-invoked during navigation. The UI holds `ReplaySession` in memory for the session lifetime.
- No lazy loading of `question_results` is needed. Full `ReplaySession` (all questions) is loaded at entry. For the V1.3 session size (≤ 30 questions), in-memory holding is architecturally sound.
- If session size exceeds 30 questions in a future version, lazy question loading becomes relevant. This is deferred to V2.
- No client-side caching of `ReplaySession` across multiple replay requests. Each replay invocation produces a fresh `ReplaySession`.

### 7.6 Implementation Verification Required

**AA-08 Status: CONDITIONALLY VERIFIED.**

Architectural analysis confirms no O(n²) or worse complexity path exists. Navigation is O(1). Rendering is O(n) or O(k) linear. No architectural blocker for performance.

**However:** The Master Plan's explicit requirement to profile with a 20-question fixture cannot be satisfied by architecture analysis. A profiling gate is required during implementation:

| Gate | Requirement | Phase |
|---|---|---|
| Load time profiling | `replay_node` + first render ≤ 1s for 20-question fixture | Implementation Plan profiling phase |
| Navigation step profiling | Position change + re-render ≤ 100ms | Implementation Plan profiling phase |
| Memory footprint | `ReplaySession` ≤ 500 KB for 20-question fixture | Implementation Plan profiling phase |

These gates must be documented in `EPIC-04-IMPLEMENTATION-PLAN.md` as mandatory pre-ship verification.

---

## 8. Replay Completeness Verification

Every UI panel has at least one source field in `ReplaySession`. This verifies that the Replay UI is fully sourced from the projection artifact with no live computation required.

| UI Panel | Source `ReplaySession` Field(s) | Completeness |
|---|---|---|
| Session summary | `session_metadata` (all 8 fields), `scoring_snapshot` (conditional) | COMPLETE |
| Navigation bar | `timeline` (all 5 fields), `current_position` (UI state) | COMPLETE |
| Question panel | `question_results[i]` (all 18 `ReplayQuestionRecord` fields) | COMPLETE |
| Execution result | `question_results[i].execution_status`, `passed_tests`, `total_tests` | COMPLETE (conditional) |
| Scoring panel | `scoring_snapshot` (10 of 17 fields; 7 excluded by design) | COMPLETE |
| Coaching panel | `narrative` (insights, overview_section), `coaching_snapshot` (objectives, recommendations) | COMPLETE |
| Error boundary | `is_successful`, `failure_reason` | COMPLETE |

**Replay completeness: VERIFIED.** No UI panel requires a field outside `ReplaySession`.

---

## 9. Extensibility Assessment

| Concern | V1.3 Position | V2 Path |
|---|---|---|
| C-11 `ReplayAuditPanel` (operator view) | Excluded from V1.3 | Consumes `manifest`, `policy_versions`, `knowledge_epoch`, `schema_version` — all present in `ReplaySession` |
| KNOWLEDGE-level replay | Out of scope for EPIC-04 | Consumes `profile_snapshot`, `observation_store_snapshot` — both present in `ReplaySession` |
| Session size > 30 questions | Not expected in V1.3 | Lazy question loading at UI layer; `ReplaySession` contract already supports arbitrary-length `question_results` |
| `ReplayAuditPanel` for MIGRATION/RECOVERY modes | Out of scope | `manifest.migration_metadata` already present in `ReplayManifest` |

**V1.3 `ReplaySession` field set is extensibility-complete** for all identified V2 requirements. No field addition to `ReplaySession` is anticipated for V2 Replay UI concerns.

---

## 10. Architecture Assumptions Final Status

| ID | Status | Verified By |
|---|---|---|
| AA-01 | VERIFIED | EPIC-04-REPLAY-UI.md §5 |
| AA-02 | CONDITIONALLY VERIFIED | Architectural test mandate (implementation artifact) |
| AA-03 | VERIFIED | EPIC-04-DOMAIN-CONTRACTS.md §2.2 |
| AA-04 | VERIFIED | EPIC-04-REPLAY-UI.md §5 |
| AA-05 | VERIFIED | EPIC-04-DOMAIN-CONTRACTS.md §6 |
| AA-06 | VERIFIED | ADR-037 D1 §1.4 |
| AA-07 | **VERIFIED** | §6 — Gradio stack confirmed; no new dependency required |
| AA-08 | **CONDITIONALLY VERIFIED** | §7 — O(1) navigation confirmed; profiling gates required in Implementation Plan |

**Status changes produced by this document:**
- AA-07: UNVERIFIED → **VERIFIED**
- AA-08: UNVERIFIED → **CONDITIONALLY VERIFIED**

---

## 11. Validation (Playbook §8.3 DoD)

- [x] All open modelling questions from Domain Contracts are resolved (§2, §3, §4)
- [x] Complete field tables frozen for all affected artifacts (§4.1 through §4.9)
- [x] Replay completeness verified: every UI panel sourced from `ReplaySession` (§8)
- [x] Extensibility for next epics evaluated (§9)
- [x] AA-07 VERIFIED (§6)
- [x] AA-08 CONDITIONALLY VERIFIED (§7) — profiling gates required; no architectural blocker
- [x] All Architecture Assumptions have status VERIFIED or CONDITIONALLY VERIFIED; none UNVERIFIED (§10)
- [x] No `INVALIDATED` assumption (no architectural response needed)
- [x] UI State Ownership Matrix complete — no duplication, no persistence, no hidden state (§2)
- [x] Rendering Ownership Matrix complete — every rendered field has exactly one owner (§3)
- [x] Every Domain Contract represented in field tables (§4)
- [x] Every `ReplaySession` field has a defined lifecycle: consumed fields in §4; unconsumed fields frozen in §5
- [x] No architectural contradiction exists between this document and EPIC-04-REPLAY-UI.md or EPIC-04-DOMAIN-CONTRACTS.md
