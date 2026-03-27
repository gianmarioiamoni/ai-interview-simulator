# app/graph/nodes/feedback_node.py

from domain.contracts.interview_state import InterviewState
from app.contracts.feedback_bundle import (
    FeedbackBundle,
    FeedbackBlockResult,
    FeedbackQuality,
)


class FeedbackNode:

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question

        if question is None:
            return state

        result = state.get_result_for_question(question.id)

        if not result:
            return state

        execution = result.execution
        evaluation = result.evaluation

        if execution is None:
            return state

        # ---------------------------------------------------------
        # QUALITY
        # ---------------------------------------------------------

        quality = self._compute_quality(execution)

        # ---------------------------------------------------------
        # CONTENT
        # ---------------------------------------------------------

        if evaluation and evaluation.feedback:
            content = evaluation.feedback
        elif execution.error:
            content = execution.error
        else:
            content = "Execution evaluated"

        # ---------------------------------------------------------
        # SEVERITY
        # ---------------------------------------------------------

        severity = "error" if not execution.success else "info"

        # ---------------------------------------------------------
        # BLOCK
        # ---------------------------------------------------------

        block = FeedbackBlockResult(
            title="Result",
            content=content,
            severity=severity,
            confidence=1.0,
            signals=[],
            learning=[],
            quality=FeedbackQuality(
                level=quality,
                explanation="auto",
            ),
        )

        # ---------------------------------------------------------
        # BUNDLE
        # ---------------------------------------------------------

        bundle = FeedbackBundle(
            blocks=[block],
            overall_severity=severity,
            overall_confidence=1.0,
            overall_quality=quality,
            markdown=content,
        )

        # ---------------------------------------------------------
        # STATE UPDATE
        # ---------------------------------------------------------

        return state.model_copy(update={"last_feedback_bundle": bundle})

    # ---------------------------------------------------------
    # INTERNAL LOGIC
    # ---------------------------------------------------------

    def _compute_quality(self, execution) -> str:

        # No tests → invalid evaluation
        if execution.total_tests == 0:
            return "incorrect"

        # All passed
        if execution.passed_tests == execution.total_tests:
            return "correct"

        # Partial success
        if execution.passed_tests > 0:
            return "partial"

        # Zero passed
        return "incorrect"
