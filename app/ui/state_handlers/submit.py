from typing import Generator

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.answer import Answer

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.runtime.interview_runtime import get_runtime_llm


def submit_answer(
    state: InterviewState, answer: str
) -> Generator[InterviewState, None, None]:

    # -----------------------------------------------------
    # SAFETY
    # -----------------------------------------------------

    if not state or not state.current_question:
        yield state
        return

    question = state.current_question
    question_id = question.id

    # -----------------------------------------------------
    # STEP 0 — ENTER PROCESSING
    # -----------------------------------------------------

    state.awaiting_user_input = False
    state.allowed_actions = []

    # 👉 opzionale: tracking fase (utile per loader dinamico)
    state.current_step = "validating"

    yield state

    # -----------------------------------------------------
    # STEP 1 — BUILD ANSWER
    # -----------------------------------------------------

    attempt = state.get_attempt_for_question(question_id) + 1

    new_answer = Answer(
        question_id=question_id,
        content=answer,
        attempt=attempt,
    )

    state = state.add_answer(new_answer)

    state.awaiting_user_input = False
    state.current_step = "processing"

    yield state

    # -----------------------------------------------------
    # STEP 2 — USE CASE (LLM)
    # -----------------------------------------------------

    llm = get_runtime_llm()
    use_case = EvaluateAnswerUseCase(llm=llm)

    state = use_case.execute(state)

    # -----------------------------------------------------
    # STEP 3 — FINALIZE STATE
    # -----------------------------------------------------

    state.awaiting_user_input = True
    state.current_step = None

    yield state
