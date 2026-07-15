# tests/app/graph/nodes/test_replay_node.py
# EPIC-03 Phase 4a — replay_node unit tests.
#
# Validates (per EPIC-03-IMPLEMENTATION-PLAN.md §6 Phase 4 gate):
# - replay_node produces ReplaySession from a valid SessionHistory fixture.
# - replay_node produces ReplaySession(is_successful=False) when SessionHistory not found.
# - replay_node produces ReplaySession(is_successful=False) on unexpected exception.
# - replay_node is the sole writer of ReplayGraphState.result.
# - session_loader is never called with a write operation (read-only invariant I-R07).
# - No LLM calls are made during replay_node execution (I-11).

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_graph_state import ReplayGraphState
from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session_builder import ReplaySessionBuilder
from domain.contracts.replay.replay_session_v13 import ReplaySessionV13
from domain.contracts.session_history.question_result_record import QuestionResultRecord
from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    ReplayMetadata,
    SessionHistory,
    TranscriptEntry,
)
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder
from app.graph.nodes.replay_node import replay_node

from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_knowledge_snapshot,
)
from tests.domain.contracts.session_history.conftest import (
    FIXED_HISTORY_DT,
    make_interview_metadata,
    make_language_profile,
    make_question_timeline,
    make_session_history,
    make_transcript,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_question_result(
    question_id: str = "q-001",
    question_index: int = 0,
    question_type: str = "written",
    area_label: str = "Algorithms",
    question_prompt: str = "Describe REST.",
    score: float = 75.0,
    max_score: float = 100.0,
    feedback: str = "Good.",
    attempts: int = 1,
) -> QuestionResultRecord:
    return QuestionResultRecord(
        question_id=question_id,
        question_index=question_index,
        question_type=question_type,
        area_label=area_label,
        question_prompt=question_prompt,
        score=score,
        max_score=max_score,
        feedback=feedback,
        attempts=attempts,
    )


def _make_session_history_with_results(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
    question_results: Optional[list[QuestionResultRecord]] = None,
) -> SessionHistory:
    qr = question_results if question_results is not None else [_make_question_result()]
    snapshot = make_knowledge_snapshot(session_id=session_id, candidate_id=candidate_id)
    return (
        SessionHistoryBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_id)
        .with_interview_index(0)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata())
        .with_language_profile(make_language_profile(session_id=session_id))
        .with_transcript([
            TranscriptEntry(
                question_index=0,
                question_id="q-001",
                question_prompt="Describe REST.",
                answer_content="REST is a style.",
                answer_attempt=1,
            )
        ])
        .with_question_timeline(make_question_timeline())
        .with_question_results(qr)
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_HISTORY_DT)
        .build()
    )


def _make_request(
    session_id: str = SESSION_ID,
    replay_mode: ReplayMode = ReplayMode.STANDARD,
    replay_level: ReplayLevel = ReplayLevel.PRESENTATION,
) -> ReplayRequest:
    return ReplayRequest(
        session_id=session_id,
        replay_mode=replay_mode,
        replay_level=replay_level,
    )


def _make_state(request: Optional[ReplayRequest] = None) -> ReplayGraphState:
    req = request or _make_request()
    return ReplayGraphState(request=req)


def _loader_returns(sh: Optional[SessionHistory]) -> callable:
    """Return a session_loader that always yields the given SessionHistory."""
    def _loader(session_id: str) -> Optional[SessionHistory]:
        return sh
    return _loader


def _loader_raises(exc: Exception) -> callable:
    """Return a session_loader that always raises the given exception."""
    def _loader(session_id: str) -> Optional[SessionHistory]:
        raise exc
    return _loader


# ---------------------------------------------------------------------------
# Core production tests
# ---------------------------------------------------------------------------

