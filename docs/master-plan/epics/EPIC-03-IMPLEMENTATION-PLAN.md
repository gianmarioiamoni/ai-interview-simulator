# EPIC-03 — Implementation Plan

**Status:** ACCEPTED — Implementation COMPLETE; EPIC CLOSED  
**Date:** 2026-07-15  
**Close-out sync:** 2026-07-22 — living status aligned at Release Documentation Synchronization  
**Epic Close:** 2026-07-15 (`e13a47f` migration cleanup)  
**Epic ID:** EPIC-V13-03  
**Authority:** EPIC-03-ARCHITECTURE-FREEZE.md (FROZEN, commit `db28db7`)  
**Regression baseline:** 6332 passing tests  
**Precondition:** Architecture Freeze declared. Implementation Plan Dependency Validation applied (§2). No implementation begins without this plan accepted.  
**Living Overview:** `EPIC-03-OVERVIEW.md`

---

## 1. Objectives

### 1.1 Implementation Goals

1. Rename the V1.2 `ReplaySession` orchestrator to `ReplayOrchestrator` without breaking any test.
2. Implement all new V1.3 replay domain contracts: `ReplaySession`, `ReplayQuestionRecord`, `ReplaySessionMetadata`, `ReplayTimeline`, `ReplayTimelineEntry`, `ReplayRequest`, `ReplayGraphState`, `ReplayFeatureEngine`, `ReplaySessionBuilder`.
3. Implement `replay_node` as a standalone LangGraph node that reads `SessionHistory` and produces `ReplaySession` deterministically.
4. Implement the Replay Graph (`replay_node → END`) as a separate, independently invocable graph.
5. Extend `ReplayValidator` with `validate_session`; extend `ReplayStatistics` with `from_session`.
6. Delete all V1.2 legacy replay artifacts (`ReplayResult`, `ReplayOrchestrator`, `validate_result`, `from_result`) in the same increment as V1.3 activation.
7. Enforce domain invariant I-11 (LLM-free) by architectural test.
8. Enforce Reconstruction Completeness (P-08) by architectural test.
9. Leave the regression suite green (≥ 6332 passing, zero failures) at every phase boundary.

### 1.2 Success Criteria

- `replay_node` reconstructs any stored `SessionHistory` into a `ReplaySession` deterministically.
- `ReplaySession` is `frozen=True`, `extra=forbid`, sole builder, sole writer.
- Domain invariant I-11 enforced by architectural test: zero LLM calls during `replay_node` execution.
- Reconstruction completeness test: every `ReplaySession` field explicitly enumerated in `ReplaySessionBuilder.build()`.
- Determinism test: ≥ 20 distinct `SessionHistory` fixtures; dual-invocation field equality on all knowledge fields.
- `ReplayResult`, `ReplayOrchestrator`, `validate_result`, `from_result` deleted.
- No `LongitudinalProfile` import in any replay contract module.
- Full regression suite: ≥ 6332 passing, zero failures.

### 1.3 Out of Scope

- Replay UI (EPIC-04) — no frontend components in this epic.
- `LongitudinalProfile` integration — prohibited by ADR-034 D7.
- Re-submission of answers — prohibited by Master Plan §6.
- AI commentary during replay — prohibited by I-11.
- Persistence of `ReplaySession` — prohibited by ADR-037 D1 §1.4.
- `ReplayLevel.REASONING` activation — reserved; not implemented.
- Performance optimization of replay reconstruction — deferred to EPIC-09.

---

## 2. Phase Breakdown

### Phase 1 — Legacy Rename (Migration Bridge)

**Purpose:** Rename the V1.2 `ReplaySession` orchestrator to `ReplayOrchestrator` to free the `ReplaySession` name for the V1.3 Projection Artifact. This phase is purely a rename — no new behavior is introduced. The regression suite must be green before Phase 2 begins.

**Affected modules:**
- `domain/contracts/replay/replay_session.py` → rename to `replay_orchestrator.py`
- `domain/contracts/replay/__init__.py` — update exports
- `tests/domain/contracts/replay/test_replay_contracts.py` — update all `ReplaySession` (orchestrator) references to `ReplayOrchestrator`
- `tests/domain/contracts/replay/conftest.py` — update if `ReplaySession` (orchestrator) is referenced

