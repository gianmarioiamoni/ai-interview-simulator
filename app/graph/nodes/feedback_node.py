# app/graph/nodes/feedback_node.py

from domain.contracts.interview_state import InterviewState
from app.ui.presenters.feedback.feedback_builder import FeedbackBuilder


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
        # 🔥 SINGLE SOURCE OF TRUTH FOR QUALITY
        # -----------------------------------------------------

        quality = self._compute_quality(execution)

        # -----------------------------------------------------
        # BUILD UI BLOCKS
        # -----------------------------------------------------

        bundle = self._builder.build(
            state=state,
            result=result,
            evaluation=evaluation,
            execution=execution,
        )

        # -----------------------------------------------------
        # FORCE QUALITY INTO BUNDLE
        # -----------------------------------------------------

        bundle = bundle.model_copy(
            update={
                "overall_quality": quality,
            }
        )

        return state.model_copy(update={"last_feedback_bundle": bundle})

    # =========================================================

    def _compute_quality(self, execution) -> str:

        if not execution:
            return "incorrect"

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        # no tests case
        if total == 0:
            return "correct" if execution.success else "incorrect"

        if passed == total:
            return "correct"

        if passed > 0:
            return "partial"

        return "incorrect"
