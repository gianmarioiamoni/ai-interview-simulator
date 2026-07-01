---
title: AI Interview Simulator
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
python_version: 3.11
app_file: app.py
---

# AI Interview Simulator

Enterprise-grade AI Interview Simulation platform. Conducts adaptive, multi-domain technical interviews, evaluates candidate performance through a deterministic reasoning pipeline, and produces a structured coaching report with a hire/no-hire decision.

---

## Overview

The AI Interview Simulator is a production-quality platform designed to simulate real technical interviews at senior engineering and engineering management level. It supports the full interview lifecycle:

- **Adaptive interview graph** — 16-node LangGraph-based interview orchestration with dynamic routing, follow-up question injection, and context-aware navigation.
- **Question generation** — Hybrid RAG + LLM pipelines across Written, Coding, and SQL domains. Questions adapt to seniority level, business context, and session-level coverage state.
- **Evaluation pipeline** — Dimensional scoring (technical depth, system design, engineering judgment, communication, behavioral) with signal enrichment and normalized hire-decision gating.
- **Humanizer** — Conversational question framing and follow-up engine. Deterministic selector, STRICT-mode parser, 17-rule validation guard. Feature-flagged. Frozen M1.
- **Follow-up engine** — Policy-driven follow-up generation. LLM-generated, guard-validated. Up to 2 follow-ups per interview, 20% coverage target.
- **Interview Reasoner** — Fully deterministic, LLM-free reasoning pipeline. 13 pattern detectors (coverage, consistency, trend, reasoning depth, engineering judgment, communication, behavioral, leadership, collaboration, adaptability, confidence calibration). Frozen M2.
- **Navigation engine** — Adaptive and legacy navigation paths. Driven by `ReasonerDecision` (advisory) and explicit candidate intent.
- **Reporting** — Structured final report: Executive Summary, What Went Well, What Held You Back, Knowledge Gap Summary, Next Interview Strategy, score bands, percentile benchmark. PDF and JSON export.

---

## Architecture

The platform follows a strict **Domain-Driven Design** layered architecture:

```
interface
    ↓
app  (LangGraph interview graph, Gradio UI, prompts, ports)
    ↓
services  (question intelligence, reasoner, humanizer, evaluation, reporting)
    ↓
domain  (contracts, value objects, InterviewState, InterviewMemory, policies)
    ↑
infrastructure  (LLM adapters, Chroma vector store, SQLite persistence, config)
```

Dependencies flow inward only. The domain layer is the sole source of truth for contracts.

The interview graph is stateless except for `InterviewState`. All session-scoped reasoning is accumulated in `InterviewMemory` (5-substructure composition: EvidenceStore, CandidateProfile, ReasoningHistory, RetrievalMemory, SessionMetrics).

All public APIs across M1 and M2 are frozen. All contracts carry `extra=forbid` and `schema_version` where applicable.

ADR registry: 67 accepted Architecture Decision Records.

---

## Key Features

- Adaptive multi-domain technical interviews (Written, Coding, SQL)
- LangGraph-based interview graph with 16 nodes and deterministic routing
- Hybrid RAG + LLM question generation with semantic deduplication
- Dimensional answer evaluation with hire-decision gating
- Deterministic Interview Reasoner — 13 pattern detectors, no LLM dependency
- EvaluationSignalWriter — evaluation scores mapped to typed evidence signals in the same reasoning cycle
- Conversational Humanizer with follow-up question engine
- Adaptive navigation driven by reasoner recommendations
- Coaching-first final report with executive summary, strength/gap analysis, and next-interview strategy
- PDF and JSON report export
- Chroma vector corpus with HF Dataset backup/restore
- Gradio UI — deployable locally or on Hugging Face Spaces
- Business context profiles (job description and company description integration)
- Feature-flag-gated experimental paths (humanizer, follow-up, adaptive navigation)

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Interview orchestration | LangGraph 1.1 |
| UI | Gradio 5.23 |
| LLM integration | OpenAI (gpt-4o-mini default), configurable |
| Vector store | ChromaDB 1.4 |
| Embeddings | OpenAI text-embedding-3-small + MiniLM local fallback |
| Persistence | SQLite (question bank) + Chroma (corpus) |
| Validation | Pydantic 2.12 (extra=forbid on all contracts) |
| Configuration | Pydantic-settings |
| PDF export | WeasyPrint |
| Testing | pytest (2,802 tests, 0 failures) |
| Linting | Ruff |
| Type checking | mypy |
| CI | GitHub Actions |
| Deployment | Docker / Hugging Face Spaces |