**Dependencies:** None. This phase has no dependency on any new artifact.

**Expected outputs:**
- `domain/contracts/replay/replay_orchestrator.py` (renamed from `replay_session.py`)
- `ReplayOrchestrator` class (renamed from `ReplaySession`)
- `ReplayError` retained in `replay_orchestrator.py`
- `__init__.py` exports `ReplayOrchestrator`, `ReplayError` (not `ReplaySession`)
- All existing tests pass under the new name

**Completion criteria:**
- `domain/contracts/replay/replay_session.py` does not exist.
- `domain/contracts/replay/replay_orchestrator.py` exists; exports `ReplayOrchestrator`, `ReplayError`.
- `__init__.py` does not export `ReplaySession` from the orchestrator module.
- Regression suite: ≥ 6332 passing, zero failures.

---

### Phase 2 — New Domain Contracts (Value Objects and Sub-Artifacts)

**Purpose:** Implement all new V1.3 frozen domain contracts that have no dependency on `replay_node` or the Replay Graph. These are standalone `frozen=True` artifacts.

**Sub-phases (each independently committable):**

**2a — ReplayRequest**
- New file: `domain/contracts/replay/replay_request.py`
- Tests: `tests/domain/contracts/replay/test_replay_request.py`

**2b — ReplaySessionMetadata**
- New file: `domain/contracts/replay/replay_session_metadata.py`
- Tests: `tests/domain/contracts/replay/test_replay_session_metadata.py`

**2c — ReplayQuestionRecord**
- New file: `domain/contracts/replay/replay_question_record.py`
- Tests: `tests/domain/contracts/replay/test_replay_question_record.py`

**2d — ReplayTimelineEntry + ReplayTimeline**
- New file: `domain/contracts/replay/replay_timeline.py`
- Tests: `tests/domain/contracts/replay/test_replay_timeline.py`

**2e — ReplaySession (V1.3 Projection Artifact)**
- New file: `domain/contracts/replay/replay_session_v13.py`
- Note: uses `_v13` suffix until Phase 4 deletion enables rename to `replay_session.py`
- Tests: `tests/domain/contracts/replay/test_replay_session_v13.py`

**2f — ReplayGraphState**
- New file: `domain/contracts/replay/replay_graph_state.py`
- Tests: `tests/domain/contracts/replay/test_replay_graph_state.py`

**Dependencies:** Phase 1 complete. Each sub-phase is independently committable in the order 2a → 2b → 2c → 2d → 2e → 2f. 2e depends on 2b, 2c, 2d. 2f depends on 2a and 2e.

**Expected outputs:** 6 new contract modules; 6 new test modules. All contracts `frozen=True`, `extra=forbid`. All tests pass.

**Completion criteria:**
- All 6 contract modules exist with correct field sets per Data Model §2–§4, §7.
- Each contract's immutability test passes (mutation raises `ValidationError`).
- Each contract's `extra=forbid` test passes.
- `ReplaySession` (V1.3) model validators V-RS-01 through V-RS-06 all pass.
- `ReplayQuestionRecord` validators V-RQR-01 through V-RQR-04 all pass.
- `ReplayRequest` validators V-RRQ-01 and V-RRQ-02 all pass.
- Regression suite: ≥ 6332 passing, zero failures.

---

### Phase 3 — ReplayFeatureEngine and ReplaySessionBuilder

**Purpose:** Implement the read-only `ReplayFeatureEngine` and the `ReplaySessionBuilder` (sole construction path for `ReplaySession`). These are the two core assembly components. Both are independently testable without `replay_node`.

**Sub-phases:**

**3a — ReplayFeatureEngine**
- New file: `domain/contracts/replay/replay_feature_engine.py`
- Tests: `tests/domain/contracts/replay/test_replay_feature_engine.py`
- Verify: `get_features()` and `get_feature()` return stored values from `CandidateProfileSnapshot`; any computation method raises `RuntimeError`.

