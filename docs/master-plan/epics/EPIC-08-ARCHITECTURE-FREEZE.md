# EPIC-08 — Architecture Freeze

**Status:** APPROVED  
**Date:** 2026-07-18  
**Epic ID:** EPIC-V13-08  
**Playbook Category:** Category A — Standard Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-08; Product Goal P-08  
**Inputs:** `EPIC-08-OVERVIEW.md`; `EPIC-08-ARCHITECTURE-DISCOVERY.md`; `EPIC-08-ARCHITECTURE-REVIEW.md` (APPROVED WITH OBSERVATIONS); ARC-01; Playbook v1.0  
**Authority:** Freezes Architecture Review decisions AR-01–AR-18. Introduces **no** new architecture beyond Review-accepted scope and the stable observability field names required for EPIC-09 compatibility.  
**ADR required:** NO  
**Domain Contracts / Data Model:** N/A (Category A)  
**Implementation:** Blocked until Implementation Plan accepted; Implementation Plan is now authorized against this Freeze.

---

## 1. Scope

Industrialize and harden the **existing** Hugging Face Spaces deployment:

- Environment-parameterised configuration
- Structured logging + LLM telemetry extension
- Side-effect-free readiness health + CI deploy gate
- Process-level SIGTERM drain
- Deployment and DB migration runbooks (HF operational model)

**Platform:** Hugging Face Spaces only. No platform redesign or migration.

---

## 2. Architectural objectives

| ID | Objective |
|---|---|
| AO-01 | Zero manual production configuration beyond env/secrets via Settings |
| AO-02 | Operator can diagnose session failure from structured logs alone |
| AO-03 | Readiness health gates CI / deploy |
| AO-04 | SIGTERM drain without LangGraph topology or orchestration changes |
| AO-05 | HF / platform behaviour confined to infrastructure / process edge |
| AO-06 | Observability sufficient for EPIC-V13-09 latency measurement |
| AO-07 | Preserve ARC-01: no computation in projection; no ownership dual paths; P-04; P-06 |

---

## 3. Frozen decisions

All Architecture Review decisions are frozen as follows.

### 3.1 Accepted decisions

| ID | Frozen decision |
|---|---|
| AR-01 | HF Spaces is the sole production deployment target |
| AR-02 | HF-specific behaviour confined to process edge / infrastructure |
| AR-03 | `infrastructure/config/settings.py` is the exclusive runtime configuration entry point |
| AR-04 | Production secret/env access goes through Settings only (no dual entrypoint env reads) |
| AR-05 | Structured logging via infrastructure emission helper; graph nodes emit required fields; no new graph edges |
| AR-07 | LLM observability extends existing `ObservingLLMAdapter` / collector path (tokens, latency, model) |
| AR-08 | Health = readiness for LLM connectivity, DB connectivity, execution sandbox |
| AR-10 | Health endpoint used as CI / deploy gate |
| AR-11 | Graceful shutdown = process-level SIGTERM drain for in-flight work |
| AR-13 | Deployment runbook: local / staging / production for HF Spaces model |
| AR-14 | DB migration runbook = policy extension; no on-disk shape change in EPIC-08 |
| AR-16 | EPIC-10 dead-code purity is release-gate / EPIC-10 — not a hard blocker of EPIC-08 implementation |
| AR-18 | Mechanism/wiring details (names, HTTP path, CI YAML shape) belong to Implementation Plan only |

### 3.2 Explicitly rejected approaches

| ID | Rejected |
|---|---|
| AR-06 | Parallel / alternate LLM telemetry ownership |
| AR-09 | Health probes that mutate session/DB or run knowledge / interview LLM cycles |
| AR-12 | New LangGraph shutdown / drain orchestration nodes |
| AR-15 | Schema rewrite / `schema_version` bump in EPIC-08 |
| AR-17 | Domain Contracts / Data Model documents for this epic (Category A) |

---

## 4. Infrastructure boundaries

| Rule | Frozen |
|---|---|
| IB-01 | Platform-specific configuration and HF Spaces behaviour remain in infrastructure / process edge (`app.py`, infra adapters) |
| IB-02 | No HF / deploy-platform dependency in Domain, LangGraph, `InterviewState`, or frozen models |
| IB-03 | Logging and health payloads are infrastructure contracts — not domain `frozen` models |
| IB-04 | Telemetry must not dual-write domain artifacts |
| IB-05 | No new LangGraph nodes, edges, or out-of-graph session routers |

---

## 5. Configuration architecture

| Rule | Frozen |
|---|---|
| CFG-01 | `infrastructure/config/settings.py` (`Settings`) is the **exclusive** runtime configuration entry point |
| CFG-02 | No production component may access `os.environ` directly |
| CFG-03 | Environment variables and secrets are loaded only through Settings |
| CFG-04 | No hardcoded API keys or environment-specific paths in production code |
| CFG-05 | Platform-specific configuration remains confined to infrastructure |

---

## 6. Observability architecture

### 6.1 Structured logging schema (frozen)

Stable fields for structured operational events. Null/omit only when not applicable to the event type; field names are stable.

