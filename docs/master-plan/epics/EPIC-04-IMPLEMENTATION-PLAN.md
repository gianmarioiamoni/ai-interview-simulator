# EPIC-04 — Replay UI Experience: Implementation Plan

**Status:** ACCEPTED  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-04  
**Authority:** EPIC-04-ARCHITECTURE-FREEZE.md (APPROVED, commit `3e8f31a`)  
**Regression baseline:** 6574 passing tests, 0 failures  
**Precondition:** Architecture Freeze APPROVED. Implementation Dependency Validation applied (§2). No implementation begins without this plan accepted.

---

## 1. Objectives

### 1.1 Implementation Goals

1. Add `UIState.REPLAY` to `UIState` enum without breaking existing state resolution.
2. Add `ReplayContext` (UI-layer signal) and extend `UIStateMachine.resolve()` with an additive `replay_context=None` parameter.
3. Implement `ReplayEntryPoint` (C-01): accepts `session_id`, invokes Replay Graph, routes `ReplaySession` to `ReplayViewController` or `ReplayErrorBoundary`.
4. Implement `ReplayViewController` (C-02): owns `current_position`; derives `current_record`; distributes to panel renderers.
5. Implement `ReplayNavigationBar` (C-04): progress indicator; forward/backward controls with boundary enforcement.
6. Implement `ReplaySessionSummaryPanel` (C-03): session-level metadata and conditional scoring summary.
7. Implement `ReplayQuestionPanel` (C-05): full per-question rendering including conditional sections.
8. Implement `ReplayExecutionResultPanel` (C-06): conditional coding question execution result.
9. Implement `ReplayScoringPanel` (C-07): conditional session-level scoring panel.
10. Implement `ReplayCoachingPanel` (C-08): narrative insights and coaching objectives.
11. Implement `ReplayErrorBoundary` (C-09): candidate-facing error panel.
12. Integrate Replay UI into the Gradio layout and event binding layer.
13. Write the LLM-free architectural test (AA-02 enforcement).
14. Execute and pass the 20-question performance profiling gate (AA-08).
15. Verify responsive layout at all three breakpoints (AA-07).
16. Leave the regression suite green (≥ 6574 passing, zero failures) at every phase boundary.

### 1.2 Success Criteria

- `UIStateMachine.resolve()` returns `UIState.REPLAY` when `ReplayContext.is_active=True`.
- All existing `UIStateMachine` tests pass unchanged.
- Forward/backward navigation advances/retreats `current_position` within bounds.
- Per-question panel renders all 18 `ReplayQuestionRecord` fields correctly.
- `ReplayExecutionResultPanel` is visible iff `is_coding_question=True`.
- `ReplayScoringPanel` is visible iff `has_scoring=True`.
- `ReplayErrorBoundary` renders candidate-facing message; raw `failure_reason` not exposed.
- Architectural test: zero LLM invocations during render path traversal (AA-02).
- Performance: replay load ≤ 1s, navigation step ≤ 100ms, memory ≤ 500 KB for 20-question fixture (AA-08).
- Layout correct at 320px, 768px, 1280px breakpoints (AA-07).
- Full regression suite: ≥ 6574 passing, zero failures at every phase boundary.

### 1.3 Out of Scope

- C-11 `ReplayAuditPanel` — excluded from V1.3 scope (Domain Contracts §2.11).
- `ReplayLevel.KNOWLEDGE` or `REASONING` UI (reserved).
- Re-submission controls — prohibited by Master Plan.
- `profile_snapshot`, `observation_store_snapshot`, `policy_versions`, `knowledge_epoch`, `manifest`, `candidate_identity_id`, `replay_mode`, `replay_level`, `schema_version` rendering — freeze invariant (Data Model §5).
- Any modification to `ReplaySession`, `replay_node`, or `ReplaySessionBuilder`.
- Any modification to `InterviewState`.
- Persistence of `ReplaySession`, `current_position`, or `ReplayContext`.

