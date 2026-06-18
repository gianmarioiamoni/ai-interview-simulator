# ADR-005 — Dual Embedding Strategy

**Status:** Proposed
**Date:** 2026-06-18
**Owner:** Infra

---

## Context

<!-- TODO: Two embedding use cases — Chroma retrieval (semantic search) vs local dedup/diversity planning -->

## Decision

<!-- TODO: OpenAI embeddings for Chroma; SentenceTransformer (local) for diversity/dedup in planning -->

## Rationale

<!-- TODO: Cost, latency, offline availability for planning -->

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Single embedding model for both | |
| Local model for both | |

## Consequences

### Positive
-

### Negative / Risks
- TD-001: diversity embeddings not available at retrieval time
- TD-002: double embedding generation in corpus build

## Implementation Evidence

- `infrastructure/config/settings.py` — `embedding_model`, `local_embedding_model`
- `scripts/question_corpus/build_chroma_corpus.py`

## Review Trigger

TD-001 and TD-002 resolution.
