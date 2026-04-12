# services/coding_engine/harness/blocks/signature_validation_block.py

from typing import List, Optional

from domain.contracts.execution.coding_spec import CodingSpec

from .base_block import BaseBlock

from services.coding_engine.harness.template_renderer import TemplateRenderer
from services.coding_engine.harness.strategies.signature.validation_strategy_factory import (
    SignatureValidationStrategyFactory,
)


class SignatureValidationBlock(BaseBlock):

    def __init__(self, coding_spec: Optional[CodingSpec]):
        self.coding_spec = coding_spec

        self._renderer = TemplateRenderer("services/coding_engine/harness/templates")

    def render(self) -> List[str]:

        strategy = SignatureValidationStrategyFactory.create(self.coding_spec)

        rendered = self._renderer.render(
            strategy.template_name(),
            strategy.context(),
        )

        return rendered.split("\n") + [""]
