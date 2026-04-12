# app/ui/presenters/feedback/blocks/success_block.py

from app.contracts.feedback_bundle import (
    FeedbackSignal,
    LearningSuggestion,
    FeedbackBlockResult,
)
from domain.contracts.feedback.feedback.severity import Severity


class SuccessBlock:

    def can_handle(self, result, _evaluation, execution, _analysis) -> bool:

        question = getattr(result, "question", None)

        return bool(
            execution
            and execution.success
            and question
            and question.is_execution_based()
        )

    def build(
        self, _state, _result, _evaluation, execution, _analysis, _quality
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
                severity=Severity.INFO,
                message="All tests passed successfully",
            )
        ]

        if exec_time and exec_time > 200:
            signals.append(
                FeedbackSignal(
                    severity=Severity.WARNING,
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

        confidence = 0.95 if execution.success else 0.85

        return FeedbackBlockResult(
            title="Success",
            content=content,
            severity=Severity.INFO,
            confidence=confidence,
            signals=signals,
            learning=learning,
            quality=None,
        )
