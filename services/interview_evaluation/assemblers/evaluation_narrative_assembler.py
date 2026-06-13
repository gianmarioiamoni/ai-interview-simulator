# services/interview_evaluation/assemblers/evaluation_narrative_assembler.py

from typing import Dict, List, Any

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.user.role import RoleType, ROLE_DISTRIBUTION

from app.ports.llm_port import LLMPort

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

from app.core.logger import get_logger

logger = get_logger(__name__)


class EvaluationNarrativeAssembler:
    """
    Assembles all narrative and presentational outputs for an interview
    evaluation result.

    Responsibilities:
    - Map dimension scores to human-readable form
    - Generate decision explanation
    - Compute percentile metadata
    - Build confidence object
    - Generate executive summary (with fallback)
    - Generate per-dimension narrative
    - Build performance dimensions
    - Build improvement suggestions
    """

    def __init__(self, llm: LLMPort, narrative_service: NarrativeService) -> None:
        self._dimension_mapper = ReadableDimensionMapper()
        self._decision_generator = DecisionExplanationGenerator(narrative_service)
        self._summary_generator = ExecutiveSummaryGenerator(narrative_service)
        self._dimension_builder = DimensionBuilder()
        self._improvement_builder = ImprovementBuilder()
        self._narrative_generator = NarrativeGenerator(llm)

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def assemble(
        self,
        dimension_scores: Dict,
        dimension_signals: Dict[str, float],
        hire_decision,
        overall_score: float,
        scoring,
        evaluations: List[QuestionEvaluation],
        interview_type: InterviewType,
        role: RoleType,
    ) -> Dict[str, Any]:
        """
        Compute and return all narrative fields needed by InterviewEvaluation.

        Returns a dict with keys:
          readable, strongest, weakest, strongest_score, weakest_score,
          decision_explanation, percentile, percentile_explanation, confidence,
          executive_summary, narrative, performance_dimensions, improvement_suggestions
        """

        # -------------------------------------------------
        # READABLE DIMENSIONS
        # -------------------------------------------------

        readable, strongest, weakest, strongest_score, weakest_score = (
            self._dimension_mapper.map(dimension_scores)
        )

        # -------------------------------------------------
        # DECISION EXPLANATION
        # -------------------------------------------------

        decision_explanation = self._decision_generator.generate(
            hire_decision.value,
            readable,
            dimension_signals,
        )

        # -------------------------------------------------
        # PERCENTILE
        # -------------------------------------------------

        percentile = scoring.percentile
        dist_params = ROLE_DISTRIBUTION[role]

        percentile_explanation = (
            f"Percentile computed analytically using role-specific "
            f"normal distribution (μ={dist_params['mean']}, σ={dist_params['std']})."
        )

        # -------------------------------------------------
        # CONFIDENCE
        # -------------------------------------------------

        confidence = Confidence(
            base=scoring.confidence,
            final=scoring.confidence,
        )

        # -------------------------------------------------
        # EXECUTIVE SUMMARY
        # -------------------------------------------------

        executive_summary = self._summary_generator.generate(
            hire_decision.value,
            overall_score,
            strongest,
            weakest,
            percentile,
            strongest_score,
            weakest_score,
        )

        if not executive_summary or not executive_summary.strip():
            logger.warning("executive_summary_empty → fallback applied")
            executive_summary = (
                f"The candidate achieved an overall score of {overall_score:.1f}. "
                f"Strongest area: {strongest} ({strongest_score:.1f}). "
                f"Area for improvement: {weakest} ({weakest_score:.1f})."
            )

        # -------------------------------------------------
        # NARRATIVE
        # -------------------------------------------------

        narrative = self._narrative_generator.generate(
            evaluations,
            dimension_scores,
            interview_type,
            role,
        )

        # -------------------------------------------------
        # DIMENSIONS + IMPROVEMENTS
        # -------------------------------------------------

        performance_dimensions = self._dimension_builder.build(
            dimension_scores,
            narrative,
        )

        improvement_suggestions = self._improvement_builder.build(
            dimension_scores,
            narrative,
        )

        return {
            "readable": readable,
            "strongest": strongest,
            "weakest": weakest,
            "strongest_score": strongest_score,
            "weakest_score": weakest_score,
            "decision_explanation": decision_explanation,
            "percentile": percentile,
            "percentile_explanation": percentile_explanation,
            "confidence": confidence,
            "executive_summary": executive_summary,
            "narrative": narrative,
            "performance_dimensions": performance_dimensions,
            "improvement_suggestions": improvement_suggestions,
        }
