# EPIC-03 — Replay Engine

**Status:** CLOSED  
**Date:** 2026-07-15 (implementation close); living Overview recovered 2026-07-22  
**Epic ID:** EPIC-V13-03  
**Playbook Category:** Category B — Major Architectural Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-03; Product Goal P-03  
**Roadmap Phase:** Phase 2 — Core Domain  
**Precondition:** EPIC-V13-01 CLOSED; ADR-037 accepted; Architecture Freeze FROZEN.  
**Architecture Discovery:** `EPIC-03-REPLAY-ENGINE.md` — historical planning record  
**Domain Contracts:** `EPIC-03-DOMAIN-CONTRACTS.md` — FROZEN  
**Data Model:** `EPIC-03-DATA-MODEL.md` — FROZEN  
**Architecture Freeze:** `EPIC-03-ARCHITECTURE-FREEZE.md` — FROZEN  
**Implementation Plan:** `EPIC-03-IMPLEMENTATION-PLAN.md` — ACCEPTED; EPIC CLOSED  
**Implementation:** COMPLETE (Phases through migration cleanup `e13a47f`)  
**Governing ADR:** ADR-037  
**Construction Architecture Review (CAR):** Historical — no contemporaneous Overview CAR transcript (pre–living-Overview convention)  
**Final Review (FR):** Accepted by EPIC-04 Definition of Ready (“EPIC-03 Final Review passed and CLOSED”)  
**Epic Close:** CLOSED — 2026-07-15; documentation recovery 2026-07-22  
**Playbook:** V13 Development Playbook Version 1.0

---

## 1. Business Objective

Implement `replay_node` as a closed, deterministic, LLM-free reconstruction pipeline that produces a navigable `ReplaySession` from stored `SessionHistory`.

## 2. Architectural Objective

Activate V1.3 replay contracts; wire a standalone Replay Graph; enforce I-11 and Reconstruction Completeness by architectural tests; delete V1.2 legacy replay orchestrator/result artifacts in the same activation increment.

## 3. Dependencies

| EPIC / ADR | Status | Dependency |
|---|---|---|
| EPIC-V13-01 | CLOSED | `Report`-consistent scoring fields on `SessionHistory` v2.0 |
| EPIC-V13-02 | CLOSED | Parallel Phase 2; no hard runtime dependency |
| ADR-037 | Accepted | Replay engine architecture |

## 4. Workflow Status

```
EPIC Initialization  ← COMPLETE
Architecture Discovery  ← COMPLETE (historical)
Domain Contracts  ← COMPLETE (frozen)
Data Model  ← COMPLETE (frozen)
Architecture Freeze  ← COMPLETE
Implementation Plan  ← ACCEPTED
Implementation  ← COMPLETE
CAR (living transcript)  ← NOT RECORDED AT CLOSE (historical gap)
Final Review  ← ACCEPTED via EPIC-04 DoR
Epic Close  ← CLOSED
Documentation Recovery  ← COMPLETE — 2026-07-22
```

## 5. Closure Evidence

| Evidence | Reference |
|---|---|
| Migration + cleanup complete | commit `e13a47f` (2026-07-15) |
| Determinism fixtures | `tests/app/graph/nodes/test_replay_determinism.py` (≥20 cases) |
| I-11 architectural tests | `tests/app/graph/nodes/test_replay_architectural_invariants.py` |
| Successor DoR | `EPIC-04-OVERVIEW.md` prerequisites checked |

## 6. Open / Carry-Forward

None blocking. Replay UI owned by EPIC-V13-04 (CLOSED).

## 7. Recommendation

**EPIC-V13-03 is CLOSED.** No further EPIC-03 scope.

---

*This Overview is the living status document for EPIC-V13-03. Frozen Discovery / Domain Contracts / Data Model / Architecture Freeze bodies remain historical records. Epic CLOSED.*
