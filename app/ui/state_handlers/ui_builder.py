# app/ui/state_handlers/ui_builder.py

from domain.contracts.interview_state import InterviewState

from app.ui.ui_response import UIResponse
from app.ui.builders.ui_response_builder import UIResponseBuilder

_builder = UIResponseBuilder()


def build_ui_response_from_state(state: InterviewState) -> UIResponse:
    return _builder.build(state)
