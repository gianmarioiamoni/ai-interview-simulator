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

        show_submit = ButtonMapper._show_submit(is_feedback)
        show_retry = ButtonMapper._show_retry(is_feedback, can_retry, has_valid_state)
        show_next = ButtonMapper._show_next(is_feedback)

        return {
            # -------------------------------------------------
            # Visibility
            # -------------------------------------------------
            "show_submit": show_submit,
            "show_retry": show_retry,
            "show_next": show_next,
            # -------------------------------------------------
            # Interactivity (Gradio-specific)
            # -------------------------------------------------
            "show_submit_interactive": show_submit,
            "retry_interactive": show_retry,
            # -------------------------------------------------
            # Labels
            # -------------------------------------------------
            "next_label": ButtonMapper._next_label(state),
        }

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
    ) -> bool:
        return is_feedback and can_retry and has_valid_state

    @staticmethod
    def _show_next(is_feedback: bool) -> bool:
        return is_feedback

    # =========================================================
    # LABELS
    # =========================================================

    @staticmethod
    def _next_label(state: InterviewState) -> str:
        return "Generate Report" if state.is_last_question else "Next Question"
