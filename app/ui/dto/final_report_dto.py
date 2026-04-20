# app/ui/dto/final_report_dto.py

from typing import List, Dict, Optional
from pydantic import BaseModel

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO

from app.ui.mappers.hire_decision_mapper import HireDecisionMapper

from app.ui.dto.builders.question_mapper import QuestionMapper
from app.ui.dto.builders.dimension_mapper import DimensionMapper
from app.ui.dto.builders.token_calculator import TokenCalculator

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview_state import InterviewState
from domain.contracts.user.role import RoleType


class FinalReportDTO(BaseModel):

    overall_score: float
    hiring_probability: float
    hire_decision: str
    decision_explanation: Dict[str, List[str]]

    percentile_rank: float
    percentile_explanation: str

    executive_summary: str

    gating_triggered: bool
    gating_reason: Optional[str]

    weighted_breakdown: Dict

    dimension_scores: List[DimensionScoreDTO]
    question_assessments: List[QuestionAssessmentDTO]

    improvement_suggestions: List[str]

    total_tokens_used: int

    confidence: Confidence

    role: RoleType

    @classmethod
    def from_components(cls, state: InterviewState, final_evaluation):

        question_mapper = QuestionMapper()
        dimension_mapper = DimensionMapper()
        token_calculator = TokenCalculator()

        question_assessments = question_mapper.map(state)
        dimension_scores = dimension_mapper.map(final_evaluation)
        tokens = token_calculator.calculate(state)

        role = state.role.type

        hire_decision = (HireDecisionMapper.to_label(final_evaluation.hire_decision))

        return cls(
            overall_score=final_evaluation.overall_score,
            hiring_probability=final_evaluation.hiring_probability,
            hire_decision=hire_decision,
            decision_explanation=final_evaluation.decision_explanation,
            percentile_rank=final_evaluation.percentile_rank,
            percentile_explanation=final_evaluation.percentile_explanation,
            executive_summary=final_evaluation.executive_summary,
            gating_triggered=final_evaluation.gating_triggered,
            gating_reason=final_evaluation.gating_reason,
            weighted_breakdown=final_evaluation.weighted_breakdown,
            dimension_scores=dimension_scores,
            question_assessments=question_assessments,
            improvement_suggestions=final_evaluation.improvement_suggestions,
            total_tokens_used=tokens,
            confidence=final_evaluation.confidence,
            role=role,
        )
