# app/graph/nodes/feedback_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.feedback.quality import Quality
from domain.contracts.shared.action_type import ActionType

from services.score_calculator import ScoreCalculator
from services.feedback.dimension_aggregator import FeedbackDimensionAggregator

from app.ui.presenters.feedback.feedback_builder import FeedbackBuilder
from app.ui.constants.loader_steps import LoaderStep
from app.ports.llm_port import LLMPort


class FeedbackNode:

    def __init__(self, llm: LLMPort):
        self._builder = FeedbackBuilder(llm)
        self._scorer = ScoreCalculator()
        self._dimension_aggregator = FeedbackDimensionAggregator()

    def __call__(self, state: InterviewState) -> InterviewState:

        if state.last_action == ActionType.GENERATE_REPORT:
            return state

        working_state = state.model_copy(
            update={"current_step": LoaderStep.GENERATING_FEEDBACK}
        )

        question = state.current_question
        if question is None:
            return working_state

        result = state.get_result_for_question(question.id)
        if not result:
            return working_state

        execution = result.execution
        evaluation = result.evaluation

        # -----------------------------------------------------
        # SCORE + QUALITY
        # -----------------------------------------------------

        if execution:
            score, quality = self._scorer.compute(
                passed=execution.passed_tests,
                total=execution.total_tests,
                execution_time_ms=execution.execution_time_ms,
            )

        elif evaluation:
            score = evaluation.score or 0.0

            if score >= 75:
                quality = Quality.CORRECT
            elif score >= 50:
                quality = Quality.PARTIAL
            else:
                quality = Quality.INCORRECT

        else:
            score = 0.0
            quality = Quality.INCORRECT

        # -----------------------------------------------------
        # BUILD BUNDLE 
        # -----------------------------------------------------

        bundle = self._builder.build(
            state=state,
            result=result,
            evaluation=evaluation,
            execution=execution,
            quality=quality,  
        )

        # -----------------------------------------------------
        # AGGREGATE DIMENSIONS
        # -----------------------------------------------------

        dimension_signals = self._dimension_aggregator.aggregate(bundle.blocks)
        print("DIMENSION SIGNALS:", dimension_signals)

        # -----------------------------------------------------
        # ENRICH BUNDLE (KEEP - backward compatibility)
        # -----------------------------------------------------

        from app.contracts.feedback_bundle import FeedbackBundle

        updated_bundle = FeedbackBundle(
            blocks=bundle.blocks,
            overall_severity=bundle.overall_severity,
            overall_confidence=bundle.overall_confidence,
            overall_quality=quality,
            markdown=bundle.markdown,
        )
        updated_bundle.dimension_signals = dimension_signals

        return working_state.model_copy(
            update={
                "last_feedback_bundle": updated_bundle,
            }
        )
