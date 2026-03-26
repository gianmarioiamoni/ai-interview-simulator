# app/graph/nodes/execution_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from services.execution_engine import ExecutionEngine


class ExecutionNode:

    def __init__(self, execution_engine: ExecutionEngine) -> None:
        self._execution_engine = execution_engine

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.last_answer

        # Safety
        if question is None or answer is None:
            return state

        # ✅ Correct enum type
        if question.type not in (QuestionType.CODING, QuestionType.DATABASE):
            return state

        try:
            # ✅ FIX: pass string, not object
            result = self._execution_engine.execute(
                question=question,
                user_answer=answer.content,
            )

            # ⚠️ Important protection
            if result is None:
                return state

            # ✅ Ensure semantic consistency
            if getattr(result, "question_id", None) is None:
                try:
                    result = result.model_copy(update={"question_id": question.id})
                except Exception:
                    result.question_id = question.id  # fallback simple

            new_state = state.model_copy(deep=True)
            new_state.register_execution(result)

            return new_state

        except Exception:
            return state  # fallback simple (for now)
