# app/ui/presenters/feedback/blocks/failure_block.py

from domain.contracts.test_execution_result import TestStatus
from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class FailureBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:

        if not execution or not execution.test_results:
            return False

        return any(
            t.status != TestStatus.PASSED and t.status != TestStatus.ERROR
            for t in execution.test_results
        )

    def build(
        self, state, result, evaluation, execution, analysis
    ) -> FeedbackBlockResult:

        failed = [
            t
            for t in execution.test_results
            if t.status != TestStatus.PASSED and t.status != TestStatus.ERROR
        ]

        failed_str = "\n".join(
            [
                f"Input: {t.args} | Expected: {t.expected} | Actual: {t.actual}"
                for t in failed[:2]
            ]
        )

        ai_hint = result.ai_hint if result else None

        # -----------------------------------------------------
        # Signals
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity="error",
                message=f"{len(failed)} test(s) failed",
            )
        ]

        # -----------------------------------------------------
        # Learning
        # -----------------------------------------------------

        learning = [
            LearningSuggestion(
                topic="Algorithm correctness",
                action="Analyze failing cases and adjust logic accordingly",
            )
        ]

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        content_lines = [
            "### ❌ Failed Tests",
            "",
            failed_str,
        ]

        if len(failed) > 2:
            content_lines.append("")
            content_lines.append(f"...and {len(failed) - 2} more failing test cases")

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
