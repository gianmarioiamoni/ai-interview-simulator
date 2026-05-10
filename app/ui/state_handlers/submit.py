# app/ui/state_handlers/submit.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.answer import Answer
from app.ui.constants.loader_steps import LoaderStep

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.runtime.interview_runtime import get_runtime_llm

from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ui.state_machine.ui_state_machine import UIStateMachine


def submit_answer(
    state: InterviewState, 
    written_answer: str, 
    coding_answer: str, 
    database_answer: str,
):

    if not state or not state.current_question:
        return build_ui_response_from_state(state).to_gradio_outputs()

    # START processing
    new_state = state.model_copy(deep=True)

    question = new_state.current_question
    attempt = new_state.get_attempt_for_question(question.id) + 1

    answer_content = _resolve_answer(new_state, written_answer, coding_answer, database_answer)

    if not answer_content.strip():
        return build_ui_response_from_state(new_state).to_gradio_outputs()

    new_answer = Answer(
        question_id=question.id,
        content=answer_content,
        attempt=attempt,
    )

    # ADD answer
    new_state = new_state.add_answer(new_answer)
    new_state.awaiting_user_input = False

    # EVALUATE answer
    llm = get_runtime_llm()
    use_case = EvaluateAnswerUseCase(llm=llm)

    new_state = use_case.execute(new_state)

    # END processing
    new_state.awaiting_user_input = True

    # 🔍 DEBUG
    print("FEEDBACK BUNDLE:", new_state.last_feedback_bundle is not None)
    print("ALLOWED ACTIONS:", new_state.allowed_actions)
    print("AWAITING USER INPUT:", new_state.awaiting_user_input)
    print("UI STATE:", UIStateMachine.resolve(new_state))

    return build_ui_response_from_state(new_state).to_gradio_outputs()


def _resolve_answer(state, written, coding, database) -> str:
    q = state.current_question

    if not q:
        return ""

    if q.is_written():
        return written or ""

    if q.is_coding():
        return coding or ""

    if q.is_database():
        return database or ""

    return ""
