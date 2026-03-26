from typing import List
from unittest.mock import Mock

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import Question
from domain.contracts.answer import Answer
from domain.contracts.role import Role, RoleType
from domain.contracts.interview_type import InterviewType


def build_interview_state(
    *,
    questions: List[Question] | None = None,
    answers: List[Answer] | None = None,
    current_question_index: int = 0,
) -> InterviewState:
    """
    Factory realistica per InterviewState.

    # Garantisce:
    # - stato valido Pydantic
    # - compatibile con computed properties
    """

    if questions is None:
        questions = [Mock(id="q1", type="coding")]

    if answers is None:
        answers = [
            Answer(
                question_id=questions[0].id,
                content="print('hello')",
                attempt=1,
            )
        ]

    return InterviewState(
        interview_id="test-id",
        role=Role(type=RoleType.SOFTWARE_ENGINEER),
        company="TestCorp",
        interview_type=InterviewType.TECHNICAL,
        language="en",
        questions=questions,
        answers=answers,
        current_question_index=current_question_index,
    )
