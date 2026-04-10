# services/coding_engine/harness/blocks/callable_resolver_block.py

import os
from typing import List, Optional

from domain.contracts.coding_spec import CodingSpec

from .base_block import BaseBlock

from services.coding_engine.harness.template_renderer import TemplateRenderer
from services.coding_engine.harness.strategies.resolver_strategy_factory import (
    ResolverStrategyFactory,
)

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "../templates")

class CallableResolverBlock(BaseBlock):

    def __init__(
        self,
        function_name: str,
        coding_spec: Optional[CodingSpec],
    ):
        self.function_name = function_name
        self.coding_spec = coding_spec

        self._renderer = TemplateRenderer(TEMPLATES_DIR)

    def render(self) -> List[str]:

        strategy = ResolverStrategyFactory.create(
            self.function_name,
            self.coding_spec,
        )

        rendered = self._renderer.render(
            strategy.template_name(),
            strategy.context(),
        )

        return rendered.split("\n") + [""]
