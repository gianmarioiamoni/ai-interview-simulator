# tests/ui/replay/test_replay_navigation_bar.py

from __future__ import annotations

from app.ui.replay.panels.replay_navigation_bar import ReplayNavigationBar
from domain.contracts.replay.replay_timeline import ReplayTimeline, ReplayTimelineEntry


def _timeline(question_count: int) -> ReplayTimeline:
    if question_count == 0:
        return ReplayTimeline(
            entries=(),
            total_positions=0,
            first_position=-1,
            last_position=-1,
            is_empty=True,
        )
    entries = tuple(
        ReplayTimelineEntry(
            position=i,
            question_id=f"q-{i:03d}",
            question_index=i,
            area_label="Algorithms",
            question_type="technical",
        )
        for i in range(question_count)
    )
    return ReplayTimeline(
        entries=entries,
        total_positions=question_count,
        first_position=0,
        last_position=question_count - 1,
        is_empty=False,
    )


def test_progress_label_at_first_position() -> None:
    bar = ReplayNavigationBar(timeline=_timeline(3), current_position=0)
    model = bar.render()
    assert model.display_label == "Question 1 of 3"
    assert model.backward_enabled is False
    assert model.forward_enabled is True
    assert bar.is_at_first is True
    assert bar.is_at_last is False


def test_progress_label_at_last_position() -> None:
    bar = ReplayNavigationBar(timeline=_timeline(3), current_position=2)
    model = bar.render()
    assert model.display_label == "Question 3 of 3"
    assert model.backward_enabled is True
    assert model.forward_enabled is False
    assert bar.is_at_first is False
    assert bar.is_at_last is True


def test_middle_position_both_controls_enabled() -> None:
    bar = ReplayNavigationBar(timeline=_timeline(3), current_position=1)
    model = bar.render()
    assert model.display_label == "Question 2 of 3"
    assert model.backward_enabled is True
    assert model.forward_enabled is True


def test_empty_timeline_disables_controls_and_shows_no_questions() -> None:
    from app.ui.presentation import REPLAY_EMPTY_KEY, get_empty_copy_entry

    bar = ReplayNavigationBar(timeline=_timeline(0), current_position=0)
    model = bar.render()
    assert model.display_label == get_empty_copy_entry(REPLAY_EMPTY_KEY).message_text
    assert model.is_empty is True
    assert model.forward_enabled is False
    assert model.backward_enabled is False
    assert bar.is_at_first is True
    assert bar.is_at_last is True
    assert bar.emit_forward() is None
    assert bar.emit_backward() is None


def test_emit_forward_only_when_enabled() -> None:
    at_first = ReplayNavigationBar(timeline=_timeline(2), current_position=0)
    assert at_first.emit_forward() == "navigate_forward"
    assert at_first.emit_backward() is None

    at_last = ReplayNavigationBar(timeline=_timeline(2), current_position=1)
    assert at_last.emit_forward() is None
    assert at_last.emit_backward() == "navigate_backward"


def test_navigation_bar_does_not_own_position_state() -> None:
    timeline = _timeline(3)
    bar = ReplayNavigationBar(timeline=timeline, current_position=0)
    assert bar.render().current_position == 0

    bar_moved = ReplayNavigationBar(timeline=timeline, current_position=2)
    assert bar_moved.render().current_position == 2
    assert bar.render().current_position == 0
