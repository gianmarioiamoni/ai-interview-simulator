# /docs/architecture/runtime-flow.md

# Runtime Flow

## High-Level Runtime Pipeline

START
  ↓
Interview Setup
  ↓
Question Generation
  ↓
Question Presentation
  ↓
Answer Submission
  ↓
Execution (coding/sql only)
  ↓
Evaluation
  ↓
Hint Generation
  ↓
Feedback Generation
  ↓
Decision
  ↓
Retry / Next / Final Report

---

# Runtime Core

The runtime is orchestrated through:

- LangGraph
- InterviewState
- state-driven UI rendering

The system is intentionally state-centric.

The graph mutates semantic state.
The UI derives entirely from state.

---

# Runtime Entry Point

Main entry point:

run_interview_graph(state)

Defined in:

app/runtime/interview_runtime.py

---

# Runtime Graph

Main graph builder:

app/graph/interview_graph.py

Core orchestration:

entry
  ↓
router
  ↓
execution / written
  ↓
evaluation
  ↓
hint
  ↓
feedback
  ↓
decision
  ↓
navigation
  ↓
completion
  ↓
evaluation_aggregate
  ↓
report

---

# Entry Routing

Entry routing is intent-driven.

Current semantic driver:

state.intent

NOT:

state.last_action

---

# Supported Intents

class ActionType(str, Enum):
    RETRY = "retry"
    NEXT = "next"
    GENERATE_REPORT = "generate_report"
    SUBMIT = "submit"
    NONE = "none"

---

# Runtime State Philosophy

The system uses a strongly state-driven architecture.

The UI never decides behavior.
The graph owns orchestration.

---

# Important Runtime Flags

## intent

Represents user-requested action.

Examples:
- submit
- retry
- next
- generate report

---

## is_processing

Represents runtime processing state.

Used for:
- loaders
- button locking
- processing UI

---

## awaiting_user_input

Represents conversational wait state.

Not equivalent to processing state.

---

# Current Graph Nodes

## ExecutionNode

Responsibilities:
- coding execution
- sql execution
- execution result injection

Owns:
- execution results

---

## EvaluationNode

Responsibilities:
- evaluate coding/sql answers
- compute structured evaluation

---

## WrittenEvaluationNode

Responsibilities:
- evaluate written answers

---

## HintNode

Responsibilities:
- generate adaptive hints
- enrich feedback pipeline

---

## FeedbackNode

Responsibilities:
- generate FeedbackBundle
- compute quality
- aggregate dimension signals

---

## DecisionNode

Responsibilities:
- decide retry/next/report actions
- compute allowed actions

---

## NavigationNode

Responsibilities:
- state transitions
- retry/next/report flow

---

## CompletionNode

Responsibilities:
- interview completion detection

---

## EvaluationAggregateNode

Responsibilities:
- aggregate full interview evaluation
- build final evaluation

---

## ReportNode

Responsibilities:
- generate final report

---

# Runtime Ownership Rules

Each node may write a field only if:
- it semantically owns the field
- or the field is None

Critical fields:
- confidence
- retry counts
- evaluation
- control flags

---

# State Machine Philosophy

The runtime is:
- graph-driven
- immutable-safe
- state-derived

No UI-driven orchestration is allowed.

---

# Current Runtime Strengths

- semantic orchestration
- adaptive runtime flow
- executable validation
- state-driven UI
- deterministic transitions

---

# Planned Runtime Evolution

## Full LangGraph orchestration

Current state:
- hybrid orchestration

Target:
- graph-first orchestration

---

# Planned Runtime Improvements

- retrieval orchestration
- follow-up orchestration
- memory-aware runtime
- adaptive interview paths
- difficulty balancing