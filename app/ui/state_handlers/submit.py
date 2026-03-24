# app/ui/state_handlers/submit.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.answer import Answer

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from infrastructure.llm.llm_factory import get_llm


def submit_answer(state: InterviewState, answer: str):

    if not state or not state.current_question:
        return build_ui_response_from_state(state)

    question = state.current_question
    question_id = question.id

    # -----------------------------------------------------
    # ATTEMPT (derived)
    # -----------------------------------------------------

    attempt = state.get_attempt_for_question(question_id) + 1

    new_answer = Answer(
        question_id=question_id,
        content=answer,
        attempt=attempt,
    )

    # -----------------------------------------------------
    # DOMAIN METHOD
    # -----------------------------------------------------

    state = state.add_answer(new_answer)

    # -----------------------------------------------------
    # USE CASE
    # -----------------------------------------------------

    llm = get_llm()
    use_case = EvaluateAnswerUseCase(llm)

    state = use_case.execute(state)

    return build_ui_response_from_state(state)
