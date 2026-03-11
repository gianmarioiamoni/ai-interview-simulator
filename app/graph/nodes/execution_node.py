# app/graph/nodes/execution_node.py

from domain.contracts.interview_state import InterviewState
from services.execution_engine import ExecutionEngine


engine = ExecutionEngine()


def execution_node(state: InterviewState) -> InterviewState:

    if not state.answers:
        return state

    last_answer = state.answers[-1]

    question = next(
        (q for q in state.questions if q.id == last_answer.question_id),
        None,
    )

    if question is None:
        return state

    if question.type not in ["coding", "database"]:
        return state

    result = engine.execute(
        question,
        last_answer.content,
    )

    state.execution_results.append(result)

    return state