**3b — ReplaySessionBuilder**
- New file: `domain/contracts/replay/replay_session_builder.py`
- Tests: `tests/domain/contracts/replay/test_replay_session_builder.py`
- Verify: `build()` enforces all RC-B-01 through RC-B-07 invariants; `as_failed()` produces a failed `ReplaySession`; wildcard copy is absent; all 18 fields explicitly enumerated.
- Architectural test (P-08 — Reconstruction Completeness): asserts `ReplaySessionBuilder.build()` references every declared field of `ReplaySession` by name.

**Dependencies:** Phase 2 complete. 3a has no dependency on 3b. 3b depends on all Phase 2 contracts and 3a.

**Expected outputs:** 2 new modules; 2 new test modules; 1 architectural test for Reconstruction Completeness.

**Completion criteria:**
- `ReplayFeatureEngine` returns stored features from `CandidateProfileSnapshot` without invoking live `FeatureEngine`.
- `ReplayFeatureEngine` raises `RuntimeError` for any computation method call.
- `ReplaySessionBuilder.build()` enforces all RC-B invariants.
- `ReplaySessionBuilder.as_failed()` produces a valid failed `ReplaySession`.
- Reconstruction Completeness architectural test passes.
- Regression suite: ≥ 6332 passing, zero failures.

---

### Phase 4 — replay_node and Replay Graph

**Purpose:** Implement `replay_node` as a LangGraph node and wire it into the standalone Replay Graph. This phase introduces all runtime behavior of the replay pipeline.

**Sub-phases:**

**4a — replay_node**
- New file: `app/graph/nodes/replay_node.py`
- Responsibilities: load `SessionHistory` from persistence (read-only); instantiate `ReplayFeatureEngine`; call `ReplaySessionBuilder`; produce `ReplaySession`; handle non-fatal failures; emit structured logs.
- Tests: `tests/app/graph/nodes/test_replay_node.py`

**4b — Replay Graph**
- New file: `app/graph/replay_graph.py`
- Responsibilities: define `replay_node → END` graph; configure with `ReplayGraphState`; disable LangGraph checkpointing.
- Tests: `tests/app/graph/test_replay_graph_wiring.py`

**4c — Architectural invariant tests (I-11, I-R03, I-R07)**
- New file: `tests/app/graph/nodes/test_replay_architectural_invariants.py`
- I-11: mock all LLM service interfaces; assert zero invocations during `replay_node` execution.
- I-R03: assert `replay_node` module imports no live session node; assert `ReplayGraphState` does not reference `InterviewState`.
- I-R07: mock persistence layer; assert zero write calls during `replay_node` execution.
- I-R06: import graph analysis — assert zero cross-references between replay contracts and `LongitudinalProfile` contracts.

**Dependencies:** Phase 3 complete. 4a depends on Phase 3. 4b depends on 4a. 4c depends on 4a and 4b.

**Expected outputs:** 3 new modules; 3 new test modules; architectural invariant tests for I-11, I-R03, I-R07, I-R06.

**Completion criteria:**
- `replay_node` produces `ReplaySession` from a stored `SessionHistory` fixture.
- `replay_node` produces `ReplaySession(is_successful=False)` when `SessionHistory` not found.
- Replay Graph wired as `replay_node → END`.
- LangGraph checkpointing disabled on Replay Graph.
- I-11 architectural test passes (zero LLM calls).
- I-R03 architectural test passes (no live session imports, no `InterviewState` in `ReplayGraphState`).
- I-R07 architectural test passes (zero persistence writes).
- I-R06 architectural test passes (zero cross-references to `LongitudinalProfile`).
- Regression suite: ≥ 6332 passing, zero failures.

---

### Phase 5 — Determinism Tests

**Purpose:** Verify deterministic reconstruction across ≥ 20 `SessionHistory` fixtures. This phase produces only tests — no new production code.

**New files:**
- `tests/app/graph/nodes/test_replay_determinism.py`

**Fixture coverage (minimum):**
- Standard sessions with `scoring_snapshot` present.
- Sessions with `scoring_snapshot=None` (no evaluation completed).
- Sessions with `question_results=()` (empty).
- Coding question sessions (with `execution_status`, `passed_tests`, `total_tests`).
- Sessions with `replay_level=KNOWLEDGE` (includes `observation_store_snapshot`).
- Sessions with `follow_up_question` present.
- Sessions with `ai_hint_explanation` present.
- Sessions with `company=None`.
- Sessions where `question_timeline[*].duration_seconds` are all `None` (→ `session_duration_seconds=None`).
- Sessions where `question_timeline[*].duration_seconds` are all non-None (→ `session_duration_seconds` aggregated).
- At least 10 additional sessions with varying question counts (1, 3, 5, 10, 20 questions).

