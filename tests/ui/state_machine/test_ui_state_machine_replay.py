# tests/ui/state_machine/test_ui_state_machine_replay.py

from app.ui.replay.replay_context import ReplayContext
from app.ui.state_machine.ui_state_machine import UIStateMachine
from app.ui.ui_state import UIState
from tests.domain.contracts.report.conftest import make_report
from tests.factories.interview_state_factory import build_interview_state
from tests.factories.question_factory import build_question


def test_ui_state_replay_enum_value_exists() -> None:
    assert UIState.REPLAY == "replay"
    assert UIState.REPLAY.value == "replay"


def test_resolve_returns_replay_when_replay_context_is_active() -> None:
    resolved = UIStateMachine.resolve(
        state=None,
        replay_context=ReplayContext(session_id="session-x", is_active=True),
    )
    assert resolved == UIState.REPLAY


def test_resolve_does_not_return_replay_when_replay_context_is_none() -> None:
    resolved = UIStateMachine.resolve(state=None, replay_context=None)
    assert resolved == UIState.SETUP
    assert resolved != UIState.REPLAY


def test_resolve_does_not_return_replay_when_is_active_false() -> None:
    resolved = UIStateMachine.resolve(
        state=None,
        replay_context=ReplayContext(session_id="session-x", is_active=False),
    )
    assert resolved == UIState.SETUP
    assert resolved != UIState.REPLAY


def test_resolve_replay_takes_precedence_over_report() -> None:
    q = build_question(qid="q1")
    state = build_interview_state(questions=[q]).model_copy(
        update={"report": make_report(), "is_completed": True}
    )
    assert UIStateMachine.resolve(state) == UIState.REPORT

    resolved = UIStateMachine.resolve(
        state=state,
        replay_context=ReplayContext(session_id="session-x", is_active=True),
    )
    assert resolved == UIState.REPLAY


def test_resolve_existing_signature_unchanged_without_replay_context() -> None:
    resolved = UIStateMachine.resolve(None)
    assert resolved == UIState.SETUP
