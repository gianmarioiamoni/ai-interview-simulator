# services/coding_engine/harness/harness_builder.py

from typing import List, Optional

from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.execution.coding_spec import CodingSpec

from services.coding_engine.harness.blocks.user_code_block import UserCodeBlock
from services.coding_engine.harness.blocks.imports_block import ImportsBlock
from services.coding_engine.harness.blocks.callable_resolver_block import (
    CallableResolverBlock,
)
from services.coding_engine.harness.blocks.signature_validation_block import (
    SignatureValidationBlock,
)
from services.coding_engine.harness.blocks.entry_point_block import EntryPointBlock
from services.coding_engine.harness.blocks.comparator_block import ComparatorBlock
from services.coding_engine.harness.blocks.test_runner_block import TestRunnerBlock


class HarnessBuilder:

    def build(
        self,
        user_code: str,
        visible_tests: List[CodingTestCase],
        hidden_tests: List[CodingTestCase],
        function_name: str,
        coding_spec: Optional[CodingSpec],
    ) -> str:

        blocks = [
            UserCodeBlock(user_code),
            ImportsBlock(),
            CallableResolverBlock(function_name, coding_spec),
            SignatureValidationBlock(coding_spec),
            EntryPointBlock(),
            ComparatorBlock(),
            TestRunnerBlock(visible_tests, hidden_tests),
        ]

        lines = []

        for block in blocks:
            lines.extend(block.render())

        lines.append("__run_tests()")

        return "\n".join(lines)
