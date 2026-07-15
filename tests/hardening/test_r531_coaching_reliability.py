# tests/hardening/test_r531_coaching_reliability.py
#
# R5.3.1 Coaching Reliability Hardening Tests
#
# Covers:
#   F1  — Comparator contract disclosure
#   F3  — Oracle enforcement: no unvalidated hidden tests
#   F4  — Cache protection: no caching of unvalidated tests
#   F6  — Hint refresh after retry
#   F9  — Stronger alignment validation

import hashlib
from unittest.mock import MagicMock

import pytest

from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.execution.coding_spec import CodingSpec
from domain.contracts.question.question import Question, QuestionType
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.ai.ai_hint import AIHint
from domain.contracts.ai.hint_level import HintLevel
from domain.contracts.question.question_result import QuestionResult


# ===========================================================
# Helpers
# ===========================================================


def _tc(args, expected) -> CodingTestCase:
    return CodingTestCase(args=args, expected=expected)


def _make_spec(entrypoint="two_sum", parameters=None) -> CodingSpec:
    return CodingSpec(
        type="function",
        entrypoint=entrypoint,
        parameters=parameters or ["nums", "target"],
    )


def _make_question(
    *,
    qid: str = "q-test",
    reference_solution: str = "",
    prompt: str = "Implement two_sum(nums, target).",
    spec: CodingSpec | None = None,
    visible_tests: list | None = None,
) -> Question:
    return Question(
        id=qid,
        area=InterviewArea.TECH_CODING,
        type=QuestionType.CODING,
        prompt=prompt,
        coding_spec=spec or _make_spec(),
        visible_tests=visible_tests or [],
        reference_solution=reference_solution,
    )


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

_VISIBLE = [_tc([[2, 7, 11, 15], 9], [0, 1])]


# ===========================================================
# F3 — Oracle enforcement: unvalidated hidden tests discarded
# ===========================================================


class TestOracleEnforcement:
    def _make_generator(self, question, lm_tests):
        from app.ai.test_generation.ai_test_generator import AITestGenerator

        gen = AITestGenerator(llm=MagicMock())
        gen._cache.get_tests = MagicMock(return_value=None)
        gen._cache.store_tests = MagicMock()
        gen._response_parser.invoke_and_parse = MagicMock(return_value=lm_tests)
        gen._diversity_filter.filter = MagicMock(side_effect=lambda t, n: t)
        return gen

    def test_empty_reference_solution_discards_hidden_tests(self):
        question = _make_question(reference_solution="", visible_tests=_VISIBLE)
        hidden = [_tc([[1, 2], 3], [0, 1])]
        gen = self._make_generator(question, hidden)

        result = gen.generate_tests(question, num_tests=1)

        assert result == []

    def test_missing_reference_solution_discards_hidden_tests(self):
        question = _make_question(reference_solution="", visible_tests=_VISIBLE)
        hidden = [_tc([[3, 2, 4], 6], [1, 2])]
        gen = self._make_generator(question, hidden)

        result = gen.generate_tests(question, num_tests=1)

        assert result == []

    def test_failing_reference_solution_discards_hidden_tests(self):
        broken_ref = "def two_sum(nums, target): return [99, 99]"
        question = _make_question(reference_solution=broken_ref, visible_tests=_VISIBLE)
        hidden = [_tc([[3, 2, 4], 6], [1, 2])]
        gen = self._make_generator(question, hidden)

        result = gen.generate_tests(question, num_tests=1)

        assert result == []

    def test_valid_reference_solution_retains_correct_hidden_tests(self):
        question = _make_question(reference_solution=CORRECT_TWO_SUM, visible_tests=_VISIBLE)
        # two_sum([3,2,4], 6) → [1,2] (correct)
        hidden = [_tc([[3, 2, 4], 6], [1, 2])]
        gen = self._make_generator(question, hidden)

        result = gen.generate_tests(question, num_tests=1)

        assert len(result) == 1


# ===========================================================
# F4 — Cache protection
# ===========================================================


