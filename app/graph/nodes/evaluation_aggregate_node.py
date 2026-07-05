# app/graph/nodes/evaluation_aggregate_node.py

from domain.contracts.shared.action_type import ActionType
from infrastructure.llm.metrics.interview_metrics_aggregator import (
    InterviewMetricsAggregator,
)
from services.interview_evaluation_service import InterviewEvaluationService
from services.observability.interview_cost_calculator import InterviewCostCalculator
from app.core.logger import get_logger

logger = get_logger(__name__)


class EvaluationAggregateNode:

    def __init__(self, service: InterviewEvaluationService):
        self._service = service
        self._metrics_aggregator = InterviewMetricsAggregator()
        self._cost_calculator = InterviewCostCalculator()

    def __call__(self, state):

        # ---------------------------------------------------------
        # IDENTITY / GUARDS
        # ---------------------------------------------------------

        # Already computed → no-op (idempotent).
        # Phase 7A: guard uses scoring_snapshot (the new canonical field).
        # interview_evaluation is kept as bridge until Phase 7C.
        if state.scoring_snapshot is not None:
            return state

        # Not finished → skip
        if not state.is_completed:
            return state

        # ---------------------------------------------------------
        # SOURCE OF TRUTH: QuestionResult
        # ---------------------------------------------------------

        question_results = list(state.results_by_question.values())

        if not question_results:
            logger.error("Cannot compute interview evaluation: no question results")
            return state.model_copy(
                update={"current_step": None, "intent": ActionType.NONE}
            )

        # ---------------------------------------------------------
        # EVALUATION
        # ---------------------------------------------------------

        try:
            _kwargs = dict(
                question_results=question_results,
                questions=state.questions,
                interview_type=state.interview_type,
                role=state.role.type,
                context_profile=state.context_profile,
                seniority_level=getattr(state, "seniority_level", "mid") or "mid",
            )
            # Bridge (Phase 7A): produce legacy artifact for downstream readers.
            interview_eval = self._service.evaluate(**_kwargs)
            # New artifacts (ADR-033): produced via evaluate_scoring() which
            # internally calls _compute() independently — no shared cache.
            # Each call runs the full pipeline once; no computation is shared
            # between evaluate() and evaluate_scoring() in the current bridge.
            # Phase 7C will remove evaluate() and this dual-call.
            scoring_snapshot, scoring_narrative = self._service.evaluate_scoring(**_kwargs)
        except Exception as exc:
            logger.error("Interview evaluation failed: %s", exc)
            return state.model_copy(
                update={"current_step": None, "intent": ActionType.NONE}
            )

        # ---------------------------------------------------------
        # LLM METRICS SNAPSHOT
        # ---------------------------------------------------------

        from app.runtime.interview_runtime import get_runtime_metrics_collector

        raw_metrics = get_runtime_metrics_collector().get_metrics()
        interview_metrics = self._metrics_aggregator.aggregate(raw_metrics)
        interview_cost_metrics = self._cost_calculator.calculate(
            interview_metrics,
            question_count=len(state.questions),
        )

        # ---------------------------------------------------------
        # STATE UPDATE
        # ---------------------------------------------------------

        return state.model_copy(
            update={
                "interview_evaluation": interview_eval,
                "scoring_snapshot": scoring_snapshot,
                "scoring_narrative": scoring_narrative,
                "interview_metrics": interview_metrics,
                "interview_cost_metrics": interview_cost_metrics,
                "intent": ActionType.NONE,
                "current_step": None,
            }
        )
