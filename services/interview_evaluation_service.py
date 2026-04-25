# services/interview_evaluation_service.py

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

from services.interview_evaluation.mappers.readable_dimension_mapper import (
    ReadableDimensionMapper,
)
from services.interview_evaluation.generators.decision_explanation_generator import (
    DecisionExplanationGenerator,
)
from services.interview_evaluation.generators.executive_summary_generator import (
    ExecutiveSummaryGenerator,
)
from services.interview_evaluation.builders.dimension_builder import DimensionBuilder
from services.interview_evaluation.builders.improvement_builder import (
    ImprovementBuilder,
)
from services.interview_evaluation.generators.narrative_generator import (
    NarrativeGenerator,
)

from services.feedback.signal_extractor import SignalExtractor

logger = logging.getLogger(__name__)


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

        # core services
        self._scoring_engine = InterviewScoringEngine()
        self._narrative_service = NarrativeService(llm)
        self._signal_extractor = SignalExtractor()
        # components
        self._dimension_mapper = ReadableDimensionMapper()
        self._decision_generator = DecisionExplanationGenerator(self._narrative_service)
        self._summary_generator = ExecutiveSummaryGenerator(self._narrative_service)
        self._dimension_builder = DimensionBuilder()
        self._improvement_builder = ImprovementBuilder()
        self._narrative_generator = NarrativeGenerator(llm)

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

        # ---------------- scoring

        scoring = self._scoring_engine.compute(
            questions=questions,
            evaluations=per_question_evaluations,
            role=role,
        )

        dimension_scores = scoring.dimension_scores or {}
        overall_score = scoring.overall_score

        # ---------------- readable dimensions

        readable, strongest, weakest, strongest_score, weakest_score = (
            self._dimension_mapper.map(dimension_scores)
        )

        # ---------------- signals extraction 

        dimension_signals = {}

        try:
            aggregated = {}

            # NOTE:
            # oggi NON hai execution qui → quindi niente signals reali
            # workaround: skip se non hai execution

            # FUTURE (correct design):
            # passare QuestionResult invece di QuestionEvaluation

            for ev in per_question_evaluations:

                # placeholder: execution non disponibile
                continue

            # no signals available for now
            dimension_signals = {}

        except Exception as e:
            logger.warning(f"signal_extraction_failed: {e}")
            dimension_signals = {}

        # ---------------- decision explanation

        decision_explanation = self._decision_generator.generate(
            scoring.hire_decision.value,
            readable,
            dimension_signals,
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

        # ---------------- executive summary (FIXED)

        executive_summary = self._summary_generator.generate(
            scoring.hire_decision.value,
            overall_score,
            strongest,
            weakest,
            percentile,
            strongest_score,
            weakest_score,
        )

        # HARD FALLBACK (NO legacy method)
        if not executive_summary or not executive_summary.strip():
            print("executive_summary_empty → fallback applied")
            print("\n⚠️ EXECUTIVE SUMMARY FALLBACK TRIGGERED\n")

            executive_summary = (
                f"The candidate achieved an overall score of {overall_score:.1f}. "
                f"Strongest area: {strongest} ({strongest_score:.1f}). "
                f"Area for improvement: {weakest} ({weakest_score:.1f})."
            )

        # ---------------- narrative

        narrative = self._narrative_generator.generate(
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

        # ---------------- final object

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
