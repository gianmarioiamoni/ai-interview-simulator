# Graph Node Reference

**Status:** STUB — populate from `app/graph/nodes/` and `app/graph/interview_graph.py`
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

<!-- TODO: Fill each row from actual node implementations -->

| Node | File | Purpose | Inputs (state keys) | Outputs (state keys) | Side Effects |
|---|---|---|---|---|---|
| `entry_node` | `entry_node.py` | — | — | — | — |
| `router_node` | `router_node.py` | Intent routing | `intent` | next node | — |
| `navigation_node` | `navigation_node.py` | Area sequencing | — | — | — |
| `adaptive_navigation_node` | `adaptive_navigation_node.py` | Adaptive routing | — | — | — |
| `question_node` | `question_node.py` | Question selection & delivery | — | — | — |
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

### 3. Routing Logic

<!-- TODO: Conditional edges table -->
<!-- Columns: From | Condition | To -->

### 4. State Keys Reference

<!-- TODO: Key InterviewState fields consumed/produced by nodes -->
<!-- Reference: domain/contracts/interview_state/base.py -->

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
