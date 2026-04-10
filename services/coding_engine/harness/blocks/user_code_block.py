# services/coding_engine/harness/blocks/user_code_block.py

from typing import List
from .base_block import BaseBlock


class UserCodeBlock(BaseBlock):

    def __init__(self, user_code: str):
        self.user_code = user_code

    def render(self) -> List[str]:
        return [self.user_code, ""]