**Test protocol:** For each fixture, invoke `replay_node` twice; assert field-level equality on all knowledge fields; exclude `manifest.replay_timestamp` and `manifest.replay_engine_version` from equality assertion (per Data Model §13.2).

**Dependencies:** Phase 4 complete.

**Completion criteria:**
- ≥ 20 determinism fixtures defined.
- All determinism assertions pass on both invocations.
- P0/P1/P2 failure classification logic present (per Data Model §13.3).
- Regression suite: ≥ 6332 passing, zero failures.

---

### Phase 6 — Legacy Deletion

**Purpose:** Delete all V1.2 legacy replay artifacts. Rename `replay_session_v13.py` → `replay_session.py`. Update `__init__.py`. This is the migration completion step — no behavior change, only deletion and rename.

**Files to delete:**
- `domain/contracts/replay/replay_result.py`
- `domain/contracts/replay/replay_orchestrator.py`

**Files to modify:**
- `domain/contracts/replay/replay_validator.py` — delete `validate_result` method; keep `validate_context`; add `validate_session` (implementing RS-V-01 through RS-V-10 from Data Model §11.2).
- `domain/contracts/replay/replay_statistics.py` — delete `from_result` factory; add `from_session` factory (implementing new fields from Data Model §12.2).
- `domain/contracts/replay/__init__.py` — remove `ReplayResult`, `ReplayOrchestrator`, `ReplayError` exports; add `ReplaySession`, `ReplaySessionBuilder`, `ReplayRequest`, `ReplayFeatureEngine`, `ReplayGraphState`, `ReplayTimeline`, `ReplayTimelineEntry`, `ReplayQuestionRecord`, `ReplaySessionMetadata`.
- `tests/domain/contracts/replay/test_replay_contracts.py` — migrate all `ReplayResult`-based tests to `ReplaySession` equivalents; delete `ReplayResult` import; delete `ReplayOrchestrator` import.

**Files to rename:**
- `domain/contracts/replay/replay_session_v13.py` → `domain/contracts/replay/replay_session.py`
- `tests/domain/contracts/replay/test_replay_session_v13.py` → `tests/domain/contracts/replay/test_replay_session.py`

**Sub-phases (must be applied as a single atomic commit or as two sequential commits with green regression between them):**

**6a — Extend ReplayValidator and ReplayStatistics** (add new methods before deleting old ones)
- Add `validate_session` to `ReplayValidator`.
- Add `from_session` to `ReplayStatistics`.
- All existing tests still pass (old methods present).

**6b — Delete legacy artifacts and rename**
- Delete `replay_result.py`, `replay_orchestrator.py`.
- Delete `validate_result`, `from_result`.
- Rename `replay_session_v13.py` → `replay_session.py`.
- Update `__init__.py`.
- Migrate tests.
- Regression suite must be green.

**Dependencies:** Phase 5 complete.

**Completion criteria:**
- `domain/contracts/replay/replay_result.py` does not exist.
- `domain/contracts/replay/replay_orchestrator.py` does not exist.
- `domain/contracts/replay/replay_session.py` exists (V1.3 `ReplaySession` — renamed from `_v13`).
- `ReplayValidator.validate_result` does not exist.
- `ReplayStatistics.from_result` does not exist.
- `ReplayValidator.validate_session` exists and implements RS-V-01 through RS-V-10.
- `ReplayStatistics.from_session` exists and includes `question_count`, `has_scoring`, `total_follow_up_questions`.
- `__init__.py` exports V1.3 artifact set only.
- Regression suite: ≥ 6332 passing, zero failures.

---

## 3. Implementation Order

