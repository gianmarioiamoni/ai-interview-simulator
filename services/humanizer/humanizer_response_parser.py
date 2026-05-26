# services/humanizer/humanizer_response_parser.py

import json

from services.humanizer.contracts.humanizer_output import HumanizerOutput


class HumanizerResponseParser:

    # =====================================================
    # PUBLIC
    # =====================================================

    def parse(
        self,
        response: str,
    ) -> HumanizerOutput:

        payload = json.loads(response)

        return HumanizerOutput.model_validate(payload)
