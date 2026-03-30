# app/graph/nodes/feedback_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.execution_result import ExecutionStatus

from app.contracts.feedback_bundle import (
    FeedbackBundle,
    FeedbackBlockResult,
    FeedbackQuality,
    FeedbackSignal,
    LearningSuggestion,
)


class FeedbackNode:

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        if question is None:
            return state

        result = state.get_result_for_question(question.id)
        if not result:
            return state

        execution = result.execution
        evaluation = result.evaluation

        # =========================================================
        # WRITTEN FLOW (NEW - FIX)
        # =========================================================

        if execution is None and evaluation is not None:

            content = evaluation.feedback or "Evaluation completed."

            # Basic quality inference for written answers
            quality = "correct" if evaluation.score >= 70 else "incorrect"

            block = FeedbackBlockResult(
                title="Result",
                content=content,
                severity="info",
                confidence=1.0,
                signals=[],
                learning=[],
                quality=FeedbackQuality(
                    level=quality,
                    explanation="Evaluation based on written answer.",
                ),
            )

            bundle = FeedbackBundle(
                blocks=[block],
                overall_severity="info",
                overall_confidence=1.0,
                overall_quality=quality,
                markdown=content,
            )

            return state.model_copy(update={"last_feedback_bundle": bundle})

        # =========================================================
        # NO DATA SAFETY
        # =========================================================

        if execution is None:
            return state

        # =========================================================
        # QUALITY
        # =========================================================

        quality = self._compute_quality(execution)

        # =========================================================
        # SIGNALS
        # =========================================================

        signals = self._extract_signals(execution)

        # =========================================================
        # LEARNING
        # =========================================================

        learning = self._extract_learning(execution, quality)

        # =========================================================
        # CONTENT
        # =========================================================

        content = self._build_content(evaluation, execution, signals)

        # =========================================================
        # SEVERITY
        # =========================================================

        severity = "error" if not execution.success else "info"

        # =========================================================
        # BLOCK
        # =========================================================

        block = FeedbackBlockResult(
            title="Result",
            content=content,
            severity=severity,
            confidence=1.0,
            signals=signals,
            learning=learning,
            quality=FeedbackQuality(
                level=quality,
                explanation=self._build_quality_explanation(quality),
            ),
        )

        # =========================================================
        # BUNDLE
        # =========================================================

        bundle = FeedbackBundle(
            blocks=[block],
            overall_severity=severity,
            overall_confidence=1.0,
            overall_quality=quality,
            markdown=content,
        )

        return state.model_copy(update={"last_feedback_bundle": bundle})

    # =========================================================
    # QUALITY
    # =========================================================

    def _compute_quality(self, execution) -> str:

        status = execution.status

        # REAL ERRORS
        if status in (
            ExecutionStatus.RUNTIME_ERROR,
            ExecutionStatus.SYNTAX_ERROR,
            ExecutionStatus.INTERNAL_ERROR,
        ):
            return "incorrect"

        # NO TESTS
        if execution.total_tests == 0:
            return "incorrect"

        # TEST RESULTS
        if execution.passed_tests == 0:
            return "incorrect"

        if execution.passed_tests < execution.total_tests:
            return "partial"

        return "correct"

    # =========================================================
    # SIGNALS
    # =========================================================

    def _extract_signals(self, execution):

        signals = []
        status = execution.status

        if status in (
            ExecutionStatus.RUNTIME_ERROR,
            ExecutionStatus.SYNTAX_ERROR,
            ExecutionStatus.INTERNAL_ERROR,
        ):
            signals.append(
                FeedbackSignal(
                    severity="error",
                    message=execution.error or "Execution error",
                )
            )

        elif execution.total_tests == 0:
            signals.append(
                FeedbackSignal(
                    severity="warning",
                    message="No tests detected in execution",
                )
            )

        elif execution.passed_tests < execution.total_tests:
            signals.append(
                FeedbackSignal(
                    severity="warning",
                    message=f"{execution.passed_tests}/{execution.total_tests} tests passed",
                )
            )

        return signals

    # =========================================================
    # LEARNING
    # =========================================================

    def _extract_learning(self, execution, quality):

        suggestions = []
        status = execution.status

        if status in (
            ExecutionStatus.RUNTIME_ERROR,
            ExecutionStatus.SYNTAX_ERROR,
        ):
            suggestions.append(
                LearningSuggestion(
                    topic="Debugging",
                    action="Fix runtime or syntax errors before addressing logic",
                )
            )

        elif quality == "partial":
            suggestions.append(
                LearningSuggestion(
                    topic="Edge cases",
                    action="Review failing test cases and handle edge conditions",
                )
            )

        elif quality == "incorrect":
            suggestions.append(
                LearningSuggestion(
                    topic="Problem understanding",
                    action="Revisit problem requirements and expected behavior",
                )
            )

        return suggestions

    # =========================================================
    # CONTENT
    # =========================================================

    def _build_content(self, evaluation, execution, signals):

        if evaluation and evaluation.feedback:
            return evaluation.feedback

        if execution.error:
            return execution.error

        if signals:
            return signals[0].message

        return "Execution evaluated"

    # =========================================================
    # QUALITY EXPLANATION
    # =========================================================

    def _build_quality_explanation(self, quality: str) -> str:

        if quality == "correct":
            return "All tests passed successfully."

        if quality == "partial":
            return "Some tests failed. Improvements needed."

        if quality == "incorrect":
            return "Solution is incorrect or failed to execute."

        return "Evaluation completed."
