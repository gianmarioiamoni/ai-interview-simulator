# V1.3 — Production-Equivalent Deployment Validation

**Artifact ID:** DV-V1.3  
**Gate:** Master Plan §9 Production deployment; RR blocker B-RR-03; Deployment Runbook verification criteria  
**Activity:** Production-Equivalent Deployment Validation (ops only)  
**Date:** 2026-07-22  
**Evaluated HEAD:** `d267aac9a422a6dd96c4da5b6699a9b9c18d3752`  
**Working tree at evaluation:** clean  
**Operator:** Release-candidate deployment validation (local ops execution)  
**Scope:** Deployment validation + certification record only — no application redesign; no RR re-run; no VERSION/tag ceremony  

---

## 1. Preflight

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `d267aac9a422a6dd96c4da5b6699a9b9c18d3752` |
| Working tree | clean |
| Prior RR | `V13-RELEASE-READINESS-REVIEW.md` — NOT RELEASE READY (B-RR-03 open) |
| Prior blocker assessment | `V13-RELEASE-BLOCKER-ASSESSMENT.md` §4 — B-RR-03 requires executed prod-equivalent validation + record |
| Open V1.3 P0/P1 (pre-validation) | Zero architecture P0/P1; B-RR-03 ops gap open |
| Docker Desktop | Started for image build attempt |
| Local Settings secrets | `.env` present; `OPENAI_API_KEY`, `CORPUS_HF_REPO`, `HF_TOKEN` set |

### Inputs used

| Input | Role |
|---|---|
| `V13-DEVELOPMENT-PLAYBOOK.md` v1.0 | RR / evidence / Success Metrics process |
| `ARC-01-ARCHITECTURE-CONSTITUTION.md` | Boundary: ops validation only |
| `V13-PRODUCT-MASTER-PLAN.md` §9 | Production deployment metric |
| `docs/ops/DEPLOYMENT-RUNBOOK.md` | Local / staging / production procedures + pass criteria |
| `docs/ops/DB-MIGRATION-RUNBOOK.md` | §6.1 no-op migration verify path |
| Health readiness implementation | `GET /health/ready`; probes LLM / DB / sandbox |
| Repository at evaluated HEAD | Runtime under validation |

---

## 2. Environment description

| Dimension | Value |
|---|---|
| Equivalence class | **Production process-edge parity** per Deployment Runbook §5 (`python app.py` — same HF Spaces entrypoint / ASGI edge as Docker `CMD`) |
| Host | macOS local workstation (darwin); Python 3.12.4 venv `.venv-v13-deploy` |
| Entrypoint | `python app.py` |
| Listen | `0.0.0.0:7860` (`PORT=7860`) |
| Config surface | Settings-only via `.env` (CFG-01) |
| Corpus | `CORPUS_HF_REPO=gianmarioiamoni67/ai-interview-corpus` — startup `CORPUS_OK … document_count=1272` |
| SQLite | `SQLITE_DB_PATH=data/questions.db` (readable file present for DB probe) |
| Logging | `LOG_LEVEL=INFO`, `LOG_SINK=stdout` |
| Probes | LLM / DB / sandbox **enabled** (production defaults) |
| Drain | `SHUTDOWN_DRAIN_TIMEOUT_S=30` |

### Docker image attempt (production-parity image)

| Step | Result |
|---|---|
| `docker build -t ai-interview-simulator:v13-rc-d267aac .` (attempt 1) | **FAIL** — daemon EOF while downloading large CUDA/torch wheels |
| `docker build` retry (attempt 2) | Pip layer completed; **FAIL** at export — containerd sync I/O error |
| Runnable image digest | **Not produced** |

**Classification of Docker failure:** Environment / platform constraint during local image materialization (oversized torch+CUDA pull + Desktop I/O). Not treated as an application defect. Validation continued on the runbook-authorized process-edge path (§5), which is the same entrypoint as HF Spaces / Dockerfile `CMD`.

---

## 3. Deployment execution summary

| Step | Action | Result |
|---|---|---|
| 1 | Identify RC revision `d267aac` | PASS |
| 2 | Install deps from `requirements.txt` into isolated venv | PASS |
| 3 | Load Settings from `.env` (no ad-hoc behaviour overrides) | PASS |
| 4 | Ensure SQLite file at Settings path (DB probe prerequisite; no schema migration) | PASS |
| 5 | Start `python app.py` | PASS — Uvicorn listening on `:7860` |
| 6 | Corpus load at startup | PASS — `CORPUS_OK document_count=1272` |
| 7 | DB migration | **N/A / no-op verify** per DB-MIGRATION-RUNBOOK §6.1 (no authorized migration) |
| 8 | Post-start verification suite | See §4–§5 |
| 9 | SIGTERM drain | PASS — see §4 |
| 10 | Rollback procedure | Dry-run recorded — see §4 |

---

## 4. Validation results

| # | Check | Pass criteria | Result | Severity if fail | Blocks release? |
|---|---|---|---|---|---|
| 1 | Clean deployment | Process starts from RC HEAD without manual code changes | **PASS** | — | — |
| 2 | Environment configuration | Required Settings present (`OPENAI_API_KEY`, corpus, tokens); defaults for port/log/probes/drain | **PASS** | — | — |
| 3 | Database migration | §6.1 no-op: DB file readable; no schema rewrite | **PASS** (no-op) | — | — |
| 4 | Application startup | Uvicorn startup complete; Gradio built | **PASS** | — | — |
| 5 | Health endpoint | `GET /health/ready` → HTTP **200**, `"ready": true` | **FAIL** | **P0** | **YES** |
| 6 | Structured logging | Startup + process-edge logs on stdout with structured fields | **PASS** | — | — |
| 7 | Primary-flow smoke | UI root + Gradio config responsive | **PASS** (basic) | — | — |
| 8 | Graceful shutdown (SIGTERM) | Drain completes; process exits; process-edge log | **PASS** | — | — |
| 9 | Rollback procedure | Runbook §7.4 executable (prior revision identifiable) | **PASS** (dry-run) | — | — |