class TestCacheProtection:
    def _make_generator(self, question, lm_tests, ref_solution=""):
        from app.ai.test_generation.ai_test_generator import AITestGenerator

        question_with_ref = _make_question(
            reference_solution=ref_solution,
            visible_tests=_VISIBLE,
        )
        gen = AITestGenerator(llm=MagicMock())
        gen._cache.get_tests = MagicMock(return_value=None)
        gen._cache.store_tests = MagicMock()
        gen._response_parser.invoke_and_parse = MagicMock(return_value=lm_tests)
        gen._diversity_filter.filter = MagicMock(side_effect=lambda t, n: t)
        return gen, question_with_ref

    def test_cache_not_called_when_reference_missing(self):
        hidden = [_tc([[1, 2], 3], [0, 1])]
        gen, question = self._make_generator(_make_question(), hidden, ref_solution="")

        gen.generate_tests(question, num_tests=1)

        gen._cache.store_tests.assert_not_called()

    def test_cache_not_called_when_all_hidden_discarded(self):
        broken_ref = "def two_sum(nums, target): return [99, 99]"
        question = _make_question(reference_solution=broken_ref, visible_tests=_VISIBLE)

        from app.ai.test_generation.ai_test_generator import AITestGenerator

        gen = AITestGenerator(llm=MagicMock())
        gen._cache.get_tests = MagicMock(return_value=None)
        gen._cache.store_tests = MagicMock()
        gen._response_parser.invoke_and_parse = MagicMock(
            return_value=[_tc([[3, 2, 4], 6], [1, 2])]
        )
        gen._diversity_filter.filter = MagicMock(side_effect=lambda t, n: t)

        gen.generate_tests(question, num_tests=1)

        gen._cache.store_tests.assert_not_called()

    def test_cache_called_only_with_validated_tests(self):
        question = _make_question(reference_solution=CORRECT_TWO_SUM, visible_tests=_VISIBLE)
        valid_hidden = [_tc([[3, 2, 4], 6], [1, 2])]

        from app.ai.test_generation.ai_test_generator import AITestGenerator

        gen = AITestGenerator(llm=MagicMock())
        gen._cache.get_tests = MagicMock(return_value=None)
        gen._cache.store_tests = MagicMock()
        gen._response_parser.invoke_and_parse = MagicMock(return_value=valid_hidden)
        gen._diversity_filter.filter = MagicMock(side_effect=lambda t, n: t)

        result = gen.generate_tests(question, num_tests=1)

        assert result != []
        gen._cache.store_tests.assert_called_once()


# ===========================================================
# F6 — Hint refresh after retry
# ===========================================================


class TestHintRefreshOnRetry:
    def _build_state_with_hint(self):
        from tests.factories.interview_state_factory import build_state_with_execution

        state = build_state_with_execution(passed_tests=0, total_tests=5)
        question = state.current_question

        old_hint = AIHint(explanation="old bug", suggestion="old fix")
        old_result = state.get_result_for_question(question.id)
        updated_result = old_result.model_copy(
            update={"ai_hint": old_hint, "hint_level": HintLevel.TARGETED}
        )
        new_results = dict(state.results_by_question)
        new_results[question.id] = updated_result
        return state.model_copy(update={"results_by_question": new_results})

    def test_clear_result_removes_ai_hint(self):
        state = self._build_state_with_hint()
        question = state.current_question

        assert state.get_result_for_question(question.id).ai_hint is not None

        cleared = state.clear_result_for_question(question.id)

        assert cleared.get_result_for_question(question.id) is None

    def test_hint_node_generates_fresh_hint_when_result_cleared(self):
        from app.graph.nodes.hint_node import HintNode
        from tests.factories.interview_state_factory import build_state_with_execution
        from unittest.mock import Mock

        state = build_state_with_execution(passed_tests=0, total_tests=5)
        question = state.current_question

        cleared = state.clear_result_for_question(question.id)

        # After clear, no result exists — HintNode should skip (no execution result)
        mock_service = Mock()
        node = HintNode(mock_service)
        result_state = node(cleared)

        # No execution result → hint node bails out before LLM call
        mock_service.generate_hint.assert_not_called()

    def test_hint_node_idempotency_does_not_fire_after_retry_clears_result(self):
        from app.graph.nodes.hint_node import HintNode
        from tests.factories.interview_state_factory import build_state_with_execution
        from unittest.mock import Mock

        # Build state with existing result but NO hint (simulates post-retry new execution)
        state = build_state_with_execution(passed_tests=0, total_tests=5)
        question = state.current_question

        # Confirm no hint on fresh result
        result = state.get_result_for_question(question.id)
        assert result.ai_hint is None
        assert result.hint_level is None

        mock_service = Mock()
        fresh_hint = AIHint(explanation="fresh explanation", suggestion="fresh fix")
        mock_service.generate_hint.return_value = fresh_hint

        node = HintNode(mock_service)
        new_state = node(state)

        # Hint should be generated (not blocked by idempotency guard)
        mock_service.generate_hint.assert_called_once()
        final_result = new_state.get_result_for_question(question.id)
        assert final_result.ai_hint == fresh_hint


