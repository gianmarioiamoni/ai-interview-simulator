# app/ui/response/config/button_mapper.py

import re

from domain.contracts.interview_state import InterviewState
from domain.contracts.action_type import ActionType
from domain.contracts.feedback.feedback.quality import Quality

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

        quality = ButtonMapper._get_quality(state)

        # =====================================================
        # QUALITY FLAGS
        # =====================================================

        is_correct = quality.is_at_least(Quality.CORRECT)
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
            show_retry = ActionType.RETRY in actions and can_retry
            show_next = ActionType.NEXT in actions or ActionType.GENERATE_REPORT in actions
        elif is_partial:
            show_retry = can_retry_action
            show_next = can_next_action

        elif is_correct:
            show_next = can_next_action

            # allow retry if not perfect score
            score = ButtonMapper._get_score(state)
            should_allow_retry = score < 100 and can_retry_action

            if should_allow_retry:
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
            next_label = ButtonMapper._next_label(quality)

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

        if not bundle or not bundle.overall_quality:
            raise RuntimeError("No feedback bundle found")

        return bundle.overall_quality

    # =========================================================

    @staticmethod
    def _next_label(quality: Quality) -> str:

        if quality in [Quality.CORRECT, Quality.OPTIMAL]:
            return "➡️ Continue"

        if quality == Quality.PARTIAL:
            return "➡️ Continue (can improve)"

        if quality == Quality.INEFFICIENT:
            return "➡️ Continue (optimize later)"

        return "Next Question"

    @staticmethod
    def _retry_label(quality: Quality) -> str:

        if quality == Quality.INCORRECT:
            return "🔁 Try Again"

        if quality == Quality.PARTIAL:
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
