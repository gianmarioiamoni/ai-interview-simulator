# EPIC-02 — Longitudinal Profile Architecture Planning

**Status:** PLANNING  
**Epic ID:** EPIC-V13-02  
**Date:** 2026-07-14  
**Phase:** Phase 2 — Core Domain  
**Precondition:** EPIC-01 closed; FR-01 passed; `Report` is sole authoritative scoring artifact; `InterviewEvaluation` deleted.  
**Authority:** This document is the architecture planning artifact for EPIC-02. It does not freeze decisions. Decisions will be frozen in subsequent ADRs after the Architecture Review phase.

---

## 1. Vision

V1.2 accumulates rich, structured knowledge within a session. At session close, that knowledge is sealed into `SessionHistory` and projected into `Report`. The projection is complete. The continuity is not.

A candidate who completes multiple sessions has no cross-session identity in the current architecture. `CandidateIdentity` exists as a stable anchor (ADR-016A) and `CandidateProfileSnapshot` exists as a closure artifact (ADR-022), but nothing connects the two across session boundaries. Each session is an island.

The Longitudinal Profile closes this gap. It is a persistent, cross-session accumulation of `CandidateProfileSnapshot` instances, anchored to `CandidateIdentity`, that enables the platform to track a candidate's knowledge evolution over time. It is not a session artifact — it is a candidate-scoped artifact that spans sessions.

The vision for EPIC-02 is not to build a feature. It is to declare and enforce the architectural boundary that separates session-scoped knowledge from candidate-scoped knowledge, and to give that boundary a concrete, persistent representation.

---

## 2. Current Architecture

### What Exists

The following artifacts are present and frozen after EPIC-01:

**Session-scoped artifacts (closed per session):**
- `CandidateProfileSnapshot` — immutable point-in-time projection of `CandidateProfile` at session close; embedded in `KnowledgeSnapshot` → `SessionHistory`. Carries `candidate_identity_id`, `features: tuple[ProfileFeature, ...]`, `closed_at_question_index`, `source_observation_ids`, `total_feature_count`, `mean_confidence`, `profile_schema_version`.
- `SessionHistory` (schema v2.0) — write-once per session; carries `candidate_identity_id` as foreign key to `CandidateIdentity`; carries `interview_index` (sequential session number); carries `knowledge_snapshot`, `scoring_snapshot`, `scoring_narrative`, `question_results`, `transcript`, `question_timeline`, `interview_metadata`, `language_profile`, `replay_metadata`.
- `LearningProgress` — derived, read-only, never-persisted cross-session view computed on demand from `SessionHistory[]`. Carries `SessionProgressEntry` instances (one per `SessionHistory`). Sole creation path: `LearningProgressBuilder`. Not a persistent artifact — recomputed each time.

**Candidate-scoped anchor:**
- `CandidateIdentity` (ADR-016A) — immutable aggregate root; `candidate_identity_id` (uuid4); `created_at`; `display_name` (only mutable field); `schema_version`. Present and operative as a session anchor. Not yet an active cross-session accumulation anchor.

**Replay infrastructure (partial — EPIC-03 scope):**
- `ReplaySession` — assembles `ReplayResult` from `ReplayContext` (which carries `KnowledgeSnapshot` from `SessionHistory`). Currently reads only session-scoped knowledge. No longitudinal data in replay path.
- `ReplayResult` — carries `profile_snapshot`, `narrative`, `coaching_snapshot` from `KnowledgeSnapshot`. No cross-session fields.

**Progress tracking (partial):**
- `LearningProgress` — exists but derives progress only from `CandidateProfileSnapshot.features` (dimensional knowledge score trends). Behavioral profile continuity across sessions is not tracked.
- `ProgressTracker` — computes `LearningProgress` from `SessionHistory[]`. Consumes `knowledge_snapshot.profile_snapshot` only.

### What Does Not Exist

