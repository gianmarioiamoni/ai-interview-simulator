# services/interview_policy/interview_policy.py

from pydantic import BaseModel


class InterviewPolicy(BaseModel):

    target_average_difficulty: float

    preferred_areas: list[str]

    max_questions_per_area: int

    prioritize_architecture: bool

    prioritize_scalability: bool

    prioritize_production_experience: bool

    model_config = {
        "frozen": True,
    }
