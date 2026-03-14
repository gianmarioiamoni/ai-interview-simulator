# app/graph/routing/interview_router.py

from langgraph.graph import END
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress


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
    # No question
    # ---------------------------------------------------------

    if q is None:
        state.progress = InterviewProgress.COMPLETED
        return END


    # ---------------------------------------------------------
    # Wait for answer
    # ---------------------------------------------------------

    if state.last_answer is None:
        return END

    if state.last_answer.question_id != q.id:
        return END


    # ---------------------------------------------------------
    # Ensure question processed
    # ---------------------------------------------------------

    if not state.is_question_processed(q):
        return END


    # ---------------------------------------------------------
    # Interview finished
    # ---------------------------------------------------------

    if state.is_last_question:

        print("INTERVIEW COMPLETED")

        state.progress = InterviewProgress.COMPLETED

        return END


    # ---------------------------------------------------------
    # Next question
    # ---------------------------------------------------------

    return "advance"
