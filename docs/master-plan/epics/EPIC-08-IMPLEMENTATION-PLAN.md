# EPIC-08 — Implementation Plan

**Status:** ACCEPTED (planning complete; implementation authorized after pre-P1 baseline)  
**Date:** 2026-07-18  
**Epic ID:** EPIC-V13-08  
**Playbook Category:** Category A — Standard Epic  
**Master Plan Reference:** V13-PRODUCT-MASTER-PLAN.md §4 EPIC-V13-08; Product Goal P-08  
**Governing Freeze:** `EPIC-08-ARCHITECTURE-FREEZE.md` (APPROVED)  
**ADR required:** NO  
**Domain Contracts / Data Model:** N/A  
**Playbook:** V13 Development Playbook Version 1.0 (§2 Implementation Dependency Validation; §8.6 DoD)

---

## 1. Preflight

| Item | Value |
|---|---|
| Working tree at plan authoring | Clean |
| HEAD | `35d152b` — docs(epic-08): freeze Deployment & Operations architecture |
| Architecture Freeze | APPROVED |
| Formal ADR | SKIP |
| Domain Contracts / Data Model | N/A (Category A) |
| Regression baseline (epic init) | 7003 passed / 0 failed |
| Pre-P1 gate | **DONE** — EPIC-08 implementation baseline recorded in Overview: 7003 passed / 0 failed |
| Platform | Hugging Face Spaces only (AR-01) |

---

## 2. Planning assumptions

| ID | Assumption | Freeze anchor |
|---|---|---|
| PA-01 | No `InterviewState`, Domain, frozen-model, or LangGraph topology changes | Boundary validation §14; SDN-03/04; IB-05 |
| PA-02 | Settings is exclusive runtime config entrypoint; production `os.environ` eliminated | CFG-01–CFG-05; AR-03/04 |
| PA-03 | Structured log schema fields frozen in Freeze §6.1; names stable for EPIC-09 | OBS-01–OBS-05; AR-05 |
| PA-04 | LLM telemetry extends existing `ObservingLLMAdapter` / collector only | AR-07; OBS-04; rejects AR-06 |
| PA-05 | Health = side-effect-free readiness (LLM, DB, sandbox); CI/deploy gate | HLT-01–HLT-06; rejects AR-09 |
| PA-06 | Shutdown = process-edge SIGTERM drain only | SDN-01–SDN-04; rejects AR-12 |
| PA-07 | DB migration runbook = policy extension only; no on-disk shape / `schema_version` bump | AR-14; rejects AR-15 |
| PA-08 | EPIC-10 dead-code purity is release-gate, not EPIC-08 blocker | AR-16 |
| PA-09 | HTTP path, CI YAML shape, helper module names are Implementation Plan choices (AR-18) | AR-18 |
| PA-10 | Category A preserved; no ADR / Domain Contracts / Data Model unless reclassified | AR-17 |

---

## 3. Governing constraints (non-negotiable)

- Trace every change to Freeze AR/CFG/OBS/HLT/SDN/IB rules.
- No new architecture, runtime ownership, persistence, domain contracts, or data model.
- Zero Known Failing Tests at every commit and phase end.
- ARC-01: P-01, P-04, P-06; no silent fallbacks; no dual ownership of telemetry.
- HF / platform behaviour confined to infrastructure / process edge (`app.py`, infra adapters).
- Logging must not alter control flow or swallow failures (OBS-03).
- Mechanism details below are wiring only — not architectural forks.

---

## 4. Implementation phases (scope)

### Macro phase map

| Macro | Phases | Checkpoint |
|---|---|---|
| **A — Config & observability** | P1, P2, P3 | Checkpoint A after P3 |
| **B — Runtime ops edge** | P4, P5 | Checkpoint B after P5 |
| **C — Docs & hardening** | P6, P7 | Checkpoint C after P7 → CAR |

---

### P1 — Configuration unification

**Objective:** Exclusive Settings-driven runtime configuration; no production dual env reads.  
**In scope:** Complete/extend `infrastructure/config/settings.py`; migrate production readers; platform confinement; arch tests CFG-01–05.  
**Out of scope:** Logging schema; health; shutdown; runbooks; LLM telemetry fields.  
**Depends on:** Pre-P1 baseline.  
**Freeze:** AR-03, AR-04, CFG-01–CFG-05, IB-01, IB-02.

---

### P2 — Structured logging

