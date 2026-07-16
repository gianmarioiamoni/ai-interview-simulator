# tests/ui/replay/test_replay_performance.py
# EPIC-04 Phase 6 — AA-08 performance profiling gates (20-question fixture).

from __future__ import annotations

import pickle
import time
from typing import Optional

from app.graph.nodes.replay_node import SessionLoader
from app.graph.replay_graph import build_replay_graph
from app.ui.bindings.handlers.replay_layout_coordinator import ReplayLayoutCoordinator
from app.ui.replay.replay_html_composer import compose_success_panels
from app.ui.replay.replay_view_controller import ReplayViewController
from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.session_history.session_history import SessionHistory
from tests.ui.replay.fixtures.session_history_20q import (
    QUESTION_COUNT_20,
    make_session_history_20q,
)

_LOAD_BUDGET_MS = 1000.0
_NAV_BUDGET_MS = 100.0
_MEMORY_BUDGET_BYTES = 500 * 1024


def _loader_for(history: SessionHistory) -> SessionLoader:
    def _loader(session_id: str) -> Optional[SessionHistory]:
        return history if session_id == history.session_id else None

    return _loader


def _build_replay_session(history: SessionHistory) -> ReplaySession:
    graph = build_replay_graph(session_loader=_loader_for(history))
    output = graph.invoke({"request": ReplayRequest(session_id=history.session_id)})
    result = output["result"]
    assert isinstance(result, ReplaySession)
    return result


def test_replay_load_time_20q() -> None:
    """AA-08: replay_node + first render ≤ 1000ms for 20-question fixture."""
    history = make_session_history_20q()
    assert history.question_count == QUESTION_COUNT_20

    coordinator = ReplayLayoutCoordinator(session_loader=_loader_for(history))

    started = time.perf_counter()
    snapshot = coordinator.enter(history.session_id)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    assert snapshot.runtime is not None
    assert snapshot.runtime.controller is not None
    assert snapshot.runtime.controller.session.question_count == QUESTION_COUNT_20
    assert snapshot.question_html
    assert (
        elapsed_ms <= _LOAD_BUDGET_MS
    ), f"Load+first-render exceeded budget: {elapsed_ms:.2f}ms > {_LOAD_BUDGET_MS}ms"


def test_replay_navigation_step_20q() -> None:
    """AA-08: position change + panel re-render ≤ 100ms."""
    history = make_session_history_20q()
    session = _build_replay_session(history)
    controller = ReplayViewController(session)
    # Warm first render outside the measured window.
    _ = compose_success_panels(controller)

    started = time.perf_counter()
    controller.navigate_forward()
    panels = compose_success_panels(controller)
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    assert controller.current_position == 1
    assert "Prompt" in panels["question_html"] or "question" in panels["question_html"].lower()
    assert (
        elapsed_ms <= _NAV_BUDGET_MS
    ), f"Navigation step exceeded budget: {elapsed_ms:.2f}ms > {_NAV_BUDGET_MS}ms"


def test_replay_memory_footprint_20q() -> None:
    """AA-08: ReplaySession in-memory footprint ≤ 500 KB for 20-question fixture."""
    history = make_session_history_20q()
    session = _build_replay_session(history)

    footprint = len(pickle.dumps(session, protocol=pickle.HIGHEST_PROTOCOL))

    assert session.question_count == QUESTION_COUNT_20
    assert footprint <= _MEMORY_BUDGET_BYTES, (
        f"ReplaySession footprint exceeded budget: "
        f"{footprint} bytes > {_MEMORY_BUDGET_BYTES} bytes"
    )
