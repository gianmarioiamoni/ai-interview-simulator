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

        pass_rate = (
            (passed / total) if total > 0 else (1.0 if execution.success else 0.0)
        )

        error_type = getattr(analysis, "error_type", ErrorType.UNKNOWN)

        # -----------------------------------------------------
        # TITLE + MESSAGE
        # -----------------------------------------------------

        if error_type == ErrorType.LOGIC:
            title = "Logic Errors Detected"
            message = "Your solution produces incorrect results."

        elif error_type == ErrorType.RUNTIME:
            title = "Runtime Errors in Tests"
            message = "Your code fails during execution for some inputs."

        else:
            title = "Test Failures Detected"
            message = "Some test cases failed."

        # -----------------------------------------------------
        # PASS RATE INTERPRETATION (NEW)
        # -----------------------------------------------------

        if pass_rate >= 0.8:
            severity_msg = "Minor issues detected."
        elif pass_rate >= 0.5:
            severity_msg = "Partial correctness — several cases failing."
        else:
            severity_msg = "Fundamental issues in solution."

        # -----------------------------------------------------
        # ADVANCED CLASSIFICATION (EDGE CASE DETECTION)
        # -----------------------------------------------------

        is_edge_case = False

        if execution and execution.test_results:
            for t in execution.test_results:
                if (
                    t.status != "passed"
                    and t.expected is not None
                    and t.actual is not None
                ):
                    if t.expected == [] or t.actual == []:
                        is_edge_case = True

                    if isinstance(t.expected, (int, float)) and t.expected in [0, 1]:
                        is_edge_case = True

        # -----------------------------------------------------
        # SMART LEARNING SUGGESTIONS
        # -----------------------------------------------------

        if error_type == ErrorType.LOGIC:

            if is_edge_case:
                learning = [
                    LearningSuggestion(
                        topic="Edge cases",
                        action="Review how your solution handles boundary inputs (empty, single values, zero)",
                    )
                ]
            else:
                learning = [
                    LearningSuggestion(
                        topic="Algorithm correctness",
                        action="Check your core logic and verify intermediate steps",
                    )
                ]

        elif error_type == ErrorType.RUNTIME:

            learning = [
                LearningSuggestion(
                    topic="Runtime debugging",
                    action="Validate input types and ensure safe access to data structures",
                )
            ]

        else:
            learning = [
                LearningSuggestion(
                    topic="Debugging",
                    action="Analyze failing test cases step-by-step",
                )
            ]

        # -----------------------------------------------------
        # BUILD FAILURE DETAILS (ENHANCED)
        # -----------------------------------------------------

        details = ""
        insight = ""

        if execution and execution.test_results:

            failed_tests = [t for t in execution.test_results if t.status != "passed"]

            if failed_tests:
                sample = failed_tests[0]

                details = "\n\n---\n\n"

                # -------------------------------------------------
                # MULTI FAILURE AWARENESS
                # -------------------------------------------------

                if len(failed_tests) > 1:
                    details += (
                        f"⚠️ Multiple failures detected ({len(failed_tests)} cases)\n\n"
                    )

                # -------------------------------------------------
                # FAILURE EXAMPLE + INSIGHT
                # -------------------------------------------------

                if sample.expected is not None and sample.actual is not None:

                    # STEP 3.1 — INTELLIGENT INSIGHT
                    if sample.expected != sample.actual:

                        if isinstance(sample.expected, (int, float)) and isinstance(
                            sample.actual, (int, float)
                        ):

                            if sample.actual < sample.expected:
                                insight = "Your solution produces smaller results than expected."
                            elif sample.actual > sample.expected:
                                insight = "Your solution produces larger results than expected."
                            else:
                                insight = "Mismatch detected."

                        else:
                            insight = "Output does not match expected structure."

                    details += (
                        "### 🔍 Example Failure\n"
                        f"- Expected: {sample.expected}\n"
                        f"- Got: {sample.actual}\n"
                    )

                    if insight:
                        details += f"\n💡 Insight: {insight}\n"

                elif sample.error:
                    details += "### 🔍 Runtime Error\n" f"{sample.error}\n"

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
        # FINAL CONTENT
        # -----------------------------------------------------

        content = (
            f"### ❌ {message}\n\n"
            f"{severity_msg}\n"
            f"Passed {passed}/{total} tests.\n"
            + details
            + "\n\nReview the failing cases to identify the issue."
        )

        return FeedbackBlockResult(
            title=title,
            content=content,
            severity=Severity.ERROR,
            confidence=0.9,
            signals=signals,
            learning=learning,
            quality=None,
        )
