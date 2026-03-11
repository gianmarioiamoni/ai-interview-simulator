# services/coding_engine/test_case_runner.py

import json
from typing import List

from domain.contracts.test_case import TestCase


class TestCaseRunner:

    RESULT_MARKER = "__RESULT__"

    def build_harness(
        self,
        user_code: str,
        test_cases: List[TestCase],
    ) -> str:

        total_tests = len(test_cases)

        lines: List[str] = []

        # ---------------------------------------------------------
        # User code
        # ---------------------------------------------------------

        lines.append(user_code)
        lines.append("")
        lines.append("import inspect")

        # ---------------------------------------------------------
        # Detect candidate function
        # ---------------------------------------------------------

        lines.append("def __get_function():")
        lines.append("    funcs = []")
        lines.append("    for name, obj in globals().items():")
        lines.append(
            "        if inspect.isfunction(obj) and not name.startswith('__'):"
        )
        lines.append("            funcs.append(obj)")
        lines.append("    if not funcs:")
        lines.append("        raise RuntimeError('No callable function found')")
        lines.append("    return funcs[0]")
        lines.append("")

        # ---------------------------------------------------------
        # Test runner
        # ---------------------------------------------------------

        lines.append("def __run_tests():")
        lines.append("    passed = 0")
        lines.append(f"    total = {total_tests}")
        lines.append("    func = __get_function()")

        for idx, test in enumerate(test_cases, start=1):

            input_repr = repr(test.input)
            expected_repr = repr(test.expected_output)

            lines.append("    try:")

            lines.append(f"        data = {input_repr}")
            lines.append(f"        expected = {expected_repr}")

            lines.append("        if isinstance(data, (list, tuple)):")
            lines.append("            result = func(*data)")
            lines.append("        else:")
            lines.append("            result = func(data)")

            lines.append("        if result != expected:")
            lines.append(
                f'            print("TEST_FAILED:{idx}: expected=" + str(expected) + " actual=" + str(result) + " input=" + str(data))'
            )
            lines.append("        else:")
            lines.append("            passed += 1")

            lines.append("    except Exception as e:")
            lines.append(
                f'        print("TEST_FAILED:{idx}: exception=" + str(e) + " input=" + str(data))'
            )

        # ---------------------------------------------------------
        # Result marker (parsed by CodingExecutor)
        # ---------------------------------------------------------

        lines.append(
            f'    print("{self.RESULT_MARKER}:" + str(passed) + ":" + str(total))'
        )

        lines.append("")
        lines.append("__run_tests()")

        return "\n".join(lines)
