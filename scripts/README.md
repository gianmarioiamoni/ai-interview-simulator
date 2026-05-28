# Test Scripts Organization

This directory contains test scripts organized by functional domain, aligned with the system architecture.

## Directory Structure

### 📥 `ingestion/`
Dataset loading, adapters, normalization, and metadata extraction.
- Dataset loaders (JSON, JSONL, CSV, HuggingFace)
- Adapter registry and implementations
- Question normalization and classification
- Vector ingestion and indexing

### 📚 `corpus/`
Corpus management, validation, onboarding, and quality control.
- Corpus onboarding and validation
- Curated dataset import
- Deduplication and balancing
- Diagnostics and diversity scoring

### 🔍 `retrieval/`
Question retrieval strategies and pipelines.
- Semantic, hybrid, and embedding retrieval
- Adaptive and diversity-aware retrieval
- Memory-aware retrieval pipelines
- Retrieval diagnostics and reranking

### 📋 `planning/`
Interview planning, question selection, and assembly.
- Constraint-based planning
- Adaptive difficulty balancing
- Policy-driven assembly
- Candidate pool management

### ⚡ `quality/`
Question quality scoring and analysis.
- Quality scoring engines
- Coverage analysis
- Technical domain filtering
- Coverage-constrained reranking

### 🧠 `semantic/`
Semantic operations (clustering, deduplication, similarity).
- Semantic clustering and deduplication
- Embedding similarity
- Cluster suppression and cooldown
- Question reuse prevention

### 🎯 `orchestration/`
Interview orchestration and coordination.
- End-to-end interview flow
- Multi-component integration tests

### ⚙️ `execution/`
Code and SQL execution engines.
- SQL database and query execution
- Coding test execution
- Manual execution testing

### 🔬 `question_corpus/`
Question corpus infrastructure (Chroma-based).
- Chroma vector store operations
- Corpus validation and statistics
- Schema validation and loaders