The following do not exist and must be created or activated by EPIC-02:

- A persistent, candidate-scoped artifact that accumulates `CandidateProfileSnapshot` instances across sessions.
- A declared owner (node) for the cross-session accumulation write path.
- A persistence layer for cross-session data (no persistent storage exists for candidate-scoped artifacts beyond individual `SessionHistory` records).
- A defined update trigger: when, in the runtime lifecycle, is the longitudinal record updated?
- Behavioral profile trend tracking in `ProgressTracker` / `LearningProgress`.
- `LanguageCapability` activation — defined in V1.2 domain freeze as a reserved concept; not yet active.
- An explicit cross-session `ObservationStore` accumulation policy (Observations are currently session-scoped with no declared cross-session boundary).

### Structural Gap

The structural gap is not one of missing contracts. `CandidateProfileSnapshot` and `CandidateIdentity` already exist. The gap is the absence of:

1. A declared architectural artifact that represents the candidate's accumulated knowledge across sessions.
2. A declared node that owns the write path for that artifact.
3. A declared persistence model for that artifact.
4. A declared update trigger that fits within the existing runtime lifecycle without violating constitutional principles.

---

## 3. Target Architecture

### The Longitudinal Profile Artifact

The `LongitudinalProfile` is a persistent, candidate-scoped, immutable-at-instantiation artifact. It is not a session artifact. It is not a report. It is not a progress view. It is the authoritative cross-session accumulation record for a candidate.

At the architectural level, its role is analogous to `SessionHistory` but at a higher scope: where `SessionHistory` is the closed record of one session, `LongitudinalProfile` is the closed record of one candidate's journey across sessions.

The `LongitudinalProfile` is updated — meaning a new version is produced — after each session is closed. The prior version is superseded by the new one. The profile is immutable at any given version; update means replace-and-persist, not mutate.

### The Accumulation Unit

The accumulation unit is `CandidateProfileSnapshot`. Each completed session contributes exactly one `CandidateProfileSnapshot` to the `LongitudinalProfile`. The profile accumulates these snapshots in session-index order.

This is structurally consistent with `LearningProgress`, which already treats `CandidateProfileSnapshot` as its source unit. The difference: `LearningProgress` is derived on demand from `SessionHistory[]`. `LongitudinalProfile` is persisted and updated incrementally.

### The Cross-Session Identity Anchor

`CandidateIdentity` is the anchor. `LongitudinalProfile` belongs to exactly one `CandidateIdentity`. The relationship is:

```
CandidateIdentity (1)
    ↓ owns
LongitudinalProfile (1)
    ↓ accumulates
CandidateProfileSnapshot (n) — one per closed session
```

### Relationship to SessionHistory

`SessionHistory` is the source of truth for each session's contribution. The update path reads from the just-closed `SessionHistory` to extract the `CandidateProfileSnapshot` and relevant metadata, then produces a new `LongitudinalProfile` that appends the new snapshot.

`LongitudinalProfile` does not replace `SessionHistory`. It derives from it. If `LongitudinalProfile` is lost or corrupted, it can be reconstructed from the sequence of `SessionHistory` records (full reconstruction). This is the longitudinal analog of the Reconstruction Completeness principle.

### Relationship to Replay

`ReplaySession` currently operates on `KnowledgeSnapshot` from a single `SessionHistory`. In EPIC-03, `replay_node` will produce a `ReplayResult` from a closed `SessionHistory`. The `LongitudinalProfile` is not part of the core replay path — replay reconstructs session-scoped knowledge, not cross-session accumulation.

However, the Replay UI (EPIC-04) and Unified Report (EPIC-05) will need access to the candidate's longitudinal trend for the progress panel. The architectural question is whether that trend is sourced from `LongitudinalProfile` directly or recomputed from `SessionHistory[]` on demand. This is an open decision for the ADR phase.

### Relationship to LearningProgress

`LearningProgress` is a derived, never-persisted view. After EPIC-02:

