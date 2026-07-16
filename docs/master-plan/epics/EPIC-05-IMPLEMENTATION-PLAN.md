# EPIC-05 — Unified Report: Implementation Plan

**Status:** ACCEPTED  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-05  
**Authority:** EPIC-05-ARCHITECTURE-FREEZE.md (APPROVED, commit `3fecfe5`)  
**Governing ADRs:** ADR-003, ADR-025, ADR-033, ADR-034, ADR-037  
**Regression baseline (plan open):** 6637 passing tests, 0 failures  
**Precondition:** Architecture Freeze APPROVED. Implementation Dependency Validation applied (§2). No production implementation begins without this plan accepted.

---

## 1. Implementation Overview

### 1.1 Implementation Goals

1. Extend `FinalReportDTO` with frozen additives `study_recommendations` and `session_id`; map both in `from_report` exclusively from `Report`.
2. Close the study-recommendations production gap (PC-05 / F-W-03): production HTML path uses DTO only — no domain `Report` getattr fallback.
3. Enforce report→replay sole-source identity (I-C25-01 / F-W-01): `Report.session_id` only when report present.
4. Implement ProgressTrendPanel (C-23) from `LearningProgress` with UI gate `session_count >= 3` (OI-DM-01 / F-W-02 / F-W-05).
5. Wire progress into the report presentation surface without embedding progress fields into `FinalReportDTO`.
6. Enforce dual-read / sole-factory architectural tests; clean stale `from_components` tooling (F-W-06).
7. Leave the regression suite green (≥ 6637 passing, zero failures) at every phase boundary; update baseline after each phase.

### 1.2 Implementation Constraints (Frozen)

From EPIC-05-ARCHITECTURE-FREEZE.md §10 — constitutionally binding:

1. `Report` → `FinalReportDTO.from_report` is the sole session-report body path.
2. No second `FinalReportDTO` factory.
3. Progress never embedded into `FinalReportDTO`.
4. Progress UI gate: `session_count >= 3`; insufficient-data otherwise; no extrapolation.
5. Report→replay uses `Report.session_id` exclusively when report present.
6. Explainability out of scope (EPIC-06).
7. No new ADR; no domain ownership changes to `Report` / `LongitudinalProfile` / `ReplaySession` writers.
8. Zero Known Failing Tests on every commit.
9. Frozen planning docs require Freeze Integrity Check if modified.

### 1.3 Frozen Architecture Reminder

Three non-overlapping planes (Data Model §1):

| Plane | Source | Carrier | Work owned by |
|---|---|---|---|
| A — Session report body | `Report` | `FinalReportDTO` | Phases 1–2 |
| C — Replay handoff | `Report.session_id` | trigger string | Phase 3 |
| B — Progress trend | `LongitudinalProfile` → `LearningProgress` | ProgressTrendPanel | Phases 4–5 |

### 1.4 Out of Scope

- Explainability anchors / evidence UX (EPIC-06)
- Scoring logic / `ReportBuilder` / `report_node` ownership changes
- `LongitudinalProfile` schema changes / LP-LP-03 amendment
- `ReplaySession` / EPIC-04 Replay UI internals (handoff only)
- Coaching actions / narrative five-sections as new EPIC-05 panels
- PDF/email distribution channels (V2)

---

## 2. Implementation Dependency Validation

All commit boundaries validated for self-containment per Playbook §2.

| Phase | Depends On | Independently Testable |
|---|---|---|
| Phase 1 — DTO additives + `from_report` mapping | Nothing new (uses frozen `Report`) | Yes — unit tests on `from_report` field presence / mapping |
| Phase 2 — VM / study-recommendations production path | Phase 1 (`study_recommendations` on DTO) | Yes — VM/section tests with DTO fixture only |
| Phase 3 — Replay `session_id` sole-source | Phase 1 (`session_id` on DTO) optional but preferred | Yes — resolver unit tests; does not require Phase 2 |
| Phase 4 — ProgressTrendPanel | Nothing from Planes A/C code; uses EPIC-02 `LearningProgress` | Yes — panel unit tests with `LearningProgress` fixtures |
| Phase 5 — Progress bind into report surface | Phases 1–4 (DTO identity + panel exists) | Yes — integration: report render includes progress states |
| Phase 6 — Architectural tests + tooling cleanup | Phases 1–5 | Yes — arch tests + script fix; suite green |

