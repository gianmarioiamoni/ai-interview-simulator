# app/ui/presenters/feedback/blocks/test_breakdown_block.py

from domain.contracts.test_execution_result import TestStatus
from domain.contracts.severity import Severity

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

        # TYPE-AWARE
        if question and hasattr(question, "is_execution_based"):
            if not question.is_execution_based():
                return False

        if not execution.test_results:
            return False

        return any(t.status != TestStatus.PASSED for t in execution.test_results)

    def build(
        self,
        _state,
        _result,
        _evaluation,
        execution,
        _analysis,
        _quality,
    ) -> FeedbackBlockResult:

        failed = [t for t in execution.test_results if t.status != TestStatus.PASSED]

        lines = []

        for t in failed[:3]:

            if t.status == TestStatus.ERROR:
                lines.append(f"❌ Input: {t.args}\nError: {t.error}")
            else:
                lines.append(
                    f"❌ Input: {t.args}\nExpected: {t.expected}\nActual: {t.actual}"
                )

        if len(failed) > 3:
            lines.append(f"\n...and {len(failed) - 3} more failing tests")

        content = "\n\n".join(lines)

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=f"{len(failed)} failing test cases detected",
            )
        ]

        learning = [
            LearningSuggestion(
                topic="Test-driven debugging",
                action="Analyze input/output mismatches to identify incorrect logic paths",
            )
        ]

        return FeedbackBlockResult(
            title="Test Breakdown",
            content=content,
            severity=Severity.ERROR,
            confidence=0.95,
            signals=signals,
            learning=learning,
            quality=None,
        )
