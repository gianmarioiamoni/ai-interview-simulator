# EPIC-06 — Explainability: Implementation Plan

**Status:** IMPLEMENTATION COMPLETE — FR **PASS WITH OBSERVATIONS** (0 P0/P1); Epic Close AUTHORIZED — 2026-07-22  
**Date:** 2026-07-16  
**Epic ID:** EPIC-V13-06  
**Playbook Category:** Category B — Major Architectural Epic  
**Phase:** Implementation Plan (Playbook §8.6) — close-out markers updated at CAR/FR recovery  
**Precondition:** `EPIC-06-ARCHITECTURE-FREEZE.md` APPROVED; ADR STEP SKIPPED; working tree clean  
**Authority:** Implementation sequence, commit boundaries, tests, OF-01 presentation-mechanism selection (implementation-only). No architecture changes. No ADR. No production code in this document step.

---

## Save Token (precondition)

| Check | Result |
|---|---|
| Working tree | Clean |
| HEAD | `8ed96ab3160630379c9017d250410d6179294596` (`8ed96ab` — docs(epic-06): declare architecture freeze) |
| Stash | Not created |

---

## 0. Governing Constraints (non-negotiable)

| Constraint | Rule |
|---|---|
| Zero Known Failing Tests | Every commit leaves suite green; no commit with known failing tests |
| Green suite after every commit | Full relevant test target green before commit lands |
| No compatibility bridges | Unless an explicit in-phase exception is recorded (default: none) |
| Single-writer | No new Report / Narrative / CoachingEngine writers; DTO factory sole presentation writer |
| Report-only presentation | Explainability from `FinalReportDTO` only; no SessionHistory / Observation-store reads |
| Fail-fast | Missing required explainability fields → fail; silent omit forbidden (EC-V-01) |
| Frozen architecture | ADR-023 + ADR-033 binding; Domain Contracts + Data Model field tables immutable for this epic |

---

## 1. OF-01 Resolution (Implementation Concern Only)

### 1.1 Decision

**Presentation mechanism (OF-01):** Inline evidence surfacing inside existing Unified Report sections.

| Surface | Mechanism |
|---|---|
| Narrative insights (C-20) | Under each insight, render candidate-visible evidence from `NarrativeInsightDTO.source_feature_id` + `is_traceable` (e.g. feature identity labels). No modal, no separate explainability route, no Observation payload fetch |
| Coaching actions | Render each `CoachingActionDTO` with its origin fields (`origin_feature_type`, `origin_supporting_observation_types`, `origin_objective_description`) inline on the coaching actions surface composed by existing report hosts/renderer. Objective-level optional enrichment (OF-04) may mirror observation types but must not replace action-level origin |
| Export (C-26) | Same fields, same sole `from_report` DTO — markdown/HTML parity |

### 1.2 Classification

| Attribute | Value |
|---|---|
| Decision class | **Presentation-layer design / implementation concern** |
| Architecture change? | **No** |
| ADR required? | **No** |
| Sequence placement | **Phase P0 (locked before UI commits)**; executed in Macro Phase M3 |

### 1.3 Bound

Mechanism may adjust layout/copy/CSS within frozen DTO contracts only. It must not reopen evidence target, origin model, fail-fast class, or persistence ownership.

**OF-01 status after this plan:** **RESOLVED** (implementation-plan level).

---

## 2. Incremental Implementation Phases

### Macro Phase M0 — Plan lock & fixture baseline

| Item | Detail |
|---|---|
| Goal | Confirm freeze inputs; inventory existing report DTO/UI/export tests; establish fixture Reports with insights + actions + objectives |
| Code | None (docs already frozen) or test-fixture-only if missing fixtures |
| Exit | Fixture set identified; OF-01 recorded; Stopping Rule SR-M0 green |
| Architecture Checkpoint | **ACP-M0** — confirm no architecture reopen; OF-01 remains presentation-only |

### Macro Phase M1 — DTO migrations (critical path start)