```
Phase 1 — Legacy Rename (ReplayOrchestrator)
  ↓ [regression suite green]
Phase 2 — New Domain Contracts (2a → 2b → 2c → 2d → 2e → 2f)
  ↓ [regression suite green]
Phase 3 — ReplayFeatureEngine + ReplaySessionBuilder (3a → 3b)
  ↓ [regression suite green]
Phase 4 — replay_node + Replay Graph + Architectural Invariant Tests (4a → 4b → 4c)
  ↓ [regression suite green]
Phase 5 — Determinism Tests
  ↓ [regression suite green]
Phase 6 — Legacy Deletion (6a → 6b)
  ↓ [regression suite green]
EPIC-03 COMPLETE
```

No phase may begin until its predecessor leaves the regression suite green. No parallel work across phases — each phase builds on a stable, tested baseline.

Within Phase 2, sub-phases 2a through 2f are serialized (2a first; 2e cannot begin until 2b, 2c, 2d are complete; 2f cannot begin until 2a and 2e are complete). Within Phase 3, 3a precedes 3b. Within Phase 4, 4a precedes 4b, which precedes 4c. Within Phase 6, 6a precedes 6b.

---

## 4. File Ownership

### Phase 1

| Action | File |
|---|---|
| Rename (create) | `domain/contracts/replay/replay_orchestrator.py` |
| Delete | `domain/contracts/replay/replay_session.py` |
| Modify | `domain/contracts/replay/__init__.py` |
| Modify | `tests/domain/contracts/replay/test_replay_contracts.py` |
| Modify (if needed) | `tests/domain/contracts/replay/conftest.py` |

**Frozen (must not be touched in Phase 1):** All files outside `domain/contracts/replay/` and `tests/domain/contracts/replay/`.

### Phase 2

| Action | File |
|---|---|
| Create | `domain/contracts/replay/replay_request.py` |
| Create | `domain/contracts/replay/replay_session_metadata.py` |
| Create | `domain/contracts/replay/replay_question_record.py` |
| Create | `domain/contracts/replay/replay_timeline.py` |
| Create | `domain/contracts/replay/replay_session_v13.py` |
| Create | `domain/contracts/replay/replay_graph_state.py` |
| Create | `tests/domain/contracts/replay/test_replay_request.py` |
| Create | `tests/domain/contracts/replay/test_replay_session_metadata.py` |
| Create | `tests/domain/contracts/replay/test_replay_question_record.py` |
| Create | `tests/domain/contracts/replay/test_replay_timeline.py` |
| Create | `tests/domain/contracts/replay/test_replay_session_v13.py` |
| Create | `tests/domain/contracts/replay/test_replay_graph_state.py` |

**Frozen in Phase 2:** `replay_orchestrator.py`; all files outside `domain/contracts/replay/` and `tests/domain/contracts/replay/`.

### Phase 3

| Action | File |
|---|---|
| Create | `domain/contracts/replay/replay_feature_engine.py` |
| Create | `domain/contracts/replay/replay_session_builder.py` |
| Create | `tests/domain/contracts/replay/test_replay_feature_engine.py` |
| Create | `tests/domain/contracts/replay/test_replay_session_builder.py` |

**Frozen in Phase 3:** All Phase 1 and Phase 2 outputs.

### Phase 4

| Action | File |
|---|---|
| Create | `app/graph/nodes/replay_node.py` |
| Create | `app/graph/replay_graph.py` |
| Create | `tests/app/graph/nodes/test_replay_node.py` |
| Create | `tests/app/graph/test_replay_graph_wiring.py` |
| Create | `tests/app/graph/nodes/test_replay_architectural_invariants.py` |

**Frozen in Phase 4:** All Phase 1–3 outputs. Live session graph files (`interview_graph.py`, all existing `app/graph/nodes/` except the new file).

### Phase 5

| Action | File |
|---|---|
| Create | `tests/app/graph/nodes/test_replay_determinism.py` |

**Frozen in Phase 5:** All production files. No production code modified in Phase 5.

### Phase 6

