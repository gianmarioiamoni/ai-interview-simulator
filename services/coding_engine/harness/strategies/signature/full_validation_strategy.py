# services/coding_engine/harness/strategies/signature/full_validation_strategy.py

from .base_strategy import SignatureValidationStrategy


class FullSignatureValidationStrategy(SignatureValidationStrategy):

    def __init__(self, parameters):
        self.parameters = parameters

    def template_name(self) -> str:
        return "signature_validation_full.j2"

    def context(self) -> dict:
        return {
            "expected": repr(self.parameters),
        }
