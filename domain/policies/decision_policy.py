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
        # CORRECT → always go next
        # -----------------------------------------------------

        if quality in (Quality.CORRECT, Quality.OPTIMAL):
            return "next"

        # -----------------------------------------------------
        # PARTIAL → allow progression
        # -----------------------------------------------------

        if quality == Quality.PARTIAL:
            return "next"

        # -----------------------------------------------------
        # INCORRECT → force retry if possible
        # -----------------------------------------------------

        if quality == Quality.INCORRECT:
            if attempts < max_attempts:
                return "retry"
            return "next"

        # -----------------------------------------------------
        # fallback
        # -----------------------------------------------------

        return "next"
