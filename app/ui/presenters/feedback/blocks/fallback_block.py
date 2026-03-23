# app/ui/presenters/feedback/blocks/fallback_block.py

from app.ui.presenters.feedback.feedback_models import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class FallbackBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return True  # always last

    def build(
        self, state, result, evaluation, execution, analysis
    ) -> FeedbackBlockResult:

        signals = [
            FeedbackSignal(
                severity="info",
                message="No detailed feedback available",
            )
        ]

        learning = [
            LearningSuggestion(
                topic="General improvement",
                action="Review your solution and consider edge cases",
            )
        ]

        content = "Execution completed. No issues detected but no detailed feedback available."

        return FeedbackBlockResult(
            title="General Feedback",
            content=content,
            severity="info",
            confidence=0.5,
            signals=signals,
            learning=learning,
        )
