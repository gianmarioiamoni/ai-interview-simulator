# app/graph/nodes/answer_processing_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from services.execution_engine import ExecutionEngine


engine = ExecutionEngine()


def answer_processing_node(state: InterviewState) -> InterviewState:

    question = state.current_question
    answer = state.last_answer

    if question is None or answer is None:
        return state

    print("ANSWER PROC:", question.id, question.type)

    # ---------------------------------------------------------
    # Avoid double execution
    # ---------------------------------------------------------

    existing = state.get_result_for_question(question.id)

    if existing and existing.execution is not None:
        return state

    # ---------------------------------------------------------
    # Execute coding / database
    # ---------------------------------------------------------

    if question.type in [
        QuestionType.CODING,
        QuestionType.DATABASE,
    ]:

        result = engine.execute(
            question,
            answer.content,
        )

        state.register_execution(result)

    return state
