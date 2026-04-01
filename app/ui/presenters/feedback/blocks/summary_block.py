# app/ui/presenters/feedback/blocks/summary_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
    FeedbackQuality,
)


class SummaryBlock:

    def can_handle(self, _result, _evaluation, execution, _analysis) -> bool:
        return execution is not None

    def build(self, _state, _result, _evaluation, execution, _analysis):

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        if total > 0 and passed == total:
            status = "correct"
            icon = "✅"
            label = "Correct Solution"

        elif passed > 0:
            status = "partial"
            icon = "🟡"
            label = "Partial Solution"

        else:
            status = "incorrect"
            icon = "❌"
            label = "Incorrect Solution"

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        content = f"{icon} {label}"

        # -----------------------------------------------------
        # Signals
        # -----------------------------------------------------

        signals = [
            FeedbackSignal(
                severity="info",
                message=label,
            )
        ]

        # -----------------------------------------------------
        # Quality
        # -----------------------------------------------------

        quality = FeedbackQuality(
            level=status,
            explanation=f"Solution classified as {status}.",
        )

        return FeedbackBlockResult(
            title="Summary",
            content=content,
            severity="info",
            confidence=0.95,
            signals=signals,
            learning=[],
            quality=quality,
        )
