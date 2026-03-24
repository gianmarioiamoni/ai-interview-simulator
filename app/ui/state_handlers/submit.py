# app/ui/state_handlers/submit.py

from domain.events.answer_submitted_event import AnswerSubmittedEvent
from domain.contracts.interview_state import InterviewState

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from app.application.flow.interview_flow_engine import InterviewFlowEngine

flow = InterviewFlowEngine()


def submit_answer(state, answer):

    # attach answer to state
    state = state.with_answer(answer)

    # run evaluation
    state = flow.submit_answer(state)

    return build_ui_response_from_state(state)
