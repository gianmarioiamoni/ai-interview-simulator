# app/ui/presenters/feedback/blocks/hint_block.py

from app.contracts.feedback_bundle import FeedbackBlockResult
from domain.contracts.severity import Severity
from domain.contracts.error_type import ErrorType


class HintBlock:

    def can_handle(self, result, _evaluation, _execution, _analysis):
        return bool(result and result.ai_hint)

    def build(
        self, _state, result, _evaluation, _execution, analysis, _quality
    ) -> FeedbackBlockResult:

        ai_hint = result.ai_hint

        error_type = getattr(analysis, "error_type", ErrorType.UNKNOWN)

        # -----------------------------------------------------
        # CONTEXT-AWARE PREFIX
        # -----------------------------------------------------

        if error_type == ErrorType.LOGIC:
            prefix = "💡 Logic Hint"

        elif error_type == ErrorType.RUNTIME:
            prefix = "🛠 Runtime Hint"

        elif error_type == ErrorType.SIGNATURE:
            prefix = "📐 Signature Hint"

        else:
            prefix = "🤖 AI Hint"

        content = "\n".join(
            [
                f"### {prefix}",
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
