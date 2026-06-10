# tests/domain/contracts/test_interview_state.py

# follow-up count 0-2 range and minimal instantiation (without questions, answers, evaluations)


import pytest
from pydantic import ValidationError, BaseModel
from typing import List, Optional

from domain.contracts.interview_state import InterviewState
from domain.contracts.user.role import Role, RoleType


def _base_state() -> dict:
    return {
        "interview_id": "int-1",
        "role": Role(type=RoleType.BACKEND_ENGINEER),
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
    from domain.contracts.interview.interview_progress import InterviewProgress
    
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Generic IT",
        language="en",
    )

    assert state.questions == []
    assert state.answers == []
    assert state.results_by_question == {}
    assert state.interview_evaluation is None
    assert state.progress == InterviewProgress.SETUP


def test_minimal_state_has_no_results() -> None:
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Generic IT",
        language="en",
    )

    assert state.get_result_for_question("any") is None
    assert state.current_question is None
