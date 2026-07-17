# EPIC-08 — Deployment & Operations

**Status:** IMPLEMENTATION COMPLETE — ready for Checkpoint C
**Date:** 2026-07-18
**Epic ID:** EPIC-V13-08
**Playbook Category:** Category A — Standard Epic
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-08; Product Goal P-08
**Roadmap Phase:** Phase 4 — Production Readiness
**Precondition:** EPIC-V13-07 CLOSED; working tree clean at initialization.
**Regression baseline (initialization):** 7003 passed / 0 failed.
**EPIC-08 implementation baseline (pre-P1):** 7003 passed / 0 failed.
**Regression baseline (current):** 7417 passed / 0 failed (after P7 / C17 certification).
**Planning:** Initialization COMPLETE
**Architecture Discovery:** `EPIC-08-ARCHITECTURE-DISCOVERY.md` — **COMPLETE**
**Architecture Review:** `EPIC-08-ARCHITECTURE-REVIEW.md` — **APPROVED WITH OBSERVATIONS**
**Formal ADR:** **SKIP** (ADR required: NO)
**Domain Contracts:** N/A (Category A)
**Data Model:** N/A (Category A)
**Architecture Freeze:** `EPIC-08-ARCHITECTURE-FREEZE.md` — **APPROVED**
**Implementation Plan:** `EPIC-08-IMPLEMENTATION-PLAN.md` — **ACCEPTED** (7 phases / 17 commits)
**Implementation:** **COMPLETE** (P1–P7; C1–C17) — ready for Checkpoint C
**Playbook:** V13 Development Playbook Version 1.0

---

## 1. EPIC Identification

| Field | Value |
|---|---|
| **Identifier** | EPIC-V13-08 |
| **Title** | Deployment & Operations |
| **Master Plan reference** | `V13-PRODUCT-MASTER-PLAN.md` §4 EPIC-V13-08; Product Goal **P-08** |
| **Category** | **Category A** — Standard Epic |
| **Phase** | Phase 4 — Production Readiness |
| **Category rationale** | Does not introduce or substantially change domain contracts, persistent artifacts, builders, immutable models, report/replay/longitudinal structures, `InterviewState` ownership, or serialization/`schema_version` shape. Scope is configuration, observability, health, process lifecycle, and operational runbooks for an **existing** Hugging Face Spaces deployment. Escalate to Category B only if Discovery proves stored-shape, state-ownership, or frozen-domain changes. |

---

## 2. Scope

Industrialize, harden, and operationalize the **existing** production deployment on Hugging Face Spaces.

In scope (Master Plan):

- Environment-parameterised configuration (`settings.py` fully environment-driven; no hardcoded paths or API keys).
- Structured logging (every node emits structured log events with `session_id`, node name, duration, outcome).
- Health endpoint (readiness: LLM connectivity, database connectivity, execution sandbox).
- Graceful shutdown (in-flight sessions handled on SIGTERM).
- LLM call observability (per-call token usage, latency, model tier — extend V1.2 cost telemetry).
- Deployment runbook (local, staging, production) for the current HF Spaces-based deployment model.
- Database migration runbook (SQLite schema versioning policy from V1.2 extended).

**Architectural confinement (binding):** Platform-specific behaviour (Hugging Face Spaces) must remain confined to infrastructure. No deployment-platform dependency may leak into Domain, runtime orchestration, LangGraph, `InterviewState`, or frozen models.

Concrete mechanisms (logging adapters, health probe design, shutdown drain strategy) are deferred to Architecture Discovery / Architecture Review — this Overview remains architecture-neutral on solutions.

---

## 3. Goals

| ID | Goal |
|---|---|
| G-01 | Deploy to the existing production environment with zero manual configuration beyond environment variables / platform secrets. |
| G-02 | An operator can diagnose a session failure from structured logs alone. |
| G-03 | Health endpoint is active and used as a CI deployment gate. |
| G-04 | SIGTERM handling verified for in-flight sessions. |
| G-05 | Deployment and database migration runbooks documented and reviewed for the HF Spaces operational model. |
| G-06 | LLM call observability complete enough to support EPIC-V13-09 latency measurement. |

---

## 4. Non-Goals

