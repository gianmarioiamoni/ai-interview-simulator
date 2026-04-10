# app/ui/presenters/feedback/blocks/written_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)
from services.answer_improvement.answer_improver import AnswerImprover

from domain.contracts.severity import Severity


class WrittenBlock:

    def can_handle(self, _result, evaluation, execution, _analysis) -> bool:
        return bool(evaluation and not execution)

    def build(
        self, 
        _state, 
        _result, 
        evaluation, 
        _execution, 
        _analysis, 
        _quality # injected (unused but required for uniformity)
    ) -> FeedbackBlockResult:

        score = evaluation.score if evaluation else 0
        feedback = evaluation.feedback if evaluation else ""

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
            severity = Severity.ERROR,
            label = "🔴 Incorrect Answer"

        elif score < 75:
            severity = Severity.WARNING,
            label = "🟡 Partial Answer"

        elif score < 90:
            severity = Severity.INFO,
            label = "🟢 Good Answer"

        else:
            severity = Severity.INFO,
            label = "🟢🟢 Strong Answer"

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
            f"## {label}",
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
            quality=None,
        )
