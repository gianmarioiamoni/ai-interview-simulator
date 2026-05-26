# services/humanizer/humanizer_policy_engine.py

from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.contracts.humanizer_input import HumanizerInput


class HumanizerPolicyEngine:

    FOLLOW_UP_THRESHOLD = 5.0

    MAX_FOLLOW_UPS = 2

    # =====================================================
    # PUBLIC
    # =====================================================

    def decide(
        self,
        input_data: HumanizerInput,
    ) -> HumanizerDecision:

        # -------------------------------------------------
        # Missing evaluation
        # -------------------------------------------------

        if input_data.previous_score is None:

            return HumanizerDecision.PLAIN_QUESTION

        # -------------------------------------------------
        # Follow-up limit reached
        # -------------------------------------------------

        if input_data.follow_up_count >= self.MAX_FOLLOW_UPS:

            return HumanizerDecision.REMARK_PLUS_QUESTION

        # -------------------------------------------------
        # Prevent consecutive follow-ups
        # -------------------------------------------------

        if input_data.last_was_follow_up:

            return HumanizerDecision.REMARK_PLUS_QUESTION

        # -------------------------------------------------
        # Strong answer
        # -------------------------------------------------

        if input_data.previous_score >= self.FOLLOW_UP_THRESHOLD:

            return HumanizerDecision.FOLLOW_UP

        # -------------------------------------------------
        # Weak answer
        # -------------------------------------------------

        return HumanizerDecision.REMARK_PLUS_QUESTION
