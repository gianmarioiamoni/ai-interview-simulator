# tests/domain/contracts/test_question.py

# difficulty is a closed enum (easy / medium / hard)

import pytest
from pydantic import ValidationError

from domain.contracts.question.question import (
    Question,
    QuestionDifficulty,
    QuestionType,
)
from domain.contracts.interview.interview_area import InterviewArea


def _question_kwargs() -> dict:
    return {
        "id": "q1",
        "area": InterviewArea.TECH_BACKGROUND,
        "type": QuestionType.WRITTEN,
        "prompt": "Explain REST.",
    }


def test_question_valid_difficulty_enum() -> None:
    question = Question(**_question_kwargs(), difficulty=QuestionDifficulty.HARD)

    assert question.difficulty == QuestionDifficulty.HARD


def test_question_difficulty_defaults_to_medium() -> None:
    question = Question(**_question_kwargs())

    assert question.difficulty == QuestionDifficulty.MEDIUM


def test_question_invalid_difficulty_numeric() -> None:
    with pytest.raises(ValidationError):
        Question(**_question_kwargs(), difficulty=3)


def test_question_invalid_difficulty_unknown_value() -> None:
    with pytest.raises(ValidationError):
        Question(**_question_kwargs(), difficulty="extreme")
