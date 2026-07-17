# infrastructure/observability/graph_node_logging.py
#
# EPIC-08 P2/C5–C6 — observational wrapper for LangGraph node emission via
# emit_structured_log (OBS-01/02/03/05). Does not alter topology or swallow failures.

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import TypeVar

from infrastructure.observability.structured_log import emit_structured_log

# Core interview cycle nodes (OI-02 batch A).
BATCH_A_GRAPH_NODES: frozenset[str] = frozenset(
    {
        "start_processing",
        "navigation",
        "question",
        "router",
        "execution",
        "evaluation",
        "evaluation_aggregate",
        "feedback",
        "reasoner",
        "hint",
        "decision",
        "written",
        "completion",
    }
)

# Remaining production LangGraph nodes (OI-02 batch B; replay included at C6).
BATCH_B_GRAPH_NODES: frozenset[str] = frozenset(
    {
        "entry",
        "session_close",
        "report",
        "longitudinal_update",
        "replay",
    }
)

PRODUCTION_GRAPH_NODES: frozenset[str] = BATCH_A_GRAPH_NODES | BATCH_B_GRAPH_NODES

_COMPONENT = "langgraph"
_EVENT = "graph_node.execute"

TState = TypeVar("TState")
TResult = TypeVar("TResult")


def instrument_graph_node(
    graph_node: str,
    node: Callable[[TState], TResult],
) -> Callable[[TState], TResult]:
    """
    Wrap a LangGraph node callable for Freeze §6.1 structured emission.

    Observational only: re-raises after failure emission (OBS-03).
    """

    def _wrapped(state: TState) -> TResult:
        started = time.perf_counter()
        session_id = _resolve_session_id(state)
        try:
            result = node(state)
        except Exception as exc:
            emit_structured_log(
                event=_EVENT,
                component=_COMPONENT,
                status="failure",
                level="ERROR",
                session_id=session_id,
                graph_node=graph_node,
                duration_ms=_elapsed_ms(started),
                error_type=type(exc).__name__,
            )
            raise
        emit_structured_log(
            event=_EVENT,
            component=_COMPONENT,
            status="success",
            session_id=session_id,
            graph_node=graph_node,
            duration_ms=_elapsed_ms(started),
        )
        return result

    _wrapped.__name__ = getattr(node, "__name__", graph_node)
    _wrapped.__qualname__ = getattr(node, "__qualname__", graph_node)
    setattr(_wrapped, "__wrapped__", node)
    setattr(_wrapped, "graph_node_name", graph_node)
    return _wrapped


def _resolve_session_id(state: object) -> str | None:
    interview_id = getattr(state, "interview_id", None)
    if interview_id is not None:
        return str(interview_id)

    session_id = getattr(state, "session_id", None)
    if session_id is not None:
        return str(session_id)

    if isinstance(state, Mapping):
        request = state.get("request")
        if request is not None:
            request_session_id = getattr(request, "session_id", None)
            if request_session_id is not None:
                return str(request_session_id)
        mapped = state.get("session_id")
        if mapped is not None:
            return str(mapped)
        mapped_interview = state.get("interview_id")
        if mapped_interview is not None:
            return str(mapped_interview)

    return None


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)
