# Performance Baseline Report

**Epic:** EPIC-V13-09 — Performance & Scalability Baseline  
**Artifact:** Release performance baseline (Freeze AR-19 / PRD-02)  
**Date:** 2026-07-21  
**Primary certification LLM:** Deterministic stub/fake (AR-16)  
**Governing Freeze:** `docs/master-plan/epics/EPIC-09-ARCHITECTURE-FREEZE.md`  
**Harness sources:** `tests/performance/`, `scripts/performance/`  
**P0 disposition:** **P0-ABSENT** (EPIC-09 C9)  
**Release attachment:** **ATTACHED** to V1.3.0 (`v1.3.0` tag; ceremony 2026-07-22; Master Plan §5 / RR authorization)

---

## 1. Methodology

| Item | Choice |
|---|---|
| Measurement ownership | Infra/harness wall-clock at invoke / node boundary (AR-01–AR-04; MEAS-*) |
| SLO-Q boundary | Written evaluation `graph.invoke` (written → feedback → reasoner → decision) |
| SLO-R boundary | Contiguous wall-clock `session_close` entry → `report` exit; excludes `longitudinal_update`, UI, `FinalReportDTO` |
| SLO-P boundary | `replay_node` / replay graph invoke on materialized `SessionHistory` (≥20q fixture); no durable DB |
| Load shape | **50** consecutive sessions × **5** written questions (Implementation Plan §3) |
| Degradation windows | Sessions **1–10** (early) vs **41–50** (late); late/early ≤ **1.25** and absolute SLO hold |
| Stub LLM | `DeterministicStubLLM` — primary certification path; no live network |
| Live-LLM appendix | Optional only; **not** the P0 gate (AR-16; O-03) |
| Authoritative sources | This report + Freeze + harness measurements (OBS-06) |
| Optional cycle emit | Infra-only `question_cycle.complete` via existing EPIC-08 Freeze schema fields |

### Reproduction commands

```bash
python scripts/performance/run_stub_load.py
python scripts/performance/profile_reasoner_kp.py
python scripts/performance/profile_longitudinal.py
python -m pytest tests/performance/ -q
```

---

## 2. Measurements (in-scope SLOs)

Certification run under stub-LLM (2026-07-21). Absolute targets from Freeze / Implementation Plan §3.

| SLO | Boundary | Target | Measured | Result |
|---|---|---|---|---|
| **SLO-Q** | Written `graph.invoke` P99 (250 samples under load) | &lt; 8000 ms | **2.25 ms** P99 | **PASS** |
| **SLO-R** | `session_close` → `report` max (50 sessions) | &lt; 3000 ms | **0.41 ms** max | **PASS** |
| **SLO-P** | Replay reconstruction (materialized ≥20q) | &lt; 1000 ms | **≤ 1.45 ms** (sample max) | **PASS** |
| **SLO-D** | SessionHistory DB read by `session_id` | &lt; 100 ms | — | **N/A V1.3** (see §6) |

Harness modules: `tests/performance/slo_q.py`, `slo_r.py`, `slo_p.py`, `load_stub_sessions.py`.

---

## 3. Profiles

Stubbed written-cycle / close-path profiling (PROF-01–05 / AR-11–AR-12). Values are harness wall-clock evidence, not product telemetry schema fields.

### 3.1 `reasoner_node` + KnowledgePipeline (per-question)

| Stage | Duration (ms) |
|---|---|
| Whole `reasoner_node` | 1.11 |
| Detectors | 0.22 |
| Observation extract | 0.58 |
| KnowledgePipeline (node attribution) | 0.22 |
| KP total (feature engine + profile build) | 0.17 |
| Containing written cycle (invoke) | 6.68 |

Command: `python scripts/performance/profile_reasoner_kp.py`

### 3.2 `longitudinal_update_node` (+ repo I/O)

| Session | Whole node (ms) | repo get (ms) | repo save (ms) | Prior profile |
|---|---|---|---|---|
| First (`interview_index=0`) | 0.82 | 0.01 | 0.77 | No |
| Second (`interview_index=1`) | 0.32 | 0.05 | 0.24 | Yes |

Command: `python scripts/performance/profile_longitudinal.py`

---

## 4. Load results

