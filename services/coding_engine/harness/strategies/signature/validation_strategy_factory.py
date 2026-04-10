# services/coding_engine/harness/strategies/signature/validation_strategy_factory.py

from domain.contracts.coding_spec import CodingSpec

from .full_validation_strategy import FullSignatureValidationStrategy
from .noop_strategy import NoOpSignatureValidationStrategy


class SignatureValidationStrategyFactory:

    @staticmethod
    def create(coding_spec: CodingSpec | None):

        if coding_spec and coding_spec.parameters:
            return FullSignatureValidationStrategy(coding_spec.parameters)

        return NoOpSignatureValidationStrategy()
