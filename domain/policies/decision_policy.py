# app/domain/policies/decision_policy.py


class DecisionPolicy:

    def decide(
        self,
        *,
        quality: str,
        attempts: int,
        max_attempts: int,
    ) -> str:

        if quality == "correct":
            return "next"

        if quality in ("partial", "incorrect"):
            if attempts < max_attempts:
                return "retry"
            return "next"

        return "next"
