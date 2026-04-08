# services/coding_engine/test_case_runner.py

from typing import List, Optional
from domain.contracts.coding_test_case import CodingTestCase
from domain.contracts.coding_spec import CodingSpec


class TestCaseRunner:

    RESULT_MARKER = "__RESULT__"
    VISIBLE_MARKER = "__VISIBLE__"
    HIDDEN_MARKER = "__HIDDEN__"
    TEST_RESULT_MARKER = "__TEST_RESULT__"

    def build_harness(
        self,
        user_code: str,
        visible_tests: List[CodingTestCase],
        hidden_tests: List[CodingTestCase],
        function_name: str,
        coding_spec: Optional[CodingSpec],
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
        # IMPORTS
        # =========================================================

        lines.append("import inspect")
        lines.append("import json")
        lines.append("")

        # =========================================================
        # CALLABLE RESOLUTION (DETERMINISTIC)
        # =========================================================

        if coding_spec:

            if coding_spec.type == "class_method":

                lines.append("def __resolve_callable():")
                lines.append(f"    if '{coding_spec.entrypoint}' not in globals():")
                lines.append(
                    f"        raise RuntimeError('Class {coding_spec.entrypoint} not found')"
                )
                lines.append(f"    cls = globals()['{coding_spec.entrypoint}']")
                lines.append("    instance = cls()")
                lines.append(
                    f"    if not hasattr(instance, '{coding_spec.method_name}'):"
                )
                lines.append(
                    f"        raise RuntimeError('Method {coding_spec.method_name} not found')"
                )
                lines.append(
                    f"    return getattr(instance, '{coding_spec.method_name}')"
                )
                lines.append("")

            else:

                lines.append("def __resolve_callable():")
                lines.append(f"    if '{coding_spec.entrypoint}' not in globals():")
                lines.append(
                    f"        raise RuntimeError('Function {coding_spec.entrypoint} not found')"
                )
                lines.append(f"    return globals()['{coding_spec.entrypoint}']")
                lines.append("")

        else:
            # LEGACY
            lines.append("def __resolve_callable():")
            lines.append(f"    if '{function_name}' in globals():")
            lines.append(f"        return globals()['{function_name}']")
            lines.append("")
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
            lines.append("    if len(candidates) > 1:")
            lines.append(
                "        raise RuntimeError('Multiple callables found. Provide CodingSpec.')"
            )
            lines.append("")
            lines.append("    return candidates[0]")
            lines.append("")

        # =========================================================
        # SIGNATURE VALIDATION
        # =========================================================

        if coding_spec and coding_spec.parameters:

            lines.append("def __validate_signature(fn):")
            lines.append("    sig = inspect.signature(fn)")
            lines.append("    params = list(sig.parameters.keys())")
            lines.append(f"    expected = {repr(coding_spec.parameters)}")

            lines.append("    if len(params) != len(expected):")
            lines.append(
                "        raise RuntimeError(f'Invalid signature. Expected {expected}, got {params}')"
            )

            lines.append("    if params != expected:")
            lines.append(
                f"""        print("{self.TEST_RESULT_MARKER}:" + json.dumps({{
                    "type": "visible",
                    "id": 0,
                    "status": "failed",
                    "error": f"Signature warning. Expected {{expected}}, got {{params}}"
                }}))"""
            )
            lines.append("")
        else:

            lines.append("def __entry_point__(*args, **kwargs):")
            lines.append("    func = __resolve_callable()")
            lines.append("    return func(*args, **kwargs)")
            lines.append("")

        # =========================================================
        # COMPARATOR
        # =========================================================

        lines.append("def __compare(a, b):")
        lines.append("    import math")
        lines.append("    if isinstance(a, float) and isinstance(b, float):")
        lines.append("        return math.isclose(a, b, rel_tol=1e-6)")
        lines.append("    return a == b")
        lines.append("")

        # =========================================================
        # TEST RUNNER (UNCHANGED)
        # =========================================================

        lines.append("def __run_tests():")
        lines.append("    func = __entry_point__")
        lines.append("")
        lines.append("    visible_passed = 0")
        lines.append("    hidden_passed = 0")
        lines.append("")

        for idx, test in enumerate(visible_tests, start=1):
            lines.append("    try:")
            lines.append(f"        args = {repr(test.args)}")
            lines.append(f"        kwargs = {repr(test.kwargs)}")
            lines.append(f"        expected = {repr(test.expected)}")
            lines.append("        result = func(*args, **kwargs)")
            lines.append("        if not __compare(result, expected):")
            lines.append(
                f"""            print("{self.TEST_RESULT_MARKER}:" + json.dumps({{"type":"visible","id":{idx},"status":"failed","expected":expected,"actual":result}}))"""
            )
            lines.append("        else:")
            lines.append("            visible_passed += 1")
            lines.append(
                f"""            print("{self.TEST_RESULT_MARKER}:" + json.dumps({{"type":"visible","id":{idx},"status":"passed"}}))"""
            )
            lines.append("    except Exception as e:")
            lines.append(
                f"""        print("{self.TEST_RESULT_MARKER}:" + json.dumps({{"type":"visible","id":{idx},"status":"error","error":str(e)}}))"""
            )

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
