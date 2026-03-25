# app/ui/response/config/button_mapper.py

from domain.contracts.interview_state import InterviewState

from app.ui.ui_state import UIState
from app.ui.types.ui_fields import ButtonState


class ButtonMapper:

    MAX_ATTEMPTS = 3

    @staticmethod
    def map(
        state: InterviewState,
        ui_state: UIState,
        can_retry: bool,  # lo lasciamo per backward compatibility
    ) -> ButtonState:

        is_feedback = ui_state == UIState.FEEDBACK
        has_valid_state = bool(state and state.current_question)

        # -----------------------------------------------------
        # QUALITY + ATTEMPT (NEW)
        # -----------------------------------------------------

        quality = ButtonMapper._get_quality(state)
        attempt = ButtonMapper._get_attempt(state)

        # -----------------------------------------------------
        # RULES
        # -----------------------------------------------------

        show_submit = not is_feedback

        show_retry = ButtonMapper._show_retry(
            is_feedback,
            has_valid_state,
            quality,
            attempt,
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

        bundle = getattr(state, "last_feedback_bundle", None)

        if not bundle or not bundle.overall_quality:
            return "unknown"

        return bundle.overall_quality

    # =========================================================
    # ATTEMPT (NEW)
    # =========================================================

    @staticmethod
    def _get_attempt(state: InterviewState) -> int:

        if not state or not state.current_question:
            return 0

        return state.get_attempt_for_question(state.current_question.id)

    # =========================================================
    # RULES
    # =========================================================

    @staticmethod
    def _show_retry(
        is_feedback: bool,
        has_valid_state: bool,
        quality: str,
        attempt: int,
    ) -> bool:

        if not is_feedback or not has_valid_state:
            return False

        if attempt >= ButtonMapper.MAX_ATTEMPTS:
            return False

        if quality == "incorrect":
            return True

        if quality == "partial":
            return True

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
