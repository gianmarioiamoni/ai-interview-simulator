# services/coding_engine/harness/blocks/base_block.py

from typing import List


class BaseBlock:

    def render(self) -> List[str]:
        raise NotImplementedError