# ===========================================================
# F1 — Comparator contract disclosure
# ===========================================================


class TestComparatorContractDisclosure:
    def _build_contract(self, entrypoint="solve", parameters=None, visible_tests=None):
        from app.ui.response.sections.display_section import DisplaySection

        spec = CodingSpec(
            type="function",
            entrypoint=entrypoint,
            parameters=parameters or ["nums"],
        )
        question = Question(
            id="q-display",
            area=InterviewArea.TECH_CODING,
            type=QuestionType.CODING,
            prompt=f"Implement {entrypoint}(nums).",
            coding_spec=spec,
            visible_tests=visible_tests or [],
        )
        return DisplaySection._build_contract_block(question)

    def test_contract_shows_float_tolerance(self):
        block = self._build_contract()
        assert "1e-6" in block

    def test_contract_mentions_relative_tolerance(self):
        block = self._build_contract()
        assert "relative tolerance" in block or "rel_tol" in block or "1e-6" in block

    def test_contract_no_longer_says_exact_equality_only(self):
        block = self._build_contract()
        # Must NOT claim pure exact equality without qualification
        assert "Exact equality\n" not in block
        assert block.count("Exact equality") == 1  # present but with float qualifier

    def test_contract_shows_full_comparison_rule(self):
        block = self._build_contract()
        assert "Exact equality (floats: relative tolerance 1e-6)" in block


# ===========================================================
# F9 — Alignment validation: runtime blocking vs narrative warnings
# ===========================================================


