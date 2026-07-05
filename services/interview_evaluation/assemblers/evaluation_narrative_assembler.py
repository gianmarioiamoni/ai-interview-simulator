# services/interview_evaluation/assemblers/evaluation_narrative_assembler.py

from typing import Any, Dict, List, Optional

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.report.scoring_narrative import ScoringNarrative
from domain.contracts.report.scoring_narrative_item import ScoringNarrativeItem
from domain.contracts.user.role import ROLE_DISTRIBUTION, RoleType

from app.ports.llm_port import LLMPort

from services.narrative_service import NarrativeService
from services.interview_evaluation.builders.dimension_builder import DimensionBuilder
from services.interview_evaluation.builders.improvement_builder import ImprovementBuilder
from services.interview_evaluation.generators.decision_explanation_generator import (
    DecisionExplanationGenerator,
)
from services.interview_evaluation.generators.executive_summary_generator import (
    ExecutiveSummaryGenerator,
)
from services.interview_evaluation.generators.narrative_generator import (
    NarrativeGenerator,
)
from services.interview_evaluation.mappers.readable_dimension_mapper import (
    ReadableDimensionMapper,
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
    - Construct ScoringNarrative (ADR-033)
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
        context_profile: Optional[InterviewContextProfile] = None,
        seniority_level: str = "mid",
    ) -> "AssemblerResult":
        """
        Compute and return all narrative fields as an AssemblerResult.

        The result exposes both the legacy dict fields (for backward
        compatibility within Phase 6 only) and the new ScoringNarrative.
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
            context_profile=context_profile,
            evaluations=evaluations,
            seniority_level=seniority_level,
            role=role.value if hasattr(role, "value") else str(role),
        )

        if not executive_summary or not executive_summary.strip():
            logger.warning("executive_summary_empty → fallback applied")
            executive_summary = (
                f"The candidate achieved an overall score of {overall_score:.1f}. "
                f"Strongest area: {strongest} ({strongest_score:.1f}). "
                f"Area for improvement: {weakest} ({weakest_score:.1f})."
            )

        # -------------------------------------------------
        # NARRATIVE (LLM dict)
        # -------------------------------------------------

        narrative_dict = self._narrative_generator.generate(
            evaluations,
            dimension_scores,
            interview_type,
            role,
            context_profile=context_profile,
        )

        # -------------------------------------------------
        # DIMENSIONS + IMPROVEMENTS
        # -------------------------------------------------

        performance_dimensions = self._dimension_builder.build(
            dimension_scores,
            narrative_dict,
        )

        improvement_suggestions = self._improvement_builder.build(
            dimension_scores,
            narrative_dict,
            evaluations=evaluations,
        )

        # -------------------------------------------------
        # SCORING NARRATIVE (ADR-033)
        # -------------------------------------------------

        scoring_narrative = self._build_scoring_narrative(
            executive_summary=executive_summary,
            narrative_dict=narrative_dict,
            improvement_suggestions_list=improvement_suggestions,
        )

        return AssemblerResult(
            readable=readable,
            strongest=strongest,
            weakest=weakest,
            strongest_score=strongest_score,
            weakest_score=weakest_score,
            decision_explanation=decision_explanation,
            percentile=percentile,
            percentile_explanation=percentile_explanation,
            confidence=confidence,
            executive_summary=executive_summary,
            narrative_dict=narrative_dict,
            performance_dimensions=performance_dimensions,
            improvement_suggestions=improvement_suggestions,
            scoring_narrative=scoring_narrative,
        )

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    def _build_scoring_narrative(
        self,
        executive_summary: str,
        narrative_dict: Dict[str, Any],
        improvement_suggestions_list: list,
    ) -> ScoringNarrative:
        went_well = tuple(narrative_dict.get("went_well", []))

        held_you_back = self._map_held_you_back(
            narrative_dict.get("held_you_back", [])
        )
        knowledge_gaps = self._map_knowledge_gaps(
            narrative_dict.get("knowledge_gaps", [])
        )
        next_strategy = self._map_next_strategy(
            narrative_dict.get("next_strategy", [])
        )

        # improvement_suggestions come from ImprovementBuilder as list[str]
        improvement_suggestions = tuple(
            str(s) for s in improvement_suggestions_list if s
        )

        return ScoringNarrative(
            executive_summary=executive_summary,
            went_well=went_well,
            held_you_back=held_you_back,
            knowledge_gaps=knowledge_gaps,
            next_strategy=next_strategy,
            improvement_suggestions=improvement_suggestions,
        )

    @staticmethod
    def _map_held_you_back(
        items: List[Any],
    ) -> tuple[ScoringNarrativeItem, ...]:
        result = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    ScoringNarrativeItem(
                        category="held_you_back",
                        description=str(item.get("behaviour") or "").strip() or "—",
                        why_it_matters=str(item.get("why_it_matters") or "").strip() or "—",
                        context_detail=str(item.get("impact") or "").strip() or None,
                    )
                )
            except Exception:
                logger.warning("held_you_back_item_skipped | item=%s", item)
        return tuple(result)

    @staticmethod
    def _map_knowledge_gaps(
        items: List[Any],
    ) -> tuple[ScoringNarrativeItem, ...]:
        result = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    ScoringNarrativeItem(
                        category=str(item.get("category") or "knowledge_gap").strip() or "knowledge_gap",
                        description=str(item.get("concept") or "").strip() or "—",
                        why_it_matters=str(item.get("why_it_matters") or "").strip() or "—",
                        context_detail=str(item.get("interview_impact") or "").strip() or None,
                    )
                )
            except Exception:
                logger.warning("knowledge_gap_item_skipped | item=%s", item)
        return tuple(result)

    @staticmethod
    def _map_next_strategy(
        items: List[Any],
    ) -> tuple[ScoringNarrativeItem, ...]:
        result = []
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    ScoringNarrativeItem(
                        category=str(item.get("priority") or "").strip() or "—",
                        description=str(item.get("why") or "").strip() or "—",
                        why_it_matters=str(item.get("expected_improvement") or "").strip() or "—",
                        context_detail=str(item.get("impact") or "").strip() or None,
                    )
                )
            except Exception:
                logger.warning("next_strategy_item_skipped | item=%s", item)
        return tuple(result)


class AssemblerResult:
    """Structured result from EvaluationNarrativeAssembler.assemble().

    Replaces the previous untyped dict return. Exposes all fields needed
    by InterviewEvaluationService for building both InterviewEvaluation
    (Phase 6 compat) and the new ScoringNarrative artifact (ADR-033).
    """

    __slots__ = (
        "readable", "strongest", "weakest", "strongest_score", "weakest_score",
        "decision_explanation", "percentile", "percentile_explanation",
        "confidence", "executive_summary", "narrative_dict",
        "performance_dimensions", "improvement_suggestions", "scoring_narrative",
    )

    def __init__(
        self,
        *,
        readable,
        strongest,
        weakest,
        strongest_score,
        weakest_score,
        decision_explanation,
        percentile,
        percentile_explanation,
        confidence,
        executive_summary,
        narrative_dict,
        performance_dimensions,
        improvement_suggestions,
        scoring_narrative: ScoringNarrative,
    ) -> None:
        self.readable = readable
        self.strongest = strongest
        self.weakest = weakest
        self.strongest_score = strongest_score
        self.weakest_score = weakest_score
        self.decision_explanation = decision_explanation
        self.percentile = percentile
        self.percentile_explanation = percentile_explanation
        self.confidence = confidence
        self.executive_summary = executive_summary
        self.narrative_dict = narrative_dict
        self.performance_dimensions = performance_dimensions
        self.improvement_suggestions = improvement_suggestions
        self.scoring_narrative = scoring_narrative
