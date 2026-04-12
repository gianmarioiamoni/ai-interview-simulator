# domain/contracts/interview_state/factory.py

from typing import Self

from domain.contracts.role import Role
from domain.contracts.interview_type import InterviewType
from domain.contracts.question.question import Question
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.role import RoleType


class InterviewStateFactoryMixin:

    @classmethod
    def create_initial(
        cls,
        role_type: RoleType,
        interview_type: InterviewType,
        company: str,
        language: str,
        questions: list[Question],
        interview_id: str,
    ) -> Self:

        return cls(
            interview_id=interview_id,
            role=Role(type=role_type),
            interview_type=interview_type,
            company=company.strip(),
            language=language,
            questions=questions,
            progress=InterviewProgress.SETUP,
        )
