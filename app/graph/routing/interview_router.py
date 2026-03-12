# app/graph/routing/interview_router.py

from langgraph.graph import END
from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType


def route_next_step(state: InterviewState):

    question = state.current_question

    if question is None:
        return END

    # ---------------------------------------
    # No answer yet → wait for user
    # ---------------------------------------

    if state.last_answer is None:
        return END

    # ---------------------------------------
    # Written question must produce evaluation
    # ---------------------------------------

    if question.type == QuestionType.WRITTEN:

        if state.last_evaluation is None:
            return END

    # ---------------------------------------
    # Coding / SQL must produce execution result
    # ---------------------------------------

    if question.type in [QuestionType.CODING, QuestionType.DATABASE]:

        if state.last_execution is None:
            return END

    # ---------------------------------------
    # End interview
    # ---------------------------------------

    if state.is_last_question:
        return END

    # ---------------------------------------
    # Advance to next question
    # ---------------------------------------

    return "advance"
