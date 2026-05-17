# services/question_ingestion/contracts/normalized_question_record.py

from pydantic import BaseModel

from domain.contracts.user.role import RoleType
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.seniority_level import SeniorityLevel


class NormalizedQuestionRecord(BaseModel):

    text: str

    role_hint: RoleType | None = None
    area_hint: InterviewArea | None = None
    level_hint: SeniorityLevel | None = None

    difficulty_hint: int | None = None

    source: str

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