---

## Project Structure

```
app/              Interview graph (16 nodes), Gradio UI, prompts, ports, settings
domain/           Contracts, value objects, InterviewState, InterviewMemory, policies, events
services/         Question intelligence, Interview Reasoner, Humanizer, Evaluation, Reporting
infrastructure/   LLM adapters, Chroma vector store, SQLite, embeddings, configuration
interface/        CLI entry points
scripts/          Corpus build, ingestion, upload, audit utilities
datasets/         Curated and raw question corpora
tests/            Unit, integration, and hardening tests (280 modules)
docs/             Architecture docs, ADR registry, master plan (PRD + TDS), technical debt register
```

---

## Development Workflow

All development follows a structured engineering process:

```
Architecture design
    ↓
Contract definition (Pydantic, extra=forbid)
    ↓
ADR registration
    ↓
Implementation
    ↓
Testing (TDD where feasible)
    ↓
Audit (layering, ownership, configuration)
    ↓
Freeze (API freeze, contract freeze, detector freeze)
    ↓
Milestone Certification
```

Every architectural decision is recorded in the ADR registry (`docs/decisions/`). The master plan (`docs/master-plan/`) is the authoritative source for all V1.x scope, contracts, and freeze status.

---

## Getting Started

### Prerequisites

- Python 3.11+
- `OPENAI_API_KEY` (required)
- `CORPUS_HF_REPO` — HF Dataset repo ID containing the pre-built corpus (required if corpus not already built locally)
- `HF_TOKEN` — optional, required only for private HF repos

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment variables

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `CORPUS_HF_REPO` | Yes (if no local corpus) | HF Dataset repo, e.g. `username/interview-corpus` |
| `HF_TOKEN` | No | HF access token for private repos |

### Run locally

```bash
python -m app.main
```

The app validates `OPENAI_API_KEY` at startup and bootstraps or validates the Chroma corpus before launching. Startup fails fast with a clear error if either is missing.

---

## Hugging Face Spaces Deployment

The production entrypoint is `app.py`, used automatically by HF Spaces via `app_file: app.py` above.

### Required Spaces secrets

| Secret | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `CORPUS_HF_REPO` | HF Dataset repo containing `chroma_corpus.tar.gz` |
| `HF_TOKEN` | HF token (if corpus repo is private) |

### Build and push corpus artifact

```bash
python scripts/question_corpus/build_chroma_corpus.py
python scripts/upload_chroma_artifact.py
```

### Deploy

Push to the HF Space repository. The `Dockerfile` and `spaces.yml` are already configured.

---

## Current Status

**Version:** 1.1.0 Stable

- M1 (Humanizer / Follow-Up Engine) — Frozen
- M2 (Interview Reasoner / 13 Detectors / EvaluationSignalWriter) — Frozen
- API Freeze — Complete (M2-8)
- Contract Freeze — Complete
- Certification — Complete (M2-9)
- Stable Release — Complete (SR-1, 2026-07-01)
- Test suite: 2,802 passing / 0 failures

V1.2 is planned. Extension points are reserved in V1.1 ADRs. See `docs/master-plan/PRD-V1.1-V1.2.md` and `docs/master-plan/INDEX.md`.

---

## Roadmap

**V1.1 (current RC)**
- Adaptive interview graph
- Humanizer + follow-up engine
- Interview Reasoner (13 detectors, deterministic, LLM-free)
- EvaluationSignalWriter (same-cycle evidence visibility)
- Structured coaching report with hire decision

**V1.2 (planned)**
- ProfileFeature abstraction (ADR-048)
- NarrativeGenerator consuming ProfileFeatures (ADR-050)
- CoachingEngine pipeline (ADR-067)
- Evidence freshness weighting (ADR-039)
- Observation model for behavioral detectors (ADR-055, ADR-066)
- Domain layer cleanup (TD-DL-001)

**Future**
- Knowledge gap classification engine (ADR-020)
- Multi-language coding engine (ADR-016)
- Replay engine (ADR-023)
- Progress tracking persistence (ADR-022)

---

## License

See [LICENSE](LICENSE) for details.
