# EPIC-09 — Architecture Freeze

**Status:** APPROVED  
**Date:** 2026-07-20  
**Epic ID:** EPIC-V13-09  
**Playbook Category:** Category A — Standard Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-09; Product Goal P-09  
**Inputs:** `EPIC-09-ARCHITECTURE-DISCOVERY.md`; `EPIC-09-ARCHITECTURE-REVIEW.md` (APPROVED WITH OBSERVATIONS); ARC-01; Playbook v1.0; EPIC-08 Freeze observability (§6)  
**Authority:** Freezes Architecture Review decisions AR-01–AR-22. Introduces **no** new architecture beyond Review-accepted scope.  
**ADR required:** NO  
**Domain Contracts / Data Model:** N/A (Category A)  
**Implementation:** Implementation Plan **ACCEPTED** (`EPIC-09-IMPLEMENTATION-PLAN.md`); production implementation authorized from Pre-P1 / C1 against this Freeze.

**Disambiguation:** Not PRD EPIC-09 (Interview Replay / session persistence).

---

## 1. Scope

Establish and verify the production performance baseline:

- In-scope SLO measurement (question cycle, report generation, replay load)
- Profiling (`reasoner_node`, KnowledgePipeline per-question, `longitudinal_update_node`)
- 50-session load test with degradation rules
- P0 remediation inside existing compute surfaces
- Performance baseline report as release artifact
- SessionHistory DB read SLO dispositioned **N/A (V1.3)**

**Out of scope (frozen):** horizontal scaling, Redis, CDN, SessionHistory durable store, domain caches, query optimisation beyond SQLite baseline (V2), EPIC-10 dead-code audit.

---

## 2. Architectural objectives

| ID | Objective |
|---|---|
| AO-01 | Question-cycle P99 &lt; 8s measurable and certifiable under baseline load |
| AO-02 | Report generation &lt; 3s measurable (`session_close` → `report`) |
| AO-03 | Replay reconstruction &lt; 1s from materialized `SessionHistory` |
| AO-04 | Profile reasoner + KP (per-q) + longitudinal (cross-session) |
| AO-05 | 50-session load with stub-LLM primary certification |
| AO-06 | P0 SLO violations resolved or release blocked |
| AO-07 | Baseline report published with AR-05 N/A statement |
| AO-08 | Preserve ARC-01: no compute in projection; no ownership dual paths; P-04; P-06 |

---

## 3. Frozen decisions

### 3.1 Accepted / deferred dispositions

| ID | Frozen decision |
|---|---|
| AR-01 | Question-cycle SLO = wall-clock of one written evaluation `graph.invoke`; path includes `written` → `feedback` → `reasoner` → `decision`; P99 &lt; 8s |
| AR-02 | Measurement owned by infra/harness at invoke boundary; no new `InterviewState` fields; optional Freeze-schema emit using existing fields only |
| AR-03 | Report SLO = wall-clock `session_close` entry → `report` exit; excludes `longitudinal_update`, UI, `FinalReportDTO`; target &lt; 3s |
| AR-04 | Replay SLO = `replay_node` reconstruction from materialized `SessionHistory` via `SessionLoader`; target &lt; 1s; “stored” ≠ durable DB I/O |
| AR-05 | SessionHistory DB read SLO = **N/A V1.3**; baseline report must state N/A; no store built in this epic |
| AR-09 | Authoritative cycle latency includes nested LLM; diagnostic LLM join best-effort infra-only; missing join does not block P99 |
| AR-10 | Existing EPIC-08 Freeze fields adequate; infra-only use of existing optional fields allowed; no domain-contract schema fields |
| AR-11 | Profile `reasoner_node` whole + stages (detectors, observation extract, KP) |
| AR-12 | KP = per-question cost; cross-session = `longitudinal_update_node` (+ repo I/O); both required |
| AR-14 | P0 remediations only in existing runtime compute surfaces or infra harness/measurement |
| AR-15 | Load: 50 consecutive sessions; fixed synthetic written-heavy shape (exact N → Impl Plan); early vs late window degradation; zero new hard failures |
| AR-16 | Primary certification = deterministic LLM stub/fake; live-LLM optional appendix only |
| AR-17 | P0 = violation of AR-01/AR-03/AR-04 under AR-15 load; P1/P2 = non-violating work + AR-05 deferral |
| AR-18 | EPIC-06 Overview not CLOSED does not block EPIC-09 |
| AR-19 | Baseline report = markdown release artifact (methodology, measurements, profiles, load, P0, AR-05 N/A, ARC-01 note) |
| AR-22 | Mechanism details (paths, exact thresholds, harness layout) belong to Implementation Plan only |

### 3.2 Explicitly rejected approaches

