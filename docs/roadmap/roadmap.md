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

Slim down:
- QuestionSelectionService

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

# STEP 5 — Humanizer Refactor

Extract:
- follow-up orchestration
- conversational logic

Into:

HumanizerService

Features:
- max 2 follow-ups
- non-consecutive
- score-triggered

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

QuestionBankLoader
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