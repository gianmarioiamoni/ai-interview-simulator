# EPIC-02 — Implementation Plan

**Status:** ACCEPTED — Implementation COMPLETE (P1–P5); EPIC CLOSED  
**Epic ID:** EPIC-V13-02  
**Date:** 2026-07-14  
**Close-out sync:** 2026-07-22 — living status aligned at Release Documentation Synchronization  
**Epic Close:** 2026-07-15 (`e051ada`)  
**Precondition:** Architecture Freeze declared (`EPIC-02-ARCHITECTURE-FREEZE.md`). All frozen documents accepted.  
**Authority:** This document defines the implementation sequence for EPIC-02. Every phase must preserve the invariants declared in ADR-034. Any deviation requires a Freeze Integrity Check before the deviation is committed.  
**Living Overview:** `EPIC-02-OVERVIEW.md`

---

## 1. Implementation Phases

EPIC-02 is implemented in five sequential phases. Each phase is independently committable and leaves the runtime in a valid, tested state.

| Phase | Name | Type | Blocking Next? |
|---|---|---|---|
| P1 | Domain Contracts — Core Artifacts | New contracts | Yes |
| P2 | Domain Contracts — LearningProgress Extension | Contract extension | Yes |
| P3 | Repository Interface + Infrastructure Adapter | New infrastructure | Yes |
| P4 | Runtime Node (`longitudinal_update_node`) | New graph node | Yes |
| P5 | ProgressTracker + LearningProgressBuilder Migration | Service migration | No — parallel with P4 post-graph stabilisation |

**No bridge phases are required.** The implementation sequence is strictly additive until P5, which migrates an existing service's input source. No temporary compatibility shim is needed because `LearningProgress` is a derived, never-persisted artifact — changing its input source from `SessionHistory[]` to `LongitudinalProfile` has no persistence migration cost.

---

## 2. Critical Path

```
P1 (domain contracts) → P2 (LearningProgress extension) → P3 (repository) → P4 (runtime node) → P5 (service migration)
```

All phases are sequential on the critical path. P5 depends on P4 completing successfully (the node must be running and writing profiles before the service migration can be validated end-to-end). P3 may be developed in parallel with P2 if two developers are available — but P4 depends on both P2 and P3.

**Critical path blockers:**
- P1 must be complete before any other phase begins (all subsequent phases import from the new contracts).
- P3 repository interface must be available before P4 can call `LongitudinalProfileRepository.save()`.
- P4 must be running before P5 end-to-end validation is meaningful.

---

## 3. Parallelizable Work

| Parallelizable pair | Condition |
|---|---|
| P2 (LearningProgress extension) ∥ P3 (repository interface) | After P1 is merged — both depend only on P1 artifacts |
| P3 unit tests ∥ P2 unit tests | After P1 merged — fully independent |
| Architectural test suite ∥ P5 service migration | Architectural tests (LP-01, LP-03, LP-11) can be written starting at P1; they become meaningful as phases complete |

---

## 4. Bridge Phases

**No bridge phases required.**

Rationale:
- All new contracts (`LongitudinalProfile`, `LongitudinalSessionEntry`, `LongitudinalSessionMetadata`, `CrossSessionLanguageCapability`) are new — no existing contract is modified in a breaking way.
- `LearningProgress` and `SessionProgressEntry` are extended with new fields carrying safe defaults — existing serialization and callers are not broken by the extension.
- `LearningProgressBuilder` input source changes from `SessionHistory[]` to `LongitudinalProfile`. Since `LearningProgress` is never persisted, there is no persistent data migration. The change is a clean input substitution.
- `LongitudinalProfile` is a new persistent artifact — there is no existing data to migrate.

No temporary shims, compatibility adapters, or dual-write paths are planned.

---

## 5. Commit Boundaries

Each commit boundary must leave the test suite green and the runtime in a valid state.

### P1 — Domain Contracts (3 commits)

