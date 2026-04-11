# app/ui/presenters/feedback/blocks/runtime_error_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)
from domain.contracts.severity import Severity


class RuntimeErrorBlock:

    def can_handle(
        self,
        result,
        _evaluation,
        _execution,
        analysis,
    ) -> bool:

        if not analysis or not analysis.has_runtime_error:
            return False

        question = getattr(result, "question", None)

        # TYPE-AWARE
        if question and hasattr(question, "is_execution_based"):
            return question.is_execution_based()

        return True

    def build(
        self, _state, result, _evaluation, _execution, analysis, _quality
    ) -> FeedbackBlockResult:

        clean_error = analysis.primary_error.strip().splitlines()[-1]

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=clean_error,
            )
        ]

        learning = [
            LearningSuggestion(
                topic="Debugging runtime errors",
                action="Check variable definitions, imports, and variable scope",
            )
        ]

        lines = [
            f"`{clean_error}`",
            "",
        ]

        if "Counter" in clean_error:
            lines.extend(
                [
                    "",
                    "💡 Suggested fix:",
                    "`from collections import Counter`",
                ]
            )

        content = "\n".join(lines)

        return FeedbackBlockResult(
            title="⚠️ Runtime Error",
            content=content,
            severity=Severity.ERROR,
            confidence=0.95,
            signals=signals,
            learning=learning,
            quality=None,
        )
