from typing import List

from domain.contracts.interview_state import InterviewState
from domain.contracts.answer import Answer
from domain.contracts.role import Role, RoleType
from domain.contracts.interview_type import InterviewType

from tests.factories.question_factory import build_question


def build_interview_state(
    *,
    questions=None,
    answers=None,
    current_question_index: int = 0,
) -> InterviewState:

    if questions is None:
        questions = [build_question()]

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
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company="TestCorp",
        interview_type=InterviewType.TECHNICAL,
        language="en",
        questions=questions,
        answers=answers,
        current_question_index=current_question_index,
    )
