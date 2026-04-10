# services/coding_engine/harness/strategies/base_strategy.py

from abc import ABC, abstractmethod


class ResolverStrategy(ABC):

    @abstractmethod
    def template_name(self) -> str:
        pass

    @abstractmethod
    def context(self) -> dict:
        pass
