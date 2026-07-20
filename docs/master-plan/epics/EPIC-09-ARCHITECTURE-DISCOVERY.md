# EPIC-09 — Architecture Discovery

**Status:** COMPLETE  
**Date:** 2026-07-20  
**Epic ID:** EPIC-V13-09  
**Playbook Category:** Category A — Standard Epic (provisional; see §9)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-09; Product Goal P-09  
**Playbook:** V13 Development Playbook Version 1.0  
**Authority:** Findings-only analysis. Does not freeze decisions. Does not authorize implementation. Does not propose solutions.

**Disambiguation:** Not PRD EPIC-09 (Interview Replay / session persistence).

---

## 1. Purpose

Inventory measurement surfaces, latency paths, SLO boundaries, observability readiness, profiling points, load-test boundaries, and architectural risks for EPIC-V13-09 Performance & Scalability Baseline. Determine Category A vs B.

---

## 2. Scope inventory (Master Plan)

| Item | Master Plan statement |
|---|---|
| SLO — question latency | P99 &lt; 8s end-to-end for a written question evaluation cycle |
| SLO — report generation | &lt; 3s from session close |
| SLO — replay load | &lt; 1s for any stored session |
| SLO — SessionHistory read | &lt; 100ms for any `SessionHistory` query |
| Load test | 50 consecutive sessions, no degradation |
| Profile | `reasoner_node` highest-latency path |
| Profile | `KnowledgePipeline` cross-session profile update cost |
| Remediation | Address P0 (SLO violations under baseline load); defer P1/P2 to V2 |
| Release artifact | Performance baseline report |
| Non-goals | Horizontal scaling, Redis, CDN, query optimisation beyond SQLite baseline |

---

## 3. Architectural inventory

### 3.1 Measurement surfaces (existing)

| Surface | Location | Emits | Notes |
|---|---|---|---|
| Structured log schema | `infrastructure/observability/structured_log.py` | Freeze §6.1 fields incl. `duration_ms`, `session_id`, `graph_node`, LLM token fields | Sole emission path (OBS-01) |
| Graph node timing | `infrastructure/observability/graph_node_logging.py` (`instrument_graph_node`) | `event=graph_node.execute`, `component=langgraph`, wall `duration_ms`, status | All production interview + replay nodes wrapped |
| LLM call timing | `ObservingLLMAdapter` → `llm_structured_log_bridge.py` | `event=llm.call`, `duration_ms`, model, tokens, status | **No** `session_id` / `graph_node` / `execution_id` on LLM events |
| In-process LLM metrics | `InterviewMetricsCollector` / `InterviewMetricsAggregator` | avg latency by operation | No p99; no export |
| Ad hoc node timers | e.g. `reasoner_node` INFO `elapsed_ms`; KP stage metrics; `SessionCloseMetrics` | Not Freeze schema | Parallel to structured logs |
| Replay unit budget | `tests/ui/replay/test_replay_performance.py` | ≤1000ms load / ≤100ms nav (in-memory 20q) | Not production I/O |
| Metrics export / SLO tooling | — | **Absent** | No Prometheus/OTel/`/metrics`, no log aggregators, no p99 pipeline |

### 3.2 End-to-end latency flow (written question cycle)

| Stage | Finding |
|---|---|
| Entry | `evaluate_answer` use case → `interview_graph.invoke` |
| Typical path | `entry` → `router` → `written` → `feedback` → `reasoner` → `decision` → END |
| Wall-clock cycle span | **Absent** as a first-class structured event |
| Closest measure | Sum of per-node `graph_node.execute` `duration_ms` for one invoke |
| Outer invoke | `graph.invoke` not timed in Freeze schema |
| LLM on path | `written` (evaluation); `feedback` (improvement). `reasoner` / `decision`: no LLM |
| Correlation gap | LLM `llm.call` events not joined by `session_id` to node events |

### 3.3 `reasoner_node`

| Aspect | Finding |
|---|---|
| Path | `app/graph/nodes/reasoner_node.py` |
| Role | Orchestration: eval-signal inject → `ReasoningContextBuilder` → `ReasonerService.reason` → observation extraction → `KnowledgePipeline` → state updates |
| Sub-timing | INFO `elapsed_ms`; detector `execution_time_ms`; KP stage ms in result metrics |
| Structured timing | Whole-node only via `instrument_graph_node("reasoner")` — sub-stages not in Freeze schema |
| Highest-latency drivers (structural) | Detector registry work; observation extraction; KnowledgePipeline (FeatureEngine / store query / profile build) — all grow with session depth |

