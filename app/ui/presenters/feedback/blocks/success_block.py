# app/ui/presenters/feedback/blocks/success_block.py

from app.contracts.feedback_bundle import (
    FeedbackSignal,
    LearningSuggestion,
    FeedbackBlockResult,
)


class SuccessBlock:

    def can_handle(self, _result, _evaluation, execution, _analysis) -> bool:
        return bool(execution and execution.success)

    def build(
        self, 
        _state, 
        _result, 
        _evaluation, 
        execution, 
        _analysis, 
        _quality
    ) -> FeedbackBlockResult:

        exec_time = execution.execution_time_ms or 0

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        if execution.total_tests:
            content = (
                f"## ✅ All tests passed\n\n"
                f"Passed {execution.passed_tests} / {execution.total_tests} tests"
            )
        else:
            content = "## ✅ Execution completed successfully"

        # -----------------------------------------------------
        # Signals
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity="info",
                message="All tests passed successfully",
            )
        ]

        # performance hint (NO quality decision)
        if exec_time and exec_time > 200:
            signals.append(
                FeedbackSignal(
                    severity="warning",
                    message="Performance can be improved",
                )
            )

        # -----------------------------------------------------
        # Learning
        # -----------------------------------------------------

        if exec_time and exec_time < 50:
            learning = [
                LearningSuggestion(
                    topic="Advanced optimization",
                    action="Explore alternative algorithms or data structures",
                )
            ]

        elif exec_time and exec_time < 200:
            learning = [
                LearningSuggestion(
                    topic="Performance tuning",
                    action="Analyze time and space complexity",
                )
            ]

        else:
            learning = [
                LearningSuggestion(
                    topic="Optimization",
                    action="Refactor the solution to improve performance",
                )
            ]

        # -----------------------------------------------------
        # Confidence
        # -----------------------------------------------------

        confidence = 0.95 if execution.success else 0.85

        return FeedbackBlockResult(
            title="Success",
            content=content,
            severity="info",
            confidence=confidence,
            signals=signals,
            learning=learning,
            quality=None,
        )
