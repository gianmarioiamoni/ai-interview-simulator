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

        harness_lines = []

        # ---------------------------------------------------------
        # User code
        # ---------------------------------------------------------

        harness_lines.append(user_code)
        harness_lines.append("")
        harness_lines.append("import inspect")
        harness_lines.append("import ast")

        # ---------------------------------------------------------
        # Detect candidate function
        # ---------------------------------------------------------

        harness_lines.append("def __get_candidate_function():")
        harness_lines.append("    funcs = []")
        harness_lines.append("    for name, obj in globals().items():")
        harness_lines.append("        if inspect.isfunction(obj) and not name.startswith('__'):")
        harness_lines.append("            funcs.append(obj)")
        harness_lines.append("    if not funcs:")
        harness_lines.append("        raise RuntimeError('No callable function found')")
        harness_lines.append("    return funcs[0]")
        harness_lines.append("")

        # ---------------------------------------------------------
        # Test runner
        # ---------------------------------------------------------

        harness_lines.append("def __run_tests():")
        harness_lines.append("    passed = 0")
        harness_lines.append(f"    total = {total_tests}")
        harness_lines.append("    func = __get_candidate_function()")

        for idx, test in enumerate(test_cases, start=1):

            input_repr = json.dumps(test.input)
            expected_repr = json.dumps(test.expected_output)

            harness_lines.append("    try:")
            harness_lines.append(f"        parsed = ast.literal_eval({input_repr})")
            harness_lines.append("        if isinstance(parsed, tuple):")
            harness_lines.append("            result = func(*parsed)")
            harness_lines.append("        else:")
            harness_lines.append("            result = func(parsed)")
            harness_lines.append(f"        assert str(result) == {expected_repr}")
            harness_lines.append("        passed += 1")
            harness_lines.append("    except Exception as e:")
            harness_lines.append(f'        print(f"TEST_FAILED:{idx}:{{e}}")')

        # ---------------------------------------------------------
        # Result marker
        # ---------------------------------------------------------

        harness_lines.append(
            f'    print("{self.RESULT_MARKER}:" + str(passed) + ":" + str(total))'
        )

        harness_lines.append("")
        harness_lines.append("__run_tests()")

        return "\n".join(harness_lines)
