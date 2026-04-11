# app/ui/presenters/feedback/blocks/hint_block.py

from app.contracts.feedback_bundle import FeedbackBlockResult
from domain.contracts.severity import Severity


class HintBlock:

    def can_handle(self, result, _evaluation, _execution, _analysis):
        return bool(result and result.ai_hint)

    def build(
        self, _state, result, _evaluation, _execution, _analysis, _quality
    ) -> FeedbackBlockResult:

        ai_hint = result.ai_hint

        content = "\n".join(
            [
                "### 🤖 AI Hint",
                f"**Explanation:** {ai_hint.explanation}",
                f"**Suggestion:** {ai_hint.suggestion}",
            ]
        )

        return FeedbackBlockResult(
            title="AI Hint",
            content=content,
            severity=Severity.INFO,
            confidence=0.85,
            signals=[],
            learning=[],
            quality=None,
        )
