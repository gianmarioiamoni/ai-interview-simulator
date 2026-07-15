# app/ui/replay/replay_context.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayContext:
    """UI-layer REPLAY signal (not a domain contract; not persisted).

    When ``is_active=True``, ``UIStateMachine.resolve`` returns ``UIState.REPLAY``.
    """

    session_id: str
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id must be non-empty")