| Commit | Content | Test gate |
|---|---|---|
| P1-C1 | `domain/contracts/longitudinal/longitudinal_profile.py` — `LongitudinalProfile`, `LongitudinalSessionEntry`, `LongitudinalSessionMetadata`, `CrossSessionLanguageCapability` | Unit tests for all model validators (LP-V-01 through LP-V-08, LC-V-01 through LC-V-05, XC-01 through XC-05) |
| P1-C2 | `domain/contracts/longitudinal/longitudinal_profile_builder.py` — `LongitudinalProfileBuilder` (all 10 steps from DC §4.3) | Unit tests: first-session path, n-session path, idempotency guard (LP-07), identity mismatch rejection, language capability aggregation, trend direction computation |
| P1-C3 | `domain/contracts/longitudinal/__init__.py`, `domain/contracts/longitudinal/longitudinal_profile_repository.py` — repository interface only | Unit test: repository interface is abstract; no concrete adapter (P3 scope) |

### P2 — LearningProgress Extension (2 commits)

| Commit | Content | Test gate |
|---|---|---|
| P2-C1 | Extend `domain/contracts/progress/learning_progress.py`: add `BehavioralTrend`, `FeatureTrend`, `BehavioralScore`; add `behavioral_trend`, `language_capability_summary`, `has_sufficient_data` to `LearningProgress`; add `behavioral_scores`, `language_ids_present` to `SessionProgressEntry` | Unit tests: existing `LearningProgress` fields unchanged; new fields have safe defaults; invariants LP-LP-01 through LP-LP-07 pass |
| P2-C2 | Extend `domain/contracts/progress/learning_progress_builder.py`: migrate input from `SessionHistory[]` to `LongitudinalProfile`; implement `BehavioralTrend` derivation; implement `FeatureTrend` computation; implement `has_sufficient_data` | Unit tests: builder produces correct `LearningProgress` from a synthetic 3-session `LongitudinalProfile`; builder returns empty `LearningProgress` when profile is `None`; builder rejects `SessionHistory[]` input |

### P3 — Repository Interface + Infrastructure Adapter (1 commit)

| Commit | Content | Test gate |
|---|---|---|
| P3-C1 | `infrastructure/longitudinal/longitudinal_profile_repository_impl.py` — concrete implementation of `LongitudinalProfileRepository`; technology choice per infrastructure layer | Integration tests: `save` → `get` round-trip; `exists` returns `False` before first save, `True` after; replace-on-write semantics verified |

**Sequencing note:** Repository dependency injection wiring (`infrastructure/__init__.py` updates) requires the existence of `longitudinal_update_node` (the sole DI consumer). It is therefore moved to P4-C1, where the node and its wiring are introduced together.

### P4 — Runtime Node (2 commits)

| Commit | Content | Test gate |
|---|---|---|
| P4-C1 | `app/graph/nodes/longitudinal_update_node.py` — full node: read `InterviewState.session_history`; extract `language_capabilities` from session state; load prior profile from repository; call `LongitudinalProfileBuilder`; call `repository.save()`; non-fatal failure path with `WARNING` log. Repository dependency injection wiring; `infrastructure/__init__.py` updates | Unit tests: success path; persistence failure path (node returns without raising; logs `WARNING`; invariant LP-09); idempotency guard (same `interview_index` is no-op; LP-07); integration test: `longitudinal_update_node` can receive a repository instance via DI |
| P4-C2 | `app/graph/` — wire `longitudinal_update_node` into graph: edge `report_node → longitudinal_update_node → END`; update graph definition | Integration test: full session close sequence (`session_close_node → report_node → longitudinal_update_node → END`) executes without error; `LongitudinalProfile` is persisted after session close |

### P5 — ProgressTracker + Service Migration (2 commits)