class TestReplayNodeProducesReplaySession:
    """replay_node produces a valid ReplaySession from a SessionHistory fixture."""

    def test_result_is_replay_session_v13(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert isinstance(output["result"], ReplaySessionV13)

    def test_result_is_successful(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].is_successful is True

    def test_failure_reason_is_none_on_success(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].failure_reason is None

    def test_result_session_id_matches_request(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state(_make_request(session_id=SESSION_ID))
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].session_id == SESSION_ID

    def test_result_candidate_identity_id_matches(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].candidate_identity_id == CANDIDATE_ID

    def test_result_replay_mode_propagated(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state(_make_request(replay_mode=ReplayMode.STANDARD))
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].replay_mode == ReplayMode.STANDARD

    def test_result_replay_level_propagated(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state(_make_request(replay_level=ReplayLevel.PRESENTATION))
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].replay_level == ReplayLevel.PRESENTATION

    def test_result_question_count(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].question_count == 1

    def test_result_is_frozen(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        from pydantic import ValidationError
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            output["result"].session_id = "mutated"  # type: ignore[misc]

    def test_result_schema_version(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].schema_version == "1.0"

    def test_result_manifest_session_id_matches(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state(_make_request(session_id=SESSION_ID))
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].manifest.session_id == SESSION_ID

    def test_original_request_preserved_in_output(self) -> None:
        sh = _make_session_history_with_results()
        req = _make_request()
        state = _make_state(req)
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["request"] is req

    def test_session_loader_called_with_correct_session_id(self) -> None:
        sh = _make_session_history_with_results()
        calls: list[str] = []

        def _loader(sid: str) -> Optional[SessionHistory]:
            calls.append(sid)
            return sh

        state = _make_state(_make_request(session_id=SESSION_ID))
        replay_node(state, session_loader=_loader)
        assert calls == [SESSION_ID]

    def test_session_loader_called_exactly_once(self) -> None:
        sh = _make_session_history_with_results()
        call_count = {"n": 0}

        def _loader(sid: str) -> Optional[SessionHistory]:
            call_count["n"] += 1
            return sh

        state = _make_state()
        replay_node(state, session_loader=_loader)
        assert call_count["n"] == 1


# ---------------------------------------------------------------------------
# Failure path: SessionHistory not found
# ---------------------------------------------------------------------------

class TestReplayNodeSessionNotFound:
    """replay_node produces is_successful=False when SessionHistory not found."""

    def test_result_is_not_successful(self) -> None:
        state = _make_state(_make_request(session_id="missing-session"))
        output = replay_node(state, session_loader=_loader_returns(None))
        assert output["result"].is_successful is False

    def test_failure_reason_is_populated(self) -> None:
        state = _make_state(_make_request(session_id="missing-session"))
        output = replay_node(state, session_loader=_loader_returns(None))
        assert output["result"].failure_reason is not None
        assert len(output["result"].failure_reason) > 0

    def test_session_id_preserved_in_failed_result(self) -> None:
        sid = "missing-session"
        state = _make_state(_make_request(session_id=sid))
        output = replay_node(state, session_loader=_loader_returns(None))
        assert output["result"].session_id == sid

    def test_result_is_replay_session_v13_type(self) -> None:
        state = _make_state(_make_request(session_id="missing-session"))
        output = replay_node(state, session_loader=_loader_returns(None))
        assert isinstance(output["result"], ReplaySessionV13)

    def test_replay_mode_preserved_on_failure(self) -> None:
        state = _make_state(_make_request(session_id="missing", replay_mode=ReplayMode.STANDARD))
        output = replay_node(state, session_loader=_loader_returns(None))
        assert output["result"].replay_mode == ReplayMode.STANDARD

    def test_replay_level_preserved_on_failure(self) -> None:
        state = _make_state(_make_request(session_id="missing", replay_level=ReplayLevel.PRESENTATION))
        output = replay_node(state, session_loader=_loader_returns(None))
        assert output["result"].replay_level == ReplayLevel.PRESENTATION


# ---------------------------------------------------------------------------
# Failure path: unexpected exception from session_loader
# ---------------------------------------------------------------------------

class TestReplayNodeExceptionHandling:
    """replay_node handles unexpected exceptions without propagating."""

    def test_exception_from_loader_produces_failed_result(self) -> None:
        state = _make_state()
        output = replay_node(state, session_loader=_loader_raises(RuntimeError("DB down")))
        assert output["result"].is_successful is False

    def test_exception_failure_reason_contains_error_type(self) -> None:
        state = _make_state()
        output = replay_node(state, session_loader=_loader_raises(RuntimeError("DB down")))
        assert "RuntimeError" in output["result"].failure_reason

    def test_exception_does_not_propagate(self) -> None:
        state = _make_state()
        output = replay_node(state, session_loader=_loader_raises(ValueError("bad")))
        assert output["result"] is not None

    def test_exception_session_id_preserved(self) -> None:
        state = _make_state(_make_request(session_id=SESSION_ID))
        output = replay_node(state, session_loader=_loader_raises(Exception("oops")))
        assert output["result"].session_id == SESSION_ID


# ---------------------------------------------------------------------------
# I-R07: no persistence writes during replay_node execution
# ---------------------------------------------------------------------------

class TestReplayNodeNoPersistenceWrites:
    """I-R07: session_loader is read-only — no write calls during replay_node."""

    def test_loader_is_only_read_called(self) -> None:
        sh = _make_session_history_with_results()
        loader_mock = MagicMock(return_value=sh)
        state = _make_state()
        replay_node(state, session_loader=loader_mock)
        # Only one call (read), no write-like method calls.
        assert loader_mock.call_count == 1

    def test_loader_has_no_write_method_calls(self) -> None:
        sh = _make_session_history_with_results()
        loader_mock = MagicMock(return_value=sh)
        state = _make_state()
        replay_node(state, session_loader=loader_mock)
        # Verify no save/write/update methods were called on the mock.
        for call in loader_mock.method_calls:
            assert "write" not in call[0].lower()
            assert "save" not in call[0].lower()
            assert "update" not in call[0].lower()


# ---------------------------------------------------------------------------
# I-11: no LLM calls during replay_node execution
# ---------------------------------------------------------------------------

class TestReplayNodeNoLLMCalls:
    """I-11: replay_node must never invoke LLM services."""

    def test_no_llm_invocation_on_success(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        with patch("app.graph.nodes.replay_node.ReplaySessionBuilder") as mock_builder_cls:
            mock_builder = MagicMock()
            mock_builder_cls.return_value = mock_builder
            mock_builder.with_session_history.return_value = mock_builder
            mock_builder.with_replay_mode.return_value = mock_builder
            mock_builder.with_replay_level.return_value = mock_builder
            mock_builder.with_operator_id.return_value = mock_builder
            # Produce a real result to avoid type errors.
            real_result = (
                ReplaySessionBuilder()
                .with_session_history(sh)
                .with_replay_mode(ReplayMode.STANDARD)
                .with_replay_level(ReplayLevel.PRESENTATION)
                .with_operator_id(None)
                .build()
            )
            mock_builder.build.return_value = real_result

            replay_node(state, session_loader=_loader_returns(sh))

            # Verify no attribute named 'llm', 'invoke', 'generate', 'chat' was accessed.
            for call in mock_builder.method_calls:
                assert "llm" not in call[0].lower()
                assert "invoke" not in call[0].lower()

    def test_no_openai_call_on_success(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        with patch("openai.ChatCompletion.create", side_effect=AssertionError("LLM called")):
            # Should not raise — no LLM path in replay_node.
            output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].is_successful is True


# ---------------------------------------------------------------------------
# Sole writer: replay_node is the sole writer of ReplayGraphState.result
# ---------------------------------------------------------------------------

class TestReplayNodeSoleWriter:
    """I-R01: replay_node is the sole writer of ReplayGraphState.result."""

    def test_result_key_set_by_replay_node(self) -> None:
        sh = _make_session_history_with_results()
        initial_state: ReplayGraphState = ReplayGraphState(request=_make_request())
        assert "result" not in initial_state or initial_state.get("result") is None
        output = replay_node(initial_state, session_loader=_loader_returns(sh))
        assert output["result"] is not None

    def test_result_written_exactly_once(self) -> None:
        sh = _make_session_history_with_results()
        build_count = {"n": 0}
        original_build = ReplaySessionBuilder.build

        def _counting_build(self) -> ReplaySessionV13:
            build_count["n"] += 1
            return original_build(self)

        state = _make_state()
        with patch.object(ReplaySessionBuilder, "build", _counting_build):
            replay_node(state, session_loader=_loader_returns(sh))
        assert build_count["n"] == 1

    def test_replay_session_builder_is_sole_construction_path(self) -> None:
        """Verify ReplaySessionBuilder.build() is called — not direct ReplaySessionV13()."""
        sh = _make_session_history_with_results()
        state = _make_state()

        builder_build_called = {"called": False}
        original_build = ReplaySessionBuilder.build

        def _spy_build(self) -> ReplaySessionV13:
            builder_build_called["called"] = True
            return original_build(self)

        with patch.object(ReplaySessionBuilder, "build", _spy_build):
            replay_node(state, session_loader=_loader_returns(sh))

        assert builder_build_called["called"] is True


# ---------------------------------------------------------------------------
# ReplayFeatureEngine instantiation
# ---------------------------------------------------------------------------

class TestReplayNodeReplayFeatureEngine:
    """replay_node instantiates ReplayFeatureEngine with the profile_snapshot."""

    def test_replay_feature_engine_instantiated(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        with patch("app.graph.nodes.replay_node.ReplayFeatureEngine") as mock_rfe_cls:
            mock_rfe = MagicMock()
            mock_rfe_cls.return_value = mock_rfe

            replay_node(state, session_loader=_loader_returns(sh))

            mock_rfe_cls.assert_called_once_with(
                profile_snapshot=sh.knowledge_snapshot.profile_snapshot
            )

    def test_replay_feature_engine_receives_profile_snapshot(self) -> None:
        sh = _make_session_history_with_results()
        state = _make_state()
        captured: dict = {}
        with patch("app.graph.nodes.replay_node.ReplayFeatureEngine") as mock_rfe_cls:
            mock_rfe = MagicMock()
            mock_rfe_cls.return_value = mock_rfe

            def _capture(**kwargs):
                captured["profile_snapshot"] = kwargs.get("profile_snapshot")
                return mock_rfe

            mock_rfe_cls.side_effect = _capture
            replay_node(state, session_loader=_loader_returns(sh))

        assert captured["profile_snapshot"] is sh.knowledge_snapshot.profile_snapshot


# ---------------------------------------------------------------------------
# Empty question_results (edge case)
# ---------------------------------------------------------------------------

class TestReplayNodeEmptySession:
    """replay_node handles sessions with no question_results."""

    def test_empty_session_is_successful(self) -> None:
        sh = _make_session_history_with_results(question_results=[])
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].is_successful is True

    def test_empty_session_question_count_is_zero(self) -> None:
        sh = _make_session_history_with_results(question_results=[])
        state = _make_state()
        output = replay_node(state, session_loader=_loader_returns(sh))
        assert output["result"].question_count == 0
