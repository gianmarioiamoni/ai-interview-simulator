# app/ui/response/config/button_mapper.py

import re

from domain.contracts.interview_state import InterviewState
from domain.contracts.action_type import ActionType
from domain.contracts.quality import Quality
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
        # QUALITY FLAGS
        # =====================================================

        is_correct = quality in (Quality.CORRECT, Quality.OPTIMAL)
        is_partial = quality == Quality.PARTIAL
        is_incorrect = quality == Quality.INCORRECT

        # =====================================================
        # BASE ACTION FLAGS (from graph)
        # =====================================================

        can_next_action = (
            ActionType.NEXT in actions or ActionType.GENERATE_REPORT in actions
        )

        can_retry_action = ActionType.RETRY in actions and can_retry

        # =====================================================
        # FINAL VISIBILITY
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

            # allow retry if not perfect score
            score = ButtonMapper._get_score(state)

            if score < 100 and can_retry_action:
                show_retry = True

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
    def _get_quality(state: InterviewState) -> Quality:
        bundle = state.last_feedback_bundle

        if not bundle:
            raise RuntimeError("No feedback bundle found")

        return bundle.overall_quality

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

    # =========================================================
    # SCORE EXTRACTION (METADATA FIRST)
    # =========================================================

    @staticmethod
    def _get_score(state: InterviewState) -> float:

        bundle = getattr(state, "last_feedback_bundle", None)

        if not bundle or not bundle.blocks:
            return 0.0

        for b in bundle.blocks:

            if b.title == "Score":

                # structured metadata (preferred)
                if hasattr(b, "metadata") and b.metadata:
                    return float(b.metadata.get("score", 0.0))

                # fallback (backward compatibility)
                match = re.search(r"(\d+)", b.content)
                if match:
                    return float(match.group(1))

        return 0.0
