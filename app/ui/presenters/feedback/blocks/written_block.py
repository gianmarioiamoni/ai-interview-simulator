# app/ui/presenters/feedback/blocks/written_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
    FeedbackQuality,
)


class WrittenBlock:

    def can_handle(self, _result, evaluation, execution, _analysis) -> bool:
        return bool(evaluation and not execution)

    def build(
        self, _state, _result, evaluation, _execution, _analysis
    ) -> FeedbackBlockResult:

        # -----------------------------------------------------
        # Base data
        # -----------------------------------------------------

        score = evaluation.score if evaluation else 0
        feedback = evaluation.feedback if evaluation else ""

        # -----------------------------------------------------
        # Severity
        # -----------------------------------------------------

        if score < 50:
            severity = "error"
        elif score < 75:
            severity = "warning"
        else:
            severity = "info"

        # -----------------------------------------------------
        # Quality classification
        # -----------------------------------------------------

        if score < 50:
            quality_level = "incorrect"
            quality_explanation = "Answer shows significant gaps in understanding."
        elif score < 75:
            quality_level = "partial"
            quality_explanation = (
                "Answer is partially correct but lacks completeness or precision."
            )
        elif score < 90:
            quality_level = "correct"
            quality_explanation = (
                "Answer is correct but could be improved in clarity or depth."
            )
        else:
            quality_level = "optimal"
            quality_explanation = "Answer is clear, complete, and well-structured."

        # -----------------------------------------------------
        # Signals
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity=severity,
                message=f"Score: {score:.1f}/100",
            )
        ]

        # -----------------------------------------------------
        # Learning suggestions (slightly adaptive)
        # -----------------------------------------------------

        if score < 50:
            learning = [
                LearningSuggestion(
                    topic="Fundamentals",
                    action="Review the core concepts and definitions for this topic",
                )
            ]
        elif score < 75:
            learning = [
                LearningSuggestion(
                    topic="Concept refinement",
                    action="Focus on missing details and improve explanation accuracy",
                )
            ]
        else:
            learning = [
                LearningSuggestion(
                    topic="Communication",
                    action="Improve clarity and structure of your explanations",
                )
            ]

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        content = "\n".join(
            [
                f"## Score: {score:.1f}/100",
                "",
                "### Feedback",
                feedback,
            ]
        )

        # -----------------------------------------------------
        # Confidence (simple heuristic)
        # -----------------------------------------------------

        confidence = 0.85 if score < 75 else 0.9

        # -----------------------------------------------------
        # Return
        # -----------------------------------------------------

        return FeedbackBlockResult(
            title="Written Answer Evaluation",
            content=content,
            severity=severity,
            confidence=confidence,
            signals=signals,
            learning=learning,
            quality=FeedbackQuality(
                level=quality_level,
                explanation=quality_explanation,
            ),
        )
