# app/ui/presenters/feedback/blocks/test_breakdown/test_breakdown_block.py

from domain.contracts.execution.test_execution_result import TestStatus
from domain.contracts.feedback.severity import Severity
from domain.contracts.feedback.error_type import ErrorType

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
)

from app.ui.presenters.feedback.blocks.test_breakdown.test_case_formatter import TestCaseFormatter
from app.ui.presenters.feedback.blocks.test_breakdown.learning_builder import LearningBuilder


class TestBreakdownBlock:

    def __init__(self):
        self._formatter = TestCaseFormatter()
        self._learning_builder = LearningBuilder()

    # -----------------------------------------------------

    def can_handle(self, result, _evaluation, execution, _analysis) -> bool:

        if not execution:
            return False

        question = getattr(result, "question", None)

        if question and hasattr(question, "is_execution_based"):
            if not question.is_execution_based():
                return False

        if not execution.test_results:
            return False

        return any(t.status != TestStatus.PASSED for t in execution.test_results)

    # -----------------------------------------------------

    def build(self, _state, _result, _evaluation, execution, analysis, _quality):

        failed = [t for t in execution.test_results if t.status != TestStatus.PASSED]
        error_type = getattr(analysis, "error_type", ErrorType.UNKNOWN)

        lines = []
        llm_used = False

        for idx, t in enumerate(failed[:3], start=1):

            text, used_llm = self._formatter.format(
                idx,
                t,
                error_type,
                llm_used,
            )

            if used_llm:
                llm_used = True

            lines.append(text)

        if len(failed) > 3:
            lines.append(f"\n...and {len(failed) - 3} more failing tests")

        content = "\n\n".join(lines)

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=f"{len(failed)} failing test cases detected",
            )
        ]

        learning = self._learning_builder.build(error_type)

        return FeedbackBlockResult(
            title="Test Breakdown",
            content=content,
            severity=Severity.ERROR,
            confidence=0.95,
            signals=signals,
            learning=learning,
            quality=None,
        )
