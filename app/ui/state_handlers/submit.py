# app/ui/state_handlers/submit.py

from domain.events.answer_submitted_event import AnswerSubmittedEvent
from domain.contracts.interview_state import InterviewState

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.ui.state_handlers.ui_builder import build_ui_response_from_state


def submit_answer(state: InterviewState, user_answer: str):

    question = state.current_question

    event = AnswerSubmittedEvent(
        question_id=question.id,
        content=user_answer,
    )

    state = state.apply_event(event)

    from infrastructure.llm.llm_factory import get_llm

    llm = get_llm()
    use_case = EvaluateAnswerUseCase(llm)

    state = use_case.execute(state)

    return build_ui_response_from_state(state)
