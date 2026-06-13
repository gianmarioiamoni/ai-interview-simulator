# app/ui/presenters/feedback/blocks/failure_block.py

from domain.contracts.feedback.error_type import ErrorType
from domain.contracts.feedback.severity import Severity

from app.contracts.feedback_bundle import (
    FeedbackBlockResult,
    FeedbackSignal,
)
from infrastructure.config.evaluation import FEEDBACK_CONFIDENCE_WRITTEN
from app.ui.presenters.feedback.blocks.failure.failure_title_selector import (
    FailureTitleSelector,
)
from app.ui.presenters.feedback.blocks.failure.pass_rate_interpreter import (
    PassRateInterpreter,
)
from app.ui.presenters.feedback.blocks.failure.edge_case_detector import (
    EdgeCaseDetector,
)
from app.ui.presenters.feedback.blocks.failure.learning_suggestion_selector import (
    LearningSuggestionSelector,
)
from app.ui.presenters.feedback.blocks.failure.failure_detail_builder import (
    FailureDetailBuilder,
)


class FailureBlock:

    def __init__(self) -> None:
        self._title_selector = FailureTitleSelector()
        self._pass_rate_interpreter = PassRateInterpreter()
        self._edge_case_detector = EdgeCaseDetector()
        self._suggestion_selector = LearningSuggestionSelector()
        self._detail_builder = FailureDetailBuilder()

    def can_handle(
        self,
        result,
        _evaluation,
        execution,
        _analysis,
    ) -> bool:

        if not execution:
            return False

        question = getattr(result, "question", None)

        if question and hasattr(question, "is_execution_based"):
            if not question.is_execution_based():
                return False

        if execution.total_tests and execution.passed_tests < execution.total_tests:
            return True

        return False

    def build(
        self, _state, _result, _evaluation, execution, analysis, _quality
    ) -> FeedbackBlockResult:

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0
        pass_rate = (
            (passed / total) if total > 0 else (1.0 if execution.success else 0.0)
        )

        error_type = getattr(analysis, "error_type", ErrorType.UNKNOWN)
        test_results = execution.test_results if execution else None

        title, message = self._title_selector.select(error_type)
        severity_msg = self._pass_rate_interpreter.interpret(pass_rate)
        is_edge_case = self._edge_case_detector.detect(test_results)
        learning = self._suggestion_selector.select(error_type, is_edge_case)
        details = self._detail_builder.build(test_results)

        signals = [
            FeedbackSignal(
                severity=Severity.ERROR,
                message=f"{passed}/{total} tests passed",
            )
        ]

        content = (
            f"### ❌ {message}\n\n"
            f"{severity_msg}\n"
            f"Passed {passed}/{total} tests.\n"
            + details
            + "\n\nReview the failing cases to identify the issue."
        )

        return FeedbackBlockResult(
            title=title,
            content=content,
            severity=Severity.ERROR,
            confidence=FEEDBACK_CONFIDENCE_WRITTEN,
            signals=signals,
            learning=learning,
            quality=None,
        )