---

## 2. Implementation Dependency Validation

All commit boundaries below have been validated for self-containment per Playbook §2.

| Phase | Depends On | Independently Testable |
|---|---|---|
| Phase 1 — UIState + UIStateMachine extension | Nothing (additive) | Yes — existing tests unchanged; new REPLAY state test can be written |
| Phase 2 — ReplayContext + Entry Point | Phase 1 (`UIState.REPLAY` exists) | Yes — unit test: `ReplayEntryPoint` routes correctly from mocked `ReplaySession` |
| Phase 3 — Navigation (ReplayViewController + NavigationBar) | Phase 2 (`ReplaySession` available via entry point) | Yes — unit test: navigation cursor advances/retreats on events |
| Phase 4 — Panel Renderers (C-03, C-05, C-06, C-07, C-08, C-09) | Phase 3 (`current_record` available from C-02) | Yes — unit tests per panel: render from fixture `ReplaySession` |
| Phase 5 — Layout Integration | Phases 1–4 (all components exist) | Yes — integration test: full replay flow with fixture |
| Phase 6 — Architectural + Performance Tests | Phases 1–5 (full implementation) | Yes — architectural test; profiling fixture |

**No circular dependencies.** Each phase depends only on artefacts from prior phases.

---

## 3. Macro Phase Breakdown

EPIC-04 is organised into two macro phases. Each macro phase ends with a mandatory Architecture Checkpoint.

```
Macro Phase A — Core Replay UI
  Phase 1: UIState + UIStateMachine extension
  Phase 2: ReplayContext + ReplayEntryPoint
  Phase 3: Navigation (ReplayViewController + ReplayNavigationBar)
        ↓
Architecture Checkpoint A
        ↓
Macro Phase B — Panel Renderers + Integration + Verification
  Phase 4: Panel Renderers (C-03, C-05, C-06, C-07, C-08, C-09)
  Phase 5: Layout Integration
  Phase 6: Architectural + Performance Tests
        ↓
Architecture Checkpoint B
        ↓
CAR → Regression → Documentation → Final Review → Epic Close
```

---

## 4. Phase Specifications

---

### Phase 1 — UIState Extension and UIStateMachine REPLAY Routing

**Macro Phase:** A  
**Objective:** Add `UIState.REPLAY` enum value and extend `UIStateMachine.resolve()` with additive `replay_context=None` parameter and REPLAY priority routing.

**Scope:**
- `app/ui/ui_state.py` — add `REPLAY = "replay"` enum value
- `app/ui/state_machine/ui_state_machine.py` — extend `resolve()` signature; add REPLAY priority branch

**Forbidden scope:** All other files.

**Dependencies:** None.

**Expected artifacts:**
- `UIState.REPLAY` enum value
- `UIStateMachine.resolve(state, replay_context=None)` — additive signature; existing callers with positional `state` argument are unaffected

**Completion criteria:**
- `UIState.REPLAY` is a valid `UIState` value.
- `UIStateMachine.resolve(state=None, replay_context=ReplayContext(session_id="x", is_active=True))` returns `UIState.REPLAY`.
- All existing `UIStateMachine` tests pass unchanged (compatibility regression gate).
- New unit test: REPLAY state returned when `replay_context.is_active=True`.
- New unit test: REPLAY state NOT returned when `replay_context=None` or `is_active=False`.

**Regression gate:** ≥ 6574 passing, zero failures.

**Architectural invariants:**
- I-C10-01: REPLAY takes precedence when `is_active=True`.
- I-C10-03: `UIStateMachine` does not invoke `replay_node` or the Replay Graph.
- ADR-003: state derivation only; no orchestration logic.

**Commit boundary:** One atomic commit — `feat(replay-ui): add UIState.REPLAY and UIStateMachine REPLAY routing`

---

### Phase 2 — ReplayContext and ReplayEntryPoint

