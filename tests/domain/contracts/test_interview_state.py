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
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Generic IT",
        language="en",
    )

    assert state.questions == []
    assert state.answers == []
    assert state.results_by_question == {}
    assert state.scoring_snapshot is None
    assert state.is_completed is False


def test_minimal_state_has_no_results() -> None:
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Generic IT",
        language="en",
    )

    assert state.get_result_for_question("any") is None
    assert state.current_question is None


def test_follow_up_count_limit_matches_constant() -> None:
    from app.settings.constants import MAX_FOLLOW_UPS_PER_INTERVIEW

    with pytest.raises(ValidationError):
        InterviewState(**_base_state(), follow_up_count=MAX_FOLLOW_UPS_PER_INTERVIEW + 1)


def test_create_initial_enable_humanizer_false() -> None:
    from domain.contracts.user.role import RoleType
    from domain.contracts.interview.interview_type import InterviewType

    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="Acme",
        language="en",
        questions=[],
        interview_id="test-1",
        enable_humanizer=False,
    )

    assert state.enable_humanizer is False


def test_create_initial_enable_humanizer_default_true() -> None:
    from domain.contracts.user.role import RoleType
    from domain.contracts.interview.interview_type import InterviewType

    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="Acme",
        language="en",
        questions=[],
        interview_id="test-2",
    )

    assert state.enable_humanizer is True
