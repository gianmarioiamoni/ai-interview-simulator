# tests/services/humanizer/follow_up/test_follow_up_output.py
#
# Covers: DTO validation, type constraints, confidence range, extra fields.

import pytest
from pydantic import ValidationError

from services.humanizer.follow_up.follow_up_output import FollowUpOutput


_VALID = {
    "follow_up_question": "How does Redis handle LRU eviction under memory pressure?",
    "reasoning": "The candidate mentioned LRU but did not address memory limits.",
    "topic_anchor": "LRU eviction",
    "confidence": 0.85,
}


class TestFollowUpOutput:

    def test_valid_dto_created(self) -> None:
        out = FollowUpOutput(**_VALID)
        assert out.follow_up_question == _VALID["follow_up_question"]
        assert out.confidence == 0.85

    def test_frozen(self) -> None:
        from pydantic import ValidationError as PydanticVE
        out = FollowUpOutput(**_VALID)
        with pytest.raises((TypeError, AttributeError, PydanticVE)):
            out.confidence = 0.5  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FollowUpOutput(**_VALID, extra_key="bad")  # type: ignore[call-arg]

    def test_missing_follow_up_question(self) -> None:
        data = {k: v for k, v in _VALID.items() if k != "follow_up_question"}
        with pytest.raises(ValidationError):
            FollowUpOutput(**data)

    def test_missing_reasoning(self) -> None:
        data = {k: v for k, v in _VALID.items() if k != "reasoning"}
        with pytest.raises(ValidationError):
            FollowUpOutput(**data)

    def test_missing_topic_anchor(self) -> None:
        data = {k: v for k, v in _VALID.items() if k != "topic_anchor"}
        with pytest.raises(ValidationError):
            FollowUpOutput(**data)

    def test_missing_confidence(self) -> None:
        data = {k: v for k, v in _VALID.items() if k != "confidence"}
        with pytest.raises(ValidationError):
            FollowUpOutput(**data)

    def test_confidence_below_zero_fails(self) -> None:
        with pytest.raises(ValidationError):
            FollowUpOutput(**{**_VALID, "confidence": -0.1})

    def test_confidence_above_one_fails(self) -> None:
        with pytest.raises(ValidationError):
            FollowUpOutput(**{**_VALID, "confidence": 1.01})

    def test_confidence_at_zero_valid(self) -> None:
        out = FollowUpOutput(**{**_VALID, "confidence": 0.0})
        assert out.confidence == 0.0

    def test_confidence_at_one_valid(self) -> None:
        out = FollowUpOutput(**{**_VALID, "confidence": 1.0})
        assert out.confidence == 1.0

    def test_question_without_question_mark_fails(self) -> None:
        with pytest.raises(ValidationError):
            FollowUpOutput(**{**_VALID, "follow_up_question": "No question mark here"})

    def test_empty_follow_up_question_fails(self) -> None:
        with pytest.raises(ValidationError):
            FollowUpOutput(**{**_VALID, "follow_up_question": ""})

    def test_empty_reasoning_fails(self) -> None:
        with pytest.raises(ValidationError):
            FollowUpOutput(**{**_VALID, "reasoning": ""})

    def test_empty_topic_anchor_fails(self) -> None:
        with pytest.raises(ValidationError):
            FollowUpOutput(**{**_VALID, "topic_anchor": ""})

    def test_wrong_type_confidence_string_fails(self) -> None:
        with pytest.raises(ValidationError):
            FollowUpOutput(**{**_VALID, "confidence": "high"})  # type: ignore[arg-type]