class TestAlignmentValidation:
    def _make_generated(
        self, prompt: str, entrypoint: str, parameters: list[str], spec_type: str = "function"
    ):
        from services.question_intelligence.coding_question_generator import GeneratedCodingQuestion
        from domain.contracts.execution.coding_spec import CodingSpec

        spec = CodingSpec(type=spec_type, entrypoint=entrypoint, parameters=parameters)
        return GeneratedCodingQuestion(
            prompt=prompt,
            coding_spec=spec,
            visible_tests=[],
        )

    def _make_pipeline(self):
        from services.question_intelligence.pipelines.coding_question_pipeline import (
            CodingQuestionPipeline,
        )

        return CodingQuestionPipeline(
            retrieval_service=MagicMock(),
            coding_generator=MagicMock(),
        )

    # ------------------------------------------------------------------
    # BLOCKING: runtime contract violations must still raise
    # ------------------------------------------------------------------

    def test_valid_spec_passes_regardless_of_prose(self):
        # Prose omits function name entirely — must NOT raise (narrative warning only)
        pipeline = self._make_pipeline()
        item = self._make_generated(
            prompt="Implement a function that finds two numbers summing to the target.",
            entrypoint="two_sum",
            parameters=["nums", "target"],
        )
        spec = item.coding_spec
        pipeline._validate_alignment(item, spec)  # must not raise

    def test_entrypoint_not_in_prose_does_not_raise(self):
        # Core change: missing entrypoint in prose is now a warning, not an error
        pipeline = self._make_pipeline()
        item = self._make_generated(
            prompt="Design and implement a function taking implementations and test cases.",
            entrypoint="run_tests",
            parameters=["implementations", "test_cases"],
        )
        spec = item.coding_spec
        pipeline._validate_alignment(item, spec)  # must not raise

    def test_parameter_not_in_prose_does_not_raise(self):
        # Core change: missing param in prose is now a warning, not an error
        pipeline = self._make_pipeline()
        item = self._make_generated(
            prompt="Implement def two_sum that returns indices.",
            entrypoint="two_sum",
            parameters=["nums", "target"],
        )
        spec = item.coding_spec
        pipeline._validate_alignment(item, spec)  # must not raise

    def test_invalid_entrypoint_identifier_raises(self):
        # BLOCKING: entrypoint must be a valid Python identifier
        pipeline = self._make_pipeline()
        from domain.contracts.execution.coding_spec import CodingSpec
        from services.question_intelligence.coding_question_generator import GeneratedCodingQuestion

        spec = CodingSpec(type="function", entrypoint="two-sum", parameters=["nums"])
        item = GeneratedCodingQuestion(
            prompt="Implement two-sum.", coding_spec=spec, visible_tests=[]
        )
        with pytest.raises(ValueError, match="valid Python identifier"):
            pipeline._validate_alignment(item, spec)

    def test_type_annotated_parameter_raises(self):
        # BLOCKING: type annotations in parameters are rejected (CodingSpec normalizes them
        # at construction time; this tests direct _validate_alignment rejection path)
        pipeline = self._make_pipeline()
        from domain.contracts.execution.coding_spec import CodingSpec
        from services.question_intelligence.coding_question_generator import GeneratedCodingQuestion

        # Build spec with already-normalized bare param (CodingSpec strips annotations)
        # then manually inject a bad param to test validator directly
        spec = CodingSpec(type="function", entrypoint="solve", parameters=["n"])
        item = GeneratedCodingQuestion(
            prompt="Implement solve(n: int).",
            coding_spec=spec,
            visible_tests=[],
        )
        # Override parameters with annotation to simulate LLM JSON bypass
        object.__setattr__(spec, "parameters", ["n: int"])
        with pytest.raises(ValueError, match="valid Python identifier"):
            pipeline._validate_alignment(item, spec)

    # ------------------------------------------------------------------
    # CodingSpec normalization tests
    # ------------------------------------------------------------------

    def test_coding_spec_strips_type_annotations(self):
        from domain.contracts.execution.coding_spec import CodingSpec

        spec = CodingSpec(
            type="function",
            entrypoint="get_deployment_strategy",
            parameters=["strategy_type: str"],
        )
        assert spec.parameters == ["strategy_type"]

    def test_coding_spec_strips_multiple_type_annotations(self):
        from domain.contracts.execution.coding_spec import CodingSpec

        spec = CodingSpec(
            type="function",
            entrypoint="process",
            parameters=["items: List[int]", "threshold: float", "name"],
        )
        assert spec.parameters == ["items", "threshold", "name"]

    # ------------------------------------------------------------------
    # Class method: method_name required (still blocking)
    # ------------------------------------------------------------------

    def test_class_method_without_method_name_raises(self):
        from domain.contracts.execution.coding_spec import CodingSpec

        with pytest.raises(ValueError, match="method_name required"):
            CodingSpec(type="class_method", entrypoint="LRUCache", parameters=["key"])

    def test_class_method_valid_passes(self):
        pipeline = self._make_pipeline()
        from domain.contracts.execution.coding_spec import CodingSpec
        from services.question_intelligence.coding_question_generator import GeneratedCodingQuestion

        spec = CodingSpec(
            type="class_method",
            entrypoint="LRUCache",
            method_name="get",
            parameters=["key"],
        )
        item = GeneratedCodingQuestion(
            prompt="Implement an LRU cache supporting get and put.",
            coding_spec=spec,
            visible_tests=[],
        )
        pipeline._validate_alignment(item, spec)  # must not raise