| Action | File |
|---|---|
| Add methods to | `domain/contracts/replay/replay_validator.py` (Phase 6a) |
| Add methods to | `domain/contracts/replay/replay_statistics.py` (Phase 6a) |
| Delete | `domain/contracts/replay/replay_result.py` (Phase 6b) |
| Delete | `domain/contracts/replay/replay_orchestrator.py` (Phase 6b) |
| Delete methods from | `domain/contracts/replay/replay_validator.py` (Phase 6b) |
| Delete methods from | `domain/contracts/replay/replay_statistics.py` (Phase 6b) |
| Rename | `domain/contracts/replay/replay_session_v13.py` → `replay_session.py` (Phase 6b) |
| Rename | `tests/domain/contracts/replay/test_replay_session_v13.py` → `test_replay_session.py` (Phase 6b) |
| Modify | `domain/contracts/replay/__init__.py` (Phase 6b) |
| Modify | `tests/domain/contracts/replay/test_replay_contracts.py` (Phase 6b — remove ReplayResult / ReplayOrchestrator tests) |

---

## 5. Dependency Graph

```
Phase 1 (rename only)
  │
  └──→ Phase 2a (ReplayRequest)
         └──→ Phase 2b (ReplaySessionMetadata)
                └──→ Phase 2c (ReplayQuestionRecord)
                       └──→ Phase 2d (ReplayTimeline + ReplayTimelineEntry)
                              └──→ Phase 2e (ReplaySession V1.3) ←── depends on 2b, 2c, 2d
                                     └──→ Phase 2f (ReplayGraphState) ←── depends on 2a, 2e
                                            └──→ Phase 3a (ReplayFeatureEngine)
                                                   └──→ Phase 3b (ReplaySessionBuilder)
                                                          └──→ Phase 4a (replay_node)
                                                                 └──→ Phase 4b (Replay Graph)
                                                                        └──→ Phase 4c (Arch invariants)
                                                                               └──→ Phase 5 (Determinism)
                                                                                      └──→ Phase 6a (extend validator + statistics)
                                                                                             └──→ Phase 6b (delete legacy)
```

No cyclic dependencies. Each phase has at most one predecessor at the phase level. No phase is an island — every phase feeds into the next.

---

## 6. Validation Gates

### Phase 1

| Gate | Requirement |
|---|---|
| Unit tests | All existing `test_replay_contracts.py` tests pass under `ReplayOrchestrator` name |
| Regression | 6332 passing, zero failures |
| Completion gate | `replay_session.py` absent; `replay_orchestrator.py` present; `__init__.py` exports `ReplayOrchestrator` |

### Phase 2 (per sub-phase)

| Gate | Requirement |
|---|---|
| Contract tests | `frozen=True` mutation test passes; `extra=forbid` test passes; all model validators pass |
| Unit tests | Constructor, property, and validator tests for each new contract |
| Regression | ≥ 6332 passing, zero failures after each sub-phase commit |
| Completion gate | All 6 contracts exist with complete field sets per Data Model §2–§4, §7 |

### Phase 3

| Gate | Requirement |
|---|---|
| Unit tests (3a) | `ReplayFeatureEngine.get_features()` returns stored values; computation methods raise `RuntimeError` |
| Unit tests (3b) | `ReplaySessionBuilder.build()` enforces all RC-B invariants; `as_failed()` produces valid failed session |
| Architectural test | Reconstruction Completeness: every `ReplaySession` field enumerated explicitly in `build()` |
| Regression | ≥ 6332 passing, zero failures |
| Completion gate | Reconstruction Completeness test passes |

### Phase 4

| Gate | Requirement |
|---|---|
| Unit tests (4a) | `replay_node` produces `ReplaySession` from fixture; handles missing `SessionHistory`; non-fatal failure path |
| Unit tests (4b) | Replay Graph wired; `replay_node → END`; checkpointing disabled |
| Architectural tests (4c) | I-11 (zero LLM calls), I-R03 (no live imports / no `InterviewState`), I-R07 (zero persistence writes), I-R06 (zero longitudinal cross-references) |
| Regression | ≥ 6332 passing, zero failures |
| Completion gate | All 4 architectural invariant tests pass |

### Phase 5

| Gate | Requirement |
|---|---|
| Determinism tests | ≥ 20 fixtures; dual-invocation equality on all knowledge fields |
| Coverage | All fixture categories from §2 Phase 5 present |
| Regression | ≥ 6332 passing, zero failures |
| Completion gate | All ≥ 20 determinism assertions pass |

### Phase 6

| Gate (6a) | Requirement |
|---|---|
| Unit tests | `validate_session` tests for RS-V-01 through RS-V-10 pass; `from_session` tests pass |
| Regression | ≥ 6332 passing, zero failures |