- `LearningProgress` may continue to be derived on demand from `SessionHistory[]`, or
- `LearningProgress` may be derived from `LongitudinalProfile` instead of `SessionHistory[]`.

This is an open decision. The correct choice depends on performance (deriving from `LongitudinalProfile` avoids re-reading all `SessionHistory` records) and consistency (the `LongitudinalProfile` is already the accumulated view). The ADR must resolve this.

### Relationship to Future Analytics (V2)

`LongitudinalProfile` is designed to be the foundational artifact for V2 analytics capabilities: cohort benchmarking, organisation-level profiles, and goal tracking. These are explicitly out of scope for V1.3. The architectural decisions for EPIC-02 must not close off these paths, but they must not over-engineer for them either.

The V2 boundary is: `LongitudinalProfile` is candidate-scoped and single-candidate in V1.3. In V2, cohort-level aggregation may read from `LongitudinalProfile[]` across candidates. The V1.3 architecture must not make this impossible, but it does not implement it.

### Runtime Integration Point

The update of `LongitudinalProfile` must occur after session close — specifically, after `session_close_node` writes `SessionHistory` and after `report_node` produces `Report`. The candidate's session is fully closed before the longitudinal record is updated.

Constitutionally:
- The update is a closure operation (OP-01 Cascading Closure applies).
- The update involves no computation — no LLM calls, no `FeatureEngine`, no `NarrativeGenerator`.
- The update is write-once per session (idempotent re-execution must not create duplicate snapshot entries).

The update path is a new LangGraph node (P-04: LangGraph is the sole runtime orchestrator). The node reads the closed `SessionHistory` (specifically its `knowledge_snapshot.profile_snapshot`), reads the prior `LongitudinalProfile` (from persistence), produces a new `LongitudinalProfile` with the appended snapshot, and writes it back to persistence.

The node must be non-fatal: failure to update the `LongitudinalProfile` must not fail session close. The session is complete whether or not the longitudinal update succeeds. Observable failure (P-06) is mandatory.

### Target Graph Node Sequence

After EPIC-02, the graph close sequence extends to:

```
completion → evaluation_aggregate → session_close → report → longitudinal_update → END
```

`longitudinal_update` is the sole writer of `LongitudinalProfile`. It reads `InterviewState.session_history` (written by `session_close_node`) and `InterviewState.report` (written by `report_node`). It does not modify any prior state field.

---

## 4. Product Goals

EPIC-02 serves the following product goals from the Master Plan:

**P-02 — Cross-Session Profile Continuity.**  
The primary goal. A candidate who completes multiple sessions accumulates a longitudinal knowledge record that persists across session boundaries and enables behavioral trend tracking.

**P-05 — Unified Report (progress trend panel).**  
The Unified Report's progress trend panel (EPIC-05) will source its data from `LongitudinalProfile` (or `LearningProgress` derived from it). EPIC-02 is a blocking dependency for this panel.

**P-10 — Final Architecture Cleanup.**  
The `LanguageCapability` reserved concept defined in V1.2 must be activated. EPIC-02 is the intended activation point.

EPIC-02 does not directly serve: P-01 (closed by EPIC-01), P-03 (Replay — EPIC-03), P-04 (Replay UI — EPIC-04), P-06 (Explainability — EPIC-06), P-07/P-08/P-09 (production readiness — later epics).

---

## 5. Scope

### In Scope

