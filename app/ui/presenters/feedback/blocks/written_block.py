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
        # Quality classification (FIXED + UX LABELS)
        # -----------------------------------------------------

        if score < 50:
            quality_level = "incorrect"
            quality_label = "🔴 Incorrect Answer"
            quality_explanation = "Answer shows significant gaps in understanding."

        elif score < 75:
            quality_level = "partial"
            quality_label = "🟡 Partial Answer"
            quality_explanation = (
                "Answer is partially correct but lacks completeness or precision."
            )

        elif score < 90:
            # 🔥 FIX: non è più "correct" → è "good"
            quality_level = "good"
            quality_label = "🟢 Good Answer"
            quality_explanation = "Answer is correct but could be improved with more concrete examples or clarity."

        else:
            quality_level = "optimal"
            quality_label = "🟢 Strong Answer"
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
        # Learning suggestions (improved)
        # -----------------------------------------------------

        if score < 50:
            learning = [
                LearningSuggestion(
                    topic="Fundamentals",
                    action="Review core concepts and ensure you fully understand the basics",
                )
            ]

        elif score < 75:
            learning = [
                LearningSuggestion(
                    topic="Completeness",
                    action="Add missing details and improve explanation accuracy",
                )
            ]

        else:
            learning = [
                LearningSuggestion(
                    topic="Answer quality",
                    action="Add concrete examples (problem → solution → outcome) to strengthen your answer",
                )
            ]

        # -----------------------------------------------------
        # Actionable improvement (NEW)
        # -----------------------------------------------------

        improvement_section = ""

        if score >= 75 and score < 90:
            improvement_section = "\n".join(
                [
                    "",
                    "### How to Improve",
                    "- Add a concrete real-world example",
                    "- Describe a specific challenge you faced",
                    "- Explain how you solved it and the impact",
                ]
            )

        elif score < 75:
            improvement_section = "\n".join(
                [
                    "",
                    "### How to Improve",
                    "- Clarify your reasoning",
                    "- Cover missing aspects of the question",
                    "- Be more precise in your explanation",
                ]
            )

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        content = "\n".join(
            [
                f"## {quality_label}",
                f"Score: {score:.1f}/100",
                "",
                "### Feedback",
                feedback,
                improvement_section,
            ]
        )

        # -----------------------------------------------------
        # Confidence
        # -----------------------------------------------------

        if score < 50:
            confidence = 0.8
        elif score < 75:
            confidence = 0.85
        else:
            confidence = 0.9

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
