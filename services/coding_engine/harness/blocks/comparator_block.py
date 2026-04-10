# services/coding_engine/harness/blocks/comparator_block.py

from typing import List
from .base_block import BaseBlock


class ComparatorBlock(BaseBlock):

    def render(self) -> List[str]:
        return [
            "def __compare(a, b):",
            "    import math",
            "    if isinstance(a, float) and isinstance(b, float):",
            "        return math.isclose(a, b, rel_tol=1e-6)",
            "    return a == b",
            "",
        ]
