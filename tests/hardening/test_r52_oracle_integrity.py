# tests/hardening/test_r52_oracle_integrity.py
#
# R5.2 Oracle Integrity — unit tests for:
#   - OracleValidator (reference execution + overlap cross-check)
#   - AITestGenerator cache version bump
#   - GeneratedCodingQuestion.reference_solution field

import types
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.execution.coding_test_case import CodingTestCase
from app.ai.test_generation.oracle_validator import OracleValidator, _outputs_equal
from app.ai.test_generation.test_cache_service import TestCacheService
from services.question_intelligence.coding_question_generator import GeneratedCodingQuestion


# ===========================================================
# Helpers
# ===========================================================

def _tc(args, expected) -> CodingTestCase:
    return CodingTestCase(args=args, expected=expected)


def _make_spec(entrypoint="two_sum"):
    from domain.contracts.execution.coding_spec import CodingSpec
    return CodingSpec(type="function", entrypoint=entrypoint, parameters=["nums", "target"])


CORRECT_TWO_SUM = """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        comp = target - n
        if comp in seen:
            return [seen[comp], i]
        seen[n] = i
    return []
"""

WRONG_TWO_SUM = """
def two_sum(nums, target):
    return [0, 0]
"""

# Visible test: two_sum([2,7,11,15], 9) → [0,1]
_VISIBLE_TESTS = [_tc([[2, 7, 11, 15], 9], [0, 1])]


# ===========================================================
# _outputs_equal
# ===========================================================

class TestOutputsEqual:

    def test_exact_match(self):
        assert _outputs_equal([0, 2], [0, 2]) is True

    def test_reordered_list_is_not_equal(self):
        assert _outputs_equal([1, 0], [0, 1]) is False

    def test_mismatch(self):
        assert _outputs_equal([0, 3], [0, 2]) is False

    def test_none_not_equal_to_value(self):
        assert _outputs_equal(None, 0) is False

    def test_string_match(self):
        assert _outputs_equal("hello", "hello") is True


# ===========================================================
# OracleValidator — trust check (TASK 2)
# ===========================================================

class TestOracleValidatorTrustCheck:

    def setup_method(self):
        self.validator = OracleValidator()
        self.spec = _make_spec()
        self.visible = _VISIBLE_TESTS

    def test_wrong_reference_solution_fails_trust_check(self):
        result = self.validator.validate(
            reference_solution=WRONG_TWO_SUM,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=[_tc([[1, 5, 3, 2], 4], [0, 2])],
        )
        assert result is None

    def test_correct_reference_solution_passes_trust_check(self):
        result = self.validator.validate(
            reference_solution=CORRECT_TWO_SUM,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=[],
        )
        assert result is not None

    def test_empty_reference_solution_disables_validation(self):
        result = self.validator.validate(
            reference_solution="",
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=[_tc([[1, 2], 3], 0)],
        )
        assert result is None

    def test_none_reference_solution_disables_validation(self):
        result = self.validator.validate(
            reference_solution=None,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=[],
        )
        assert result is None


# ===========================================================
# OracleValidator — hidden test filtering (TASK 1)
# ===========================================================

class TestOracleValidatorHiddenFiltering:

    def setup_method(self):
        self.validator = OracleValidator()
        self.visible = _VISIBLE_TESTS

    def test_correct_hidden_expected_retained(self):
        # two_sum([3,2,4], 6) → [1,2]
        hidden = [_tc([[3, 2, 4], 6], [1, 2])]
        result = self.validator.validate(
            reference_solution=CORRECT_TWO_SUM,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=hidden,
        )
        assert result is not None
        assert len(result) == 1

    def test_wrong_hidden_expected_discarded(self):
        # two_sum([1,5,3,2], 4) → correct [0,2], LLM said [0,3]
        hidden = [_tc([[1, 5, 3, 2], 4], [0, 3])]
        result = self.validator.validate(
            reference_solution=CORRECT_TWO_SUM,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=hidden,
        )
        assert result == []

    def test_mix_of_correct_and_wrong_hidden_tests(self):
        hidden = [
            _tc([[3, 2, 4], 6], [1, 2]),        # correct
            _tc([[1, 5, 3, 2], 4], [0, 3]),     # wrong
        ]
        result = self.validator.validate(
            reference_solution=CORRECT_TWO_SUM,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=hidden,
        )
        assert result is not None
        assert len(result) == 1
        assert result[0].args == [[3, 2, 4], 6]

    def test_all_hidden_discarded_returns_empty_list(self):
        hidden = [
            _tc([[1, 5, 3, 2], 4], [0, 3]),
            _tc([[2, 7, 11, 15], 9], [99, 99]),
        ]
        result = self.validator.validate(
            reference_solution=CORRECT_TWO_SUM,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=hidden,
        )
        assert result == []