**Macro Phase:** A  
**Objective:** Implement `ReplayContext` (UI-layer signal) and `ReplayEntryPoint` (C-01).

**Scope:**
- `app/ui/replay/replay_context.py` — new file; `ReplayContext` dataclass
- `app/ui/replay/replay_entry_point.py` — new file; `ReplayEntryPoint` component

**Forbidden scope:** All domain contracts. `replay_node`. `ReplaySession`.

**Dependencies:** Phase 1 (`UIState.REPLAY` exists).

**Expected artifacts:**
- `ReplayContext` with `session_id: str`, `is_active: bool`
- `ReplayEntryPoint.load(session_id: str) -> ReplaySession` — invokes `build_replay_graph(session_loader).invoke(ReplayRequest(session_id=session_id))`; returns `ReplaySession`
- `ReplayEntryPoint.route(session: ReplaySession) -> tuple[ReplayViewController | None, ReplayErrorBoundary | None]`

**Completion criteria:**
- `ReplayContext(session_id="", is_active=True)` raises `ValueError` (empty session_id).
- `ReplayEntryPoint.load()` returns `ReplaySession` from mocked Replay Graph.
- Routing: `is_successful=True` → `ReplayViewController`; `is_successful=False` → `ReplayErrorBoundary`.
- `ReplayEntryPoint` does not persist `ReplaySession`.
- Unit tests for all routing paths.

**Regression gate:** ≥ 6574 passing, zero failures.

**Architectural invariants:**
- I-C01-01: empty `session_id` rejected.
- I-C01-02: no persistence of `ReplaySession`.
- I-C01-03: routing based solely on `is_successful`.
- I-C01-04: no LLM call; only Replay Graph invocation.

**Commit boundary:** One atomic commit — `feat(replay-ui): add ReplayContext and ReplayEntryPoint`

---

### Phase 3 — Navigation: ReplayViewController and ReplayNavigationBar

**Macro Phase:** A  
**Objective:** Implement C-02 `ReplayViewController` and C-04 `ReplayNavigationBar`.

**Scope:**
- `app/ui/replay/replay_view_controller.py` — new file
- `app/ui/replay/panels/replay_navigation_bar.py` — new file

**Forbidden scope:** All domain contracts. Panel renderers (C-03, C-05–C-09).

**Dependencies:** Phase 2 (`ReplaySession` available from entry point).

**Expected artifacts:**
- `ReplayViewController`: holds `ReplaySession` and `current_position: int`; exposes `navigate_forward()`, `navigate_backward()`, `current_record` property
- `ReplayNavigationBar`: renders progress indicator; forward/backward buttons with enabled/disabled state

**Completion criteria:**
- `current_position` initialised to `0`.
- `navigate_forward()` increments by 1; clamped at `timeline.last_position`.
- `navigate_backward()` decrements by 1; clamped at `timeline.first_position`.
- When `timeline.is_empty=True`, no navigation events dispatched.
- `current_record` returns `session.question_results[current_position]`.
- `ReplayNavigationBar` forward button disabled when `is_at_last`.
- `ReplayNavigationBar` backward button disabled when `is_at_first`.
- Progress label renders `"Question N of M"`.
- Unit tests for boundary cases: first, last, empty session.

**Regression gate:** ≥ 6574 passing, zero failures.

**Architectural invariants:**
- I-C02-01: position always in `[first_position, last_position]`.
- I-C02-02: no events when `is_empty`.
- I-C02-03: no service invocation from `ReplayViewController`.
- I-C04-05: `ReplayNavigationBar` does not own position state.

**Commit boundary:** One atomic commit — `feat(replay-ui): add ReplayViewController and ReplayNavigationBar`

---

*Architecture Checkpoint A is mandatory here. Implementation of Macro Phase B may not begin until Checkpoint A is AUTHORIZED.*

---

### Architecture Checkpoint A

