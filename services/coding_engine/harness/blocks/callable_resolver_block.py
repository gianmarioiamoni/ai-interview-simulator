# services/coding_engine/harness/blocks/callable_resolver_block.py

from typing import List, Optional
from .base_block import BaseBlock
from domain.contracts.coding_spec import CodingSpec


class CallableResolverBlock(BaseBlock):

    def __init__(
        self,
        function_name: str,
        coding_spec: Optional[CodingSpec],
    ):
        self.function_name = function_name
        self.coding_spec = coding_spec

    def render(self) -> List[str]:

        lines: List[str] = []

        # =========================================================
        # WITH CODING SPEC
        # =========================================================

        if self.coding_spec:

            if self.coding_spec.type == "class_method":

                lines.extend(
                    [
                        "def __resolve_callable():",
                        f"    if '{self.coding_spec.entrypoint}' not in globals():",
                        f"        raise RuntimeError('Class {self.coding_spec.entrypoint} not found')",
                        f"    cls = globals()['{self.coding_spec.entrypoint}']",
                        "    instance = cls()",
                        f"    if not hasattr(instance, '{self.coding_spec.method_name}'):",
                        f"        raise RuntimeError('Method {self.coding_spec.method_name} not found')",
                        f"    return getattr(instance, '{self.coding_spec.method_name}')",
                        "",
                    ]
                )

            else:

                lines.extend(
                    [
                        "def __resolve_callable():",
                        f"    if '{self.coding_spec.entrypoint}' not in globals():",
                        f"        raise RuntimeError('Function {self.coding_spec.entrypoint} not found')",
                        f"    return globals()['{self.coding_spec.entrypoint}']",
                        "",
                    ]
                )

        # =========================================================
        # LEGACY MODE
        # =========================================================

        else:

            lines.extend(
                [
                    "def __resolve_callable():",
                    f"    if '{self.function_name}' in globals():",
                    f"        return globals()['{self.function_name}']",
                    "",
                    "    candidates = []",
                    "    for name, obj in globals().items():",
                    "        if inspect.isfunction(obj) and not name.startswith('__'):",
                    "            candidates.append(obj)",
                    "",
                    "    if not candidates:",
                    "        raise RuntimeError('No callable function found')",
                    "",
                    "    if len(candidates) > 1:",
                    "        raise RuntimeError('Multiple callables found. Provide CodingSpec.')",
                    "",
                    "    return candidates[0]",
                    "",
                ]
            )

        return lines
