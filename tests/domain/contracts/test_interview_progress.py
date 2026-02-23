import pytest
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_state import InterviewState


def test_default_progress_is_setup() -> None:
    state = InterviewState(
        interview_id="int-1",
        role="backend",
        company="Generic IT",
    )

    assert state.progress == InterviewProgress.SETUP


def test_progress_enum_accepts_valid_value() -> None:
    from domain.contracts.question import Question, QuestionType
    
    state = InterviewState(
        interview_id="int-1",
        role="backend",
        company="Generic IT",
        progress=InterviewProgress.IN_PROGRESS,
        questions=[
            Question(
                id="q1",
                area="backend",
                type=QuestionType.WRITTEN,
                prompt="Sample question",
                difficulty=3,
            )
        ],
    )

    assert state.progress == InterviewProgress.IN_PROGRESS


def test_progress_invalid_value_fails() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        InterviewState(
            interview_id="int-1",
            role="backend",
            company="Generic IT",
            progress="random",
        )


def test_in_progress_without_questions_fails() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Cannot be in progress without questions"):
        InterviewState(
            interview_id="int-1",
            role="backend",
            company="Generic IT",
            progress=InterviewProgress.IN_PROGRESS,
        )


def test_completed_without_evaluations_fails() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Cannot complete interview without evaluations"):
        InterviewState(
            interview_id="int-1",
            role="backend",
            company="Generic IT",
            progress=InterviewProgress.COMPLETED,
        )
