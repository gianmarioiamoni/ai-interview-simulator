# app/ui/presenters/feedback/blocks/written_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
    FeedbackQuality,
)

from services.answer_improvement.answer_improver import AnswerImprover


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
        # get answer scoped to current question
        # -----------------------------------------------------

        question = _state.current_question
        question_text = question.prompt if question else ""

        latest_answer = (
            _state.get_latest_answer_for_question(question.id) if question else None
        )

        user_answer = latest_answer.content if latest_answer else ""

        # -----------------------------------------------------
        # AI Improved Answer
        # -----------------------------------------------------

        improved_answer = ""

        try:
            if score < 90 and user_answer:
                improver = AnswerImprover()

                improved_answer = improver.improve(
                    question_text,
                    user_answer,
                    feedback,
                )
        except Exception:
            improved_answer = ""

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
            quality_label = "🔴 Incorrect Answer"
            quality_explanation = "Answer shows significant gaps in understanding."

        elif score < 75:
            quality_level = "partial"
            quality_label = "🟡 Partial Answer"
            quality_explanation = (
                "Answer is partially correct but lacks completeness or precision."
            )

        elif score < 90:
            quality_level = "good"
            quality_label = "🟢 Good Answer"
            quality_explanation = "Answer is correct but could be improved."

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
        # Learning
        # -----------------------------------------------------

        if score < 50:
            learning = [
                LearningSuggestion(
                    topic="Fundamentals",
                    action="Review core concepts",
                )
            ]
        elif score < 75:
            learning = [
                LearningSuggestion(
                    topic="Completeness",
                    action="Add missing details",
                )
            ]
        else:
            learning = [
                LearningSuggestion(
                    topic="Answer quality",
                    action="Add concrete examples",
                )
            ]

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        content_lines = [
            f"## {quality_label}",
            f"Score: {score:.1f}/100",
            "",
            "### Feedback",
            feedback,
        ]

        if improved_answer:
            content_lines.extend(
                [
                    "",
                    "### ✨ Suggested Improved Answer",
                    improved_answer,
                ]
            )

        content = "\n".join(content_lines)

        return FeedbackBlockResult(
            title="Written Answer Evaluation",
            content=content,
            severity=severity,
            confidence=0.9,
            signals=signals,
            learning=learning,
            quality=FeedbackQuality(
                level=quality_level,
                explanation=quality_explanation,
            ),
        )