- Definition of `LongitudinalProfile` domain contract: fields, types, validation invariants, ownership, lifecycle, schema versioning policy.
- Activation of `CandidateIdentity` as the cross-session accumulation anchor.
- Declaration of the sole writer node for `LongitudinalProfile` (new LangGraph node).
- Definition of the persistence boundary for `LongitudinalProfile` (which store, what schema, what versioning policy).
- Incremental update path: how a new `CandidateProfileSnapshot` is appended to an existing `LongitudinalProfile` on session completion.
- First-session path: how a `LongitudinalProfile` is created for a candidate with no prior sessions.
- Extension of `ProgressTracker` to derive behavioral profile trend data from `LongitudinalProfile`.
- Extension of `LearningProgress` to carry behavioral trend fields (or decision to replace its source from `SessionHistory[]` to `LongitudinalProfile` — ADR decision).
- Activation of `LanguageCapability` for cross-session accumulation.
- Explicit definition of the cross-session `ObservationStore` accumulation policy.
- Reconstruction guarantee: `LongitudinalProfile` must be fully reconstructable from the ordered sequence of `SessionHistory` records for a candidate.
- Architectural tests: no LLM calls in the longitudinal update path; `LongitudinalProfile` sole writer invariant.

### Out of Scope

Identical to EPIC-02-OVERVIEW.md §5. Cohort analytics, organisation profiles, `CandidateIdentity` federation, `GoalTrack`, comparative analysis. See §6 below.

---

## 6. Out of Scope

The following are explicitly not addressed by EPIC-02. Proposals to include them are scope creep.

- **Cohort benchmarking (`PeerBenchmark`).** Requires cohort data volume and multi-candidate aggregation. V2.
- **Organisation-level profiles (`OrganisationProfile`).** Requires multi-tenant architecture. V2.
- **Authentication or `CandidateIdentity` federation.** V1.3 `CandidateIdentity` is anonymous (uuid4, no external auth system). The V2 migration path must be documented in the ADR but not implemented.
- **`GoalTrack`.** V1.3 stretch goal at best; excluded from EPIC-02 scope.
- **Replay scoring trend.** Replay UI may show session-level scores; longitudinal trend in the replay view is a Unified Report concern (EPIC-05), not a replay concern (EPIC-03).
- **AI-generated longitudinal summaries.** Any LLM-generated summary of cross-session trends is computation — it violates P-01 (The Runtime Computes; Projection Never Computes) if performed at projection time. If it is ever in scope, it must run in the runtime cycle, not at report generation time. It is not in V1.3 scope.
- **Real-time longitudinal updates during a session.** The `LongitudinalProfile` is updated once per session at session close, not during the session.
- **Cross-session `ObservationStore` accumulation (storage).** The policy is declared by EPIC-02. The actual persistence of `ObservationStore` data across sessions (if required) is a separate infrastructure concern that may surface as a V2 item.

---

## 7. Ownership Model

### Constitutional Basis

P-02 (Single Ownership) is the governing principle. Every artifact has exactly one producer and exactly one writer.

### LongitudinalProfile Ownership

| Role | Owner | Notes |
|---|---|---|
| Producer | `LongitudinalProfileBuilder` | Assembles the new profile from prior profile + new snapshot. No computation — pure assembly (P-05). |
| Sole writer (runtime) | `longitudinal_update` node | New LangGraph node. Sole writer of `LongitudinalProfile` to persistence and to `InterviewState` (if a state field is added). |
| Persistence layer | To be decided by ADR | Which store, what schema. V1.3 scope: single-candidate, single-node persistence. |
| Readers (declared) | `ProgressTracker`, Unified Report layer (EPIC-05), Replay UI progress panel (EPIC-04/05). |

### CandidateProfileSnapshot Ownership (unchanged)

`CandidateProfileSnapshot` ownership is unchanged from V1.2. The sole producer remains `FeatureEngine` (via `CandidateProfileBuilder`) at session close. EPIC-02 only reads it — it does not change its production path.

### LearningProgress Ownership (potentially changed)

If the ADR decides `LearningProgress` should be derived from `LongitudinalProfile` rather than from `SessionHistory[]`, the reader set of `LongitudinalProfile` expands to include `LearningProgressBuilder`. The production path of `LearningProgress` does not change (sole creation path remains `LearningProgressBuilder`); only its input source changes. This is a reader-side change, not an ownership change.

