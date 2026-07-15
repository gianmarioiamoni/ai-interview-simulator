# tests/ui/replay/test_replay_entry_point.py

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.ui.replay.replay_entry_point import ReplayEntryPoint, ReplayErrorRoute
from app.ui.replay.replay_view_controller import ReplayViewController
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_manifest import ReplayManifest, ReplaySourcePriority
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.replay.replay_session_metadata import ReplaySessionMetadata
from domain.contracts.replay.replay_timeline import ReplayTimeline
from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_candidate_profile_snapshot,
    make_coaching_snapshot,
    make_narrative,
    make_policy_versions,
)

SESSION_DATE = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)


def _make_session(*, is_successful: bool = True) -> ReplaySession:
    failure_reason = None if is_successful else "session_not_found"
    return ReplaySession(
        session_id=SESSION_ID,
        candidate_identity_id=CANDIDATE_ID,
        profile_snapshot=make_candidate_profile_snapshot(),
        narrative=make_narrative(),
        coaching_snapshot=make_coaching_snapshot(),
        policy_versions=make_policy_versions(),
        knowledge_epoch="1",
        manifest=ReplayManifest.for_standard_replay(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            replay_level=ReplayLevel.PRESENTATION,
            replay_engine_version="1.0",
            source_per_component={
                "profile": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
                "narrative": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
                "coaching": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
                "policy_versions": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            },
        ),
        session_metadata=ReplaySessionMetadata(
            interview_index=1,
            session_date=SESSION_DATE,
            role="Software Engineer",
            seniority_level="Senior",
            interview_mode="technical",
            question_count=0,
        ),
        timeline=ReplayTimeline(
            entries=(),
            total_positions=0,
            first_position=-1,
            last_position=-1,
            is_empty=True,
        ),
        question_results=(),
        is_successful=is_successful,
        failure_reason=failure_reason,
        replay_mode=ReplayMode.STANDARD,
        replay_level=ReplayLevel.PRESENTATION,
    )


def test_load_rejects_empty_session_id() -> None:
    entry = ReplayEntryPoint(session_loader=lambda _sid: None)
    with pytest.raises(ValueError, match="session_id must be non-empty"):
        entry.load("")


def test_load_returns_replay_session_from_mocked_graph() -> None:
    expected = _make_session(is_successful=True)
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"result": expected}

    with patch(
        "app.ui.replay.replay_entry_point.build_replay_graph",
        return_value=mock_graph,
    ) as mock_build:
        entry = ReplayEntryPoint(session_loader=lambda _sid: None)
        result = entry.load(SESSION_ID)

    mock_build.assert_called_once()
    mock_graph.invoke.assert_called_once()
    assert result is expected
    assert result.is_successful is True


def test_load_does_not_persist_replay_session() -> None:
    expected = _make_session(is_successful=True)
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"result": expected}
    entry = ReplayEntryPoint(session_loader=lambda _sid: None)

    with patch(
        "app.ui.replay.replay_entry_point.build_replay_graph",
        return_value=mock_graph,
    ):
        entry.load(SESSION_ID)

    assert not hasattr(entry, "_cached_session")
    assert not hasattr(entry, "persisted_session")
    assert getattr(entry, "_session_loader", None) is not None


def test_route_successful_session_to_view_controller() -> None:
    entry = ReplayEntryPoint(session_loader=lambda _sid: None)
    session = _make_session(is_successful=True)

    view_controller, error_route = entry.route(session)

    assert isinstance(view_controller, ReplayViewController)
    assert view_controller.session is session
    assert view_controller.current_position == 0
    assert error_route is None


def test_route_failed_session_to_error_route() -> None:
    entry = ReplayEntryPoint(session_loader=lambda _sid: None)
    session = _make_session(is_successful=False)

    view_controller, error_route = entry.route(session)

    assert view_controller is None
    assert isinstance(error_route, ReplayErrorRoute)
    assert error_route.session is session
    assert error_route.session.failure_reason == "session_not_found"
