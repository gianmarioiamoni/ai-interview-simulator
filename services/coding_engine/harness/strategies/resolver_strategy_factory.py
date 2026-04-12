# services/coding_engine/harness/strategies/resolver_strategy_factory.py

from domain.contracts.execution.coding_spec import CodingSpec

from .function_strategy import FunctionResolverStrategy
from .class_method_strategy import ClassMethodResolverStrategy
from .legacy_strategy import LegacyResolverStrategy


class ResolverStrategyFactory:

    @staticmethod
    def create(function_name: str, coding_spec: CodingSpec | None):

        if coding_spec:

            if coding_spec.type == "class_method":
                return ClassMethodResolverStrategy(
                    coding_spec.entrypoint,
                    coding_spec.method_name,
                )

            return FunctionResolverStrategy(coding_spec.entrypoint)

        return LegacyResolverStrategy(function_name)
