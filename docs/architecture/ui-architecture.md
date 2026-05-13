# /docs/architecture/ui-architecture.md

# UI Architecture

# Overview

The UI architecture is fully state-driven.

The UI never owns business logic.

The rendering pipeline is:

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
Gradio Outputs

---

# UI Philosophy

The UI layer:
- renders state
- triggers intents
- never orchestrates domain logic

---

# UI State Machine

Defined in:

app/ui/state_machine/ui_state_machine.py

---

# Current UI States

class UIState(Enum):
    SETUP
    PROCESSING
    QUESTION
    FEEDBACK
    REPORT

---

# State Resolution

UI state is derived from:
- interview state
- processing flags
- feedback presence
- completion status

---

# Processing State

The UI processing system is driven by:

state.is_processing

Used for:
- loader visibility
- button disabling
- lock state

---

# Intent System

The UI triggers runtime behavior through:

state.intent

The UI never manipulates graph flow directly.

---

# Current Intent Flow

UI Action
    ↓
intent
    ↓
graph routing
    ↓
state mutation
    ↓
UI rendering

---

# Loader System

## Current Architecture

Loader state is graph-driven.

The UI only renders:
- current_step
- current_progress
- is_processing

---

# Loader Steps

## Setup

- GENERATING_STRUCTURE
- GENERATING_QUESTIONS
- GENERATING_TESTS
- FINALIZING

## Submit

- SUBMITTING
- RUNNING_EXECUTION
- ANALYZING
- GENERATING_FEEDBACK

## Report

- PREPARING_REPORT
- ANALYZING_RESULTS
- GENERATING_REPORT
- FINALIZING_REPORT

---

# UIResponse

Current UI transport object.

Responsibilities:
- semantic UI state
- visibility flags
- labels
- rendering state

---

# Output Contract Refactor

## Current State

Implemented.

The system moved from:
- positional outputs

to:
- semantic output contracts

---

# Current Output Pipeline

UIResponse
    ↓
to_dict()
    ↓
UIOutputAdapter
    ↓
Gradio output list

---

# Output Contract

Single source of truth:

OUTPUT_KEYS

---

# Benefits

- order safety
- mismatch prevention
- easier maintenance
- centralized output contract
- easier testing

---

# Current UI Strengths

- state-driven rendering
- semantic routing
- adaptive buttons
- loader orchestration
- clean output contracts

---

# Planned UI Evolution

## Planned Refactor

Future target:

UIResponse = pure DTO
GradioPresenter = transport layer

Goal:
- remove Gradio dependency from UIResponse

---

# Why This Matters

This would enable:
- frontend portability
- easier testing
- framework independence
- cleaner SRP boundaries

---

# Current Position

The current architecture is already stable and maintainable.

Presenter split is intentionally postponed.

---

# Important UI Invariants

- UI derives from state
- graph owns orchestration
- loaders are state-driven
- buttons derive from allowed_actions
- processing derives from is_processing

---

# Current Technical Debt

Moderate:
- Gradio coupling
- transport leakage into UIResponse

Low urgency.