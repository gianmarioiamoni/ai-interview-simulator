# app/ui/presenters/feedback/blocks/fallback_block.py

from domain.contracts.severity import Severity

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class FallbackBlock:

    def can_handle(
        self, 
        _result, 
        evaluation, 
        execution, 
        _analysis, 
    ) -> bool:
    # enter only if there is no other useful block
        return not execution and not evaluation

    def build(
        self, 
        _state, 
        _result, 
        _evaluation, 
        _execution, 
        _analysis, 
        _quality):

        signals = [
            FeedbackSignal(
                severity=Severity.INFO,
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
            severity=Severity.INFO,
            confidence=0.4,
            signals=signals,
            learning=learning,
            quality=None,
        )
