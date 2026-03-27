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
        can_retry: bool,  # backward compatibility
    ) -> ButtonState:

        is_feedback = ui_state == UIState.FEEDBACK
        has_valid_state = bool(state and state.current_question)

        # -----------------------------------------------------
        # QUALITY + ATTEMPT
        # -----------------------------------------------------

        quality = ButtonMapper._get_quality(state)
        attempt = ButtonMapper._get_attempt(state)

        # -----------------------------------------------------
        # VISIBILITY
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

        # -----------------------------------------------------
        # LABELS (🔥 UX IMPROVEMENT)
        # -----------------------------------------------------

        next_label = ButtonMapper._next_label(state, quality)
        retry_label = ButtonMapper._retry_label(quality)

        return {
            "show_submit": show_submit,
            "show_retry": show_retry,
            "show_next": show_next,
            "show_submit_interactive": show_submit,
            "retry_interactive": show_retry,
            "next_label": next_label,
            "retry_label": retry_label,  # 👈 nuovo (se lo vuoi usare in UI)
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
    # ATTEMPT
    # =========================================================

    @staticmethod
    def _get_attempt(state: InterviewState) -> int:

        if not state or not state.current_question:
            return 0

        return state.get_attempt_for_question(state.current_question.id)

    # =========================================================
    # VISIBILITY RULES
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

        return quality in ("incorrect", "partial")

    @staticmethod
    def _show_next(
        is_feedback: bool,
        quality: str,
    ) -> bool:

        if not is_feedback:
            return False

        # puoi andare avanti se non è completamente sbagliato
        return quality != "incorrect"

    # =========================================================
    # LABELS (🔥 UX CORE)
    # =========================================================

    @staticmethod
    def _next_label(state: InterviewState, quality: str) -> str:

        if state.is_completed:
            return "📊 Generate Final Report"

        if quality == "correct":
            return "➡️ Continue"

        if quality == "partial":
            return "➡️ Continue (can improve)"

        if quality == "inefficient":
            return "➡️ Continue (optimize later)"

        return "Next Question"

    @staticmethod
    def _retry_label(quality: str) -> str:

        if quality == "incorrect":
            return "🔁 Try Again"

        if quality == "partial":
            return "🔧 Fix Issues"

        return "Retry"