| ID | Non-goal |
|---|---|
| NG-01 | Designing or migrating to a new deployment platform |
| NG-02 | Container orchestration (Kubernetes, ECS) |
| NG-03 | Autoscaling |
| NG-04 | Multi-region deployment |
| NG-05 | SaaS billing / subscription management |
| NG-06 | Performance SLO validation (EPIC-V13-09) |
| NG-07 | Final dead-code / PAT cleanup audit (EPIC-V13-10) |

---

## 5. Known Inputs

Inventory of **already existing** artifacts for Architecture Discovery to inspect. No decisions, analysis, or design alternatives.

### Deployment / platform (existing)

- Production application deployment on **Hugging Face Spaces** (operational).
- Existing Space configuration surface (environment / secrets as provisioned today).
- Existing local / CI invocation paths used to build and push the Space artifact.

### Configuration (existing)

- `settings.py` and current environment / settings loading paths.
- Existing API key, path, and environment assumptions present in configuration.

### Observability (existing)

- V1.2 LLM cost telemetry (token usage / related hooks — partial relative to Master Plan target).
- Existing logging call sites and log formats used by nodes / services.

### Persistence (existing)

- SQLite persistence paths used in production/local.
- V1.2 SQLite schema versioning policy and migration artifacts.

### Runtime / process (existing)

- Application process entrypoint(s) used on Hugging Face Spaces.
- LangGraph node surface (instrumentation targets for structured logging).
- Execution sandbox connectivity surface (health probe target).
- LLM connectivity surface (health probe / observability target).

### Governance (existing)

- `ARC-01-ARCHITECTURE-CONSTITUTION.md`
- `V13-PRODUCT-MASTER-PLAN.md` §4 EPIC-V13-08; §5 Go-Live Engineering/Documentation items for deploy/ops
- `V13-DEVELOPMENT-PLAYBOOK.md` Version 1.0
- Prior epic closure baseline: EPIC-V13-07 CLOSED; regression 7003 / 0

---

## 6. Assumptions Register

| ID | Description | Status | Verification Document | Notes |
|---|---|---|---|---|
| AA-01 | No new `InterviewState` fields are required for logging, health, or shutdown. | VERIFIED | `EPIC-08-ARCHITECTURE-DISCOVERY.md` | Escalate to Category B if invalidated later |
| AA-02 | Health payload and structured log event shapes remain infrastructure contracts, not domain `frozen` models. | VERIFIED | `EPIC-08-ARCHITECTURE-DISCOVERY.md` | |
| AA-03 | Extending SQLite schema versioning policy does not change on-disk `schema_version` / stored shape in this epic. | VERIFIED | `EPIC-08-ARCHITECTURE-DISCOVERY.md` | Invalidate → Category B + Data Model |
| AA-04 | LLM observability extends existing V1.2 cost telemetry ownership paths (no dual writers). | VERIFIED | `EPIC-08-ARCHITECTURE-DISCOVERY.md` | |
| AA-05 | Hugging Face Spaces remains the sole production deployment target for V1.3. | VERIFIED | This Overview (Known Inputs) | User-confirmed; platform migration out of scope |
| AA-06 | Platform-specific HF behaviour can be confined to infrastructure without Domain/LangGraph/`InterviewState` leakage. | VERIFIED | `EPIC-08-ARCHITECTURE-DISCOVERY.md` | CAR must re-check leakage |
| AA-07 | EPIC-V13-10 dead-code cleanup is a release-gate concern, not a hard blocker for EPIC-08 feature freeze. | VERIFIED | `EPIC-08-ARCHITECTURE-REVIEW.md` AR-16 | Release gate / EPIC-10 |

---

## 7. Risks Register

| ID | Risk | Severity | Mitigation direction (non-design) |
|---|---|---|---|
| R-01 | HF-specific APIs or env conventions leak into Domain / LangGraph / `InterviewState` | High | Enforce infrastructure confinement; Architecture Review + CAR |
| R-02 | Graceful shutdown appears to require out-of-graph session orchestration | High | Flag Orchestration Boundary; ADR only if boundary must be crossed |
| R-03 | Health probes invoke LLM or mutate session/DB state | Medium | Discovery must classify probe side effects |
| R-04 | Structured logging changes control flow or silences failures | High | Align with ARC-01 P-06; no silent fallbacks |
| R-05 | Incomplete log fields block EPIC-V13-09 SLO work | Medium | Keep G-06 explicit in Review exit criteria |
| R-06 | EPIC-10 dependency vs Phase 4/5 sequencing ambiguity | Medium | Resolve AA-07 in Architecture Review |
| R-07 | Schema policy work accidentally becomes a data-model change | Medium | AA-03 gate; category reclassification if needed |

