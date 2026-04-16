# services/interview_evaluation/interview_evaluation_service.py

from typing import List
import logging

from app.ports.llm_port import LLMPort

from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.feedback.confidence import Confidence
from domain.contracts.question.question import Question
from domain.contracts.user.role import RoleType, ROLE_DISTRIBUTION

from services.interview_scoring.interview_scoring_engine import InterviewScoringEngine
from services.narrative_service import NarrativeService

from services.interview_evaluation.mappers.readable_dimension_mapper import ReadableDimensionMapper
from services.interview_evaluation.generators.decision_explanation_generator import DecisionExplanationGenerator
from services.interview_evaluation.generators.executive_summary_generator import ExecutiveSummaryGenerator
from services.interview_evaluation.builders.dimension_builder import DimensionBuilder
from services.interview_evaluation.builders.improvement_builder import ImprovementBuilder

logger = logging.getLogger(__name__)


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

        self._scoring_engine = InterviewScoringEngine()
        self._narrative_service = NarrativeService(llm)

        # components
        self._dimension_mapper = ReadableDimensionMapper()
        self._decision_generator = DecisionExplanationGenerator(self._narrative_service)
        self._summary_generator = ExecutiveSummaryGenerator(self._narrative_service)
        self._dimension_builder = DimensionBuilder()
        self._improvement_builder = ImprovementBuilder()

    # ---------------------------------------------------------

    def evaluate(
        self,
        per_question_evaluations: List[QuestionEvaluation],
        questions: List[Question],
        interview_type: InterviewType,
        role: RoleType,
    ) -> InterviewEvaluation:

        if not per_question_evaluations:
            raise ValueError("Cannot evaluate interview without question evaluations")

        scoring = self._scoring_engine.compute(
            questions=questions,
            evaluations=per_question_evaluations,
            role=role,
        )

        dimension_scores = scoring.dimension_scores
        overall_score = scoring.overall_score

        # ---------------- readable dimensions

        readable, strongest, weakest = self._dimension_mapper.map(dimension_scores)

        # ---------------- decision explanation

        decision_explanation = self._decision_generator.generate(
            scoring.hire_decision.value,
            readable,
        )

        # ---------------- percentile

        percentile = scoring.percentile
        dist_params = ROLE_DISTRIBUTION[role]

        percentile_explanation = (
            f"Percentile computed analytically using role-specific "
            f"normal distribution (μ={dist_params['mean']}, σ={dist_params['std']})."
        )

        # ---------------- confidence

        confidence = Confidence(
            base=scoring.confidence,
            final=scoring.confidence,
        )

        # ---------------- executive summary

        executive_summary = self._summary_generator.generate(
            scoring.hire_decision.value,
            overall_score,
            strongest,
            weakest,
            percentile,
        )

        if not executive_summary:
            executive_summary = self._generate_executive_summary(
                overall_score,
                dimension_scores,
            )

        # ---------------- narrative

        narrative = self._generate_narrative(
            per_question_evaluations,
            dimension_scores,
            interview_type,
            role,
        )

        # ---------------- dimensions

        performance_dimensions = self._dimension_builder.build(
            dimension_scores,
            narrative,
        )

        # ---------------- improvements

        improvement_suggestions = self._improvement_builder.build(
            dimension_scores,
            narrative,
        )

        # ---------------- final

        return InterviewEvaluation(
            overall_score=overall_score,
            executive_summary=executive_summary,
            performance_dimensions=performance_dimensions,
            dimension_scores=dimension_scores,
            level=scoring.level,
            hire_decision=scoring.hire_decision,
            decision_explanation=decision_explanation,
            hiring_probability=scoring.hiring_probability,
            percentile_rank=percentile,
            percentile_explanation=percentile_explanation,
            gating_triggered=scoring.gating_triggered,
            gating_reason=scoring.gating_reason,
            weighted_breakdown=scoring.weighted_breakdown,
            per_question_assessment=per_question_evaluations,
            improvement_suggestions=improvement_suggestions,
            confidence=confidence,
        )
