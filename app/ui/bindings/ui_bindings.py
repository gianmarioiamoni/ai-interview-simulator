# app/ui/bindings/ui_bindings.py

from __future__ import annotations

from typing import Optional

from app.graph.nodes.replay_node import SessionLoader
from app.ui.bindings.orchestrators.ui_event_orchestrator import UIEventOrchestrator
from domain.contracts.session_history.session_history import SessionHistory


def _default_session_loader(_session_id: str) -> Optional[SessionHistory]:
    """Default loader until persistence wiring is available (EPIC-05+)."""
    return None


def bind_events(
    components,
    session_loader: SessionLoader | None = None,
) -> None:
    orchestrator = UIEventOrchestrator(
        components,
        session_loader=session_loader or _default_session_loader,
    )
    orchestrator.bind()
