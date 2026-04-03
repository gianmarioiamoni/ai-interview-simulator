# app/graph/nodes/feedback_node.py

from domain.contracts.interview_state import InterviewState
from app.ui.presenters.feedback.feedback_builder import FeedbackBuilder
from app.contracts.feedback_bundle import FeedbackBundle
from domain.contracts.quality import Quality


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

        print("AI HINT DEBUG:", result.ai_hint)

        execution = result.execution
        evaluation = result.evaluation

        # -----------------------------------------------------
        # 🔥 SINGLE SOURCE OF TRUTH (FIXED)
        # -----------------------------------------------------

        quality = self._compute_quality(
            execution=execution,
            evaluation=evaluation,
        )

        # -----------------------------------------------------
        # BUILD BASE BUNDLE
        # -----------------------------------------------------

        bundle = self._builder.build(
            state=state,
            result=result,
            evaluation=evaluation,
            execution=execution,
            quality=quality,
        )

        # -----------------------------------------------------
        # 🔥 REBUILD BUNDLE WITH CORRECT QUALITY
        # (dataclass → no model_copy)
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
    # QUALITY ENGINE
    # =========================================================

    def _compute_quality(self, execution, evaluation) -> Quality:

        # -----------------------------------------------------
        # WRITTEN QUESTIONS (NO EXECUTION)
        # -----------------------------------------------------

        if execution is None and evaluation is not None:

            score = evaluation.score or 0

            if score >= 90:
                return Quality.OPTIMAL

            if score >= 75:
                return Quality.CORRECT

            if score >= 50:
                return Quality.PARTIAL

            return Quality.INCORRECT

        # -----------------------------------------------------
        # CODING / SQL
        # -----------------------------------------------------

        if not execution:
            return Quality.INCORRECT

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        # edge case (no tests)
        if total == 0:
            return Quality.CORRECT if execution.success else Quality.INCORRECT

        if passed == total:
            return Quality.CORRECT

        if passed > 0:
            return Quality.PARTIAL

        return Quality.INCORRECT
