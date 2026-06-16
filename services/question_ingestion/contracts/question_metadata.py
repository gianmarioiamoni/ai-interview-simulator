# services/question_ingestion/contracts/question_metadata.py

from pydantic import BaseModel

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel


class QuestionMetadata(BaseModel):

    role: RoleType | None = None

    area: InterviewArea | None = None

    level: SeniorityLevel | None = None

    difficulty: int | None = None

    domains: list[str] = []

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
