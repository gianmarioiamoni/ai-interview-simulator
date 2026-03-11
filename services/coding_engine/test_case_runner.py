import json
import inspect
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

        lines = []

        lines.append(user_code)
        lines.append("")
        lines.append("import inspect")

        # detect candidate function
        lines.append("def __get_function():")
        lines.append("    funcs = []")
        lines.append("    for name, obj in globals().items():")
        lines.append(
            "        if inspect.isfunction(obj) and not name.startswith('__'):"
        )
        lines.append("            funcs.append(obj)")
        lines.append("    if not funcs:")
        lines.append("        raise RuntimeError('No function found')")
        lines.append("    return funcs[0]")
        lines.append("")

        lines.append("def __run_tests():")
        lines.append("    passed = 0")
        lines.append(f"    total = {total_tests}")
        lines.append("    func = __get_function()")

        for idx, test in enumerate(test_cases, start=1):

            input_repr = json.dumps(test.input)
            expected_repr = json.dumps(test.expected_output)

            lines.append("    try:")
            lines.append(f"        data = {input_repr}")
            lines.append("        if isinstance(data, list):")
            lines.append("            result = func(*data)")
            lines.append("        elif isinstance(data, tuple):")
            lines.append("            result = func(*data)")
            lines.append("        else:")
            lines.append("            result = func(data)")
            lines.append(f"        assert result == {expected_repr}")
            lines.append("        passed += 1")
            lines.append("    except Exception as e:")
            lines.append(f'        print("TEST_FAILED:{idx}:" + str(e))')

        lines.append(
            f'    print("{self.RESULT_MARKER}:" + str(passed) + ":" + str(total))'
        )

        lines.append("")
        lines.append("__run_tests()")

        return "\n".join(lines)
