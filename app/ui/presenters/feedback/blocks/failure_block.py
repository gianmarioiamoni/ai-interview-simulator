# app/ui/presenters/feedback/blocks/failure_block.py

from domain.contracts.severity import Severity

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class FailureBlock:

    def can_handle(
        self,
        _result,
        _evaluation,
        execution,
        _analysis,
    ) -> bool:

        if not execution:
            return False

        # fallback SQL / generic
        if execution.total_tests and execution.passed_tests < execution.total_tests:
            return True

        return False

    def build(
        self, _state, result, _evaluation, execution, _analysis, _quality
    ) -> FeedbackBlockResult:

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        # -----------------------------------------------------
        # CONTENT (NO DUPLICATION WITH BREAKDOWN)
        # -----------------------------------------------------

        content = (
            "### ❌ Some tests failed\n\n"
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

        # -----------------------------------------------------
        # LEARNING
        # -----------------------------------------------------

        if total > 0 and passed == 0:
            learning = [
                LearningSuggestion(
                    topic="Algorithm correctness",
                    action="Your solution fails all tests — revisit core logic",
                )
            ]
        else:
            learning = [
                LearningSuggestion(
                    topic="Edge cases",
                    action="Focus on edge cases and input variations",
                )
            ]

        return FeedbackBlockResult(
            title="Logic Errors Detected",
            content=content,
            severity=Severity.ERROR,
            confidence=0.9,
            signals=signals,
            learning=learning,
            quality=None,
        )