| Metric | Value |
|---|---|
| Sessions | 50 consecutive |
| Questions / session | 5 written |
| SLO-Q samples | 250 |
| Hard failures | **0** |
| SLO-Q P99 (all) | 2.25 ms (&lt; 8000) |
| SLO-R max (all) | 0.41 ms (&lt; 3000) |
| Early SLO-Q P99 (1–10) | 3.66 ms |
| Late SLO-Q P99 (41–50) | 2.18 ms |
| SLO-Q late/early ratio | **0.60** (≤ 1.25) |
| Early SLO-R max (1–10) | 0.41 ms |
| Late SLO-R max (41–50) | 0.20 ms |
| SLO-R late/early ratio | **0.49** (≤ 1.25) |
| Absolute hold (late window) | Late SLO-Q P99 &lt; 8s; late SLO-R max &lt; 3s — **PASS** |

Command: `python scripts/performance/run_stub_load.py`  
Tests: `tests/performance/test_load_stub_sessions.py`, `test_load_degradation.py`

### Live-LLM appendix

Not executed for this baseline. Live-LLM remains optional and must not replace stub-primary certification (AR-16; Freeze O-03).

---

## 5. P0 disposition

| Item | Result |
|---|---|
| In-scope P0 definition | Violation of SLO-Q / SLO-R / SLO-P under AR-15 stub load (AR-17) |
| P0 list | **Empty** |
| Remediation applied | **None** (certification-only; C9) |
| Category B / PRD-05 stop | Not triggered |
| Verdict | **P0-ABSENT** |

---

## 6. SLO-D — N/A V1.3

**Disposition:** SessionHistory DB read latency (**SLO-D**) is **N/A for V1.3**.

| Rule | Application |
|---|---|
| AR-05 | No production SessionHistory query-by-`session_id` store in this epic |
| AR-06 rejected | Durable SessionHistory store / schema **not** built |
| PRD-03 / O-01 | This report **must** state N/A — satisfied here |
| Claim SLO-D met | **Forbidden** without a production query surface |

SLO-P remains the in-scope replay reconstruction gate on **materialized** `SessionHistory` only.

---

## 7. ARC-01 / Category A compliance note

| Constraint | Status |
|---|---|
| ARC-01 — runtime computes; projection never | **Held** — `report_node`, replay UI, DTO mapping remain non-computing |
| ARC-02 / AR-13 — no compute moved into projection | **Held** |
| CAT-02–CAT-08 — no Domain Contracts, Data Model, InterviewState, topology, SessionHistory persistence, domain caches, metrics contracts | **Held** |
| AR-14 — P0 only in existing compute / harness | N/A (no remediation) |
| Arch enforcement | `tests/infrastructure/architecture/test_epic09_hardening_architecture.py` (C10) |

EPIC-09 authorized surfaces remain harnesses, optional infra cycle emit within existing Freeze schema, profiling, load tests, and this baseline report.

---

## 8. Production-readiness checklist (performance)

| ID | Criterion | Evidence | Status |
|---|---|---|---|
| PRD-01 | SLO-Q / SLO-R / SLO-P pass under stub load | §2, §4; C7–C8 | **PASS** |
| PRD-02 | Baseline report published | This artifact | **PASS** |
| PRD-03 | SLO-D documented N/A | §6 | **PASS** |
| PRD-04 | EPIC-06 not CLOSED does not block | Freeze AR-18 | **N/A (allowed)** |
| PRD-05 | No Category B stop required | C9 P0-absent | **PASS** |
| AO-01…AO-04 | In-scope SLOs measurable / met under harness | §2 | **PASS** |
| AO-05 | 50-session stub load | §4 | **PASS** |
| AO-06 | P0 resolved or absent | §5 | **PASS** |
| AO-08 | ARC-01 preserved | §7; C10 arch tests | **PASS** |
| LOAD-03 | Degradation ≤ 1.25 + absolute hold | §4 | **PASS** |
| O-02 | Zero compute-in-projection; no new caches/state fields | C10 arch tests | **PASS** |
| Full regression ≥ Pre-P1 | C12 suite certification | **PASS** — **7485 passed / 0 failed** (baseline 7417) |

---

## 9. Out of scope (explicit)

- SessionHistory durable store / SLO-D production query surface  
- Redis / CDN / horizontal scaling  
- Domain caches (`ReplaySession`, `LongitudinalProfile`, `SessionHistory`)  
- InterviewState / LangGraph topology changes  
- Live-LLM as sole P0 gate  
- EPIC-10 dead-code audit  
- Claiming SLO-D met  

---

## 10. Document control

| Field | Value |
|---|---|
| Path | `docs/ops/PERFORMANCE-BASELINE-REPORT.md` |
| Created | EPIC-V13-09 Commit C11 |
| C12 regression note | Full suite **7485 / 0** (2026-07-21); ≥ Pre-P1 7417 |
| Supersedes | None (initial V1.3 performance baseline) |
