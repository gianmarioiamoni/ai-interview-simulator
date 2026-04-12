# domain/policies/hint_policy.py

from domain.contracts.ai.hint_level import HintLevel
from domain.contracts.feedback.quality import Quality


class HintPolicy:

    def resolve(
        self,
        *,
        quality: Quality,
        attempts: int,
        has_error: bool,
    ) -> HintLevel:

        # -----------------------------------------------------
        # SUCCESS
        # -----------------------------------------------------

        if quality == Quality.CORRECT:
            return HintLevel.NONE

        # -----------------------------------------------------
        # INCORRECT (strong signal)
        # -----------------------------------------------------

        if quality == Quality.INCORRECT:

            if attempts <= 1:
                return HintLevel.TARGETED

            return HintLevel.SOLUTION

        # -----------------------------------------------------
        # PARTIAL (progressive guidance)
        # -----------------------------------------------------

        if quality == Quality.PARTIAL:

            if attempts == 1:
                return HintLevel.BASIC

            if attempts == 2:
                return HintLevel.TARGETED

            return HintLevel.SOLUTION

        # -----------------------------------------------------
        # DEFAULT
        # -----------------------------------------------------

        return HintLevel.NONE
