# tests/domain/contracts/replay/test_replay_session_builder.py
# EPIC-03 Phase 3b — ReplaySessionBuilder unit tests.
# Verifies build() invariants RC-B-01 through RC-B-07, as_failed(), and Reconstruction
# Completeness architectural test (P-08).

from __future__ import annotations

import sys
import os
import inspect
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "session_history"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "knowledge_snapshot"))
from tests.domain.contracts.session_history.conftest import (  # noqa: E402
    CANDIDATE_ID,
    SESSION_ID,
    FIXED_HISTORY_DT,
    make_session_history,
    make_interview_metadata,
    make_language_profile,
    make_transcript,
    make_question_timeline,
)
from tests.domain.contracts.knowledge_snapshot.conftest import make_knowledge_snapshot  # noqa: E402

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_question_record import ReplayQuestionRecord
from domain.contracts.replay.replay_session_builder import ReplaySessionBuilder
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.replay.replay_timeline import ReplayTimeline
from domain.contracts.session_history.question_result_record import QuestionResultRecord
from domain.contracts.session_history.session_history import (
    SessionHistory,
    TranscriptEntry,
    QuestionTimelineEntry,
    ReplayMetadata,
)
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder


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


def _make_session_with_results(
    question_results: list[QuestionResultRecord] | None = None,
    transcript: list[TranscriptEntry] | None = None,
) -> SessionHistory:
    sh = make_session_history()
    # Rebuild with question_results
    qr = question_results if question_results is not None else [_make_question_result()]
    tr = transcript if transcript is not None else [
        TranscriptEntry(
            question_index=0,
            question_id="q-001",
            question_prompt="Describe REST.",
            answer_content="REST stands for representational state transfer.",
            answer_attempt=1,
        )
    ]
    snapshot = make_knowledge_snapshot(session_id=sh.session_id, candidate_id=sh.candidate_identity_id)
    return (
        SessionHistoryBuilder()
        .with_session_id(sh.session_id)
        .with_candidate_identity_id(sh.candidate_identity_id)
        .with_interview_index(sh.interview_index)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata())
        .with_language_profile(make_language_profile(session_id=sh.session_id))
        .with_transcript(tr)
        .with_question_timeline(make_question_timeline())
        .with_question_results(qr)
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_HISTORY_DT)
        .build()
    )