### ObservationStore Accumulation Policy

The `ObservationStore` is session-scoped in V1.2. The question for EPIC-02 is whether `ObservationStore` contents should be accumulated across sessions in `LongitudinalProfile` (or a related artifact). The architectural position is: **Observations are session-scoped by nature** — they are raw signals from a specific session's questions and answers, not reusable across sessions. Cross-session insight derives from `CandidateProfileSnapshot.features` (the interpreted, dimensioned knowledge derived from observations), not from raw observations.

The declared policy is therefore: `ObservationStore` contents are **not** accumulated in `LongitudinalProfile`. The cross-session accumulation unit is `CandidateProfileSnapshot`, not `ObservationStore`. This policy must be confirmed or overridden by ADR if evidence suggests otherwise.

---

## 8. Runtime Lifecycle

The following describes the constitutional lifecycle of `LongitudinalProfile` within the platform runtime.

### Session Lifecycle (existing, unchanged)

```
Session start  → [reasoning cycles] → session_close_node → report_node
                                              ↓
                                   SessionHistory v2.0 written
                                   (candidate_identity_id, knowledge_snapshot,
                                    scoring_snapshot, scoring_narrative, ...)
```

### Longitudinal Update (new, EPIC-02)

```
report_node completes
    ↓
longitudinal_update node (new)
    ├── reads: InterviewState.session_history
    │          (specifically: knowledge_snapshot.profile_snapshot,
    │           candidate_identity_id, interview_index)
    ├── reads: prior LongitudinalProfile from persistence
    │          (by candidate_identity_id; None if first session)
    ├── produces: new LongitudinalProfile via LongitudinalProfileBuilder
    │              (prior profile + new CandidateProfileSnapshot appended)
    └── writes: new LongitudinalProfile to persistence
                (sole writer invariant — OP-04)
```

### Failure Semantics

The `longitudinal_update` node is **non-fatal**. If the longitudinal update fails (persistence unavailable, schema mismatch, builder validation failure), the node emits an observable error at WARNING or above (P-06) and allows the session lifecycle to complete. The session is not rolled back. The failed update is detectable from logs.

This means `LongitudinalProfile` may be temporarily out-of-sync with `SessionHistory`. The reconstruction guarantee (§3, Relationship to SessionHistory) ensures the profile can be rebuilt from `SessionHistory[]` if a failure leaves a gap.

### Idempotency

Re-executing the `longitudinal_update` node for the same session must not create a duplicate `CandidateProfileSnapshot` entry. The node must guard against duplicate entries by checking whether the `interview_index` of the new snapshot is already present in the persisted profile.

### First-Session Path

When `candidate_identity_id` has no prior `LongitudinalProfile`, the node creates a new profile containing exactly one `CandidateProfileSnapshot`. This is the first-session path. It does not differ architecturally from the subsequent-session path — `LongitudinalProfileBuilder` receives `prior_profile=None` and produces a profile with one entry.

---

## 9. Artifact Lifecycle

### LongitudinalProfile

| Phase | State | Notes |
|---|---|---|
| Before first session | Does not exist | No `LongitudinalProfile` record for this `candidate_identity_id` |
| After first session | Created | One `CandidateProfileSnapshot` entry; `session_count = 1` |
| After each subsequent session | Replaced (immutable update) | New `LongitudinalProfile` instance produced; prior version superseded in persistence |
| At report render time | Read-only | Read by `ProgressTracker` and Unified Report layer; never modified |
| At replay time | Read-only (if accessed) | Never modified by replay path |

### Versioning

`LongitudinalProfile` must carry a `schema_version` field (analogous to `SessionHistory.schema_version = "2.0"`). The initial version is `"1.0"`. The schema versioning policy — how version increments are triggered and how older versions are migrated — must be declared in the first `LongitudinalProfile` ADR before implementation begins.

