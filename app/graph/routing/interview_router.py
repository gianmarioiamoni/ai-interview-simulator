# app/graph/routing/interview_router.py

from domain.contracts.interview_state import InterviewState


def route_next_step(state: InterviewState):

    if not state.has_questions:
        return "end"

    if state.is_last_question:
        return "end"

    return "advance"
