# /docs/roadmap/roadmap.md

# Roadmap

# Strategic Goal

Build an AI-native technical interview platform with:

- semantic retrieval
- adaptive questioning
- executable validation
- structured evaluation
- dynamic feedback

---

# STEP 1 — Question Intelligence Refactor

## Goal

Reduce orchestration complexity.

## Actions

Create:

services/question_intelligence/question_intelligence_service.py

Move orchestration there.

Replaced legacy `QuestionSelectionService` with:

- `AreaQuestionBuilder` (per-area retrieve + generate)
- `QuestionSetBuilder` (set assembly, dedup, quality)
- `LazyAdaptiveInterviewService` (adaptive runtime path)

---

# STEP 2 — AreaQuestionBuilder

## Critical Refactor

Implement:

class AreaQuestionBuilder

Responsibilities:
- 2 retrieve
- 2 generate

---

# STEP 3 — RetrievalQueryBuilder

Introduce:

class RetrievalQueryBuilder

Goal:
- better retrieval quality
- more contextual retrieval
- semantic query construction

---

# STEP 4 — SQL Generator

## STEP 4.1

SQLQuestionGenerator

## STEP 4.2

SQL → Question contract mapping

## STEP 4.3

SQLExecutor multi-test refactor

## STEP 4.4

AreaQuestionBuilder integration

---

# STEP 5 — Humanizer Refactor ✓ COMPLETED

Extracted:
- follow-up orchestration
- conversational logic

Into:

HumanizerService

Features implemented:
- max 2 follow-ups (MAX_FOLLOW_UPS_PER_INTERVIEW)
- non-consecutive
- score-triggered (FOLLOW_UP_SCORE_THRESHOLD = Quality.OPTIMAL.rank())
- DIRECT_QUESTION and REMARK_PLUS_QUESTION: ACTIVE in V1
- FOLLOW_UP: gated behind HUMANIZER_FOLLOW_UP_ENABLED (default False, V1.1)
- question_display_text wired to DisplaySection
- LastQuestionContext snapshot prevents timing defect

---

# STEP 6 — FollowUpQuestionGenerator

Implement:

FollowUpQuestionGenerator

Major qualitative improvement.

---

# STEP 7 — Dataset + Ingestion

## Sources

### HuggingFace
- technical-interview-questions
- behavioral-interview-questions

### GitHub
- FAANG interview datasets

### Kaggle
- SQL interview datasets

---

# Planned Pipeline

Question ingestion pipeline (services/question_ingestion)
    ↓
SQLite
    ↓
Chroma

---

# STEP 8 — Quality Controls

Implement:
- semantic deduplication
- diversity checks
- difficulty balancing

---

# Major Strategic Focus

Most important differentiator:

Hybrid Question Intelligence Engine
(RAG + LLM + structured generation)

This is the real platform selling point.

---

# Planned Future Evolution

- recruiter dashboard
- analytics
- benchmarking
- interview replay
- SaaS platform
- enterprise workflows