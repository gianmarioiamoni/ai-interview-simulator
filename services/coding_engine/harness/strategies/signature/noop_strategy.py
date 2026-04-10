# services/coding_engine/harness/strategies/signature/noop_strategy.py

from .base_strategy import SignatureValidationStrategy


class NoOpSignatureValidationStrategy(SignatureValidationStrategy):

    def template_name(self) -> str:
        return "signature_validation_noop.j2"

    def context(self) -> dict:
        return {}
