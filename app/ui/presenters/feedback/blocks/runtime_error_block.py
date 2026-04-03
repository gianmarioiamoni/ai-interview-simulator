# app/ui/presenters/feedback/blocks/runtime_error_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    LearningSuggestion,
)


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
        self, 
        _state, 
        result, 
        _evaluation, 
        _execution, 
        analysis, 
        _quality
    ) -> FeedbackBlockResult:

        # -----------------------------------------------------
        # Extract clean error
        # -----------------------------------------------------

        clean_error = analysis.primary_error.strip().splitlines()[-1]

        # -----------------------------------------------------
        # AI Hint (if available)
        # -----------------------------------------------------

        ai_hint = result.ai_hint if result and result.ai_hint else None

        # -----------------------------------------------------
        # Signals
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity="error",
                message=clean_error,
            )
        ]

        # -----------------------------------------------------
        # Learning suggestions
        # -----------------------------------------------------

        learning = [
            LearningSuggestion(
                topic="Debugging runtime errors",
                action="Check variable definitions, imports, and variable scope",
            )
        ]

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        lines = [
            f"`{clean_error}`",
            "",
        ]

        if "Counter" in clean_error:
            lines.extend(
                [
                    "",
                    "💡 Suggested fix:",
                    "`from collections import Counter`",
                ]
            )

        # AI Hint
        if ai_hint:
            lines.extend(
                [
                    "### 🤖 AI Hint",
                    f"**Explanation:** {ai_hint.explanation}",
                    f"**Suggestion:** {ai_hint.suggestion}",
                ]
            )
        else:
            # fallback smart hint
            lines.extend(
                [
                    "### 💡 Quick Hint",
                    "Check imports and variable definitions.",
                ]
            )

        content = "\n".join(lines)

        # -----------------------------------------------------
        # Return block
        # -----------------------------------------------------

        return FeedbackBlockResult(
            title="⚠️ Runtime Error",
            content=content,
            severity="error",
            confidence=0.95,
            signals=signals,
            learning=learning,
            quality=None,  
        )
