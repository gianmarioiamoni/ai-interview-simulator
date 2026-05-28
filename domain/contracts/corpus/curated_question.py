# domain/contracts/corpus/curated_question.py

from pydantic import BaseModel

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel


class CuratedQuestion(BaseModel):

    id: str

    question: str

    role: RoleType

    seniority: SeniorityLevel

    area: InterviewArea

    domains: list[str]

    difficulty: int

    source: str

    quality_score: float

    tags: list[str]

    expected_topics: list[str]

    follow_up_hints: list[str] = []

    
    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
