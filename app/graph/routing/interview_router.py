# app/graph/routing/interview_router.py

from langgraph.graph import END
from domain.contracts.interview_state import InterviewState


def route_next_step(state: InterviewState):

    state.advance_question()

    if state.is_completed:
        return END

    return "question"
