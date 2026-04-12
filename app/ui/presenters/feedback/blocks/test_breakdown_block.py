# app/ui/presenters/feedback/blocks/test_breakdown_block.py

from domain.contracts.test_execution_result import TestStatus
from domain.contracts.feedback.feedback.severity import Severity
from domain.contracts.feedback.feedback.error_type import ErrorType

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)

from services.explanation.test_case_explanation_service import (
    TestCaseExplanationService,
)


def _safe_repr(value):
    return repr(value)


class TestBreakdownBlock:

    def __init__(self):
        # LLM fallback service (lazy usage)
        self._explanation_service = TestCaseExplanationService()

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

        # LIMIT LLM CALLS
        llm_used = False

        for idx, t in enumerate(failed[:3], start=1):

            case_text, used_llm = self._format_test_case(
                idx,
                t,
                error_type,
                llm_used,
            )

            if used_llm:
                llm_used = True

            lines.append(case_text)

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
        # LEARNING
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
    
    def _is_complex_case(self, expected, actual, test) -> bool:
            # Decide whether LLM is worth calling.
            # Keeps cost low and avoids useless explanations.

        try:
            # -----------------------------------------------------
            # SKIP trivial scalar mismatches
            # -----------------------------------------------------

            if isinstance(expected, (int, float, str, bool)) and isinstance(actual, (int, float, str, bool)):
                return False

            # -----------------------------------------------------
            # SKIP None vs "None" (we handle via heuristic)
            # -----------------------------------------------------

            if expected is None and actual == "None":
                return False

            # -----------------------------------------------------
            # SKIP simple list mismatches
            # -----------------------------------------------------

            if isinstance(expected, list) and isinstance(actual, list):

                # length mismatch → already handled
                if len(expected) != len(actual):
                    return False

                # order mismatch → already handled
                if sorted(expected) == sorted(actual):
                    return False

            # -----------------------------------------------------
            # USE LLM for complex structures
            # -----------------------------------------------------

            if isinstance(expected, (list, dict)) or isinstance(actual, (list, dict)):
                return True

        except Exception:
            return False

        return False
    
    
    def _format_test_case(self, idx, test, error_type, llm_used):

        # -----------------------------------------------------
        # RUNTIME ERROR
        # -----------------------------------------------------

        if test.status == TestStatus.ERROR:

            return (
                "\n".join(
                    [
                        f"❌ Case {idx} — Runtime Error",
                        f"Input: {test.args}",
                        f"Error: {test.error}",
                    ]
                ),
                False,
            )

        # -----------------------------------------------------
        # LOGIC FAILURE
        # -----------------------------------------------------

        expected = test.expected
        actual = test.actual

        insight = self._infer_logic_issue(expected, actual, error_type)

        # LLM FALLBACK (only once, only if needed)
        if (
            not insight 
            and error_type == ErrorType.LOGIC 
            and not llm_used
            and self._is_complex_case(expected, actual, test)
        ):
            insight = self._explain_with_llm(test, expected, actual)
            used_llm = True
        else:
            used_llm = False

        lines = [
            f"❌ Case {idx} — Incorrect Output",
            f"Input: {test.args}",
            f"Expected: {_safe_repr(expected)}",
            f"Actual: {_safe_repr(actual)}",
        ]

        if insight:
            lines.append(f"💡 Likely issue: {insight}")

        return "\n".join(lines), used_llm

    # =========================================================

    def _infer_logic_issue(self, expected, actual, error_type):

        if error_type != ErrorType.LOGIC:
            return None

        try:
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

    def _explain_with_llm(self, test, expected, actual):

        return self._explanation_service.explain(
            input_data=test.args,
            expected=expected,
            actual=actual,
        )

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
