# app/ui/presenters/feedback/blocks/written_block.py

from app.ui.presenters.feedback.feedback_models import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


class WrittenBlock:

    def can_handle(self, result, evaluation, execution, analysis) -> bool:
        return bool(evaluation and not execution)

    def build(
        self, state, result, evaluation, execution, analysis
    ) -> FeedbackBlockResult:

        score = evaluation.score if evaluation else 0
        feedback = evaluation.feedback if evaluation else ""

        severity = "info"
        if score < 50:
            severity = "error"
        elif score < 75:
            severity = "warning"

        signals = [
            FeedbackSignal(
                severity=severity,
                message=f"Score: {score:.1f}/100",
            )
        ]

        learning = [
            LearningSuggestion(
                topic="Conceptual understanding",
                action="Review the core concepts behind this question",
            )
        ]

        content = "\n".join(
            [
                f"## Score: {score:.1f}/100",
                "",
                "### Feedback",
                feedback,
            ]
        )

        return FeedbackBlockResult(
            title="Written Answer Evaluation",
            content=content,
            severity=severity,
            confidence=0.9,
            signals=signals,
            learning=learning,
        )
