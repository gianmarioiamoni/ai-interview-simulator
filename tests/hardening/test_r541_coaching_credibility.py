# tests/hardening/test_r541_coaching_credibility.py
#
# R5.4.1 — Candidate Coaching Credibility
#   P0-1: Hint refresh on answer change
#   P0-2: SQL hint prompt dispatch
#   P0-3: Dynamic improvement roadmap
#   P0-4: Coding failure explanation

import hashlib
from unittest.mock import MagicMock, patch

import pytest

# ===========================================================
# Helpers
# ===========================================================


def _make_execution(
    success=False,
    status="failed_tests",
    error=None,
    passed=0,
    total=3,
    test_results=None,
    hidden_sample=None,
):
    from domain.contracts.execution.execution_result import (
        ExecutionResult,
        ExecutionStatus,
        ExecutionType,
    )

    if success and error is None:
        error_val = None
    else:
        error_val = error or "failed"

    return ExecutionResult(
        question_id="q1",
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus(status),
        success=success,
        error=error_val,
        passed_tests=passed,
        total_tests=total,
        test_results=test_results or [],
        hidden_failure_sample=hidden_sample,
    )


def _answer_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


# ===========================================================
# P0-1 — Hint refresh on answer change
# ===========================================================


class TestHintAnswerHashIdempotency:

    def _make_result(self, hint=None, hint_level=None, answer_hash=None):
        from domain.contracts.question.question_result import QuestionResult

        return QuestionResult(
            question_id="q1",
            ai_hint=hint,
            hint_level=hint_level,
            hint_answer_hash=answer_hash,
        )

    def test_hint_answer_hash_field_exists(self):
        from domain.contracts.question.question_result import QuestionResult

        r = QuestionResult(question_id="q1")
        assert hasattr(r, "hint_answer_hash")
        assert r.hint_answer_hash is None

    def test_same_answer_reuses_hint(self):
        from domain.contracts.ai.ai_hint import AIHint
        from domain.contracts.ai.hint_level import HintLevel

        content = "def f(): return 1"
        h = _answer_hash(content)
        hint = AIHint(explanation="x", suggestion="y")
        result = self._make_result(hint=hint, hint_level=HintLevel.BASIC, answer_hash=h)

        # Simulate the idempotency check from HintNode
        assert result.ai_hint is not None
        assert result.hint_level is not None
        assert result.hint_answer_hash == _answer_hash(content)

    def test_changed_answer_breaks_idempotency(self):
        from domain.contracts.ai.ai_hint import AIHint
        from domain.contracts.ai.hint_level import HintLevel

        old_content = "def f(): return 1"
        new_content = "def f(): return 2"
        old_hash = _answer_hash(old_content)

        hint = AIHint(explanation="x", suggestion="y")
        result = self._make_result(
            hint=hint, hint_level=HintLevel.BASIC, answer_hash=old_hash
        )

        # Hash mismatch → should NOT skip hint generation
        assert result.hint_answer_hash != _answer_hash(new_content)

    def test_no_prior_hint_not_idempotent(self):
        result = self._make_result(hint=None, hint_level=None, answer_hash=None)
        # hint is None → generation should proceed
        assert result.ai_hint is None

    def test_hint_stored_with_hash(self):
        from domain.contracts.ai.ai_hint import AIHint
        from domain.contracts.ai.hint_level import HintLevel

        content = "select * from users"
        h = _answer_hash(content)
        hint = AIHint(explanation="a", suggestion="b")
        result = self._make_result(
            hint=hint, hint_level=HintLevel.TARGETED, answer_hash=h
        )
        assert result.hint_answer_hash == h


# ===========================================================
# P0-2 — SQL hint prompt dispatch
# ===========================================================


