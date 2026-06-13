# services/interview_evaluation_service.py

from typing import List

from app.ports.llm_port import LLMPort

from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.feedback.confidence import Confidence
from domain.contracts.question.question import Question
from domain.contracts.user.role import RoleType, ROLE_DISTRIBUTION, ROLE_WEIGHTS

from services.interview_scoring.interview_scoring_engine import InterviewScoringEngine
from services.narrative_service import NarrativeService
from services.decision_engine.decision_engine import DecisionEngine

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
from services.execution_analysis.execution_analyzer import ExecutionAnalyzer
from infrastructure.config.evaluation import ENRICHMENT_ALPHA

from app.core.logger import get_logger

logger = get_logger(__name__)


class InterviewEvaluationService:

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

        # core services
        self._scoring_engine = InterviewScoringEngine()
        self._narrative_service = NarrativeService(llm)
        self._signal_extractor = SignalExtractor()
        self._execution_analyzer = ExecutionAnalyzer()

        # components
        self._dimension_mapper = ReadableDimensionMapper()
        self._decision_generator = DecisionExplanationGenerator(self._narrative_service)
        self._decision_engine = DecisionEngine()
        self._summary_generator = ExecutiveSummaryGenerator(self._narrative_service)
        self._dimension_builder = DimensionBuilder()
        self._improvement_builder = ImprovementBuilder()
        self._narrative_generator = NarrativeGenerator(llm)

    # ---------------------------------------------------------

    def evaluate(
        self,
        question_results: List[QuestionResult],
        questions: List[Question],
        interview_type: InterviewType,
        role: RoleType,
    ) -> InterviewEvaluation:

        if not question_results:
            raise ValueError("Cannot evaluate interview without question results")

        # -----------------------------------------------------
        # EXTRACT EVALUATIONS
        # -----------------------------------------------------

        evaluations: List[QuestionEvaluation] = [
            qr.evaluation for qr in question_results if qr.evaluation is not None
        ]

        if not evaluations:
            raise ValueError("No question evaluations available")

        # -----------------------------------------------------
        # SCORING (BASE)
        # -----------------------------------------------------

        scoring = self._scoring_engine.compute(
            questions=questions,
            evaluations=evaluations,
            role=role,
        )

        base_dimension_scores = scoring.dimension_scores or {}
        overall_score = scoring.overall_score

        # -----------------------------------------------------
        # SIGNAL EXTRACTION
        # -----------------------------------------------------

        dimension_signals = {}

        try:
            for qr in question_results:

                execution = qr.execution
                if not execution:
                    continue

                analysis = self._execution_analyzer.analyze(execution)

                signals = self._signal_extractor.extract(
                    execution=execution,
                    error_type=analysis.error_type,
                    analysis=analysis,
                )

                for k, v in signals.items():
                    dimension_signals[k] = dimension_signals.get(k, 0.0) + v

            dimension_signals = {
                k: round(min(1.0, v), 2) for k, v in dimension_signals.items()
            }

            print("FINAL DIMENSION SIGNALS:", dimension_signals)

        except Exception as e:
            logger.warning(f"signal_extraction_failed: {e}")
            dimension_signals = {}

        # -----------------------------------------------------
        # ENRICHMENT
        # -----------------------------------------------------

        enriched_scores = {}

        for dim, base_score in base_dimension_scores.items():

            dim_key = dim.value if hasattr(dim, "value") else dim
            signal = dimension_signals.get(dim_key, 0.0)

            enriched = (
                base_score * (1 - ENRICHMENT_ALPHA) + (signal * 100) * ENRICHMENT_ALPHA
            )

            enriched_scores[dim] = round(enriched, 1)

        dimension_scores = enriched_scores

        # -----------------------------------------------------
        # NORMALIZED WEIGHTS (FIX)
        # -----------------------------------------------------

        weights = ROLE_WEIGHTS[role]

        valid_weights = {
            dim: weight for dim, weight in weights.items() if dim in dimension_scores
        }

        total_weight = sum(valid_weights.values())

        if total_weight == 0:
            raise ValueError("Total weight is zero after filtering dimensions")

        normalized_weights = {
            dim: weight / total_weight for dim, weight in valid_weights.items()
        }

        weighted_breakdown = {}

        for dim, score in dimension_scores.items():

            if dim not in normalized_weights:
                continue

            weight = normalized_weights[dim]
            weighted_breakdown[dim] = round(score * weight, 2)

        overall_score = round(sum(weighted_breakdown.values()), 1)

        # -----------------------------------------------------
        # DECISION ENGINE (UNICA FONTE DI VERITÀ)
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
            f"DECISION TRACE → raw={raw_score}, adjusted={adjusted_score}, "
            f"decision={hire_decision}, gating={gating_reason}"
        )

        # -----------------------------------------------------
        # READABLE DIMENSIONS
        # -----------------------------------------------------

        readable, strongest, weakest, strongest_score, weakest_score = (
            self._dimension_mapper.map(dimension_scores)
        )

        # -----------------------------------------------------
        # DECISION EXPLANATION
        # -----------------------------------------------------

        decision_explanation = self._decision_generator.generate(
            hire_decision.value,
            readable,
            dimension_signals,
        )

        # -----------------------------------------------------
        # PERCENTILE
        # -----------------------------------------------------

        percentile = scoring.percentile
        dist_params = ROLE_DISTRIBUTION[role]

        percentile_explanation = (
            f"Percentile computed analytically using role-specific "
            f"normal distribution (μ={dist_params['mean']}, σ={dist_params['std']})."
        )

        # -----------------------------------------------------
        # CONFIDENCE
        # -----------------------------------------------------

        confidence = Confidence(
            base=scoring.confidence,
            final=scoring.confidence,
        )

        # -----------------------------------------------------
        # EXECUTIVE SUMMARY
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # NARRATIVE
        # -----------------------------------------------------

        narrative = self._narrative_generator.generate(
            evaluations,
            dimension_scores,
            interview_type,
            role,
        )

        # -----------------------------------------------------
        # DIMENSIONS
        # -----------------------------------------------------

        performance_dimensions = self._dimension_builder.build(
            dimension_scores,
            narrative,
        )

        # -----------------------------------------------------
        # IMPROVEMENTS
        # -----------------------------------------------------

        improvement_suggestions = self._improvement_builder.build(
            dimension_scores,
            narrative,
        )

        # -----------------------------------------------------
        # FINAL OBJECT
        # -----------------------------------------------------

        return InterviewEvaluation(
            overall_score=overall_score,
            raw_score=raw_score,
            adjusted_score=adjusted_score,
            executive_summary=executive_summary,
            performance_dimensions=performance_dimensions,
            dimension_scores=dimension_scores,
            dimension_signals=dimension_signals,
            level=scoring.level,
            hire_decision=hire_decision,
            decision_explanation=decision_explanation,
            hiring_probability=scoring.hiring_probability,
            percentile_rank=percentile,
            percentile_explanation=percentile_explanation,
            gating_triggered=gating_triggered,
            gating_reason=gating_reason,
            weighted_breakdown=weighted_breakdown,
            per_question_assessment=evaluations,
            improvement_suggestions=improvement_suggestions,
            confidence=confidence,
        )
