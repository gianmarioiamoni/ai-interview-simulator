## services/coding_engine/test_case_runner.py

from typing import List

from domain.contracts.test_case import TestCase


class TestCaseRunner:

    RESULT_MARKER = "__RESULT__"
    VISIBLE_MARKER = "__VISIBLE__"
    HIDDEN_MARKER = "__HIDDEN__"

    def build_harness(
        self,
        user_code: str,
        visible_tests: List[TestCase],
        hidden_tests: List[TestCase],
    ) -> str:

        total_visible = len(visible_tests)
        total_hidden = len(hidden_tests)

        lines: List[str] = []

        # ---------------------------------------------------------
        # User code
        # ---------------------------------------------------------

        lines.append(user_code)
        lines.append("")
        lines.append("import inspect")

        # ---------------------------------------------------------
        # Detect candidate callable
        # ---------------------------------------------------------

        lines.append("def __get_callable():")
        lines.append("    candidates = []")
        lines.append("    for name, obj in globals().items():")
        lines.append(
            "        if inspect.isfunction(obj) and not name.startswith('__'):"
        )
        lines.append("            candidates.append(obj)")
        lines.append("    if not candidates:")
        lines.append("        raise RuntimeError('No callable function found')")
        lines.append("    return candidates[0]")
        lines.append("")

        # ---------------------------------------------------------
        # Test runner
        # ---------------------------------------------------------

        lines.append("def __run_tests():")
        lines.append("    func = __get_callable()")

        lines.append("    visible_passed = 0")
        lines.append("    hidden_passed = 0")

        # -------------------------
        # Visible tests
        # -------------------------

        for idx, test in enumerate(visible_tests, start=1):

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
                f'            print("VISIBLE_TEST_FAILED:{idx}: expected=" + str(expected) + " actual=" + str(result) + " input=" + str(data))'
            )
            lines.append("        else:")
            lines.append("            visible_passed += 1")

            lines.append("    except Exception as e:")
            lines.append(
                f'        print("VISIBLE_TEST_FAILED:{idx}: exception=" + str(e) + " input=" + str(data))'
            )

        # -------------------------
        # Hidden tests
        # -------------------------

        for idx, test in enumerate(hidden_tests, start=1):

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
            lines.append("            pass")
            lines.append("        else:")
            lines.append("            hidden_passed += 1")

            lines.append("    except Exception:")
            lines.append("        pass")

        # ---------------------------------------------------------
        # Result markers
        # ---------------------------------------------------------

        lines.append(
            f'    print("{self.VISIBLE_MARKER}:" + str(visible_passed) + ":" + str({total_visible}))'
        )

        lines.append(
            f'    print("{self.HIDDEN_MARKER}:" + str(hidden_passed) + ":" + str({total_hidden}))'
        )

        lines.append(
            f'    print("{self.RESULT_MARKER}:" + str(visible_passed + hidden_passed) + ":" + str({total_visible + total_hidden}))'
        )

        lines.append("")
        lines.append("__run_tests()")

        return "\n".join(lines)