---

## 8. Current Deployment Assessment (Hugging Face)

| Aspect | Assessment |
|---|---|
| Platform | Application **already deployed** and **operational** on Hugging Face Spaces |
| Epic posture | Harden / industrialize existing deploy — **not** greenfield platform design |
| Platform migration | **Out of scope** |
| Configuration maturity | Exists; Master Plan requires full environment-parameterisation (no hardcoded paths/keys) |
| Observability maturity | Partial (V1.2 cost telemetry); structured per-node logging incomplete vs go-live |
| Health / CI gate | Not yet established as Master Plan go-live gate |
| Shutdown | SIGTERM / in-flight session handling not yet certified |
| Runbooks | Deployment + DB migration runbooks required for HF operational model |
| Layering | Platform specifics must stay in infrastructure |

---

## 9. Gap Analysis (Current vs Target)

| Area | Current | Target (EPIC-08) |
|---|---|---|
| Deploy platform | HF Spaces operational | Same platform; hardened ops |
| Configuration | Settings exist; not fully certified env-driven | Fully environment-driven; zero manual config beyond secrets/env |
| Logging | Incomplete structured node events | Every node: `session_id`, node, duration, outcome |
| LLM observability | Partial V1.2 telemetry | Per-call token usage, latency, model tier |
| Health | Not CI deployment gate | Readiness for LLM, DB, sandbox; CI gate |
| Shutdown | Not certified | Graceful SIGTERM; in-flight sessions handled |
| Deploy runbook | Incomplete vs go-live | Local / staging / production for HF model |
| DB migration runbook | V1.2 policy exists | Extended policy + tested runbook |
| Deploy artifact purity | EPIC-01 closed; EPIC-10 pending | No legacy in artifact; dead code addressed per Master Plan dependency resolution |

---

## 10. Category Confirmation

**Confirmed: Category A — Standard Epic.**

| Criterion | Applies? |
|---|---|
| New/changed domain contracts | No (assumed; AA-01–AA-03) |
| New/changed persistent / serialization shape | No (assumed; AA-03) |
| Report / replay / longitudinal / `InterviewState` ownership | No (assumed; AA-01) |
| Ops: settings, logging, health, shutdown, runbooks on existing HF deploy | Yes |

**Mandatory Category A workflow:** Master Plan → Architecture Review → conditional ADR → Implementation → CAR → Regression → Documentation → FR → Epic Close.

**Reclassification trigger:** Any invalidated AA that requires frozen domain models, `InterviewState` ownership changes, or stored-shape / `schema_version` changes → Category B before Architecture Freeze / Implementation.

---

## 11. Dependencies

### Master Plan dependencies

| EPIC | Role | Notes |
|---|---|---|
| EPIC-V13-01 | Deploy artifact free of legacy scoring paths | CLOSED (context) |
| EPIC-V13-10 | No dead code in deployed build | Phase 5 — sequencing vs 08 close tracked as AA-07 / R-06 |

### Sequencing (Master Plan Phase 4)

- Environment configuration work may proceed under feature-stable Phase 3 baseline (satisfied: EPIC-07 CLOSED).
- Health endpoint and graceful shutdown require Phase 3 feature stability — satisfied.

### Downstream

| EPIC | Dependency on EPIC-08 |
|---|---|
| EPIC-V13-09 | Structured logging required for latency measurement |

### Inherited context (not Master Plan blockers)

| Item | Notes |
|---|---|
| EPIC-V13-07 | CLOSED; UX production baseline |
| V1.2 cost telemetry | Extension target for LLM observability |
| V1.2 SQLite schema versioning | Extension + runbook target |

---

## 12. Success Criteria