**Trigger:** Completion of Phase 3.  
**Scope:** Phases 1–3 against EPIC-04-ARCHITECTURE-FREEZE.md.  
**Produces:** AUTHORIZED or BLOCKED.

**Checkpoint must verify:**
- `UIStateMachine` extension is additive; no existing tests broken.
- `ReplayContext` is not a domain contract; not persisted.
- `ReplayViewController` owns `current_position` exclusively; no other component stores it.
- `ReplayNavigationBar` emits signals only; does not own state.
- No `InterviewState` field modified.
- No `ReplaySession` field modified.
- Regression suite green at ≥ 6574.

---

### Phase 4 — Panel Renderers (C-03, C-05, C-06, C-07, C-08, C-09)

**Macro Phase:** B  
**Objective:** Implement all six panel renderers.

**Scope:**
- `app/ui/replay/panels/replay_session_summary_panel.py` — C-03
- `app/ui/replay/panels/replay_question_panel.py` — C-05
- `app/ui/replay/panels/replay_execution_result_panel.py` — C-06
- `app/ui/replay/panels/replay_scoring_panel.py` — C-07
- `app/ui/replay/panels/replay_coaching_panel.py` — C-08
- `app/ui/replay/panels/replay_error_boundary.py` — C-09

**Forbidden scope:** All domain contracts. Layout integration files. `ReplaySession`. `replay_node`.

**Dependencies:** Phase 3 (Architecture Checkpoint A AUTHORIZED; `current_record` available).

**Expected artifacts per panel:**

| Component | Key behaviors |
|---|---|
| C-03 `ReplaySessionSummaryPanel` | Renders all 8 `ReplaySessionMetadata` fields; conditional score/hire_decision/level when `has_scoring=True`; "score not available" when `has_scoring=False` |
| C-05 `ReplayQuestionPanel` | All 18 `ReplayQuestionRecord` fields; empty answer → neutral indicator; empty strengths/weaknesses → not rendered; follow-up conditional; hint conditional; delegates to C-06 when `is_coding_question=True` |
| C-06 `ReplayExecutionResultPanel` | `execution_status`, `passed_tests`, `total_tests`; pass rate percentage; only when `is_coding_question=True` |
| C-07 `ReplayScoringPanel` | 10 `ScoringSnapshot` fields; gating section conditional; only when `has_scoring=True` |
| C-08 `ReplayCoachingPanel` | Section A: `narrative.insights`, `overview_section`; Section B: `coaching_snapshot` objectives and recommendations; clearly labelled sections; empty-state indicators |
| C-09 `ReplayErrorBoundary` | Pattern-matches `failure_reason` to candidate message; raw string not exposed; single CTA button |

**Completion criteria (per panel):**
- Renders correctly from a fixture `ReplaySession`.
- Conditional sections visible/hidden per their guard conditions.
- No service call. No LLM call.
- Unit test per panel with at least: happy path, empty optional fields, conditional section off.
- C-09 unit test: raw `failure_reason` not present in rendered output.

**Regression gate:** ≥ 6574 passing, zero failures.

**Architectural invariants (all panels):**
- All inputs sourced exclusively from `ReplaySession` or its sub-artifacts.
- No write to any domain artifact.
- Freeze invariant: none of the 9 excluded fields appear in any panel render.

**Commit boundary:** One atomic commit per panel renderer (6 commits total):
- `feat(replay-ui): add ReplaySessionSummaryPanel (C-03)`
- `feat(replay-ui): add ReplayQuestionPanel (C-05)`
- `feat(replay-ui): add ReplayExecutionResultPanel (C-06)`
- `feat(replay-ui): add ReplayScoringPanel (C-07)`
- `feat(replay-ui): add ReplayCoachingPanel (C-08)`
- `feat(replay-ui): add ReplayErrorBoundary (C-09)`

Each sub-commit must leave the regression suite green.

---

### Phase 5 — Layout Integration