### 3.4 `KnowledgePipeline`

| Aspect | Finding |
|---|---|
| Paths | `services/knowledge_pipeline/*`; factory `default_knowledge_pipeline_factory.py` |
| When | **Per question**, inside `reasoner_node` |
| Not run at | `session_close_node`, `report_node` (enforced by tests / RS-02B) |
| LLM | None |
| Cross-session | **Not** KnowledgePipeline. Cross-session profile update is `longitudinal_update_node` + `JsonFileLongitudinalProfileRepository` (`data/longitudinal/`) |
| Master Plan wording gap | MP asks to profile “KnowledgePipeline for cross-session profile update cost” — code shows KP is session-scoped per question; longitudinal path is separate |

### 3.5 Report generation

| Aspect | Finding |
|---|---|
| Graph path | `session_close` → `report` → `longitudinal_update` → END |
| `report_node` | `ReportBuilder.with_session_history` → `state.report` — **assembly / projection** (no FeatureEngine / KP / LLM) |
| Close work | Narrative + Coaching + `SessionClosePipeline` → `session_history` (compute at close; not report projection) |
| UI | `FinalReportDTO.from_report` (presentation) |
| Timing surfaces | Node `duration_ms` for `session_close` / `report`; internal close metrics **not** in Freeze schema |
| SLO boundary ambiguity | “&lt; 3s from session close” — unclear whether clock starts at close entry, close exit, or includes `report` (+ DTO) |

### 3.6 Replay flow

| Aspect | Finding |
|---|---|
| Graph | `app/graph/replay_graph.py`: `replay` → END; instrumented |
| Node | `replay_node`: `SessionLoader` → `ReplayFeatureEngine` → `ReplaySessionBuilder` |
| Caching | None; reconstruct every request (ADR-037) |
| Default loader | UI binding default returns `None`; live path uses in-memory `state.session_history` |
| Persistence I/O | **No** durable SessionHistory load in production path observed |
| Existing gate | In-memory 20q fixture ≤1s (`test_replay_performance.py`) |

### 3.7 SessionHistory reads

| Aspect | Finding |
|---|---|
| Domain model | `domain/contracts/session_history/*` |
| SQLite persistence | `infrastructure/persistence/sqlite/*` = **question_bank only** — **no** SessionHistory table/repo |
| Production query-by-`session_id` | **Absent** |
| SLO implication | Master Plan DB read SLO (&lt;100ms) has **no production read path** to measure today |

### 3.8 EPIC-08 observability readiness for SLO measurement

| Capability | Ready? | Finding |
|---|---|---|
| Per-node wall duration | Yes | OBS-02 / instrumented production nodes |
| LLM latency + tokens | Partial | Emitted; not session-correlated |
| P99 question-cycle | No | No cycle span / cycle id; no p99 aggregation |
| Report SLO span | Partial | Node durations exist; span definition + Freeze coverage incomplete |
| Replay SLO (persisted) | No | No persisted SessionHistory I/O |
| SessionHistory query SLO | No | No store |
| Export / baseline report pipeline | No | Absent |
| OBS-05 intent | Schema-ready | Fields exist; measurement methodology incomplete |

### 3.9 ARC-01 interaction

| Principle | Discovery finding |
|---|---|
| P-01 Runtime computes; projection never | Report/replay/DTO paths must remain non-computing; perf work must not move FeatureEngine/KP/LLM into projection |
| P-04 LangGraph sole orchestrator | Load/profile harnesses must not invent out-of-graph session orchestration as product control flow |
| P-06 No silent fallbacks | Logging/metrics must not swallow failures or alter control flow |
| Replay LLM-free (I-11) | Replay timing must not introduce LLM |
| Caching / dual ownership | Any cache of `LongitudinalProfile` / `ReplaySession` / `SessionHistory` would cross ownership — Category B + ADR territory (not evidenced as required yet) |

### 3.10 Profiling points (inventory only)

