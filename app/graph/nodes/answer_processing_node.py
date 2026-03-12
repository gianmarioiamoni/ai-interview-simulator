# app/graph/nodes/answer_processing_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from services.execution_engine import ExecutionEngine


engine = ExecutionEngine()


def answer_processing_node(state: InterviewState) -> InterviewState:

    question = state.current_question
    answer = state.last_answer

    print("ANSWER PROC:", question.id, question.type)

    if question is None or answer is None:
        return state

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