**Objective:** Infrastructure emission helper + every LangGraph node emits frozen schema fields.  
**In scope:** Sole emission helper; node instrumentation (`session_id`, `graph_node`, `duration_ms`, `status` + stable schema); tests OBS-01–03, OBS-05.  
**Out of scope:** LLM token/latency ownership path (P3); health; shutdown.  
**Depends on:** P1 (Settings for log level / sinks if configured).  
**Freeze:** AR-05, OBS-01–OBS-03, OBS-05, IB-03, IB-05.

---

### P3 — LLM observability extension

**Objective:** Per-call tokens, latency, model via existing observing path; EPIC-09-ready fields.  
**In scope:** Extend `ObservingLLMAdapter` / collector; emit `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, latency via helper; no second writer.  
**Out of scope:** New telemetry ownership; SLO validation (EPIC-09); graph changes.  
**Depends on:** P2 (emission helper).  
**Freeze:** AR-07, OBS-04, OBS-05; rejects AR-06.

---

### P4 — Health & readiness

**Objective:** Side-effect-free readiness endpoint; CI/deploy gate.  
**In scope:** Probes for LLM connectivity, DB connectivity, execution sandbox; process-edge HTTP exposure; CI gate wiring.  
**Out of scope:** Probe designs that mutate session/DB or run interview/knowledge LLM cycles; LangGraph execution in probes.  
**Depends on:** P1 (Settings for probe targets/timeouts). P2 optional for structured health events.  
**Freeze:** AR-08, AR-10, HLT-01–HLT-06; rejects AR-09.

**Wiring (AR-18):** Readiness HTTP path `GET /health/ready` (process edge). CI gate: fail deploy job if readiness ≠ success.

---

### P5 — Graceful shutdown

**Objective:** Process-level SIGTERM drain for in-flight work; no graph/orchestration changes.  
**In scope:** SIGTERM handler / drain at process edge; reject new requests during drain; allow in-flight to finish within timeout from Settings; tests.  
**Out of scope:** New LangGraph nodes/edges/routers; out-of-graph session orchestration.  
**Depends on:** P1 (drain timeout Settings).  
**Freeze:** AR-11, SDN-01–SDN-04; rejects AR-12.

---

### P6 — Operational documentation

**Objective:** Deployment + DB migration runbooks for HF Spaces model.  
**In scope:** Local / staging / production deploy runbook; SQLite schema **versioning policy** extension + operator steps; reproducibility note (same image + Settings/env).  
**Out of scope:** On-disk schema / `schema_version` changes; platform migration.  
**Depends on:** P1–P5 behaviour stable enough to document accurately (ordered after P5).  
**Freeze:** AR-13, AR-14; rejects AR-15.

---

### P7 — Hardening & production readiness

**Objective:** Architecture verification, full regression, production-readiness checklist.  
**In scope:** Arch tests (HF confinement, no Domain/LangGraph/`InterviewState` leakage, no dual telemetry, health side-effect-free, no graph topology drift); full regression; readiness checklist vs Freeze §13 / Master Plan P-08.  
**Out of scope:** EPIC-10 dead-code purge; EPIC-09 SLOs.  
**Depends on:** P1–P6.  
**Freeze:** Success criteria §13; AR-16; Observation O-01 re-check at CAR.

---

## 5. Commit plan

Each commit: one logical concern; independently testable; suite green after apply.

| ID | Phase | Objective | Affected components | Expected tests | Acceptance criteria | Architectural constraints | Dependencies |
|---|---|---|---|---|---|---|---|
| **C1** | P1 | Extend Settings as exclusive runtime config surface (keys, paths, timeouts, feature flags needed by later phases) | `infrastructure/config/settings.py`; related loaders | Unit: required env missing → fail-fast; defaults only where Freeze allows; no hardcoded API keys | Settings loads all EPIC-08 runtime knobs from env/secrets | CFG-01, CFG-03–05; ARC-01 P-06 | Pre-P1 baseline |
| **C2** | P1 | Migrate production direct `os.environ` / dual env reads to Settings | Production callers under app/infra/runtime (not tests/tools allowlisted) | Unit/integration: callers use Settings; behaviour parity | No production dual entrypoint env reads | CFG-02, AR-04; IB-01 | C1 |
| **C3** | P1 | Arch test: production `os.environ` ban + HF confinement of config | Arch test modules | Arch: no production `os.environ` outside Settings / explicit process-edge allowlist; no HF imports in Domain/LangGraph | CFG-01–05 verified by test; suite green | IB-01, IB-02 | C1–C2 |
| **C4** | P2 | Infrastructure structured-log helper implementing Freeze §6.1 schema | New/extended infra logging module | Unit: required fields present; null/omit rules; emission does not raise into caller control flow | Sole emission path for schema exists | OBS-01, OBS-03, IB-03 | C3 |
| **C5** | P2 | Instrument LangGraph nodes (batch A — core interview cycle nodes) | Graph node modules (batch A) | Unit/integration: each instrumented node emits `session_id`, `graph_node`, `duration_ms`, `status` | Batch A nodes OBS-02 compliant; failures still surface | OBS-02, OBS-03; IB-05; no new edges | C4 |
| **C6** | P2 | Instrument remaining LangGraph nodes (batch B) + coverage gate | Remaining graph nodes | Same as C5 for batch B; inventory test: all production nodes covered | Every production LangGraph node emits required fields | OBS-02, OBS-05 | C5 |
| **C7** | P3 | Extend existing ObservingLLMAdapter / collector for latency + model (+ tokens if gaps) | Existing LLM observing adapter / collector only | Unit: per-call tokens, latency, model recorded; no alternate collector | AR-07 fields available on existing path | OBS-04; rejects AR-06; IB-04 | C4 |
| **C8** | P3 | Emit LLM schema fields via structured-log helper; EPIC-09 field compatibility | Adapter ↔ log helper bridge | Unit: `model`, token fields, `duration_ms` on LLM events; status/error_type on failure | OBS-04/05 satisfied; no dual-write of domain artifacts | OBS-04, OBS-05, IB-04 | C6, C7 |
| **C9** | P4 | Side-effect-free readiness probes (LLM, DB, sandbox) | Infra health probe modules | Unit: each probe success/failure; assert no session/DB mutation; no LangGraph invoke; no knowledge/interview LLM cycle | HLT-01–HLT-05 | HLT-*; rejects AR-09; P-01 | C1 |
| **C10** | P4 | Expose readiness at process edge `GET /health/ready` | `app.py` / process-edge HTTP | Integration: HTTP status + payload reflect probe aggregate; Settings-driven | Endpoint active; infra contract only (not domain frozen model) | AR-08, IB-01, IB-03 | C9 |
| **C11** | P4 | CI / deploy gate on readiness | CI workflow / deploy scripts | CI test or job step: non-ready fails gate | AR-10 satisfied | AR-10; AR-18 wiring | C10 |
| **C12** | P5 | Process-edge SIGTERM drain (stop admit; finish in-flight; timeout from Settings) | Process entrypoint / lifecycle | Unit/integration: SIGTERM starts drain; in-flight completes or times out observably; no new graph nodes | SDN-01–SDN-02 | SDN-*; rejects AR-12; P-04 | C1 |
| **C13** | P5 | Shutdown verification + regression at ops-edge boundary | Tests for drain; no topology drift assert | Tests prove drain; arch assert no new LangGraph nodes/edges/routers from EPIC-08 | SDN-03–SDN-04 | IB-05 | C12 |
| **C14** | P6 | Deployment runbook (local / staging / production HF Spaces) | Ops docs under `docs/` (runbook path chosen in commit; not Architecture Freeze) | Doc review checklist; optional link/smoke from CI docs job if present | AR-13; reproducibility note | AR-01, AR-13 | C10–C13 (accurate ops surface) |
| **C15** | P6 | DB migration runbook — versioning **policy** extension only | Ops docs; policy text referencing V1.2 SQLite versioning | Doc review; tests unchanged for on-disk shape | No schema/`schema_version` code change; AR-14 | Rejects AR-15 | C14 |
| **C16** | P7 | Arch hardening tests (HF confinement, telemetry single path, health side-effect-free, config ban) | Arch test suite | All P7 arch tests green | Freeze §13 structural items test-enforced | O-01 forward to CAR | C3, C8, C11, C13, C15 |
| **C17** | P7 | Production-readiness checklist + full regression certification | Checklist in Overview or plan status; no prod code | Full suite green ≥ baseline; checklist vs Freeze §13 / P-08 | Epic implementation complete; ready for CAR | AR-16 (EPIC-10 not required) | C16 |

**Wiring names (AR-18, non-architectural):**

| Concern | Plan choice |
|---|---|
| Readiness path | `GET /health/ready` |
| Structured log helper | Infrastructure module under `infrastructure/` (exact filename at C4; sole emission path) |
| CI gate | Deploy/CI job fails if readiness check fails |
| Runbook location | `docs/ops/` (create if absent) — deployment + DB migration runbooks |

---

## 6. Implementation order (authoritative)

1. Pre-P1: full regression → record EPIC-08 implementation baseline  
2. P1: C1 → C2 → C3  
3. P2: C4 → C5 → C6  
4. P3: C7 → C8  
5. **Checkpoint A** (authorize Macro B)  
6. P4: C9 → C10 → C11  
7. P5: C12 → C13  
8. **Checkpoint B** (authorize Macro C)  
9. P6: C14 → C15  
10. P7: C16 → C17  
11. **Checkpoint C** → CAR → Regression → Documentation → FR → Epic Close  

---

## 7. Dependency validation (Playbook §2)

| Check | Result |
|---|---|
| Every commit depends only on prior commits | **PASS** — see table Dependencies column |
| Every commit has executable test gate | **PASS** — unit/integration/arch/doc-review as listed |
| No circular dependencies | **PASS** — linear C1…C17 with Checkpoint gates |
| Suite can stay green after each commit | **PASS** — additive/migratory; no bridge-break removals planned |
| P3 (C7) before full node coverage (C6)? | **Ordered C7 after C4, C8 after C6** — adapter extension needs helper; log bridge needs node helper stable |
| P4 (C9) vs P2 | **C9 depends on C1 only** — may proceed after P1 if rescheduled; plan keeps observability-first for EPIC-09 field readiness before health docs |
| P6 after P5 | **Required** — runbooks document final ops surface |
| Hidden dep: CI gate (C11) needs endpoint (C10) | **Satisfied** |
| Hidden dep: C8 needs C7 + C4/C6 | **Satisfied** |

**Validation verdict:** Implementation Dependency Validation **PASSED**. No commit redesign required.

---

## 8. Dependency graph

```
Pre-P1 baseline
    → C1 → C2 → C3
              → C4 → C5 → C6 ─┐
              → C4 → C7 ──────┴→ C8
    C1 → C9 → C10 → C11
    C1 → C12 → C13
    C10–C13 → C14 → C15 → C16 → C17
