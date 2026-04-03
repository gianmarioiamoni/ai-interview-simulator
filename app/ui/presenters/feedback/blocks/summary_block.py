# app/ui/presenters/feedback/blocks/summary_block.py

from app.contracts.feedback_bundle import FeedbackBlockResult


class SummaryBlock:

    def can_handle(self, _result, _evaluation, execution, _analysis) -> bool:
        return execution is not None

    def build(
        self,
        _state,
        _result,
        _evaluation,
        execution,
        _analysis,
        quality: str,  
    ) -> FeedbackBlockResult:

        # -----------------------------------------------------
        # Map quality → UI label (SINGLE SOURCE OF TRUTH)
        # -----------------------------------------------------

        if quality in ["correct", "optimal"]:
            icon = "✅"
            label = "Correct Solution"

        elif quality == "partial":
            icon = "🟡"
            label = "Partial Solution"

        elif quality == "incorrect":
            icon = "❌"
            label = "Incorrect Solution"

        else:
            icon = "❌"
            label = "Incorrect Solution"

        content = f"{icon} {label}"

        return FeedbackBlockResult(
            title="Summary",
            content=content,
            severity="info",
            confidence=0.95,
            signals=[],
            learning=[],
            quality=None,
        )
