# app/ui/state_handlers/submit.py

import time

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.answer import Answer
from domain.contracts.shared.action_type import ActionType

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.runtime.interview_runtime import get_runtime_llm
from app.ui.constants.loader_steps import LoaderStep
from app.ui.state_handlers.ui_builder import build_ui_response_from_state
from app.ui.adapters.ui_output_adapter import UIOutputAdapter

def submit_answer(
    state: InterviewState,
    written_answer: str,
    coding_answer: str,
    database_answer: str,
):

    # ---------------------------------------------------------
    # SAFETY
    # ---------------------------------------------------------
    if not state or not state.current_question:
        yield UIOutputAdapter.to_gradio(build_ui_response_from_state(state))
        return

    new_state = state.model_copy(deep=True)

    # ---------------------------------------------------------
    # INTENT
    # ---------------------------------------------------------
    new_state.intent = ActionType.SUBMIT

    # ---------------------------------------------------------
    # LOCK UI
    # ---------------------------------------------------------
    new_state.is_processing = True
    new_state.awaiting_user_input = False
    new_state.current_step = LoaderStep.SUBMITTING
    new_state.current_progress = 10

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(new_state))

    # ---------------------------------------------------------
    # PREPARE ANSWER
    # ---------------------------------------------------------
    question = new_state.current_question

    attempt = new_state.get_attempt_for_question(question.id) + 1

    answer_content = _resolve_answer(
        new_state,
        written_answer,
        coding_answer,
        database_answer,
    )

    # ---------------------------------------------------------
    # EMPTY ANSWER
    # ---------------------------------------------------------
    if not answer_content.strip():

        new_state.awaiting_user_input = True
        new_state.is_processing = False

        yield UIOutputAdapter.to_gradio(build_ui_response_from_state(new_state))

        return

    # ---------------------------------------------------------
    # CREATE ANSWER
    # ---------------------------------------------------------
    new_answer = Answer(
        question_id=question.id,
        content=answer_content,
        attempt=attempt,
    )

    new_state = new_state.add_answer(new_answer)

    # ---------------------------------------------------------
    # GRAPH EXECUTION
    # ---------------------------------------------------------
    llm = get_runtime_llm()

    use_case = EvaluateAnswerUseCase(llm=llm)

    new_state = use_case.execute(new_state)

    # ---------------------------------------------------------
    # RESET LOADER STATE
    # ---------------------------------------------------------
    new_state.current_step = None
    new_state.current_progress = 0

    # ---------------------------------------------------------
    # UNLOCK UI
    # ---------------------------------------------------------
    new_state.awaiting_user_input = True
    new_state.is_processing = False
    new_state.intent = ActionType.NONE

    yield UIOutputAdapter.to_gradio(build_ui_response_from_state(new_state))


# =========================================================
# HELPER
# =========================================================
def _resolve_answer(
    state,
    written,
    coding,
    database,
) -> str:

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