**No circular dependencies.** Phase 3 does not depend on Phase 2. Phase 4 does not depend on Phases 1–3 for its unit gate (integration in Phase 5).

---

## 3. Macro Phase Decomposition

```
Macro Phase A — Sole-Source Report Body + Replay Handoff
  Phase 1: FinalReportDTO additives (study_recommendations, session_id)
  Phase 2: Study recommendations production path (DTO-only VM/render)
  Phase 3: Report→replay session_id sole-source (I-C25-01)
        ↓
Architecture Checkpoint A
        ↓
Macro Phase B — Progress Trend + Verification
  Phase 4: ProgressTrendPanel (C-23) + sufficiency gate
  Phase 5: Progress bind into report presentation surface
  Phase 6: Architectural enforcement tests + tooling cleanup (F-W-06)
        ↓
Architecture Checkpoint B
        ↓
CAR (Architecture Traceability)
        ↓
Regression Certification
        ↓
Documentation Certification
        ↓
Final Review (FR / FAR)
        ↓
EPIC Close
```

---

## 4. Phase Breakdown

---

### Phase 1 — FinalReportDTO Additives

**Macro Phase:** A  
**Objective:** Add frozen `FinalReportDTO` fields `study_recommendations` and `session_id`; map them in `from_report` from `Report` only.

**Scope:**
- `app/ui/dto/final_report_dto.py` — add `StudyRecommendationDTO`; add fields; extend `from_report`
- `tests/ui/mappers/test_final_report_dto.py` (and/or adjacent DTO tests) — field coverage

**Forbidden:**
- ViewModel / section renderer changes
- Replay resolver changes
- Progress / Longitudinal code
- Domain contracts / `ReportBuilder` / graph nodes
- Explainability fields

**Deliverables:**
- `StudyRecommendationDTO` with frozen fields (Data Model §2.4)
- `FinalReportDTO.study_recommendations: List[StudyRecommendationDTO]`
- `FinalReportDTO.session_id: str`
- `from_report` maps recommendations from `report.coaching_snapshot.collection.recommendations`
- `from_report` maps `session_id` from `report.session_id`
- Unit tests: mapping present; empty recommendations when domain empty; `session_id` equals `report.session_id`; still no `from_components`

**Completion gate:**
- All Phase 1 unit tests pass
- Full suite ≥ 6637 (updated baseline after this phase), 0 failures
- DM-FR-01…04 respected

**Commit:** one atomic — `feat(unified-report): add study_recommendations and session_id to FinalReportDTO`

---

### Phase 2 — Study Recommendations Production Path

**Macro Phase:** A  
**Objective:** Ensure production report HTML renders study recommendations from `FinalReportDTO` only (closes F-W-03).

**Scope:**
- `app/ui/views/report/report_view_model_builder.py` — DTO-first `study_recommendations` (no domain fallback on production path)
- `app/ui/views/report/sections/study_recommendations_section.py` — verify consumption
- Related unit tests

**Forbidden:**
- `FinalReportDTO` field set changes (already done)
- Replay resolver
- Progress panel
- Domain layer

**Deliverables:**
- Production VM path reads `study_recommendations` from DTO
- Domain `coaching_snapshot` getattr fallback removed from production path (or unreachable when DTO is input)
- Unit/section tests: non-empty DTO recommendations render; empty list renders empty/neutral state

**Completion gate:**
- Study recommendations visible when DTO carries them
- Suite green at updated baseline

