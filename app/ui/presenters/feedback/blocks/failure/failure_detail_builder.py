# app/ui/presenters/feedback/blocks/failure/failure_detail_builder.py

from typing import Any


class FailureDetailBuilder:
    """
    Builds the markdown detail block (example failure, insight, multi-failure
    warning) from the raw test_results list.

    Returns an empty string when no actionable details are available.
    Stateless.
    """

    def build(self, test_results: list[Any] | None) -> str:
        if not test_results:
            return ""

        failed_tests = [t for t in test_results if t.status != "passed"]
        if not failed_tests:
            return ""

        sample = failed_tests[0]
        details = "\n\n---\n\n"

        if len(failed_tests) > 1:
            details += f"⚠️ Multiple failures detected ({len(failed_tests)} cases)\n\n"

        if sample.expected is not None and sample.actual is not None:
            insight = self._insight(sample)
            details += (
                "### 🔍 Example Failure\n"
                f"- Expected: {sample.expected}\n"
                f"- Got: {sample.actual}\n"
            )
            if insight:
                details += f"\n💡 Insight: {insight}\n"

        elif sample.error:
            details += f"### 🔍 Runtime Error\n{sample.error}\n"

        return details

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    @staticmethod
    def _insight(sample: Any) -> str:
        if sample.expected == sample.actual:
            return ""

        if isinstance(sample.expected, (int, float)) and isinstance(
            sample.actual, (int, float)
        ):
            if sample.actual < sample.expected:
                return "Your solution produces smaller results than expected."
            if sample.actual > sample.expected:
                return "Your solution produces larger results than expected."
            return "Mismatch detected."

        return "Output does not match expected structure."