The ADR-033 review trigger is relevant here: "EPIC-V13-02 (`LongitudinalProfile`) requires scoring data from `SessionHistory.scoring_snapshot` — confirm `ScoringSnapshot` field set is sufficient." This must be evaluated during the Architecture Review phase.

### Reconstruction Guarantee

If the persistence layer for `LongitudinalProfile` is lost or corrupted, the profile can be reconstructed by processing each `SessionHistory` in `interview_index` order for the given `candidate_identity_id`. This reconstruction is deterministic and produces the same `LongitudinalProfile` that the normal update path would have produced. This guarantee is constitutional (P-08: Reconstruction Completeness). It must be verified by an architectural test.

### Immutability

Each `LongitudinalProfile` instance is `frozen=True`. "Update" means: produce a new instance with the new snapshot appended, persist it, discard the prior instance. No in-place mutation of any `LongitudinalProfile` field is permitted at any point.

---

## 10. Dependencies

### Hard Dependencies (blocking EPIC-02)

| Dependency | Status | Notes |
|---|---|---|
| EPIC-01 (Scoring Pipeline Migration) | **Closed** | `Report` is sole scoring artifact; `InterviewEvaluation` deleted; `SessionHistory` v2.0 active |
| `CandidateProfileSnapshot` contract | **Frozen** (V1.2) | Already the accumulation unit; no changes required |
| `CandidateIdentity` contract (ADR-016A) | **Frozen** (V1.2) | Already the ownership anchor; activation (as cross-session anchor) is EPIC-02 scope |
| `SessionHistory` v2.0 contract (ADR-033) | **Frozen** (EPIC-01) | Source of truth for each session's contribution |

### Soft Dependencies (informing design)

| Dependency | Status | Notes |
|---|---|---|
| `LearningProgress` / `LearningProgressBuilder` | Active (V1.2) | May change input source from `SessionHistory[]` to `LongitudinalProfile` — ADR decision |
| `ProgressTracker` | Active (V1.2) | Extended to consume behavioral trends from `LongitudinalProfile` |
| `LanguageCapability` | Reserved (V1.2 domain freeze) | Activated by EPIC-02 for cross-session accumulation |

### Downstream Dependents (blocked until EPIC-02 closes)

| Epic | Dependency |
|---|---|
| EPIC-V13-05 (Unified Report) | Progress trend panel requires `LongitudinalProfile` or `LearningProgress` sourced from it |
| EPIC-V13-06 (Explainability) | May reference behavioral profile features as evidence anchors |
| EPIC-V13-09 (Performance Baseline) | Must profile longitudinal update cost per session |

EPIC-V13-03 (Replay Engine) and EPIC-V13-04 (Replay UI) are **not** blocked by EPIC-02 — replay operates on session-scoped data from `SessionHistory`. These epics may proceed in parallel with EPIC-02.

---

## 11. Risks

| Risk | Likelihood | Impact | Architectural Concern |
|---|---|---|---|
| Ownership decision for `longitudinal_update` node is contentious — where in the graph does it fit? | Medium | High | The update must follow `report_node` (reads from closed `SessionHistory`), must be non-fatal, and must be a LangGraph node. The constitutional constraints are clear; the implementation decision may reveal edge cases. |
| `LongitudinalProfile` schema versioning not established before first implementation, causing costly migration later | Medium | High | The schema versioning policy must be frozen in the first ADR. This is a constitutional pre-condition for persistence. |
| `CandidateIdentity` anonymous model (uuid4 only) is incompatible with V2 auth requirements, requiring a breaking change | Low | High | The V1.3 design must treat `candidate_identity_id` as opaque and stable, with no assumption of external auth backing. The V2 migration path must be documented in the ADR. |
| Behavioral trend computation in `ProgressTracker` requires data not available in `CandidateProfileSnapshot` | Low | Medium | `CandidateProfileSnapshot.features` carries the full `ProfileFeature` set including `semantic_category` and `confidence`. This is the same data source `LearningProgress` already uses. Risk is low but must be validated during Architecture Review. |
| `LongitudinalProfile` reconstruction from `SessionHistory[]` is not idempotent if snapshot ordering is not strict | Low | Medium | `interview_index` provides strict ordering. The reconstruction algorithm must sort by `interview_index` ascending. Test coverage required. |
| `LongitudinalProfile` persistence failure silently skips sessions, causing profile/history divergence | Medium | Medium | Non-fatal semantics require observable failure (P-06). A gap detection mechanism (comparing `LongitudinalProfile.session_count` with count of `SessionHistory` records for the candidate) must be available for operator diagnosis. |
| `LanguageCapability` activation reveals design gaps in `CandidateProfileSnapshot` feature representation | Low | Low | `LanguageCapability` is a reserved concept; its activation may require extending `ProfileFeature` or adding a dedicated field. Risk is contained — any change is an additive contract extension, not a breaking one. |

