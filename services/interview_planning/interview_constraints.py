# services/interview_planning/interview_constraints.py

from pydantic import BaseModel


class InterviewConstraints(BaseModel):

    required_areas: list[str]

    excluded_areas: list[str]

    max_questions_per_area: int

    minimum_average_difficulty: float

    minimum_total_questions: int

    model_config = {
        "frozen": True,
    }
