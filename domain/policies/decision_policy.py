# app/domain/policies/decision_policy.py

from domain.contracts.quality import Quality


class DecisionPolicy:

    def decide(
        self,
        *,
        quality: Quality,
        attempts: int,
        max_attempts: int,
    ) -> str:

        # -----------------------------------------------------
        # HIGH QUALITY → always go next
        # -----------------------------------------------------

        if quality.is_at_least(Quality.CORRECT):
            return "next"

        # -----------------------------------------------------
        # MEDIUM QUALITY → allow progression
        # -----------------------------------------------------

        if quality == Quality.PARTIAL:
            return "next"

        # -----------------------------------------------------
        # LOW QUALITY → retry if possible
        # -----------------------------------------------------

        if quality == Quality.INCORRECT:
            if attempts < max_attempts:
                return "retry"
            return "next"

        # -----------------------------------------------------
        # fallback (defensive)
        # -----------------------------------------------------

        return "next"
