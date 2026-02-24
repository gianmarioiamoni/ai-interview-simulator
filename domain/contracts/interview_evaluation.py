# Interview-level evaluation contract
#
# Represents the final structured evaluation of the whole interview.
# Produced at termination phase.
#
# Responsibility: immutable global evaluation snapshot.

from pydantic import BaseModel, Field
from typing import List
from domain.contracts.question_evaluation import QuestionEvaluation


class PerformanceDimension(BaseModel):
    name: str = Field(..., min_length=1)
    score: float = Field(..., ge=1.0, le=10.0)
    justification: str = Field(..., min_length=1)


class InterviewEvaluation(BaseModel):
    overall_score: float = Field(..., ge=1.0, le=10.0)

    performance_dimensions: List[PerformanceDimension]

    hiring_probability: float = Field(..., ge=0.0, le=100.0)

    per_question_assessment: List[QuestionEvaluation]

    improvement_suggestions: List[str]

    confidence: float = Field(..., ge=0.0, le=1.0)

    model_config = {"frozen": True}