# ===========================================================
# OracleValidator — overlap cross-check (TASK 3)
# ===========================================================

class TestOracleValidatorOverlapCheck:

    def setup_method(self):
        self.validator = OracleValidator()
        self.visible = _VISIBLE_TESTS

    def test_hidden_test_same_args_same_expected_retained(self):
        # Same args AND same expected as visible test → kept (also passes reference check)
        hidden = [_tc([[2, 7, 11, 15], 9], [0, 1])]
        result = self.validator.validate(
            reference_solution=CORRECT_TWO_SUM,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=hidden,
        )
        assert result is not None
        assert len(result) == 1

    def test_hidden_test_same_args_different_expected_discarded(self):
        # Same args as visible test but wrong expected → overlap check discards it
        hidden = [_tc([[2, 7, 11, 15], 9], [99, 99])]
        result = self.validator.validate(
            reference_solution=CORRECT_TWO_SUM,
            entrypoint="two_sum",
            visible_tests=self.visible,
            hidden_tests=hidden,
        )
        assert result == []


# ===========================================================
# AITestGenerator — all hidden discarded → no crash
# ===========================================================

class TestAITestGeneratorAllDiscarded:

    def test_all_hidden_discarded_returns_empty_no_crash(self):
        from app.ai.test_generation.ai_test_generator import AITestGenerator
        from domain.contracts.question.question import Question, QuestionType
        from domain.contracts.interview.interview_area import InterviewArea
        from domain.contracts.execution.coding_spec import CodingSpec

        spec = CodingSpec(type="function", entrypoint="two_sum", parameters=["nums", "target"])
        question = Question(
            id="q-oracle-test",
            area=InterviewArea.TECH_CODING,
            type=QuestionType.CODING,
            prompt="Implement two_sum(nums, target).",
            coding_spec=spec,
            visible_tests=list(_VISIBLE_TESTS),
            reference_solution=CORRECT_TWO_SUM,
        )

        llm = MagicMock()
        generator = AITestGenerator(llm=llm)

        # Patch cache miss
        generator._cache.get_tests = MagicMock(return_value=None)
        generator._cache.store_tests = MagicMock()

        # LLM returns hidden tests with wrong expected
        wrong_test = _tc([[1, 5, 3, 2], 4], [0, 3])
        generator._response_parser.invoke_and_parse = MagicMock(return_value=[wrong_test])
        generator._diversity_filter.filter = MagicMock(side_effect=lambda t, n: t)

        result = generator.generate_tests(question, num_tests=1)

        # All hidden tests discarded → visible-only (empty)
        assert result == []
        # Cache must NOT store empty list
        generator._cache.store_tests.assert_not_called()


# ===========================================================
# Cache version
# ===========================================================

class TestCacheVersion:

    def test_cache_version_is_4(self):
        assert TestCacheService.CACHE_VERSION == 4

    def test_cache_key_includes_version_and_ref_hash(self):
        import hashlib
        from domain.contracts.question.question import Question, QuestionType
        from domain.contracts.interview.interview_area import InterviewArea

        q = Question(
            id="q1",
            area=InterviewArea.TECH_CODING,
            type=QuestionType.CODING,
            prompt="test",
            reference_solution="def f(): pass",
        )
        svc = TestCacheService.__new__(TestCacheService)
        svc._cache = {}
        key = svc._build_cache_key(q, 3)
        ref_hash = hashlib.sha256("def f(): pass".encode()).hexdigest()[:16]
        expected_key = hashlib.sha256(f"v4:q1:test:3:{ref_hash}".encode()).hexdigest()
        assert key == expected_key


# ===========================================================
# GeneratedCodingQuestion.reference_solution
# ===========================================================

class TestGeneratedCodingQuestionReferenceSolution:

    def test_reference_solution_defaults_to_empty_string(self):
        from domain.contracts.execution.coding_spec import CodingSpec
        spec = CodingSpec(type="function", entrypoint="f", parameters=["x"])
        q = GeneratedCodingQuestion(
            prompt="Implement f(x).",
            coding_spec=spec,
            visible_tests=[],
        )
        assert q.reference_solution == ""

    def test_reference_solution_can_be_set(self):
        from domain.contracts.execution.coding_spec import CodingSpec
        spec = CodingSpec(type="function", entrypoint="f", parameters=["x"])
        q = GeneratedCodingQuestion(
            prompt="Implement f(x).",
            coding_spec=spec,
            visible_tests=[],
            reference_solution="def f(x): return x",
        )
        assert q.reference_solution == "def f(x): return x"
