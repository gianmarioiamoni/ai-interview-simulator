# tests/domain/contracts/session_history/test_question_result_record.py

import pytest
from pydantic import ValidationError

from domain.contracts.session_history.question_result_record import QuestionResultRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _written(**overrides) -> dict:
    base = {
        "question_id": "q-001",
        "question_index": 0,
        "question_type": "written",
        "area_label": "System Design",
        "question_prompt": "Describe a scalable notification system.",
        "score": 78.0,
        "max_score": 100.0,
        "feedback": "Good high-level design but missed sharding concerns.",
        "strengths": ("Clear structure.", "Considered failure modes."),
        "weaknesses": ("Missed sharding.", "No mention of backpressure."),
        "attempts": 1,
    }
    base.update(overrides)
    return base


def _coding(**overrides) -> dict:
    base = _written(
        question_type="coding",
        area_label="Algorithms",
        question_prompt="Implement a binary search.",
        passed_tests=8,
        total_tests=10,
        execution_status="partial",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------


class TestQuestionResultRecordConstruction:
    def test_valid_written_question(self):
        r = QuestionResultRecord(**_written())
        assert r.question_id == "q-001"
        assert r.question_index == 0
        assert r.score == 78.0
        assert r.max_score == 100.0
        assert r.attempts == 1
        assert r.schema_version == "1.0"

    def test_valid_coding_question_with_tests(self):
        r = QuestionResultRecord(**_coding())
        assert r.passed_tests == 8
        assert r.total_tests == 10
        assert r.execution_status == "partial"

    def test_full_test_pass(self):
        r = QuestionResultRecord(**_coding(passed_tests=10, total_tests=10))
        assert r.passed_tests == r.total_tests

    def test_zero_passed_tests_valid(self):
        r = QuestionResultRecord(**_coding(passed_tests=0, total_tests=5))
        assert r.passed_tests == 0

    def test_no_coding_fields_for_written(self):
        r = QuestionResultRecord(**_written())
        assert r.passed_tests is None
        assert r.total_tests is None
        assert r.execution_status is None

    def test_follow_up_question_optional(self):
        r = QuestionResultRecord(**_written(follow_up_question="How would you handle failures?"))
        assert r.follow_up_question == "How would you handle failures?"

    def test_follow_up_question_defaults_to_none(self):
        r = QuestionResultRecord(**_written())
        assert r.follow_up_question is None

    def test_strengths_and_weaknesses_empty_tuples(self):
        r = QuestionResultRecord(**_written(strengths=(), weaknesses=()))
        assert r.strengths == ()
        assert r.weaknesses == ()

    def test_ai_hint_both_set(self):
        r = QuestionResultRecord(**_written(
            ai_hint_explanation="Consider time complexity.",
            ai_hint_suggestion="Use a hash map for O(1) lookups.",
        ))
        assert r.ai_hint_explanation == "Consider time complexity."
        assert r.ai_hint_suggestion == "Use a hash map for O(1) lookups."

    def test_ai_hint_both_none(self):
        r = QuestionResultRecord(**_written())
        assert r.ai_hint_explanation is None
        assert r.ai_hint_suggestion is None

    def test_ai_hint_explanation_only_valid(self):
        r = QuestionResultRecord(**_written(
            ai_hint_explanation="Think about edge cases.",
            ai_hint_suggestion=None,
        ))
        assert r.ai_hint_explanation == "Think about edge cases."
        assert r.ai_hint_suggestion is None

    def test_multiple_attempts(self):
        r = QuestionResultRecord(**_written(attempts=3))
        assert r.attempts == 3

    def test_schema_version_default(self):
        r = QuestionResultRecord(**_written())
        assert r.schema_version == "1.0"

    def test_custom_schema_version(self):
        r = QuestionResultRecord(**_written(schema_version="2.0"))
        assert r.schema_version == "2.0"

    def test_question_prompt_stored_in_full(self):
        long_prompt = "A" * 500
        r = QuestionResultRecord(**_written(question_prompt=long_prompt))
        assert r.question_prompt == long_prompt

    def test_boundary_score_zero(self):
        r = QuestionResultRecord(**_written(score=0.0))
        assert r.score == 0.0

    def test_boundary_score_hundred(self):
        r = QuestionResultRecord(**_written(score=100.0))
        assert r.score == 100.0

    def test_boundary_attempts_one(self):
        r = QuestionResultRecord(**_written(attempts=1))
        assert r.attempts == 1

    def test_question_index_zero_valid(self):
        r = QuestionResultRecord(**_written(question_index=0))
        assert r.question_index == 0


# ---------------------------------------------------------------------------
# Field validation
# ---------------------------------------------------------------------------


class TestQuestionResultRecordFieldValidation:
    def test_empty_question_id_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(question_id=""))

    def test_negative_question_index_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(question_index=-1))

    def test_empty_question_type_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(question_type=""))

    def test_empty_area_label_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(area_label=""))

    def test_empty_question_prompt_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(question_prompt=""))

    def test_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(score=-0.1))

    def test_score_above_hundred_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(score=100.1))

    def test_max_score_zero_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(max_score=0.0))

    def test_empty_feedback_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(feedback=""))

    def test_attempts_zero_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(attempts=0))

    def test_negative_passed_tests_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_coding(passed_tests=-1))

    def test_total_tests_zero_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_coding(total_tests=0))

    def test_empty_schema_version_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(schema_version=""))

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            QuestionResultRecord(**_written(unknown_field="value"))


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------


