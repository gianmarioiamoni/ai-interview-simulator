# app/ui/state_handlers/submit.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.answer import Answer

from app.application.use_cases.evaluate_answer import EvaluateAnswerUseCase
from app.runtime.interview_runtime import get_runtime_llm

from app.ui.state_handlers.ui_builder import build_ui_response_from_state


def submit_answer(
    state: InterviewState, 
    written_answer: str, 
    coding_answer: str, 
    database_answer: str,
):

    if not state or not state.current_question:
        return build_ui_response_from_state(state).to_gradio_outputs()

    question = state.current_question
    attempt = state.get_attempt_for_question(question.id) + 1

    answer_content = _resolve_answer(state, written_answer, coding_answer, database_answer)

    if not answer_content.strip():
        return build_ui_response_from_state(state).to_gradio_outputs()

    new_answer = Answer(
        question_id=question.id,
        content=answer_content,
        attempt=attempt,
    )

    state = state.add_answer(new_answer)

    llm = get_runtime_llm()
    use_case = EvaluateAnswerUseCase(llm=llm)

    state = use_case.execute(state)

    state.awaiting_user_input = True

    return build_ui_response_from_state(state).to_gradio_outputs()


def _resolve_answer(state, written, coding, database) -> str:
    q = state.current_question

    if not q:
        return ""

    if q.type == "written":
        return written or ""

    if q.type == "coding":
        return coding or ""

    if q.type == "database":
        return database or ""

    return ""
