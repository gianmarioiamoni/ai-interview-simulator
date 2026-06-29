# app/ui/dto/final_report_dto.py

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO

from app.ui.mappers.hire_decision_mapper import HireDecisionMapper
from app.ui.dto.builders.dimension_score_mapper import DimensionScoreMapper
from app.ui.dto.builders.question_mapper import QuestionMapper
from app.ui.dto.builders.token_calculator import TokenCalculator

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview_state import InterviewState
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.interview_context_profile import InterviewContextProfile


class FinalReportDTO(BaseModel):

    overall_score: float
    raw_score: float
    adjusted_score: float
    hiring_probability: float
    hire_decision: str
    decision_explanation: Dict[str, List[str]]
    dimension_signals: Dict[str, float]

    percentile_rank: float
    percentile_explanation: str

    executive_summary: str

    gating_triggered: bool
    gating_reason: Optional[str]

    weighted_breakdown: Dict[str, float]

    dimension_scores: List[DimensionScoreDTO]
    question_assessments: List[QuestionAssessmentDTO]

    improvement_suggestions: List[str]

    # Coaching sections (V1.0)
    went_well: List[str] = Field(default_factory=list)
    held_you_back: List[Dict] = Field(default_factory=list)
    knowledge_gaps: List[Dict] = Field(default_factory=list)
    next_strategy: List[Dict] = Field(default_factory=list)

    total_tokens_used: int

    confidence: Confidence

    role: RoleType

    seniority_level: str

    context_profile: InterviewContextProfile

    @classmethod
    def from_components(cls, state: InterviewState, final_evaluation):

        question_mapper = QuestionMapper()
        dimension_mapper = DimensionScoreMapper()
        token_calculator = TokenCalculator()

        question_assessments = question_mapper.map(state)
        dimension_scores = dimension_mapper.map(
            final_evaluation.dimension_scores,
            final_evaluation.weighted_breakdown,
            getattr(final_evaluation, "performance_dimensions", None),
        )
        tokens = token_calculator.calculate(state)

        role = state.role.type

        hire_decision = (HireDecisionMapper.to_label(final_evaluation.hire_decision))

        seniority_level = state.seniority_level
        context_profile = state.context_profile

        return cls(
            overall_score=final_evaluation.overall_score,
            raw_score=final_evaluation.raw_score,
            adjusted_score=final_evaluation.adjusted_score,
            hiring_probability=final_evaluation.hiring_probability,
            hire_decision=hire_decision,
            decision_explanation=final_evaluation.decision_explanation,
            dimension_signals=final_evaluation.dimension_signals,
            percentile_rank=final_evaluation.percentile_rank,
            percentile_explanation=final_evaluation.percentile_explanation,
            executive_summary=final_evaluation.executive_summary,
            gating_triggered=final_evaluation.gating_triggered,
            gating_reason=final_evaluation.gating_reason,
            weighted_breakdown=final_evaluation.weighted_breakdown,
            dimension_scores=dimension_scores,
            question_assessments=question_assessments,
            improvement_suggestions=final_evaluation.improvement_suggestions,
            went_well=getattr(final_evaluation, "went_well", []) or [],
            held_you_back=getattr(final_evaluation, "held_you_back", []) or [],
            knowledge_gaps=getattr(final_evaluation, "knowledge_gaps", []) or [],
            next_strategy=getattr(final_evaluation, "next_strategy", []) or [],
            total_tokens_used=tokens,
            confidence=final_evaluation.confidence,
            role=role,
            seniority_level=seniority_level,
            context_profile=context_profile,
        )
