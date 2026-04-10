# services/coding_engine/harness/strategies/signature/base_strategy.py

from abc import ABC, abstractmethod


class SignatureValidationStrategy(ABC):

    @abstractmethod
    def template_name(self) -> str:
        pass

    @abstractmethod
    def context(self) -> dict:
        pass
