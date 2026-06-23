# tests/hardening/test_r534_coding_trust.py
#
# R5.3.4 — Final Coding Trust Hardening
#   Task 1: Oracle/Harness list semantics consistency
#   Task 2: Hidden exception transparency
#   Task 3: Cache key includes reference_solution

import hashlib
import json
from unittest.mock import MagicMock, patch

import pytest

from app.ai.test_generation.oracle_validator import _outputs_equal
from app.ai.test_generation.test_cache_service import TestCacheService
from domain.contracts.execution.coding_test_case import CodingTestCase


# ===========================================================
# Helpers
# ===========================================================

def _tc(args, expected) -> CodingTestCase:
    return CodingTestCase(args=args, expected=expected)


def _make_question(ref="def f(): pass"):
    from domain.contracts.question.question import Question, QuestionType
    from domain.contracts.interview.interview_area import InterviewArea
    return Question(
        id="q-r534",
        area=InterviewArea.TECH_CODING,
        type=QuestionType.CODING,
        prompt="Implement f(x).",
        reference_solution=ref,
    )


# ===========================================================
# Task 1 — Oracle list ordering must match runtime semantics
# ===========================================================

class TestOutputsEqualOrdering:

    def test_ordered_lists_equal(self):
        assert _outputs_equal([0, 1], [0, 1]) is True

    def test_reordered_list_not_equal(self):
        # Runtime uses ==; oracle must agree
        assert _outputs_equal([1, 0], [0, 1]) is False

    def test_nested_list_exact_match(self):
        assert _outputs_equal([[0, 1], [2, 3]], [[0, 1], [2, 3]]) is True

    def test_nested_list_reordered_outer_not_equal(self):
        assert _outputs_equal([[2, 3], [0, 1]], [[0, 1], [2, 3]]) is False

    def test_nested_list_reordered_inner_not_equal(self):
        assert _outputs_equal([[1, 0], [2, 3]], [[0, 1], [2, 3]]) is False

    def test_mixed_type_list_not_equal(self):
        # [1, "1"] != ["1", 1] — str coercion must not collapse
        assert _outputs_equal([1, "1"], ["1", 1]) is False

    def test_int_list_not_equal_to_str_list(self):
        assert _outputs_equal([1, 2], ["1", "2"]) is False

    def test_float_tolerance_applied(self):
        assert _outputs_equal(1.0, 1.0000000001) is True

    def test_float_out_of_tolerance_not_equal(self):
        assert _outputs_equal(1.0, 1.1) is False

    def test_scalar_match(self):
        assert _outputs_equal(42, 42) is True

    def test_scalar_mismatch(self):
        assert _outputs_equal(42, 43) is False

    def test_none_not_equal_to_value(self):
        assert _outputs_equal(None, 0) is False

    def test_none_equal_to_none(self):
        assert _outputs_equal(None, None) is True

    def test_type_mismatch_list_vs_tuple(self):
        assert _outputs_equal([0, 1], (0, 1)) is False


# ===========================================================
# Task 2 — Hidden exception emits failure sample
# ===========================================================

class TestHiddenExceptionTransparency:
    """
    Verifies that the rendered harness code emits __HIDDEN_FAILURE__ on exception.
    Uses HarnessBuilder to generate real code, then exec() it.
    """

    def _render_harness(self, candidate_code: str, hidden_tests):
        from services.coding_engine.harness.harness_builder import HarnessBuilder
        from domain.contracts.execution.coding_spec import CodingSpec

        spec = CodingSpec(type="function", entrypoint="f", parameters=["x"])
        builder = HarnessBuilder()
        return builder.build(
            user_code=candidate_code,
            visible_tests=[],
            hidden_tests=hidden_tests,
            function_name="f",
            coding_spec=spec,
        )

    def _exec_harness(self, code: str):
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(compile(code, "<harness>", "exec"), {})
        return buf.getvalue()

    def test_hidden_type_error_emits_failure_sample(self):
        # f(x) raises TypeError when called with incompatible args
        candidate = "def f(x): return x + 1"
        # Pass a string arg to trigger TypeError
        hidden = [_tc(["not_an_int"], 99)]
        code = self._render_harness(candidate, hidden)
        output = self._exec_harness(code)
        assert "__HIDDEN_FAILURE__" in output
        line = next(l for l in output.splitlines() if "__HIDDEN_FAILURE__" in l)
        data = json.loads(line.split("__HIDDEN_FAILURE__:")[1])
        assert data["error"] is not None
        assert "TypeError" in data["error"]
        assert data["expected"] is None
        assert data["actual"] is None

    def test_hidden_attribute_error_emits_failure_sample(self):
        candidate = "def f(x): return x.nonexistent_attr"
        hidden = [_tc([42], "anything")]
        code = self._render_harness(candidate, hidden)
        output = self._exec_harness(code)
        assert "__HIDDEN_FAILURE__" in output
        line = next(l for l in output.splitlines() if "__HIDDEN_FAILURE__" in l)
        data = json.loads(line.split("__HIDDEN_FAILURE__:")[1])
        assert "AttributeError" in data["error"]

    def test_only_first_hidden_exception_emitted(self):
        candidate = "def f(x): return x + 1"
        hidden = [_tc(["a"], 1), _tc(["b"], 2)]
        code = self._render_harness(candidate, hidden)
        output = self._exec_harness(code)
        count = output.count("__HIDDEN_FAILURE__")
        assert count == 1

    def test_hidden_logic_failure_still_emits_sample(self):
        candidate = "def f(x): return x * 2"
        hidden = [_tc([3], 99)]  # correct is 6, not 99
        code = self._render_harness(candidate, hidden)
        output = self._exec_harness(code)
        assert "__HIDDEN_FAILURE__" in output
        line = next(l for l in output.splitlines() if "__HIDDEN_FAILURE__" in l)
        data = json.loads(line.split("__HIDDEN_FAILURE__:")[1])
        assert data.get("error") is None
        assert data["actual"] == 6


