# Deployment Runbook — Hugging Face Spaces

**Epic:** EPIC-V13-08 (C14 / P6)  
**Freeze:** AR-01, AR-13; reproducibility per Freeze §9  
**Platform:** Hugging Face Spaces (Docker SDK) — sole production deployment target  
**Complement:** `docs/ops/DB-MIGRATION-RUNBOOK.md` (C15) — SQLite versioning policy / migration ops only

---

## 1. Purpose

Operator guide for deploying the AI Interview Simulator under the **existing Hugging Face Spaces Docker model** for:

| Environment | Intent |
|---|---|
| **Local** | Developer workstation; same process edge as production |
| **Staging** | Pre-production HF Space (or local Docker parity) with staging secrets |
| **Production** | Production HF Space |

This runbook documents wiring only. It does **not** introduce a new deployment platform, orchestration layer, or domain/data-model change.

---

## 2. Architecture surface (ops edge only)

| Concern | Location | Notes |
|---|---|---|
| Production entrypoint | `app.py` | HF Spaces `app_file`; Docker `CMD` |
| Local entrypoint | `python -m app.main` or `python app.py` | Same ASGI process edge |
| Space metadata | `spaces.yml`, README front matter | `sdk: docker` |
| Image build | `Dockerfile` | Python 3.11; exposes `7860`; runs `app.py` |
| Runtime config | `infrastructure/config/settings.py` (`Settings`) | Exclusive config entrypoint (CFG-01) |
| Readiness | `GET /health/ready` | Process-edge HTTP; probes LLM / DB / sandbox |
| CI deploy gate | `.github/workflows/ci.yml` → readiness smoke | Non-ready fails the job (AR-10) |
| Shutdown | SIGTERM → process-edge drain | Timeout: `SHUTDOWN_DRAIN_TIMEOUT_S` (default 30s) |

Platform-specific HF behaviour stays at process edge / infrastructure. Domain, LangGraph, and `InterviewState` remain free of deploy-platform imports (IB-01 / IB-02).

---

## 3. Reproducibility (mandatory)

**Same Docker image + same Settings/env (secrets) → same deploy behaviour.**

| Input | Effect |
|---|---|
| Image digest / tag built from the same `Dockerfile` + source revision | Runtime binaries and layout |
| Settings-backed env vars / Space secrets | Credentials, paths, probe flags, ports, drain timeout, log level |

Do **not** rely on ad-hoc shell exports outside Settings for production behaviour. Changing only the Space UI metadata without rebuilding the image does not change application behaviour.

---

## 4. Required Settings / secrets

Loaded exclusively via `Settings` (env / `.env` / Space secrets).

| Variable | Required | Default / notes |
|---|---|---|
| `OPENAI_API_KEY` | **Yes** | Fail-fast if missing |
| `CORPUS_HF_REPO` | Yes if no local corpus | HF Dataset repo with corpus artifact |
| `HF_TOKEN` / `HUGGINGFACE_TOKEN` | If private corpus | Optional otherwise |
| `PORT` / `SERVER_PORT` | No | Default `7860` |
| `SQLITE_DB_PATH` | No | Default `data/questions.db` |
| `LOG_LEVEL` | No | Default `INFO` |
| `LOG_SINK` | No | Default `stdout` |
| `HEALTH_PROBE_TIMEOUT_MS` | No | Default `5000` |
| `HEALTH_LLM_PROBE_ENABLED` | No | Default `true` |
| `HEALTH_DB_PROBE_ENABLED` | No | Default `true` |
| `HEALTH_SANDBOX_PROBE_ENABLED` | No | Default `true` |
| `READINESS_GATE_BASE_URL` | No | Default `http://127.0.0.1:7860` (CI/gate clients) |
| `READINESS_GATE_TIMEOUT_S` | No | Default `5.0` |
| `SHUTDOWN_DRAIN_TIMEOUT_S` | No | Default `30` |

Feature flags and model knobs follow the same Settings surface; see `infrastructure/config/settings.py`.

---

## 5. Local deployment

### 5.1 Prerequisites

- Python 3.11+
- `OPENAI_API_KEY` set
- Corpus available locally **or** `CORPUS_HF_REPO` (+ `HF_TOKEN` if private)

### 5.2 Install and run (venv)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit secrets
python -m app.main
```

Equivalent process edge via Spaces entrypoint:

```bash
python app.py
```

UI and readiness share the ASGI app. Default listen: `0.0.0.0:7860` (override with `PORT` / `SERVER_PORT`).

### 5.3 Local Docker (production-parity image)

```bash
docker build -t ai-interview-simulator:local .
docker run --rm -p 7860:7860 \
  -e OPENAI_API_KEY \
  -e CORPUS_HF_REPO \
  -e HF_TOKEN \
  ai-interview-simulator:local
