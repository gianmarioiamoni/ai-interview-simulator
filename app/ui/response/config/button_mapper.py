# app/ui/response/config/button_mapper.py

from domain.contracts.interview_state import InterviewState

from app.ui.ui_state import UIState
from app.ui.types.ui_fields import ButtonState


class ButtonMapper:

    @staticmethod
    def map(
        state: InterviewState,
        ui_state: UIState,
        can_retry: bool,
    ) -> ButtonState:

        is_feedback = ui_state == UIState.FEEDBACK
        has_valid_state = bool(state and state.current_question)

        # -----------------------------------------------------
        # Derive quality (temporary heuristic)
        # -----------------------------------------------------

        quality = ButtonMapper._derive_quality(state)

        # -----------------------------------------------------
        # Adaptive rules
        # -----------------------------------------------------

        show_submit = ButtonMapper._show_submit(is_feedback)

        show_retry = ButtonMapper._show_retry(
            is_feedback,
            can_retry,
            has_valid_state,
            quality,
        )

        show_next = ButtonMapper._show_next(
            is_feedback,
            quality,
        )

        return {
            "show_submit": show_submit,
            "show_retry": show_retry,
            "show_next": show_next,
            "show_submit_interactive": show_submit,
            "retry_interactive": show_retry,
            "next_label": ButtonMapper._next_label(state, quality),
        }

    # =========================================================
    # QUALITY (temporary)
    # =========================================================

    @staticmethod
    def _derive_quality(state: InterviewState) -> str:

        if not state.current_question:
            return "unknown"

        result = state.get_result_for_question(state.current_question.id)

        if not result:
            return "unknown"

        execution = result.execution

        if not execution:
            return "unknown"

        # runtime error
        if not execution.success:
            return "incorrect"

        # simple heuristic
        if execution.total_tests and execution.passed_tests == execution.total_tests:

            if execution.execution_time_ms and execution.execution_time_ms > 200:
                return "inefficient"

            return "correct"

        return "partial"

    # =========================================================
    # RULES
    # =========================================================

    @staticmethod
    def _show_submit(is_feedback: bool) -> bool:
        return not is_feedback

    @staticmethod
    def _show_retry(
        is_feedback: bool,
        can_retry: bool,
        has_valid_state: bool,
        quality: str,
    ) -> bool:

        if not is_feedback or not has_valid_state:
            return False

        if quality == "incorrect":
            return can_retry

        if quality == "partial":
            return can_retry

        if quality == "inefficient":
            return can_retry  # optional retry

        return False

    @staticmethod
    def _show_next(
        is_feedback: bool,
        quality: str,
    ) -> bool:

        if not is_feedback:
            return False

        if quality == "incorrect":
            return False

        return True

    # =========================================================
    # LABELS
    # =========================================================

    @staticmethod
    def _next_label(state: InterviewState, quality: str) -> str:

        if state.is_last_question:
            return "Generate Report"

        if quality == "inefficient":
            return "Next (Improve Later)"

        return "Next Question"
