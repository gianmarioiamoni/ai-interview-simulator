# app/graph/nodes/feedback_node.py

from domain.contracts.interview_state import InterviewState
from app.ui.presenters.feedback.feedback_builder import FeedbackBuilder
from app.contracts.feedback_bundle import FeedbackBundle


class FeedbackNode:

    def __init__(self):
        self._builder = FeedbackBuilder()

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
        # SINGLE SOURCE OF TRUTH
        # -----------------------------------------------------

        quality = self._compute_quality(execution)

        # -----------------------------------------------------
        # BUILD BASE BUNDLE
        # -----------------------------------------------------

        bundle = self._builder.build(
            state=state,
            result=result,
            evaluation=evaluation,
            execution=execution,
        )

        # -----------------------------------------------------
        # 🔥 REBUILD BUNDLE WITH CORRECT QUALITY
        # -----------------------------------------------------

        updated_bundle = FeedbackBundle(
            blocks=bundle.blocks,
            overall_severity=bundle.overall_severity,
            overall_confidence=bundle.overall_confidence,
            overall_quality=quality,
            markdown=bundle.markdown,
        )

        return state.model_copy(update={"last_feedback_bundle": updated_bundle})

    # =========================================================

    def _compute_quality(self, execution) -> str:

        if not execution:
            return "incorrect"

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        if total == 0:
            return "correct" if execution.success else "incorrect"

        if passed == total:
            return "correct"

        if passed > 0:
            return "partial"

        return "incorrect"