class TestQuestionResultRecordInvariants:
    def test_v_qrr_01_passed_without_total_rejected(self):
        with pytest.raises(ValidationError, match="V-QRR-01"):
            QuestionResultRecord(**_written(passed_tests=5, total_tests=None))

    def test_v_qrr_01_total_without_passed_rejected(self):
        with pytest.raises(ValidationError, match="V-QRR-01"):
            QuestionResultRecord(**_written(passed_tests=None, total_tests=10))

    def test_v_qrr_02_passed_exceeds_total_rejected(self):
        with pytest.raises(ValidationError, match="V-QRR-02"):
            QuestionResultRecord(**_coding(passed_tests=11, total_tests=10))

    def test_v_qrr_02_passed_equals_total_accepted(self):
        r = QuestionResultRecord(**_coding(passed_tests=10, total_tests=10))
        assert r.passed_tests == r.total_tests

    def test_v_qrr_03_suggestion_without_explanation_rejected(self):
        with pytest.raises(ValidationError, match="V-QRR-03"):
            QuestionResultRecord(**_written(
                ai_hint_explanation=None,
                ai_hint_suggestion="Use a hash map.",
            ))

    def test_v_qrr_03_explanation_without_suggestion_accepted(self):
        r = QuestionResultRecord(**_written(
            ai_hint_explanation="Think about this.",
            ai_hint_suggestion=None,
        ))
        assert r.ai_hint_explanation == "Think about this."
        assert r.ai_hint_suggestion is None


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestQuestionResultRecordImmutability:
    def test_score_assignment_raises(self):
        r = QuestionResultRecord(**_written())
        with pytest.raises((TypeError, ValidationError)):
            r.score = 50.0  # type: ignore[misc]

    def test_question_id_assignment_raises(self):
        r = QuestionResultRecord(**_written())
        with pytest.raises((TypeError, ValidationError)):
            r.question_id = "q-999"  # type: ignore[misc]

    def test_passed_tests_assignment_raises(self):
        r = QuestionResultRecord(**_coding())
        with pytest.raises((TypeError, ValidationError)):
            r.passed_tests = 0  # type: ignore[misc]

    def test_strengths_assignment_raises(self):
        r = QuestionResultRecord(**_written())
        with pytest.raises((TypeError, ValidationError)):
            r.strengths = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


class TestQuestionResultRecordSerialization:
    def test_round_trip_written(self):
        r = QuestionResultRecord(**_written())
        restored = QuestionResultRecord.model_validate(r.model_dump())
        assert restored == r

    def test_round_trip_coding(self):
        r = QuestionResultRecord(**_coding())
        restored = QuestionResultRecord.model_validate(r.model_dump())
        assert restored == r

    def test_round_trip_with_hints(self):
        r = QuestionResultRecord(**_written(
            ai_hint_explanation="Edge cases matter.",
            ai_hint_suggestion="Check for null inputs.",
        ))
        restored = QuestionResultRecord.model_validate(r.model_dump())
        assert restored == r

    def test_none_fields_serialized_as_none(self):
        r = QuestionResultRecord(**_written())
        data = r.model_dump()
        assert data["passed_tests"] is None
        assert data["total_tests"] is None
        assert data["ai_hint_explanation"] is None

    def test_full_prompt_preserved_in_serialization(self):
        long_prompt = "B" * 300
        r = QuestionResultRecord(**_written(question_prompt=long_prompt))
        data = r.model_dump()
        assert data["question_prompt"] == long_prompt


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------


class TestQuestionResultRecordEquality:
    def test_equal_written_instances(self):
        a = QuestionResultRecord(**_written())
        b = QuestionResultRecord(**_written())
        assert a == b

    def test_different_score_not_equal(self):
        a = QuestionResultRecord(**_written(score=70.0))
        b = QuestionResultRecord(**_written(score=80.0))
        assert a != b

    def test_different_question_id_not_equal(self):
        a = QuestionResultRecord(**_written(question_id="q-001"))
        b = QuestionResultRecord(**_written(question_id="q-002"))
        assert a != b

    def test_written_vs_coding_not_equal(self):
        a = QuestionResultRecord(**_written())
        b = QuestionResultRecord(**_coding())
        assert a != b
