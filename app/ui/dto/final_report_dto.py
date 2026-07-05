# app/ui/dto/final_report_dto.py
# EPIC-V13-05 Phase 9 — FinalReportDTO sourced exclusively from Report v2.0.
# from_components deleted (R-05). from_report is the sole factory.

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO

from app.ui.mappers.hire_decision_mapper import HireDecisionMapper
from app.ui.dto.builders.dimension_score_mapper import DimensionScoreMapper
from app.ui.dto.builders.question_assessment_mapper import QuestionAssessmentMapper

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.report.report import Report
from domain.contracts.user.role import RoleType
from domain.contracts.interview.interview_context_profile import InterviewContextProfile


def _safe_role_type(role_str: str) -> RoleType:
    try:
        return RoleType(role_str)
    except ValueError:
        return RoleType.OTHER


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
    def from_report(cls, report: Report) -> "FinalReportDTO":
        """Build FinalReportDTO exclusively from Report v2.0 (ADR-033, R-05, EPIC-V13-05 Phase 9).

        No InterviewState reads. No SessionHistory reads.
        """
        scoring = report.scoring
        narrative = report.scoring_narrative

        dimension_scores = DimensionScoreMapper().map(scoring.scoring_dimensions)

        question_assessments = [
            QuestionAssessmentMapper.to_dto(r) for r in report.question_assessments
        ]

        total_tokens = (
            report.generation_metadata.total_tokens_used
            if report.generation_metadata is not None
            else 0
        )

        return cls(
            overall_score=scoring.overall_score,
            raw_score=scoring.raw_score or 0.0,
            adjusted_score=scoring.adjusted_score or scoring.overall_score,
            hiring_probability=scoring.hiring_probability,
            hire_decision=HireDecisionMapper.to_label(scoring.hire_decision),
            decision_explanation=scoring.decision_explanation,
            dimension_signals=scoring.dimension_signals,
            percentile_rank=scoring.percentile_rank,
            percentile_explanation=scoring.percentile_explanation,
            executive_summary=narrative.executive_summary,
            gating_triggered=scoring.gating_triggered,
            gating_reason=scoring.gating_reason,
            weighted_breakdown=scoring.weighted_breakdown,
            dimension_scores=dimension_scores,
            question_assessments=question_assessments,
            improvement_suggestions=list(narrative.improvement_suggestions),
            went_well=list(narrative.went_well),
            held_you_back=[item.to_dict() for item in narrative.held_you_back],
            knowledge_gaps=[item.to_dict() for item in narrative.knowledge_gaps],
            next_strategy=[item.to_dict() for item in narrative.next_strategy],
            total_tokens_used=total_tokens,
            confidence=scoring.confidence,
            role=_safe_role_type(report.role),
            seniority_level=report.seniority,
            context_profile=report.context_profile,
        )