class TestReplaySessionBuilderBuild:

    def test_build_returns_replay_session_v13(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert isinstance(result, ReplaySession)

    def test_build_is_successful(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.is_successful is True
        assert result.failure_reason is None

    def test_build_session_id_matches(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.session_id == sh.session_id

    def test_build_candidate_id_matches(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.candidate_identity_id == sh.candidate_identity_id

    def test_build_profile_snapshot_identity(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.profile_snapshot is sh.knowledge_snapshot.profile_snapshot

    def test_build_narrative_identity(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.narrative is sh.knowledge_snapshot.narrative

    def test_build_coaching_snapshot_identity(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.coaching_snapshot is sh.knowledge_snapshot.coaching_snapshot

    def test_build_policy_versions_identity(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.policy_versions is sh.knowledge_snapshot.policy_versions

    def test_build_knowledge_epoch(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.knowledge_epoch == sh.knowledge_snapshot.knowledge_epoch

    def test_build_schema_version_is_1_0(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.schema_version == "1.0"


class TestReplaySessionBuilderQuestionResults:

    def test_question_results_assembled(self):
        qr = _make_question_result(question_id="q-001", question_index=0)
        sh = _make_session_with_results(question_results=[qr])
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert len(result.question_results) == 1
        assert result.question_results[0].question_id == "q-001"

    def test_candidate_answer_joined_from_transcript(self):
        qr = _make_question_result(question_id="q-001", question_index=0)
        tr = [TranscriptEntry(
            question_index=0, question_id="q-001",
            question_prompt="Describe REST.", answer_content="My answer.", answer_attempt=1,
        )]
        sh = _make_session_with_results(question_results=[qr], transcript=tr)
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.question_results[0].candidate_answer == "My answer."

    def test_candidate_answer_empty_when_no_transcript_match(self):
        qr = _make_question_result(question_id="q-999", question_index=0)
        tr = [TranscriptEntry(
            question_index=0, question_id="q-001",
            question_prompt="Describe REST.", answer_content="My answer.", answer_attempt=1,
        )]
        sh = _make_session_with_results(question_results=[qr], transcript=tr)
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.question_results[0].candidate_answer == ""

    def test_question_results_ordered_by_question_index(self):
        qr0 = _make_question_result(question_id="q-001", question_index=0)
        qr1 = _make_question_result(question_id="q-002", question_index=1,
                                     question_prompt="Explain Big-O.", feedback="Good.", area_label="DS")
        snapshot = make_knowledge_snapshot()
        sh = (
            SessionHistoryBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_interview_index(0)
            .with_knowledge_snapshot(snapshot)
            .with_interview_metadata(make_interview_metadata())
            .with_language_profile(make_language_profile())
            .with_transcript([
                TranscriptEntry(question_index=0, question_id="q-001",
                                question_prompt="Describe REST.", answer_content="Ans1.", answer_attempt=1),
                TranscriptEntry(question_index=1, question_id="q-002",
                                question_prompt="Explain Big-O.", answer_content="Ans2.", answer_attempt=1),
            ])
            .with_question_timeline(make_question_timeline())
            .with_question_results([qr0, qr1])
            .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
            .with_created_at(FIXED_HISTORY_DT)
            .build()
        )
        result = ReplaySessionBuilder().with_session_history(sh).build()
        indices = [qr.question_index for qr in result.question_results]
        assert indices == sorted(indices)

    def test_empty_question_results(self):
        sh = _make_session_with_results(question_results=[], transcript=[])
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.question_results == ()
        assert result.question_count == 0


class TestReplaySessionBuilderTimeline:

    def test_timeline_total_positions_matches_question_count(self):
        qr = _make_question_result()
        sh = _make_session_with_results(question_results=[qr])
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.timeline.total_positions == result.question_count

    def test_timeline_entries_have_correct_position(self):
        qr0 = _make_question_result(question_id="q-001", question_index=0)
        sh = _make_session_with_results(question_results=[qr0])
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.timeline.entries[0].position == 0
        assert result.timeline.entries[0].question_id == "q-001"

    def test_empty_timeline_for_empty_results(self):
        sh = _make_session_with_results(question_results=[], transcript=[])
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.timeline.is_empty is True


class TestReplaySessionBuilderMetadata:

    def test_session_metadata_interview_index(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.session_metadata.interview_index == sh.interview_index + 1

    def test_session_metadata_session_date_from_created_at(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.session_metadata.session_date == sh.created_at

    def test_session_metadata_role(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.session_metadata.role == sh.interview_metadata.role

    def test_session_metadata_seniority_level_from_seniority(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.session_metadata.seniority_level == sh.interview_metadata.seniority

    def test_session_metadata_question_count_from_results(self):
        qr = _make_question_result()
        sh = _make_session_with_results(question_results=[qr])
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.session_metadata.question_count == len(sh.question_results)

    def test_session_duration_seconds_aggregated(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        # make_question_timeline has 120.0 + 180.0 = 300.0
        assert result.session_metadata.session_duration_seconds == pytest.approx(300.0)

    def test_session_duration_none_when_any_timeline_entry_is_none(self):
        snapshot = make_knowledge_snapshot()
        sh = (
            SessionHistoryBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_interview_index(0)
            .with_knowledge_snapshot(snapshot)
            .with_interview_metadata(make_interview_metadata())
            .with_language_profile(make_language_profile())
            .with_transcript([])
            .with_question_timeline([
                QuestionTimelineEntry(
                    question_index=0, question_id="q-001",
                    question_type="written", question_difficulty="medium",
                    duration_seconds=None,  # None → session_duration_seconds = None
                )
            ])
            .with_question_results([])
            .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
            .with_created_at(FIXED_HISTORY_DT)
            .build()
        )
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.session_metadata.session_duration_seconds is None


class TestReplaySessionBuilderInvariants:

    def test_rc_b_01_no_session_history_raises(self):
        with pytest.raises(ValueError, match="RC-B-01"):
            ReplaySessionBuilder().build()

    def test_rc_b_04_reasoning_level_raises(self):
        sh = _make_session_with_results()
        with pytest.raises(ValueError, match="RC-B-04"):
            (
                ReplaySessionBuilder()
                .with_session_history(sh)
                .with_replay_level(ReplayLevel.REASONING)
                .build()
            )

    def test_manifest_session_id_matches(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.manifest.session_id == sh.session_id

    def test_manifest_candidate_id_matches(self):
        sh = _make_session_with_results()
        result = ReplaySessionBuilder().with_session_history(sh).build()
        assert result.manifest.candidate_identity_id == sh.candidate_identity_id


class TestReplaySessionBuilderAsFailed:

    def test_as_failed_is_not_successful(self):
        result = ReplaySessionBuilder.as_failed(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            failure_reason="SessionHistory not found.",
        )
        assert result.is_successful is False
        assert result.failure_reason == "SessionHistory not found."

    def test_as_failed_session_id(self):
        result = ReplaySessionBuilder.as_failed(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            failure_reason="Error.",
        )
        assert result.session_id == SESSION_ID
        assert result.candidate_identity_id == CANDIDATE_ID

    def test_as_failed_returns_replay_session_v13(self):
        result = ReplaySessionBuilder.as_failed(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            failure_reason="Error.",
        )
        assert isinstance(result, ReplaySession)

    def test_as_failed_empty_question_results(self):
        result = ReplaySessionBuilder.as_failed(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            failure_reason="Error.",
        )
        assert result.question_results == ()
        assert result.timeline.is_empty is True


class TestReplaySessionBuilderReconstructionCompleteness:
    """P-08: Architectural test — every ReplaySession field must be explicitly
    assigned in ReplaySessionBuilder.build()."""

    def test_all_18_fields_explicitly_assigned_in_build(self):
        build_source = inspect.getsource(ReplaySessionBuilder.build)
        session_fields = list(ReplaySession.model_fields.keys())
        missing = [f for f in session_fields if f not in build_source]
        assert missing == [], (
            f"P-08 Reconstruction Completeness FAILURE: the following ReplaySession "
            f"fields are not explicitly referenced in ReplaySessionBuilder.build(): {missing}"
        )
