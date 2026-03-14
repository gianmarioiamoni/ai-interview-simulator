# app/graph/routing/interview_router.py

from langgraph.graph import END
from domain.contracts.interview_state import InterviewState


def route_next_step(state: InterviewState):

    q = state.current_question

    print(
        "ROUTER:",
        q.id if q else None,
        "ans:",
        state.last_answer.question_id if state.last_answer else None,
    )

    print("RESULT MAP:", state.results_by_question)

    if q is None:
        return "complete"

    if state.last_answer is None:
        return END

    if state.last_answer.question_id != q.id:
        return END

    if not state.is_question_processed(q):
        return END

    if state.is_last_question:
        print("INTERVIEW COMPLETED")
        return "complete"

    return "advance"