| Point | Why |
|---|---|
| Written cycle: `written` + `feedback` + `reasoner` (+ LLM calls) | Dominant question-latency path |
| `reasoner_node` sub-stages | Highest non-LLM compute concentration |
| KnowledgePipeline stages | Per-question cost growth |
| `session_close` Narrative/Coaching | Likely dominates “from session close” wall time |
| `report_node` | Should be cheap if projection-only — verify |
| `longitudinal_update_node` | Actual cross-session update cost |
| `replay_node` reconstruction | Replay SLO (compute); persistence I/O if/when present |
| SessionHistory load API | DB read SLO — path missing |

### 3.11 Load-test boundaries

| Boundary | Finding |
|---|---|
| Master Plan | 50 consecutive sessions, no degradation |
| Existing harness | **Absent** |
| Degradation definition | Undefined (latency drift? memory? error rate?) |
| Scope of “session” | Full interview vs synthetic short session — undefined |
| Interaction with LLM cost/rate limits | Not inventoried as a product constraint; load design must account for external LLM latency variance |

### 3.12 Release metrics (go-live / success)

| Metric | Source |
|---|---|
| All defined SLOs under 50-session load | Master Plan §5 Engineering |
| Performance baseline report published / attached to release | §5 Documentation / Release |
| Production deployment validated | §9 Success Metrics (related) |
| Zero P0/P1 at release gate | §5 Testing |

---

## 4. Dependency analysis

| Dependency | Status | Discovery finding |
|---|---|---|
| EPIC-V13-01 | CLOSED (inherited) | Clean scoring path; report assembly from `Report` |
| EPIC-V13-03 | CLOSED (inherited) | Replay reconstruction + LLM-free invariant; load SLO target |
| EPIC-V13-08 | CLOSED WITH OBSERVATIONS | Structured logs + LLM bridge present; OBS-05 schema support declared |
| EPIC-V13-04 replay perf unit | CLOSED | In-memory ≤1s gate only |
| EPIC-V13-06 | Overview not CLOSED | Not MP dependency; Phase-3 “feature completeness” sequencing note remains open for Review |
| EPIC-V13-10 | Later | Dead-code purity orthogonal; P0 perf fixes must not reintroduce dual paths |

---

## 5. Risk analysis

| ID | Risk | Severity | Boundary |
|---|---|---|---|
| R-01 | No first-class question-cycle span → P99 SLO unverifiable from logs alone | High | Measurement |
| R-02 | LLM events lack `session_id` → cannot attribute LLM cost to cycle | High | Observability join |
| R-03 | SessionHistory query SLO has no production read path | High | Scope / Category B trigger |
| R-04 | Replay SLO “any stored session” lacks durable store I/O | High | Scope / Category B trigger |
| R-05 | Report SLO clock boundary ambiguous (close vs report vs DTO) | Medium | SLO definition |
| R-06 | MP “KnowledgePipeline cross-session” ≠ code (longitudinal is separate) | Medium | Scope clarity |
| R-07 | P0 fixes tempt compute-in-projection or caching without ADR | High | ARC-01 P-01 / ownership |
| R-08 | Load test undefined (degradation, session length, LLM variance) | High | Load boundary |
| R-09 | Sub-stage timings outside Freeze schema → incomplete bottleneck evidence | Medium | Observability |
| R-10 | In-process aggregator only → no release-grade p99 evidence pipeline | Medium | Release artifact |
| R-11 | Optimising close-time Narrative/Coaching may blur compute vs projection | Medium | ARC-01 P-01 |
| R-12 | EPIC-06 unfinished close vs Phase-3 completeness note | Low–Med | Sequencing |
| R-13 | 50-session load against live LLM may be cost/rate limited | Medium | Ops / harness |
| R-14 | Dual timing paths (INFO/metrics vs Freeze logs) confuse baseline report | Low | Hygiene |

---

## 6. Confirmed vs missing (for Review — not decisions)

### Confirmed by Discovery

- EPIC-08 Freeze schema fields exist and production graph nodes emit `duration_ms`.
- LLM latency emits via existing adapter bridge.
- `reasoner_node` hosts per-question KnowledgePipeline.
- `report_node` is projection/assembly.
- Replay reconstructs; no ReplaySession cache.
- No SessionHistory SQLite repository.
- No 50-session load harness; no p99 export pipeline.
- Category A covers measurement/profiling/harness/P0 fixes that stay infra/test-only.

### Missing (Architecture Review must resolve)

