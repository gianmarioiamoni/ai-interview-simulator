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

AI-powered technical interview simulation platform. Generates adaptive, context-aware interview questions across Behavioral, Technical Knowledge, and Coding domains. Evaluates answers with dimensional scoring, produces humanized conversational framing, and exports structured PDF/JSON reports.

## Features

- Domain-aware question generation (BG, TK, Coding, SQL)
- LangGraph-based interview graph with adaptive flow
- Humanizer subsystem for conversational question framing
- Business context profiles (job/company description integration)
- Dimensional answer evaluation with hire/no-hire decision
- PDF and JSON report export
- Chroma vector corpus with HF Dataset backup/restore
- Gradio UI — deployable locally or on Hugging Face Spaces

---

## Local Setup

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

Copy and populate:

```bash
cp .env.example .env
```

Required keys:

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

The production entrypoint is `app.py`. It is used automatically by HF Spaces via the `app_file: app.py` frontmatter above.

### Required Spaces secrets

Set these in the HF Space settings → Secrets:

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

## Project structure

```
app/              Gradio UI, interview graph, core utilities
domain/           Contracts, value objects, interview state
infrastructure/   LLM adapters, settings, embeddings, persistence
services/         Question generation, evaluation, corpus, export
scripts/          Corpus build, ingestion, upload utilities
tests/            Unit and integration tests
```
