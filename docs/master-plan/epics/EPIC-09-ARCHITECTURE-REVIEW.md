# EPIC-09 — Architecture Review

**Status:** COMPLETE  
**Verdict:** APPROVED WITH OBSERVATIONS  
**Date:** 2026-07-20  
**Epic ID:** EPIC-V13-09  
**Playbook Category:** Category A — Standard Epic (**confirmed**)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-09; Product Goal P-09  
**Inputs:** `EPIC-09-ARCHITECTURE-DISCOVERY.md`; ARC-01; Playbook v1.0; EPIC-08 Freeze observability (§6); Master Plan  
**Authority:** Decision disposition for Category A. No Domain Contracts. No Data Model. No Implementation Plan. No production code. No proactive ADR.

**Disambiguation:** Not PRD EPIC-09 (Interview Replay / session persistence).

---

## 1. Scope reviewed

| In scope | Out of scope |
|---|---|
| SLO span definitions + measurement methodology | Horizontal scaling / Redis / CDN |
| Harness + evidence pipeline for baseline report | Building SessionHistory durable store |
| Profiling: `reasoner_node`, KnowledgePipeline (per-q), `longitudinal_update_node` | Query optimisation beyond SQLite baseline (V2) |
| Load test: 50 consecutive sessions, degradation rules | Caching `ReplaySession` / `LongitudinalProfile` / `SessionHistory` |
| P0 remediation inside existing compute nodes (no contract change) | New `InterviewState` fields / sole writers |
| Replay reconstruction latency (materialized `SessionHistory`) | New frozen domain contracts / builders for metrics |
| Infra-only observability join/span helpers (existing Freeze schema) | Moving compute into report/replay/DTO projection |
| Performance baseline report (release artifact) | EPIC-10 dead-code audit |

---

## 2. Discovery review

Discovery accepted as complete and accurate. Key accepted findings:

- EPIC-08 schema is necessary but not sufficient for release-grade SLO evidence.
- No SessionHistory SQLite repository; no durable replay load path.
- KnowledgePipeline is per-question inside `reasoner_node`; cross-session cost is `longitudinal_update_node`.
- `report_node` is projection; close-time Narrative/Coaching is compute.
- Category B triggers are persistence/schema/state/cache — not measurement harnesses.

---

## 3. Architectural decisions

