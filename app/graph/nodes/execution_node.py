# app/graph/nodes/execution_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType
from domain.contracts.shared.action_type import ActionType
from domain.contracts.execution.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
)
from domain.contracts.question.question_result import QuestionResult

from services.execution_engine import ExecutionEngine

from app.ui.constants.loader_steps import LoaderStep
from app.core.logger import get_logger

logger = get_logger(__name__)


class ExecutionNode:

    def __init__(self, execution_engine: ExecutionEngine) -> None:
        self._execution_engine = execution_engine

    def __call__(self, state: InterviewState) -> InterviewState:

        if state.intent == ActionType.GENERATE_REPORT:
            return state

        question = state.current_question
        answer = state.get_latest_answer_for_question(question.id)
        

        # ---------------------------------------------------------
        # Safety guards
        # ---------------------------------------------------------

        if question is None or answer is None:
            return state

        if question.type not in (QuestionType.CODING, QuestionType.DATABASE):
            return state

        existing = state.get_result_for_question(question.id)
        if existing and existing.execution:
            return state

        # ---------------------------------------------------------
        # Set loader step
        # ---------------------------------------------------------
        working_state = state.model_copy(
            update={"current_step": LoaderStep.RUNNING_EXECUTION}
        )

        # ---------------------------------------------------------
        # Execution
        # ---------------------------------------------------------

        try:
            execution_result = self._execution_engine.execute(
                question=question,
                user_answer=answer.content,
            )

            if execution_result is None:
                return working_state

            if getattr(execution_result, "question_id", None) is None:
                try:
                    execution_result = execution_result.model_copy(
                        update={"question_id": question.id}
                    )
                except Exception:
                    execution_result.question_id = question.id

        except Exception as exc:
            logger.error("Execution failed for question %s: %s", question.id, exc)

            error_result = ExecutionResult(
                question_id=question.id,
                execution_type=(
                    ExecutionType.DATABASE
                    if question.type == QuestionType.DATABASE
                    else ExecutionType.CODING
                ),
                status=ExecutionStatus.INTERNAL_ERROR,
                success=False,
                output="",
                error=f"Execution service unavailable: {exc}",
                passed_tests=0,
                total_tests=0,
                execution_time_ms=0,
                test_results=[],
            )

            new_results = dict(state.results_by_question)
            existing_result = new_results.get(question.id)
            if existing_result is None:
                existing_result = QuestionResult(
                    question_id=question.id,
                    question=question,
                )
            existing_result = existing_result.model_copy(update={"execution": error_result})
            new_results[question.id] = existing_result

            return working_state.model_copy(update={"results_by_question": new_results})

        # ---------------------------------------------------------
        # State update (IMMUTABLE SAFE)
        # ---------------------------------------------------------

        new_results = dict(state.results_by_question)

        result = new_results.get(question.id)

        if result is None:
            result = QuestionResult(
                question_id=question.id,
                question=question,
            )
        else:
            if result.question is None:
                result = result.model_copy(update={"question": question})

        result = result.model_copy(update={"execution": execution_result})

        new_results[question.id] = result

        return working_state.model_copy(
            update={
                "results_by_question": new_results,
            }
        )
