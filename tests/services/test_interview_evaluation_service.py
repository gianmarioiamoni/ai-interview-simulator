# tests/services/test_interview_evaluation_service.py

# Behavioral tests for the CURRENT InterviewEvaluationService architecture:
# deterministic scoring engine + decision engine + signal enrichment,
# with LLM used only for narrative generation (with deterministic fallbacks).
#
# The legacy suite targeted a removed LLM-JSON evaluation contract
# (per_question_evaluations kwarg, JSON retry loops, dimension-set guards)
# and was classified obsolete in Phase 7B-Z.

import pytest

from unittest.mock import Mock

from domain.contracts.execution.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
)
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.user.role import RoleType

from services.interview_evaluation_service import InterviewEvaluationService

from tests.factories.interview_state_factory import build_question


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------


class FakeLLMResponse(str):
    """String response that also exposes .content like provider payloads."""

    @property
    def content(self) -> str:
        return str(self)


def build_llm(summary: str = "Solid performance overall.") -> Mock:
    llm = Mock()
    llm.invoke.return_value = FakeLLMResponse(summary)
    llm.invoke_json.side_effect = ValueError("structured output unavailable")
    return llm


def build_evaluation(qid: str, score: float) -> QuestionEvaluation:
    return QuestionEvaluation(
        question_id=qid,
        score=score,
        max_score=100.0,
        feedback=f"Feedback for {qid}",
        strengths=["clarity"],
        weaknesses=["depth"],
        passed=score >= 60,
    )


def build_execution(qid: str, *, passed_tests: int, total_tests: int) -> ExecutionResult:
    success = total_tests > 0 and passed_tests == total_tests
    return ExecutionResult(
        question_id=qid,
        execution_type=ExecutionType.CODING,
        status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED_TESTS,
        success=success,
        output="",
        error=None if success else "Some tests failed",
        passed_tests=passed_tests,
        total_tests=total_tests,
        execution_time_ms=10,
        test_results=[],
    )


def build_result(
    qid: str,
    *,
    score: float = 80.0,
    with_evaluation: bool = True,
    execution: ExecutionResult | None = None,
) -> QuestionResult:
    return QuestionResult(
        question_id=qid,
        execution=execution,
        evaluation=build_evaluation(qid, score) if with_evaluation else None,
        ai_hint=None,
        hint_level=None,
    )


def evaluate(service: InterviewEvaluationService, results, questions):
    return service.evaluate(
        question_results=results,
        questions=questions,
        interview_type=InterviewType.TECHNICAL,
        role=RoleType.BACKEND_ENGINEER,
    )


# ---------------------------------------------------------
# GUARDS
# ---------------------------------------------------------


def test_evaluate_raises_without_question_results():

    service = InterviewEvaluationService(build_llm())

    with pytest.raises(ValueError, match="without question results"):
        evaluate(service, [], [])


def test_evaluate_raises_without_evaluations():

    service = InterviewEvaluationService(build_llm())

    results = [build_result("q1", with_evaluation=False)]
    questions = [build_question(qid="q1")]

    with pytest.raises(ValueError, match="No question evaluations available"):
        evaluate(service, results, questions)


# ---------------------------------------------------------
# HAPPY PATH
# ---------------------------------------------------------


def test_evaluate_returns_complete_interview_evaluation():

    service = InterviewEvaluationService(build_llm())

    questions = [build_question(qid="q1"), build_question(qid="q2")]
    results = [
        build_result("q1", score=80.0),
        build_result("q2", score=60.0),
    ]

    evaluation = evaluate(service, results, questions)

    assert isinstance(evaluation, InterviewEvaluation)
    assert 0.0 <= evaluation.overall_score <= 100.0
    assert 0.0 <= evaluation.hiring_probability <= 100.0
    assert 0.0 <= evaluation.percentile_rank <= 100.0
    assert evaluation.hire_decision in HireDecision
    assert evaluation.executive_summary.strip()
    assert evaluation.per_question_assessment == [r.evaluation for r in results]
    assert evaluation.dimension_scores
    assert evaluation.weighted_breakdown


def test_overall_score_is_decision_adjusted_and_bounded():

    service = InterviewEvaluationService(build_llm())

    questions = [build_question(qid="q1")]
    results = [build_result("q1", score=100.0)]

    evaluation = evaluate(service, results, questions)

    assert 0.0 <= evaluation.overall_score <= 100.0
    assert evaluation.adjusted_score == evaluation.overall_score
    assert evaluation.raw_score is not None


def test_low_scores_produce_negative_leaning_decision():

    service = InterviewEvaluationService(build_llm())

    questions = [build_question(qid="q1"), build_question(qid="q2")]
    results = [
        build_result("q1", score=5.0),
        build_result("q2", score=10.0),
    ]

    evaluation = evaluate(service, results, questions)

    assert evaluation.hire_decision in (
        HireDecision.NO_HIRE,
        HireDecision.LEAN_NO_HIRE,
    )


# ---------------------------------------------------------
# SIGNAL ENRICHMENT
# ---------------------------------------------------------


def test_dimension_signals_extracted_from_executions():

    service = InterviewEvaluationService(build_llm())

    questions = [build_question(qid="q1")]
    results = [
        build_result(
            "q1",
            score=50.0,
            execution=build_execution("q1", passed_tests=1, total_tests=4),
        )
    ]

    evaluation = evaluate(service, results, questions)

    assert isinstance(evaluation.dimension_signals, dict)

    for key, value in evaluation.dimension_signals.items():
        assert isinstance(key, str)
        assert 0.0 <= value <= 1.0


# ---------------------------------------------------------
# CONFIDENCE
# ---------------------------------------------------------


def test_confidence_within_bounds():

    service = InterviewEvaluationService(build_llm())

    questions = [build_question(qid="q1"), build_question(qid="q2")]
    results = [
        build_result("q1", score=95.0),
        build_result("q2", score=20.0),
    ]

    evaluation = evaluate(service, results, questions)

    assert 0.0 <= evaluation.confidence.base <= 1.0
    assert 0.0 <= evaluation.confidence.final <= 1.0


# ---------------------------------------------------------
# NARRATIVE FALLBACKS
# ---------------------------------------------------------


def test_executive_summary_falls_back_when_llm_returns_empty():

    service = InterviewEvaluationService(build_llm(summary=""))

    questions = [build_question(qid="q1")]
    results = [build_result("q1", score=70.0)]

    evaluation = evaluate(service, results, questions)

    assert evaluation.executive_summary.strip()
    assert "overall score" in evaluation.executive_summary.lower()
