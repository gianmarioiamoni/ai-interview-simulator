# tests/domain/contracts/replay/test_replay_timeline.py
# EPIC-03 Phase 2d — ReplayTimeline + ReplayTimelineEntry contract tests.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.contracts.replay.replay_timeline import ReplayTimeline, ReplayTimelineEntry


def _entry(position: int = 0, question_id: str = "q-001", question_index: int = 0) -> ReplayTimelineEntry:
    return ReplayTimelineEntry(
        position=position,
        question_id=question_id,
        question_index=question_index,
        area_label="Algorithms",
        question_type="technical",
    )


def _timeline(*entries: ReplayTimelineEntry) -> ReplayTimeline:
    n = len(entries)
    return ReplayTimeline(
        entries=entries,
        total_positions=n,
        first_position=0 if n > 0 else -1,
        last_position=n - 1 if n > 0 else -1,
        is_empty=(n == 0),
    )


class TestReplayTimelineEntryConstruction:

    def test_valid_entry(self):
        e = _entry()
        assert e.position == 0
        assert e.question_id == "q-001"
        assert e.question_index == 0
        assert e.area_label == "Algorithms"
        assert e.question_type == "technical"

    def test_entry_position_zero_accepted(self):
        e = _entry(position=0)
        assert e.position == 0

    def test_entry_position_large_accepted(self):
        e = _entry(position=99)
        assert e.position == 99


class TestReplayTimelineEntryImmutability:

    def test_frozen_raises_on_mutation(self):
        e = _entry()
        with pytest.raises((ValidationError, TypeError)):
            e.position = 5

    def test_frozen_raises_on_question_id_mutation(self):
        e = _entry()
        with pytest.raises((ValidationError, TypeError)):
            e.question_id = "changed"


class TestReplayTimelineEntryExtraForbid:

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            ReplayTimelineEntry(
                position=0,
                question_id="q-001",
                question_index=0,
                area_label="Algorithms",
                question_type="technical",
                extra_field="bad",  # type: ignore[call-arg]
            )


class TestReplayTimelineEntryFieldConstraints:

    def test_position_negative_rejected(self):
        with pytest.raises(ValidationError):
            _entry(position=-1)

    def test_question_id_empty_rejected(self):
        with pytest.raises(ValidationError):
            ReplayTimelineEntry(
                position=0,
                question_id="",
                question_index=0,
                area_label="Algorithms",
                question_type="technical",
            )


class TestReplayTimelineConstruction:

    def test_empty_timeline(self):
        t = _timeline()
        assert t.total_positions == 0
        assert t.first_position == -1
        assert t.last_position == -1
        assert t.is_empty is True
        assert t.entries == ()

    def test_single_entry_timeline(self):
        e = _entry()
        t = _timeline(e)
        assert t.total_positions == 1
        assert t.first_position == 0
        assert t.last_position == 0
        assert t.is_empty is False

    def test_three_entry_timeline(self):
        entries = (
            _entry(position=0, question_id="q-001", question_index=0),
            _entry(position=1, question_id="q-002", question_index=1),
            _entry(position=2, question_id="q-003", question_index=2),
        )
        t = _timeline(*entries)
        assert t.total_positions == 3
        assert t.first_position == 0
        assert t.last_position == 2
        assert t.is_empty is False


class TestReplayTimelineImmutability:

    def test_frozen_raises_on_mutation(self):
        t = _timeline()
        with pytest.raises((ValidationError, TypeError)):
            t.total_positions = 5

    def test_frozen_raises_on_entries_mutation(self):
        t = _timeline()
        with pytest.raises((ValidationError, TypeError)):
            t.entries = ()


class TestReplayTimelineExtraForbid:

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            ReplayTimeline(
                entries=(),
                total_positions=0,
                first_position=-1,
                last_position=-1,
                is_empty=True,
                extra_field="bad",  # type: ignore[call-arg]
            )


class TestReplayTimelineConsistencyValidator:

    def test_total_positions_mismatch_rejected(self):
        with pytest.raises(ValidationError, match="total_positions"):
            ReplayTimeline(
                entries=(_entry(),),
                total_positions=2,
                first_position=0,
                last_position=0,
                is_empty=False,
            )

    def test_first_position_wrong_rejected(self):
        with pytest.raises(ValidationError, match="first_position"):
            ReplayTimeline(
                entries=(_entry(),),
                total_positions=1,
                first_position=1,
                last_position=0,
                is_empty=False,
            )

    def test_last_position_wrong_rejected(self):
        with pytest.raises(ValidationError, match="last_position"):
            ReplayTimeline(
                entries=(_entry(),),
                total_positions=1,
                first_position=0,
                last_position=5,
                is_empty=False,
            )

    def test_is_empty_wrong_for_non_empty_rejected(self):
        with pytest.raises(ValidationError, match="is_empty"):
            ReplayTimeline(
                entries=(_entry(),),
                total_positions=1,
                first_position=0,
                last_position=0,
                is_empty=True,
            )

    def test_empty_timeline_wrong_first_rejected(self):
        with pytest.raises(ValidationError, match="first_position"):
            ReplayTimeline(
                entries=(),
                total_positions=0,
                first_position=0,
                last_position=-1,
                is_empty=True,
            )