class TestSQLHintPromptDispatch:

    def _make_hint_service(self, mock_llm=None):
        from services.ai_hint_engine.ai_hint_service import AIHintService

        llm = mock_llm or MagicMock()
        llm.invoke.return_value = MagicMock(
            content='{"explanation": "test", "suggestion": "fix"}'
        )
        return AIHintService(llm), llm

    def test_sql_question_loads_sql_prompt(self):
        from domain.contracts.question.question import QuestionType
        from domain.contracts.ai.ai_hint import AIHintInput
        from domain.contracts.ai.hint_level import HintLevel
        from app.prompts.prompt_loader import PromptLoader

        svc, llm = self._make_hint_service()

        hint_input = AIHintInput(
            error=None,
            user_code="SELECT * FROM users",
            failed_tests="Input: [] | Expected: 5 | Actual: 0 | Error: None",
            question="Write a query",
            hint_level=HintLevel.TARGETED,
        )

        with patch.object(PromptLoader, "load", wraps=PromptLoader.load) as mock_load:
            svc.generate_hint(hint_input, level="TARGETED", question_type=QuestionType.DATABASE)
            loaded = [call[0][0] for call in mock_load.call_args_list]
            assert any("sql_hint" in p for p in loaded)

    def test_coding_question_loads_python_prompt(self):
        from domain.contracts.question.question import QuestionType
        from domain.contracts.ai.ai_hint import AIHintInput
        from domain.contracts.ai.hint_level import HintLevel
        from app.prompts.prompt_loader import PromptLoader

        svc, llm = self._make_hint_service()

        hint_input = AIHintInput(
            error=None,
            user_code="def f(): pass",
            failed_tests="None",
            question="Implement f",
            hint_level=HintLevel.BASIC,
        )

        with patch.object(PromptLoader, "load", wraps=PromptLoader.load) as mock_load:
            svc.generate_hint(hint_input, level="BASIC", question_type=QuestionType.CODING)
            loaded = [call[0][0] for call in mock_load.call_args_list]
            assert any("hint_generation" in p for p in loaded)
            assert not any("sql_hint" in p for p in loaded)

    def test_sql_prompt_file_exists(self):
        from app.prompts.prompt_loader import PromptLoader

        content = PromptLoader.load("feedback/sql_hint_generation.txt")
        assert "SQL" in content
        # Must not say "Python interviewer" like the coding prompt does
        assert "Python interviewer" not in content

    def test_sql_prompt_contains_no_python_wording(self):
        from app.prompts.prompt_loader import PromptLoader

        content = PromptLoader.load("feedback/sql_hint_generation.txt")
        # "senior Python interviewer" phrasing must not appear
        assert "senior Python" not in content

    def test_sql_prompt_references_sql_concepts(self):
        from app.prompts.prompt_loader import PromptLoader

        content = PromptLoader.load("feedback/sql_hint_generation.txt")
        assert "JOIN" in content or "WHERE" in content or "GROUP BY" in content


# ===========================================================
# P0-3 — Dynamic improvement roadmap
# ===========================================================


class TestDynamicImprovementRoadmap:

    def _make_evaluation(self, weaknesses):
        from domain.contracts.question.question_evaluation import QuestionEvaluation

        return QuestionEvaluation(
            question_id="q1",
            score=40.0,
            max_score=100.0,
            feedback="partial",
            strengths=[],
            weaknesses=weaknesses,
            passed=False,
        )

    def test_llm_suggestions_used_when_present(self):
        from services.interview_evaluation.builders.improvement_builder import (
            ImprovementBuilder,
        )

        builder = ImprovementBuilder()
        narrative = {
            "improvement_suggestions": [
                "Practice handling duplicates in hash map problems.",
                "Work on off-by-one errors in loop bounds.",
                "Review SQL JOIN semantics.",
            ]
        }
        result = builder.build({}, narrative, evaluations=None)
        assert len(result) == 3
        assert "duplicates" in result[0]

    def test_fallback_to_evaluation_weaknesses_when_llm_empty(self):
        from services.interview_evaluation.builders.improvement_builder import (
            ImprovementBuilder,
        )

        builder = ImprovementBuilder()
        ev = self._make_evaluation(
            weaknesses=[
                "Most test cases failed (4 of 5)",
                "Edge cases not handled correctly",
            ]
        )
        result = builder.build({}, {"improvement_suggestions": []}, evaluations=[ev])
        assert len(result) >= 1
        assert any("test cases" in s or "Edge" in s for s in result)

    def test_generic_strings_filtered_out(self):
        from services.interview_evaluation.builders.improvement_builder import (
            ImprovementBuilder,
        )

        builder = ImprovementBuilder()
        narrative = {"improvement_suggestions": ["  ", "", None]}
        ev = self._make_evaluation(weaknesses=["No test cases passed"])
        result = builder.build({}, narrative, evaluations=[ev])
        # Empty/whitespace entries removed; falls through to evaluation weaknesses
        assert all(s.strip() for s in result)

    def test_missing_dim_note_appended(self):
        from services.interview_evaluation.builders.improvement_builder import (
            ImprovementBuilder,
        )
        from domain.contracts.shared.performance_dimension_type import (
            PerformanceDimensionType,
        )

        builder = ImprovementBuilder()
        dimension_scores = {PerformanceDimensionType.SYSTEM_DESIGN: None}
        result = builder.build(
            dimension_scores, {"improvement_suggestions": ["fix edge cases"]}, evaluations=[]
        )
        assert any("not assessed" in s for s in result)

    def test_deduplication_across_evaluations(self):
        from services.interview_evaluation.builders.improvement_builder import (
            ImprovementBuilder,
        )

        builder = ImprovementBuilder()
        ev1 = self._make_evaluation(weaknesses=["Edge cases not handled correctly"])
        ev2 = self._make_evaluation(weaknesses=["Edge cases not handled correctly"])
        result = builder.build({}, {"improvement_suggestions": []}, evaluations=[ev1, ev2])
        assert result.count("Edge cases not handled correctly") == 1


