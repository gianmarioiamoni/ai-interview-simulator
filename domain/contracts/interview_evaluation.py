# domain/contracts/interview_evaluation.py

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from domain.contracts.performance_dimension import PerformanceDimension
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.confidence import Confidence


class InterviewEvaluation(BaseModel):

    overall_score: float = Field(..., ge=0.0, le=100.0)
    executive_summary: str = Field(..., min_length=1)

    performance_dimensions: List[PerformanceDimension]

    hiring_probability: float = Field(..., ge=0.0, le=100.0)
    percentile_rank: float = Field(..., ge=0.0, le=100.0)
    percentile_explanation: str

    gating_triggered: bool
    gating_reason: Optional[str] = None
    weighted_breakdown: Dict[str, float]

    per_question_assessment: List[QuestionEvaluation]
    improvement_suggestions: List[str]

    confidence: Confidence

    model_config = {"frozen": True}