**Commit:** one atomic — `fix(unified-report): render study recommendations from FinalReportDTO only`

---

### Phase 3 — Replay SessionId Sole-Source

**Macro Phase:** A  
**Objective:** Enforce I-C25-01 / F-W-01 — report→replay uses `Report.session_id` only when report present.

**Scope:**
- `app/ui/bindings/handlers/replay_layout_coordinator.py` — `resolve_session_id_from_report`
- Unit tests for resolver

**Forbidden:**
- Replay UI panels / EPIC-04 internals beyond resolver
- DTO mapping (Phase 1)
- Progress

**Deliverables:**
- When `state.report is not None`: `session_id = state.report.session_id` exclusively
- When `state.report is None`: fail-fast (reject replay-from-report)
- No `SessionHistory.session_id` / `interview_id` preference when report present
- Unit tests covering report-present, report-absent, and non-use of `session_history`

**Completion gate:**
- Resolver tests pass
- Suite green at updated baseline

**Commit:** one atomic — `fix(unified-report): resolve replay session_id from Report only`

---

### Architecture Checkpoint A

**Trigger:** Completion of Phase 3 (Macro Phase A complete).  
**Review scope:** Phases 1–3 vs EPIC-05-ARCHITECTURE-FREEZE.md and Domain Contracts / Data Model Planes A+C.  
**Classification:** PASS / WARNING / BLOCKER per dimension.  
**Approval criteria:**
- `from_report` maps `study_recommendations` and `session_id`
- Production study-recommendations path is DTO-only
- Replay resolver complies with I-C25-01
- No progress fields on `FinalReportDTO`
- No explainability scope creep
- Regression suite green
- No dual factory

**Outcome:** **AUTHORIZED** (Macro Phase B may begin) or **BLOCKED**.

---

### Phase 4 — ProgressTrendPanel

**Macro Phase:** B  
**Precondition:** Architecture Checkpoint A **AUTHORIZED**.  
**Objective:** Implement C-23 ProgressTrendPanel consuming `LearningProgress` with UI gate `session_count >= 3` (OI-DM-01 / F-W-02).

**Scope:**
- New progress panel module under `app/ui/views/report/` (or dedicated progress package under report views)
- Unit tests with LearningProgress fixtures (`session_count` 0, 1, 2, 3+)

**Forbidden:**
- Embedding progress into `FinalReportDTO`
- Reading `SessionHistory[]` for progress
- Amending LP-LP-03 / Longitudinal domain contracts
- Using `has_sufficient_data` alone as UI gate
- Layout chrome integration (Phase 5)

**Deliverables:**
- ProgressTrendPanel render function/component
- `session_count < 3` → explicit insufficient-data UI; no trend extrapolation
- `session_count >= 3` → trend from `behavioral_trend` / allowed entry fields (Data Model §2.6)
- Unit tests for both states

**Completion gate:**
- Panel unit tests pass
- Suite green at updated baseline

**Commit:** one atomic — `feat(unified-report): add ProgressTrendPanel with session_count>=3 gate`

---

### Phase 5 — Progress Bind into Report Surface

**Macro Phase:** B  
**Objective:** Bind persisted `LongitudinalProfile` → `LearningProgress` at report UI time and compose ProgressTrendPanel into report presentation (F-W-05).

**Scope:**
- Report render/bind path (`UIResponseBuilder` and/or report facade / Gradio report section as required)
- `ProgressTracker` / repository read using `Report.candidate_identity_id`
- `report_renderer.py` composition order update
- Integration tests

**Forbidden:**
- Assuming longitudinal data on `InterviewState` at `report_node` time
- Writing Longitudinal / Report domain artifacts from UI
- DTO progress fields

**Deliverables:**
- Bind path loads `LearningProgress` from persisted profile (or empty progress when absent)
- Report HTML includes ProgressTrendPanel output
- Integration tests: insufficient-data and trend-visible fixtures
- No `SessionHistory` dual-read introduced

