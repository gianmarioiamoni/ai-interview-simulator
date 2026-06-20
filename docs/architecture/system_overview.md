# /docs/architecture/system-overview.md

# System Overview

# Project Vision

AI Interview Simulator is an AI-native technical interview platform designed to simulate realistic engineering interviews through:

- adaptive question generation
- executable coding validation
- structured semantic evaluation
- dynamic feedback generation
- final hiring assessment

The long-term objective is to build a production-grade AI interviewing platform suitable for:
- freelancers
- recruiting agencies
- technical screening providers
- enterprise hiring workflows

---

# Core Strategic Differentiator

The most important differentiator is NOT:
- LangGraph
- evaluation
- Gradio UI

The strongest differentiator is:

Hybrid Question Intelligence Engine
(RAG + LLM + structured generation)

This is considered the primary strategic asset of the platform.

---

# Architectural Philosophy

The system follows these principles:

- state-driven orchestration
- graph-based runtime
- strict separation of concerns
- semantic ownership of state
- immutable state transitions
- framework-independent domain layer
- adaptive AI orchestration

---

# High-Level Architecture

Frontend (Gradio UI)
    ↓
UI State Machine
    ↓
UI Response Builder
    ↓
Runtime Graph (LangGraph)
    ↓
Application Services
    ↓
Domain Contracts
    ↓
Infrastructure Layer

---

# Main Architectural Layers

# 1. UI Layer

Location:

app/ui/

Responsibilities:
- render state
- collect user inputs
- trigger intents
- display feedback
- display loaders
- display reports

The UI never owns orchestration logic.

---

# 2. Runtime Layer

Location:

app/runtime/
app/graph/

Responsibilities:
- orchestrate execution flow
- coordinate graph nodes
- manage semantic transitions

Core technology:
- LangGraph

---

# 3. Application Layer

Location:

app/application/
services/

Responsibilities:
- orchestration services
- execution coordination
- evaluation services
- retrieval services
- report generation

---

# 4. Domain Layer

Location:

domain/contracts/
domain/policies/

Responsibilities:
- domain contracts
- invariants
- policies
- semantic ownership

The domain layer must remain framework-independent.

---

# 5. Infrastructure Layer

Location:

infrastructure/

Responsibilities:
- LLM adapters
- execution sandboxes
- persistence
- embeddings
- vector stores
- external integrations

---

# Core Runtime Model

The entire system revolves around:

InterviewState

The state is:
- semantic
- immutable-safe
- graph-driven

The UI derives entirely from state.

---

# Runtime Orchestration

Main runtime orchestrator:

run_interview_graph(state)

Graph nodes:
- execution
- evaluation
- feedback
- hint
- decision
- navigation
- completion
- aggregation
- report

---

# Current Runtime Flow

Interview Setup
    ↓
Question Generation
    ↓
Question Presentation
    ↓
Answer Submission
    ↓
Execution
    ↓
Evaluation
    ↓
Feedback
    ↓
Decision
    ↓
Retry / Next
    ↓
Final Report

---

# Current Question Types

Supported:
- written questions
- coding questions
- SQL/database questions

---

# Evaluation System

The evaluation system combines:
- executable validation
- LLM semantic evaluation
- structured scoring
- dimension aggregation

Current dimensions:
- problem solving
- technical depth
- system design

---

# Feedback System

The platform generates:
- structured feedback
- adaptive hints
- retry guidance
- final decision rationale

Current architecture:
- FeedbackBundle
- block-based feedback system
- AI-generated narratives

---

# Current UI Architecture

The UI is fully state-driven.

Pipeline:

InterviewState
    ↓
UIStateMachine
    ↓
UIResponseBuilder
    ↓
UIResponse
    ↓
UIOutputAdapter
    ↓
Gradio outputs

---

# Current UI Features

- adaptive loaders
- state-driven rendering
- semantic output contract
- processing lock system
- dynamic buttons
- final report rendering

---

# Output Contract Refactor

Implemented architecture:

UIResponse
    ↓
semantic dict contract
    ↓
UIOutputAdapter
    ↓
Gradio positional outputs

Benefits:
- safer output evolution
- centralized contract
- reduced mismatch bugs

---

# Current State Flags

Important runtime flags:

## intent

Represents semantic user action.

Examples:
- submit
- retry
- next
- generate report

---

## is_processing

Represents processing state.

Used for:
- loaders
- UI locking
- button disabling

---

## awaiting_user_input

Represents conversational wait state.

Not equivalent to processing state.

---

# Loader System

Current loaders are:
- fully state-driven
- graph-driven
- semantic

Loader groups:
- setup
- submit
- report

---

# Current AI Components

## Question Intelligence

Hybrid generation system:
- retrieval (`QuestionRetrievalService`)
- per-area assembly (`AreaQuestionBuilder`)
- set orchestration (`QuestionSetBuilder`, `LazyAdaptiveInterviewService`)
- LLM generation

---

## Evaluation

Combines:
- execution
- semantic evaluation (WrittenEvaluationNode / QuestionEvaluationService)
- scoring (InterviewScoringEngine)
- aggregation (EvaluationAggregateNode / InterviewEvaluationService)

---

## Narrative Service

Generates:
- hiring rationale
- blockers
- strengths
- report narratives

---

# Current Technical Stack

Frontend:
- Gradio

Backend:
- Python

Runtime:
- LangGraph

LLM orchestration:
- LangChain

Execution:
- Python sandbox
- SQLite

Vector retrieval:
- Chroma (active — production usage)

Deployment target:
- HuggingFace Spaces

---

# Current Strengths

- state-driven architecture
- graph orchestration
- executable validation
- adaptive evaluation
- semantic feedback pipeline
- clean runtime layering

---

# Current Strategic Focus

Highest-value investment area:

Question Intelligence Engine

Specifically:
- retrieval quality
- generation diversity
- adaptive questioning
- semantic balancing

---

# Planned Major Evolutions

## Runtime

- deeper LangGraph orchestration
- adaptive graph branching
- memory-aware interviews

---

## Question Intelligence

- retrieval query builder
- dataset ingestion
- semantic deduplication
- difficulty balancing

---

## Evaluation

- richer execution analysis
- weighted dimensions
- follow-up orchestration

---

## UI

- presenter separation
- frontend portability
- richer streaming

---

# Long-Term Vision

The long-term target is an enterprise-grade AI interviewing platform with:

- adaptive interviews
- recruiter analytics
- benchmarking
- interview replay
- candidate comparison
- organization-level insights
- SaaS delivery
- multi-tenant architecture