# tests/performance/slo_p.py
# EPIC-V13-09 C4 — SLO-P harness: replay_node on materialized SessionHistory (AR-04, RPL-*).

from __future__ import annotations

from typing import Optional

from app.graph.nodes.replay_node import SessionLoader
from app.graph.replay_graph import build_replay_graph
from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.session_history.session_history import SessionHistory
from tests.performance.helpers import measure_wall_clock_ms
from tests.ui.replay.fixtures.session_history_20q import (
    QUESTION_COUNT_20,
    make_session_history_20q,
)

# Implementation Plan §3 / AR-04 absolute target.
SLO_P_TARGET_MS = 1000.0


def materialized_session_loader(history: SessionHistory) -> SessionLoader:
    """In-memory SessionLoader — RPL-02/03 (materialized artifact, not durable DB I/O)."""

    def _loader(session_id: str) -> Optional[SessionHistory]:
        return history if session_id == history.session_id else None

    return _loader


def run_replay_reconstruction(history: SessionHistory) -> ReplaySession:
    """
    Reconstruct ReplaySession via replay graph (sole node: replay_node).

    RPL-01/05: wall-clock reconstruction path; LLM-free; no ReplaySession cache (RPL-04).
    """
    graph = build_replay_graph(session_loader=materialized_session_loader(history))
    output = graph.invoke({"request": ReplayRequest(session_id=history.session_id)})
    result = output["result"]
    if not isinstance(result, ReplaySession):
        raise TypeError(f"Unexpected replay result type: {type(result)!r}")
    return result


def measure_replay_reconstruction_ms(
    history: SessionHistory | None = None,
) -> tuple[ReplaySession, float, SessionHistory]:
    """AR-04 / MEAS-06: measure replay_node reconstruction from materialized history."""
    materialized = history if history is not None else make_session_history_20q()
    if materialized.question_count < QUESTION_COUNT_20:
        raise ValueError(
            f"SLO-P fixture must retain ≥{QUESTION_COUNT_20} questions; "
            f"got {materialized.question_count}"
        )

    session, elapsed_ms = measure_wall_clock_ms(
        lambda: run_replay_reconstruction(materialized)
    )
    return session, elapsed_ms, materialized