# ===========================================================
# Task 2 — Parser handles error field
# ===========================================================

class TestHarnessOutputParserHiddenError:

    def _make_raw(self, stdout: str):
        raw = MagicMock()
        raw.stdout = stdout
        raw.execution_time_ms = 0
        return raw

    def _parse(self, stdout: str):
        from services.coding_engine.harness_output_parser import HarnessOutputParser
        parser = HarnessOutputParser()
        return parser.parse("q1", self._make_raw(stdout))

    def test_error_field_stored_in_hidden_failure_sample(self):
        payload = json.dumps({"args": [42], "expected": None, "actual": None, "error": "TypeError: unsupported"})
        stdout = (
            f"__HIDDEN_FAILURE__:{payload}\n"
            "__HIDDEN__:0:1\n"
            "__RESULT__:0:1\n"
        )
        result = self._parse(stdout)
        assert result.hidden_failure_sample is not None
        assert result.hidden_failure_sample["error"] == "TypeError: unsupported"
        assert result.hidden_failure_sample["expected"] is None
        assert result.hidden_failure_sample["actual"] is None

    def test_logic_failure_sample_has_no_error_field(self):
        payload = json.dumps({"args": [3], "expected": 99, "actual": 6, "error": None})
        stdout = (
            f"__HIDDEN_FAILURE__:{payload}\n"
            "__HIDDEN__:0:1\n"
            "__RESULT__:0:1\n"
        )
        result = self._parse(stdout)
        assert result.hidden_failure_sample is not None
        assert result.hidden_failure_sample["error"] is None
        assert result.hidden_failure_sample["actual"] == 6


# ===========================================================
# Task 2 — FailureBlock renders exception message
# ===========================================================

class TestFailureBlockHiddenException:

    def _make_execution(self, hidden_sample):
        execution = MagicMock()
        execution.passed_tests = 2
        execution.total_tests = 3
        execution.success = False
        execution.test_results = []
        execution.hidden_failure_sample = hidden_sample
        return execution

    def _build_block(self, hidden_sample):
        from app.ui.presenters.feedback.blocks.failure_block import FailureBlock
        block = FailureBlock()
        execution = self._make_execution(hidden_sample)
        analysis = MagicMock()
        from domain.contracts.feedback.error_type import ErrorType
        analysis.error_type = ErrorType.UNKNOWN
        return block.build(None, None, None, execution, analysis, None)

    def test_exception_sample_shows_error_not_expected_got(self):
        sample = {"args": [42], "expected": None, "actual": None, "error": "TypeError: unsupported operand"}
        result = self._build_block(sample)
        assert "TypeError: unsupported operand" in result.content
        assert "Error:" in result.content
        assert "Expected:" not in result.content
        assert "Got:" not in result.content

    def test_logic_failure_shows_expected_and_got(self):
        sample = {"args": [3], "expected": 99, "actual": 6, "error": None}
        result = self._build_block(sample)
        assert "Expected: 99" in result.content
        assert "Got: 6" in result.content
        assert "Error:" not in result.content


# ===========================================================
# Task 3 — Cache key includes reference_solution
# ===========================================================

class TestCacheKeyRefSolution:

    def _make_svc(self):
        svc = TestCacheService.__new__(TestCacheService)
        svc._cache = {}
        return svc

    def test_different_ref_solutions_produce_different_keys(self):
        svc = self._make_svc()
        q1 = _make_question(ref="def f(): return 1")
        q2 = _make_question(ref="def f(): return 2")
        assert svc._build_cache_key(q1, 3) != svc._build_cache_key(q2, 3)

    def test_same_ref_solution_produces_same_key(self):
        svc = self._make_svc()
        q1 = _make_question(ref="def f(): pass")
        q2 = _make_question(ref="def f(): pass")
        assert svc._build_cache_key(q1, 3) == svc._build_cache_key(q2, 3)

    def test_empty_ref_solution_produces_valid_key(self):
        svc = self._make_svc()
        q = _make_question(ref="")
        key = svc._build_cache_key(q, 3)
        assert isinstance(key, str) and len(key) == 64

    def test_none_ref_solution_handled(self):
        svc = self._make_svc()
        q = _make_question(ref=None)
        key = svc._build_cache_key(q, 3)
        assert isinstance(key, str) and len(key) == 64

    def test_cache_version_is_4(self):
        assert TestCacheService.CACHE_VERSION == 4

    def test_changing_ref_invalidates_cache(self):
        svc = self._make_svc()
        q_v1 = _make_question(ref="def f(): return 1")
        q_v2 = _make_question(ref="def f(): return 2")
        tests = [_tc([1], 2)]
        svc.store_tests(q_v1, 3, tests)
        # Should not find cached tests for updated reference
        assert svc.get_tests(q_v2, 3) is None

    def test_correct_ref_returns_cached_tests(self):
        svc = self._make_svc()
        q = _make_question(ref="def f(): return 1")
        tests = [_tc([1], 2)]
        svc.store_tests(q, 3, tests)
        cached = svc.get_tests(q, 3)
        assert cached is not None
        assert len(cached) == 1