| Item | Detail |
|---|---|
| Goal | Additive presentation types and `from_report` mapping per Data Model §2–§5 |
| Deliverables | `FeatureIdentity` DTO shape; extend `NarrativeInsightDTO`; add `CoachingActionDTO`; add `FinalReportDTO.coaching_actions`; map origin join; projection completeness gate (PC-E05) |
| Forbidden | Domain schema changes; ReportBuilder changes; Observation/SessionHistory reads; ADR-025 FK introduction |
| Exit | Unit/contract tests for mapping + fail-fast; suite green |
| Architecture Checkpoint | **ACP-M1** — sole factory; fail-fast; no dual-read; field tables honored |

### Macro Phase M2 — Architectural & integration tests (DTO plane)

| Item | Detail |
|---|---|
| Goal | Lock invariants before UI (R-03, R-04, R-06) |
| Deliverables | Architectural tests (no SessionHistory/Observation/LLM on explainability path; no silent omit); integration tests `Report` → `from_report` → DTO completeness |
| Exit | All M2 tests green; suite green |
| Architecture Checkpoint | **ACP-M2** — EC-V-01 / EC-N-01 / EC-C-01 enforced on DTO plane |

### Macro Phase M3 — Presentation-layer implementation (OF-01)

| Item | Detail |
|---|---|
| Goal | Candidate-visible inline evidence on C-20 + coaching action surface + export parity |
| Deliverables | View-model/renderer/section updates consuming DTO only; export markdown/HTML includes same fields |
| OF-01 | Apply §1 mechanism |
| OF-04 | Optional; if done, action-level origin remains mandatory |
| Exit | UI/export behavioral tests; suite green |
| Architecture Checkpoint | **ACP-M3** — DTO-only UI; Report-only; export parity (X-08) |

### Macro Phase M4 — Epic acceptance & regression seal

| Item | Detail |
|---|---|
| Goal | R-07 coverage; full regression; Freeze Integrity Check |
| Deliverables | Acceptance fixtures: every insight/action surfaces required fields; full suite green; CAR inputs ready |
| Exit | Stopping Rule SR-M4; epic ready for CAR |
| Architecture Checkpoint | **ACP-M4** — Traceability R-01…R-07 satisfied; no architecture drift |

---

## 3. Commit Boundaries

| Commit ID | Macro | Scope | Must be green |
|---|---|---|---|
| C1 | M1 | `FeatureIdentityDTO` (or equivalent) + `NarrativeInsightDTO` fields + `from_report` insight mapping + unit tests | Yes |
| C2 | M1 | `CoachingActionDTO` + `FinalReportDTO.coaching_actions` + origin resolution + fail-fast on missing objective + unit tests | Yes |
| C3 | M1 | Projection completeness gate hardening (if not fully in C1–C2) + contract tests for empty collections vs missing fields | Yes |
| C4 | M2 | Architectural tests: dual-read ban, LLM-free path, silent-omit forbidden | Yes |
| C5 | M2 | Integration tests: Report fixtures → DTO explainability completeness | Yes |
| C6 | M3 | Narrative section (C-20) inline evidence rendering + tests | Yes |
| C7 | M3 | Coaching actions surface inline origin rendering + tests | Yes |
| C8 | M3 | Export parity (C-26) for explainability fields + tests | Yes |
| C9 | M3 | Optional OF-04 objective enrichment (skip commit if deferred) | Yes if landed |
| C10 | M4 | Acceptance fixtures / epic-level behavioral coverage + full regression | Yes |

**Commit rules**
- One logical concern per commit; no bundling UI with DTO unless hotfix after ACP failure.
- No `--no-verify`. No known failing tests.
- No compatibility shims for old DTO shapes without required explainability fields on presented items.

---

## 4. Critical Path

```
M0 lock
  → C1 NarrativeInsightDTO evidence mapping
  → C2 CoachingActionDTO + origin join + coaching_actions
  → C3 projection gate (if split)
  → C4–C5 architectural + integration tests
  → C6 Narrative UI (OF-01)
  → C7 Coaching actions UI (OF-01)
  → C8 Export parity
  → C10 Acceptance + regression
```

**Critical path bottleneck:** C2 (origin join + fail-fast) blocks all coaching UI and R-02 acceptance.

---

## 5. Parallelizable Work

