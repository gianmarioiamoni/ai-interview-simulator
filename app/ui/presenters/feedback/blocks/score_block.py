# app/ui/presenters/feedback/blocks/score_block.py

from app.contracts.feedback_bundle import FeedbackBlockResult
from domain.contracts.severity import Severity


class ScoreBlock:

    def can_handle(self, result, _evaluation, execution, _analysis) -> bool:

        if not execution:
            return False

        question = getattr(result, "question", None)

        # TYPE-AWARE
        if question and hasattr(question, "is_execution_based"):
            if not question.is_execution_based():
                return False

        return execution.total_tests is not None

    def build(
        self,
        _state,
        _result,
        _evaluation,
        execution,
        _analysis,
        _quality,
    ):

        if not execution:
            return None

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        if total == 0:
            score = 0
        else:
            score = int((passed / total) * 100)

        content = f"Score: {score}/100\nTests: {passed}/{total} passed"

        metadata = {
            "score": score,
            "passed": passed,
            "total": total,
        }

        return FeedbackBlockResult(
            title="Score",
            content=content,
            severity=Severity.INFO,
            confidence=0.95,
            signals=[],
            learning=[],
            quality=None,
            metadata=metadata,
        )
