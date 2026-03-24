# app/ui/state_handlers/next.py

from domain.contracts.interview_state import InterviewState
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from app.application.flow.interview_flow_engine import InterviewFlowEngine

flow = InterviewFlowEngine()


def next_question(state: InterviewState):

    state = flow.next_question(state)

    return build_ui_response_from_state(state)
