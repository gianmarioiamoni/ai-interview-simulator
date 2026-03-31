# app/ui/response/config/button_mapper.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.action_type import ActionType

from app.ui.ui_state import UIState
from app.ui.types.ui_fields import ButtonState


class ButtonMapper:

    MAX_ATTEMPTS = 3

    @staticmethod
    def map(
        state: InterviewState,
        ui_state: UIState,
        can_retry: bool,  # kept for backward compatibility (not used)
    ) -> ButtonState:

        is_feedback = ui_state == UIState.FEEDBACK
        has_valid_state = bool(state and state.current_question)

        quality = ButtonMapper._get_quality(state)
        actions = state.allowed_actions

        # =====================================================
        # QUESTION STATE (default input phase)
        # =====================================================

        if not is_feedback or not has_valid_state:
            return {
                "show_submit": True,
                "show_retry": False,
                "show_next": False,
                "show_submit_interactive": True,
                "retry_interactive": False,
                "next_label": "",
                "retry_label": "",
            }

        # =====================================================
        # FEEDBACK STATE → DRIVEN BY allowed_actions
        # =====================================================

        show_retry = ActionType.RETRY in actions
        show_next = ActionType.NEXT in actions

        return {
            "show_submit": False,
            "show_retry": show_retry,
            "show_next": show_next,
            "show_submit_interactive": False,
            "retry_interactive": show_retry,
            "next_label": ButtonMapper._next_label(state, quality) if show_next else "",
            "retry_label": ButtonMapper._retry_label(quality) if show_retry else "",
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
    # LABELS (UX)
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
