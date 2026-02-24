# tests/domain/contracts/test_evaluation.py

# score 0-100 range

import pytest
from pydantic import ValidationError

from domain.contracts.question_evaluation import QuestionEvaluation


def test_evaluation_score_valid() -> None:
    result = QuestionEvaluation(
        question_id="q1",
        score=85.0,
        max_score=100.0,
        feedback="Good",
        strengths=["Clear explanation"],
        weaknesses=["Missing edge cases"],
        passed=True,
    )

    assert result.score == 85.0


def test_evaluation_score_above_100_invalid() -> None:
    with pytest.raises(ValidationError):
        QuestionEvaluation(
            question_id="q1",
            score=120.0,
            max_score=100.0,
            feedback="Invalid",
            strengths=[],
            weaknesses=[],
            passed=False,
        )
