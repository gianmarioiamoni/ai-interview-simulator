# app/ui/presenters/feedback/blocks/test_breakdown/test_case_formatter.py

from domain.contracts.execution.test_execution_result import TestStatus

from .logic_issue_analyzer import LogicIssueAnalyzer
from .llm_explanation_policy import LLMExplanationPolicy
from .utils import safe_repr


class TestCaseFormatter:

    def __init__(self):
        self._logic = LogicIssueAnalyzer()
        self._llm = LLMExplanationPolicy()

    def format(self, idx, test, error_type, llm_used):

        if test.status == TestStatus.ERROR:
            return self._format_runtime(idx, test), False

        return self._format_logic(idx, test, error_type, llm_used)

    # -----------------------------------------------------

    def _format_runtime(self, idx, test):

        return "\n".join(
            [
                f"❌ Case {idx} — Runtime Error",
                f"Input: {test.args}",
                f"Error: {test.error}",
            ]
        )

    # -----------------------------------------------------

    def _format_logic(self, idx, test, error_type, llm_used):

        expected = test.expected
        actual = test.actual

        insight = self._logic.infer(expected, actual, error_type)

        used_llm = False

        if not insight and self._llm.should_use(expected, actual, error_type, llm_used):
            insight = self._llm.explain(test, expected, actual)
            used_llm = True

        lines = [
            f"❌ Case {idx} — Incorrect Output",
            f"Input: {test.args}",
            f"Expected: {safe_repr(expected)}",
            f"Actual: {safe_repr(actual)}",
        ]

        if insight:
            lines.append(f"💡 Likely issue: {insight}")

        return "\n".join(lines), used_llm