| Commit | Content | Test gate |
|---|---|---|
| P5-C1 | Extend `services/progress/progress_tracker.py` — source behavioral trend data from `LongitudinalProfile`; produce extended `LearningProgress` with `BehavioralTrend` and `CrossSessionLanguageCapability` | Unit tests: `ProgressTracker` returns `LearningProgress.has_sufficient_data = False` for one-session profile; returns trend data for two-session profile |
| P5-C2 | End-to-end integration test: 3-session synthetic run; verify `LongitudinalProfile` accumulated correctly; verify `LearningProgress` derived from `LongitudinalProfile` is consistent with direct session data | Integration test suite green |

---

## 6. Regression Strategy

### Baseline
All V1.2 and EPIC-01 tests must pass before any EPIC-02 code is committed. Confirmed at Architecture Freeze baseline (HEAD `ed9edb4`).

### Per-phase regression policy

| Phase | Regression scope | Acceptance |
|---|---|---|
| P1 | Full existing suite + new P1 unit tests | 100% pass — new contracts are additive, no existing code modified |
| P2 | Full existing suite + P1 + new P2 unit tests | 100% pass — `LearningProgress` field additions carry safe defaults; existing callers unaffected |
| P3 | Full existing suite + P1 + P2 + P3 integration tests | 100% pass — new infrastructure; no existing infrastructure modified |
| P4 | Full existing suite + P1–P3 + P4 unit + integration | 100% pass — graph extension is additive; session close sequence unchanged before `longitudinal_update_node` |
| P5 | Full existing suite + P1–P4 + P5 integration | 100% pass — service migration: `LearningProgressBuilder` input change. BREAKING CHANGE RISK: any test that calls `LearningProgressBuilder` with `SessionHistory[]` directly must be updated to pass a `LongitudinalProfile` instead. See §7. |

### P5 regression risk — `LearningProgressBuilder` input change

Existing tests that pass `SessionHistory[]` to `LearningProgressBuilder` will fail after P2-C2 because the builder no longer accepts `SessionHistory[]`. This is expected. These tests must be updated as part of P2-C2:

1. Identify all test files that invoke `LearningProgressBuilder` directly.
2. Replace `SessionHistory[]` input with a synthetic `LongitudinalProfile`.
3. Verify the test assertions still hold against the new output shape (which adds `behavioral_trend`, `language_capability_summary`, `has_sufficient_data`).

This is a test migration, not a production behaviour regression.

---

## 7. Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `LanguageCapability` instances not available in `InterviewState` at `longitudinal_update_node` execution time | Medium | High | Inspect `InterviewState` fields at P4-C1 start. If `language_capabilities` are not already a state field, identify where they are produced (session evaluation path) and confirm they are accessible before session state expires. This may require reading `InterviewState.language_profile` or a dedicated field. Do not modify `SessionHistory`. |
| `LearningProgressBuilder` test migration underestimates scope — many call sites | Medium | Medium | `rg` search for all `LearningProgressBuilder` usages before P2-C2. Count call sites. Estimate migration effort. Flag if > 10 files affected. |
| `LongitudinalProfileBuilder` trend direction rule (§2.6 DC: ±0.05 threshold) proves brittle under test data | Low | Low | Rule is stated in DC §2.6. Test with boundary values: `latest = earliest + 0.05` (stable), `+0.051` (improving). |
| Infrastructure adapter serialization of `tuple[LanguageCapability, ...]` within `LongitudinalSessionMetadata` | Medium | Medium | `LanguageCapability` is a Pydantic `frozen=True` model. Pydantic v2 handles nested model serialization natively. Verify round-trip fidelity in P3-C1 integration test. |
| Graph wiring (P4-C2) breaks existing end-to-end session flow | Low | High | `longitudinal_update_node` is non-fatal — a graph wiring error (e.g., wrong edge) will not break session close, but it will silently skip the node. P4-C2 integration test must verify the node is actually called, not just that the session completes. Use a mock repository with assertion on `save()` call count. |
| `LongitudinalProfile` size growth (embedding full `CandidateProfileSnapshot` per session) | Low | Low | V1.3 single-node persistence. Acceptable per DATA-MODEL.md §1.5. No mitigation required for V1.3. |

---

## 8. Testing Strategy

