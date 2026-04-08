# app/graph/nodes/feedback_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.quality import Quality

from services.score_calculator import ScoreCalculator

from app.ui.presenters.feedback.feedback_builder import FeedbackBuilder


class FeedbackNode:

    def __init__(self):
        self._builder = FeedbackBuilder()
        self._scorer = ScoreCalculator()

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        if question is None:
            return state

        result = state.get_result_for_question(question.id)
        if not result:
            return state

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
        # BUILD BUNDLE (FIX)
        # -----------------------------------------------------

        bundle = self._builder.build(
            state=state,
            result=result,
            evaluation=evaluation,
            execution=execution,
            quality=quality,  # 🔥 FIX CRITICO
        )

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

        return state.model_copy(update={"last_feedback_bundle": updated_bundle})
