# app/ui/presenters/feedback/blocks/failure_block.py

from domain.contracts.feedback.severity import Severity
from domain.contracts.feedback.error_type import ErrorType

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class FailureBlock:

    def can_handle(
        self,
        result,
        _evaluation,
        execution,
        _analysis,
    ) -> bool:

        if not execution:
            return False

        question = getattr(result, "question", None)

        if question and hasattr(question, "is_execution_based"):
            if not question.is_execution_based():
                return False

        if execution.total_tests and execution.passed_tests < execution.total_tests:
            return True

        return False

    def build(
        self, _state, _result, _evaluation, execution, analysis, _quality
    ) -> FeedbackBlockResult:

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        error_type = getattr(analysis, "error_type", ErrorType.UNKNOWN)

        # -----------------------------------------------------
        # TYPE-AWARE TITLE + MESSAGE
        # -----------------------------------------------------

        if error_type == ErrorType.LOGIC:
            title = "Logic Errors Detected"
            message = "Your solution produces incorrect results."

            learning = [
                LearningSuggestion(
                    topic="Algorithm correctness",
                    action="Review logic and edge cases — output is incorrect",
                )
            ]

        elif error_type == ErrorType.RUNTIME:
            title = "Runtime Errors in Tests"
            message = "Your code fails during execution for some inputs."

            learning = [
                LearningSuggestion(
                    topic="Runtime debugging",
                    action="Check how your code handles edge inputs and types",
                )
            ]

        else:
            title = "Logic Errors Detected"
            message = "Some tests failed."

            learning = [
                LearningSuggestion(
                    topic="Debugging",
                    action="Analyze failing test cases to identify issues",
                )
            ]

        # -----------------------------------------------------
        # CONTENT
        # -----------------------------------------------------

        content = (
            f"### ❌ {message}\n\n"
            f"Passed {passed}/{total} tests.\n\n"
            "Review the failing cases below."
        )

        # -----------------------------------------------------
        # SIGNALS
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=f"{passed}/{total} tests passed",
            )
        ]

        return FeedbackBlockResult(
            title=title,
            content=content,
            severity=Severity.ERROR,
            confidence=0.9,
            signals=signals,
            learning=learning,
            quality=None,
        )