| ID | Rejected |
|---|---|
| AR-06 | Building SessionHistory durable store / schema in EPIC-09 |
| AR-07 | Caching `ReplaySession` / `LongitudinalProfile` / `SessionHistory` |
| AR-08 | New `InterviewState` fields for cycle correlation |
| AR-13 | Moving FeatureEngine / KP / LLM / Narrative / Coaching into `report_node`, replay UI, or DTO mapping |
| AR-20 | Domain Contracts / Data Model / proactive ADR for this epic |
| AR-21 | LangGraph topology changes for performance (new nodes/edges/routers) |

---

## 4. Frozen SLO definitions

| SLO ID | Metric | Boundary | Target | In-scope for P0 |
|---|---|---|---|---|
| SLO-Q | Written question evaluation cycle | `graph.invoke` wall-clock (AR-01) | P99 &lt; 8s | **Yes** |
| SLO-R | Report generation | `session_close` entry → `report` exit (AR-03) | &lt; 3s | **Yes** |
| SLO-P | Replay load | `replay_node` on materialized `SessionHistory` (AR-04) | &lt; 1s | **Yes** |
| SLO-D | SessionHistory DB read | Production query-by-`session_id` | &lt; 100ms | **No — N/A V1.3** (AR-05) |

---

## 5. Measurement ownership & latency boundaries

| Rule | Frozen |
|---|---|
| MEAS-01 | Question-cycle measurement owned by **infra/harness** at invoke boundary (AR-02) |
| MEAS-02 | No new `InterviewState` fields for measurement (AR-08 rejected) |
| MEAS-03 | Optional structured emit only via existing EPIC-08 Freeze schema fields from infra (AR-02, AR-10) |
| MEAS-04 | Authoritative question latency = AR-01 wall-clock (includes nested LLM) (AR-09) |
| MEAS-05 | Report span excludes longitudinal update, UI, and DTO mapping (AR-03) |
| MEAS-06 | Replay measurement uses injected `SessionLoader` with materialized history — not durable DB I/O (AR-04) |
| MEAS-07 | Harnesses are not product LangGraph control flow (AR-21) |

---

## 6. Profiling boundaries

| Rule | Frozen |
|---|---|
| PROF-01 | Profile `reasoner_node` whole-node + internal stages (AR-11) |
| PROF-02 | Profile KnowledgePipeline as **per-question** cost inside reasoner (AR-12) |
| PROF-03 | Profile `longitudinal_update_node` as **cross-session** update cost (AR-12) |
| PROF-04 | Sub-stage timings may use harness/INFO; Freeze-schema sub-stages not mandatory (AR-10, AR-11) |
| PROF-05 | Highest-latency path evidence = written-cycle reasoner contribution under load (AR-11) |

---

## 7. Load-test methodology

| Rule | Frozen |
|---|---|
| LOAD-01 | 50 consecutive sessions (AR-15) |
| LOAD-02 | Fixed synthetic written-heavy session shape; exact question count → Implementation Plan (AR-15, AR-22) |
| LOAD-03 | Degradation = early window (e.g. 1–10) vs late window (e.g. 41–50) on SLO-Q P99 and SLO-R; threshold → Implementation Plan (AR-15, AR-22) |
| LOAD-04 | Zero new hard failures under load (AR-15) |
| LOAD-05 | Primary certification uses deterministic LLM stub/fake (AR-16) |
| LOAD-06 | Live-LLM run optional appendix only; must not replace stub-primary P0 gate (AR-16; Review O-03) |

---

## 8. Observability usage

| Rule | Frozen |
|---|---|
| OBS-01 | Reuse EPIC-08 Freeze structured-log schema; sole emission path remains infrastructure helper |
| OBS-02 | Node `duration_ms` and LLM `llm.call` durations are valid evidence inputs |
| OBS-03 | Infra-only use of existing optional fields (`execution_id`, cycle-oriented `event` names) allowed (AR-10) |
| OBS-04 | No new domain frozen models for metrics; no schema field set that implies Domain Contracts (AR-10, AR-20) |
| OBS-05 | Diagnostic LLM↔session join is best-effort; must not alter LLM control flow or swallow failures (ARC-01 P-06; AR-09) |
| OBS-06 | Baseline report cites Freeze logs + harness measurements as authoritative sources (AR-19) |

---

## 9. Replay measurement definition

| Rule | Frozen |
|---|---|
| RPL-01 | Replay SLO measures `replay_node` reconstruction wall-clock (AR-04) |
| RPL-02 | Input = materialized `SessionHistory` via `SessionLoader` (fixture or in-memory) |
| RPL-03 | “Stored session” means materialized artifact, **not** durable persistence I/O |
| RPL-04 | No `ReplaySession` cache (AR-07 rejected) |
| RPL-05 | Replay remains LLM-free (I-11); measurement must not introduce LLM |

---

