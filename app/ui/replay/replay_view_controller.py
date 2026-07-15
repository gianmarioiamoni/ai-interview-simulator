# app/ui/replay/replay_view_controller.py

from __future__ import annotations

from domain.contracts.replay.replay_question_record import ReplayQuestionRecord
from domain.contracts.replay.replay_session import ReplaySession


class ReplayViewController:
    """C-02: owns ``current_position``; derives ``current_record``; no services."""

    def __init__(self, session: ReplaySession) -> None:
        self._session = session
        self._current_position = 0

    @property
    def session(self) -> ReplaySession:
        return self._session

    @property
    def current_position(self) -> int:
        return self._current_position

    @property
    def current_record(self) -> ReplayQuestionRecord:
        """I-C02-04: pure index access into ``question_results``."""
        return self._session.question_results[self._current_position]

    @property
    def is_at_first(self) -> bool:
        timeline = self._session.timeline
        if timeline.is_empty:
            return True
        return self._current_position == timeline.first_position

    @property
    def is_at_last(self) -> bool:
        timeline = self._session.timeline
        if timeline.is_empty:
            return True
        return self._current_position == timeline.last_position

    def navigate_forward(self) -> None:
        """Advance by 1; clamp at ``timeline.last_position`` (I-C02-01, I-C02-02)."""
        timeline = self._session.timeline
        if timeline.is_empty:
            return
        if self._current_position < timeline.last_position:
            self._current_position += 1

    def navigate_backward(self) -> None:
        """Retreat by 1; clamp at ``timeline.first_position`` (I-C02-01, I-C02-02)."""
        timeline = self._session.timeline
        if timeline.is_empty:
            return
        if self._current_position > timeline.first_position:
            self._current_position -= 1
