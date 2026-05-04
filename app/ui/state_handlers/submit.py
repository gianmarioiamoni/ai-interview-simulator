# app/ui/state_handlers/submit.py

from typing import Generator

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.answer import Answer

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from app.runtime.interview_runtime import get_runtime_llm
from app.ui.ui_response import UIResponse


def submit_answer(
    state: InterviewState, answer: str
) -> Generator[UIResponse, None, None]:

    if not state or not state.current_question:
        yield build_ui_response_from_state(state)
        return

    question = state.current_question
    question_id = question.id

    # -----------------------------------------------------
    # STEP 1 — VALIDATION / PREP
    # -----------------------------------------------------

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="🔍 Validating answer...",
    )

    # -----------------------------------------------------
    # STEP 2 — BUILD ANSWER
    # -----------------------------------------------------

    attempt = state.get_attempt_for_question(question_id) + 1

    new_answer = Answer(
        question_id=question_id,
        content=answer,
        attempt=attempt,
    )

    state = state.add_answer(new_answer)

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="⚙️ Processing answer...",
    )

    # -----------------------------------------------------
    # STEP 3 — USE CASE (LLM)
    # -----------------------------------------------------

    llm = get_runtime_llm()
    use_case = EvaluateAnswerUseCase(llm=llm)

    state = use_case.execute(state)

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="🧠 Evaluating response...",
    )

    # -----------------------------------------------------
    # STEP 4 — FINAL UI
    # -----------------------------------------------------

    response = build_ui_response_from_state(state)

    yield response
