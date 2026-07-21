# EPIC-09 — Performance & Scalability Baseline

**Status:** IMPLEMENTATION IN PROGRESS — Macro C / C9 complete — next C10  
**Date:** 2026-07-21  
**Epic ID:** EPIC-V13-09  
**Playbook Category:** Category A — Standard Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-09; Product Goal P-09  
**Roadmap Phase:** Phase 4 — Production Readiness  
**Precondition:** EPIC-V13-01 CLOSED; EPIC-V13-03 CLOSED; EPIC-V13-08 CLOSED WITH OBSERVATIONS; Architecture Freeze APPROVED.  
**Regression baseline (planning):** 7417 passed / 0 failed (EPIC-08 close-out)  
**EPIC-09 implementation baseline (pre-P1):** **7417 passed / 0 failed**  
**Planning:** COMPLETE  
**Architecture Discovery:** `EPIC-09-ARCHITECTURE-DISCOVERY.md` — **COMPLETE**  
**Architecture Review:** `EPIC-09-ARCHITECTURE-REVIEW.md` — **APPROVED WITH OBSERVATIONS**  
**Formal ADR:** **SKIP** (ADR required: NO)  
**Domain Contracts:** N/A (Category A)  
**Data Model:** N/A (Category A)  
**Architecture Freeze:** `EPIC-09-ARCHITECTURE-FREEZE.md` — **APPROVED**  
**Implementation Plan:** `EPIC-09-IMPLEMENTATION-PLAN.md` — **ACCEPTED**  
**Implementation:** IN PROGRESS — **C1–C9 complete**; Checkpoint A **PASSED**; Checkpoint B **PASSED**; next **C10**  
**P0 disposition (P6 / C9):** **P0-ABSENT** — no in-scope SLO violations under P5 stub-LLM load (C7–C8 green); no compute remediation applied  
**Playbook:** V13 Development Playbook Version 1.0

**Disambiguation:** Not PRD EPIC-09 (Interview Replay / session persistence).

---

## 1. EPIC Identification

| Field | Value |
|---|---|
| **Identifier** | EPIC-V13-09 |
| **Title** | Performance & Scalability Baseline |
| **Master Plan reference** | `V13-PRODUCT-MASTER-PLAN.md` §4 EPIC-V13-09; Product Goal **P-09** |
| **Category** | **Category A** — Standard Epic |
| **Phase** | Phase 4 — Production Readiness |
| **Category rationale** | Measurement, profiling, load, P0 in-node optimisations, baseline report — no domain contracts, persistence, InterviewState, or topology changes (Freeze CAT-*). |

---

## 2. Scope

Establish and verify production performance baseline per Freeze:

- SLO-Q / SLO-R / SLO-P measurement and certification under stub-LLM load  
- Profiling: `reasoner_node`, KnowledgePipeline (per-question), `longitudinal_update_node`  
- 50-session load + degradation gate  
- P0 remediation within existing compute surfaces (or P0-absent certification)  
- Performance baseline report (`docs/ops/PERFORMANCE-BASELINE-REPORT.md`)  
- SLO-D (SessionHistory DB read) dispositioned **N/A V1.3**

---

## 3. Goals

| ID | Goal |
|---|---|
| G-01 | Question-cycle P99 &lt; 8s under baseline load |
| G-02 | Report generation &lt; 3s (`session_close` → `report`) |
| G-03 | Replay reconstruction &lt; 1s from materialized SessionHistory |
| G-04 | Profiling evidence for reasoner/KP/longitudinal |
| G-05 | 50-session stub-LLM load with degradation ≤1.25 |
| G-06 | P0 resolved or certified absent |
| G-07 | Baseline report published with SLO-D N/A |
| G-08 | ARC-01 / Category A constraints held |

---

## 4. Non-Goals

| ID | Non-goal |
|---|---|
| NG-01 | SessionHistory durable store |
| NG-02 | Redis / CDN / horizontal scaling |
| NG-03 | Domain caches |
| NG-04 | InterviewState / LangGraph topology changes |
| NG-05 | Claiming SLO-D met |
| NG-06 | EPIC-10 dead-code audit |

---

## 5. Dependencies

| EPIC | Status | Dependency |
|---|---|---|
| EPIC-V13-01 | CLOSED | Clean pipeline |
| EPIC-V13-03 | CLOSED | Replay reconstruction target |
| EPIC-V13-08 | CLOSED WITH OBSERVATIONS | Structured logging / LLM duration fields |

---

## 6. Workflow status

```
EPIC Initialization          ← COMPLETE
Architecture Discovery       ← COMPLETE
Architecture Review          ← APPROVED WITH OBSERVATIONS
Architecture Freeze          ← APPROVED
Implementation Plan          ← ACCEPTED
Pre-P1 baseline              ← COMPLETE (7417 passed / 0 failed)
Implementation (C1–C12)      ← IN PROGRESS (C1–C9 complete; Macro C / P6 done)
Checkpoint A                 ← PASSED
Checkpoint B                 ← PASSED (Macro C authorized)
Checkpoint C
CAR → Regression → Docs → FR → Epic Close
```

---

## 7. Implementation progress

| Commit | Phase | Status |
|---|---|---|
| Pre-P1 | — | **DONE** — baseline 7417 passed / 0 failed |
| C1 | P1 | **DONE** — SLO-Q written invoke harness + stub + P99 helper |
| C2 | P1 | **DONE** — optional infra cycle emit (`question_cycle.complete`) |
| C3 | P2 | **DONE** — SLO-R close→report harness (&lt; 3s) |
| C4 | P3 | **DONE** — SLO-P replay reconstruction harness (&lt; 1s) |
| Checkpoint A | — | **PASSED** — Macro B authorized |
| C5 | P4 | **DONE** — reasoner + KP stage profiling harness |
| C6 | P4 | **DONE** — longitudinal_update (+ repo I/O) profiling harness |
| C7 | P5 | **DONE** — 50-session stub-LLM load + absolute SLO gates |
| C8 | P5 | **DONE** — early vs late degradation gate (≤1.25 + absolute hold) |
| Checkpoint B | — | **PASSED** — Macro C (P6–P7) authorized |
| C9 | P6 | **DONE** — **P0-ABSENT** certified (no remediation; C7–C8 re-verified green) |

### P6 / C9 — P0 certification

| Item | Result |
|---|---|
| P5 load (C7) | Green — SLO-Q P99 &lt; 8s; SLO-R max &lt; 3s; zero hard failures |
| Degradation (C8) | Green — late/early ≤ 1.25; absolute SLO hold |
| In-scope P0 list (AR-17) | **Empty** |
| Remediation applied | **None** (certification-only; no speculative compute changes) |
| Freeze stop rule (PRD-05) | N/A — no Category B pressure |
| Category A / ARC-01 | Held — no Domain Contracts, Data Model, InterviewState, topology, persistence, or cache changes |

---

## 8. Next planned activity

**C10** — Category A / ARC-01 arch constraint tests per `EPIC-09-IMPLEMENTATION-PLAN.md`.
