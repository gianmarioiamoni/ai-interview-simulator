# app/graph/nodes/evaluation_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.shared.action_type import ActionType
from domain.contracts.execution.execution_result import ExecutionStatus

from app.ui.dto.builders.dimension_mapper import DimensionMapper
from app.ui.constants.loader_steps import LoaderStep
from app.ui.presenters.feedback.blocks.failure.edge_case_detector import EdgeCaseDetector
from app.ui.presenters.feedback.blocks.test_breakdown.logic_issue_analyzer import LogicIssueAnalyzer
from domain.contracts.feedback.error_type import ErrorType
from infrastructure.config.evaluation import (
    EXECUTION_SLOW_MS,
    CODING_QUALITY_CORRECT_THRESHOLD,
    CODING_QUALITY_PARTIAL_THRESHOLD,
)
from services.coding_engine.coding_failure_explainer import CodingFailureExplainer

_EDGE_CASE_DETECTOR = EdgeCaseDetector()
_LOGIC_ISSUE_ANALYZER = LogicIssueAnalyzer()
_FAILURE_EXPLAINER = CodingFailureExplainer()


def _build_coding_signals(execution) -> tuple[list[str], list[str]]:
    total = execution.total_tests or 0
    passed = execution.passed_tests or 0
    pass_rate = (passed / total) if total > 0 else (1.0 if execution.success else 0.0)
    is_perfect = total > 0 and passed == total
    status = execution.status

    strengths: list[str] = []
    weaknesses: list[str] = []

    # --- STRENGTHS ---

    if is_perfect:
        strengths.append("All test cases passed")

    if status not in (
        ExecutionStatus.RUNTIME_ERROR,
        ExecutionStatus.SYNTAX_ERROR,
        ExecutionStatus.TIMEOUT,
        ExecutionStatus.INTERNAL_ERROR,
    ) and not any(
        hasattr(t, "error") and t.error for t in execution.test_results
    ):
        if status == ExecutionStatus.SUCCESS or pass_rate >= CODING_QUALITY_CORRECT_THRESHOLD / 100:
            strengths.append("No runtime errors detected")

    if (
        execution.execution_time_ms > 0
        and execution.execution_time_ms < EXECUTION_SLOW_MS
        and is_perfect
    ):
        strengths.append("Efficient execution time")

    # --- WEAKNESSES ---

    if status in (ExecutionStatus.RUNTIME_ERROR, ExecutionStatus.SYNTAX_ERROR):
        label = "Syntax error in submitted code" if status == ExecutionStatus.SYNTAX_ERROR else "Runtime error during execution"
        weaknesses.append(label)

    elif status == ExecutionStatus.TIMEOUT:
        weaknesses.append("Solution exceeded time limit")

    if not is_perfect and total > 0:
        failed = total - passed
        if pass_rate == 0.0:
            weaknesses.append("No test cases passed")
        elif pass_rate < CODING_QUALITY_PARTIAL_THRESHOLD / 100:
            weaknesses.append(f"Most test cases failed ({failed} of {total})")
        else:
            weaknesses.append(f"Partial test coverage ({passed} of {total} passed)")

    if _EDGE_CASE_DETECTOR.detect(execution.test_results):
        weaknesses.append("Edge cases not handled correctly")

    return strengths[:3], weaknesses[:3]


def _build_sql_signals(execution) -> tuple[list[str], list[str]]:
    total = execution.total_tests or 0
    passed = execution.passed_tests or 0
    is_perfect = total > 0 and passed == total

    strengths: list[str] = []
    weaknesses: list[str] = []

    # --- STRENGTHS ---

    if is_perfect:
        strengths.append("Correct query logic demonstrated across all tested scenarios")

    has_test_errors = any(
        getattr(t, "status", None) is not None and t.status.value == "error"
        for t in execution.test_results
    )

    if execution.status == ExecutionStatus.SUCCESS and not has_test_errors:
        strengths.append("Query executed successfully without runtime errors")

    # --- WEAKNESSES ---

    for t in execution.test_results:
        if getattr(t, "status", None) is None or t.status.value != "error":
            continue
        error_str = (t.error or "").lower()
        if "syntax error" in error_str:
            label = "SQL syntax issues detected"
        elif "no such table" in error_str or "no such column" in error_str:
            label = "Schema understanding issues detected"
        else:
            label = "SQL execution errors detected"
        if label not in weaknesses:
            weaknesses.append(label)
        break  # one error-class weakness is enough

    if not is_perfect and total > 0:
        for t in execution.test_results:
            if getattr(t, "status", None) is None or t.status.value != "failed":
                continue
            msg = _LOGIC_ISSUE_ANALYZER.infer(t.expected, t.actual, ErrorType.LOGIC)
            if msg and msg not in weaknesses:
                weaknesses.append(msg)
            break  # one logic weakness per question

    if _EDGE_CASE_DETECTOR.detect(execution.test_results):
        label = "Query does not correctly handle empty-result scenarios"
        if label not in weaknesses:
            weaknesses.append(label)

    return strengths[:3], weaknesses[:3]


class EvaluationNode:

    def __call__(self, state: InterviewState) -> InterviewState:

        if state.intent == ActionType.GENERATE_REPORT:
            return state

        working_state = state.model_copy(
            update={"current_step": LoaderStep.ANALYZING}
        )

        question = state.current_question

        if question is None:
            return working_state

        if question.type not in (QuestionType.CODING, QuestionType.DATABASE):
            return working_state

        result = state.get_result_for_question(question.id)

        if result is None or result.execution is None:
            return working_state

        execution = result.execution

        # ---------------------------------------------------------
        # Compute evaluation
        # ---------------------------------------------------------

        if execution.total_tests and execution.total_tests > 0:
            score = (execution.passed_tests / execution.total_tests) * 100
        else:
            score = 100 if execution.success else 0

        if question.type == QuestionType.CODING:
            strengths, weaknesses = _build_coding_signals(execution)
        elif question.type == QuestionType.DATABASE:
            strengths, weaknesses = _build_sql_signals(execution)
        else:
            strengths, weaknesses = [], []

        evaluation = QuestionEvaluation(
            question_id=question.id,
            score=score,
            max_score=100,
            passed=execution.success,
            feedback=_FAILURE_EXPLAINER.explain(execution),
            strengths=strengths,
            weaknesses=weaknesses,
            passed_tests=execution.passed_tests,
            total_tests=execution.total_tests,
            execution_status=execution.status.value,
        )

        # ---------------------------------------------------------
        # DIMENSION SIGNALS UPDATE
        # ---------------------------------------------------------

        dimension_mapper = DimensionMapper()

        error_type = execution.error_type if hasattr(execution, "error_type") else None

        dimension = dimension_mapper.map(error_type, execution)

        current_signals = dict(getattr(state, "dimension_signals", {}) or {})

        if dimension:
            current_signals[dimension] = current_signals.get(dimension, 0) + 1

        # ---------------------------------------------------------
        # STATE UPDATE
        # ---------------------------------------------------------

        new_results = dict(state.results_by_question)

        updated_result = result.model_copy(
            update={
                "evaluation": evaluation,
                "question": result.question or question,
            }
        )

        new_results[question.id] = updated_result

        return working_state.model_copy(
            update={
                "results_by_question": new_results,
                "dimension_signals": current_signals,
            }
        )
