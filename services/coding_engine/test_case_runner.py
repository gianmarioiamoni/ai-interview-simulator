# services/coding_engine/test_case_runner.py

from typing import List, Optional
from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.execution.coding_spec import CodingSpec

from services.coding_engine.harness.harness_builder import HarnessBuilder


class TestCaseRunner:

    def build_harness(
        self,
        user_code: str,
        visible_tests: List[CodingTestCase],
        hidden_tests: List[CodingTestCase],
        function_name: str,
        coding_spec: Optional[CodingSpec],
    ) -> str:

        builder = HarnessBuilder()

        return builder.build(
            user_code=user_code,
            visible_tests=visible_tests,
            hidden_tests=hidden_tests,
            function_name=function_name,
            coding_spec=coding_spec,
        )
