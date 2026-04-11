# app/ui/presenters/feedback/blocks/summary_block.py

from app.contracts.feedback_bundle import FeedbackBlockResult

from domain.contracts.quality import Quality
from domain.contracts.severity import Severity


class SummaryBlock:

    def can_handle(self, _result, _evaluation, _execution, _analysis) -> bool:
        return True

    def build(
        self,
        _state,
        _result,
        evaluation,
        execution,
        _analysis,
        quality: Quality,
    ) -> FeedbackBlockResult:

        is_coding = execution is not None

        # -----------------------------------------------------
        # Map quality → label
        # -----------------------------------------------------

        if quality in (Quality.CORRECT, Quality.OPTIMAL):
            icon = "✅"
            label = "Correct Solution"

        elif quality == Quality.PARTIAL:
            icon = "🟡"
            label = "Partial Solution"

        else:
            icon = "❌"
            label = "Incorrect Solution"

        # -----------------------------------------------------
        # UX FIX (DIFFERENZIATE CODING VS WRITTEN)
        # -----------------------------------------------------

        if is_coding and quality in (Quality.CORRECT, Quality.OPTIMAL):
            content = f"{icon} {label}\n\nGreat job! All tests passed."
        elif not is_coding and quality in (Quality.CORRECT, Quality.OPTIMAL):
            content = f"{icon} {label}\n\nGreat answer! Well structured and complete."
        else:
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
