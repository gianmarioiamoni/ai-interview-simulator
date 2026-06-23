# app/ai/test_generation/oracle_validator.py
#
# OracleValidator
#
# Executes a reference solution against a test case in an isolated subprocess
# and compares the output to the LLM-generated expected value.
#
# Used for:
#   TASK 2: trust check — reference solution vs visible tests
#   TASK 1: filter — reference solution vs hidden tests
#   TASK 3: overlap check — hidden test args vs visible test args/expected

import json
import textwrap
from typing import Any, List, Optional, Tuple

from domain.contracts.execution.coding_test_case import CodingTestCase
from services.coding_engine.execution_sandbox import ExecutionSandbox
from app.core.logger import get_logger

logger = get_logger(__name__)

_SANDBOX_TIMEOUT = 5
_REPR_MAX = 500


def _build_runner(reference_solution: str, entrypoint: str, test: CodingTestCase) -> str:
    args_repr = repr(test.args)
    kwargs_repr = repr(dict(test.kwargs)) if test.kwargs else "{}"
    return textwrap.dedent(f"""\
import json, sys

{reference_solution}

try:
    result = {entrypoint}(*{args_repr}, **{kwargs_repr})
    print(json.dumps(result))
except Exception as exc:
    print("__ERROR__:" + str(exc), file=sys.stderr)
    sys.exit(1)
""")


def _run_reference(
    reference_solution: str,
    entrypoint: str,
    test: CodingTestCase,
) -> Tuple[bool, Any]:
    """
    Returns (success, output).
    success=False when execution errors, timeouts, or produces no parseable output.
    """
    sandbox = ExecutionSandbox(timeout_seconds=_SANDBOX_TIMEOUT)
    code = _build_runner(reference_solution, entrypoint, test)
    result = sandbox.execute(code)

    if result.returncode != 0 or result.timeout:
        return False, None

    stdout = result.stdout.strip()
    if not stdout:
        return False, None

    try:
        return True, json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return True, stdout


def _outputs_equal(reference_output: Any, expected: Any) -> bool:
    """
    Structural equality — handles list ordering (treats lists as sets for index-pair results).
    Primary: direct equality.
    Secondary: sorted comparison (for index-pair / unordered results).
    """
    if reference_output == expected:
        return True
    try:
        if isinstance(reference_output, list) and isinstance(expected, list):
            return sorted(str(x) for x in reference_output) == sorted(str(x) for x in expected)
    except Exception:
        pass
    return False


class OracleValidator:
    """
    Validates LLM-generated hidden tests against a reference solution.

    Step 1 (TASK 2): verify reference solution passes all visible tests.
    Step 2 (TASK 1): discard hidden tests whose expected value differs from reference output.
    Step 3 (TASK 3): discard hidden tests whose args overlap with a visible test but expected differs.
    """

    def validate(
        self,
        reference_solution: str,
        entrypoint: str,
        visible_tests: List[CodingTestCase],
        hidden_tests: List[CodingTestCase],
    ) -> Optional[List[CodingTestCase]]:
        """
        Returns the validated subset of hidden_tests, or None if validation is disabled
        (reference solution not trusted or not provided).
        """
        if not reference_solution or not reference_solution.strip():
            logger.warning("[OracleValidator] No reference solution — skipping validation")
            return None

        # ----------------------------------------------------------
        # TASK 2: trust check — reference solution vs visible tests
        # ----------------------------------------------------------
        if not self._reference_passes_visible(reference_solution, entrypoint, visible_tests):
            logger.warning(
                "[OracleValidator] Reference solution failed visible tests — "
                "validation disabled, using visible-only scoring"
            )
            return None

        # ----------------------------------------------------------
        # TASK 3: build visible args index for overlap check
        # ----------------------------------------------------------
        visible_index = {
            repr(t.args): t.expected for t in visible_tests
        }

        # ----------------------------------------------------------
        # TASK 1: filter hidden tests
        # ----------------------------------------------------------
        validated: List[CodingTestCase] = []
        for test in hidden_tests:
            # TASK 3: overlap check
            args_key = repr(test.args)
            if args_key in visible_index:
                if not _outputs_equal(visible_index[args_key], test.expected):
                    logger.debug(
                        "[OracleValidator] Hidden test discarded (overlap mismatch): args=%s "
                        "visible_expected=%s hidden_expected=%s",
                        args_key[:_REPR_MAX],
                        visible_index[args_key],
                        test.expected,
                    )
                    continue

            # TASK 1: reference execution check
            success, ref_output = _run_reference(reference_solution, entrypoint, test)
            if not success:
                logger.debug(
                    "[OracleValidator] Hidden test discarded (reference execution error): args=%s",
                    args_key[:_REPR_MAX],
                )
                continue

            if not _outputs_equal(ref_output, test.expected):
                logger.debug(
                    "[OracleValidator] Hidden test discarded (wrong expected): "
                    "args=%s ref=%s llm_expected=%s",
                    args_key[:_REPR_MAX],
                    ref_output,
                    test.expected,
                )
                continue

            validated.append(test)

        return validated

    # ------------------------------------------------------------------

    def _reference_passes_visible(
        self,
        reference_solution: str,
        entrypoint: str,
        visible_tests: List[CodingTestCase],
    ) -> bool:
        if not visible_tests:
            return True
        for test in visible_tests:
            success, ref_output = _run_reference(reference_solution, entrypoint, test)
            if not success:
                logger.debug(
                    "[OracleValidator] Reference solution execution error on visible test: args=%s",
                    repr(test.args)[:_REPR_MAX],
                )
                return False
            if not _outputs_equal(ref_output, test.expected):
                logger.debug(
                    "[OracleValidator] Reference solution produced wrong output on visible test: "
                    "args=%s ref=%s expected=%s",
                    repr(test.args)[:_REPR_MAX],
                    ref_output,
                    test.expected,
                )
                return False
        return True
