# app/ui/presenters/feedback/blocks/failure_block.py

from domain.contracts.test_execution_result import TestStatus
from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class FailureBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:

        if not execution:
            return False

        # -----------------------------------------------------
        # CASE 1: execution without test_results (SQL fallback)
        # -----------------------------------------------------

        if execution.total_tests and execution.passed_tests < execution.total_tests:
            return True

        # -----------------------------------------------------
        # CASE 2: detailed test results (coding)
        # -----------------------------------------------------

        if execution.test_results:
            return any(
                t.status != TestStatus.PASSED and t.status != TestStatus.ERROR
                for t in execution.test_results
            )

        return False

    def build(
        self, state, result, evaluation, execution, analysis
    ) -> FeedbackBlockResult:

        ai_hint = result.ai_hint if result else None

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        # -----------------------------------------------------
        # FAILED TEST DETAILS (if available)
        # -----------------------------------------------------

        failed_str = ""

        if execution.test_results:

            failed = [
                t
                for t in execution.test_results
                if t.status != TestStatus.PASSED and t.status != TestStatus.ERROR
            ]

            if failed:
                failed_str = "\n".join(
                    [
                        f"Input: {t.args} | Expected: {t.expected} | Actual: {t.actual}"
                        for t in failed[:2]
                    ]
                )

                if len(failed) > 2:
                    failed_str += (
                        f"\n\n...and {len(failed) - 2} more failing test cases"
                    )

        else:
            # -----------------------------------------------------
            # SQL / GENERIC FALLBACK
            # -----------------------------------------------------

            failed_str = "Query result does not match expected output."

        # -----------------------------------------------------
        # SIGNALS (FIXED: no nonsense)
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity="error",
                message=f"{passed}/{total} tests passed",
            )
        ]

        # -----------------------------------------------------
        # LEARNING (UPGRADED)
        # -----------------------------------------------------

        if total > 0 and passed == 0:
            learning = [
                LearningSuggestion(
                    topic="Query correctness",
                    action="Review filtering, ordering, and constraints (e.g. LIMIT, WHERE)",
                )
            ]
        else:
            learning = [
                LearningSuggestion(
                    topic="Algorithm correctness",
                    action="Analyze failing cases and adjust logic accordingly",
                )
            ]

        # -----------------------------------------------------
        # CONTENT
        # -----------------------------------------------------

        content_lines = [
            "### ❌ Failed Tests",
            "",
            failed_str,
        ]

        # -----------------------------------------------------
        # AI HINT (clean rendering)
        # -----------------------------------------------------

        if ai_hint:
            content_lines.extend(
                [
                    "",
                    "### 🤖 AI Hint",
                    f"**Explanation:** {ai_hint.explanation}",
                    f"**Suggestion:** {ai_hint.suggestion}",
                ]
            )

        content = "\n".join(content_lines)

        return FeedbackBlockResult(
            title="Logic Errors Detected",
            content=content,
            severity="error",
            confidence=0.9,
            signals=signals,
            learning=learning,
            quality=None,  
        )
