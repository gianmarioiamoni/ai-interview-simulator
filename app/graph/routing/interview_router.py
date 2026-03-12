# app/graph/routing/interview_router.py

from langgraph.graph import END
from domain.contracts.interview_state import InterviewState


def route_next_step(state: InterviewState):

    # ---------------------------------------
    # No answer yet → wait for user
    # ---------------------------------------

    if state.last_answer is None:
        return END

    # ---------------------------------------
    # Answer submitted but not evaluated yet
    # ---------------------------------------

    if state.last_evaluation is None:
        return END

    # ---------------------------------------
    # Interview finished
    # ---------------------------------------

    if state.is_last_question:
        return END

    # ---------------------------------------
    # Move to next question
    # ---------------------------------------

    return "advance"
