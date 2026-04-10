# services/coding_engine/harness/blocks/imports_block.py

from typing import List
from .base_block import BaseBlock


class ImportsBlock(BaseBlock):

    def render(self) -> List[str]:
        return [
            "import inspect",
            "import json",
            "",
        ]
