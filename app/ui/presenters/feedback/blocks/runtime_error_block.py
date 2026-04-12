# app/ui/presenters/feedback/blocks/runtime_error_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)
from domain.contracts.feedback.feedback.severity import Severity
from domain.contracts.feedback.feedback.error_type import ErrorType


class RuntimeErrorBlock:

    def can_handle(
        self,
        _result,
        _evaluation,
        _execution,
        analysis,
    ) -> bool:

        return bool(analysis and analysis.has_runtime_error)

    def build(
        self, _state, _result, _evaluation, _execution, analysis, _quality
    ) -> FeedbackBlockResult:

        error = (analysis.primary_error or "").strip().splitlines()[-1]
        error_type = analysis.error_type

        # -----------------------------------------------------
        # TYPE-AWARE MESSAGING
        # -----------------------------------------------------

        if error_type == ErrorType.SYNTAX:
            title = "⚠️ Syntax Error"
            suggestion = "Check syntax (missing colons, parentheses, indentation)"

        elif error_type == ErrorType.SIGNATURE:
            title = "⚠️ Signature Error"
            suggestion = "Ensure function signature matches expected parameters"

        elif error_type == ErrorType.TIMEOUT:
            title = "⚠️ Timeout Error"
            suggestion = "Optimize algorithm (likely O(n²) or worse)"
        elif error_type == ErrorType.RUNTIME:
            title = "⚠️ Runtime Error"
            suggestion = "Check variable definitions, imports, and edge cases"

        else:
            title = "⚠️ Runtime Error"
            suggestion = "Check variable definitions, imports, and variable scope"

        # -----------------------------------------------------
        # SIGNALS
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=error,
            )
        ]

        # -----------------------------------------------------
        # LEARNING
        # -----------------------------------------------------

        learning = [
            LearningSuggestion(
                topic="Debugging",
                action=suggestion,
            )
        ]

        # -----------------------------------------------------
        # CONTENT
        # -----------------------------------------------------

        content = f"`{error}`"

        return FeedbackBlockResult(
            title=title,
            content=content,
            severity=Severity.ERROR,
            confidence=0.95,
            signals=signals,
            learning=learning,
            quality=None,
        )