| ID | Question | Disposition | Notes |
|---|---|---|---|
| AR-01 | Question-cycle SLO span | **Accepted** | Wall-clock of one written evaluation `graph.invoke` (use-case / runtime edge → invoke return). Nodes: path that includes `written` → `feedback` → `reasoner` → `decision`. Target P99 &lt; 8s. |
| AR-02 | Question-cycle ownership | **Accepted** | Measurement owned by **infra/harness** at invoke boundary. **No** new `InterviewState` fields. Optional Freeze-schema emit using existing fields (`session_id`, `execution_id`, `duration_ms`, `event`) from infra only. |
| AR-03 | Report generation SLO span | **Accepted** | Wall-clock from `session_close` **entry** through `report` **exit** (sum or contiguous span of those two nodes). **Excludes** `longitudinal_update`, UI, and `FinalReportDTO` mapping. Target &lt; 3s. |
| AR-04 | Replay load SLO | **Accepted** | Wall-clock of `replay_node` reconstruction given a **materialized** `SessionHistory` via injected `SessionLoader` (fixture or in-memory). Target &lt; 1s. “Stored” = materialized artifact, **not** durable DB I/O. |
| AR-05 | SessionHistory DB read SLO | **Deferred N/A (V1.3)** | No production query path exists. EPIC-09 **does not** build SessionHistory persistence. Baseline report records **N/A — no production SessionHistory query surface**; release-gate Engineering checkbox treated as dispositioned N/A for V1.3 unless a later epic adds the store (Category B). |
| AR-06 | Building SessionHistory durable store / schema in EPIC-09 | **Rejected** | Category B + out of non-goals / would redefine epic. |
| AR-07 | Caching ReplaySession / LongitudinalProfile / SessionHistory | **Rejected** | Ownership / immutability risk; ADR + Category B if ever required. |
| AR-08 | New InterviewState fields for cycle correlation | **Rejected** | AR-02 covers measurement without state ownership changes. |
| AR-09 | LLM ↔ session correlation | **Accepted (infra-only)** | Authoritative cycle latency is AR-01 wall-clock (**includes** nested LLM time). Diagnostic LLM attribution: best-effort infra context propagation into existing `ObservingLLMAdapter` / bridge **without** new domain contracts. Missing join must not block P99 certification. |
| AR-10 | Structured logging adequacy | **Accepted with extension allowance** | Existing Freeze fields adequate for node/LLM durations. Allow **infra-only** use of existing optional fields (`execution_id`, cycle-oriented `event` names) — **no** schema field rename/add that implies domain contracts. Sub-stage KP/reasoner timings may remain harness/INFO for profiling evidence. |
| AR-11 | `reasoner_node` profiling boundary | **Accepted** | Profile whole node + internal stages (detectors, observation extract, KnowledgePipeline) via existing metrics / harness timers. Highest-latency path = written-cycle reasoner contribution under load. |
| AR-12 | KnowledgePipeline vs cross-session | **Accepted** | **KP** = per-question profile/feature update cost (inside reasoner). **Cross-session** = `longitudinal_update_node` (+ repository I/O). Both profiled. Master Plan wording corrected by this disposition (AA-04 FALSE retained). |
| AR-13 | Compute in projection | **Rejected** | P0 fixes **must not** move FeatureEngine / KP / LLM / Narrative / Coaching into `report_node`, replay UI, or DTO mapping (ARC-01 P-01). |
| AR-14 | P0 remediations location | **Accepted** | Only inside existing runtime compute surfaces (e.g. reasoner/KP/close pipelines) or infra harness/measurement — no topology ownership changes. |
| AR-15 | Load-test methodology | **Accepted** | 50 consecutive sessions; fixed synthetic session shape (written-heavy, bounded question count — exact N deferred to Implementation Plan). **Degradation** = compare early vs late window (e.g. sessions 1–10 vs 41–50): question-cycle P99 and report span must not worsen beyond Implementation Plan threshold; zero new hard failures. |
| AR-16 | Load-test LLM strategy | **Accepted** | Primary certification run uses **deterministic LLM stub/fake** so compute path is measurable. Supplemental **live-LLM** sample run optional for baseline report appendix (variance noted; not sole P0 gate). |
| AR-17 | P0 / P1 / P2 rubric | **Accepted** | **P0:** any in-scope SLO (AR-01, AR-03, AR-04) violated under AR-15 baseline load. **P1/P2:** non-violating optimisations, tooling polish, deferred persistence (AR-05). P0 must be resolved or release blocked. |
| AR-18 | EPIC-06 / Phase-3 completeness | **Accepted** | EPIC-06 Overview not CLOSED does **not** block EPIC-09. Performance surfaces depend on 01/03/08 (+ 04/05/07 for UX hosts). Proceed. |
| AR-19 | Baseline report artifact | **Accepted** | Markdown release artifact: methodology (this Review), measurements, profiles, load results, P0 dispositions, AR-05 N/A statement, ARC-01 compliance note. |
| AR-20 | Domain Contracts / Data Model / proactive ADR | **Rejected** | Category A; no B trigger authorized. |
| AR-21 | LangGraph topology changes for performance | **Rejected** | No new nodes/edges/routers for perf. |
| AR-22 | Implementation mechanism details | **Deferred** | Implementation Plan — harness layout, thresholds, file paths. |

---

## 4. Discovery M-01–M-10 disposition

| ID | Disposition |
|---|---|
| M-01 | **Resolved** — AR-01, AR-03, AR-04, AR-05 |
| M-02 | **Resolved** — AR-02, AR-09 (no Category B state) |
| M-03 | **Resolved** — AR-05 Deferred N/A; AR-06 Rejected |
| M-04 | **Resolved** — AR-04 materialized SessionHistory; no durable I/O required |
| M-05 | **Resolved** — AR-12 (KP per-q + longitudinal cross-session) |
| M-06 | **Resolved** — AR-15, AR-16 |
| M-07 | **Resolved** — AR-17 |
| M-08 | **Resolved** — AR-10 (infra-only existing fields; no domain schema) |
| M-09 | **Resolved** — AR-18 |
| M-10 | **Resolved** — AR-19 |

---

## 5. Assumption dispositions (AA-01–AA-08)

