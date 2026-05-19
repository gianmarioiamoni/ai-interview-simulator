# services/interview_selection/adaptive_interview_result.py

from pydantic import BaseModel

from services.interview_selection.assembled_question import (
    AssembledQuestion,
)


class AdaptiveInterviewResult(BaseModel):

    questions: list[AssembledQuestion]

    coverage_score: float

    average_difficulty: float

    progression_score: float

    model_config = {
        "frozen": True,
    }