| Gate (6b) | Requirement |
|---|---|
| Deletion verification | `replay_result.py` absent; `replay_orchestrator.py` absent; `validate_result` absent; `from_result` absent |
| Rename verification | `replay_session.py` present (V1.3 artifact); no `_v13` suffix modules remain |
| Import audit | `__init__.py` exports V1.3 artifact set only; no `ReplayResult`, `ReplayOrchestrator` exported |
| Regression | ≥ 6332 passing, zero failures |
| Completion gate | All deletion and rename verifications pass; regression green |

---

## 7. Risk Assessment

### Regression Risks

| Risk | Phase | Mitigation |
|---|---|---|
| `ReplayOrchestrator` rename breaks an import not found in `test_replay_contracts.py` | 1 | Run full regression immediately after rename; any `ImportError` surfaces before Phase 2 begins |
| `ReplaySession` (V1.3) name collision with `_v13` suffix causes IDE confusion | 2e | Suffix is temporary; removed in Phase 6b; test file uses `_v13` naming consistently throughout Phase 2–5 |
| `ReplaySessionBuilder` does not cover all 18 fields (Reconstruction Completeness failure) | 3b | Architectural test in Phase 3 blocks advancement if any field is missing |
| `replay_node` import accidentally pulls in a live session module | 4a | I-R03 architectural test in Phase 4c catches this; keep `replay_node` imports restricted to replay contracts and persistence layer only |
| Determinism test fixture construction is brittle (hardcoded IDs that clash across tests) | 5 | Use `uuid4()` for all `session_id` and `candidate_identity_id` values in fixtures; never hardcode |

### Migration Risks

| Risk | Phase | Mitigation |
|---|---|---|
| Phase 6b deletion causes `ImportError` in a test file that still imports `ReplayResult` | 6b | Phase 6a regression gate: run full suite before beginning 6b; no deletion before all consumers migrated |
| `replay_session_v13.py` rename in Phase 6b breaks imports in test files created in Phase 2 | 6b | All test files under `tests/domain/contracts/replay/` that import from `replay_session_v13` must be updated in the same 6b commit |
| `validate_result` deletion breaks a test that was not found in the pre-Phase-6 audit | 6b | Phase 6a green regression is the gate; any test that imports `validate_result` surfaces before 6b begins |

### Serialization Risks

| Risk | Phase | Mitigation |
|---|---|---|
| `candidate_answer` join by `question_id` silently produces empty strings for all questions if `TranscriptEntry` uses a different `question_id` format than `QuestionResultRecord` | 4a | Write explicit unit test for the join logic with a fixture that has matching and non-matching IDs; assert `candidate_answer = ""` for the non-matching case |
| `session_duration_seconds` returns `None` for all sessions due to `QuestionTimelineEntry.duration_seconds=None` being the norm | 4a | Profile existing `SessionHistory` fixtures before Phase 4 to determine actual coverage; document expected `None` rate in test fixtures |

### Compatibility Risks

| Risk | Phase | Mitigation |
|---|---|---|
| Existing `test_replay_contracts.py` tests rely on behavior that `ReplayOrchestrator` inherits from its V1.2 `ReplaySession` name (unlikely but possible via string matching) | 1 | Review test file for any string-based assertions on the class name before Phase 1 commit |
| `ReplayStatistics.from_session` field set does not cover all fields that downstream consumers of `from_result` expected | 6a | Review all callers of `from_result` before Phase 6a; ensure `from_session` is a strict superset |

---

## 8. Rollback Strategy

Each phase produces an independently committable change. Rollback is by `git revert` of the phase commit(s).

