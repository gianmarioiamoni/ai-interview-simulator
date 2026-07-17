# EPIC-08 — Architecture Review

**Status:** COMPLETE  
**Verdict:** APPROVED WITH OBSERVATIONS  
**Date:** 2026-07-18  
**Epic ID:** EPIC-V13-08  
**Playbook Category:** Category A — Standard Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-08; Product Goal P-08  
**Inputs:** `EPIC-08-OVERVIEW.md`; `EPIC-08-ARCHITECTURE-DISCOVERY.md`; ARC-01; Playbook v1.0  
**Living Overview:** `EPIC-08-OVERVIEW.md`  
**Authority:** Decision disposition for Category A. No Domain Contracts. No Data Model. No Architecture Freeze document. No Implementation Plan. No production code. No proactive ADR.

---

## 1. Scope reviewed

| In scope | Out of scope |
|---|---|
| Env-driven configuration via `settings.py` | New deployment platform |
| Structured node logging | K8s / ECS / autoscaling / multi-region |
| LLM telemetry extension (existing infra path) | SaaS billing |
| Readiness health + CI deploy gate | Performance SLO validation (EPIC-09) |
| Process-level SIGTERM drain | Final dead-code audit (EPIC-10) |
| HF Spaces deploy + DB migration runbooks (policy/docs) | On-disk schema shape changes |
| HF confinement to process/infra edge | LangGraph topology / Domain / `InterviewState` changes |

**Platform:** Hugging Face Spaces — harden existing operational deploy only.

---

## 2. Architecture assessment

| Concern | Review conclusion |
|---|---|
| Constitutional boundaries | Preserved by accepted decisions below; no required boundary crossing |
| HF confinement | Mandatory: Spaces/Docker/token bootstrap remain at `app.py` / infrastructure adapters only |
| Runtime orchestration | **No** new LangGraph nodes, edges, or out-of-graph session routers |
| Domain ownership | **No** new sole writers; logging/telemetry do not write domain artifacts |
| Persistence | **No** stored-shape / `schema_version` changes; runbook/policy only |
| Computation / projection | Health and ops must not perform knowledge computation or session assembly |

---

## 3. Decision log

| ID | Capability / question | Disposition | Notes |
|---|---|---|---|
| AR-01 | HF Spaces remains sole production target; no platform redesign | **Accepted** | Known Input; NG-01 |
| AR-02 | HF-specific behaviour confined to process edge / infrastructure | **Accepted** | Binding; CAR verifies |
| AR-03 | Single configuration source: `infrastructure/config/settings.py` | **Accepted** | Unify secret/env reads through Settings |
| AR-04 | Entrypoint dual `os.environ` secret reads eliminated in favour of Settings | **Accepted** | Resolves M-05 / R-08 |
| AR-05 | Structured logging: infrastructure emission helper; nodes emit `session_id`, node, duration, outcome | **Accepted** | No new graph edges; field set fixed by Master Plan |
| AR-06 | Parallel / alternate telemetry ownership for LLM calls | **Rejected** | Extend `ObservingLLMAdapter` / existing collector only |
| AR-07 | LLM observability: token usage, latency, model tier via existing path | **Accepted** | EPIC-09 compatibility (duration fields + LLM latency) |
| AR-08 | Health = readiness for LLM connectivity, DB connectivity, execution sandbox | **Accepted** | Master Plan scope |
| AR-09 | Health probes that mutate session/DB or run knowledge/LLM interview cycles | **Rejected** | Side-effect-free verification only |
| AR-10 | Health used as CI / deploy gate | **Accepted** | Exact HF wiring detail → Implementation Plan |
| AR-11 | Graceful shutdown = process-level SIGTERM drain for in-flight work | **Accepted** | Preserves P-04 |
| AR-12 | New LangGraph shutdown / drain orchestration nodes | **Rejected** | Would cross Orchestration Boundary → would require ADR; not selected |
| AR-13 | Deployment runbook (local / staging / production) for HF model | **Accepted** | Docs/ops |
| AR-14 | DB migration runbook = policy extension; no on-disk shape change in EPIC-08 | **Accepted** | AA-03; resolves M-07 |
| AR-15 | Schema rewrite / `schema_version` bump as part of EPIC-08 | **Rejected** | Category B trigger if ever required later |
| AR-16 | EPIC-10 dead-code purity as hard blocker of EPIC-08 Review / Impl Plan | **Rejected** | Release-gate / EPIC-10; AA-07 **VERIFIED** |
| AR-17 | Domain Contracts / Data Model / Architecture Freeze documents for EPIC-08 | **Rejected** | Category A; no B trigger evidenced |
| AR-18 | Implementation mechanism details (helper names, HTTP path, CI YAML shape) | **Deferred** | Implementation Plan — not architectural forks |

