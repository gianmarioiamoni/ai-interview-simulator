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

    # ---------------------------------------------------------
    # No question → terminate
    # ---------------------------------------------------------

    if q is None:
        return END

    # ---------------------------------------------------------
    # No answer yet → UI must wait
    # ---------------------------------------------------------

    if state.last_answer is None:
        return END

    # ---------------------------------------------------------
    # Ensure the answer refers to the current question
    # ---------------------------------------------------------

    if state.last_answer.question_id != q.id:
        return END

    # ---------------------------------------------------------
    # Ensure processing completed
    # ---------------------------------------------------------

    if not state.is_question_processed(q):
        return END

    # ---------------------------------------------------------
    # LAST QUESTION → finish interview
    # ---------------------------------------------------------

    if state.is_last_question:

        print("INTERVIEW COMPLETED")

        state.progress = state.progress.COMPLETED

        return END

    # ---------------------------------------------------------
    # Otherwise move to next question
    # ---------------------------------------------------------

    print("ADVANCING QUESTION")

    return "advance"