**Macro Phase:** B  
**Objective:** Integrate the Replay UI into the Gradio layout and event binding layer. Add the replay entry trigger to the report view and session history list. Verify responsive layout at all three breakpoints.

**Scope:**
- `app/ui/layout/layout_builder.py` — add replay view section; add replay trigger button to report view
- `app/ui/layout/assets/styles.py` — add responsive CSS rules for replay panels
- `app/ui/bindings/ui_bindings.py` — add replay event bindings
- `app/ui/bindings/orchestrators/ui_event_orchestrator.py` — add replay trigger handler
- `app/ui/replay/__init__.py` — new package init

**Forbidden scope:** All domain contracts. `replay_node`. `ReplaySession`. All Phase 1–4 component files (already implemented).

**Dependencies:** Phase 4 (all panel renderers implemented).

**Expected artifacts:**
- "Replay Session" button in report view triggers `ReplayContext(session_id=..., is_active=True)`.
- `UIStateMachine.resolve()` called with `ReplayContext` — returns `UIState.REPLAY`.
- Replay view renders: `ReplayNavigationBar` + `ReplayQuestionPanel` + `ReplaySessionSummaryPanel` + conditional `ReplayScoringPanel` + `ReplayCoachingPanel`.
- Exit replay clears `ReplayContext`; returns to `UIState.REPORT`.
- Responsive CSS: three breakpoints (< 640px, 640–1024px, > 1024px) per Data Model §6.3.

**Completion criteria:**
- Integration test: full replay flow with fixture `SessionHistory` — entry → navigation (forward 3 steps, backward 1 step) → exit.
- Responsive layout test: layout correct at 320px, 768px, 1280px viewports.
- `UIStateMachine` compatibility regression: all pre-EPIC-04 state resolution paths pass unchanged.
- No `InterviewState` modification confirmed.

**Regression gate:** ≥ 6574 passing, zero failures.

**Commit boundary:** One atomic commit — `feat(replay-ui): integrate replay panels into gradio layout`

---

### Phase 6 — Architectural and Performance Tests

**Macro Phase:** B  
**Objective:** Implement the LLM-free architectural test (AA-02) and the 20-question performance profiling gate (AA-08).

**Scope:**
- `tests/ui/replay/test_replay_llm_free.py` — new architectural test (AA-02)
- `tests/ui/replay/test_replay_performance.py` — new performance profiling test (AA-08)
- `tests/ui/replay/fixtures/session_history_20q.py` — 20-question `SessionHistory` fixture

**Forbidden scope:** All production files (tests only in this phase).

**Dependencies:** Phase 5 (full implementation complete).

**Expected artifacts:**

**AA-02 Architectural Test (LLM-free enforcement):**
- Mocks all LLM service interfaces (`NarrativeGenerator`, `CoachingEngine`, `InterviewEvaluationService`, and any adapter calling an external model API).
- Invokes the full Replay UI render path with a fixture `ReplaySession`.
- Asserts zero LLM service invocations.
- Test name: `test_replay_ui_render_path_invokes_no_llm_service`.

**AA-08 Performance Tests:**
- 20-question `SessionHistory` fixture constructed from stored domain contracts.
- Measures: (a) `replay_node` execution + first render ≤ 1000ms; (b) position change + panel re-render ≤ 100ms; (c) `ReplaySession` in-memory footprint ≤ 500 KB.
- All three gates must PASS before the epic may close.

**Completion criteria:**
- `test_replay_ui_render_path_invokes_no_llm_service` — PASS.
- `test_replay_load_time_20q` — PASS (≤ 1000ms).
- `test_replay_navigation_step_20q` — PASS (≤ 100ms).
- `test_replay_memory_footprint_20q` — PASS (≤ 500 KB).

**Regression gate:** ≥ 6574 + new tests passing, zero failures.

**Commit boundary:** One atomic commit — `test(replay-ui): add LLM-free architectural test and performance profiling gate`

---

