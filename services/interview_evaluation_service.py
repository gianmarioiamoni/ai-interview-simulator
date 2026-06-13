# services/interview_evaluation_service.py

from typing import List

from app.ports.llm_port import LLMPort

from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.question import Question
from domain.contracts.user.role import RoleType

from services.interview_scoring.interview_scoring_engine import InterviewScoringEngine
from services.narrative_service import NarrativeService
from services.decision_engine.decision_engine import DecisionEngine

from services.interview_evaluation.steps.signal_enrichment_step import (
    SignalEnrichmentStep,
)
from services.interview_evaluation.steps.weight_normalization_step import (
    WeightNormalizationStep,
)
from services.interview_evaluation.assemblers.evaluation_narrative_assembler import (
    EvaluationNarrativeAssembler,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class InterviewEvaluationService:
    """
    Public facade for the interview evaluation pipeline.

    Orchestrates:
    1. Input validation + evaluation extraction
    2. Base scoring (InterviewScoringEngine)
    3. Signal extraction + score enrichment (SignalEnrichmentStep)
    4. Weight normalisation + overall score (WeightNormalizationStep)
    5. Hire decision (DecisionEngine)
    6. Narrative assembly (EvaluationNarrativeAssembler)
    7. Final DTO construction
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

    # ---------------------------------------------------------

    def evaluate(
        self,
        question_results: List[QuestionResult],
        questions: List[Question],
        interview_type: InterviewType,
        role: RoleType,
    ) -> InterviewEvaluation:

        # -----------------------------------------------------
        # 1. INPUT VALIDATION
        # -----------------------------------------------------

        if not question_results:
            raise ValueError("Cannot evaluate interview without question results")

        evaluations: List[QuestionEvaluation] = [
            qr.evaluation for qr in question_results if qr.evaluation is not None
        ]

        if not evaluations:
            raise ValueError("No question evaluations available")

        # -----------------------------------------------------
        # 2. BASE SCORING
        # -----------------------------------------------------

        scoring = self._scoring_engine.compute(
            questions=questions,
            evaluations=evaluations,
            role=role,
        )

        base_dimension_scores = scoring.dimension_scores or {}

        # -----------------------------------------------------
        # 3. SIGNAL EXTRACTION + ENRICHMENT
        # -----------------------------------------------------

        dimension_signals = self._signal_enrichment.extract_signals(question_results)

        dimension_scores = self._signal_enrichment.enrich_scores(
            base_dimension_scores=base_dimension_scores,
            dimension_signals=dimension_signals,
        )

        # -----------------------------------------------------
        # 4. WEIGHT NORMALISATION
        # -----------------------------------------------------

        weighted_breakdown, overall_score = self._weight_normalization.compute(
            dimension_scores=dimension_scores,
            role=role,
        )

        # -----------------------------------------------------
        # 5. DECISION
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # 6. NARRATIVE ASSEMBLY
        # -----------------------------------------------------

        narrative_outputs = self._narrative_assembler.assemble(
            dimension_scores=dimension_scores,
            dimension_signals=dimension_signals,
            hire_decision=hire_decision,
            overall_score=overall_score,
            scoring=scoring,
            evaluations=evaluations,
            interview_type=interview_type,
            role=role,
        )

        # -----------------------------------------------------
        # 7. FINAL DTO
        # -----------------------------------------------------

        return InterviewEvaluation(
            overall_score=overall_score,
            raw_score=raw_score,
            adjusted_score=adjusted_score,
            executive_summary=narrative_outputs["executive_summary"],
            performance_dimensions=narrative_outputs["performance_dimensions"],
            dimension_scores=dimension_scores,
            dimension_signals=dimension_signals,
            level=scoring.level,
            hire_decision=hire_decision,
            decision_explanation=narrative_outputs["decision_explanation"],
            hiring_probability=scoring.hiring_probability,
            percentile_rank=narrative_outputs["percentile"],
            percentile_explanation=narrative_outputs["percentile_explanation"],
            gating_triggered=gating_triggered,
            gating_reason=gating_reason,
            weighted_breakdown=weighted_breakdown,
            per_question_assessment=evaluations,
            improvement_suggestions=narrative_outputs["improvement_suggestions"],
            confidence=narrative_outputs["confidence"],
        )
