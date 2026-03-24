# app/ui/presenters/feedback/blocks/fallback_block.py

from app.ui.presenters.feedback.feedback_models import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
    FeedbackQuality,
)


class FallbackBlock:

    def can_handle(self, _result, _evaluation, _execution, _analysis) -> bool:
        return True  # always last

    def build(self, _state, _result, _evaluation, _execution, _analysis):

        signals = [
            FeedbackSignal(
                severity="info",
                message="Limited feedback available",
            )
        ]

        learning = [
            LearningSuggestion(
                topic="General improvement",
                action="Review your solution and consider edge cases",
            )
        ]

        content = "Execution completed, but no detailed feedback could be generated."

        return FeedbackBlockResult(
            title="General Feedback",
            content=content,
            severity="info",
            confidence=0.4,
            signals=signals,
            learning=learning,
            quality=FeedbackQuality(
                level="partial",
                explanation="System could not fully evaluate the solution.",
            ),
        )
