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

    # ---------------------------------------------------------
    # No question → end
    # ---------------------------------------------------------

    if q is None:
        return END

    # ---------------------------------------------------------
    # No answer yet → UI must wait
    # ---------------------------------------------------------

    if state.last_answer is None:
        return END

    # ---------------------------------------------------------
    # Ensure answer belongs to current question
    # ---------------------------------------------------------

    if state.last_answer.question_id != q.id:
        return END

    # ---------------------------------------------------------
    # Question not processed yet
    # ---------------------------------------------------------

    if not state.is_question_processed(q):
        return END

    # ---------------------------------------------------------
    # Last question → interview completed
    # ---------------------------------------------------------

    if state.is_last_question:
        state.progress = state.progress.COMPLETED
        return END

    # ---------------------------------------------------------
    # Move to next question
    # ---------------------------------------------------------

    return "advance"
