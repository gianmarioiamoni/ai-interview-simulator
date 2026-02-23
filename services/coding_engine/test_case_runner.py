# services/coding_engine/test_case_runner.py

# TestCaseRunner
#
# Responsibility:
# Generates a Python test harness for user-submitted code.
# Does not execute code.
# Produces structured output marker for result parsing.

import json
from typing import List

from domain.contracts.coding_test_case import CodingTestCase


class TestCaseRunner:
    RESULT_MARKER = "__RESULT__"

    def build_harness(
        self,
        user_code: str,
        function_name: str,
        test_cases: List[CodingTestCase],
    ) -> str:

        total_tests = len(test_cases)

        harness_lines = []

        harness_lines.append(user_code)
        harness_lines.append("")
        harness_lines.append("def __run_tests():")
        harness_lines.append("    passed = 0")
        harness_lines.append(f"    total = {total_tests}")

        for idx, test in enumerate(test_cases, start=1):
            args_repr = ", ".join([json.dumps(arg) for arg in test.args])

            kwargs_repr = ", ".join(
                [f"{k}={json.dumps(v)}" for k, v in test.kwargs.items()]
            )

            call_signature = ", ".join(
                [part for part in [args_repr, kwargs_repr] if part]
            )

            expected_repr = json.dumps(test.expected)

            harness_lines.append("    try:")
            harness_lines.append(f"        result = {function_name}({call_signature})")
            harness_lines.append(f"        assert result == {expected_repr}")
            harness_lines.append("        passed += 1")
            harness_lines.append("    except Exception as e:")
            harness_lines.append(f'        print("TEST_FAILED:{idx}", str(e))')

        harness_lines.append(
            f'    print("{self.RESULT_MARKER}:" + str(passed) + ":" + str(total))'
        )
        harness_lines.append("")
        harness_lines.append("__run_tests()")

        return "\n".join(harness_lines)
