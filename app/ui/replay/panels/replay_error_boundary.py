# app/ui/replay/panels/replay_error_boundary.py
# EPIC-04 C-09 + EPIC-07 C4 — align REPLAY_ENTER with CandidateFacingError catalog (AR-09).

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.ui.presentation.async_boundary import AsyncBoundary
from app.ui.presentation.boundary_error_emission import emit_boundary_error
from app.ui.presentation.candidate_facing_error import CandidateFacingError
from domain.contracts.replay.replay_session import ReplaySession

EntryContext = Literal["report", "session_list"]

_ACTION_LABELS: dict[EntryContext, str] = {
    "report": "Return to Report",
    "session_list": "Return to Session List",
}


@dataclass(frozen=True)
class ErrorViewModel:
    """C-09 rendering model (EPIC-04-DATA-MODEL §4.9); message from EPIC-07 §5.1 catalog."""

    candidate_message: str
    action_label: str


class ReplayErrorBoundary:
    """Candidate-facing replay failure panel; catalog message only (no raw failure_reason)."""

    def __init__(
        self,
        session: ReplaySession | None = None,
        entry_context: EntryContext = "report",
        *,
        candidate_facing_error: CandidateFacingError | None = None,
    ) -> None:
        if session is not None and session.is_successful:
            raise ValueError("ReplayErrorBoundary requires is_successful=False (I-C09-01).")
        if session is None and candidate_facing_error is None:
            raise ValueError(
                "ReplayErrorBoundary requires a failed session or candidate_facing_error."
            )
        self._session = session
        self._entry_context = entry_context
        self._error = candidate_facing_error or emit_boundary_error(
            AsyncBoundary.REPLAY_ENTER
        )
        if self._error.boundary is not AsyncBoundary.REPLAY_ENTER:
            raise ValueError("ReplayErrorBoundary requires boundary=REPLAY_ENTER.")

    @property
    def session(self) -> ReplaySession | None:
        return self._session

    @property
    def candidate_facing_error(self) -> CandidateFacingError:
        return self._error

    def render(self) -> ErrorViewModel:
        return ErrorViewModel(
            candidate_message=self._error.message_text,
            action_label=_ACTION_LABELS[self._entry_context],
        )