*Architecture Checkpoint B is mandatory here. CAR may not begin until Checkpoint B is AUTHORIZED.*

---

### Architecture Checkpoint B

**Trigger:** Completion of Phase 6.  
**Scope:** Phases 4–6 against EPIC-04-ARCHITECTURE-FREEZE.md.  
**Produces:** AUTHORIZED (proceed to CAR) or BLOCKED.

**Checkpoint must verify:**
- All panel renderers read exclusively from `ReplaySession`.
- Freeze invariant: none of the 9 excluded fields rendered.
- Layout integration does not modify any domain contract.
- AA-02 test passes (zero LLM invocations).
- AA-08 performance gates pass.
- AA-07 responsive layout verified at all three breakpoints.
- Regression suite green at ≥ 6574 + new tests.

---

## 5. Commit Boundary Table

| # | Phase | Commit Message | Regression Gate |
|---|---|---|---|
| C1 | Phase 1 | `feat(replay-ui): add UIState.REPLAY and UIStateMachine REPLAY routing` | ≥ 6574 |
| C2 | Phase 2 | `feat(replay-ui): add ReplayContext and ReplayEntryPoint` | ≥ 6574 |
| C3 | Phase 3 | `feat(replay-ui): add ReplayViewController and ReplayNavigationBar` | ≥ 6574 |
| — | Checkpoint A | Architecture Checkpoint A — review only; no commit | — |
| C4 | Phase 4a | `feat(replay-ui): add ReplaySessionSummaryPanel (C-03)` | ≥ 6574 |
| C5 | Phase 4b | `feat(replay-ui): add ReplayQuestionPanel (C-05)` | ≥ 6574 |
| C6 | Phase 4c | `feat(replay-ui): add ReplayExecutionResultPanel (C-06)` | ≥ 6574 |
| C7 | Phase 4d | `feat(replay-ui): add ReplayScoringPanel (C-07)` | ≥ 6574 |
| C8 | Phase 4e | `feat(replay-ui): add ReplayCoachingPanel (C-08)` | ≥ 6574 |
| C9 | Phase 4f | `feat(replay-ui): add ReplayErrorBoundary (C-09)` | ≥ 6574 |
| C10 | Phase 5 | `feat(replay-ui): integrate replay panels into gradio layout` | ≥ 6574 |
| C11 | Phase 6 | `test(replay-ui): add LLM-free architectural test and performance profiling gate` | ≥ 6574 + new |
| — | Checkpoint B | Architecture Checkpoint B — review only; no commit | — |

**Total production commits:** 11  
**Total review gates:** 2 (Checkpoint A after C3; Checkpoint B after C11)

---

## 6. Validation Gates Summary

| Gate | Phase | Trigger | Pass Condition |
|---|---|---|---|
| UIStateMachine compatibility regression | Phase 1 | After C1 | All pre-EPIC-04 state resolution tests pass unchanged |
| REPLAY state routing | Phase 1 | After C1 | `UIState.REPLAY` returned when `is_active=True` |
| Entry routing test | Phase 2 | After C2 | `is_successful=True` → C-02; `is_successful=False` → C-09 |
| Navigation boundary test | Phase 3 | After C3 | Position clamped at `first_position`/`last_position` |
| Architecture Checkpoint A | After Phase 3 | After C3 | AUTHORIZED before Macro Phase B begins |
| Panel unit tests | Phase 4 | After each C4–C9 | All conditional sections correct; no excluded fields rendered |
| Freeze invariant test | Phase 4 | After C9 | None of the 9 excluded `ReplaySession` fields present in any rendered output |
| Integration test | Phase 5 | After C10 | Full replay flow with fixture; entry → 3 forward → 1 backward → exit |
| Responsive layout test | Phase 5 | After C10 | Correct layout at 320px, 768px, 1280px |
| LLM-free architectural test (AA-02) | Phase 6 | After C11 | Zero LLM invocations during render path |
| Performance gate — load time (AA-08) | Phase 6 | After C11 | `replay_node` + first render ≤ 1000ms for 20q fixture |
| Performance gate — navigation step (AA-08) | Phase 6 | After C11 | Position change + re-render ≤ 100ms |
| Performance gate — memory (AA-08) | Phase 6 | After C11 | `ReplaySession` ≤ 500 KB for 20q fixture |
| Architecture Checkpoint B | After Phase 6 | After C11 | AUTHORIZED before CAR |
| Full regression suite | Every phase | After every commit | ≥ 6574 passing, zero failures |

