# app/ui/state_handlers/navigation.py

from domain.contracts.interview_state import InterviewState
from app.ui.state_handlers.ui_builder import build_ui_response_from_state


def new_interview(state: InterviewState):
    new_state = InterviewState.create_empty()
    return build_ui_response_from_state(new_state).to_gradio_outputs()
