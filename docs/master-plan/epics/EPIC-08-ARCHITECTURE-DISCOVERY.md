# EPIC-08 — Architecture Discovery

**Status:** COMPLETE  
**Date:** 2026-07-18  
**Epic ID:** EPIC-V13-08  
**Playbook Category:** Category A — Standard Epic (confirmed)  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-08; Product Goal P-08  
**Living Overview:** `EPIC-08-OVERVIEW.md`  
**Playbook:** V13 Development Playbook Version 1.0  
**Regression baseline:** 7003 passed / 0 failed  

**Authority:** Findings-only analysis. Does not freeze decisions. Does not authorize implementation.

---

## 1. Purpose

Analyze current Hugging Face Spaces deployment and operational architecture against Master Plan EPIC-08 targets. Identify gaps, constraints, risks, and whether Category A remains valid.

---

## 2. Current architecture assessment

| Subsystem | Location / evidence | Capability |
|---|---|---|
| Process entrypoint | `app.py` | HF Spaces Docker CMD target; corpus ensure; Gradio `launch` on `0.0.0.0` / `PORT` |
| Space metadata | `spaces.yml` | `sdk: docker` |
| Container build | `Dockerfile` | Python 3.11; exposes 7860; `CMD python app.py` |
| Configuration | `infrastructure/config/settings.py` | `pydantic_settings.BaseSettings`; `.env` + env; `OPENAI_API_KEY` required at construct |
| Secrets | Env / Space secrets | `openai_api_key`, `hf_token` / `HF_TOKEN` / `HUGGINGFACE_TOKEN` (entrypoint also reads HF token outside Settings) |
| Logging | `app/core/logger.py` | `logging.basicConfig` text format — not structured node events |
| LLM observability | `infrastructure/llm/observability/*`, metrics collector | Per-call latency, tokens, model via `ObservingLLMAdapter` / `LLMCallMetric` |
| Persistence | `infrastructure/persistence/sqlite/*` | SQLite connection + repositories |
| Execution sandbox | infrastructure execution surface | Exists (health target) |
| Graph nodes | `app/graph/nodes/*` | Ad hoc `logger.*` calls; no uniform `session_id` / duration / outcome schema |
| CI | `.github/workflows/ci.yml` | Lint + pytest; **no** health/readiness deploy gate |
| Runbooks | — | **None** found |
| Health endpoint | — | **None** found |
| SIGTERM / graceful drain | — | **None** found |

**Layering note:** HF-specific startup (`ensure_corpus`, Spaces entrypoint) already lives at process edge (`app.py`). Domain / LangGraph / `InterviewState` show no HF platform types in inspected deploy path.

---

## 3. Current deployment assessment (Hugging Face)

| Aspect | Finding |
|---|---|
| Platform | HF Spaces, Docker SDK — **operational** (Known Input) |
| Workflow | Build image from `Dockerfile` → Space runs `app.py` |
| Startup | Logging configure → corpus ensure (HF token) → Gradio build → bind port |
| Restart | Platform container restart; no app-level drain/handshake observed |
| Secrets | Platform env/secrets; Settings validates OpenAI key |
| Portability | Docker + env-driven Settings; defaults for models/thresholds in Settings |
| Epic posture | Harden existing deploy — **not** platform redesign |

---

## 4. Gap analysis (current vs target)

| Area | Current | Target | Gap |
|---|---|---|---|
| Configuration | Settings env-backed; some dual token read paths; defaults in code | Fully env-parameterised; no hardcoded paths/keys; zero manual config beyond secrets/env | Audit remaining hardcoded paths/assumptions; unify secret/env surface |
| Structured logging | Text logger; uneven node logs | Every node: `session_id`, node, duration, outcome | Uniform structured emission missing |
| LLM observability | Adapter records latency/tokens/model | Same fields certified + operator-diagnosable | Extend/certify coverage; align with node logging for EPIC-09 |
| Health | Absent | Readiness: LLM, DB, sandbox; CI gate | Endpoint + CI wiring missing |
| Graceful shutdown | Absent | SIGTERM; in-flight sessions handled | Process lifecycle missing |
| Deploy runbook | Absent | Local / staging / production (HF model) | Documentation missing |
| DB migration runbook | SQLite present; no ops runbook | Extended V1.2 policy + tested runbook | Policy/runbook missing (not evidence of schema rewrite) |
| Release process | CI tests only | Health gates deploy | Deploy gate missing |
| Platform confinement | Entrypoint is HF-aware | Stay in infrastructure / process edge | Must not expand into Domain/graph/state |

---

## 5. Dependency analysis

| Dependency | Status | Discovery finding |
|---|---|---|
| EPIC-V13-01 (no legacy in artifact) | CLOSED (context) | No Discovery evidence blocking ops hardening |
| EPIC-V13-10 (no dead code) | Phase 5 | Sequencing ambiguity remains (AA-07); not evidence of Category B |
| Phase 3 stability | Satisfied (EPIC-07 CLOSED) | Health/shutdown may proceed |
| V1.2 cost telemetry | Present in infrastructure | Extension path exists |
| EPIC-V13-09 | Downstream | Requires structured logging fields for latency |

