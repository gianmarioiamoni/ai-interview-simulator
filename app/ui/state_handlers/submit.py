# app/ui/state_handlers/submit.py

from domain.events.answer_submitted_event import AnswerSubmittedEvent
from domain.contracts.interview_state import InterviewState

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.ui.state_handlers.ui_builder import build_ui_response_from_state


def submit_answer(state: InterviewState, answer: str):

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not state or not state.current_question:
        return build_ui_response_from_state(state)

    # -----------------------------------------------------
    # BUILD EVENT
    # -----------------------------------------------------

    event = AnswerSubmittedEvent(
        question_id=state.current_question.id,
        content=answer,
    )

    # -----------------------------------------------------
    # USE CASE (CORE LOGIC)
    # -----------------------------------------------------

    use_case = EvaluateAnswerUseCase()

    state = use_case.execute(state, event)

    return build_ui_response_from_state(state)
