# tests/domain/contracts/replay/test_replay_question_record.py
# EPIC-03 Phase 2c — ReplayQuestionRecord contract tests.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.contracts.replay.replay_question_record import ReplayQuestionRecord


def _make(**overrides) -> ReplayQuestionRecord:
    defaults = dict(
        question_id="q-001",
        question_index=0,
        question_type="technical",
        area_label="Algorithms",
        question_prompt="Describe merge sort.",
        candidate_answer="It divides the array recursively.",
        score=75.0,
        max_score=100.0,
        feedback="Good explanation.",
        strengths=("Clear structure",),
        weaknesses=("Missing complexity analysis",),
        attempts=1,
    )
    defaults.update(overrides)
    return ReplayQuestionRecord(**defaults)


class TestReplayQuestionRecordConstruction:

    def test_minimal_construction(self):
        rec = _make()
        assert rec.question_id == "q-001"
        assert rec.question_index == 0
        assert rec.score == 75.0
        assert rec.max_score == 100.0
        assert rec.attempts == 1
        assert rec.follow_up_question is None
        assert rec.execution_status is None
        assert rec.passed_tests is None
        assert rec.total_tests is None
        assert rec.ai_hint_explanation is None
        assert rec.ai_hint_suggestion is None

    def test_empty_candidate_answer_accepted(self):
        rec = _make(candidate_answer="")
        assert rec.candidate_answer == ""

    def test_strengths_weaknesses_default_empty_tuple(self):
        rec = _make(strengths=(), weaknesses=())
        assert rec.strengths == ()
        assert rec.weaknesses == ()

    def test_coding_question_fields(self):
        rec = _make(
            execution_status="passed",
            passed_tests=5,
            total_tests=5,
        )
        assert rec.is_coding_question is True
        assert rec.passed_tests == 5
        assert rec.total_tests == 5

    def test_follow_up_question_present(self):
        rec = _make(follow_up_question="What is the time complexity?")
        assert rec.follow_up_question == "What is the time complexity?"

    def test_hint_fields(self):
        rec = _make(ai_hint_explanation="Consider divide-and-conquer.", ai_hint_suggestion="Try recursion.")
        assert rec.has_hint is True
        assert rec.ai_hint_suggestion == "Try recursion."


class TestReplayQuestionRecordImmutability:

    def test_frozen_raises_on_mutation(self):
        rec = _make()
        with pytest.raises((ValidationError, TypeError)):
            rec.score = 50.0

    def test_frozen_raises_on_question_id_mutation(self):
        rec = _make()
        with pytest.raises((ValidationError, TypeError)):
            rec.question_id = "changed"


class TestReplayQuestionRecordExtraForbid:

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            _make(unknown_extra="bad")  # type: ignore[call-arg]


class TestReplayQuestionRecordProperties:

    def test_score_ratio(self):
        rec = _make(score=75.0, max_score=100.0)
        assert rec.score_ratio == pytest.approx(0.75)

    def test_score_ratio_full(self):
        rec = _make(score=100.0, max_score=100.0)
        assert rec.score_ratio == pytest.approx(1.0)

    def test_is_coding_question_false(self):
        rec = _make()
        assert rec.is_coding_question is False

    def test_is_coding_question_true(self):
        rec = _make(execution_status="passed", passed_tests=3, total_tests=3)
        assert rec.is_coding_question is True

    def test_has_hint_false(self):
        rec = _make()
        assert rec.has_hint is False

    def test_has_hint_true(self):
        rec = _make(ai_hint_explanation="hint text")
        assert rec.has_hint is True


class TestReplayQuestionRecordValidatorVRQR01:
    """V-RQR-01: max_score must be > 0.0."""

    def test_max_score_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make(max_score=0.0)

    def test_max_score_negative_rejected(self):
        with pytest.raises(ValidationError):
            _make(max_score=-1.0)


class TestReplayQuestionRecordValidatorVRQR02:
    """V-RQR-02: score must not exceed max_score."""

    def test_score_equal_to_max_score_accepted(self):
        rec = _make(score=100.0, max_score=100.0)
        assert rec.score == rec.max_score

    def test_score_exceeds_max_score_rejected(self):
        with pytest.raises(ValidationError, match="V-RQR-02"):
            _make(score=80.0, max_score=50.0)


class TestReplayQuestionRecordValidatorVRQR04:
    """V-RQR-04: coding fields are co-present or all None."""

    def test_all_coding_fields_present_accepted(self):
        rec = _make(execution_status="passed", passed_tests=5, total_tests=5)
        assert rec.is_coding_question is True

    def test_all_coding_fields_none_accepted(self):
        rec = _make(execution_status=None, passed_tests=None, total_tests=None)
        assert rec.is_coding_question is False

    def test_partial_coding_fields_execution_only_rejected(self):
        with pytest.raises(ValidationError, match="V-RQR-04"):
            _make(execution_status="passed", passed_tests=None, total_tests=None)

    def test_partial_coding_fields_tests_only_rejected(self):
        with pytest.raises(ValidationError, match="V-RQR-04"):
            _make(execution_status=None, passed_tests=5, total_tests=10)

    def test_partial_coding_fields_passed_only_rejected(self):
        with pytest.raises(ValidationError, match="V-RQR-04"):
            _make(execution_status=None, passed_tests=5, total_tests=None)


class TestReplayQuestionRecordFieldConstraints:

    def test_question_id_empty_rejected(self):
        with pytest.raises(ValidationError):
            _make(question_id="")

    def test_question_index_negative_rejected(self):
        with pytest.raises(ValidationError):
            _make(question_index=-1)

    def test_attempts_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make(attempts=0)

    def test_attempts_negative_rejected(self):
        with pytest.raises(ValidationError):
            _make(attempts=-1)

    def test_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make(score=-1.0)

    def test_score_above_100_rejected(self):
        with pytest.raises(ValidationError):
            _make(score=100.1)
