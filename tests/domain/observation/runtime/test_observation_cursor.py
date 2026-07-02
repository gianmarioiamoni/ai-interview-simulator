# tests/domain/observation/runtime/test_observation_cursor.py

from __future__ import annotations

import pytest

from domain.observation.runtime.observation_cursor import ObservationCursor
from tests.domain.observation.runtime.conftest import make_obs


class TestObservationCursorBasic:
    def test_empty_cursor_exhausted(self):
        cursor = ObservationCursor(())
        assert cursor.exhausted
        assert cursor.total == 0
        assert cursor.remaining == 0

    def test_next_advances_position(self):
        obs = [make_obs(i) for i in range(3)]
        cursor = ObservationCursor.from_list(obs)
        assert cursor.position == 0
        cursor.next()
        assert cursor.position == 1

    def test_next_returns_none_when_exhausted(self):
        cursor = ObservationCursor(())
        assert cursor.next() is None

    def test_peek_does_not_advance(self):
        obs = make_obs(0)
        cursor = ObservationCursor((obs,))
        peeked = cursor.peek()
        assert peeked == obs
        assert cursor.position == 0

    def test_peek_returns_none_when_exhausted(self):
        cursor = ObservationCursor(())
        assert cursor.peek() is None

    def test_remaining_decreases(self):
        cursor = ObservationCursor.from_list([make_obs(i) for i in range(5)])
        assert cursor.remaining == 5
        cursor.next()
        assert cursor.remaining == 4


class TestObservationCursorSeek:
    def test_seek_to_valid_position(self):
        cursor = ObservationCursor.from_list([make_obs(i) for i in range(5)])
        cursor.seek(3)
        assert cursor.position == 3

    def test_seek_to_end(self):
        cursor = ObservationCursor.from_list([make_obs(i) for i in range(5)])
        cursor.seek(5)
        assert cursor.exhausted

    def test_seek_out_of_range_raises(self):
        cursor = ObservationCursor.from_list([make_obs(i) for i in range(3)])
        with pytest.raises(ValueError):
            cursor.seek(10)

    def test_reset_returns_to_start(self):
        cursor = ObservationCursor.from_list([make_obs(i) for i in range(3)])
        cursor.next()
        cursor.next()
        cursor.reset()
        assert cursor.position == 0


class TestObservationCursorCollect:
    def test_collect_remaining_exhausts_cursor(self):
        obs = [make_obs(i) for i in range(4)]
        cursor = ObservationCursor.from_list(obs)
        cursor.next()  # skip one
        remaining = cursor.collect_remaining()
        assert len(remaining) == 3
        assert cursor.exhausted

    def test_skip_while_advances_past_matching(self):
        obs = [make_obs(i, confidence=0.1 * i) for i in range(5)]
        cursor = ObservationCursor.from_list(obs)
        cursor.skip_while(lambda o: o.confidence < 0.3)
        assert cursor.position == 3

    def test_slice_no_cursor_advance(self):
        obs = [make_obs(i) for i in range(5)]
        cursor = ObservationCursor.from_list(obs)
        sliced = cursor.slice(1, 3)
        assert len(sliced) == 2
        assert cursor.position == 0
