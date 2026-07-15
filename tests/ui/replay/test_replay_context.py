# tests/ui/replay/test_replay_context.py

from __future__ import annotations

import pytest

from app.ui.replay.replay_context import ReplayContext
from app.ui.state_machine.ui_state_machine import UIStateMachine
from app.ui.ui_state import UIState


def test_replay_context_construction() -> None:
    ctx = ReplayContext(session_id="session-x", is_active=True)
    assert ctx.session_id == "session-x"
    assert ctx.is_active is True


def test_replay_context_empty_session_id_raises() -> None:
    with pytest.raises(ValueError, match="session_id must be non-empty"):
        ReplayContext(session_id="", is_active=True)


def test_replay_context_drives_ui_state_replay() -> None:
    ctx = ReplayContext(session_id="session-x", is_active=True)
    assert UIStateMachine.resolve(state=None, replay_context=ctx) == UIState.REPLAY


def test_replay_context_inactive_does_not_drive_replay() -> None:
    ctx = ReplayContext(session_id="session-x", is_active=False)
    assert UIStateMachine.resolve(state=None, replay_context=ctx) == UIState.SETUP
