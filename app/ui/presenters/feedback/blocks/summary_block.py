# app/ui/presenters/feedback/blocks/summary_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
)


class SummaryBlock:

    def can_handle(self, _result, _evaluation, execution, _analysis) -> bool:
        return execution is not None

    def build(self, state, _result, _evaluation, execution, _analysis):

        bundle = getattr(state, "last_feedback_bundle", None)
        quality = bundle.overall_quality if bundle else "unknown"

        # -----------------------------------------------------
        # Map quality → UI label
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
            icon = "ℹ️"
            label = "Evaluation Result"

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        content = f"{icon} {label}"

        # -----------------------------------------------------
        # Signals (NOISE FIX)
        # -----------------------------------------------------

        signals = []  

        return FeedbackBlockResult(
            title="Summary",
            content=content,
            severity="info",
            confidence=0.95,
            signals=signals,
            learning=[],
            quality=None,  
        )
