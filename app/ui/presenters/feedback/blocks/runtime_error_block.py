# runtime_error_block.py

from app.ui.presenters.feedback.feedback_models import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class RuntimeErrorBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return bool(analysis and analysis.has_runtime_error)

    def build(
        self, state, result, evaluation, execution, analysis
    ) -> FeedbackBlockResult:

        clean_error = analysis.primary_error.strip().splitlines()[-1]

        signals = [
            FeedbackSignal(
                severity="error",
                message=clean_error,
            )
        ]

        learning = [
            LearningSuggestion(
                topic="Debugging runtime errors",
                action="Check variable definitions and imports",
            )
        ]

        return FeedbackBlockResult(
            title="⚠️ Runtime Error",
            content=f"`{clean_error}`",
            severity="error",
            confidence=0.95,
            signals=signals,
            learning=learning,
        )
