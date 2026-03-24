# app/ui/presenters/feedback/blocks/success_block.py

from app.contracts.feedback_bundle import (
    FeedbackQuality,
    FeedbackSignal,
    LearningSuggestion,
    FeedbackBlockResult,
)


class SuccessBlock:

    def can_handle(self, _result, _evaluation, execution, _analysis) -> bool:
        return bool(execution and execution.success)

    def build(self, _state, _result, _evaluation, execution, _analysis):

        # -----------------------------------------------------
        # Quality classification (enhanced)
        # -----------------------------------------------------

        exec_time = execution.execution_time_ms or 0

        if execution.total_tests and execution.passed_tests == execution.total_tests:

            # Performance-based classification
            if exec_time and exec_time < 50:
                quality_level = "optimal"
                explanation = "Solution is correct and performs efficiently."

            elif exec_time and exec_time < 200:
                quality_level = "correct"
                explanation = "Solution is correct with acceptable performance."

            else:
                quality_level = "inefficient"
                explanation = "Solution is correct but performance can be improved."

        else:
            quality_level = "partial"
            explanation = "Solution works but may not cover all cases."

        # -----------------------------------------------------
        # Build content
        # -----------------------------------------------------

        if execution.total_tests:
            content = (
                f"## ✅ All tests passed\n\n"
                f"Passed {execution.passed_tests} / {execution.total_tests} tests"
            )
        else:
            content = "## ✅ Execution completed successfully"

        # -----------------------------------------------------
        # Signals (slightly enriched)
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity="info",
                message="All tests passed successfully",
            )
        ]

        if quality_level == "inefficient":
            signals.append(
                FeedbackSignal(
                    severity="warning",
                    message="Performance can be improved",
                )
            )

        # -----------------------------------------------------
        # Learning suggestions (adaptive)
        # -----------------------------------------------------

        if quality_level == "optimal":
            learning = [
                LearningSuggestion(
                    topic="Advanced optimization",
                    action="Explore alternative algorithms or data structures",
                )
            ]

        elif quality_level == "correct":
            learning = [
                LearningSuggestion(
                    topic="Performance tuning",
                    action="Analyze time and space complexity for potential improvements",
                )
            ]

        elif quality_level == "inefficient":
            learning = [
                LearningSuggestion(
                    topic="Algorithm optimization",
                    action="Refactor the solution to reduce time complexity",
                )
            ]

        else:
            learning = [
                LearningSuggestion(
                    topic="Completeness",
                    action="Ensure all edge cases are handled correctly",
                )
            ]

        # -----------------------------------------------------
        # Confidence (slightly nuanced)
        # -----------------------------------------------------

        confidence = 0.95 if quality_level in ["optimal", "correct"] else 0.85

        # -----------------------------------------------------
        # Return
        # -----------------------------------------------------

        return FeedbackBlockResult(
            title="Success",
            content=content,
            severity="info",
            confidence=confidence,
            signals=signals,
            learning=learning,
            quality=FeedbackQuality(
                level=quality_level,
                explanation=explanation,
            ),
        )
