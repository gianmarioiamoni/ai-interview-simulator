# app/ui/response/sections/error_hint_builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.test_execution_result import TestStatus, TestType
from domain.contracts.execution_result import ExecutionStatus

from app.ui.dto.question_dto import QuestionDTO
from app.ui.ui_state import UIState


class ErrorHintBuilder:

    @staticmethod
    def build(
        state: InterviewState,
        question: QuestionDTO,
        has_previous_answer: bool,
        ui_state: UIState,
    ) -> str:

        if not ErrorHintBuilder._should_show(
            state,
            question,
            has_previous_answer,
            ui_state,
        ):
            return ""

        result = state.get_result_for_question(question.question_id)

        if not result or not result.execution:
            return ""

        execution = result.execution

        # -----------------------------------------------------
        # Runtime error
        # -----------------------------------------------------

        if execution.status == ExecutionStatus.RUNTIME_ERROR:
            return execution.error or "Runtime error"

        # -----------------------------------------------------
        # Test failure
        # -----------------------------------------------------

        failure = ErrorHintBuilder._extract_failure(execution)

        if not failure:
            return ""

        return ErrorHintBuilder._format_failure(failure)

    # =========================================================
    # POLICY
    # =========================================================

    @staticmethod
    def _should_show(
        state: InterviewState,
        question: QuestionDTO,
        has_previous_answer: bool,
        ui_state: UIState,
    ) -> bool:

        is_feedback = ui_state == UIState.FEEDBACK

        if is_feedback:
            return False

        if not has_previous_answer:
            return False

        result = state.get_result_for_question(question.question_id)

        return bool(result and result.execution)

    # =========================================================
    # FAILURE EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_failure(execution):

        if not execution.test_results:
            return None

        # Prefer visible tests first
        visible_failed = [
            t
            for t in execution.test_results
            if t.type == TestType.VISIBLE and t.status != TestStatus.PASSED
        ]

        if visible_failed:
            return visible_failed[0]

        # Fallback to any failed test
        failed = [t for t in execution.test_results if t.status != TestStatus.PASSED]

        if failed:
            return failed[0]

        return None

    # =========================================================
    # FORMAT
    # =========================================================

    @staticmethod
    def _format_failure(test) -> str:

        if test.status == TestStatus.ERROR:
            return f"Runtime error with input {test.args}"

        return (
            "Failing test:\n"
            f"Input: {test.args}\n"
            f"Expected: {repr(test.expected)}\n"
            f"Actual: {repr(test.actual)}"
        )