### Unit tests (per phase)

| Test | Phase | Target | Invariants verified |
|---|---|---|---|
| `LongitudinalProfile` validator | P1 | LP-V-01 through LP-V-08 | Field count, ordering, uniqueness, epoch, timestamps |
| `CrossSessionLanguageCapability` validator | P1 | LC-V-01 through LC-V-05 | Score bounds, uniqueness, trend direction |
| `LongitudinalProfileBuilder` — first-session | P1 | LP-02, LP-04, LP-06 | Builder-only construction; `frozen=True`; ordered accumulation |
| `LongitudinalProfileBuilder` — n-session accumulation | P1 | LP-V-01 through LP-V-08 | Running means, session count, epoch update |
| `LongitudinalProfileBuilder` — idempotency | P1 | LP-07 | Duplicate `interview_index` → no-op |
| `LongitudinalProfileBuilder` — identity mismatch | P1 | LP-05 | Raises `ValueError` on candidate mismatch |
| `LearningProgress` extension | P2 | LP-LP-01 through LP-LP-07 | New fields present; safe defaults; no persistence |
| `LearningProgressBuilder` — from `LongitudinalProfile` | P2 | LP-LP-07 | Rejects `SessionHistory[]`; correct derivation from profile |
| `LearningProgressBuilder` — empty profile | P2 | LP-LP-03 | Returns `has_sufficient_data=False` when profile is `None` |
| `longitudinal_update_node` — success | P4 | LP-01, LP-09 | Repository `save()` called exactly once |
| `longitudinal_update_node` — persistence failure | P4 | LP-09 | Node completes; `WARNING` log emitted; no exception propagated |
| `longitudinal_update_node` — idempotency | P4 | LP-07 | Same session re-execution is a no-op |

### Architectural tests

| Test | Target | Verification method |
|---|---|---|
| LP-01 Sole Writer | `longitudinal_update_node` is the only caller of `LongitudinalProfileRepository.save()` | Import graph analysis: no other module imports and calls `save()` |
| LP-03 No LLM Calls | `longitudinal_update_node` and `LongitudinalProfileBuilder` | Import graph analysis: no LLM service, `FeatureEngine`, `NarrativeGenerator`, `KnowledgePipeline` imported |
| LP-08 Reconstruction | Synthetic 10-session dataset | Reconstruct from `SessionHistory[]`; compare all fields except `language_capability_summary` (asserted `== []`) and timestamps |
| LP-11 Replay Independence | All replay contracts | Import graph analysis: no replay contract imports `LongitudinalProfile`; no `LongitudinalProfile` contract imports replay |
| LP-LP-06 No persistence | `LearningProgress` | Import graph analysis: `LearningProgress` is never imported by any persistence adapter |

### Integration tests

| Test | Phase | Scope |
|---|---|---|
| Repository round-trip | P3 | `save` → `get` → verify field equality; replace-on-write verified |
| Full session close | P4 | `session_close_node → report_node → longitudinal_update_node → END`; profile persisted; `session_count = 1` |
| 3-session synthetic run | P5 | Profile accumulates 3 entries; `LearningProgress` has `has_sufficient_data = True`; trend data present |
| Failure recovery | P4 | Inject persistence failure; verify session close succeeds; verify `WARNING` log; verify profile not corrupted |

---

## 9. Required Builders

| Builder | Status | Phase | Location |
|---|---|---|---|
| `LongitudinalProfileBuilder` | New | P1 | `domain/contracts/longitudinal/longitudinal_profile_builder.py` |
| `LearningProgressBuilder` | Migrated (input source change) | P2 | `domain/contracts/progress/learning_progress_builder.py` |

No new engines. No new LLM-backed services.

---

## 10. Required Runtime Nodes

| Node | Status | Phase | Location | Position in graph |
|---|---|---|---|---|
| `longitudinal_update_node` | New | P4 | `app/graph/nodes/longitudinal_update_node.py` | After `report_node`; before `END` |