---

## 4. Boundary validation

| Boundary | Crossed? | Evidence |
|---|---|---|
| Computation / Projection | **No** | AR-09 rejects knowledge/session-mutating health |
| Orchestration (P-04) | **No** | AR-11 process drain; AR-12 rejects graph shutdown nodes |
| Ownership | **No** | Logging/telemetry do not become domain writers |
| Immutability | **No** | No frozen-model changes |
| Replay | **No** | Out of scope |
| Presentation | **No** | Not UI-bearing |

---

## 5. Risk resolution

| ID | Resolution |
|---|---|
| R-01 | Mitigated by AR-02; CAR re-check |
| R-02 | Closed by AR-11 / AR-12 (no graph orchestration) |
| R-03 | Closed by AR-09 |
| R-04 | Constrained: logging must not alter control flow or swallow failures (P-06); Impl Plan + tests |
| R-05 | Mitigated by AR-05 / AR-07 |
| R-06 | Closed by AR-16 / AA-07 VERIFIED |
| R-07 | Closed by AR-14 / AR-15 |
| R-08 | Closed by AR-03 / AR-04 |

---

## 6. Assumption dispositions

| ID | Status after Review |
|---|---|
| AA-01 | VERIFIED |
| AA-02 | VERIFIED |
| AA-03 | VERIFIED |
| AA-04 | VERIFIED |
| AA-05 | VERIFIED |
| AA-06 | VERIFIED (CAR duty retained) |
| AA-07 | **VERIFIED** (AR-16) |

---

## 7. Discovery M-01–M-07 disposition

| ID | Disposition |
|---|---|
| M-01 | **Accepted** — infra structured-log helper; nodes emit required fields (AR-05) |
| M-02 | **Accepted** — readiness; side-effect-free probes (AR-08, AR-09) |
| M-03 | **Accepted** — process-level SIGTERM drain (AR-11); graph shutdown **Rejected** (AR-12) |
| M-04 | **Accepted** — health gates deploy (AR-10); wiring detail deferred (AR-18) |
| M-05 | **Accepted** — Settings sole config/secrets source (AR-03, AR-04) |
| M-06 | **Accepted** — EPIC-10 at release gate (AR-16) |
| M-07 | **Accepted** — runbook/policy only (AR-14) |

---

## 8. ADR assessment

**ADR required: NO**

No constitutional boundary is crossed by the accepted architecture. Process-level shutdown and side-effect-free readiness stay inside existing ARC-01 rules without exemption.

**Architecture Freeze document:** Superseded by explicit Freeze activity — see `EPIC-08-ARCHITECTURE-FREEZE.md` (APPROVED).  
**ADR / Freeze update:** None (ADR still not required).

---

## 9. Category validation

**Category A — confirmed.**

No Domain Contracts, Data Model, frozen-model, `InterviewState`, or LangGraph topology changes are authorized.

---

## 10. Findings

### Observations (non-blocking)

- O-01: CAR must prove zero HF leakage into Domain / LangGraph / `InterviewState` / frozen models.
- O-02: Implementation must keep health probes free of session mutation and knowledge computation.
- O-03: Structured log fields must be sufficient for EPIC-09 latency measurement.
- O-04: EPIC-10 remains a release-gate dependency for deploy-artifact dead-code purity.

### Blocking findings

- None.

---

## 11. Review verdict

**APPROVED WITH OBSERVATIONS**

---

## 12. Open issues

- None architectural. Implementation Plan may detail mechanisms under AR-18 without reopening architecture.

---

## 13. Next activity

**Implementation Plan** (Category A) — commit boundaries and phases for config, structured logging, LLM telemetry certification, readiness + CI gate, process shutdown, runbooks — against decisions AR-01–AR-18.
