# services/coding_engine/harness/strategies/legacy_strategy.py

from .base_strategy import ResolverStrategy


class LegacyResolverStrategy(ResolverStrategy):

    def __init__(self, function_name: str):
        self.function_name = function_name

    def template_name(self) -> str:
        return "resolver_legacy.j2"

    def context(self) -> dict:
        return {
            "function_name": self.function_name,
        }