---

## 6. Risk analysis

| ID | Risk | Severity | Constitutional angle |
|---|---|---|---|
| R-01 | HF APIs/env leak into Domain / LangGraph / `InterviewState` | High | Layering / Presentation & ownership discipline |
| R-02 | Shutdown implemented as out-of-graph session orchestration | High | **Orchestration Boundary** (P-04) — ADR only if crossed |
| R-03 | Health probes call LLM or mutate DB/session | Medium | **Computation/Projection** if knowledge computation; side effects |
| R-04 | Logging swallows errors or changes control flow | High | P-06 silent-fallback ban |
| R-05 | Incomplete logs block EPIC-09 | Medium | Product sequencing |
| R-06 | EPIC-10 vs 08 close ambiguity | Medium | Process |
| R-07 | “Schema versioning extended” becomes stored-shape change | Medium | Category B trigger if evidenced |
| R-08 | Dual config paths (`Settings` vs raw `os.environ` in entrypoint) reduce reproducibility | Low | Ops hygiene |

---

## 7. Assumption validation

| ID | Description | Discovery status | Evidence |
|---|---|---|---|
| AA-01 | No new `InterviewState` fields for logging/health/shutdown | **VERIFIED** | No gap requires state fields; ops are process/infra |
| AA-02 | Health/log shapes stay infrastructure contracts | **VERIFIED** | `LLMCallMetric` already infra; no domain model gap evidenced |
| AA-03 | Schema policy extension does not change on-disk shape in this epic | **VERIFIED** | Master Plan asks runbook/policy; no stored-shape requirement evidenced |
| AA-04 | LLM observability extends existing telemetry paths | **VERIFIED** | `ObservingLLMAdapter` / collector present |
| AA-05 | HF Spaces sole production target | **VERIFIED** | Known Input + `spaces.yml` / `app.py` |
| AA-06 | HF behaviour confinable to infrastructure | **VERIFIED** (with CAR duty) | Current HF touch is process edge; must remain so |
| AA-07 | EPIC-10 not hard blocker for 08 feature freeze | **UNVERIFIED** | Sequencing/policy — Architecture Review |

**Component Inventory:** N/A (not UI-bearing).

---

## 8. Constitutional boundary scan

| Boundary | May EPIC-08 cross? | Finding |
|---|---|---|
| Computation / Projection | Avoid | Health must not assemble knowledge; prefer connectivity checks without session computation |
| Orchestration | Avoid | Shutdown/drain must not become graph routing outside LangGraph |
| Ownership | Avoid | Logging/telemetry must not dual-write domain artifacts |
| Immutability | No | No frozen-model mutation evidenced as required |
| Replay | No | Out of scope |
| Presentation | No | Not UI-bearing |

**ADR trigger (conditional, later):** only if Review concludes shutdown or health **must** cross Orchestration or Computation/Projection boundaries. No ADR required by Discovery evidence alone.

---

## 9. Category validation

**Confirmed: Category A.**

No evidence that EPIC-08 requires changes to Domain Contracts, Data Model, frozen models, `InterviewState` ownership, or LangGraph orchestration topology.

**Reclassify to B only if** later work evidences stored-shape/`schema_version` change, new `InterviewState` fields, or new frozen domain artifacts.

---

## 10. Confirmed vs missing decisions

### Confirmed (reuse / Master Plan)

- Production platform = Hugging Face Spaces (no migration).
- Platform-specific code confined to infrastructure / process edge.
- Extend V1.2 LLM observability; do not invent parallel telemetry ownership.
- Category A workflow applies.

### Missing (Architecture Review must resolve — not frozen here)

- M-01: Structured logging emission mechanism (infra helper vs per-node) without new orchestration.
- M-02: Health probe semantics (liveness vs readiness; side-effect rules for LLM/DB/sandbox).
- M-03: SIGTERM drain policy that preserves P-04 (no out-of-graph routing).
- M-04: CI health-gate wiring relative to HF Spaces release flow.
- M-05: Env/secret surface unification (`Settings` vs entrypoint `os.environ`).
- M-06: AA-07 — EPIC-10 vs EPIC-08 close criteria.
- M-07: DB migration runbook contents (policy extension without schema rewrite).

---

## 11. Recommended architecture decisions (for Review — not ADRs)

1. Keep all HF Spaces specifics in process entrypoint / infrastructure adapters.
2. Treat structured log events and health payloads as infrastructure contracts.
3. Extend existing `ObservingLLMAdapter` metrics path for LLM observability completeness.
4. Prefer process-level graceful shutdown over new LangGraph control-flow nodes unless Review proves otherwise (ADR if orchestration boundary crossed).
5. Limit schema work to operational runbook / versioning **policy**; reject silent on-disk shape changes in this epic.
6. Defer EPIC-10 dead-code purity to release gate unless Review overturns AA-07.

---

## 12. Recommended next activity

**Architecture Review** (Category A) — resolve M-01–M-07; declare conditional ADR need; authorize Implementation Plan when no open architectural questions remain.

Do **not** author Domain Contracts, Data Model, Architecture Freeze, or ADRs unless Review finds a genuine unresolved boundary decision or Category B trigger.