| Field | Type (logical) | Required when |
|---|---|---|
| `timestamp` | ISO-8601 UTC | Always |
| `level` | string | Always |
| `session_id` | string \| null | Session-scoped events |
| `execution_id` | string \| null | Correlated execution / request |
| `component` | string | Always |
| `graph_node` | string \| null | LangGraph node events |
| `event` | string | Always |
| `duration_ms` | number \| null | Timed operations |
| `model` | string \| null | LLM calls |
| `prompt_tokens` | number \| null | LLM calls |
| `completion_tokens` | number \| null | LLM calls |
| `total_tokens` | number \| null | LLM calls |
| `status` | string | Always (success / failure / skipped / etc.) |
| `error_type` | string \| null | Failures |

**Mapping to Master Plan:** `graph_node` = node name; `duration_ms` = duration; `status` = outcome.

### 6.2 Emission rules

| Rule | Frozen |
|---|---|
| OBS-01 | Infrastructure structured-log helper is the sole emission path for this schema |
| OBS-02 | Every LangGraph node emits structured events including `session_id`, `graph_node`, `duration_ms`, `status` when executing |
| OBS-03 | Logging must not alter control flow or swallow failures (ARC-01 P-06) |
| OBS-04 | LLM call metrics extend existing observing adapter / collector — no second ownership path |
| OBS-05 | Schema must support EPIC-09 latency measurement (`duration_ms`, LLM latency fields) |

---

## 7. Health architecture

| Rule | Frozen |
|---|---|
| HLT-01 | Readiness checks cover: LLM connectivity, database connectivity, execution sandbox |
| HLT-02 | Readiness checks are **side-effect free** |
| HLT-03 | No business / knowledge computation |
| HLT-04 | No persistent mutations |
| HLT-05 | No LangGraph execution |
| HLT-06 | Health endpoint gates CI / deploy |

---

## 8. Shutdown architecture

| Rule | Frozen |
|---|---|
| SDN-01 | Process-level draining only on SIGTERM |
| SDN-02 | In-flight sessions/work handled at process edge |
| SDN-03 | No graph topology changes |
| SDN-04 | No orchestration changes (no new nodes/edges/routers) |

---

## 9. Operational documentation strategy

| Artifact | Frozen intent |
|---|---|
| Deployment runbook | Local / staging / production for HF Spaces Docker model |
| DB migration runbook | Extend V1.2 SQLite schema **versioning policy**; document operator steps; **no** on-disk shape change in this epic |
| Reproducibility | Same image + Settings/env → same deploy behaviour |

---

## 10. Constraints

- ARC-01 binding (P-01, P-04, P-06; no silent fallbacks).
- Category A: no Domain Contracts / Data Model work unless category reclassified.
- ADR not required; do not author ADR unless a future change crosses a constitutional boundary.
- EPIC-10 deploy-artifact dead-code purity remains a release-gate concern (AR-16).
- CAR must re-verify HF confinement (Review O-01).

---

## 11. Non-goals

- New deployment platform or migration off HF Spaces
- Kubernetes / ECS / autoscaling / multi-region
- SaaS billing
- Performance SLO validation (EPIC-09)
- Final architecture cleanup / dead-code audit (EPIC-10)
- On-disk schema / `schema_version` changes
- Domain, `InterviewState`, frozen-model, or LangGraph topology changes

---

## 12. Dependencies

| Dependency | Freeze stance |
|---|---|
| EPIC-V13-01 | Context: no legacy scoring paths in deploy artifact |
| EPIC-V13-10 | Release gate — not hard blocker of EPIC-08 implementation |
| EPIC-V13-07 | CLOSED — Phase 3 stability satisfied |
| V1.2 LLM observability | Extension path (AR-07) |
| EPIC-V13-09 | Downstream consumer of frozen log/telemetry fields |

---

## 13. Success criteria

- [x] Settings exclusive config; no production `os.environ` direct access
- [x] Structured logging schema fields emitted per OBS rules
- [x] LLM observability: tokens, latency, model via existing path
- [x] Readiness health active; CI/deploy gated
- [x] SIGTERM process drain verified
- [x] Deployment + DB migration runbooks complete (HF model; policy only)
- [x] Zero HF leakage into Domain / LangGraph / `InterviewState` / frozen models
- [x] Full regression green at implementation / CAR / epic-close Final Review certification (7417 / 0)

---

## 14. Boundary validation

This Freeze introduces:

| Change type | Introduced? |
|---|---|
| Domain Contract changes | **No** |
| Data Model changes | **No** |
| `InterviewState` changes | **No** |
| Frozen Model changes | **No** |
| LangGraph topology changes | **No** |

| Constitutional boundary | Crossed? |
|---|---|
| Computation / Projection | **No** |
| Orchestration | **No** |
| Ownership | **No** |
| Immutability | **No** |

---

## 15. Freeze declaration

**Architecture Freeze: APPROVED**

- All Architecture Review decisions AR-01–AR-18 frozen  
- No new architectural forks introduced  
- Category A preserved  
- ADR required: **NO**  
- Implementation Plan is the next authorized activity; implementation begins only after Implementation Plan acceptance  

**Observations carried forward (non-blocking):** Review O-01–O-04.
