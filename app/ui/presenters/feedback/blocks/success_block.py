# app/ui/presenters/feedback/blocks/success_block.py

from app.ui.presenters.feedback.feedback_models import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class SuccessBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return bool(execution and execution.success)

    def build(
        self, state, result, evaluation, execution, analysis
    ) -> FeedbackBlockResult:

        if execution.total_tests:
            content = (
                f"## ✅ All tests passed\n\n"
                f"Passed {execution.passed_tests} / {execution.total_tests} tests"
            )
        else:
            content = "## ✅ Execution completed successfully"

        signals = [
            FeedbackSignal(
                severity="info",
                message="All tests passed successfully",
            )
        ]

        learning = [
            LearningSuggestion(
                topic="Code robustness",
                action="Try adding edge case handling to strengthen your solution",
            )
        ]

        return FeedbackBlockResult(
            title="Success",
            content=content,
            severity="info",
            confidence=0.95,
            signals=signals,
            learning=learning,
        )
