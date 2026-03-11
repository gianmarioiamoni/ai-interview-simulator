from domain.contracts.interview_state import InterviewState


def route_next_step(state: InterviewState):

    # ---------------------------------------------------------
    # No answer yet → stay on question
    # ---------------------------------------------------------

    if state.last_answer is None:
        return "question"

    # ---------------------------------------------------------
    # Last question completed
    # ---------------------------------------------------------

    if state.is_last_question:
        return "end"

    # ---------------------------------------------------------
    # Go to next question
    # ---------------------------------------------------------

    return "advance"
