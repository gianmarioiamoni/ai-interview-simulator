# services/coding_engine/harness/strategies/class_method_strategy.py

from .base_strategy import ResolverStrategy


class ClassMethodResolverStrategy(ResolverStrategy):

    def __init__(self, entrypoint: str, method_name: str):
        self.entrypoint = entrypoint
        self.method_name = method_name

    def template_name(self) -> str:
        return "resolver_class_method.j2"

    def context(self) -> dict:
        return {
            "entrypoint": self.entrypoint,
            "method_name": self.method_name,
        }