---

## 12. Success Criteria

EPIC-02 is architecturally successful when all of the following are verified:

1. **`LongitudinalProfile` domain contract is frozen** (`frozen=True`, `extra=forbid`, declared sole writer, schema versioning policy declared).
2. **After every session completion, `LongitudinalProfile` is updated** — the `longitudinal_update` node runs, produces a new profile version, and persists it.
3. **`CandidateIdentity` is the active cross-session anchor** — `LongitudinalProfile` is queryable by `candidate_identity_id`.
4. **Single writer invariant holds** — no component other than `longitudinal_update` node writes `LongitudinalProfile` to persistence.
5. **Non-fatal semantics verified** — session close completes successfully even when `longitudinal_update` fails; failure is observable at WARNING or above.
6. **Idempotency verified** — re-executing `longitudinal_update` for the same session does not create a duplicate snapshot entry.
7. **First-session path works** — a candidate with no prior profile receives a new `LongitudinalProfile` with one `CandidateProfileSnapshot` after their first session.
8. **Reconstruction guarantee holds** — `LongitudinalProfile` for any candidate is reconstructable from their ordered `SessionHistory[]`; verified by architectural test.
9. **No LLM calls in the longitudinal update path** — enforced by architectural test (analogous to I-11 for replay).
10. **`ProgressTracker` extended** — `LearningProgress` reflects behavioral feature trends, not only dimensional score trends.
11. **`LanguageCapability` activated** — cross-session language feature accumulation is functional.
12. **Schema versioning policy declared and implemented** — `LongitudinalProfile.schema_version = "1.0"` at initial implementation; policy for version increments documented.
13. **All new `InterviewState` fields have declared sole writers** — if a state field for `LongitudinalProfile` reference is added, its sole writer is declared at the point of addition.
14. **Full regression suite passes** — all V1.2 and EPIC-01 acceptance criteria continue to pass.
15. **FR-02 (Final Review) produces Closed outcome**.

---

## 13. Appendix A — Affected Production Modules

This appendix identifies the production modules expected to be affected by EPIC-02. It is informational — not a contract, not an implementation plan.

| Module | Expected Impact |
|---|---|
| `domain/contracts/longitudinal/` (new) | New `LongitudinalProfile` contract and builder |
| `domain/contracts/identity/candidate_identity.py` | Likely read-only; no change expected to the contract itself |
| `domain/contracts/knowledge_snapshot/candidate_profile_snapshot.py` | Read-only from EPIC-02 perspective; no contract changes expected |
| `domain/contracts/progress/learning_progress.py` | Potentially extended with behavioral trend fields; or input source changes |
| `domain/contracts/progress/learning_progress_builder.py` | Input source may change from `SessionHistory[]` to `LongitudinalProfile` — ADR decision |
| `domain/contracts/interview_state/base.py` | New field(s) for longitudinal update node outputs, if required; sole writer declared |
| `app/graph/nodes/` (new node) | `longitudinal_update_node.py` — new LangGraph node |
| `app/graph/` (graph definition) | Graph edge: `report_node → longitudinal_update_node → END` |
| `services/progress/` | `ProgressTracker` extended to source from `LongitudinalProfile` |
| `infrastructure/` (persistence) | New persistence adapter for `LongitudinalProfile`; scope and location decided by ADR |
| `domain/contracts/feature/language_capability.py` (new or extended) | `LanguageCapability` activation |

