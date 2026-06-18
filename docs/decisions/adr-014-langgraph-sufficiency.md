# ADR-014 — LangGraph Sufficiency (No Migration)

**Status:** Accepted
**Date:** 2026-06-18
**Owner:** Arch

---

## Context

As the interview graph grew to 15 nodes with conditional routing, adaptive branching, and multi-path execution (written vs. coding), the question arose whether LangGraph remained an appropriate orchestration substrate or whether migration to a custom orchestrator or an alternative framework was warranted. The evaluation was triggered by concerns about API stability, debugging ergonomics, and whether LangGraph's abstractions could express all required routing patterns without workarounds.

## Decision

LangGraph is sufficient for the current and planned orchestration requirements. No migration is initiated. The existing `StateGraph`-based graph in `app/graph/interview_graph.py` remains the authoritative orchestration layer.

## Rationale

The graph covers all 15 nodes using native LangGraph constructs — `add_node`, `add_edge`, `add_conditional_edges`, and `set_entry_point` — without any workarounds. All routing patterns required (intent-driven entry dispatch, question-type branching, decision-gated loop, adaptive navigation, report generation) are expressible directly. Migration cost — rewiring 15 nodes, rewriting routing logic, re-establishing state propagation, and re-validating all test coverage — is not justified by any identified capability gap. LangGraph version is pinned in `pyproject.toml`, making API-stability risk manageable.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Custom Python orchestrator | Eliminates framework overhead but requires reimplementing state propagation, conditional routing, and graph compilation from scratch; high maintenance burden |
| Temporal / Prefect | Designed for long-running distributed workflows with persistence and retry semantics; adds significant operational infrastructure for a session-scoped, in-memory interview graph |
| CrewAI / AutoGen | Agent-collaboration frameworks optimised for multi-agent delegation; the interview graph is a deterministic state machine, not an autonomous agent network |
| LangChain Expression Language (LCEL) | Linear pipeline model; cannot natively express the cyclic routing (decision → navigation loop) required by the interview flow |

## Consequences

### Positive
- No migration cost; existing node implementations, routing functions, and test coverage are preserved.
- LangGraph's `StateGraph` makes routing logic explicit and traceable via `add_conditional_edges`.
- State propagation through `InterviewState` is handled by the framework's state-merging semantics.
- Graph topology is inspectable and debuggable through LangGraph's built-in tooling.

### Negative / Risks
- LangGraph API changes require version pinning; a major version bump may necessitate node-level refactoring.
- LangGraph's compilation model (`.compile()`) makes runtime graph modification impossible; structural changes require a restart.
- Debugging complex conditional edge paths requires familiarity with LangGraph's internal routing resolution.

## Implementation Evidence

- `app/graph/interview_graph.py` — 15 nodes, 4 conditional edge sets, full session lifecycle
- `pyproject.toml` — pinned `langgraph` version
- `OPERATIONAL_PROJECT_STATUS.md` — `LANGGRAPH_ALREADY_SUFFICIENT` verdict from architectural review

## Related Documents

- `docs/architecture/system_overview.md`
- `docs/architecture/runtime-flow.md`
- `docs/architecture/graph-nodes.md`

## Review Trigger

A LangGraph breaking change that cannot be absorbed with a minor refactor, or an orchestration requirement that cannot be expressed using `StateGraph` conditional routing (e.g., true parallelism, persistent cross-session graph state, or distributed node execution).