Graph close sequence after P4:
```
completion → evaluation_aggregate → session_close → report → longitudinal_update → END
```

The node is non-fatal. If it raises, the graph must catch the exception and proceed to `END` with a `WARNING` log. This must be implemented as a try/except within the node, not as a graph-level error handler (which would affect other nodes).

---

## 11. Required Contract Migrations

| Contract | Migration type | Phase | Risk |
|---|---|---|---|
| `LearningProgress` | Additive field extension (`behavioral_trend`, `language_capability_summary`, `has_sufficient_data`) | P2 | Low — new fields carry safe defaults; no existing serialized data |
| `SessionProgressEntry` | Additive field extension (`behavioral_scores`, `language_ids_present`) | P2 | Low — new fields carry safe defaults |
| `LearningProgressBuilder` | Input source change (`SessionHistory[]` → `LongitudinalProfile`) | P2 | Medium — test call sites must be migrated |

**Contracts NOT migrated:**
- `LongitudinalProfile` — new contract, no migration.
- `SessionHistory` — unchanged (ADR-034 Decision 3; OI-03 confirmed no change required).
- `CandidateProfileSnapshot` — unchanged (read-only from EPIC-02 perspective).
- `LanguageCapability` — unchanged (transient; no contract modification).
- `KnowledgeSnapshot` — unchanged.
- `Report` — unchanged.
- Any replay contract — unchanged (LP-11).

---

## 12. Stopping Rule Checkpoints

A Stopping Rule is triggered if any of the following conditions is detected. Implementation halts until the condition is resolved with a Freeze Integrity Check or a new ADR.

| Checkpoint | Trigger condition | Action |
|---|---|---|
| SR-01 | `InterviewState` does not carry `language_capabilities` and they cannot be extracted at `longitudinal_update_node` execution time | Freeze Integrity Check — determine correct extraction point; may require an additive `InterviewState` field with sole-writer declaration |
| SR-02 | `LongitudinalProfileBuilder` requires a field from `SessionHistory` that does not exist in the current v2.0 schema | Freeze Integrity Check — evaluate whether `SessionHistory` extension is required; if so, new ADR before proceeding |
| SR-03 | Architectural import test (LP-03 No LLM Calls) fails — builder or node imports a computation service | Halt — LP-03 is a constitutional invariant (P-01); implementation must be corrected before proceeding |
| SR-04 | Architectural import test (LP-11 Replay Independence) fails | Halt — LP-11 is a constitutional invariant; implementation must be corrected before proceeding |
| SR-05 | Any phase leaves the existing regression suite non-green | Halt — regression suite must be green before next phase begins |
| SR-06 | `LearningProgressBuilder` falls back to `SessionHistory[]` under any code path | Halt — ADR-034 Decision 5 violation; architectural exception; requires Freeze Integrity Check |

---

## 13. Freeze Integrity Check Checkpoints

A Freeze Integrity Check is required if any frozen planning document must be modified during implementation.

| Checkpoint | Trigger | Scope |
|---|---|---|
| FIC-01 | Any field addition to `LongitudinalProfile`, `LongitudinalSessionEntry`, `LongitudinalSessionMetadata`, or `CrossSessionLanguageCapability` | Update EPIC-02-DATA-MODEL.md; verify traceability table remains complete; update EPIC-02-DOMAIN-CONTRACTS.md if invariants are affected |
| FIC-02 | Any field addition to `LearningProgress`, `SessionProgressEntry`, `BehavioralTrend`, `FeatureTrend`, `BehavioralScore` | Update EPIC-02-DOMAIN-CONTRACTS.md §2; update EPIC-02-DATA-MODEL.md §2; verify LP-LP invariants |
| FIC-03 | `InterviewState` requires a new field to carry `language_capabilities` to `longitudinal_update_node` | Update EPIC-02-DOMAIN-CONTRACTS.md §4.2 (builder inputs) and EPIC-02-ARCHITECTURE-FREEZE.md §5.1; declare sole writer of the new state field |
| FIC-04 | Any change to `LongitudinalProfileRepository` interface (beyond `get`, `save`, `exists`) | Update EPIC-02-DATA-MODEL.md §4.2 |
| FIC-05 | Any change to the graph node sequence (e.g., `longitudinal_update_node` position changes) | Update EPIC-02-LONGITUDINAL-PROFILE.md §8; verify non-fatal semantics still hold |
| FIC-06 | Any breaking change to `LanguageCapability`, `SessionHistory`, `KnowledgeSnapshot`, or `CandidateProfileSnapshot` | Full Freeze Integrity Check across all four frozen planning documents; new ADR mandatory |

