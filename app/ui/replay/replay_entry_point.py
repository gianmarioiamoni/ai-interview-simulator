# app/ui/replay/replay_entry_point.py

from __future__ import annotations

from app.graph.nodes.replay_node import SessionLoader
from app.graph.replay_graph import build_replay_graph
from app.ui.replay.panels.replay_error_boundary import ReplayErrorBoundary
from app.ui.replay.replay_view_controller import ReplayViewController
from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session import ReplaySession


class ReplayEntryPoint:
    """C-01: load ReplaySession via Replay Graph; route by ``is_successful``."""

    def __init__(self, session_loader: SessionLoader) -> None:
        self._session_loader = session_loader

    def load(self, session_id: str) -> ReplaySession:
        """Invoke Replay Graph and return the resulting ``ReplaySession``.

        I-C01-01: empty ``session_id`` rejected before graph invocation.
        I-C01-02: result is not persisted.
        I-C01-04: only Replay Graph invocation; no LLM.
        """
        if not session_id:
            raise ValueError("session_id must be non-empty")

        graph = build_replay_graph(self._session_loader)
        output = graph.invoke({"request": ReplayRequest(session_id=session_id)})
        result = output.get("result")
        if result is None:
            raise RuntimeError("Replay Graph returned no ReplaySession result")
        return result

    def route(
        self,
        session: ReplaySession,
    ) -> tuple[ReplayViewController | None, ReplayErrorBoundary | None]:
        """Route solely by ``ReplaySession.is_successful`` (I-C01-03).

        Returns ``(view_controller, error_boundary)`` with exactly one side set.
        """
        if session.is_successful:
            return (ReplayViewController(session), None)
        return (None, ReplayErrorBoundary(session=session))
