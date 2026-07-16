# tests/ui/replay/test_replay_layout_integration.py

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ui.bindings.handlers.replay_layout_coordinator import (
    ReplayLayoutCoordinator,
    resolve_session_id_from_report,
)
from app.ui.ui_state import UIState
from domain.contracts.session_history.session_history import SessionHistory
from tests.domain.contracts.knowledge_snapshot.conftest import SESSION_ID
from tests.domain.contracts.session_history.conftest import make_session_history
from tests.ui.replay.conftest import make_question_record, make_replay_session


def _session_history_fixture() -> SessionHistory:
    return make_session_history(session_id=SESSION_ID)


def test_full_replay_flow_entry_navigate_exit() -> None:
    history = _session_history_fixture()
    replay_session = make_replay_session(
        question_results=tuple(make_question_record(index=i) for i in range(4)),
    )

    def loader(session_id: str) -> SessionHistory | None:
        return history if session_id == history.session_id else None

    coordinator = ReplayLayoutCoordinator(loader)

    with patch.object(
        coordinator._entry,
        "load",
        return_value=replay_session,
    ) as mock_load:
        entered = coordinator.enter(history.session_id)

    mock_load.assert_called_once_with(history.session_id)
    assert entered.ui_state == UIState.REPLAY
    assert entered.replay_section_visible is True
    assert entered.report_section_visible is False
    assert entered.runtime is not None
    assert entered.runtime.controller is not None
    assert entered.runtime.controller.current_position == 0
    assert entered.nav_progress == "Question 1 of 4"
    assert "Session Summary" in entered.summary_html
    assert "Prompt 0" in entered.question_html

    forward_1 = coordinator.navigate_forward(entered.runtime)
    forward_2 = coordinator.navigate_forward(forward_1.runtime)
    forward_3 = coordinator.navigate_forward(forward_2.runtime)
    assert forward_3.runtime is not None
    assert forward_3.runtime.controller is not None
    assert forward_3.runtime.controller.current_position == 3
    assert forward_3.nav_progress == "Question 4 of 4"
    assert "Prompt 3" in forward_3.question_html

    back_1 = coordinator.navigate_backward(forward_3.runtime)
    assert back_1.runtime is not None
    assert back_1.runtime.controller is not None
    assert back_1.runtime.controller.current_position == 2
    assert back_1.nav_progress == "Question 3 of 4"
    assert "Prompt 2" in back_1.question_html

    interview_state = MagicMock()
    interview_state.report = object()
    interview_state.is_completed = True
    exited = coordinator.exit(back_1.runtime, interview_state)
    assert exited.ui_state == UIState.REPORT
    assert exited.replay_section_visible is False
    assert exited.report_section_visible is True
    assert exited.runtime is None


def test_resolve_session_id_from_report_prefers_session_history() -> None:
    history = _session_history_fixture()
    state = MagicMock()
    state.session_history = history
    state.interview_id = "other-id"
    assert resolve_session_id_from_report(state) == history.session_id


def test_ui_state_machine_compatibility_unchanged_without_replay() -> None:
    from app.ui.state_machine.ui_state_machine import UIStateMachine

    assert UIStateMachine.resolve(state=None, replay_context=None) == UIState.SETUP