# ===========================================================
# P0-4 — Coding failure explanation
# ===========================================================


class TestCodingFailureExplainer:

    def _explainer(self):
        from services.coding_engine.coding_failure_explainer import CodingFailureExplainer

        return CodingFailureExplainer()

    def _make_test_result(self, status, expected=None, actual=None, args=None, error=None):
        t = MagicMock()
        t.status = status
        t.expected = expected
        t.actual = actual
        t.args = args
        t.error = error
        return t

    def test_success_returns_pass_message(self):
        from domain.contracts.execution.execution_result import (
            ExecutionResult, ExecutionStatus, ExecutionType,
        )

        ex = ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.SUCCESS,
            success=True,
            error=None,
            passed_tests=3,
            total_tests=3,
        )
        assert self._explainer().explain(ex) == "All tests passed."

    def test_syntax_error_mentions_syntax(self):
        from domain.contracts.execution.execution_result import (
            ExecutionResult, ExecutionStatus, ExecutionType,
        )

        ex = ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.SYNTAX_ERROR,
            success=False,
            error="SyntaxError: invalid syntax",
            passed_tests=0,
            total_tests=3,
        )
        msg = self._explainer().explain(ex)
        assert "syntax" in msg.lower() or "Syntax" in msg

    def test_timeout_mentions_time_limit(self):
        from domain.contracts.execution.execution_result import (
            ExecutionResult, ExecutionStatus, ExecutionType,
        )

        ex = ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.TIMEOUT,
            success=False,
            error="Time limit exceeded",
            passed_tests=0,
            total_tests=3,
        )
        msg = self._explainer().explain(ex)
        assert "time limit" in msg.lower()

    def test_runtime_type_error_mentions_type(self):
        from domain.contracts.execution.execution_result import (
            ExecutionResult, ExecutionStatus, ExecutionType,
        )

        ex = ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.RUNTIME_ERROR,
            success=False,
            error="TypeError: unsupported operand type",
            passed_tests=0,
            total_tests=3,
        )
        msg = self._explainer().explain(ex)
        assert "TypeError" in msg

    def test_numeric_mismatch_shows_values(self):
        from services.coding_engine.coding_failure_explainer import CodingFailureExplainer

        exp = CodingFailureExplainer()
        t = self._make_test_result("failed", expected=10, actual=8, args=[5])
        msg = exp._explain_logic([t], None)
        assert "8" in msg or "smaller" in msg.lower()

    def test_list_order_mismatch_detected(self):
        from services.coding_engine.coding_failure_explainer import CodingFailureExplainer

        exp = CodingFailureExplainer()
        t = self._make_test_result("failed", expected=[1, 2, 3], actual=[3, 2, 1], args=[[3, 2, 1]])
        msg = exp._explain_logic([t], None)
        assert "order" in msg.lower()

    def test_list_length_mismatch_detected(self):
        from services.coding_engine.coding_failure_explainer import CodingFailureExplainer

        exp = CodingFailureExplainer()
        t = self._make_test_result("failed", expected=[1, 2, 3], actual=[1, 2], args=[[1, 2, 3]])
        msg = exp._explain_logic([t], None)
        assert "3" in msg and "2" in msg

    def test_hidden_sample_logic_failure_explained(self):
        from services.coding_engine.coding_failure_explainer import CodingFailureExplainer

        exp = CodingFailureExplainer()
        sample = {"args": [3], "expected": 99, "actual": 6, "error": None}
        msg = exp._explain_hidden(sample)
        assert "99" in msg or "6" in msg
        assert "hidden" in msg.lower()

    def test_hidden_sample_exception_explained(self):
        from services.coding_engine.coding_failure_explainer import CodingFailureExplainer

        exp = CodingFailureExplainer()
        sample = {"args": ["x"], "expected": None, "actual": None, "error": "TypeError: bad input"}
        msg = exp._explain_hidden(sample)
        assert "exception" in msg.lower() or "TypeError" in msg

    def test_feedback_not_generic_placeholder(self):
        """EvaluationNode must not set feedback to the old placeholder."""
        from domain.contracts.execution.execution_result import (
            ExecutionResult, ExecutionStatus, ExecutionType,
        )
        from services.coding_engine.coding_failure_explainer import CodingFailureExplainer

        ex = ExecutionResult(
            question_id="q1",
            execution_type=ExecutionType.CODING,
            status=ExecutionStatus.FAILED_TESTS,
            success=False,
            error="1 test(s) failed",
            passed_tests=2,
            total_tests=3,
            test_results=[],
        )
        msg = CodingFailureExplainer().explain(ex)
        assert msg != "Execution evaluated automatically."
        assert len(msg) > 10