Aligned with Master Plan expected outcome and §5 Go-Live Engineering/Documentation items owned by this epic:

- [x] Environment-parameterised configuration: no hardcoded paths, keys, or environment assumptions.
- [x] Structured logging: every node emits structured events with `session_id`, node name, duration, outcome.
- [x] Health endpoint active and used as CI deployment gate.
- [x] Graceful shutdown verified under SIGTERM.
- [x] LLM call observability: per-call token usage, latency, model tier.
- [x] Deployment runbook complete and reviewed (HF Spaces operational model; local / staging / production).
- [x] Database migration runbook documented and tested.
- [x] Platform-specific HF behaviour confined to infrastructure (no Domain / LangGraph / `InterviewState` / frozen-model leakage).
- [x] Full regression suite green at implementation certification (7417 / 0; ≥ baseline 7003). Epic-close regression re-run remains a later workflow gate.

---

## 12A. Production-Readiness Certification (P7 / C17)

**Date:** 2026-07-18  
**Scope:** Documentation + verification only (no production code).  
**Verdict:** **PASS** — EPIC-08 implementation complete; ready for Checkpoint C → CAR.

### Freeze §13 / Master Plan P-08 mapping

| Criterion | Evidence | Status |
|---|---|---|
| Settings exclusive; no production `os.environ` | C1–C3; `test_epic08_config_architecture.py`; C16 hardening | **PASS** |
| Structured logging schema per OBS rules | C4–C6; node coverage + emission gates | **PASS** |
| LLM observability via existing path (tokens, latency, model) | C7–C8; ObservingLLMAdapter / bridge; C16 single-path | **PASS** |
| Readiness health active; CI/deploy gated | C9–C11; `GET /health/ready`; readiness gate | **PASS** |
| SIGTERM process drain verified | C12–C13; topology freeze (IB-05) | **PASS** |
| Deployment + DB migration runbooks (HF; policy only) | C14–C15; `docs/ops/` | **PASS** |
| Zero HF leakage (Domain / LangGraph / InterviewState / contracts) | C3 + C16 O-01 surfaces | **PASS** |
| Full regression ≥ baseline | C17 suite: **7417 passed / 0 failed** (baseline 7003) | **PASS** |
| AR-16 — EPIC-10 dead-code purity | Explicitly **not** required to close EPIC-08 implementation | **N/A (deferred)** |

### Architectural gates (still green)

| Gate | Result |
|---|---|
| Config / HF confinement (C3) | Green |
| LLM telemetry single path (C8) | Green |
| Health side-effect-free (C9) | Green |
| Readiness CI gate (C11) | Green |
| Topology / shutdown invariants (C13) | Green |
| P7 hardening (C16) | Green (16 tests) |
| Aggregated arch gate run (C17) | **350 passed / 0 failed** |

### Explicit exclusions (by Freeze)

- EPIC-10 dead-code purge (AR-16) — release gate / EPIC-10
- EPIC-09 SLO validation — downstream consumer
- Checkpoint C / CAR / FR / Epic Close — **not** part of C17

---

## 13. Status

| Workflow step | Status |
|---|---|
| Initialization (this document) | **COMPLETE** |
| Architecture Discovery (formal artifact) | **COMPLETE** |
| Architecture Review | **APPROVED WITH OBSERVATIONS** |
| ADR (conditional) | **SKIP** (not required) |
| Architecture Freeze | **APPROVED** |
| Implementation Plan | **ACCEPTED** (`EPIC-08-IMPLEMENTATION-PLAN.md`) |
| Implementation | **COMPLETE** (P1–P7; C1–C17) — ready for Checkpoint C |
| Checkpoint A | **PASS** (2026-07-18) — Macro B (P4–P5) authorized |
| Checkpoint B | **PASS** (2026-07-18) — Macro C (P6–P7) authorized |
| Checkpoint C | **PENDING** |
| CAR / Regression / FR / Epic Close | NOT STARTED |

---

## 14. Next Activities

1. **Architecture Checkpoint C** (after P7 / C17) — authorize CAR per `EPIC-08-IMPLEMENTATION-PLAN.md`.
2. **Do not** create Domain Contracts, Data Model, or ADRs unless category is reclassified to B or a boundary crossing is newly evidenced.
