# V1.3 — Production-Equivalent Deployment Validation

**Artifact ID:** DV-V1.3  
**Gate:** Master Plan §9 Production deployment; RR blocker B-RR-03; Deployment Runbook verification criteria  
**Activity:** Production-Equivalent Deployment Re-Validation (ops only; post P0 readiness hotfix)  
**Date:** 2026-07-22  
**Evaluated HEAD:** `b536cbd3607d6fb0945521b0553f9755b6f6a00d`  
**Working tree at evaluation:** clean (ops-only untracked local venv/log dirs excluded from commit)  
**Operator:** Release-candidate deployment re-validation (local ops execution)  
**Scope:** Deployment validation + certification record only — no application redesign; no RR re-run; no VERSION/tag ceremony  

**Supersedes:** DV-V1.3 v1.0 at HEAD `d267aac` — **NOT VALIDATED** (P0 LLM readiness probe)

---

## 1. Preflight

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `b536cbd3607d6fb0945521b0553f9755b6f6a00d` |
| HEAD subject | `fix(v1.3): restore readiness LLM probe for OpenAI SDK 2.x` |
| Working tree | clean at start of activity |
| Prior DV | `V13-DEPLOYMENT-VALIDATION.md` v1.0 — **NOT VALIDATED** (O-DV-01 P0 LLM probe) |
| Prior RR | `V13-RELEASE-READINESS-REVIEW.md` — NOT RELEASE READY (B-RR-03 open pending successful DV) |
| P0 Hotfix | HEAD `b536cbd` — `infrastructure/health/probes.py` uses `next(iter(client.models.list()), None)` (no `limit=`) |
| Open V1.3 architecture P0/P1 (pre-validation) | Zero |
| Docker Desktop | Available; image export blocked by host disk / containerd I/O |
| Local Settings secrets | `.env` present; `OPENAI_API_KEY`, `CORPUS_HF_REPO`, `HF_TOKEN` set |

### Inputs used

| Input | Role |
|---|---|
| `V13-DEVELOPMENT-PLAYBOOK.md` v1.0 | RR / evidence / Success Metrics process |
| `ARC-01-ARCHITECTURE-CONSTITUTION.md` | Boundary: ops validation only |
| `V13-PRODUCT-MASTER-PLAN.md` §9 | Production deployment metric |
| `docs/ops/DEPLOYMENT-RUNBOOK.md` | Local / staging / production procedures + pass criteria |
| `docs/ops/DB-MIGRATION-RUNBOOK.md` | §6.1 no-op migration verify path |
| Prior DV record (v1.0) | Baseline failure + re-validation checklist |
| P0 Hotfix at `b536cbd` | Remediation under re-test |
| Repository at evaluated HEAD | Runtime under validation |

---

## 2. Environment description

| Dimension | Value |
|---|---|
| Equivalence class | **Production process-edge parity** per Deployment Runbook §5 (`python app.py` — same HF Spaces entrypoint / ASGI edge as Docker `CMD`) |
| Host | macOS local workstation (darwin); Python 3.12.4 venv `.venv-v13-deploy` |
| Entrypoint | `python -u app.py` |
| Listen | `0.0.0.0:7860` (`PORT=7860`) |
| Config surface | Settings-only via `.env` (CFG-01) |
| Corpus | `CORPUS_HF_REPO=gianmarioiamoni67/ai-interview-corpus` — startup `CORPUS_OK … document_count=1272` |
| SQLite | `SQLITE_DB_PATH=data/questions.db` (readable; `PRAGMA integrity_check` → `ok`) |
| OpenAI SDK (venv) | `openai==2.46.0` |
| Logging | `LOG_LEVEL=INFO`, `LOG_SINK=stdout` |
| Probes | LLM / DB / sandbox **enabled** (production defaults) |
| Drain | `SHUTDOWN_DRAIN_TIMEOUT_S=30` |

### Docker image attempt (production-parity image)

| Step | Result |
|---|---|
| `docker build -t ai-interview-simulator:v13-rc-b536cbd .` | Pip/COPY layers completed; **FAIL** at export — `containerd` temp mount I/O error (host disk pressure) |
| Runnable image digest | **Not produced** |

**Classification of Docker failure:** Environment / platform constraint during local image materialization. Not treated as an application defect. Validation continued on the runbook-authorized process-edge path (§5), which is the same entrypoint as HF Spaces / Dockerfile `CMD`.

---

## 3. Deployment execution summary

| Step | Action | Result |
|---|---|---|
| 1 | Identify RC revision `b536cbd` | PASS |
| 2 | Install deps from `requirements.txt` into isolated venv `.venv-v13-deploy` | PASS |
| 3 | Load Settings from `.env` (no ad-hoc behaviour overrides) | PASS |
| 4 | Ensure SQLite file at Settings path (DB probe prerequisite; no schema migration) | PASS |
| 5 | Start `python -u app.py` | PASS — Uvicorn listening on `:7860` |
| 6 | Corpus load at startup | PASS — `CORPUS_OK document_count=1272` |
| 7 | DB migration | **N/A / no-op verify** per DB-MIGRATION-RUNBOOK §6.1 (no authorized migration) |
| 8 | Post-start verification suite | See §4–§5 |
| 9 | SIGTERM drain | PASS — see §4.3 |
| 10 | Rollback procedure | Dry-run recorded — see §4.4 |

---

## 4. Validation results

