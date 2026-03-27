# domain/policies/hint_policy.py

from domain.contracts.hint_level import HintLevel


class HintPolicy:

    def resolve(
        self,
        *,
        quality: str,
        attempts: int,
        has_error: bool,
    ) -> HintLevel:

        # -----------------------------------------------------
        # SUCCESS
        # -----------------------------------------------------

        if quality == "correct":
            return HintLevel.NONE

        # -----------------------------------------------------
        # INCORRECT (strong signal)
        # -----------------------------------------------------

        if quality == "incorrect":

            if attempts <= 1:
                return HintLevel.TARGETED

            return HintLevel.SOLUTION

        # -----------------------------------------------------
        # PARTIAL (progressive guidance)
        # -----------------------------------------------------

        if quality == "partial":

            if attempts == 1:
                return HintLevel.BASIC

            if attempts == 2:
                return HintLevel.TARGETED

            return HintLevel.SOLUTION

        # -----------------------------------------------------
        # DEFAULT
        # -----------------------------------------------------

        return HintLevel.NONE
