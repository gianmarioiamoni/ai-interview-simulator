# services/coding_engine/coding_failure_explainer.py

from typing import Optional, List

from domain.contracts.execution.execution_result import ExecutionResult, ExecutionStatus
from domain.contracts.execution.execution_test_result import TestExecutionResult


class CodingFailureExplainer:
    """
    Derives a concise, interview-style explanation of why a solution failed.
    Uses available execution signals: error message, failed test cases,
    hidden failure sample. No LLM call — deterministic and fast.
    """

    def explain(self, execution: ExecutionResult) -> str:

        if execution.success:
            return "All tests passed."

        # --- Runtime / Syntax / Timeout ---
        if execution.status == ExecutionStatus.SYNTAX_ERROR:
            return self._explain_syntax(execution.error)

        if execution.status == ExecutionStatus.TIMEOUT:
            return "Your solution exceeded the time limit — likely due to an inefficient algorithm or infinite loop."

        if execution.status == ExecutionStatus.RUNTIME_ERROR:
            return self._explain_runtime(execution.error)

        # --- Logic failures (FAILED_TESTS) ---
        failed = [t for t in execution.test_results if t.status != "passed"]

        if failed:
            return self._explain_logic(failed, execution.hidden_failure_sample)

        # --- Visible tests all passed but hidden failed ---
        if execution.hidden_failure_sample:
            return self._explain_hidden(execution.hidden_failure_sample)

        return "Your solution failed. Review failing cases to identify the issue."

    # ------------------------------------------------------------------

    def _explain_syntax(self, error: Optional[str]) -> str:
        if error:
            first_line = error.splitlines()[0] if "\n" in error else error
            return f"Syntax error in your code: {first_line}"
        return "Your code contains a syntax error and could not be executed."

    def _explain_runtime(self, error: Optional[str]) -> str:
        if not error:
            return "A runtime error occurred during execution."
        err_lower = error.lower()
        if "typeerror" in err_lower:
            return f"Your solution raises a TypeError — check that you handle all input types correctly. ({error.splitlines()[0]})"
        if "indexerror" in err_lower or "list index out of range" in err_lower:
            return "Your solution raises an IndexError — likely accessing an index that does not exist for edge-case inputs."
        if "keyerror" in err_lower:
            return "Your solution raises a KeyError — a dictionary key is missing for certain inputs."
        if "zerodivisionerror" in err_lower:
            return "Your solution raises a ZeroDivisionError — add a guard for zero denominators."
        if "attributeerror" in err_lower:
            return "Your solution raises an AttributeError — a method or attribute is accessed on an unexpected type."
        first_line = error.splitlines()[0]
        return f"Runtime error: {first_line}"

    def _explain_logic(
        self,
        failed: List[TestExecutionResult],
        hidden_sample: Optional[dict],
    ) -> str:
        sample = failed[0]
        multi = len(failed) > 1
        prefix = f"{len(failed)} test cases fail" if multi else "Your solution fails"

        # Error during test execution
        if getattr(sample, "error", None):
            return self._explain_runtime(sample.error)

        expected = sample.expected
        actual = sample.actual
        args = getattr(sample, "args", None)

        context = f" (input: {args})" if args is not None else ""

        if expected is None or actual is None:
            if hidden_sample:
                return self._explain_hidden(hidden_sample)
            return f"{prefix} — review the failing cases."

        # Numeric mismatch
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            if actual < expected:
                return f"{prefix}{context} — your solution returns a smaller value than expected ({actual} instead of {expected})."
            if actual > expected:
                return f"{prefix}{context} — your solution returns a larger value than expected ({actual} instead of {expected})."

        # List/sequence mismatch
        if isinstance(expected, list) and isinstance(actual, list):
            if sorted(str(x) for x in expected) == sorted(str(x) for x in actual):
                return f"{prefix}{context} — the values are correct but the order is wrong."
            if len(expected) != len(actual):
                return (
                    f"{prefix}{context} — wrong number of elements returned "
                    f"({len(actual)} instead of {len(expected)})."
                )
            return f"{prefix}{context} — incorrect values returned."

        # Boolean mismatch
        if isinstance(expected, bool) and isinstance(actual, bool):
            return f"{prefix}{context} — returns {actual} but {expected} is expected."

        # Generic
        return f"{prefix}{context} — expected {expected!r} but got {actual!r}."

    def _explain_hidden(self, sample: dict) -> str:
        error = sample.get("error")
        args = sample.get("args")
        expected = sample.get("expected")
        actual = sample.get("actual")
        context = f" (input: {args})" if args is not None else ""

        if error:
            return f"Your solution raises an exception on a hidden test case{context}: {error.splitlines()[0]}"

        if expected is not None and actual is not None:
            if isinstance(expected, list) and isinstance(actual, list):
                if sorted(str(x) for x in expected) == sorted(str(x) for x in actual):
                    return f"Your solution passes visible tests but fails a hidden case{context} — the values are correct but the order differs."
                if len(expected) != len(actual):
                    return (
                        f"Your solution passes visible tests but fails a hidden case{context} "
                        f"— wrong number of elements ({len(actual)} instead of {len(expected)})."
                    )
            return f"Your solution passes visible tests but fails a hidden case{context} — expected {expected!r}, got {actual!r}."

        return "Your solution passes visible tests but fails on hidden test cases — check for edge cases."
