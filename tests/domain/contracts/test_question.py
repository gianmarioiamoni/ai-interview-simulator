# tests/domain/contracts/test_question.py

# difficulty 1-5 range

import pytest
from pydantic import ValidationError

from domain.contracts.question import Question, QuestionType
from domain.contracts.interview_area import InterviewArea


def test_question_valid_difficulty_range() -> None:
    question = Question(
        id="q1",
        area=InterviewArea.TECH_BACKGROUND,
        type=QuestionType.WRITTEN,
        prompt="Explain REST.",
        difficulty=3,
    )

    assert question.difficulty == 3


def test_question_invalid_difficulty_low() -> None:
    with pytest.raises(ValidationError):
        Question(
            id="q1",
            area=InterviewArea.TECH_BACKGROUND,
            type=QuestionType.WRITTEN,
            prompt="Explain REST.",
            difficulty=0,
        )


def test_question_invalid_difficulty_high() -> None:
    with pytest.raises(ValidationError):
        Question(
            id="q1",
            area=InterviewArea.TECH_BACKGROUND,
            type=QuestionType.WRITTEN,
            prompt="Explain REST.",
            difficulty=6,
        )