| After | Parallel tracks | Constraint |
|---|---|---|
| C1 green | Narrative UI spike (branch) vs C2 coaching DTO | UI must not merge before C1; no merge of coaching UI before C2 |
| C2 green | C4 architectural tests ∥ C5 integration tests | Both before M3 merge preferred; C4/C5 before C6–C8 merge required |
| C6 green | C7 coaching UI ∥ C8 export (if owners differ) | Both require C2; export must not invent fields |
| Anytime (non-code) | OF-03 docs cleanup | Out of EPIC-06 critical path; optional; no ADR in this epic |

**Not parallelizable with critical path:** Domain/ReportBuilder changes (forbidden). ADR-025 redesign (forbidden).

---

## 6. Runtime Dependencies

| Dependency | Required at | Notes |
|---|---|---|
| `Report.narrative.insights` with domain evidence fields | C1+ | Already persisted; no producer change |
| `Report.coaching_snapshot.collection.actions` + `objectives` | C2+ | Same-snapshot join only |
| `FinalReportDTO.from_report` sole factory | All presentation | Unchanged ownership |
| EPIC-05 report hosts (C-01…C-06, C-20, coaching hosts, C-26) | M3 | Extend consumers; do not replace pipeline |
| No Observation store / SessionHistory | All phases | Hard ban on explainability path |
| No LLM at presentation | All phases | ARC-01 |

**Builder / domain runtime:** No new runtime dependency on ReportBuilder, NarrativeGenerator, or CoachingEngine schema changes.

---

## 7. Regression Strategy

| Layer | When | Action |
|---|---|---|
| Targeted | Every commit | Run affected unit/contract/UI tests for touched modules |
| Report DTO suite | After C1–C3, C5 | All `FinalReportDTO` / report mapper tests |
| Architectural | After C4, before M3 merge | Dual-read / fail-fast / sole-factory tests |
| Full suite | After C8, after C10, before CAR | Entire project suite — Zero Known Failing Tests |
| Manual smoke (optional) | After C8 | One fixture report: insights show feature identity; actions show origin |

**Regression rule:** If any commit breaks unrelated tests, fix in-phase before proceeding; do not defer failures.

---

## 8. Required Architectural Tests

| ID | Asserts | Maps to |
|---|---|---|
| AT-01 | `from_report` is sole factory used by report HTML and export explainability paths | R-05, PC-E06 |
| AT-02 | Explainability mapping/UI modules do not import/read SessionHistory or Observation store | R-06 |
| AT-03 | No LLM/client calls on explainability projection path | R-06, ARC-01 |
| AT-04 | Missing `source_feature_id` components or `is_traceable` on mapped insight → fail-fast | R-03, R-04, EC-V-01 |
| AT-05 | Unresolved `objective_id` / missing origin fields → fail-fast | R-03, EC-C-01 |
| AT-06 | Silent omission / soft-hide of required anchors is forbidden (negative test) | R-04 |
| AT-07 | Empty insights and empty actions succeed (not missing-anchor) | EC-V-01 empty-set rule |
| AT-08 | Scoring-narrative `knowledge_gaps` not used as coaching-action origin | EC-C-02 |

---

## 9. Integration Tests

| ID | Flow | Asserts |
|---|---|---|
| IT-01 | `Report` fixture with insights → `from_report` | Each `NarrativeInsightDTO` has `source_feature_id` + `is_traceable` |
| IT-02 | `Report` fixture with actions + matching objectives → `from_report` | Each `CoachingActionDTO` has required origin fields |
| IT-03 | `Report` fixture with action + missing objective | Projection fails (fail-fast) |
| IT-04 | `from_report` → view-model/renderer input | Sections receive explainability fields (no domain bypass) |
| IT-05 | `from_report` → export markdown/HTML | Explainability fields present with parity to HTML path |
| IT-06 | End-to-end fixture acceptance | R-07: every insight/action in fixture set surfaces required fields |

---

## 10. Builder Migrations

| Builder | EPIC-06 change | Verdict |
|---|---|---|
| `ReportBuilder` | None | **No migration** |
| `SessionHistoryBuilder` | None | **No migration** |
| NarrativeGenerator / CoachingEngine builders | None | **No migration** |
| Scoring / evaluation builders | None | **No migration** |

