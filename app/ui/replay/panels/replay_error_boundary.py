# app/ui/replay/panels/replay_error_boundary.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from domain.contracts.replay.replay_session import ReplaySession

EntryContext = Literal["report", "session_list"]

_FAILURE_MESSAGES: tuple[tuple[str, str], ...] = (
    ("SessionHistory not found", "This session is no longer available."),
    (
        "Persistence layer I/O error",
        "Unable to load session. Please try again.",
    ),
)

_DEFAULT_MESSAGE = "An error occurred loading the session. Please try again or contact support."

_ACTION_LABELS: dict[EntryContext, str] = {
    "report": "Return to Report",
    "session_list": "Return to Session List",
}


@dataclass(frozen=True)
class ErrorViewModel:
    """C-09 rendering model (EPIC-04-DATA-MODEL §4.9)."""

    candidate_message: str
    action_label: str


class ReplayErrorBoundary:
    """C-09: candidate-facing error panel; never exposes raw failure_reason."""

    def __init__(
        self,
        session: ReplaySession,
        entry_context: EntryContext = "report",
    ) -> None:
        if session.is_successful:
            raise ValueError("ReplayErrorBoundary requires is_successful=False (I-C09-01).")
        self._session = session
        self._entry_context = entry_context

    @property
    def session(self) -> ReplaySession:
        return self._session

    def render(self) -> ErrorViewModel:
        reason = self._session.failure_reason or ""
        message = _DEFAULT_MESSAGE
        for pattern, candidate_message in _FAILURE_MESSAGES:
            if pattern in reason:
                message = candidate_message
                break

        return ErrorViewModel(
            candidate_message=message,
            action_label=_ACTION_LABELS[self._entry_context],
        )