| ID | Status after Review |
|---|---|
| AA-01 | **VERIFIED** — Freeze fields + harness; no new domain contracts (AR-10) |
| AA-02 | **VERIFIED** — Invoke-boundary wall-clock; no InterviewState fields (AR-02) |
| AA-03 | **FALSE retained** — path absent; dispositioned by AR-05 (N/A), not reopened as build-store |
| AA-04 | **FALSE retained** — corrected by AR-12 |
| AA-05 | **FALSE → clarified** — Report SLO includes `session_close` compute + `report` assembly (AR-03); projection-only claim rejected |
| AA-06 | **FALSE retained** as durable-I/O claim; **replay evidence** = extended materialized reconstruction (AR-04), not DB |
| AA-07 | **VERIFIED** — Category A confirmed; store out of scope (AR-05/06) |
| AA-08 | **VERIFIED (constraint)** — P0 must not introduce cache/schema; if a P0 appears to require them → stop, Mini Freeze / escalate (AR-07, AR-13) |

---

## 6. Risk resolution

| ID | Can existing architecture address? | Resolution |
|---|---|---|
| R-01 | **Yes** | Closed by AR-01/AR-02 harness (+ optional infra emit) |
| R-02 | **Yes (non-blocking)** | Closed for certification by AR-09; diagnostic join best-effort |
| R-03 | **Yes (by scope)** | Closed by AR-05 N/A — not by building store |
| R-04 | **Yes (reinterpret)** | Closed by AR-04 materialized replay |
| R-05 | **Yes** | Closed by AR-03 |
| R-06 | **Yes** | Closed by AR-12 |
| R-07 | **Yes (constraint)** | Closed by AR-13/AR-14/AR-07; CAR enforces |
| R-08 | **Yes** | Closed by AR-15/AR-16 |
| R-09 | **Yes** | Profiling harness/INFO accepted (AR-11); not Freeze-mandatory |
| R-10 | **Yes** | Closed by AR-19 evidence pipeline in tests/scripts → report |
| R-11 | **Yes (constraint)** | Close optimisations stay in close pipeline (AR-13/AR-14) |
| R-12 | **Yes** | Closed by AR-18 |
| R-13 | **Yes** | Closed by AR-16 stub-primary |
| R-14 | **Yes** | Baseline report cites Freeze + harness as authoritative sources (AR-19) |

**Persistence / cache / state proposals:** all **Rejected** (AR-06, AR-07, AR-08).

---

## 7. Boundary validation

| Boundary | Crossed? | Evidence |
|---|---|---|
| Computation / Projection | **No** | AR-13; report/replay remain non-computing |
| Orchestration (P-04) | **No** | AR-21; harness ≠ product graph routing |
| Ownership | **No** | AR-08 rejects state fields; AR-07 rejects caches |
| Immutability | **No** | No frozen-model changes |
| Persistence / schema | **No** | AR-05/AR-06 |
| Presentation | **No** | DTO/UI excluded from report SLO |

---

## 8. Category decision

**Category A — confirmed.**

Authorized: measurement harnesses, infra-only observability helpers within existing Freeze schema, profiling, load tests, baseline report, P0 optimisations inside existing compute nodes without contract/topology/persistence changes.

**Not authorized (would force re-Review + Category B):** SessionHistory store, schema_version changes, new frozen metrics contracts, InterviewState ownership changes, domain caches.

---

## 9. ADR assessment

**ADR required: NO**

No constitutional exemption. Scope dispositions (AR-05, AR-04) and measurement ownership (AR-02) stay within ARC-01 and Category A. Caching/persistence remain rejected — if later evidence forces them, **stop** and author ADR under Category B reclassification.

**Architecture Freeze document:** Not required by Playbook Category A path. Optional later only if Implementation Plan needs a freeze-style checklist (EPIC-08 precedent) — not mandated by this Review.

---

## 10. Findings

### Observations (non-blocking)

- O-01: Baseline report must explicitly document AR-05 N/A for SessionHistory DB read SLO.
- O-02: CAR must verify zero compute-in-projection and zero new caches/state fields.
- O-03: Live-LLM appendix must not silently replace stub-primary load certification (AR-16).
- O-04: Exact synthetic session shape and degradation numeric threshold → Implementation Plan (AR-22).

### Blocking findings

- None.

---

## 11. Review verdict

**APPROVED WITH OBSERVATIONS**

---

## 12. Open issues

- None architectural. Implementation Plan may detail mechanisms under AR-22 without reopening architecture.

---

## 13. Next activity

**Implementation Plan** (Category A) — commit boundaries and phases for: measurement harnesses (AR-01/03/04), profiling (AR-11/12), 50-session load (AR-15/16), P0 remediation gate (AR-17), baseline report (AR-19) — against decisions AR-01–AR-22.

Do **not** author Domain Contracts, Data Model, or ADRs unless a P0 forces a rejected boundary (then re-Review + Category B).
