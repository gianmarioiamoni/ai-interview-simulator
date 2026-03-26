# app/graph/nodes/execution_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.execution_result import ExecutionResult
from services.execution_engine import ExecutionEngine


class ExecutionNode:

    def __init__(self, execution_engine: ExecutionEngine) -> None:
        self._execution_engine = execution_engine

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.last_answer

        if question is None or answer is None:
            return state

        if question.type not in ["coding", "database"]:
            return state

        try:
            result = self._execution_engine.execute(
                question=question,
                answer=answer,
            )

            new_state = state.model_copy(deep=True)
            new_state.register_execution(result)

            return new_state

        except Exception:
            return state  # fallback semplice (per ora)
