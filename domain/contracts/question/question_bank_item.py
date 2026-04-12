from pydantic import BaseModel, Field

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_typeimport InterviewType
from domain.contracts.user.role import Role
from domain.contracts.user.seniority_level import SeniorityLevel


class QuestionBankItem(BaseModel):
    id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)

    interview_type: InterviewType
    role: Role
    area: InterviewArea

    level: SeniorityLevel
    difficulty: int = Field(..., ge=1, le=5)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
