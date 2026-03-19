from typing import List
from domain.contracts.coding_test_case import CodingTestCase


class TestCaseRunner:

    RESULT_MARKER = "__RESULT__"
    VISIBLE_MARKER = "__VISIBLE__"
    HIDDEN_MARKER = "__HIDDEN__"

    def build_harness(
        self,
        user_code: str,
        visible_tests: List[CodingTestCase],
        hidden_tests: List[CodingTestCase],
        function_name: str,
    ) -> str:

        total_visible = len(visible_tests)
        total_hidden = len(hidden_tests)

        lines: List[str] = []

        # =========================================================
        # USER CODE
        # =========================================================

        lines.append(user_code)
        lines.append("")

        # =========================================================
        # FUNCTION RESOLUTION (DYNAMIC MAPPING)
        # =========================================================

        lines.append("import inspect")

        lines.append("def __resolve_callable():")
        lines.append("    # 1. Exact match")
        lines.append(f"    if '{function_name}' in globals():")
        lines.append(f"        return globals()['{function_name}']")
        lines.append("")
        lines.append("    # 2. Fallback: find first valid function")
        lines.append("    candidates = []")
        lines.append("    for name, obj in globals().items():")
        lines.append(
            "        if inspect.isfunction(obj) and not name.startswith('__'):"
        )
        lines.append("            candidates.append(obj)")
        lines.append("")
        lines.append("    if not candidates:")
        lines.append("        raise RuntimeError('No callable function found')")
        lines.append("")
        lines.append("    return candidates[0]")
        lines.append("")

        # =========================================================
        # WRAPPER (ENTRY POINT)
        # =========================================================

        lines.append("def __entry_point__(*args, **kwargs):")
        lines.append("    func = __resolve_callable()")
        lines.append("    return func(*args, **kwargs)")
        lines.append("")

        # =========================================================
        # COMPARATOR
        # =========================================================

        lines.append("def __compare(a, b):")
        lines.append("    import math")
        lines.append("")
        lines.append("    # float tolerance")
        lines.append("    if isinstance(a, float) and isinstance(b, float):")
        lines.append("        return math.isclose(a, b, rel_tol=1e-6)")
        lines.append("")
        lines.append("    return a == b")
        lines.append("")

        # =========================================================
        # TEST RUNNER
        # =========================================================

        lines.append("def __run_tests():")
        lines.append("    func = __entry_point__")
        lines.append("")
        lines.append("    visible_passed = 0")
        lines.append("    hidden_passed = 0")
        lines.append("")

        # ========================
        # VISIBLE TESTS
        # ========================

        for idx, test in enumerate(visible_tests, start=1):

            lines.append("    try:")
            lines.append(f"        args = {repr(test.args)}")
            lines.append(f"        kwargs = {repr(test.kwargs)}")
            lines.append(f"        expected = {repr(test.expected)}")

            lines.append("        result = func(*args, **kwargs)")

            lines.append("        if not __compare(result, expected):")
            lines.append(
                f'            print("VISIBLE_TEST_FAILED:{idx}: expected=" + str(expected) + " actual=" + str(result) + " args=" + str(args) + " kwargs=" + str(kwargs))'
            )
            lines.append("        else:")
            lines.append("            visible_passed += 1")

            lines.append("    except Exception as e:")
            lines.append(
                f'        print("VISIBLE_TEST_FAILED:{idx}: exception=" + str(e) + " args=" + str(args) + " kwargs=" + str(kwargs))'
            )

        # ========================
        # HIDDEN TESTS
        # ========================

        for idx, test in enumerate(hidden_tests, start=1):

            lines.append("    try:")
            lines.append(f"        args = {repr(test.args)}")
            lines.append(f"        kwargs = {repr(test.kwargs)}")
            lines.append(f"        expected = {repr(test.expected)}")

            lines.append("        result = func(*args, **kwargs)")

            lines.append("        if __compare(result, expected):")
            lines.append("            hidden_passed += 1")

            lines.append("    except Exception:")
            lines.append("        pass")

        # =========================================================
        # RESULT MARKERS
        # =========================================================

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