| Phase | Rollback action | Side effects |
|---|---|---|
| 1 | `git revert` — restores `replay_session.py`; removes `replay_orchestrator.py`; reverts `__init__.py` and test updates | None — Phase 2 has not begun |
| 2 (any sub-phase) | `git revert` the sub-phase commit | Only the specific new contract file and its test are removed; no other phase is affected |
| 3 (3a or 3b) | `git revert` the sub-phase commit | No production impact — Phase 4 has not begun |
| 4a | `git revert` — removes `replay_node.py` and its tests | No impact on Phase 1–3 artifacts |
| 4b | `git revert` — removes `replay_graph.py` and its tests | `replay_node.py` remains; no impact |
| 4c | `git revert` — removes architectural invariant tests only | Production code unchanged |
| 5 | `git revert` — removes determinism test file only | Production code unchanged |
| 6a | `git revert` — removes `validate_session` and `from_session` additions | No deletions yet; fully reversible |
| 6b | `git revert` — **complex**: restores deleted files, reverses rename | Phase 6b is the only phase with a non-trivial rollback; if 6b must be reverted, `replay_result.py` and `replay_orchestrator.py` must be restored from git history; `replay_session.py` (V1.3) must be renamed back to `replay_session_v13.py`; `__init__.py` reverted. This is a known risk — Phase 6b must be committed only when all preceding gates are fully green and confirmed. |

**General rule:** All phases before Phase 6b are cleanly reversible with a single `git revert`. Phase 6b is the only irreversible commit — it deletes files. Phase 6b must only be executed when all other phase completion gates have passed.

---

## 9. Acceptance Criteria

EPIC-03 is complete when all of the following are satisfied simultaneously:

### Architecture

- [ ] `replay_node` exists as a LangGraph node in `app/graph/nodes/replay_node.py`.
- [ ] Replay Graph exists in `app/graph/replay_graph.py` as a standalone `replay_node → END` graph.
- [ ] `ReplaySession` (V1.3) is `frozen=True`, `extra=forbid`, with `schema_version="1.0"`.
- [ ] `ReplaySessionBuilder` is the sole construction path for `ReplaySession`.
- [ ] `replay_node` is the sole writer of `ReplaySession`.
- [ ] `ReplaySession` is not persisted anywhere.
- [ ] `ReplayGraphState` does not reference `InterviewState`.
- [ ] No replay contract imports `LongitudinalProfile`.
- [ ] `ReplayResult`, `ReplayOrchestrator`, `validate_result`, `from_result` do not exist in the codebase.

### Testing

- [ ] I-11 architectural test passes: zero LLM service calls during `replay_node` execution across all fixtures.
- [ ] Reconstruction Completeness architectural test passes: all 18 `ReplaySession` fields explicitly enumerated in `ReplaySessionBuilder.build()`.
- [ ] I-R03 architectural test passes: `replay_node` imports no live session node; `ReplayGraphState` does not reference `InterviewState`.
- [ ] I-R07 architectural test passes: zero persistence writes during `replay_node` execution.
- [ ] I-R06 architectural test passes: zero cross-references between replay contracts and `LongitudinalProfile`.
- [ ] Determinism tests: ≥ 20 fixtures; all dual-invocation knowledge field equality assertions pass.
- [ ] `ReplayValidator.validate_session` tests: RS-V-01 through RS-V-10 all pass.
- [ ] Full regression suite: ≥ 6332 passing tests, zero failures.

### Migration

- [ ] `domain/contracts/replay/replay_result.py` does not exist.
- [ ] `domain/contracts/replay/replay_orchestrator.py` does not exist.
- [ ] `domain/contracts/replay/replay_session_v13.py` does not exist.
- [ ] `domain/contracts/replay/replay_session.py` is the V1.3 `ReplaySession` artifact.
- [ ] `domain/contracts/replay/__init__.py` exports only V1.3 artifact names.

### Implementation Dependency Validation

This plan satisfies the V13-DEVELOPMENT-PLAYBOOK.md §2 Implementation Dependency Validation rule:

- Every commit boundary is independently implementable: each phase depends only on artifacts introduced by prior phases.
- Every commit boundary has an executable test gate: each phase has at least one test that can be written and run at that boundary without requiring artifacts from future phases.
- No circular implementation dependencies: the dependency graph in §5 is acyclic.
- Every phase leaves the full regression suite green when applied in sequence.

---

*This document is the authoritative Implementation Plan for EPIC-03. Amendments to phase sequencing that do not affect the target architecture, ADRs, contracts, or data model require only a Mini Architecture Freeze per V13-DEVELOPMENT-PLAYBOOK.md §9. Amendments that affect any of the above require a full Freeze Integrity Check and potentially a new ADR.*
