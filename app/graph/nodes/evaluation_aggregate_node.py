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

        # Already computed → no-op (idempotent)
        if state.interview_evaluation is not None:
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
            interview_eval = self._service.evaluate(
                question_results=question_results,
                questions=state.questions,
                interview_type=state.interview_type,
                role=state.role.type,
            )
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
                "interview_metrics": interview_metrics,
                "interview_cost_metrics": interview_cost_metrics,
                "intent": ActionType.NONE,
                "current_step": None,
            }
        )
