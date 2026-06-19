# tests/domain/contracts/test_last_question_context.py

from domain.contracts.interview_state.last_question_context import LastQuestionContext
from domain.contracts.question.question import QuestionType


def test_last_question_context_minimal() -> None:
    ctx = LastQuestionContext(
        question_id="q1",
        question_prompt="Explain SOLID.",
        question_type=QuestionType.WRITTEN,
    )
    assert ctx.question_id == "q1"
    assert ctx.question_area is None
    assert ctx.answer_content is None
    assert ctx.quality_rank is None


def test_last_question_context_full() -> None:
    ctx = LastQuestionContext(
        question_id="q2",
        question_prompt="Design a URL shortener.",
        question_type=QuestionType.WRITTEN,
        question_area="system_design",
        answer_content="I would use a hash function...",
        quality_rank=4,
    )
    assert ctx.quality_rank == 4
    assert ctx.question_area == "system_design"
    assert ctx.answer_content == "I would use a hash function..."


def test_last_question_context_is_frozen() -> None:
    from pydantic import ValidationError
    import pytest

    ctx = LastQuestionContext(
        question_id="q1",
        question_prompt="Explain REST.",
        question_type=QuestionType.WRITTEN,
    )
    with pytest.raises((ValidationError, TypeError)):
        ctx.quality_rank = 3  # type: ignore[misc]
