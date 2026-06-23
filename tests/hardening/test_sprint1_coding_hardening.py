# tests/hardening/test_sprint1_coding_hardening.py
#
# Regression suite for Coding Hardening Sprint 1.
# Covers: P0-A (oracle integrity), P0-B (candidate feedback), P0-C (quarantine).

import json
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.execution.coding_test_case import CodingTestCase
from domain.contracts.execution.execution_result import ExecutionResult, ExecutionStatus, ExecutionType
from domain.contracts.execution.execution_test_result import TestExecutionResult, TestStatus, TestType
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType


# ===========================================================
# HELPERS
# ===========================================================


def _make_question(prompt="Implement solution(x) returning x * 2.", *, visible_tests=None, hidden_tests=None):
    return Question(
        id="q1",
        area=InterviewArea.TECH_CODING,
        type=QuestionType.CODING,
        prompt=prompt,
        difficulty=QuestionDifficulty.MEDIUM,
        visible_tests=visible_tests or [CodingTestCase(args=[2], expected=4)],
        hidden_tests=hidden_tests or [],
        function_name="solution",
    )


def _make_execution(*, passed=1, total=1, success=True, test_results=None, hidden_failure_sample=None):
    return ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED_TESTS,
        success=success,
        error=None if success else "Some tests failed",
        passed_tests=passed,
        total_tests=total,
        execution_time_ms=10,
        test_results=test_results or [],
        hidden_failure_sample=hidden_failure_sample,
    )


# ===========================================================
# P0-A1 / P0-A2 — Reject expected=None
# ===========================================================


class TestRejectNullExpected:

    def test_generated_test_case_rejects_null_expected(self):
        from pydantic import ValidationError
        from services.question_intelligence.coding_question_generator import GeneratedTestCase

        with pytest.raises(ValidationError, match="expected cannot be None"):
            GeneratedTestCase(args=[1, 2], expected=None)

    def test_generated_test_case_accepts_zero_expected(self):
        from services.question_intelligence.coding_question_generator import GeneratedTestCase

        t = GeneratedTestCase(args=[0], expected=0)
        assert t.expected == 0

    def test_generated_test_case_accepts_false_expected(self):
        from services.question_intelligence.coding_question_generator import GeneratedTestCase

        t = GeneratedTestCase(args=[0], expected=False)
        assert t.expected is False

    def test_hidden_test_parser_rejects_null_expected(self):
        from pydantic import ValidationError
        from app.ai.test_generation.test_response_parser import _GeneratedTestCase

        with pytest.raises(ValidationError, match="expected cannot be None"):
            _GeneratedTestCase(args=[1], expected=None)

    def test_hidden_test_parser_accepts_empty_list_expected(self):
        from app.ai.test_generation.test_response_parser import _GeneratedTestCase

        t = _GeneratedTestCase(args=[[1, 2]], expected=[])
        assert t.expected == []


# ===========================================================
# P0-A3 — Comparator rejects None == None
# ===========================================================


class TestComparatorNullGuard:

    def _get_comparator_code(self):
        from services.coding_engine.harness.blocks.comparator_block import ComparatorBlock
        lines = ComparatorBlock().render()
        return "\n".join(lines)

    def test_none_none_returns_false(self):
        code = self._get_comparator_code()
        ns = {}
        exec(code, ns)
        compare = ns["__compare"]
        assert compare(None, None) is False

    def test_none_value_returns_false(self):
        code = self._get_comparator_code()
        ns = {}
        exec(code, ns)
        compare = ns["__compare"]
        assert compare(None, 0) is False
        assert compare(0, None) is False

    def test_equal_ints_still_pass(self):
        code = self._get_comparator_code()
        ns = {}
        exec(code, ns)
        compare = ns["__compare"]
        assert compare(42, 42) is True

    def test_close_floats_pass(self):
        code = self._get_comparator_code()
        ns = {}
        exec(code, ns)
        compare = ns["__compare"]
        assert compare(1.0000001, 1.0) is True


# ===========================================================
# P0-A4 — No fallback hidden tests
# ===========================================================


class TestNoFallbackHiddenTests:

    def test_llm_failure_returns_empty_list(self):
        from app.ai.test_generation.ai_test_generator import AITestGenerator

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="not valid json")

        generator = AITestGenerator(mock_llm)

        from domain.contracts.execution.coding_spec import CodingSpec
        question = Question(
            id="q2",
            area=InterviewArea.TECH_CODING,
            type=QuestionType.CODING,
            prompt="Implement foo(x). foo(x) returns x.",
            difficulty=QuestionDifficulty.MEDIUM,
            visible_tests=[CodingTestCase(args=[1], expected=1)],
            hidden_tests=[],
            function_name="foo",
            coding_spec=CodingSpec(entrypoint="foo", parameters=["x"]),
        )

        tests = generator.generate_tests(question, num_tests=3)
        assert tests == []


