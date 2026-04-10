# services/coding_engine/harness/blocks/signature_validation_block.py

from typing import List, Optional
from .base_block import BaseBlock
from domain.contracts.coding_spec import CodingSpec


class SignatureValidationBlock(BaseBlock):

    def __init__(self, coding_spec: Optional[CodingSpec]):
        self.coding_spec = coding_spec

    def render(self) -> List[str]:

        lines: List[str] = []

        if self.coding_spec and self.coding_spec.parameters:

            lines.extend(
                [
                    "def __validate_signature(fn):",
                    "    sig = inspect.signature(fn)",
                    "    params = list(sig.parameters.keys())",
                    f"    expected = {repr(self.coding_spec.parameters)}",
                    "",
                    "    if len(params) != len(expected):",
                    "        raise RuntimeError(f'Invalid signature. Expected {expected}, got {params}')",
                    "",
                    "    if params != expected:",
                    """        print("__SIGNATURE_WARNING__:" + json.dumps({
            "expected": expected,
            "actual": params
        }))""",
                    "",
                ]
            )

        else:

            lines.extend(
                [
                    "def __validate_signature(fn):",
                    "    return",
                    "",
                ]
            )

        return lines
