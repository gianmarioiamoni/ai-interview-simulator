# services/coding_engine/harness/strategies/function_strategy.py

from .base_strategy import ResolverStrategy


class FunctionResolverStrategy(ResolverStrategy):

    def __init__(self, entrypoint: str):
        self.entrypoint = entrypoint

    def template_name(self) -> str:
        return "resolver_function.j2"

    def context(self) -> dict:
        return {
            "entrypoint": self.entrypoint,
        }