### 4.1 Health endpoint detail (blocking)

Observed:

- HTTP **503**
- Body: `"ready": false`
- Probes:
  - `llm`: **failure** — `Models.list() got an unexpected keyword argument 'limit'` (`TypeError`)
  - `database`: **success** — `sqlite readable`
  - `sandbox`: **success**
- `scripts/ci/check_readiness_gate.py` against live process → **exit 1**

Root cause (validation observation, not remediated in this activity): `infrastructure/health/probes.py` calls `client.models.list(limit=1)`, but installed OpenAI SDK `Models.list` signature does **not** accept `limit` (`openai==2.46.0` in the validation venv). This is an application/probe incompatibility with the resolved dependency, not an operator misconfiguration.

**Deploy-gate implication:** Production defaults enable the LLM probe; CI local readiness smoke disables it (`health_llm_probe_enabled=False`). Live production-equivalent readiness therefore fails while CI smoke can still pass.

### 4.2 Structured logging detail

| Evidence | Result |
|---|---|
| Startup: `CORPUS_OK … document_count=1272` | PASS |
| Startup: `Building Gradio app for HF Spaces...` | PASS |
| Logger format `timestamp \| LEVEL \| logger \| message` on stdout | PASS |
| SIGTERM: `process_edge_shutdown_drain outcome=clean in_flight=0 timeout_s=30.0` | PASS |

### 4.3 SIGTERM detail

| Evidence | Result |
|---|---|
| SIGTERM delivered to `python app.py` PID | PASS |
| Log: `process_edge_shutdown_drain outcome=clean in_flight=0 timeout_s=30.0` | PASS |
| Process exit + port `:7860` closed within drain timeout | PASS |
| In-flight reject body not sampled (process exited with `in_flight=0` before follow-up request) | Observation only — non-blocking |

### 4.4 Rollback dry-run

| Item | Value |
|---|---|
| Procedure | Deployment Runbook §7.4 — redeploy previous known-good revision / image; restore Settings only if changed; re-run readiness |
| Previous revision (git parent) | `3887c0cfabc7bc86fd50ddd46663ce2b11d03ecd` |
| Execution | Dry-run only (no HF Space push; no alternate revision started) |
| Result | **PASS** — procedure applicable and prior revision identifiable |

---

## 5. Smoke test summary

| Flow | Action | Result |
|---|---|---|
| UI root | `GET /` | **PASS** — HTTP 200, HTML ~139KB, Gradio present |
| Gradio config | `GET /config` | **PASS** — HTTP 200; `components=68`, `dependencies=25`, `mode=blocks` |
| Readiness gate client | `check_readiness_gate.py` | **FAIL** — HTTP 503 (same LLM probe defect) |
| Full interview path | Operator short interview (LLM multi-turn) | **NOT EXECUTED** — blocked by failed readiness gate criterion; not used to override §4.1 |

---

## 6. Remaining observations

| ID | Severity | Note | Blocks this validation? |
|---|---|---|---|
| O-DV-01 | **P0** | LLM readiness probe `TypeError` on `models.list(limit=1)` vs OpenAI SDK signature → `/health/ready` 503 | **YES** |
| O-DV-02 | Medium (ops env) | Local Docker image build/export failed (CUDA/torch size + Desktop I/O); no image digest | No — process-edge parity used |
| O-DV-03 | Low | WeasyPrint native-lib warning at startup (PDF stack); app still started | No |
| O-DV-04 | Low | SIGTERM in-flight reject body not sampled (`in_flight=0` fast exit) | No — clean drain logged |
| O-DV-05 | Info | Full multi-turn interview smoke not run after readiness failure | No additional — readiness already blocking |
| O-DV-06 | Info | HF staging/production Space push not performed in this activity | No — runbook allows local process-edge / Docker parity |

---

## 7. Deployment validation verdict

# NOT VALIDATED

**Rationale:** Production-equivalent process-edge deploy of HEAD `d267aac` started cleanly and passed config, DB no-op migration verify, startup, structured logging, basic UI smoke, SIGTERM drain, and rollback dry-run. It **failed** the mandatory readiness criterion (`GET /health/ready` → 200 / `ready: true`) due to a **P0** LLM probe defect (`TypeError: Models.list() got an unexpected keyword argument 'limit'`). Per Deployment Runbook §5.4 / §6.2 / §7.3 and Master Plan §9, production deployment is **not** successfully validated.

**B-RR-03 status after this record:** remains **open** until a subsequent validation at a remediated HEAD produces readiness PASS (and this artifact is superseded or amended).

**Not performed (out of scope):** Release Readiness Review re-run; VERSION / CHANGELOG updates; release tags.

---

## 8. Commit information

| Field | Value |
|---|---|
| Artifact path | `docs/master-plan/V13-DEPLOYMENT-VALIDATION.md` |
| Commit scope | Validation certification artifact only |
| Commit hash / message / resulting HEAD | Filled after git commit in the certification response |

---

## Document Version

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-22 | Initial production-equivalent deployment validation at HEAD `d267aac` — **NOT VALIDATED** (P0 readiness LLM probe) |
