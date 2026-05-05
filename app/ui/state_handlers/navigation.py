# app/ui/state_handlers/navigation.py

from typing import Generator

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType
from domain.contracts.user.role import RoleType
from domain.contracts.interview.interview_type import InterviewType

from app.ui.ui_state import UIState
from app.ui.ui_response import UIResponse
from app.ui.state_handlers.ui_builder import build_ui_response_from_state

from app.runtime.interview_runtime import run_interview_graph


# =========================================================
# RETRY
# =========================================================


def retry_answer(state: InterviewState) -> Generator[UIResponse, None, None]:

    if state is None or state.current_question is None:
        yield UIResponse(
            state=state,
            show_submit=False,
            show_retry=False,
            show_next=False,
        )
        return

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="🔄 Resetting attempt...",
    )

    new_state = state.model_copy(deep=True)

    q = new_state.current_question

    if q:
        new_state = new_state.clear_result_for_question(q.id)

    new_state.last_action = ActionType.NONE
    new_state.awaiting_user_input = True
    new_state.last_feedback_bundle = None

    yield UIResponse(
        state=new_state,
        loader_visible=True,
        loader_value="🧠 Preparing new attempt...",
    )

    response = build_ui_response_from_state(new_state)

    yield response


# =========================================================
# NEXT / GENERATE REPORT
# =========================================================


def next_question(state: InterviewState) -> Generator[UIResponse, None, None]:

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="➡️ Moving to next step...",
    )

    new_state = state.model_copy(deep=True)

    if ActionType.GENERATE_REPORT in state.allowed_actions:
        new_state.last_action = ActionType.GENERATE_REPORT
    else:
        new_state.last_action = ActionType.NEXT

    yield UIResponse(
        state=new_state,
        loader_visible=True,
        loader_value="🧠 Running interview engine...",
    )

    new_state = run_interview_graph(new_state)

    # -----------------------------------------------------
    # REPORT FLOW
    # -----------------------------------------------------

    if new_state.is_completed:
        response = build_ui_response_from_state(new_state)
        yield response
        return

    # -----------------------------------------------------
    # NORMAL FLOW
    # -----------------------------------------------------

    response = build_ui_response_from_state(new_state)

    yield response


# =========================================================
# NEW INTERVIEW
# =========================================================


def new_interview(state: InterviewState) -> Generator[UIResponse, None, None]:

    yield UIResponse(
        state=state,
        loader_visible=True,
        loader_value="🔄 Resetting interview...",
    )

    yield UIResponse(
        state=state,
        show_setup=True,
        show_interview=False,
        page_title="## Configure Your Interview",
        question_counter="",
        feedback_markdown="",
        written_display="",
        coding_display="",
        database_display="",
        show_submit=False,
        show_retry=False,
        show_next=False,
    )
