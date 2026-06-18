# ADR-015 — SQLite + Chroma Split Storage Backends

**Status:** Proposed
**Date:** 2026-06-18
**Owner:** Infra

---

## Context

<!-- TODO: Two distinct storage needs: structured session/result persistence vs semantic vector retrieval -->

## Decision

<!-- TODO: SQLite for structured interview data (sessions, results, history);
Chroma for vector question corpus (semantic retrieval) -->

## Rationale

<!-- TODO: Each backend optimized for its access pattern; no overlap in responsibilities -->

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Single PostgreSQL with pgvector | |
| Only Chroma for all storage | |
| Only SQLite (no vector search) | |

## Consequences

### Positive
-

### Negative / Risks
- Two backends to maintain, back up, and deploy

## Implementation Evidence

- `infrastructure/persistence/sqlite/` — structured persistence
- `infrastructure/vector_store/chroma_question_store.py` — vector retrieval
- `scripts/question_corpus/` — corpus build & upload

## Review Trigger

Scale requirements exceed SQLite limits or Chroma migration path changes.
