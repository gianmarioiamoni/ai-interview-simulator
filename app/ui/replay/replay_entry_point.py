# app/ui/replay/replay_entry_point.py

from __future__ import annotations

from dataclasses import dataclass

from app.graph.nodes.replay_node import SessionLoader
from app.graph.replay_graph import build_replay_graph
from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session import ReplaySession


@dataclass(frozen=True)
class ReplayViewRoute:
    """Phase 2 success routing token (C-02 target). Full controller is Phase 3."""

    session: ReplaySession


@dataclass(frozen=True)
class ReplayErrorRoute:
    """Phase 2 failure routing token (C-09 target). Full boundary is Phase 4."""

    session: ReplaySession


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
    ) -> tuple[ReplayViewRoute | None, ReplayErrorRoute | None]:
        """Route solely by ``ReplaySession.is_successful`` (I-C01-03).

        Returns ``(view_route, error_route)`` with exactly one side set.
        Concrete ``ReplayViewController`` / ``ReplayErrorBoundary`` arrive in
        later phases; Phase 2 emits routing tokens only.
        """
        if session.is_successful:
            return (ReplayViewRoute(session=session), None)
        return (None, ReplayErrorRoute(session=session))
