# domain/contracts/retry.py

from domain.contracts.interview_state import InterviewState
from app.ui.state_handlers.ui_builder import build_ui_response_from_state



def retry_answer(state: InterviewState):

    # activate retry mode
    setattr(state, "retry_mode", True)

    return build_ui_response_from_state(state)
