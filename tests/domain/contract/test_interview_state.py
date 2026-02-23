# tests/domain/contracts/test_interview_state.py

# follow-up count 0-2 range and minimal instantiation (without questions, answers, evaluations)

import pytest
from pydantic import ValidationError

from domain.contracts.interview_state import InterviewState


def _base_state() -> dict:
    return {
        "interview_id": "int-1",
        "role": "backend engineer",
        "company": "Generic IT",
        "language": "en",
    }


def test_follow_up_count_valid() -> None:
    state = InterviewState(**_base_state(), follow_up_count=2)
    assert state.follow_up_count == 2


def test_follow_up_count_invalid() -> None:
    with pytest.raises(ValidationError):
        InterviewState(**_base_state(), follow_up_count=3)


def test_interview_state_minimal_instantiation() -> None:
    state = InterviewState(
        interview_id="int-1",
        role="backend engineer",
        company="Generic IT",
        language="en",
    )

    assert state.questions == []
    assert state.answers == []
    assert state.evaluations == []
    assert state.total_score == 0.0
    assert state.completed is False
