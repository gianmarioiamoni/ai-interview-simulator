# tests/ui/replay/test_replay_view_controller.py

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.ui.replay.replay_view_controller import ReplayViewController
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_manifest import ReplayManifest, ReplaySourcePriority
from domain.contracts.replay.replay_question_record import ReplayQuestionRecord
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.replay.replay_session_metadata import ReplaySessionMetadata
from domain.contracts.replay.replay_timeline import ReplayTimeline, ReplayTimelineEntry
from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_candidate_profile_snapshot,
    make_coaching_snapshot,
    make_narrative,
    make_policy_versions,
)

SESSION_DATE = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)


def _make_record(index: int) -> ReplayQuestionRecord:
    return ReplayQuestionRecord(
        question_id=f"q-{index:03d}",
        question_index=index,
        question_type="technical",
        area_label="Algorithms",
        question_prompt=f"Prompt {index}",
        candidate_answer=f"Answer {index}",
        score=70.0 + index,
        max_score=100.0,
        feedback="Feedback",
        attempts=1,
    )


def _make_session(*, question_count: int) -> ReplaySession:
    records = tuple(_make_record(i) for i in range(question_count))
    if question_count == 0:
        timeline = ReplayTimeline(
            entries=(),
            total_positions=0,
            first_position=-1,
            last_position=-1,
            is_empty=True,
        )
    else:
        entries = tuple(
            ReplayTimelineEntry(
                position=i,
                question_id=records[i].question_id,
                question_index=i,
                area_label=records[i].area_label,
                question_type=records[i].question_type,
            )
            for i in range(question_count)
        )
        timeline = ReplayTimeline(
            entries=entries,
            total_positions=question_count,
            first_position=0,
            last_position=question_count - 1,
            is_empty=False,
        )

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
            question_count=question_count,
        ),
        timeline=timeline,
        question_results=records,
        is_successful=True,
        failure_reason=None,
        replay_mode=ReplayMode.STANDARD,
        replay_level=ReplayLevel.PRESENTATION,
    )


def test_current_position_initialised_to_zero() -> None:
    controller = ReplayViewController(_make_session(question_count=3))
    assert controller.current_position == 0
    assert controller.is_at_first is True
    assert controller.is_at_last is False


def test_navigate_forward_increments_and_clamps_at_last() -> None:
    controller = ReplayViewController(_make_session(question_count=3))

    controller.navigate_forward()
    assert controller.current_position == 1
    controller.navigate_forward()
    assert controller.current_position == 2
    assert controller.is_at_last is True

    controller.navigate_forward()
    assert controller.current_position == 2


def test_navigate_backward_decrements_and_clamps_at_first() -> None:
    controller = ReplayViewController(_make_session(question_count=3))
    controller.navigate_forward()
    controller.navigate_forward()
    assert controller.current_position == 2

    controller.navigate_backward()
    assert controller.current_position == 1
    controller.navigate_backward()
    assert controller.current_position == 0
    assert controller.is_at_first is True

    controller.navigate_backward()
    assert controller.current_position == 0


def test_empty_session_dispatches_no_navigation() -> None:
    controller = ReplayViewController(_make_session(question_count=0))
    assert controller.current_position == 0
    assert controller.is_at_first is True
    assert controller.is_at_last is True

    controller.navigate_forward()
    controller.navigate_backward()
    assert controller.current_position == 0


def test_current_record_follows_position() -> None:
    session = _make_session(question_count=3)
    controller = ReplayViewController(session)

    assert controller.current_record is session.question_results[0]
    controller.navigate_forward()
    assert controller.current_record is session.question_results[1]
    controller.navigate_forward()
    assert controller.current_record is session.question_results[2]


def test_current_record_empty_session_raises() -> None:
    controller = ReplayViewController(_make_session(question_count=0))
    with pytest.raises(IndexError):
        _ = controller.current_record
