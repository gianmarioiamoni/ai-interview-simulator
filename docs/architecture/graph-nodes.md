# Graph Node Reference

**Status:** Partial — `question_node`, `navigation_node`, `adaptive_navigation_node` documented below; remaining nodes are stubs
**Owner:** Arch
**SSOT For:** Per-node inputs, outputs, side-effects, routing edges
**Update Trigger:** Any node add/remove/change
**ADR:** ADR-001, ADR-014

---

## Sections (to fill)

### 1. Graph Overview

<!-- TODO: Mermaid diagram of full node graph with conditional edges -->
<!-- Entry: entry_node → router_node → [navigation | question | execution | written | ...] -->

### 2. Node Inventory

| Node | File | Purpose | Inputs (state keys) | Outputs (state keys) | Side Effects |
|---|---|---|---|---|---|
| `entry_node` | `entry_node.py` | — | — | — | — |
| `router_node` | `router_node.py` | Intent routing | `intent` | next node | — |
| `navigation_node` | `navigation_node.py` | Area sequencing; advances `current_question_index` on NEXT | `intent`, `current_question_index`, `last_feedback_bundle` | `current_question_index`, `last_question_context`, `question_display_text` (cleared), `last_feedback_bundle` (cleared) | none |
| `adaptive_navigation_node` | `adaptive_navigation_node.py` | Adaptive routing; same as navigation_node + retrieval memory | `intent`, `current_question_index`, `retrieval_memory` | `current_question_index`, `last_question_context`, `question_display_text` (cleared), `questions` (extended adaptively) | none |
| `question_node` | `question_node.py` | Humanizer invocation & question delivery | `current_question`, `enable_humanizer`, `last_feedback_bundle`, `last_question_context`, `chat_history`, `follow_up_count` | `chat_history`, `question_display_text`, `follow_up_count`, `last_humanizer_follow_up`, `memory_context` | LLM call (HumanizerService) |
| `execution_node` | `execution_node.py` | Code/SQL execution | — | — | — |
| `written_node` | `written_node.py` | Written answer intake | — | — | — |
| `evaluation_node` | `evaluation_node.py` | Answer scoring | — | — | — |
| `evaluation_aggregate_node` | `evaluation_aggregate_node.py` | Score aggregation | — | — | — |
| `hint_node` | `hint_node.py` | Hint delivery | — | — | — |
| `feedback_node` | `feedback_node.py` | Feedback generation | — | — | — |
| `decision_node` | `decision_node.py` | Next-action decision | — | — | — |
| `completion_node` | `completion_node.py` | Interview completion | — | — | — |
| `report_node` | `report_node.py` | Report generation | — | — | — |
| `start_processing_node` | `start_processing_node.py` | Processing flag | — | — | — |

### 2a. question_node — Humanizer Integration Detail

**File:** `app/graph/nodes/question_node.py`

**Behavior per path:**

| Condition | Action |
|---|---|
| `enable_humanizer=False` | Stores `question.prompt` directly in `question_display_text` and `chat_history` |
| `question.type != WRITTEN` | Stores `question.prompt` directly (Humanizer applies to WRITTEN only) |
| `question.type == WRITTEN` | Calls `HumanizerService.humanize()` → stores LLM output in `question_display_text` |
| LLM exception | Falls back to `question.prompt`; graph continues (no abort) |

**Score propagation (C1 fix):**
- Primary: `last_feedback_bundle.overall_quality.rank()`
- Fallback: `last_question_context.quality_rank` (bundle is cleared by navigation_node before question_node runs)

**State keys written:**

| Key | Description |
|---|---|
| `question_display_text` | Humanized text (or raw prompt as fallback). Read by `DisplaySection` for rendering. |
| `follow_up_count` | Incremented when policy decision is `FOLLOW_UP` |
| `last_humanizer_follow_up` | Bool flag; true when last turn was a follow-up |
| `chat_history` | Appended with displayed question text |
| `memory_context` | Updated via `InterviewMemoryUpdater` |

**Humanizer policy decisions:**

| Decision | Condition |
|---|---|
| `DIRECT_QUESTION` | First question or no prior context |
| `REMARK_PLUS_QUESTION` | Prior answer available |
| `FOLLOW_UP` | `last_answer_score >= FOLLOW_UP_SCORE_THRESHOLD` AND `HUMANIZER_FOLLOW_UP_ENABLED=True` AND `follow_up_count < MAX_FOLLOW_UPS` |

### 2b. navigation_node / adaptive_navigation_node — Humanizer Integration Detail

**On every index-advancing NEXT:**
- `last_question_context` is set to a `LastQuestionContext` snapshot of the departing question (captures `quality_rank`, `answer_content`, `question_area` before `last_feedback_bundle` is cleared)
- `question_display_text` is set to `None` (prevents stale prior-question text)
- `last_feedback_bundle` is set to `None`

**`LastQuestionContext` fields:** `question_id`, `question_prompt`, `question_type`, `question_area`, `answer_content`, `quality_rank`

### 3. Routing Logic

<!-- TODO: Conditional edges table -->
<!-- Columns: From | Condition | To -->

### 4. State Keys Reference

<!-- Reference: domain/contracts/interview_state/base.py -->

| Key | Type | Set By | Consumed By | Notes |
|---|---|---|---|---|
| `question_display_text` | `str \| None` | `question_node` | `DisplaySection` | Humanized question text. `None` on session start, cleared on navigation NEXT. |
| `last_question_context` | `LastQuestionContext \| None` | `navigation_node`, `adaptive_navigation_node` | `question_node` | Snapshot of departing question before index advances. |
| `enable_humanizer` | `bool` | `factory.create_initial()` via `settings.humanizer_enabled` | `question_node` | Gates Humanizer LLM call. |
| `follow_up_count` | `int` | `question_node` | `HumanizerPolicyEngine` | Tracks follow-ups used; capped at `MAX_FOLLOW_UPS_PER_INTERVIEW`. |
| `last_humanizer_follow_up` | `bool` | `question_node` | `HumanizerPolicyEngine` | Prevents consecutive follow-ups. |

### 5. Adding a New Node

<!-- TODO: Step-by-step extension guide -->
1. Create `app/graph/nodes/<name>_node.py`
2. Wire into `app/graph/interview_graph.py` — `add_node()` + `add_conditional_edges()`
3. Add intent/routing condition
4. Add tests in `tests/graph/nodes/test_<name>_node.py`

---

## Cross-References

- `runtime-flow.md` — sequence and intent routing overview
- ADR-001 — intent-driven routing rationale
- ADR-014 — LangGraph sufficiency decision
- `domain-contracts.md` — `InterviewState` contract
