# app/graph/routing/interview_router.py

from langgraph.graph import END
from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType


def route_next_step(state: InterviewState):

    print(
        "ROUTER:",
        state.current_question.id,
        "ans:",
        state.last_answer.question_id if state.last_answer else None,
        "eval:",
        state.last_evaluation.question_id if state.last_evaluation else None,
        "exec:",
        state.last_execution.question_id if state.last_execution else None,
    )

    q = state.current_question
    if q is None:
        return END

    # nessuna risposta → fermati (UI attende input)
    if state.last_answer is None:
        return END

    # avanzare SOLO se la domanda corrente è stata processata
    if q.type == QuestionType.WRITTEN:
        if state.last_evaluation is None:
            return END
        # protezione: evaluation deve riferirsi alla domanda corrente
        if state.last_evaluation.question_id != q.id:
            return END

    if q.type in (QuestionType.CODING, QuestionType.DATABASE):
        if state.last_execution is None:
            return END
        # protezione: execution deve riferirsi alla domanda corrente
        if state.last_execution.question_id != q.id:
            return END

    # fine intervista
    if state.is_last_question:
        return END

    # avanza UNA sola volta
    return "advance"