```

**Parallelization (optional, same green-suite rules):**

| Pair | Parallel? | Note |
|---|---|---|
| C5 vs C7 | Yes after C4 | Node batch A vs adapter extension |
| C9 vs C5–C8 | Yes after C1 | Health probes independent of logging |
| C12 vs C9–C11 | Caution | Prefer C11 before C12 only if shared process-edge edits; sequential plan avoids merge conflict |
| C14 vs code | No | Docs after ops surface stable |

Authoritative order remains §6 if parallel not used.

---

## 9. Risk validation

| ID | Risk | Severity | Plan mitigation | Residual |
|---|---|---|---|---|
| R-01 | HF APIs leak into Domain/LangGraph/`InterviewState` | High | C3 + C16 arch tests; IB-01/02; CAR O-01 | CAR re-check |
| R-02 | Shutdown needs out-of-graph session orchestration | High | C12–C13 process-edge only; reject AR-12; Stopping Rule if boundary pressure | Stop → ADR if crossed |
| R-03 | Health probes mutate state / invoke LLM cycles | Medium | C9 side-effect tests; HLT-02–05 | None if tests hold |
| R-04 | Logging alters control flow / silences failures | High | OBS-03 tests in C4–C6; P-06 | None if tests hold |
| R-05 | Incomplete fields block EPIC-09 | Medium | C6/C8 enforce `duration_ms` + LLM latency fields | EPIC-09 consumes |
| R-06 | EPIC-10 vs EPIC-08 sequencing | Medium | AR-16; C17 checklist excludes EPIC-10 purge | Release gate |
| R-07 | Schema policy becomes data-model change | Medium | C15 docs-only; rejects AR-15; no migration code | Category B if invalidated |

**Risk validation verdict:** All Overview risks addressed by commit gates; no unmitigated P0 plan gap.

---

## 10. Regression strategy

| Gate | Action |
|---|---|
| Pre-P1 | Full suite → record EPIC-08 implementation baseline in Overview |
| End of each commit | Targeted tests for commit + no known failures |
| End of each phase | Full suite green |
| Checkpoint A/B/C | Full suite green + phase acceptance |
| Post-P7 / pre-CAR | Full suite + all P7 arch tests |
| Epic close | Full suite green; count ≥ baseline (new tests may increase total) |

---

## 11. Acceptance criteria

### Per-commit

See Commit plan table (Acceptance criteria column). Each commit independently verifiable.

### Per-phase

| Phase | Acceptance |
|---|---|
| P1 | Settings exclusive; production `os.environ` ban tested; suite green |
| P2 | All production LangGraph nodes emit structured events; OBS-01–03/05; suite green |
| P3 | Tokens, latency, model via existing observing path; schema fields for EPIC-09; suite green |
| P4 | `/health/ready` active; side-effect-free probes; CI gate; suite green |
| P5 | SIGTERM drain verified; no graph/orchestration changes; suite green |
| P6 | Deploy + DB migration runbooks complete (HF model; policy only); suite green |
| P7 | Arch hardening green; production-readiness checklist complete; full regression green |

### Epic (post-CAR/FR — tracked at close)

- Freeze §13 success criteria all checked  
- Master Plan P-08 / Overview §12 success criteria  
- Platform confinement verified  
- Full regression green  

### Plan acceptance (this document)

- [x] Full epic planned (P1–P7, C1–C17)  
- [x] No architectural drift vs Freeze  
- [x] Every commit independently testable  
- [x] Every phase independently verifiable  
- [x] Architecture Freeze fully respected  
- [x] Implementation Dependency Validation passed  
- [x] Ready for implementation after pre-P1 baseline  

---

## 12. Architecture Checkpoint mandates

| Checkpoint | Status |
|---|---|
| **A** (after P3 / C8) | **PASS** — 2026-07-18; Macro B (P4–P5) **AUTHORIZED** |
| **B** (after P5 / C13) | **PASS** — 2026-07-18; Macro C (P6–P7) **AUTHORIZED** |
| **C** (after P7 / C17) | **PASS** — 2026-07-18; CAR **AUTHORIZED** |
| **CAR** | **PASS WITH OBSERVATIONS** — 2026-07-20; Final Review **AUTHORIZED** (0 P0/P1) |
| **Final Review** | **PASS WITH OBSERVATIONS** — 2026-07-20; Epic Close **AUTHORIZED** (0 P0/P1) |


| Checkpoint | After | Must verify | Authorizes |
|---|---|---|---|
| **A** | P3 / C8 | Config + logging + LLM obs match Freeze; suite green; no Freeze drift | Macro B (P4–P5) |
| **B** | P5 / C13 | Health + shutdown match Freeze; suite green; no graph topology change | Macro C (P6–P7) |
| **C** | P7 / C17 | Docs + hardening complete; suite green | CAR |

---

## 13. Stopping rules

1. Stop if implementation would require Domain Contracts, Data Model, `InterviewState`, frozen models, or LangGraph topology changes → Category B / ADR path.  
2. Stop if shutdown cannot be achieved at process edge without orchestration → Orchestration Boundary + ADR (do not invent AR-12).  
3. Stop if health requires mutating probes → redesign probe within HLT-*; do not accept AR-09.  
4. Sequencing-only issues → Plan Correction Rule + Mini Architecture Freeze.  
5. Never make architectural decisions in code.

---

## 14. Open issues

| ID | Item | Blocking? |
|---|---|---|
| OI-01 | Exact process-edge allowlist for residual env reads (if any OS/platform bootstrap) finalized at C2/C3 | **Resolved (C3)** — allowlist = `tests/` + `scripts/` only; no production residual |
| OI-02 | Node inventory split batch A/B finalized at C5 start from current graph module list | **Resolved (C6)** — batch A = 13 core cycle; batch B = entry/session_close/report/longitudinal_update/replay; coverage gate active |
| OI-03 | CAR must re-verify HF confinement (Freeze Observation O-01) | **Resolved (CAR 2026-07-20)** — O-01 surfaces clean; C3+C16 arch gates green |
| OI-04 | EPIC-10 dead-code purity remains release-gate | No (AR-16); carried forward post-FR (non-blocking) |

**Blocking open issues for implementation start:** None.

---

## 15. Implementation readiness

| Criterion | Status |
|---|---|
| Architecture Freeze APPROVED | Yes |
| ADR / Domain Contracts / Data Model | N/A / SKIP |
| Implementation Plan complete (§8.6) | Yes |
| Dependency Validation | PASSED |
| Risk Validation | PASSED |
| Pre-P1 baseline recorded | **YES** — 7003 passed / 0 failed |
| Implementation (C1–C17) | **COMPLETE** — 2026-07-18; regression certification 7417 / 0 |
| Checkpoint C | **PASS** — 2026-07-18; CAR authorized |
| CAR | **PASS WITH OBSERVATIONS** — 2026-07-20; Final Review authorized |
| Regression Certification | **COMPLETE** — 2026-07-20; 7417 passed / 0 failed |
| Documentation Certification | **COMPLETE** — 2026-07-20 |
| Final Review | **PASS WITH OBSERVATIONS** — 2026-07-20; Epic Close authorized |
| Implementation may begin | **N/A** — implementation complete |

**Recommendation:** Proceed to **Epic Close**.

---

## 16. Counts

| Metric | Count |
|---|---|
| Macro phases | 3 (A, B, C) |
| Implementation phases | 7 (P1–P7) |
| Planned commits | 17 (C1–C17) |
| Architecture Checkpoints | 3 |

---

*End of EPIC-08 Implementation Plan.*
