# app/graph/replay_graph.py
# EPIC-03 Phase 4b — Replay Graph: standalone single-node LangGraph graph.
#
# Topology (ADR-037 Decision 4): replay_node → END
# State: ReplayGraphState (does not extend InterviewState — I-R03)
# Checkpointing: disabled (Domain Contracts §8.2 — ReplaySession must not be
#   persisted as a LangGraph checkpoint)
# Entry point: "replay"
#
# Architecture invariants enforced here:
#   I-R03: ReplayGraphState does not reference InterviewState.
#   §8.2: checkpointer=None disables LangGraph checkpoint persistence.
#   ADR-037 D4: standalone graph, topologically independent from live session graph.

from __future__ import annotations

from functools import partial
from typing import Callable, Optional

from langgraph.graph import StateGraph, END

from app.core.logger import get_logger
from app.graph.nodes.replay_node import SessionLoader, replay_node
from domain.contracts.replay.replay_graph_state import ReplayGraphState
from domain.contracts.session_history.session_history import SessionHistory

logger = get_logger(__name__)

_REPLAY_NODE_NAME = "replay"


def build_replay_graph(
    session_loader: SessionLoader,
):
    """Construct and compile the Replay Graph.

    Topology: replay_node → END (ADR-037 Decision 4).
    Checkpointing disabled per Domain Contracts §8.2.

    Args:
        session_loader: Read-only callable(session_id) -> Optional[SessionHistory].
            Injected to keep replay_node free of infrastructure imports.

    Returns:
        Compiled LangGraph CompiledGraph ready for invocation.
    """
    graph: StateGraph = StateGraph(ReplayGraphState)

    # Bind session_loader into replay_node via partial (keyword-only arg).
    bound_replay_node = partial(replay_node, session_loader=session_loader)

    graph.add_node(_REPLAY_NODE_NAME, bound_replay_node)
    graph.set_entry_point(_REPLAY_NODE_NAME)
    graph.add_edge(_REPLAY_NODE_NAME, END)

    # checkpointer=None: explicitly disable LangGraph checkpointing.
    # ReplaySession must not be persisted as a checkpoint (Domain Contracts §8.2).
    compiled = graph.compile(checkpointer=None)

    logger.debug("build_replay_graph: Replay Graph compiled (checkpointing disabled)")

    return compiled
