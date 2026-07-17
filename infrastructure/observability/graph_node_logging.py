# infrastructure/observability/graph_node_logging.py
#
# EPIC-08 P2/C5 — observational wrapper for LangGraph node emission via
# emit_structured_log (OBS-01/02/03). Does not alter topology or swallow failures.

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from infrastructure.observability.structured_log import emit_structured_log

# Core interview cycle nodes (OI-02 batch A). Batch B = remaining production nodes.
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

BATCH_B_GRAPH_NODES: frozenset[str] = frozenset(
    {
        "entry",
        "session_close",
        "report",
        "longitudinal_update",
    }
)

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
        session_id = getattr(state, "interview_id", None)
        if session_id is not None:
            session_id = str(session_id)
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


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000.0, 3)
