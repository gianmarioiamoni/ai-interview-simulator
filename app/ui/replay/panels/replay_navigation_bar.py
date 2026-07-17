# app/ui/replay/panels/replay_navigation_bar.py
# EPIC-07 P5/C10 — empty timeline uses empty.replay.no_questions catalog.

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.ui.presentation.question_feedback_surface import surface_status_message
from app.ui.presentation.replay_surface import present_replay_surface
from domain.contracts.replay.replay_timeline import ReplayTimeline

NavigationSignal = Literal["navigate_forward", "navigate_backward"]


@dataclass(frozen=True)
class NavigationViewModel:
    """C-04 rendering model (EPIC-04-DATA-MODEL §4.4). Position not owned here."""

    current_position: int
    total_positions: int
    display_label: str
    is_empty: bool
    backward_enabled: bool
    forward_enabled: bool


class ReplayNavigationBar:
    """C-04: progress indicator and controls; emits signals only (I-C04-05)."""

    def __init__(self, timeline: ReplayTimeline, current_position: int) -> None:
        self._timeline = timeline
        self._current_position = current_position

    def render(self) -> NavigationViewModel:
        timeline = self._timeline
        if timeline.is_empty:
            empty_surface = present_replay_surface(has_questions=False)
            return NavigationViewModel(
                current_position=self._current_position,
                total_positions=0,
                display_label=surface_status_message(empty_surface),
                is_empty=True,
                backward_enabled=False,
                forward_enabled=False,
            )

        return NavigationViewModel(
            current_position=self._current_position,
            total_positions=timeline.total_positions,
            display_label=(f"Question {self._current_position + 1} of {timeline.total_positions}"),
            is_empty=False,
            backward_enabled=self._current_position > timeline.first_position,
            forward_enabled=self._current_position < timeline.last_position,
        )

    @property
    def is_at_first(self) -> bool:
        model = self.render()
        return model.is_empty or not model.backward_enabled

    @property
    def is_at_last(self) -> bool:
        model = self.render()
        return model.is_empty or not model.forward_enabled

    def emit_forward(self) -> NavigationSignal | None:
        """Emit ``navigate_forward`` only when the forward control is enabled."""
        if self.render().forward_enabled:
            return "navigate_forward"
        return None

    def emit_backward(self) -> NavigationSignal | None:
        """Emit ``navigate_backward`` only when the backward control is enabled."""
        if self.render().backward_enabled:
            return "navigate_backward"
        return None
