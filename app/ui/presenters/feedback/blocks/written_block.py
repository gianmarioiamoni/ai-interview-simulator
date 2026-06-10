# app/ui/presenters/feedback/blocks/written_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)
from services.answer_improvement.answer_improver import AnswerImprover
from domain.contracts.feedback.severity import Severity


class WrittenBlock:

    def __init__(self, answer_improver: AnswerImprover):
        self._improver = answer_improver

    def can_handle(self, _result, evaluation, execution, _analysis) -> bool:
        return bool(evaluation and not execution)

    def build(
        self, 
        _state, 
        result, 
        evaluation, 
        _execution, 
        _analysis, 
        _quality # injected (unused but required for uniformity)
    ) -> FeedbackBlockResult:

        score = evaluation.score if evaluation else 0
        feedback = evaluation.feedback if evaluation else ""
        strengths = list(evaluation.strengths) if evaluation else []
        weaknesses = list(evaluation.weaknesses) if evaluation else []

        question = getattr(result, "question", None)
        question_text = question.prompt if question else ""

        latest_answer = (
            _state.get_latest_answer_for_question(question.id) if question else None
        )

        user_answer = latest_answer.content if latest_answer else ""

        # -----------------------------------------------------
        # CONTEXT (role / area)
        # -----------------------------------------------------

        role = getattr(_state, "role", None)
        role_label = (
            (role.custom_name or role.type.value) if role else "unspecified"
        )
        area_label = question.area.value if question else "unspecified"

        # -----------------------------------------------------
        # AI Improved Answer
        # -----------------------------------------------------

        improved_answer = ""

        try:
            if score < 90 and user_answer:
                improved_answer = self._improver.improve(
                    question_text,
                    user_answer,
                    feedback,
                    role=role_label,
                    area=area_label,
                    weaknesses=weaknesses,
                )
        except Exception:
            improved_answer = ""

        # -----------------------------------------------------
        # Severity
        # -----------------------------------------------------

        severity, label = self._map_score_to_feedback(score)

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
        # Learning (weakness-driven when available)
        # -----------------------------------------------------

        if weaknesses:
            learning = [
                LearningSuggestion(
                    topic=area_label,
                    action=f"Address: {weakness}",
                )
                for weakness in weaknesses[:3]
            ]
        elif score < 50:
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

        if strengths:
            content_lines.extend(["", "### ✅ Strengths"])
            content_lines.extend(f"- {s}" for s in strengths)

        if weaknesses:
            content_lines.extend(["", "### ⚠️ Areas to Improve"])
            content_lines.extend(f"- {w}" for w in weaknesses)

        if improved_answer:
            content_lines.extend(
                [
                    "",
                    "### ✨ Suggested Improved Answer",
                    improved_answer,
                ]
            )

        content = "\n".join(content_lines)

        # -----------------------------------------------------
        # Dimension metadata (reused by FeedbackDimensionAggregator)
        # -----------------------------------------------------

        metadata = None
        dimension_signals = dict(getattr(_state, "dimension_signals", {}) or {})

        if dimension_signals:
            top_dimension = max(
                dimension_signals,
                key=dimension_signals.get,
            )
            dim_value = getattr(top_dimension, "value", top_dimension)
            metadata = {"dimension": dim_value}

        return FeedbackBlockResult(
            title="Written Answer Evaluation",
            content=content,
            severity=severity,
            confidence=0.9,
            signals=signals,
            learning=learning,
            quality=None,
            metadata=metadata,
        )

    def _map_score_to_feedback(self, score: float) -> tuple[Severity, str]:
        if score < 50:
            return Severity.ERROR, "🔴 Incorrect Answer"
        elif score < 75:
            return Severity.WARNING, "🟡 Partial Answer"
        else:
            return Severity.INFO, "🟢🟢 Strong Answer"
