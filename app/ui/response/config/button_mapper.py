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
        # QUALITY (SAFE)
        # -----------------------------------------------------

        quality = ButtonMapper._get_quality(state)

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
    # QUALITY
    # =========================================================

    @staticmethod
    def _get_quality(state: InterviewState) -> str:

        if not state or not getattr(state, "last_feedback_bundle", None):
            return "unknown"

        return state.last_feedback_bundle.overall_quality or "unknown"

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

        return quality in ["incorrect", "partial"] and can_retry

    @staticmethod
    def _show_next(
        is_feedback: bool,
        quality: str,
    ) -> bool:

        if not is_feedback:
            return False

        return quality in ["partial", "correct", "optimal", "inefficient"]

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