- M-01: Formal SLO span definitions (question cycle; report-from-close; replay load; DB read).
- M-02: How to correlate LLM events to sessions/cycles without Category B state ownership.
- M-03: Disposition of SessionHistory DB read SLO given absent store (measure N/A vs in-scope persistence — latter is Category B).
- M-04: Disposition of “stored session” replay SLO without durable SessionHistory I/O.
- M-05: Correct profiling target for “cross-session profile update” (KP vs `longitudinal_update_node`).
- M-06: Load-test definition (session shape, degradation metric, LLM strategy).
- M-07: P0 classification rubric vs V2 deferral.
- M-08: Whether any Freeze-schema emission extension is required (infra-only vs state fields).
- M-09: EPIC-06 / Phase-3 completeness for full SLO certification.
- M-10: Baseline report artifact shape and evidence sources.

---

## 7. Architecture Assumptions Register (initialized)

| ID | Assumption | Status |
|---|---|---|
| AA-01 | SLO validation can use existing Freeze log fields without new domain contracts | UNVERIFIED |
| AA-02 | Question-cycle P99 can be derived without new `InterviewState` fields | UNVERIFIED |
| AA-03 | SessionHistory DB read SLO is measurable against an existing persistence path | **FALSE** (path absent) |
| AA-04 | KnowledgePipeline is the cross-session update cost surface named by Master Plan | **FALSE** (longitudinal path is separate) |
| AA-05 | Report generation SLO is projection-only wall time | UNVERIFIED (close compute may dominate) |
| AA-06 | Replay ≤1s unit gate is sufficient evidence for “any stored session” | **FALSE** (in-memory only) |
| AA-07 | Epic remains Category A if SessionHistory durable store is out of remediation scope | UNVERIFIED (Review) |
| AA-08 | P0 remediations will not require caching layers or schema changes | UNVERIFIED |

---

## 8. Constitutional boundary scan

| Boundary | May EPIC-09 cross? | Finding |
|---|---|---|
| Computation / Projection | Must not | Report/replay/DTO remain non-computing; close-time compute stays at close |
| Orchestration | Avoid | Harnesses ≠ new product graph routing |
| Ownership | Avoid | No dual-write; no undeclared sole writers |
| Immutability | No | No frozen-model mutation evidenced as required for measurement |
| Persistence / schema | Avoid unless Review scopes DB SLO as build-store | Presently **no** SessionHistory store — building one is Category B |
| Presentation | Avoid | UI polish not in scope |

---

## 9. Category assessment

**Provisional: Category A** for the epic as defined (SLO measurement, profiling, load test, P0 fixes, baseline report) **provided** Review keeps durable SessionHistory persistence / schema / `InterviewState` ownership out of scope.

**Escalate to Category B if** Review requires any of:

- New or changed `SessionHistory` persistence schema / `schema_version`
- New frozen domain contracts or builders for metrics/spans
- New `InterviewState` fields or sole-writer changes for cycle correlation
- Caching layers for `ReplaySession` / `LongitudinalProfile` / `SessionHistory`
- Any change that moves computation into projection paths (would also violate ARC-01)

**Category A signals (present):** harnesses, log aggregation, profiling scripts, infra-only emission helpers, behavioral/perf tests, P0 runtime optimisations inside existing compute nodes without contract change.

---

## 10. Discovery conclusions

1. EPIC-08 delivered schema-ready node + LLM duration fields; **not** release-ready SLO measurement (no cycle span, weak LLM join, no p99 export, no 50-session harness).
2. Written question latency is multi-node + LLM; `reasoner_node` + KnowledgePipeline are primary non-LLM compute concentrations.
3. Master Plan “KnowledgePipeline cross-session” does not match code; longitudinal update is the cross-session surface.
4. Report path is projection; close-time work likely dominates “from session close” latency — span must be defined.
5. Replay and SessionHistory DB SLOs lack durable I/O surfaces; these are the primary Category B escalation triggers.
6. ARC-01 P-01 constrains all remediations: no compute-in-projection; caching/ownership changes need ADR + Category B.
7. Epic can remain Category A if Review confines scope to measurement + in-process optimisations and explicitly dispositions the two persistence SLOs.

---

## 11. Recommended next activity

**Architecture Review** (Category A) — resolve M-01–M-10 and AA-01–AA-08; confirm or overturn Category A; declare conditional ADR need; authorize Implementation Plan when no open architectural questions remain.

Do **not** author Domain Contracts, Data Model, or ADRs unless Review finds a genuine unresolved boundary decision or Category B trigger.

---

*End of Architecture Discovery. Findings only — no solutions frozen.*
