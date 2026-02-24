# app/graph/nodes/execution_node.py

from domain.contracts.interview_state import InterviewState
from services.coding_engine.coding_executor import CodingExecutor
from services.sql_engine.sql_executor import SQLExecutor


def execution_node(state: InterviewState) -> InterviewState:
    # No answers yet
    if not state.answers:
        return state

    last_answer = state.answers[-1]

    question = next(
        (q for q in state.questions if q.id == last_answer.question_id), None
    )

    if question is None:
        return state

    # Only execute for coding or sql
    if question.type == "coding":
        executor = CodingExecutor()
        result = executor.execute(question, last_answer)
        state.execution_results.append(result)

    elif question.type == "sql":
        executor = SQLExecutor()
        result = executor.execute(question, last_answer)
        state.execution_results.append(result)

    return state