---

## 14. Expected Behavioural Changes Per Phase

| Phase | Observable behaviour change | Invisible to candidate? |
|---|---|---|
| P1 | New domain contracts available; no runtime change | Yes |
| P2 | `LearningProgress` contract extended with new fields (safe defaults); `LearningProgressBuilder` migrated to `LongitudinalProfile` input — any call to `LearningProgressBuilder` with no profile returns `has_sufficient_data=False` | Yes — UI not yet connected |
| P3 | `LongitudinalProfileRepository` implementation available; no runtime change | Yes |
| P4 | Session close sequence extended: after `report_node`, `longitudinal_update_node` runs and persists `LongitudinalProfile`. First observable side-effect: `LongitudinalProfile` is written to persistence after each session. Failure is non-fatal. | Yes — UI not yet connected |
| P5 | `ProgressTracker` now reads `LongitudinalProfile` instead of `SessionHistory[]`. After 2+ sessions, `LearningProgress` carries `behavioral_trend` and `language_capability_summary`. `has_sufficient_data = True`. | Depends on EPIC-05 UI integration — not user-visible until Unified Report (EPIC-05) |

---

## 15. Completion Criteria Per Phase

### P1 Complete when:
- [ ] `domain/contracts/longitudinal/` module exists with all four contracts.
- [ ] All LP-V-01 through LP-V-08 and LC-V-01 through LC-V-05 unit tests pass.
- [ ] `LongitudinalProfileBuilder` unit tests pass (all 10 steps, idempotency, identity mismatch, first-session path).
- [ ] `LongitudinalProfileRepository` interface declared (abstract).
- [ ] Architectural tests LP-02 and LP-03 pass (import graph analysis).
- [ ] Existing regression suite: 100% pass.

### P2 Complete when:
- [ ] `LearningProgress` extended with `behavioral_trend`, `language_capability_summary`, `has_sufficient_data`.
- [ ] `SessionProgressEntry` extended with `behavioral_scores`, `language_ids_present`.
- [ ] `LearningProgressBuilder` accepts `LongitudinalProfile`, not `SessionHistory[]`.
- [ ] All LP-LP-01 through LP-LP-07 unit tests pass.
- [ ] Existing `LearningProgressBuilder` test call sites migrated.
- [ ] Architectural test LP-LP-07 passes.
- [ ] Existing regression suite: 100% pass.

### P3 Complete when:
- [ ] `LongitudinalProfileRepository` concrete implementation committed to infrastructure layer.
- [ ] `save` → `get` round-trip integration test passes (all fields equal).
- [ ] Replace-on-write semantics verified by integration test.
- [ ] `exists` behaviour verified.
- [ ] Serialization round-trip for `tuple[LanguageCapability, ...]` within `LongitudinalSessionMetadata` verified.
- [ ] Existing regression suite: 100% pass.

**Note:** Repository DI wiring is not part of P3 completion. It is committed in P4-C1 alongside the node that consumes the repository.