**Completion gate:**
- Integration tests pass
- Suite green at updated baseline

**Commit:** one atomic — `feat(unified-report): bind LearningProgress into report presentation`

---

### Phase 6 — Architectural Enforcement + Tooling Cleanup

**Macro Phase:** B  
**Objective:** Enforce frozen invariants with architectural tests; resolve F-W-06.

**Scope:**
- Architectural tests under `tests/` (report presentation dual-read ban; sole factory; replay resolver source; progress gate; no progress on DTO)
- `scripts/audit_report_quality.py` — remove/replace `from_components` usage

**Forbidden:**
- New product features
- Domain contract changes
- Explainability

**Deliverables:**
- Arch tests asserting:
  - no `SessionHistory` import/use on report presentation path for Report-owned fields
  - `from_components` absent
  - resolver uses `Report.session_id` when report present
  - ProgressTrendPanel gate `session_count >= 3`
  - `FinalReportDTO` has no progress fields
- Tooling script uses `from_report` only
- Suite green at updated baseline

**Completion gate:**
- All arch tests pass
- Tooling no longer references `from_components`
- Suite green

**Commit:** one atomic — `test(unified-report): enforce sole-source invariants and fix audit tooling`

---

### Architecture Checkpoint B

**Trigger:** Completion of Phase 6 (Macro Phase B complete).  
**Review scope:** Phases 4–6 + whole epic vs Freeze / Domain Contracts / Data Model (all planes).  
**Approval criteria:**
- Progress plane ownership intact
- UI gate `>= 3` enforced
- Architectural tests present and green
- F-W-06 closed
- Traceability R-01…R-09 implementation coverage complete
- Regression suite green

**Outcome:** **AUTHORIZED** (advance to CAR) or **BLOCKED**.

---

## 5. Commit Strategy

| Commit | Phase | Suggested message | Regression gate |
|---|---|---|---|
| C1 | Phase 1 | `feat(unified-report): add study_recommendations and session_id to FinalReportDTO` | ≥ baseline, 0 fail |
| C2 | Phase 2 | `fix(unified-report): render study recommendations from FinalReportDTO only` | ≥ updated baseline |
| C3 | Phase 3 | `fix(unified-report): resolve replay session_id from Report only` | ≥ updated baseline |
| — | Checkpoint A | review only; no commit | — |
| C4 | Phase 4 | `feat(unified-report): add ProgressTrendPanel with session_count>=3 gate` | ≥ updated baseline |
| C5 | Phase 5 | `feat(unified-report): bind LearningProgress into report presentation` | ≥ updated baseline |
| C6 | Phase 6 | `test(unified-report): enforce sole-source invariants and fix audit tooling` | ≥ updated baseline |
| — | Checkpoint B | review only; no commit | — |

**Rules:**
- Exactly one atomic commit per implementation phase
- Regression suite must be green before each commit is accepted
- No mixed feature + unrelated refactor
- No commit anticipates later-phase artefacts

**Total production commits:** 6  
**Total Architecture Checkpoints:** 2

---

## 6. Architecture Checkpoints (Summary)

| Checkpoint | After | Review scope | Continue when |
|---|---|---|---|
| A | Phase 3 | Planes A+C; DTO; study recs; replay resolver | AUTHORIZED |
| B | Phase 6 | Plane B + arch tests + full freeze conformance | AUTHORIZED → CAR |

Each checkpoint is review-only (no code). Findings: PASS / WARNING / BLOCKER. BLOCKER prevents next macro phase / CAR.

---

## 7. Regression Protocol

- **Baseline declared (plan open):** **6637** passing tests, **0** failures (verified 2026-07-16; matches EPIC-04 close-out).
- Every completed phase updates the baseline to the new passing count for the next phase prompt.
- No phase may start with a stale baseline in its implementation prompt (Playbook §10).
- No save-token / phase completion with any failing test (Zero Known Failing Tests).
- New tests introduced in a phase must pass in the same commit that lands them.