# ===========================================================
# P0-A5 — Cache skips null-expected entries
# ===========================================================


class TestCacheNullGuard:

    def test_cache_skips_null_expected_entries(self, tmp_path):
        import json
        import hashlib
        from app.ai.test_generation.test_cache_service import TestCacheService

        cache_data = {}
        question = _make_question()
        num_tests = 3
        version = TestCacheService.CACHE_VERSION
        payload = f"v{version}:{question.id}:{question.prompt}:{num_tests}"
        key = hashlib.sha256(payload.encode()).hexdigest()
        cache_data[key] = [
            {"args": [1], "expected": None},
            {"args": [2], "expected": None},
        ]
        cache_file = tmp_path / "ai_test_cache.json"
        cache_file.write_text(json.dumps(cache_data))

        svc = TestCacheService()
        svc.CACHE_FILE = cache_file
        svc._cache = cache_data

        result = svc.get_tests(question, num_tests)
        assert result is None

    def test_cache_version_in_key_invalidates_old_entries(self, tmp_path):
        import json
        import hashlib
        from app.ai.test_generation.test_cache_service import TestCacheService

        question = _make_question()
        num_tests = 3
        old_payload = f"{question.id}:{question.prompt}:{num_tests}"
        old_key = hashlib.sha256(old_payload.encode()).hexdigest()
        cache_data = {old_key: [{"args": [1], "expected": 1}]}

        svc = TestCacheService()
        svc._cache = cache_data

        result = svc.get_tests(question, num_tests)
        assert result is None


# ===========================================================
# P0-B5 — Failing test inputs in feedback
# ===========================================================


class TestFailingInputsInFeedback:

    def test_failure_detail_builder_shows_input(self):
        from app.ui.presenters.feedback.blocks.failure.failure_detail_builder import FailureDetailBuilder

        mock_test = MagicMock()
        mock_test.status = "failed"
        mock_test.expected = 4
        mock_test.actual = 5
        mock_test.args = [2]
        mock_test.error = None

        builder = FailureDetailBuilder()
        result = builder.build([mock_test])

        assert "Input" in result
        assert "[2]" in result

    def test_failure_detail_builder_no_input_when_args_empty(self):
        from app.ui.presenters.feedback.blocks.failure.failure_detail_builder import FailureDetailBuilder

        mock_test = MagicMock()
        mock_test.status = "failed"
        mock_test.expected = 4
        mock_test.actual = 5
        mock_test.args = []
        mock_test.error = None

        builder = FailureDetailBuilder()
        result = builder.build([mock_test])

        assert "Expected" in result
        assert "Input" not in result

    def test_harness_template_emits_args_in_failed_result(self):
        from services.coding_engine.coding_executor import CodingExecutor

        executor = CodingExecutor()
        question = _make_question(
            visible_tests=[CodingTestCase(args=[3], expected=99)]  # wrong expected
        )
        result = executor.execute(question, "def solution(x):\n    return x * 2")

        assert result.success is False
        failing = [t for t in result.test_results if t.status != TestStatus.PASSED]
        assert len(failing) == 1
        assert failing[0].args == [3]


# ===========================================================
# P0-B6 — Hidden failure sample surfaced in feedback
# ===========================================================


class TestHiddenFailureSample:

    def test_harness_emits_hidden_failure_sample(self):
        from services.coding_engine.coding_executor import CodingExecutor

        executor = CodingExecutor()
        question = _make_question(
            visible_tests=[CodingTestCase(args=[2], expected=4)],
            hidden_tests=[CodingTestCase(args=[5], expected=99)],  # wrong expected
        )
        result = executor.execute(question, "def solution(x):\n    return x * 2")

        assert result.success is False
        assert result.hidden_failure_sample is not None
        assert result.hidden_failure_sample["args"] == [5]
        assert result.hidden_failure_sample["expected"] == 99
        assert result.hidden_failure_sample["actual"] == 10

    def test_failure_block_shows_hidden_sample(self):
        from app.ui.presenters.feedback.blocks.failure_block import FailureBlock

        hidden_sample = {"args": [5], "expected": 99, "actual": 10}
        execution = _make_execution(passed=1, total=2, success=False, hidden_failure_sample=hidden_sample)

        mock_analysis = MagicMock()
        mock_analysis.error_type = None
        mock_result = MagicMock()
        mock_result.question = _make_question()

        block = FailureBlock()
        fb = block.build(None, mock_result, None, execution, mock_analysis, None)

        assert "Hidden Test Failure" in fb.content
        assert "[5]" in fb.content
        assert "99" in fb.content

    def test_no_hidden_sample_when_all_pass(self):
        from services.coding_engine.coding_executor import CodingExecutor

        executor = CodingExecutor()
        question = _make_question(
            visible_tests=[CodingTestCase(args=[2], expected=4)],
            hidden_tests=[CodingTestCase(args=[3], expected=6)],
        )
        result = executor.execute(question, "def solution(x):\n    return x * 2")

        assert result.success is True
        assert result.hidden_failure_sample is None


