# services/coding_engine/harness/blocks/test_runner_block.py

from typing import List
from .base_block import BaseBlock
from services.coding_engine.harness.markers import TestMarkers


class TestRunnerBlock(BaseBlock):

    def __init__(self, visible_tests, hidden_tests):
        self.visible_tests = visible_tests
        self.hidden_tests = hidden_tests

    def render(self) -> List[str]:

        total_visible = len(self.visible_tests)
        total_hidden = len(self.hidden_tests)

        lines: List[str] = []

        # =========================================================
        # TEST RUNNER
        # =========================================================

        lines.append("def __run_tests():")

        # ---------------------------------------------------------
        # SAFE GUARD (ENTRY POINT)
        # ---------------------------------------------------------

        lines.append(
            "    if '__entry_point__' not in globals() or __entry_point__ is None:"
        )

        lines.append(
            f"""        print("{TestMarkers.TEST_RESULT}:" + json.dumps({{
            "type": "visible",
            "id": 1,
            "status": "error",
            "error": __entry_error__ if '__entry_error__' in globals() else "Entry point not defined"
        }}))"""
        )

        lines.append(f'        print("{TestMarkers.VISIBLE}:0:{total_visible}")')
        lines.append(f'        print("{TestMarkers.HIDDEN}:0:{total_hidden}")')
        lines.append("        return")
        lines.append("")

        # ---------------------------------------------------------
        # INIT
        # ---------------------------------------------------------

        lines.append("    func = __entry_point__")
        lines.append("")
        lines.append("    visible_passed = 0")
        lines.append("    hidden_passed = 0")
        lines.append("")

        # =========================================================
        # VISIBLE TESTS
        # =========================================================

        for idx, test in enumerate(self.visible_tests, start=1):

            lines.append("    try:")
            lines.append(f"        args = {repr(test.args)}")
            lines.append(f"        kwargs = {repr(test.kwargs)}")
            lines.append(f"        expected = {repr(test.expected)}")
            lines.append("        result = func(*args, **kwargs)")

            lines.append("        if not __compare(result, expected):")

            lines.append(
                f"""            print("{TestMarkers.TEST_RESULT}:" + json.dumps({{
                "type": "visible",
                "id": {idx},
                "status": "failed",
                "expected": expected,
                "actual": result
            }}))"""
            )

            lines.append("        else:")
            lines.append("            visible_passed += 1")

            lines.append(
                f"""            print("{TestMarkers.TEST_RESULT}:" + json.dumps({{
                "type": "visible",
                "id": {idx},
                "status": "passed"
            }}))"""
            )

            lines.append("    except Exception as e:")

            lines.append(
                f"""        print("{TestMarkers.TEST_RESULT}:" + json.dumps({{
                "type": "visible",
                "id": {idx},
                "status": "error",
                "error": str(e)
            }}))"""
            )

        # =========================================================
        # HIDDEN TESTS
        # =========================================================

        for idx, test in enumerate(self.hidden_tests, start=1):

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
        # SUMMARY
        # =========================================================

        lines.append(
            f'    print("{TestMarkers.VISIBLE}:" + str(visible_passed) + ":" + str({total_visible}))'
        )

        lines.append(
            f'    print("{TestMarkers.HIDDEN}:" + str(hidden_passed) + ":" + str({total_hidden}))'
        )

        lines.append(
            f'    print("{TestMarkers.RESULT}:" + str(visible_passed + hidden_passed) + ":" + str({total_visible + total_hidden}))'
        )

        lines.append("")

        return lines
