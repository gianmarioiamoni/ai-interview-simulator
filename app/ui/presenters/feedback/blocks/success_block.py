# app/ui/presenters/feedback/blocks/success_block.py

from app.ui.presenters.feedback.feedback_models import (
    FeedbackQuality,
    FeedbackSignal,
    LearningSuggestion,
    FeedbackBlockResult,
)

class SuccessBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return bool(execution and execution.success)

    def build(self, state, result, evaluation, execution, analysis):

        # -----------------------------------------------------
        # Quality classification
        # -----------------------------------------------------

        if execution.total_tests and execution.passed_tests == execution.total_tests:
            quality_level = "correct"
            explanation = "All test cases passed successfully."

            # Heuristic semplice (puoi migliorare dopo)
            if execution.execution_time_ms and execution.execution_time_ms < 50:
                quality_level = "optimal"
                explanation = "Solution is correct and performs efficiently."

        else:
            quality_level = "partial"
            explanation = "Solution works but may not cover all cases."

        # -----------------------------------------------------
        # Build
        # -----------------------------------------------------

        content = (
            f"## ✅ All tests passed\n\n"
            f"Passed {execution.passed_tests} / {execution.total_tests} tests"
        )

        return FeedbackBlockResult(
            title="Success",
            content=content,
            severity="info",
            confidence=0.95,
            signals=[
                FeedbackSignal(
                    severity="info",
                    message="All tests passed successfully",
                )
            ],
            learning=[
                LearningSuggestion(
                    topic="Performance",
                    action="Consider time/space complexity improvements",
                )
            ],
            quality=FeedbackQuality(
                level=quality_level,
                explanation=explanation,
            ),
        )
