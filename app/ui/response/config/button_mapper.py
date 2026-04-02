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
        can_retry: bool,
    ) -> ButtonState:

        is_feedback = ui_state == UIState.FEEDBACK
        has_valid_state = bool(state and state.current_question)

        quality = ButtonMapper._get_quality(state)
        actions = state.allowed_actions or []

        # =====================================================
        # QUESTION STATE
        # =====================================================

        if not is_feedback or not has_valid_state or not state.last_feedback_bundle:
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
        # QUALITY FLAGS (🔥 NEW CORE LOGIC)
        # =====================================================

        is_correct = quality in ["correct", "optimal"]
        is_partial = quality == "partial"
        is_incorrect = quality == "incorrect"

        # =====================================================
        # BASE ACTION FLAGS (from graph)
        # =====================================================

        can_next_action = (
            ActionType.NEXT in actions or ActionType.GENERATE_REPORT in actions
        )

        can_retry_action = ActionType.RETRY in actions and can_retry

        # =====================================================
        # FINAL VISIBILITY (🔥 FIXED LOGIC)
        # =====================================================

        show_retry = False
        show_next = False

        if is_incorrect:
            show_retry = can_retry_action

        elif is_partial:
            show_retry = can_retry_action
            show_next = can_next_action

        elif is_correct:
            show_next = can_next_action

        else:
            # fallback safe behavior
            show_retry = can_retry_action
            show_next = can_next_action

        # =====================================================
        # LABEL LOGIC
        # =====================================================

        if ActionType.GENERATE_REPORT in actions:
            next_label = "📊 Generate Final Report"

        elif show_next:
            next_label = ButtonMapper._next_label(state, quality)

        else:
            next_label = ""

        retry_label = ButtonMapper._retry_label(quality) if show_retry else ""

        # =====================================================
        # OUTPUT
        # =====================================================

        return {
            "show_submit": False,
            "show_retry": show_retry,
            "show_next": show_next,
            "show_submit_interactive": False,
            "retry_interactive": show_retry,
            "next_label": next_label,
            "retry_label": retry_label,
        }

    # =========================================================

    @staticmethod
    def _get_quality(state: InterviewState) -> str:
        bundle = getattr(state, "last_feedback_bundle", None)
        return (
            bundle.overall_quality if bundle and bundle.overall_quality else "unknown"
        )

    # =========================================================

    @staticmethod
    def _next_label(_state: InterviewState, quality: str) -> str:

        if quality in ["correct", "optimal"]:
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
