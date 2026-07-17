# tests/ui/replay/test_replay_error_boundary.py

from __future__ import annotations

import pytest

from app.ui.presentation import AsyncBoundary, get_candidate_facing_error_entry
from app.ui.replay.panels.replay_error_boundary import ReplayErrorBoundary
from tests.ui.replay.conftest import make_replay_session

_CATALOG = get_candidate_facing_error_entry("err.replay_enter.failed")


def test_catalog_message_for_session_not_found() -> None:
    session = make_replay_session(
        is_successful=False,
        failure_reason="SessionHistory not found for id=abc",
    )
    boundary = ReplayErrorBoundary(session)
    model = boundary.render()

    assert model.candidate_message == _CATALOG.message_text
    assert boundary.candidate_facing_error.boundary is AsyncBoundary.REPLAY_ENTER
    assert model.action_label == "Return to Report"
    assert "SessionHistory not found" not in model.candidate_message
    assert session.failure_reason not in model.candidate_message


def test_catalog_message_for_persistence_io_error() -> None:
    session = make_replay_session(
        is_successful=False,
        failure_reason="Persistence layer I/O error: disk full",
    )
    boundary = ReplayErrorBoundary(session, entry_context="session_list")
    model = boundary.render()

    assert model.candidate_message == _CATALOG.message_text
    assert model.action_label == "Return to Session List"
    assert session.failure_reason not in model.candidate_message


def test_catalog_message_for_unknown_reason() -> None:
    session = make_replay_session(
        is_successful=False,
        failure_reason="unexpected internal failure xyz-999",
    )
    model = ReplayErrorBoundary(session).render()

    assert model.candidate_message == _CATALOG.message_text
    assert "xyz-999" not in model.candidate_message
    assert session.failure_reason not in model.candidate_message


def test_rejects_successful_session() -> None:
    session = make_replay_session(is_successful=True)
    with pytest.raises(ValueError, match="is_successful=False"):
        ReplayErrorBoundary(session)


def test_from_candidate_facing_error_without_session() -> None:
    from app.ui.presentation import emit_boundary_error

    error = emit_boundary_error(AsyncBoundary.REPLAY_ENTER)
    boundary = ReplayErrorBoundary(candidate_facing_error=error)
    assert boundary.session is None
    assert boundary.render().candidate_message == _CATALOG.message_text