```

### 5.4 Local readiness check

```bash
curl -sS "http://127.0.0.1:7860/health/ready"
```

Expect HTTP **200** and JSON `"ready": true` when enabled probes succeed. Any enabled probe failure → HTTP **503**, `"ready": false`.

Gate helper (Settings-driven base URL):

```bash
python scripts/ci/check_readiness_gate.py
```

### 5.5 Local SIGTERM drain

Send SIGTERM to the process. New requests are rejected while draining; in-flight work may finish within `SHUTDOWN_DRAIN_TIMEOUT_S`. No LangGraph topology or out-of-graph session orchestration is involved.

---

## 6. Staging deployment (HF Spaces model)

Staging uses the **same Docker image contract** as production on a **separate** Hugging Face Space (recommended) or a local Docker run with staging secrets.

### 6.1 Staging Space setup

1. Create a dedicated HF Space (e.g. `…-staging`) with Docker SDK.
2. Ensure Space config matches repo: `spaces.yml` / README front matter (`sdk: docker`, `app_file: app.py`).
3. Push the same git revision intended for promotion (or deploy the same image digest).
4. Configure **staging** Space secrets (never reuse production keys if policy forbids it):
   - `OPENAI_API_KEY`
   - `CORPUS_HF_REPO`
   - `HF_TOKEN` (if required)
5. Wait for Space build/start. Confirm container CMD is `python app.py` (Dockerfile).

### 6.2 Staging verification

1. Open the staging Space UI; confirm app loads.
2. `GET https://<staging-space-host>/health/ready` → HTTP 200, `"ready": true`.
3. Optionally point `READINESS_GATE_BASE_URL` at the staging base URL and run `python scripts/ci/check_readiness_gate.py`.
4. Smoke a short interview path (operator manual).
5. Confirm structured logs on stdout (Space logs) include frozen observability fields from EPIC-08.

### 6.3 Staging promote rule

Promote only when:

- Image / git revision matches the candidate production revision
- Settings/env differ only by intentional staging vs production secrets and paths
- Readiness gate is green on staging

---

## 7. Production deployment (HF Spaces)

### 7.1 Pre-deploy

1. Working tree / release revision identified; CI green on that revision (includes readiness deploy-gate smoke).
2. Corpus artifact available at `CORPUS_HF_REPO` (build/upload via `scripts/question_corpus/build_chroma_corpus.py` and `scripts/upload_chroma_artifact.py` when refreshing corpus).
3. Production Space secrets set (see §4).
4. Confirm no Domain / Data Model / `InterviewState` / LangGraph topology changes are smuggled into this ops deploy (Category A boundary).

### 7.2 Deploy

1. Push the release revision to the production HF Space repository (or trigger the Space rebuild from that revision).
2. HF Spaces builds the Docker image from `Dockerfile` and starts `app.py`.
3. Monitor Space build logs until the process is listening.

### 7.3 Post-deploy verification

| Step | Action | Pass criteria |
|---|---|---|
| Readiness | `GET /health/ready` on production host | HTTP 200, `"ready": true` |
| UI | Load Gradio root `/` | App responsive |
| Logs | Inspect Space logs | No startup fail-fast; Settings-driven config |
| Drain (optional) | Platform restart / SIGTERM | Drain completes within timeout; no graph topology involvement |

### 7.4 Rollback

1. Redeploy the previous known-good git revision / image (same Dockerfile contract).
2. Restore previous Settings/secrets only if they changed with the bad release.
3. Re-run readiness verification (§7.3).

Reproducibility: rollback success depends on restoring **both** image revision and Settings/env, not UI metadata alone.

---

## 8. CI / deploy gate

CI job `quality` runs:

1. Lint, tests
2. `python scripts/ci/run_local_readiness_gate_smoke.py` — serves readiness locally and fails if gate ≠ success

Operators must not bypass a red readiness gate for production promotion. Production Spaces should additionally be checked with live `GET /health/ready` after deploy (§7.3).

---

## 9. Operator quick reference

| Task | Command / URL |
|---|---|
| Local run | `python -m app.main` |
| Docker run | `docker build` + `docker run -p 7860:7860 …` |
| Readiness | `GET /health/ready` |
| Gate script | `python scripts/ci/check_readiness_gate.py` |
| HF entrypoint | `app.py` (Spaces + Docker CMD) |
| Config | Settings / env only |

---

## 10. Doc review checklist (C14 acceptance)

Reviewer confirms:

- [ ] Local / staging / production procedures documented for the HF Spaces Docker model (AR-13)
- [ ] HF Spaces stated as sole production deployment target (AR-01)
- [ ] Reproducibility note present: same image + Settings/env → same behaviour
- [ ] Readiness path documented as `GET /health/ready`
- [ ] CI readiness gate referenced
- [ ] SIGTERM drain documented as process-edge only (no graph/orchestration steps)
- [ ] Runtime config attributed to Settings (no dual env-read guidance)
- [ ] No DB migration / schema_version / on-disk shape instructions in this document (deferred to C15)
- [ ] No new deployment platform, Domain Contracts, Data Model, or LangGraph topology guidance introduced

**Review result:** ________  **Date:** ________  **Reviewer:** ________

---

*End of Deployment Runbook (EPIC-08 C14).*
