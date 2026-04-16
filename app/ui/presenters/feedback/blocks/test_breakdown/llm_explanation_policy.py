# app/ui/presenters/feedback/blocks/test_breakdown/llm_explanation_policy.py

from domain.contracts.feedback.error_type import ErrorType
from services.explanation.test_case_explanation_service import (
    TestCaseExplanationService,
)


class LLMExplanationPolicy:

    def __init__(self):
        self._service = TestCaseExplanationService()

    def should_use(self, expected, actual, error_type, already_used):

        if already_used:
            return False

        if error_type != ErrorType.LOGIC:
            return False

        if isinstance(expected, (int, float, str, bool)) and isinstance(
            actual, (int, float, str, bool)
        ):
            return False

        if expected is None and actual == "None":
            return False

        if isinstance(expected, list) and isinstance(actual, list):
            if len(expected) != len(actual):
                return False
            if sorted(expected) == sorted(actual):
                return False

        if isinstance(expected, (list, dict)) or isinstance(actual, (list, dict)):
            return True

        return False

    def explain(self, test, expected, actual):
        return self._service.explain(
            input_data=test.args,
            expected=expected,
            actual=actual,
        )
