import pytest
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_state import InterviewState
from domain.contracts.role import Role
from domain.contracts.role import RoleType


def test_default_progress_is_setup() -> None:
    state = InterviewState(
        interview_id="int-1",
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="Generic IT",
    )

    assert state.progress == InterviewProgress.SETUP


def test_progress_invalid_value_fails() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        InterviewState(
            interview_id="int-1",
            role=Role(type=RoleType.BACKEND_ENGINEER),
            company="Generic IT",
            progress="random",
        )


def test_in_progress_without_questions_fails() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Cannot be in progress without questions"):
        InterviewState(
            interview_id="int-1",
            role=Role(type=RoleType.BACKEND_ENGINEER),
            company="Generic IT",
            progress=InterviewProgress.IN_PROGRESS,
        )


def test_completed_without_evaluations_fails() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Cannot complete interview without evaluations"):
        InterviewState(
            interview_id="int-1",
            role=Role(type=RoleType.BACKEND_ENGINEER),
            company="Generic IT",
            progress=InterviewProgress.COMPLETED,
        )
