# tests/domain/contracts/replay/test_replay_graph_state.py
# EPIC-03 Phase 2f — ReplayGraphState contract tests.

from __future__ import annotations

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "knowledge_snapshot"))
from conftest import (  # noqa: E402
    CANDIDATE_ID,
    SESSION_ID,
    make_candidate_profile_snapshot,
    make_coaching_snapshot,
    make_narrative,
    make_policy_versions,
)

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_graph_state import ReplayGraphState
from domain.contracts.replay.replay_manifest import ReplayManifest, ReplaySourcePriority
from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session_metadata import ReplaySessionMetadata
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.replay.replay_timeline import ReplayTimeline


SESSION_DATE = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)


def _make_request() -> ReplayRequest:
    return ReplayRequest(session_id=SESSION_ID)


def _make_manifest() -> ReplayManifest:
    return ReplayManifest.for_standard_replay(
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
    )


def _make_session() -> ReplaySession:
    return ReplaySession(
        session_id=SESSION_ID,
        candidate_identity_id=CANDIDATE_ID,
        profile_snapshot=make_candidate_profile_snapshot(),
        narrative=make_narrative(),
        coaching_snapshot=make_coaching_snapshot(),
        policy_versions=make_policy_versions(),
        knowledge_epoch="1",
        manifest=_make_manifest(),
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
        is_successful=True,
        failure_reason=None,
    )


class TestReplayGraphStateConstruction:

    def test_state_with_request_only(self):
        req = _make_request()
        state: ReplayGraphState = {"request": req}
        assert state["request"] is req
        assert "result" not in state

    def test_state_with_request_and_none_result(self):
        req = _make_request()
        state: ReplayGraphState = {"request": req, "result": None}
        assert state["result"] is None

    def test_state_with_result_set(self):
        req = _make_request()
        session = _make_session()
        state: ReplayGraphState = {"request": req, "result": session}
        assert state["result"] is session

    def test_state_is_mutable(self):
        req = _make_request()
        state: ReplayGraphState = {"request": req}
        session = _make_session()
        state["result"] = session
        assert state["result"] is session

    def test_request_field_type(self):
        req = _make_request()
        state: ReplayGraphState = {"request": req}
        assert isinstance(state["request"], ReplayRequest)

    def test_result_field_type_when_set(self):
        req = _make_request()
        session = _make_session()
        state: ReplayGraphState = {"request": req, "result": session}
        assert isinstance(state["result"], ReplaySession)


class TestReplayGraphStateIsolation:

    def test_no_interview_state_import(self):
        """I-R03: ReplayGraphState must not reference InterviewState."""
        import domain.contracts.replay.replay_graph_state as module
        source = open(module.__file__).read()
        assert "InterviewState" not in source

    def test_no_longitudinal_profile_import(self):
        """I-R06: No LongitudinalProfile cross-reference."""
        import domain.contracts.replay.replay_graph_state as module
        source = open(module.__file__).read()
        assert "LongitudinalProfile" not in source
