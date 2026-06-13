# services/humanizer/policy/humanizer_policy_engine.py

from app.settings.constants import MAX_FOLLOW_UPS_PER_INTERVIEW
from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from infrastructure.config.evaluation import FOLLOW_UP_SCORE_THRESHOLD


class HumanizerPolicyEngine:

    MAX_FOLLOW_UPS = MAX_FOLLOW_UPS_PER_INTERVIEW

    FOLLOW_UP_THRESHOLD = FOLLOW_UP_SCORE_THRESHOLD

    # =====================================================
    # PUBLIC
    # =====================================================

    def decide(
        self,
        input_data: HumanizerInput,
    ) -> HumanizerDecision:

        # -------------------------------------------------
        # FOLLOW-UP LIMIT
        # -------------------------------------------------

        if input_data.follow_up_count >= self.MAX_FOLLOW_UPS:

            return HumanizerDecision.DIRECT_QUESTION

        # -------------------------------------------------
        # NO CONSECUTIVE FOLLOW-UPS
        # -------------------------------------------------

        if input_data.last_turn_was_follow_up:

            return HumanizerDecision.REMARK_PLUS_QUESTION

        # -------------------------------------------------
        # NO SCORE AVAILABLE
        # -------------------------------------------------

        if input_data.last_answer_score is None:

            return HumanizerDecision.DIRECT_QUESTION

        # -------------------------------------------------
        # GOOD ANSWER
        # -------------------------------------------------

        if input_data.last_answer_score >= self.FOLLOW_UP_THRESHOLD:

            return HumanizerDecision.FOLLOW_UP

        # -------------------------------------------------
        # WEAK ANSWER
        # -------------------------------------------------

        return HumanizerDecision.REMARK_PLUS_QUESTION
