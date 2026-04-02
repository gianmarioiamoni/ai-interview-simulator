# app/domain/policies/decision_policy.py


class DecisionPolicy:

    def decide(
        self,
        *,
        quality: str,
        attempts: int,
        max_attempts: int,
    ) -> str:

        # -----------------------------------------------------
        # CORRECT → always go next
        # -----------------------------------------------------

        if quality in ("correct", "optimal"):
            return "next"

        # -----------------------------------------------------
        # PARTIAL → allow progression
        # -----------------------------------------------------

        if quality == "partial":
            return "next"

        # -----------------------------------------------------
        # INCORRECT → force retry if possible
        # -----------------------------------------------------

        if quality == "incorrect":
            if attempts < max_attempts:
                return "retry"
            return "next"

        # -----------------------------------------------------
        # fallback
        # -----------------------------------------------------

        return "next"
