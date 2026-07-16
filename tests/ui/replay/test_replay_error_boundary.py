# tests/ui/replay/test_replay_error_boundary.py

from __future__ import annotations

import pytest

from app.ui.replay.panels.replay_error_boundary import ReplayErrorBoundary
from tests.ui.replay.conftest import make_replay_session


def test_session_not_found_message() -> None:
    session = make_replay_session(
        is_successful=False,
        failure_reason="SessionHistory not found for id=abc",
    )
    model = ReplayErrorBoundary(session).render()

    assert model.candidate_message == "This session is no longer available."
    assert model.action_label == "Return to Report"
    assert "SessionHistory not found" not in model.candidate_message
    assert session.failure_reason not in model.candidate_message


def test_persistence_io_error_message() -> None:
    session = make_replay_session(
        is_successful=False,
        failure_reason="Persistence layer I/O error: disk full",
    )
    model = ReplayErrorBoundary(session, entry_context="session_list").render()

    assert model.candidate_message == "Unable to load session. Please try again."
    assert model.action_label == "Return to Session List"
    assert session.failure_reason not in model.candidate_message


def test_default_message_for_unknown_reason() -> None:
    session = make_replay_session(
        is_successful=False,
        failure_reason="unexpected internal failure xyz-999",
    )
    model = ReplayErrorBoundary(session).render()

    assert model.candidate_message == (
        "An error occurred loading the session. Please try again or contact support."
    )
    assert "xyz-999" not in model.candidate_message
    assert session.failure_reason not in model.candidate_message


def test_rejects_successful_session() -> None:
    session = make_replay_session(is_successful=True)
    with pytest.raises(ValueError, match="is_successful=False"):
        ReplayErrorBoundary(session)
