# app/ui/presenters/feedback/blocks/summary_block.py

from app.contracts.feedback_bundle import FeedbackBlockResult

from domain.contracts.quality import Quality
from domain.contracts.severity import Severity


class SummaryBlock:

    def can_handle(self, _result, _evaluation, _execution, _analysis) -> bool:
        return True

    def build(
        self,
        state,
        _result,
        _evaluation,
        _execution,
        _analysis,
        quality: Quality,
    ) -> FeedbackBlockResult:

        question = state.current_question

        is_coding = question.is_coding() if question else False
        is_written = question.is_written() if question else False

        # -----------------------------------------------------
        # Quality mapping
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
        # TYPE-AWARE UX (DIFFERENZIATE CODING VS WRITTEN)
        # -----------------------------------------------------

        if quality in (Quality.CORRECT, Quality.OPTIMAL):

            if is_coding:
                content = f"{icon} {label}\n\nGreat job! All tests passed."

            elif is_written:
                content = (
                    f"{icon} {label}\n\nGreat answer! Well structured and complete."
                )

            else:
                content = f"{icon} {label}"

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