Modules **not** affected by EPIC-02:
- `app/graph/nodes/session_close_node.py` — session close is unchanged; `longitudinal_update` is additive.
- `app/graph/nodes/report_node.py` — report generation is unchanged.
- `domain/contracts/report/` — `Report` contract is unchanged.
- `domain/contracts/session_history/` — `SessionHistory` contract is unchanged (EPIC-01 closed this).
- `domain/contracts/replay/` — replay contracts are EPIC-03 scope.
- UI layer — UI changes are EPIC-04/05/07 scope.

---

## 14. Appendix B — Dependency Graph

```
                          CandidateIdentity (anchor)
                                │
                          owns (1:1)
                                │
                        LongitudinalProfile
                                │
                    accumulates (1:n, ordered by interview_index)
                                │
                    CandidateProfileSnapshot
                                │
                    derived from (1:1 per session)
                                │
                    SessionHistory v2.0
                    ┌───────────┴───────────┐
             (reads)                    (reads)
                │                           │
          knowledge_snapshot         scoring_snapshot
                │                   scoring_narrative
        profile_snapshot
```

**Cross-epic dependency flow:**

```
EPIC-01 [CLOSED]
    └── SessionHistory v2.0 ─── frozen ──→ EPIC-02 reads
    └── Report v2.0 ─────────── frozen ──→ EPIC-05 (Unified Report) reads

EPIC-02 [PLANNING]
    └── LongitudinalProfile ─── produces ─→ EPIC-05 (progress trend panel)
    └── LongitudinalProfile ─── produces ─→ EPIC-04 (replay progress panel, if in scope)

EPIC-03 [PENDING] — parallel with EPIC-02
    └── ReplaySession / replay_node ─── reads SessionHistory ──→ no dependency on EPIC-02

EPIC-05 [PENDING] — blocked until EPIC-02 AND EPIC-03
    └── Unified Report: progress trend panel ←── LongitudinalProfile (EPIC-02)
    └── Unified Report: replay link ←─────────── ReplaySession (EPIC-03)
```

**Constitutional hierarchy applicable to EPIC-02:**

```
Architecture Constitution (ARC-01)
    └── P-01 (Runtime Computes; Projection Never Computes)
           → longitudinal_update: no LLM calls, no computation
    └── P-02 (Single Ownership)
           → LongitudinalProfile: one node writes, one builder constructs
    └── P-03 (Immutable Domain Contracts)
           → LongitudinalProfile: frozen=True; update = replace, not mutate
    └── P-04 (LangGraph Is Sole Orchestrator)
           → longitudinal_update is a LangGraph node; not a service chain
    └── P-05 (Builders Assemble; Engines Compute)
           → LongitudinalProfileBuilder: pure assembly; no derivation logic
    └── P-06 (Fail Fast Over Silent Fallback)
           → non-fatal failure is observable; no silent skip
    └── P-08 (Reconstruction Completeness)
           → profile reconstructable from SessionHistory[]; all fields explicit
```

---

*This document is the architecture planning artifact for EPIC-02. It does not freeze decisions. All open questions identified in §3, §7, §9, and §11 must be resolved by ADR before implementation begins. The Architecture Freeze gate applies: implementation cannot begin until all decisions are frozen in accepted ADRs.*

*Revision 2026-07-14: Initial draft. Produced during EPIC-02 Architecture Planning phase following FR-01 (EPIC-01 closure) and EPIC-02 preparation.*
