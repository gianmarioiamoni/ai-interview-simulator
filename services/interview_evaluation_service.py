# services/interview_evaluation_service.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.ports.llm_port import LLMPort

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question import Question
from domain.contracts.report.scoring_dimension import ScoringDimension
from domain.contracts.report.scoring_narrative import ScoringNarrative
from domain.contracts.report.scoring_snapshot import ScoringSnapshot
from domain.contracts.report.scoring_snapshot_builder import ScoringSnapshotBuilder
from domain.contracts.shared.performance_dimension_labels import DIMENSION_LABELS
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from domain.contracts.user.role import RoleType

from services.interview_scoring.interview_scoring_engine import InterviewScoringEngine
from infrastructure.config.evaluation import (
    LEVEL_POOR_THRESHOLD,
    LEVEL_AVERAGE_THRESHOLD,
    LEVEL_STRONG_THRESHOLD,
)
from services.interview_scoring.components.dimension_scorer import AREA_TO_DIMENSION
from services.narrative_service import NarrativeService
from services.decision_engine.decision_engine import DecisionEngine

from services.interview_evaluation.steps.signal_enrichment_step import (
    SignalEnrichmentStep,
)
from services.interview_evaluation.steps.weight_normalization_step import (
    WeightNormalizationStep,
)
from services.interview_evaluation.assemblers.evaluation_narrative_assembler import (
    AssemblerResult,
    EvaluationNarrativeAssembler,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal computation result — zero-cost bridge between old and new artifacts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _ComputedEvaluation:
    """All scoring + narrative outputs from a single evaluate() computation.

    Produced once by _compute(); consumed by both evaluate() (legacy path)
    and evaluate_scoring() (new path). Guarantees zero duplicated computation.
    """

    evaluations: list[QuestionEvaluation]
    dimension_scores: dict
    dimension_signals: dict[str, float]
    weighted_breakdown: dict
    overall_score: float
    raw_score: float
    adjusted_score: float
    hire_decision: HireDecision
    gating_triggered: bool
    gating_reason: Optional[str]
    final_level: InterviewLevel
    scoring_dimensions: tuple[ScoringDimension, ...]
    hiring_probability: float
    assembled: AssemblerResult


class InterviewEvaluationService:
    """Public facade for the interview evaluation pipeline.

    Orchestrates scoring, signal enrichment, weight normalisation, decision,
    and narrative assembly.  Single public surface (Phase 7C):

    - evaluate_scoring() → (ScoringSnapshot, ScoringNarrative)

    Delegates to _compute() which runs the pipeline exactly once.
    """

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

        self._scoring_engine = InterviewScoringEngine()
        self._narrative_service = NarrativeService(llm)
        self._decision_engine = DecisionEngine()

        self._signal_enrichment = SignalEnrichmentStep()
        self._weight_normalization = WeightNormalizationStep()
        self._narrative_assembler = EvaluationNarrativeAssembler(
            llm=llm,
            narrative_service=self._narrative_service,
        )

    # ------------------------------------------------------------------
    # Public — sole surface (ADR-033; Phase 7C)
    # ------------------------------------------------------------------

    def evaluate_scoring(
        self,
        question_results: List[QuestionResult],
        questions: List[Question],
        interview_type: InterviewType,
        role: RoleType,
        context_profile: Optional[InterviewContextProfile] = None,
        seniority_level: str = "mid",
    ) -> tuple[ScoringSnapshot, ScoringNarrative]:
        """Run the full pipeline and return (ScoringSnapshot, ScoringNarrative).

        Sole public surface (ADR-033, Phase 7C). InterviewEvaluation retired.
        """
        computed = self._compute(
            question_results=question_results,
            questions=questions,
            interview_type=interview_type,
            role=role,
            context_profile=context_profile,
            seniority_level=seniority_level,
        )
        return self._build_scoring_snapshot(computed), computed.assembled.scoring_narrative

    # ------------------------------------------------------------------
    # Private — single computation pipeline
    # ------------------------------------------------------------------

    def _compute(
        self,
        question_results: List[QuestionResult],
        questions: List[Question],
        interview_type: InterviewType,
        role: RoleType,
        context_profile: Optional[InterviewContextProfile],
        seniority_level: str,
    ) -> _ComputedEvaluation:

        # 1. INPUT VALIDATION
        if not question_results:
            raise ValueError("Cannot evaluate interview without question results")

        evaluations: List[QuestionEvaluation] = [
            qr.evaluation for qr in question_results if qr.evaluation is not None
        ]

        if not evaluations:
            raise ValueError("No question evaluations available")

        # 2. BASE SCORING
        scoring = self._scoring_engine.compute(
            questions=questions,
            evaluations=evaluations,
            role=role,
        )

        base_dimension_scores = scoring.dimension_scores or {}

        # 3. SIGNAL EXTRACTION + ENRICHMENT
        dimension_signals = self._signal_enrichment.extract_signals(question_results)

        question_map = {q.id: q for q in questions}
        execution_dims: set[str] = set()
        for qr in question_results:
            if qr.execution is not None:
                q = question_map.get(qr.question_id)
                if q is not None:
                    dim = AREA_TO_DIMENSION.get(q.area)
                    if dim is not None:
                        execution_dims.add(dim.value if hasattr(dim, "value") else dim)

        dimension_scores = self._signal_enrichment.enrich_scores(
            base_dimension_scores=base_dimension_scores,
            dimension_signals=dimension_signals,
            execution_dims=execution_dims,
        )

        # 4. WEIGHT NORMALISATION
        weighted_breakdown, overall_score = self._weight_normalization.compute(
            dimension_scores=dimension_scores,
            role=role,
        )

        # 5. DECISION
        raw_score = overall_score

        hire_decision, adjusted_score, gating_triggered, gating_reason = (
            self._decision_engine.compute_decision(
                dimension_scores=dimension_scores,
                overall_score=overall_score,
                role=role,
            )
        )

        overall_score = adjusted_score

        logger.info(
            "DECISION TRACE → raw=%s, adjusted=%s, decision=%s, gating=%s",
            raw_score,
            adjusted_score,
            hire_decision,
            gating_reason,
        )

        # 6. NARRATIVE ASSEMBLY (single LLM call)
        assembled = self._narrative_assembler.assemble(
            dimension_scores=dimension_scores,
            dimension_signals=dimension_signals,
            hire_decision=hire_decision,
            overall_score=overall_score,
            scoring=scoring,
            evaluations=evaluations,
            interview_type=interview_type,
            role=role,
            context_profile=context_profile,
            seniority_level=seniority_level,
        )

        # 7. LEVEL DERIVATION
        if adjusted_score < LEVEL_POOR_THRESHOLD:
            final_level = InterviewLevel.POOR
        elif adjusted_score < LEVEL_AVERAGE_THRESHOLD:
            final_level = InterviewLevel.AVERAGE
        elif adjusted_score < LEVEL_STRONG_THRESHOLD:
            final_level = InterviewLevel.STRONG
        else:
            final_level = InterviewLevel.EXCELLENT

        # 8. SCORING DIMENSIONS
        narrative_dict = assembled.narrative_dict
        dimension_justifications: dict[str, str] = narrative_dict.get(
            "dimension_justifications", {}
        )

        scoring_dimensions: list[ScoringDimension] = []

        for dim_type, score in dimension_scores.items():
            if not isinstance(dim_type, PerformanceDimensionType):
                continue

            dim_signal = dimension_signals.get(dim_type.value, 0.0)
            wb_value = weighted_breakdown.get(dim_type, 0.0)

            # weighted_contribution = normalized weight fraction (0–1).
            # wb_value = score * normalized_weight → normalized_weight = wb_value / score
            if score > 0.0:
                raw_contribution = round(wb_value / score, 6)
                weighted_contribution = max(0.0, min(1.0, raw_contribution))
            else:
                weighted_contribution = 0.0

            readable_name = DIMENSION_LABELS.get(dim_type, dim_type.value)
            justification = (
                dimension_justifications.get(readable_name)
                or "No justification available."
            )

            if score < LEVEL_POOR_THRESHOLD:
                dim_level = "weak"
            elif score < LEVEL_STRONG_THRESHOLD:
                dim_level = "moderate"
            else:
                dim_level = "strong"

            scoring_dimensions.append(
                ScoringDimension(
                    dimension_type=dim_type,
                    score=score,
                    signal=min(1.0, max(0.0, dim_signal)),
                    weighted_contribution=weighted_contribution,
                    justification=justification,
                    level=dim_level,
                )
            )

        return _ComputedEvaluation(
            evaluations=evaluations,
            dimension_scores=dimension_scores,
            dimension_signals=dimension_signals,
            weighted_breakdown=weighted_breakdown,
            overall_score=overall_score,
            raw_score=raw_score,
            adjusted_score=adjusted_score,
            hire_decision=hire_decision,
            gating_triggered=gating_triggered,
            gating_reason=gating_reason,
            final_level=final_level,
            scoring_dimensions=tuple(scoring_dimensions),
            hiring_probability=scoring.hiring_probability,
            assembled=assembled,
        )

    # ------------------------------------------------------------------
    # Private — artifact construction from _ComputedEvaluation
    # ------------------------------------------------------------------

    @staticmethod
    def _build_scoring_snapshot(c: _ComputedEvaluation) -> ScoringSnapshot:
        assembled = c.assembled
        return (
            ScoringSnapshotBuilder()
            .with_overall_score(c.overall_score)
            .with_raw_score(c.raw_score)
            .with_adjusted_score(c.adjusted_score)
            .with_scoring_dimensions(c.scoring_dimensions)
            .with_level(c.final_level)
            .with_hire_decision(c.hire_decision)
            .with_hiring_probability(c.hiring_probability)
            .with_percentile_rank(assembled.percentile)
            .with_percentile_explanation(assembled.percentile_explanation)
            .with_decision_explanation(assembled.decision_explanation)
            .with_gating(c.gating_triggered, c.gating_reason)
            .with_confidence(assembled.confidence)
            .build()
        )
