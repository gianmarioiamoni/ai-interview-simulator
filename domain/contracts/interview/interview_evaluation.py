# domain/contracts/interview/interview_evaluation.py

from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from domain.contracts.shared.performance_dimension import PerformanceDimension
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.interview.hire_decision import HireDecision


class InterviewEvaluation(BaseModel):

    overall_score: float = Field(..., ge=0.0, le=100.0)
    raw_score: float | None = None
    adjusted_score: float | None = None
    
    executive_summary: str = Field(..., min_length=1)

    performance_dimensions: List[PerformanceDimension]

    # deterministic dimension scores
    dimension_scores: Dict[str, float]

    # signals extracted from execution results
    dimension_signals: Dict[str, float] = {}

    # FAANG-style ranking
    level: InterviewLevel

    # explicit hiring decision
    hire_decision: HireDecision
    decision_explanation: Dict[str, List[str]] 

    hiring_probability: float = Field(..., ge=0.0, le=100.0)
    percentile_rank: float = Field(..., ge=0.0, le=100.0)
    percentile_explanation: str

    gating_triggered: bool
    gating_reason: Optional[str] = None
    weighted_breakdown: Dict[str, float]

    per_question_assessment: List[QuestionEvaluation]
    improvement_suggestions: List[str]

    # Coaching sections (V1.0)
    went_well: List[str] = Field(default_factory=list)
    held_you_back: List[Dict] = Field(default_factory=list)
    knowledge_gaps: List[Dict] = Field(default_factory=list)
    next_strategy: List[Dict] = Field(default_factory=list)

    confidence: Confidence

    model_config = {"frozen": True}
