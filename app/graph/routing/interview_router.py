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
    # No question → interview completed
    # ---------------------------------------------------------

    if q is None:
        return "complete"

    # ---------------------------------------------------------
    # No answer submitted → stop
    # ---------------------------------------------------------

    if state.last_answer is None:
        return END

    # ---------------------------------------------------------
    # Wait until evaluation is complete
    # ---------------------------------------------------------

    if not state.is_question_processed(q):
        return END

    # ---------------------------------------------------------
    # After evaluation stop graph
    # UI will decide next step
    # ---------------------------------------------------------

    return END