**Sequencing note:** Absence of builder migrations is intentional (Freeze DM-P-01). Not a sequencing issue.

---

## 11. DTO Migrations

| DTO / field | Change | Phase / Commit |
|---|---|---|
| `FeatureIdentityDTO` (or equivalent nested shape) | Add presentation type with `feature_type_id`, `semantic_category` [, optional `schema_version`] | M1 / C1 |
| `NarrativeInsightDTO.source_feature_id` | Required additive | M1 / C1 |
| `NarrativeInsightDTO.is_traceable` | Required additive | M1 / C1 |
| `CoachingActionDTO` | New type per Data Model §3.3 | M1 / C2 |
| `FinalReportDTO.coaching_actions` | New list field; default empty | M1 / C2 |
| `FinalReportDTO.from_report` | Map insights + actions + origin join + gate | M1 / C1–C3 |
| `CoachingObjectiveDTO.supporting_observation_types` | Optional (OF-04) | M3 / C9 or defer |

**Migration style:** Additive only. No dual-factory period. No bridge returning explainability-less DTOs for present insights/actions.

---

## 12. Presentation-Layer Implementation

| Component | Work | Depends on | Commit |
|---|---|---|---|
| C-20 NarrativeSection / view-model | Inline evidence per OF-01 from insight DTO | C1 | C6 |
| Coaching actions surface / renderer composition | Inline origin per OF-01 from `coaching_actions` | C2 | C7 |
| C-26 Export | Parity for insight evidence + action origins | C1+C2 | C8 |
| C-21 CoachingObjectivesSection | Optional OF-04 only | C2 | C9 (optional) |
| C-11 KnowledgeGapSection | **No change** for coaching-action origin | — | — |

**UI rules**
- Read DTO fields only.
- Do not call domain `Report` bypassing DTO on production path.
- Do not fetch Observation payloads.
- Fail-fast errors from projection must not be caught and replaced with empty evidence UI.

---

## 13. Completion Criteria

| Criterion | Evidence |
|---|---|
| R-01 | Insights show `source_feature_id` + `is_traceable` in UI + export |
| R-02 | Actions show LearningObjective origin fields in UI + export |
| R-03 / R-04 | AT-04…AT-07 green |
| R-05 | No standalone explainability pipeline; hosts extended only |
| R-06 | AT-02 / AT-03 green |
| R-07 | IT-06 + acceptance fixtures green |
| OF-01 | Applied as §1 inline mechanism |
| Suite | Full green; Zero Known Failing Tests |
| Freeze integrity | No unauthorized edits to frozen planning/ADR docs |

---

## 14. Stopping Rule Checkpoints

| ID | When | Stop if |
|---|---|---|
| SR-M0 | End M0 | Freeze docs missing/contradicted; OF-01 not locked as presentation-only |
| SR-M1 | End M1 | Domain/ReportBuilder touched; dual factory; suite red; required DTO fields absent |
| SR-M2 | End M2 | Architectural tests failing; dual-read detected; fail-fast softened |
| SR-M3 | End M3 | UI reads non-DTO sources; export parity fail; OF-01 expands into architecture |
| SR-M4 | End M4 | Any R-01…R-07 unmet; suite red; Freeze Integrity Check fail |

On stop: fix in-phase or escalate Architecture Checkpoint; do not proceed to next macro phase.

---

## 15. Freeze Integrity Check Checkpoints

| ID | When | Verify |
|---|---|---|
| FIC-M0 | Start implementation | Frozen docs unchanged vs Freeze approval; HEAD baseline recorded |
| FIC-M1 | After C3 | No ADR edits; no Domain Contracts/Data Model/Freeze edits except allowed Overview status later (out of this plan’s authoring step) |
| FIC-M2 | After C5 | Implementation still matches EC-N-01 / EC-C-01 / EC-V-01 |
| FIC-M3 | After C8 | OF-01 did not introduce new ownership/persistence; DTO tables still authoritative |
| FIC-M4 | Before CAR | Diff review: no unauthorized planning/ADR mutations; architecture invariants intact |

