# app/graph/routing/interview_router.py

from langgraph.graph import END
from domain.contracts.interview_state import InterviewState


def route_next_step(state: InterviewState):

    # No answer yet → stop graph and wait for user
    if state.last_answer is None:
        return END

    # Last question completed
    if state.is_last_question:
        return END

    # Next question
    return "advance"
