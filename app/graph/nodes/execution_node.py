# app/graph/nodes/execution_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.execution_result import ExecutionResult
from services.execution_engine import ExecutionEngine


class ExecutionNode:
    
    # Node responsible for executing the user answer.
    # SRP:
    # - ONLY execute answer
    # - NO evaluation
    # - NO feedback
    # - NO hint

    def __init__(self, execution_engine: ExecutionEngine) -> None:
        self._execution_engine = execution_engine

    def __call__(self, state: InterviewState) -> InterviewState:
        # Execute the user answer if necessary and update the state.

        # Rules:
        # - always produce execution_* fields
        # - never leave fields uninitialized

        question = state.current_question
        answer = state.current_answer

        # 🔒 Safety: valid state
        if question is None or answer is None:
            return state.model_copy(
                update={
                    "execution_result": None,
                    "execution_success": False,
                    "execution_error": "Missing question or answer",
                }
            )

        # 🟡 Case: question not executable (e.g. HR / theoretical)
        if question.type not in ["coding", "database"]:
            return state.model_copy(
                update={
                    "execution_result": None,
                    "execution_success": True,
                    "execution_error": None,
                }
            )

        # 🟢 Case: real execution
        try:
            result: ExecutionResult = self._execution_engine.execute(
                question=question,
                answer=answer,
            )

            return state.model_copy(
                update={
                    "execution_result": result,
                    "execution_success": result.success,
                    "execution_error": None,
                }
            )

        except Exception as e:
            # ⚠️ fallback robust → never crash the graph
            return state.model_copy(
                update={
                    "execution_result": None,
                    "execution_success": False,
                    "execution_error": str(e),
                }
            )