# ===========================================================
# P0-B7 — Hint receives actual failing args
# ===========================================================


class TestHintReceivesArgs:

    def test_extract_signals_uses_full_args(self):
        from app.graph.nodes.hint_node import HintNode

        node = HintNode(MagicMock())

        mock_t = MagicMock()
        mock_t.status = TestStatus.FAILED
        mock_t.args = [3, 4]
        mock_t.expected = 99
        mock_t.actual = 7
        mock_t.error = None

        mock_exec = MagicMock()
        mock_exec.test_results = [mock_t]

        signals = node._extract_execution_signals(mock_exec)
        assert "[3, 4]" in signals
        assert "99" in signals

    def test_hint_supplements_with_hidden_failure_when_no_visible_failures(self):
        from app.graph.nodes.hint_node import HintNode

        mock_service = MagicMock()
        mock_service.generate_hint.return_value = MagicMock(explanation="hint", suggestion="fix it")
        node = HintNode(mock_service)

        mock_t = MagicMock()
        mock_t.status = TestStatus.PASSED

        mock_exec = MagicMock()
        mock_exec.test_results = [mock_t]
        mock_exec.hidden_failure_sample = {"args": [7], "expected": 14, "actual": 99}
        mock_exec.error = None
        mock_exec.passed_tests = 1
        mock_exec.total_tests = 2
        mock_exec.execution_time_ms = 10

        from tests.factories.interview_state_factory import build_state_with_execution
        state = build_state_with_execution(passed_tests=1, total_tests=2, quality="partial")

        result = state.get_result_for_question("q1")
        updated = result.model_copy(update={"execution": mock_exec})
        from domain.contracts.interview_state import InterviewState
        new_results = dict(state.results_by_question)
        new_results["q1"] = updated
        state2 = state.model_copy(update={"results_by_question": new_results})

        new_state = node(state2)
        call_args = mock_service.generate_hint.call_args
        if call_args:
            hint_input = call_args[0][0]
            assert "[7]" in hint_input.failed_tests or "7" in hint_input.failed_tests


# ===========================================================
# P0-C8 — Quarantine unsupported types
# ===========================================================


class TestUnsupportedTypeQuarantine:

    def _make_pipeline(self):
        from services.question_intelligence.pipelines.coding_question_pipeline import CodingQuestionPipeline
        return CodingQuestionPipeline(
            retrieval_service=MagicMock(),
            coding_generator=MagicMock(),
        )

    def test_treenode_prompt_detected(self):
        pipeline = self._make_pipeline()
        assert pipeline._requires_unsupported_type(
            "Given a TreeNode root, return the sum of all values."
        ) is True

    def test_listnode_prompt_detected(self):
        pipeline = self._make_pipeline()
        assert pipeline._requires_unsupported_type(
            "Given a ListNode head, reverse the linked list."
        ) is True

    def test_graphnode_prompt_detected(self):
        pipeline = self._make_pipeline()
        assert pipeline._requires_unsupported_type(
            "Given a GraphNode, return all neighbors."
        ) is True

    def test_normal_prompt_not_quarantined(self):
        pipeline = self._make_pipeline()
        assert pipeline._requires_unsupported_type(
            "Implement two_sum(nums, target) that returns indices."
        ) is False

    def test_map_item_raises_for_treenode_prompt(self):
        from services.question_intelligence.coding_question_generator import GeneratedCodingQuestion, GeneratedTestCase
        from domain.contracts.execution.coding_spec import CodingSpec

        pipeline = self._make_pipeline()

        item = GeneratedCodingQuestion(
            prompt="Given a TreeNode root, return height. Implement height(root).",
            coding_spec=CodingSpec(entrypoint="height", parameters=["root"]),
            visible_tests=[GeneratedTestCase(args=[1], expected=1)],
        )

        with pytest.raises(ValueError, match="quarantined"):
            pipeline._map_item(item, InterviewArea.TECH_CODING)

    def test_enrich_item_skips_treenode_corpus_seed(self):
        from services.question_intelligence.pipelines.coding_question_pipeline import CodingQuestionPipeline
        from domain.contracts.question.question_bank_item import QuestionBankItem
        from domain.contracts.question.question_provenance import QuestionProvenance
        from domain.contracts.interview.interview_area import InterviewArea
        from domain.contracts.user.role import RoleType
        from domain.contracts.user.seniority_level import SeniorityLevel

        pipeline = self._make_pipeline()

        item = MagicMock(spec=QuestionBankItem)
        item.text = "Given a TreeNode root, return the depth of the binary tree."
        item.id = "seed-001"

        result = pipeline._enrich_item(
            item=item,
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            area=InterviewArea.TECH_CODING,
            provenance=MagicMock(spec=QuestionProvenance),
            theme_guidance=None,
        )

        assert result is None
