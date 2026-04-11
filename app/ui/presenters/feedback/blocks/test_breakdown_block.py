# app/ui/presenters/feedback/blocks/test_breakdown_block.py

from domain.contracts.test_execution_result import TestStatus
from domain.contracts.severity import Severity
from domain.contracts.error_type import ErrorType

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class TestBreakdownBlock:

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

        if not execution.test_results:
            return False

        return any(t.status != TestStatus.PASSED for t in execution.test_results)

    # =========================================================

    def build(
        self,
        _state,
        _result,
        _evaluation,
        execution,
        analysis,
        _quality,
    ) -> FeedbackBlockResult:

        failed = [t for t in execution.test_results if t.status != TestStatus.PASSED]
        error_type = getattr(analysis, "error_type", ErrorType.UNKNOWN)

        lines = []

        # =====================================================
        # PER-TEST DETAIL (SMART)
        # =====================================================

        for idx, t in enumerate(failed[:3], start=1):

            lines.append(self._format_test_case(idx, t, error_type))

        if len(failed) > 3:
            lines.append(f"\n...and {len(failed) - 3} more failing tests")

        content = "\n\n".join(lines)

        # =====================================================
        # SIGNALS
        # =====================================================

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=f"{len(failed)} failing test cases detected",
            )
        ]

        # =====================================================
        # LEARNING (TYPE-AWARE)
        # =====================================================

        learning = self._build_learning(error_type)

        return FeedbackBlockResult(
            title="Test Breakdown",
            content=content,
            severity=Severity.ERROR,
            confidence=0.95,
            signals=signals,
            learning=learning,
            quality=None,
        )

    # =========================================================
    # HELPERS
    # =========================================================

    def _format_test_case(self, idx, test, error_type):

        # -----------------------------------------------------
        # RUNTIME ERROR CASE
        # -----------------------------------------------------

        if test.status == TestStatus.ERROR:

            return "\n".join(
                [
                    f"❌ Case {idx} — Runtime Error",
                    f"Input: {test.args}",
                    f"Error: {test.error}",
                ]
            )

        # -----------------------------------------------------
        # LOGIC FAILURE CASE
        # -----------------------------------------------------

        expected = test.expected
        actual = test.actual

        insight = self._infer_logic_issue(expected, actual, error_type)

        lines = [
            f"❌ Case {idx} — Incorrect Output",
            f"Input: {test.args}",
            f"Expected: {expected}",
            f"Actual: {actual}",
        ]

        if insight:
            lines.append(f"💡 Likely issue: {insight}")

        return "\n".join(lines)

    # =========================================================

    def _infer_logic_issue(self, expected, actual, error_type):

        if error_type != ErrorType.LOGIC:
            return None

        try:
            # -------------------------------------------------
            # SIMPLE HEURISTICS
            # -------------------------------------------------

            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if actual > expected:
                    return "Result is too large → possible double counting or incorrect aggregation"

                if actual < expected:
                    return "Result is too small → missing elements or incomplete logic"

            if isinstance(expected, list) and isinstance(actual, list):
                if len(actual) != len(expected):
                    return "Output length mismatch → missing or extra elements"

                if sorted(actual) == sorted(expected) and actual != expected:
                    return "Correct elements but wrong order"

        except Exception:
            return None

        return None

    # =========================================================

    def _build_learning(self, error_type):

        if error_type == ErrorType.LOGIC:
            return [
                LearningSuggestion(
                    topic="Algorithm correctness",
                    action="Focus on edge cases and verify output logic step-by-step",
                )
            ]

        if error_type == ErrorType.RUNTIME:
            return [
                LearningSuggestion(
                    topic="Runtime debugging",
                    action="Handle edge inputs and check for None / invalid values",
                )
            ]

        return [
            LearningSuggestion(
                topic="Debugging",
                action="Analyze failing test cases to identify incorrect logic paths",
            )
        ]
