# app/ui/presenters/feedback/blocks/score_block.py

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
)


class ScoreBlock:

    def can_handle(self, _result, _evaluation, execution, _analysis) -> bool:
        return execution is not None and execution.total_tests is not None

    def build(self, _state, _result, _evaluation, execution, _analysis):

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        # -----------------------------------------------------
        # Score computation
        # -----------------------------------------------------

        if total == 0:
            score = 0
        else:
            score = int((passed / total) * 100)

        # -----------------------------------------------------
        # Content
        # -----------------------------------------------------

        content = f"Score: {score}/100\n" f"Tests: {passed}/{total} passed"

        # -----------------------------------------------------
        # Metadata (CRITICAL for ButtonMapper)
        # -----------------------------------------------------

        metadata = {
            "score": score,
            "passed": passed,
            "total": total,
        }

        return FeedbackBlockResult(
            title="Score",
            content=content,
            severity="info",
            confidence=0.95,
            signals=[],  # 🔥 removed noise
            learning=[],
            quality=None,  # 🔥 UI must not decide quality
            metadata=metadata,
        )
