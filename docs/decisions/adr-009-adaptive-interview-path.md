# ADR-009 — Adaptive Interview Path

**Status:** Accepted
**Date:** 2026-06-18
**Owner:** Arch

---

## Context

The baseline interview flow presents questions sequentially from a pre-generated list. As the system acquired per-question evaluation signals (scores, weak areas, retrieval memory), it became feasible to select subsequent questions based on candidate performance rather than a fixed plan. Introducing this behaviour unconditionally risked regressing the stable baseline flow and adding un-audited complexity to V1.

## Decision

Adaptive question selection is an opt-in capability gated by the boolean flag `adaptive_interview_enabled` (default `False`). When enabled, a dedicated `AdaptiveNavigationNode` replaces the standard sequential navigation logic and uses `LazyAdaptiveInterviewService` to generate the next question on demand, informed by `retrieval_memory` accumulated during the session.

## Rationale

Defaulting to `False` bounds the blast radius of any regression to sessions that have explicitly opted in. The existing navigation node continues to serve all other sessions without modification. Lazy generation — one question per NEXT action rather than a full upfront plan — keeps latency predictable and avoids over-committing to a plan that may become stale as performance signals accumulate.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Always-on adaptive routing | Unacceptable regression risk for V1; no fallback if adaptive service fails |
| Separate LangGraph for adaptive sessions | Doubles graph maintenance surface; flag-based branching within a single graph is sufficient |
| Pre-generate adaptive plan at session start | Defeats the purpose; plan cannot incorporate live performance signals |

## Consequences

### Positive
- Zero impact on non-adaptive sessions; baseline flow is unchanged.
- Adaptive behaviour is fully testable in isolation via the flag.
- Retrieval memory accumulates incrementally, enabling progressively better question targeting.
- Single graph topology simplifies observability and debugging.

### Negative / Risks
- Two navigation code paths (`navigation_node` and `AdaptiveNavigationNode`) must be kept consistent when shared navigation logic changes.
- Flag-gated code paths require explicit test coverage for both branches.
- `LazyAdaptiveInterviewService` is a hard dependency of `AdaptiveNavigationNode`; injection failure falls back silently to sequential navigation.

## Implementation Evidence

- `domain/contracts/interview_state/base.py` — `adaptive_interview_enabled: bool = False`
- `app/ui/state_handlers/start.py` — sets `adaptive_interview_enabled: True` when adaptive mode is requested
- `app/graph/nodes/adaptive_navigation_node.py` — conditional routing on `state.adaptive_interview_enabled`
- `services/question_intelligence/lazy_adaptive_interview_service.py` — on-demand question generation
- `services/question_intelligence/adaptive_interview_memory_bridge.py` — accumulates retrieval memory per question result
- `app/graph/nodes/completion_node.py` — respects `planned_areas` length under adaptive mode
- `docs/architecture/feature-flags.md` — canonical flag registry

## Related Documents

- `docs/architecture/runtime-flow.md`
- `docs/architecture/feature-flags.md`

## Review Trigger

Adaptive path is promoted to the default navigation strategy (V1.1+), or a bug is traced to divergent behaviour between the two navigation code paths.
