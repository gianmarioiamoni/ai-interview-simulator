# app/ui/state_handlers/submit.py

from domain.contracts.interview_state import InterviewState

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from infrastructure.llm.llm_factory import get_llm


def submit_answer(state: InterviewState, answer: str):

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not state or not state.current_question:
        return build_ui_response_from_state(state)

    # -----------------------------------------------------
    # UPDATE STATE (IMMUTABLE)
    # -----------------------------------------------------

    # ⚠️ adattalo se Answer è un oggetto
    new_answer = {
        "question_id": state.current_question.id,
        "content": answer,
    }

    state = state.model_copy(update={"answers": state.answers + [new_answer]})

    # -----------------------------------------------------
    # USE CASE
    # -----------------------------------------------------

    llm = get_llm()
    use_case = EvaluateAnswerUseCase(llm)

    state = use_case.execute(state)

    return build_ui_response_from_state(state)