## 10. Production-readiness constraints

| Rule | Frozen |
|---|---|
| PRD-01 | In-scope SLOs (SLO-Q, SLO-R, SLO-P) must pass under LOAD-01…LOAD-05 or P0 blocks release (AR-17) |
| PRD-02 | Performance baseline report is a required release artifact (AR-19) |
| PRD-03 | Baseline report **must** document SLO-D N/A (AR-05; Review O-01) |
| PRD-04 | EPIC-06 not CLOSED does not block EPIC-09 (AR-18) |
| PRD-05 | If a P0 appears to require cache/persistence/state/schema → **stop**; Mini Freeze / Category B re-Review (AA-08; AR-07) |
| PRD-06 | P1/P2 optimisations and tooling polish must not reopen frozen boundaries |

---

## 11. ARC-01 compliance (frozen)

| Rule | Frozen |
|---|---|
| ARC-01 | Runtime computes; projection never — `report_node`, replay UI, DTO mapping remain non-computing |
| ARC-02 | P0 fixes must not move FeatureEngine / KP / LLM / Narrative / Coaching into projection (AR-13) |
| ARC-03 | Close-time Narrative/Coaching optimisations stay in close pipeline only (AR-14) |
| ARC-04 | LangGraph remains sole runtime orchestrator — no out-of-graph product session routers (AR-21) |
| ARC-05 | Telemetry/harness must not swallow failures or alter control flow (P-06) |
| ARC-06 | No dual ownership / undeclared sole writers |
| ARC-07 | No immutable-model mutation for performance |

---

## 12. Category A constraints (frozen)

| Rule | Frozen |
|---|---|
| CAT-01 | Epic remains **Category A** |
| CAT-02 | **No** Domain Contract changes |
| CAT-03 | **No** Data Model changes |
| CAT-04 | **No** `InterviewState` field or sole-writer changes |
| CAT-05 | **No** LangGraph topology changes (nodes/edges/routers) |
| CAT-06 | **No** SessionHistory persistence / `schema_version` additions |
| CAT-07 | **No** domain caches for ReplaySession / LongitudinalProfile / SessionHistory |
| CAT-08 | **No** new frozen domain metrics contracts or builders |
| CAT-09 | Authorized work: harnesses, infra-only observability helpers within existing schema, profiling, load tests, baseline report, in-node compute optimisations without contract change |
| CAT-10 | Any Category B trigger forces stop + re-Review before continuing |

---

## 13. Explicit prohibitions

Implementation **must not**:

1. Build or introduce a SessionHistory durable store or query API for SLO-D.
2. Add Redis / distributed cache / CDN / horizontal scaling.
3. Cache `ReplaySession`, `LongitudinalProfile`, or `SessionHistory`.
4. Add or change `InterviewState` fields for latency correlation.
5. Change LangGraph topology for performance.
6. Move compute into `report_node`, replay presentation, or DTO mapping.
7. Author Domain Contracts, Data Model, or proactive ADRs.
8. Treat live-LLM appendix as the sole P0 certification gate.
9. Claim SLO-D met without a production query surface (must record N/A).
10. Introduce parallel telemetry ownership outside EPIC-08 emission paths.
11. Use performance work to alter product orchestration outside LangGraph.
12. Silently reopen AR-05/AR-06/AR-07/AR-08/AR-13/AR-20/AR-21.

---

## 14. Confirmations

| Item | Status |
|---|---|
| No Domain Contract changes | **Confirmed** |
| No Data Model changes | **Confirmed** |
| No InterviewState changes | **Confirmed** |
| No LangGraph topology changes | **Confirmed** |
| No persistence or cache additions | **Confirmed** |
| ADR required | **NO** |
| New architectural decisions in this Freeze | **None** — AR-01–AR-22 only |

---

## 15. Architecture Exit Criteria (Freeze gate)

Freeze is **APPROVED**. Implementation Plan exit criteria:

- [x] Traces every phase to AR-01–AR-22 / rules above
- [x] Declares commit boundaries with Implementation Dependency Validation
- [x] Declares regression baseline (reconfirm at Pre-P1)
- [x] Defers only AR-22 mechanism details (paths, exact N, numeric degradation threshold) — resolved in Impl Plan §3
- [x] Does not reopen rejected decisions

---

## 16. Observations carried forward

| ID | Observation |
|---|---|
| O-01 | Baseline report must document SLO-D N/A |
| O-02 | CAR must verify zero compute-in-projection and zero new caches/state fields |
| O-03 | Live-LLM appendix must not replace stub-primary certification |
| O-04 | Exact synthetic session shape and degradation threshold → Implementation Plan |

---

## 17. Next activity

**Pre-P1 / C1** per `EPIC-09-IMPLEMENTATION-PLAN.md` (ACCEPTED).