### P4 Complete when:
- [ ] `longitudinal_update_node` committed with success and failure paths.
- [ ] Repository DI wiring committed; `infrastructure/__init__.py` updated.
- [ ] Integration test: `longitudinal_update_node` can receive a repository instance via DI.
- [ ] Node is wired into the graph: `report_node → longitudinal_update_node → END`.
- [ ] Integration test: full session close produces persisted `LongitudinalProfile`.
- [ ] Failure path test: persistence failure → node completes → `WARNING` logged → session close unaffected.
- [ ] Idempotency test: re-execution for same `interview_index` is a no-op.
- [ ] Architectural test LP-01 passes (sole writer — no other caller of `repository.save()`).
- [ ] Architectural test LP-03 passes (no LLM calls in node or builder).
- [ ] Existing regression suite: 100% pass.

### P5 Complete when:
- [ ] `ProgressTracker` reads `LongitudinalProfile` via repository; produces extended `LearningProgress`.
- [ ] 3-session synthetic integration test: profile accumulated; `LearningProgress` consistent.
- [ ] `has_sufficient_data = True` for 2+ sessions; `False` for 1 session.
- [ ] `BehavioralTrend` computed correctly (trend direction rule per DC §2.6).
- [ ] Architectural test LP-08 passes (reconstruction: 10-session synthetic dataset).
- [ ] Architectural test LP-11 passes (replay independence — import graph clean).
- [ ] All success criteria from EPIC-02-LONGITUDINAL-PROFILE.md §12 (criteria 1–14) verified.
- [ ] Existing regression suite: 100% pass.
- [ ] FR-02 gate eligible.

---

## 16. Implementation Sequence — Summary

```
BASELINE (HEAD ed9edb4)
│
├── P1 — Domain Contracts
│   ├── P1-C1: longitudinal_profile.py (all 4 contracts)
│   ├── P1-C2: longitudinal_profile_builder.py
│   └── P1-C3: repository interface + __init__
│
├── P2 — LearningProgress Extension      ← may run ∥ with P3 after P1
│   ├── P2-C1: LearningProgress / SessionProgressEntry field extensions
│   └── P2-C2: LearningProgressBuilder migration
│
├── P3 — Repository + Infrastructure     ← may run ∥ with P2 after P1
│   └── P3-C1: repository implementation
│
├── P4 — Runtime Node
│   ├── P4-C1: longitudinal_update_node + DI wiring
│   └── P4-C2: graph wiring
│
└── P5 — Service Migration
    ├── P5-C1: ProgressTracker migration
    └── P5-C2: end-to-end integration test + FR-02 eligibility
```

**Total commits: 10 commits across 5 phases.** (P3/C2 merged into P4-C1; sequencing correction 2026-07-15.)

---

## Appendix A — Pre-Implementation Check (SR-01 Investigation Required)

Before beginning P4-C1, confirm that `LanguageCapability` instances are accessible to `longitudinal_update_node` at execution time. The investigation must answer:

1. Does `InterviewState` carry a `language_profile` or `language_capabilities` field that is populated before `longitudinal_update_node` runs?
2. If yes: confirm the field contains `LanguageCapability` instances (not `LanguageCapabilityFeature` entries in `ProfileFeature`).
3. If no: an additive `InterviewState` field is required with sole-writer declaration (FIC-03 trigger). This field must be written by the session evaluation path before `longitudinal_update_node` executes. The sole writer of this field must be declared before P4-C1 is committed.

This investigation is a **read-only codebase inspection** (no code changes). It must occur before P4 begins and its findings must be documented as a pre-P4 note in the commit message of P4-C1 or in an updated FIC-03 Freeze Integrity Check.

---

*This document governs EPIC-02 implementation. Any deviation from a frozen architectural decision requires a Freeze Integrity Check before the deviation is committed. Phase completion criteria are binding — a phase is not complete until all checklist items pass.*

*Revision 2026-07-14: Initial implementation plan. Produced after Architecture Freeze declaration.*

*Revision 2026-07-15: Sequencing correction only — no architectural changes. Removed P3/C2 (repository DI wiring) as a standalone commit. DI wiring merged into P4-C1 alongside `longitudinal_update_node`, which is the sole consumer of the injected repository. Total commits reduced from 11 to 10. No ADR changes. No contract changes. No data model changes. No architecture freeze changes.*
