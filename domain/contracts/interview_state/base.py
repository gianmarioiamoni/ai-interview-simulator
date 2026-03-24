# app/ui/state_handlers/submit.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.answer import Answer

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from infrastructure.llm.llm_factory import get_llm


def submit_answer(state: InterviewState, answer: str):

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not state or not state.current_question:
        return build_ui_response_from_state(state)

    question_id = state.current_question.id

    # -----------------------------------------------------
    # ATTEMPT CALCULATION
    # -----------------------------------------------------

    attempt = state.attempts_by_question.get(question_id, 0) + 1

    # -----------------------------------------------------
    # BUILD DOMAIN ANSWER
    # -----------------------------------------------------

    new_answer = Answer(
        question_id=question_id,
        content=answer,
        attempt=attempt,
    )

    # -----------------------------------------------------
    # UPDATE STATE (IMMUTABLE)
    # -----------------------------------------------------

    state = state.model_copy(
        update={
            "answers": state.answers + [new_answer],
            "attempts_by_question": {
                **state.attempts_by_question,
                question_id: attempt,
            },
        }
    )

    # -----------------------------------------------------
    # USE CASE
    # -----------------------------------------------------

    llm = get_llm()
    use_case = EvaluateAnswerUseCase(llm)

    state = use_case.execute(state)

    return build_ui_response_from_state(state)
