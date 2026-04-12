# app/graph/nodes/router_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType


def router_node(state: InterviewState) -> str:

    question = state.current_question

    if question is None:
        return "execution"  # safe fallback

    if question.type == QuestionType.WRITTEN:
        return "written"

    return "execution"