| # | Check | Pass criteria | Result | Severity if fail | Blocks release? |
|---|---|---|---|---|---|
| 1 | Clean deployment | Process starts from RC HEAD without manual code changes | **PASS** | — | — |
| 2 | Environment configuration | Required Settings present (`OPENAI_API_KEY`, corpus, tokens); defaults for port/log/probes/drain | **PASS** | — | — |
| 3 | Database migration | §6.1 no-op: DB file readable; no schema rewrite | **PASS** (no-op) | — | — |
| 4 | Application startup | Uvicorn startup complete; Gradio built | **PASS** | — | — |
| 5 | Health endpoint | `GET /health/ready` → HTTP **200**, `"ready": true` | **PASS** | — | — |
| 6 | Structured logging | Startup + process-edge logs on stdout with structured fields | **PASS** | — | — |
| 7 | Primary-flow smoke | UI root + Gradio config + readiness gate client | **PASS** | — | — |
| 8 | Graceful shutdown (SIGTERM) | Drain completes; process exits; process-edge log | **PASS** | — | — |
| 9 | Rollback procedure | Runbook §7.4 executable (prior revision identifiable) | **PASS** (dry-run) | — | — |

### 4.1 Health endpoint detail (P0 hotfix confirmation)

Observed (production probe defaults enabled):

- HTTP **200**
- Body: `"ready": true`
- Probes:
  - `llm`: **success** — `llm api reachable` (~1.5–1.6s; `GET https://api.openai.com/v1/models` 200)
  - `database`: **success** — `sqlite readable`
  - `sandbox`: **success**
- `scripts/ci/check_readiness_gate.py` against live process → **exit 0**

**Prior P0 closed for this gate:** O-DV-01 (`Models.list() got an unexpected keyword argument 'limit'`) no longer reproduces at HEAD `b536cbd`.

### 4.2 Structured logging detail

| Evidence | Result |
|---|---|
| Startup: `CORPUS_OK … document_count=1272` | PASS |
| Startup: `Building Gradio app for HF Spaces...` | PASS |
| Logger format `timestamp \| LEVEL \| logger \| message` on stdout | PASS |
| Live LLM probe: `HTTP Request: GET https://api.openai.com/v1/models "HTTP/1.1 200 OK"` | PASS |
| SIGTERM: `process_edge_shutdown_drain outcome=clean in_flight=0 timeout_s=30.0` | PASS |

### 4.3 SIGTERM detail

| Evidence | Result |
|---|---|
| SIGTERM delivered to `python -u app.py` PID | PASS |
| Log: `process_edge_shutdown_drain outcome=clean in_flight=0 timeout_s=30.0` | PASS |
| Process exit + port `:7860` closed within drain timeout | PASS |
| In-flight reject body not sampled (process exited with `in_flight=0`) | Observation only — non-blocking |

### 4.4 Rollback dry-run

| Item | Value |
|---|---|
| Procedure | Deployment Runbook §7.4 — redeploy previous known-good revision / image; restore Settings only if changed; re-run readiness |
| Previous revision (git parent prior to hotfix lineage for rollback identity) | `f2213436e97fcc98d1089eda6a9c1814d110f4df` (prior DV record commit); pre-hotfix RC `d267aac9a422a6dd96c4da5b6699a9b9c18d3752` |
| Execution | Dry-run only (no HF Space push; no alternate revision started) |
| Result | **PASS** — procedure applicable and prior revision identifiable |

---

## 5. Smoke test summary

| Flow | Action | Result |
|---|---|---|
| UI root | `GET /` | **PASS** — HTTP 200, HTML ~139KB, Gradio present |
| Gradio config | `GET /config` | **PASS** — HTTP 200; `components=68`, `dependencies=25`, `mode=blocks` |
| Readiness gate client | `check_readiness_gate.py` | **PASS** — exit 0; HTTP 200 / `ready: true` |
| Full interview path | Operator short interview (LLM multi-turn) | **NOT EXECUTED** — optional per runbook; primary readiness + UI smoke green |

---

## 6. Remaining observations

| ID | Severity | Note | Blocks this validation? |
|---|---|---|---|
| O-DV-01 | — | **CLOSED** at `b536cbd` — LLM probe success; `/health/ready` 200 | No (resolved) |
| O-DV-02 | Medium (ops env) | Local Docker image build/export failed (containerd I/O + host disk pressure); no image digest | No — process-edge parity used |
| O-DV-03 | Low | WeasyPrint native-lib warning at startup (PDF stack); app still started | No |
| O-DV-04 | Low | SIGTERM in-flight reject body not sampled (`in_flight=0` fast exit) | No — clean drain logged |
| O-DV-05 | Info | Full multi-turn interview smoke not run | No — readiness + UI smoke satisfied primary criteria |
| O-DV-06 | Info | HF staging/production Space push not performed in this activity | No — runbook allows local process-edge / Docker parity |
| O-DV-07 | Low (ops env) | Host disk near-full during validation (~117Mi free mid-run); pip/mypy cache cleared to continue SIGTERM retest | No — did not alter application behaviour |

**Blockers:** none.

---

## 7. Deployment validation verdict

# VALIDATED WITH OBSERVATIONS

**Rationale:** Production-equivalent process-edge deploy of HEAD `b536cbd` started cleanly and passed config, DB no-op migration verify, startup, **`GET /health/ready` (200 / `ready: true` with LLM + DB + sandbox success)**, structured logging, primary UI/config/gate smoke, SIGTERM drain, and rollback dry-run. The prior **P0** LLM probe defect is confirmed remediated. Residual observations are ops-environment only (Docker image export not produced; WeasyPrint warning; optional full interview smoke / HF Space push not performed) and do **not** fail Deployment Runbook §5.4 / §6.2 / §7.3 readiness criteria.

**B-RR-03 status after this record:** deployment validation evidence now exists at a remediated HEAD. Formal closure remains for the subsequent Release Readiness Review (out of scope for this activity).

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
| 1.1 | 2026-07-22 | Re-validation at HEAD `b536cbd` (P0 hotfix) — **VALIDATED WITH OBSERVATIONS** |
