# app/ui/presenters/feedback/blocks/summary_block.py

from app.contracts.feedback_bundle import FeedbackBlockResult

from domain.contracts.quality import Quality
from domain.contracts.severity import Severity


class SummaryBlock:

    def can_handle(self, _result, _evaluation, execution, _analysis) -> bool:
        return execution is not None

    def build(
        self,
        _state,
        _result,
        _evaluation,
        _execution,
        _analysis,
        quality: Quality,  
    ) -> FeedbackBlockResult:

        # -----------------------------------------------------
        # Map quality → UI label (SINGLE SOURCE OF TRUTH)
        # -----------------------------------------------------

        if quality in (Quality.CORRECT, Quality.OPTIMAL):
            icon = "✅"
            label = "Correct Solution"

        elif quality == Quality.PARTIAL:
            icon = "🟡"
            label = "Partial Solution"

        elif quality == Quality.INCORRECT:
            icon = "❌"
            label = "Incorrect Solution"

        else:
            icon = "❌"
            label = "Incorrect Solution"

        content = f"{icon} {label}"

        return FeedbackBlockResult(
            title="Summary",
            content=content,
            severity=Severity.INFO,
            confidence=0.95,
            signals=[],
            learning=[],
            quality=None,
        )