---

## 7. Implementation Risk Mitigations

All risks from EPIC-04-ARCHITECTURE-FREEZE.md §5.2 are translated to explicit gates:

| Risk | Gate | Phase |
|---|---|---|
| AA-02 — LLM invocation from render path | `test_replay_ui_render_path_invokes_no_llm_service` | Phase 6 |
| AA-08 — Load ≤ 1s for 20q session | `test_replay_load_time_20q` | Phase 6 |
| AA-08 — Navigation ≤ 100ms | `test_replay_navigation_step_20q` | Phase 6 |
| AA-08 — Memory ≤ 500 KB | `test_replay_memory_footprint_20q` | Phase 6 |
| Gradio mobile breakpoint CSS edge case | Responsive layout test at 320px | Phase 5 |
| `UIStateMachine.resolve()` breaking existing callers | UIStateMachine compatibility regression | Phase 1 |

---

## 8. Regression Baseline Protocol

- **Baseline declared:** 6574 passing tests, 0 failures (EPIC-03 close state, verified 2026-07-16).
- Every implementation prompt must reference the **updated** baseline from the previous phase, not the epic-opening baseline.
- No commit is tagged complete if any test in the suite is failing.
- If a phase introduces a new test that fails transiently during implementation, the implementation plan must be split: the failing test may not be committed until the production code that makes it pass is committed in the same increment.

---

## 9. Allowed and Forbidden Scope Per Phase

| File / Module | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
|---|---|---|---|---|---|---|
| `app/ui/ui_state.py` | **ALLOWED** | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
| `app/ui/state_machine/ui_state_machine.py` | **ALLOWED** | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
| `app/ui/replay/replay_context.py` | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden | Forbidden | Forbidden |
| `app/ui/replay/replay_entry_point.py` | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden | Forbidden | Forbidden |
| `app/ui/replay/replay_view_controller.py` | Forbidden | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden | Forbidden |
| `app/ui/replay/panels/replay_navigation_bar.py` | Forbidden | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden | Forbidden |
| `app/ui/replay/panels/replay_session_summary_panel.py` | Forbidden | Forbidden | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden |
| `app/ui/replay/panels/replay_question_panel.py` | Forbidden | Forbidden | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden |
| `app/ui/replay/panels/replay_execution_result_panel.py` | Forbidden | Forbidden | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden |
| `app/ui/replay/panels/replay_scoring_panel.py` | Forbidden | Forbidden | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden |
| `app/ui/replay/panels/replay_coaching_panel.py` | Forbidden | Forbidden | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden |
| `app/ui/replay/panels/replay_error_boundary.py` | Forbidden | Forbidden | Forbidden | **ALLOWED** (create) | Forbidden | Forbidden |
| `app/ui/layout/layout_builder.py` | Forbidden | Forbidden | Forbidden | Forbidden | **ALLOWED** | Forbidden |
| `app/ui/layout/assets/styles.py` | Forbidden | Forbidden | Forbidden | Forbidden | **ALLOWED** | Forbidden |
| `app/ui/bindings/` | Forbidden | Forbidden | Forbidden | Forbidden | **ALLOWED** | Forbidden |
| `tests/ui/replay/` | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | **ALLOWED** (create) |
| `domain/contracts/` | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
| `app/graph/` | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
| `domain/contracts/replay/replay_session.py` | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
| `InterviewState` | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
