# services/coding_engine/harness/blocks/entry_point_block.py

from typing import List
from .base_block import BaseBlock


class EntryPointBlock(BaseBlock):

    def render(self) -> List[str]:

        return [
            "try:",
            "    __resolved_callable = __resolve_callable()",
            "    __validate_signature(__resolved_callable)",
            "",
            "    def __entry_point__(*args, **kwargs):",
            "        return __resolved_callable(*args, **kwargs)",
            "",
            "except Exception as e:",
            "    __entry_point__ = None",
            "    __entry_error__ = str(e)",
            "",
        ]
