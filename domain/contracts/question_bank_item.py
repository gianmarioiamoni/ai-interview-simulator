from pydantic import BaseModel, Field
from enum import Enum

from domain.contracts.interview_area import InterviewArea, InterviewType
from domain.contracts.role import Role


class SeniorityLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


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
