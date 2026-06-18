# Question Ingestion Architecture

**Status:** STUB — populate from `services/question_ingestion/` and `scripts/question_corpus/`
**Owner:** Services
**SSOT For:** Adapter ABC, registry, dataset loaders, corpus build pipeline
**Update Trigger:** Any adapter or ingestion pipeline change
**ADR:** ADR-013

---

## Sections (to fill)

### 1. Overview

<!-- TODO: End-to-end ingestion flow: Dataset → Adapter → RawQuestionRecord → Chroma corpus -->

### 2. DatasetAdapter ABC

<!-- TODO: Abstract interface contract -->
<!-- Location: services/question_ingestion/adapters/dataset_adapter.py -->
<!-- Required methods, return types -->

### 3. AdapterRegistry

<!-- TODO: Current registered adapters (3 of 10+) -->
<!-- How to register a new adapter -->

| Adapter | Key | Dataset Type | Status |
|---|---|---|---|
| `GenericDatasetAdapter` | `generic` | Generic HF datasets | Registered |
| `SystemDesignAdapter` | `system_design` | System design corpus | Registered |
| `HuggingFaceQAAdapter` | `huggingface_qa` | HF QA datasets | Registered |
| *(others)* | — | — | **Not registered** — used directly |

### 4. Dataset Loaders

<!-- TODO: DatasetRegistryLoader, GitHubCorpusRegistryLoader, DatasetDiscoveryRegistryLoader -->
<!-- When each is used; manifest format -->

### 5. Corpus Build Pipeline

<!-- TODO: scripts/question_corpus/build_chroma_corpus.py flow -->
<!-- Steps: load → embed → deduplicate → store → upload artifact -->
<!-- TD-002: double embedding issue -->

### 6. Ingestion Runbook

<!-- See runbooks/ingestion-run.md -->

### 7. Extension Guide — Adding a New Adapter

<!-- TODO: Step-by-step -->
1. Implement `DatasetAdapter` ABC in `services/question_ingestion/adapters/<name>_adapter.py`
2. Register in `adapter_registry.py`
3. Add dataset manifest entry
4. Add tests in `tests/services/question_ingestion/`

### 8. Known Limitations

- TD-IN-001: 7+ adapters not registered
- TD-IN-002: No semantic tag / skill / taxonomy normalization in GenericDatasetAdapter
- TD-IN-003: Missing `batch_id`, `dataset_name`, `origin_url` on `RawQuestionRecord`
- TD-007: SQL actionable pattern filter too aggressive

---

## Cross-References

- `question-intelligence.md` — downstream consumer
- `configuration.md` — HF token, embedding settings
- ADR-013 — partial registry decision
- `technical-debt-register.md` — TD-IN-001, TD-IN-002, TD-IN-003
- `runbooks/corpus-build.md` — operational build guide