---

## 8. Implementation Risks → Owner Phase

Warnings from Architecture Freeze §7 mapped to resolving phases:

| Finding | Disposition at Freeze | Owner phase |
|---|---|---|
| F-W-01 Replay session_id dual-read | Contract-resolved; enforce in impl | **Phase 3** |
| F-W-02 Progress panel absent | Deferred to implementation | **Phase 4** (+ **Phase 5** bind) |
| F-W-03 Study recommendations empty on DTO | Contract-resolved; enforce in impl | **Phase 1** + **Phase 2** |
| F-W-04 Explainability fields | Intentionally accepted (EPIC-06) | **None** (out of scope) |
| F-W-05 Longitudinal after report_node | Model-resolved; enforce bind timing | **Phase 5** |
| F-W-06 Stale `from_components` tooling | Deferred to implementation | **Phase 6** |

Every WARNING has an owner phase or intentional acceptance.

---

## 9. Final Close-Out Workflow

```
Implementation (Phases 1–6)
        ↓
Architecture Checkpoint A (after Phase 3)
        ↓
Architecture Checkpoint B (after Phase 6)
        ↓
CAR — Construction Architecture Review
  (mandatory Architecture Traceability Review — Category B)
        ↓
Regression Certification
  (full suite green; baseline certified)
        ↓
Documentation Certification
  (Master Plan / INDEX / Architecture Guide / Assumptions / status markers)
        ↓
Final Review (FR / FAR)
  (Closed | Blocked)
        ↓
EPIC Close
```

---

## 10. Allowed / Forbidden Scope Matrix

| Area | P1 | P2 | P3 | P4 | P5 | P6 |
|---|---|---|---|---|---|---|
| `final_report_dto.py` | ALLOWED | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden |
| Report VM / study section | Forbidden | ALLOWED | Forbidden | Forbidden | Forbidden | Forbidden |
| `resolve_session_id_from_report` | Forbidden | Forbidden | ALLOWED | Forbidden | Forbidden | Forbidden |
| ProgressTrendPanel module | Forbidden | Forbidden | Forbidden | ALLOWED | Forbidden | Forbidden |
| Report bind / renderer compose / ProgressTracker UI wiring | Forbidden | Forbidden | Forbidden | Forbidden | ALLOWED | Forbidden |
| Arch tests + `scripts/audit_report_quality.py` | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | ALLOWED |
| `domain/contracts/**` writers / ReportBuilder / report_node | Forbidden all phases |
| Explainability / EPIC-06 UI | Forbidden all phases |
| `ReplaySession` / replay panels internals | Forbidden all phases (resolver only in P3) |

---

## 11. Definition of Done — Implementation Plan (§8.6)

| Criterion | Status |
|---|---|
| Commit boundary table complete | YES — §5 |
| Implementation Dependency Validation applied | YES — §2 |
| Every commit independently implementable + testable | YES — §2 |
| No circular dependencies | YES |
| Regression baseline declared | YES — 6637 |
| Phase breakdown matches Architecture Freeze scope | YES |
| Architecture Checkpoints defined | YES — §3, §6 |
| Warnings mapped to owner phases | YES — §8 |

**Implementation Plan: ACCEPTED.**

Exit Criterion #10 (Playbook) is now satisfiable. Production implementation of Phase 1 may begin in a **new Cursor chat** (Playbook §10 one-chat-per-macro-phase; Macro Phase A starts here).

---

## 12. First Implementation Task

**Macro Phase A / Phase 1** — extend `FinalReportDTO` with `study_recommendations` and `session_id`; map in `from_report`; unit tests; atomic commit; regression ≥ 6637.

---

*This Implementation Plan is the accepted commit-boundary contract for EPIC-V13-05. Implementation must not deviate from frozen architecture without Stopping Rule / Freeze Integrity Check.*