**Allowed later (outside this document’s creation):** Overview status updates to reflect implementation progress — must not rewrite frozen contracts.

---

## 16. Architecture Checkpoints (Macro Phase)

| ACP | After | Mandatory checks |
|---|---|---|
| ACP-M0 | M0 | OF-01 presentation-only; no ADR |
| ACP-M1 | M1 | Sole `from_report`; additive DTO; fail-fast gate; no builder migration |
| ACP-M2 | M2 | AT-01…AT-08 intent covered; R-06 intact |
| ACP-M3 | M3 | DTO-only UI/export; inline OF-01; X-08 parity |
| ACP-M4 | M4 | R-01…R-07; Freeze integrity; ready for CAR |

---

## 17. Constraint Verification (Plan-Level)

| Constraint | Maintainable under this sequence? |
|---|---|
| Zero Known Failing Tests | **Yes** — per-commit green rule |
| Green suite after every commit | **Yes** — §3 |
| No compatibility bridges unless required | **Yes** — none required; additive DTO |
| Single-writer invariants | **Yes** — no domain/Report writers; §10 |
| Report-only presentation | **Yes** — §6 / §12 |
| Fail-fast semantics | **Yes** — C2–C3 / AT-04…AT-06 |

**Sequencing issues discovered:** None. Builder migration absence is intentional, not a gap.

---

## 18. Open Issues (post-plan)

| ID | Status | Notes |
|---|---|---|
| OF-01 | **RESOLVED** in this plan (§1) | Execute in M3 |
| OF-02 | Resolved (Data Model) | — |
| OF-03 | Open as docs debt | Out of critical path; no EPIC-06 redesign |
| OF-04 | Optional | C9 or defer without blocking R-02 |

---

## 19. Acceptance Checklist (Implementation Plan)

| Criterion | Status |
|---|---|
| Incremental phases defined | YES — M0…M4 |
| Commit boundaries defined | YES — C1…C10 |
| Critical path defined | YES — §4 |
| Parallelizable work defined | YES — §5 |
| Runtime dependencies defined | YES — §6 |
| Regression strategy defined | YES — §7 |
| Architectural tests defined | YES — §8 |
| Integration tests defined | YES — §9 |
| Builder migrations defined | YES — none required (§10) |
| DTO migrations defined | YES — §11 |
| Presentation-layer implementation defined | YES — §12 + OF-01 |
| Completion criteria defined | YES — §13 |
| Stopping Rule checkpoints | YES — §14 |
| Freeze Integrity Check checkpoints | YES — §15 |
| OF-01 resolved as implementation-only | YES — §1 |
| No architecture / ADR / production code in this step | YES |

---

## 20. Next Step

~~Begin Macro Phase **M0**, then **M1 / C1**.~~ **Superseded** — implementation complete; see §21.

---

## 21. Close-out status (CAR/FR recovery — 2026-07-22)

| Gate | Status |
|---|---|
| C1–C8, C10 | **DONE** |
| C9 / OF-04 | **DEFERRED** (plan-allowed; non-blocking) |
| ACP-M0…M4 | **RECOVERED at CAR Traceability** (living checkpoint transcripts were absent pre-recovery) |
| CAR | **PASS WITH OBSERVATIONS** — 2026-07-22; 0 P0/P1 |
| Final Review | **PASS WITH OBSERVATIONS** — 2026-07-22; 0 P0/P1; Epic Close **AUTHORIZED** |
| Explainability suite (CAR/FR) | **111 passed / 0 failed** |
| Regression Certification | **COMPLETE** — FR reconfirm 111/0 |
| Documentation Certification | **COMPLETE** — Overview / Plan / Master Plan FR markers aligned |
| Epic Close | **AUTHORIZED** — not performed |

Open plan issues disposition: OF-01 **RESOLVED** (executed); OF-03 **OPEN** docs debt (O-CAR-01); OF-04 **DEFERRED**.

---

*Implementation Plan accepted. Architecture remains frozen. OF-01 resolved as inline presentation within existing report sections. CAR/FR recovery updated living status markers only.*
