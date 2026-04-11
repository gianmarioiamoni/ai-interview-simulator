# app/graph/nodes/execution_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from services.execution_engine import ExecutionEngine


class ExecutionNode:

    def __init__(self, execution_engine: ExecutionEngine) -> None:
        self._execution_engine = execution_engine

    def __call__(self, state: InterviewState) -> InterviewState:

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
        # Execution
        # ---------------------------------------------------------

        try:
            execution_result = self._execution_engine.execute(
                question=question,
                user_answer=answer.content,
            )

            if execution_result is None:
                return state

            if getattr(execution_result, "question_id", None) is None:
                try:
                    execution_result = execution_result.model_copy(
                        update={"question_id": question.id}
                    )
                except Exception:
                    execution_result.question_id = question.id

        except Exception:
            return state

        # ---------------------------------------------------------
        # State update (IMMUTABLE SAFE)
        # ---------------------------------------------------------

        new_results = dict(state.results_by_question)

        result = new_results.get(question.id)

        if result is None:
            from domain.contracts.question_result import QuestionResult

            result = QuestionResult(
                question_id=question.id,
                question=question,  # 🔥 NEW
            )
        else:
            if result.question is None:
                result = result.model_copy(update={"question": question})

        result = result.model_copy(update={"execution": execution_result})

        new_results[question.id] = result

        return state.model_copy(update={"results_by_question": new_results})
