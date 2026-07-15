# tests/app/graph/nodes/test_replay_determinism.py
# EPIC-03 Phase 5 — Determinism validation suite.
#
# Test protocol (EPIC-03-IMPLEMENTATION-PLAN.md §2 Phase 5):
#   For each fixture, invoke replay_node twice; assert field-level equality on
#   all knowledge fields; exclude manifest.replay_timestamp and
#   manifest.replay_engine_version from equality assertion (Data Model §13.2).
#
# Fixture coverage (≥ 20 fixtures, all categories per Implementation Plan §2 Phase 5):
#   - Standard sessions with scoring_snapshot present.
#   - Sessions with scoring_snapshot=None.
#   - Sessions with question_results=() (empty).
#   - Coding question sessions.
#   - Sessions with replay_level=KNOWLEDGE.
#   - Sessions with follow_up_question present.
#   - Sessions with ai_hint_explanation present.
#   - Sessions with company=None.
#   - Sessions where all duration_seconds are None → session_duration_seconds=None.
#   - Sessions where all duration_seconds are non-None → session_duration_seconds aggregated.
#   - Sessions with 1, 3, 5, 10, 20 questions.
#
# P0/P1/P2 failure classification per Data Model §13.3.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import pytest

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_graph_state import ReplayGraphState
from domain.contracts.replay.replay_request import ReplayRequest
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
    make_knowledge_snapshot,
)
from tests.domain.contracts.session_history.conftest import (
    FIXED_HISTORY_DT,
    make_interview_metadata,
    make_language_profile,
)
from tests.domain.contracts.report.conftest import (
    make_scoring_snapshot,
    make_scoring_narrative,
)


# ---------------------------------------------------------------------------
# Failure classification (Data Model §13.3)
# ---------------------------------------------------------------------------

class DeterminismFailureClass:
    """P0/P1/P2 failure classification per EPIC-03-DATA-MODEL.md §13.3."""

    P0 = "P0"  # Identity field mismatch — blocking
    P1 = "P1"  # Knowledge field mismatch — blocking
    P2 = "P2"  # Non-deterministic metadata — informational


def classify_determinism_failure(field_name: str) -> str:
    """Return failure class for a given field mismatch."""
    identity_fields = {"session_id", "candidate_identity_id", "schema_version"}
    if field_name in identity_fields:
        return DeterminismFailureClass.P0
    manifest_non_deterministic = {"replay_timestamp", "replay_engine_version"}
    if field_name in manifest_non_deterministic:
        return DeterminismFailureClass.P2
    return DeterminismFailureClass.P1


# ---------------------------------------------------------------------------
# Fixture construction helpers
# ---------------------------------------------------------------------------

def _fresh_id() -> str:
    return str(uuid.uuid4())


def _make_question_result(
    question_id: str,
    question_index: int,
    question_type: str = "written",
    area_label: str = "Algorithms",
    question_prompt: str = "Describe REST.",
    score: float = 75.0,
    max_score: float = 100.0,
    feedback: str = "Good.",
    attempts: int = 1,
    follow_up_question: Optional[str] = None,
    execution_status: Optional[str] = None,
    passed_tests: Optional[int] = None,
    total_tests: Optional[int] = None,
    ai_hint_explanation: Optional[str] = None,
    ai_hint_suggestion: Optional[str] = None,
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
        follow_up_question=follow_up_question,
        execution_status=execution_status,
        passed_tests=passed_tests,
        total_tests=total_tests,
        ai_hint_explanation=ai_hint_explanation,
        ai_hint_suggestion=ai_hint_suggestion,
    )


def _make_transcript_entry(
    question_index: int,
    question_id: str,
    question_prompt: str = "Describe REST.",
    answer_content: str = "REST is a style.",
) -> TranscriptEntry:
    return TranscriptEntry(
        question_index=question_index,
        question_id=question_id,
        question_prompt=question_prompt,
        answer_content=answer_content,
        answer_attempt=1,
    )


def _make_timeline_entry(
    question_index: int,
    question_id: str,
    duration_seconds: Optional[float] = 120.0,
    question_type: str = "written",
) -> QuestionTimelineEntry:
    return QuestionTimelineEntry(
        question_index=question_index,
        question_id=question_id,
        question_type=question_type,
        question_difficulty="medium",
        duration_seconds=duration_seconds,
    )


def _make_interview_metadata_no_company() -> InterviewMetadata:
    return InterviewMetadata(
        role="backend_engineer",
        seniority="Senior",
        interview_type="technical",
        interview_mode="written",
        session_language="en",
        question_count=1,
        company=None,
    )


def _build_session(
    session_id: str,
    candidate_id: str,
    question_results: list[QuestionResultRecord],
    transcript: list[TranscriptEntry],
    question_timeline: list[QuestionTimelineEntry],
    interview_metadata: Optional[InterviewMetadata] = None,
    with_scoring: bool = False,
    created_at: Optional[datetime] = None,
) -> SessionHistory:
    snapshot = make_knowledge_snapshot(session_id=session_id, candidate_id=candidate_id)
    im = interview_metadata or make_interview_metadata()
    builder = (
        SessionHistoryBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_id)
        .with_interview_index(0)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(im)
        .with_language_profile(make_language_profile(session_id=session_id))
        .with_transcript(transcript)
        .with_question_timeline(question_timeline)
        .with_question_results(question_results)
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(created_at or FIXED_HISTORY_DT)
    )
    if with_scoring:
        builder = (
            builder
            .with_scoring_snapshot(make_scoring_snapshot())
            .with_scoring_narrative(make_scoring_narrative())
        )
    return builder.build()


def _make_state(
    session_id: str,
    replay_level: ReplayLevel = ReplayLevel.PRESENTATION,
    replay_mode: ReplayMode = ReplayMode.STANDARD,
) -> ReplayGraphState:
    req = ReplayRequest(
        session_id=session_id,
        replay_mode=replay_mode,
        replay_level=replay_level,
    )
    return ReplayGraphState(request=req)


def _loader_for(sh: SessionHistory):
    def _loader(sid: str) -> Optional[SessionHistory]:
        return sh
    return _loader


# ---------------------------------------------------------------------------
# Core determinism assertion helpers
# ---------------------------------------------------------------------------

# Fields excluded from determinism assertion per Data Model §13.2.
_MANIFEST_NON_DETERMINISTIC_FIELDS = frozenset({"replay_timestamp", "replay_engine_version"})

# All knowledge fields of ReplaySessionV13 (18 fields per Data Model §2).
_KNOWLEDGE_FIELDS = (
    "session_id",
    "candidate_identity_id",
    "schema_version",
    "replay_mode",
    "replay_level",
    "profile_snapshot",
    "narrative",
    "coaching_snapshot",
    "scoring_snapshot",
    "question_results",
    "timeline",
    "session_metadata",
    "policy_versions",
    "knowledge_epoch",
    # "manifest" — partially excluded; checked field-by-field below
    "is_successful",
    "failure_reason",
    "observation_store_snapshot",
)

# Manifest sub-fields included in determinism assertion.
_MANIFEST_DETERMINISTIC_FIELDS = (
    "session_id",
    "candidate_identity_id",
    "replay_mode",
    "replay_level",
    "source_per_component",
)


def assert_deterministic(result1: ReplaySessionV13, result2: ReplaySessionV13) -> None:
    """Assert field-level equality on all knowledge fields.

    Excludes manifest.replay_timestamp and manifest.replay_engine_version
    per Data Model §13.2. Any mismatch is classified (P0/P1/P2) and raised.
    """
    failures: list[str] = []

    for field in _KNOWLEDGE_FIELDS:
        v1 = getattr(result1, field)
        v2 = getattr(result2, field)
        if v1 != v2:
            cls = classify_determinism_failure(field)
            failures.append(f"[{cls}] field={field!r}: {v1!r} != {v2!r}")

    for sub_field in _MANIFEST_DETERMINISTIC_FIELDS:
        v1 = getattr(result1.manifest, sub_field)
        v2 = getattr(result2.manifest, sub_field)
        if v1 != v2:
            cls = classify_determinism_failure(sub_field)
            failures.append(
                f"[{cls}] manifest.{sub_field!r}: {v1!r} != {v2!r}"
            )

    if failures:
        raise AssertionError(
            "Determinism violation detected:\n" + "\n".join(failures)
        )


def _run_twice_and_assert(sh: SessionHistory, replay_level: ReplayLevel = ReplayLevel.PRESENTATION) -> None:
    """Run replay_node twice for the given fixture and assert deterministic output."""
    state = _make_state(sh.session_id, replay_level=replay_level)
    loader = _loader_for(sh)

    out1 = replay_node(state, session_loader=loader)
    out2 = replay_node(state, session_loader=loader)

    r1 = out1["result"]
    r2 = out2["result"]

    assert isinstance(r1, ReplaySessionV13)
    assert isinstance(r2, ReplaySessionV13)
    assert_deterministic(r1, r2)


# ---------------------------------------------------------------------------
# Fixture catalogue (≥ 20 fixtures, all categories covered)
# ---------------------------------------------------------------------------

class TestDeterminismStandardWithScoring:
    """Fixture F-01: Standard session with scoring_snapshot present."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid, duration_seconds=120.0)]
        sh = _build_session(sid, cid, [qr], tx, tl, with_scoring=True)
        _run_twice_and_assert(sh)


class TestDeterminismStandardNoScoring:
    """Fixture F-02: Standard session with scoring_snapshot=None."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl, with_scoring=False)
        _run_twice_and_assert(sh)


class TestDeterminismEmptyQuestionResults:
    """Fixture F-03: Session with question_results=() (empty)."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        sh = _build_session(sid, cid, [], [], [])
        _run_twice_and_assert(sh)


class TestDeterminismCodingQuestion:
    """Fixture F-04: Coding question session (with execution_status, passed_tests, total_tests)."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-code-001"
        qr = _make_question_result(
            question_id=qid,
            question_index=0,
            question_type="coding",
            execution_status="passed",
            passed_tests=5,
            total_tests=5,
        )
        tx = [_make_transcript_entry(0, qid, answer_content="def foo(): pass")]
        tl = [_make_timeline_entry(0, qid, question_type="coding")]
        sh = _build_session(sid, cid, [qr], tx, tl)
        _run_twice_and_assert(sh)


class TestDeterminismKnowledgeLevel:
    """Fixture F-05: Session with replay_level=KNOWLEDGE."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        _run_twice_and_assert(sh, replay_level=ReplayLevel.KNOWLEDGE)


class TestDeterminismWithFollowUpQuestion:
    """Fixture F-06: Session with follow_up_question present."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(
            question_id=qid,
            question_index=0,
            follow_up_question="Can you elaborate on caching?",
        )
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        _run_twice_and_assert(sh)


class TestDeterminismWithAiHint:
    """Fixture F-07: Session with ai_hint_explanation present."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(
            question_id=qid,
            question_index=0,
            ai_hint_explanation="Consider using a hash map.",
            ai_hint_suggestion="Use O(1) lookup via dict.",
        )
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        _run_twice_and_assert(sh)


class TestDeterminismCompanyNone:
    """Fixture F-08: Session with company=None."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid)]
        im = _make_interview_metadata_no_company()
        sh = _build_session(sid, cid, [qr], tx, tl, interview_metadata=im)
        _run_twice_and_assert(sh)


class TestDeterminismAllDurationsNone:
    """Fixture F-09: All question_timeline duration_seconds=None → session_duration_seconds=None."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid, duration_seconds=None)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        out1 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        out2 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        assert out1["result"].session_metadata.session_duration_seconds is None
        assert out2["result"].session_metadata.session_duration_seconds is None
        assert_deterministic(out1["result"], out2["result"])


class TestDeterminismAllDurationsPresent:
    """Fixture F-10: All duration_seconds non-None → session_duration_seconds aggregated."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid, duration_seconds=90.0)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        out1 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        out2 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        assert out1["result"].session_metadata.session_duration_seconds == 90.0
        assert out2["result"].session_metadata.session_duration_seconds == 90.0
        assert_deterministic(out1["result"], out2["result"])


class TestDeterminism1Question:
    """Fixture F-11: Session with 1 question."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qids = ["q-001"]
        qrs = [_make_question_result(question_id=qids[0], question_index=0)]
        txs = [_make_transcript_entry(0, qids[0])]
        tls = [_make_timeline_entry(0, qids[0])]
        sh = _build_session(sid, cid, qrs, txs, tls)
        _run_twice_and_assert(sh)


class TestDeterminism3Questions:
    """Fixture F-12: Session with 3 questions."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qids = [f"q-{i:03d}" for i in range(3)]
        qrs = [
            _make_question_result(question_id=qids[i], question_index=i, question_prompt=f"Q{i}?")
            for i in range(3)
        ]
        txs = [_make_transcript_entry(i, qids[i], question_prompt=f"Q{i}?") for i in range(3)]
        tls = [_make_timeline_entry(i, qids[i]) for i in range(3)]
        sh = _build_session(sid, cid, qrs, txs, tls)
        _run_twice_and_assert(sh)


class TestDeterminism5Questions:
    """Fixture F-13: Session with 5 questions."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        n = 5
        qids = [f"q-{i:03d}" for i in range(n)]
        qrs = [
            _make_question_result(question_id=qids[i], question_index=i, question_prompt=f"Q{i}?")
            for i in range(n)
        ]
        txs = [_make_transcript_entry(i, qids[i], question_prompt=f"Q{i}?") for i in range(n)]
        tls = [_make_timeline_entry(i, qids[i]) for i in range(n)]
        sh = _build_session(sid, cid, qrs, txs, tls)
        _run_twice_and_assert(sh)


class TestDeterminism10Questions:
    """Fixture F-14: Session with 10 questions."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        n = 10
        qids = [f"q-{i:03d}" for i in range(n)]
        qrs = [
            _make_question_result(question_id=qids[i], question_index=i, question_prompt=f"Q{i}?")
            for i in range(n)
        ]
        txs = [_make_transcript_entry(i, qids[i], question_prompt=f"Q{i}?") for i in range(n)]
        tls = [_make_timeline_entry(i, qids[i]) for i in range(n)]
        sh = _build_session(sid, cid, qrs, txs, tls)
        _run_twice_and_assert(sh)


class TestDeterminism20Questions:
    """Fixture F-15: Session with 20 questions."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        n = 20
        qids = [f"q-{i:03d}" for i in range(n)]
        qrs = [
            _make_question_result(question_id=qids[i], question_index=i, question_prompt=f"Q{i}?")
            for i in range(n)
        ]
        txs = [_make_transcript_entry(i, qids[i], question_prompt=f"Q{i}?") for i in range(n)]
        tls = [_make_timeline_entry(i, qids[i]) for i in range(n)]
        sh = _build_session(sid, cid, qrs, txs, tls)
        _run_twice_and_assert(sh)


class TestDeterminismMixedCodingAndWritten:
    """Fixture F-16: Session mixing coding and written questions."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qids = ["q-written-001", "q-code-002"]
        qrs = [
            _make_question_result(question_id=qids[0], question_index=0, question_type="written"),
            _make_question_result(
                question_id=qids[1],
                question_index=1,
                question_type="coding",
                execution_status="passed",
                passed_tests=3,
                total_tests=3,
            ),
        ]
        txs = [
            _make_transcript_entry(0, qids[0], answer_content="REST is stateless."),
            _make_transcript_entry(1, qids[1], answer_content="def solve(): pass"),
        ]
        tls = [
            _make_timeline_entry(0, qids[0], question_type="written"),
            _make_timeline_entry(1, qids[1], question_type="coding"),
        ]
        sh = _build_session(sid, cid, qrs, txs, tls)
        _run_twice_and_assert(sh)


class TestDeterminismMultipleDurations:
    """Fixture F-17: Session with multiple questions, all durations present → aggregated sum."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        n = 3
        durations = [60.0, 90.0, 120.0]
        qids = [f"q-{i:03d}" for i in range(n)]
        qrs = [
            _make_question_result(question_id=qids[i], question_index=i, question_prompt=f"Q{i}?")
            for i in range(n)
        ]
        txs = [_make_transcript_entry(i, qids[i], question_prompt=f"Q{i}?") for i in range(n)]
        tls = [_make_timeline_entry(i, qids[i], duration_seconds=durations[i]) for i in range(n)]
        sh = _build_session(sid, cid, qrs, txs, tls)
        out1 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        out2 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        assert out1["result"].session_metadata.session_duration_seconds == 270.0
        assert out2["result"].session_metadata.session_duration_seconds == 270.0
        assert_deterministic(out1["result"], out2["result"])


class TestDeterminismMixedDurations:
    """Fixture F-18: Session with mixed None/non-None durations → session_duration_seconds=None."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qids = ["q-001", "q-002"]
        qrs = [
            _make_question_result(question_id=qids[i], question_index=i, question_prompt=f"Q{i}?")
            for i in range(2)
        ]
        txs = [_make_transcript_entry(i, qids[i], question_prompt=f"Q{i}?") for i in range(2)]
        tls = [
            _make_timeline_entry(0, qids[0], duration_seconds=60.0),
            _make_timeline_entry(1, qids[1], duration_seconds=None),
        ]
        sh = _build_session(sid, cid, qrs, txs, tls)
        out1 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        out2 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        assert out1["result"].session_metadata.session_duration_seconds is None
        assert out2["result"].session_metadata.session_duration_seconds is None
        assert_deterministic(out1["result"], out2["result"])


class TestDeterminismScoringWithKnowledgeLevel:
    """Fixture F-19: Scoring present with replay_level=KNOWLEDGE."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl, with_scoring=True)
        _run_twice_and_assert(sh, replay_level=ReplayLevel.KNOWLEDGE)


class TestDeterminismFollowUpAndHintCombined:
    """Fixture F-20: follow_up_question and ai_hint both present."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(
            question_id=qid,
            question_index=0,
            follow_up_question="What about edge cases?",
            ai_hint_explanation="Think about boundary conditions.",
            ai_hint_suggestion="Test with empty input.",
        )
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        _run_twice_and_assert(sh)


class TestDeterminismMultipleStrengthsAndWeaknesses:
    """Fixture F-21: Questions with strengths/weaknesses tuples."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = QuestionResultRecord(
            question_id=qid,
            question_index=0,
            question_type="written",
            area_label="System Design",
            question_prompt="Design a URL shortener.",
            score=80.0,
            max_score=100.0,
            feedback="Good distributed design.",
            strengths=("Clear API design", "Handled load balancing"),
            weaknesses=("Missing cache invalidation", "No rate limiting"),
            attempts=1,
        )
        tx = [_make_transcript_entry(0, qid, question_prompt="Design a URL shortener.")]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        _run_twice_and_assert(sh)


class TestDeterminismTranscriptAnswerJoin:
    """Fixture F-22: candidate_answer populated via question_id join is stable."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-join-001"
        answer_text = "The answer is 42, because of the distributed consensus."
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid, answer_content=answer_text)]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        out1 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        out2 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        # Verify join populated correctly.
        assert out1["result"].question_results[0].candidate_answer == answer_text
        assert out2["result"].question_results[0].candidate_answer == answer_text
        assert_deterministic(out1["result"], out2["result"])


class TestDeterminismMissingTranscriptAnswer:
    """Fixture F-23: candidate_answer defaults to empty string for unmatched question_id."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid_result = "q-result-001"
        qid_transcript = "q-different-001"
        qr = _make_question_result(question_id=qid_result, question_index=0)
        tx = [_make_transcript_entry(0, qid_transcript, question_prompt="Describe REST.")]
        tl = [_make_timeline_entry(0, qid_result)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        out1 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        out2 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        # No transcript match → candidate_answer = "".
        assert out1["result"].question_results[0].candidate_answer == ""
        assert out2["result"].question_results[0].candidate_answer == ""
        assert_deterministic(out1["result"], out2["result"])


class TestDeterminismTimelineOrdering:
    """Fixture F-24: Timeline ordering is stable across invocations."""

    def test_deterministic_replay(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        n = 5
        qids = [f"q-{i:03d}" for i in range(n)]
        qrs = [
            _make_question_result(question_id=qids[i], question_index=i, question_prompt=f"Q{i}?")
            for i in range(n)
        ]
        txs = [_make_transcript_entry(i, qids[i], question_prompt=f"Q{i}?") for i in range(n)]
        tls = [_make_timeline_entry(i, qids[i]) for i in range(n)]
        sh = _build_session(sid, cid, qrs, txs, tls)
        out1 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        out2 = replay_node(_make_state(sid), session_loader=_loader_for(sh))
        assert [e.position for e in out1["result"].timeline.entries] == list(range(n))
        assert [e.position for e in out2["result"].timeline.entries] == list(range(n))
        assert_deterministic(out1["result"], out2["result"])


class TestDeterminismManifestTimestampExcluded:
    """manifest.replay_timestamp is non-deterministic and must NOT be asserted equal."""

    def test_manifest_timestamp_excluded_from_assertion(self) -> None:
        sid = _fresh_id()
        cid = _fresh_id()
        qid = "q-001"
        qr = _make_question_result(question_id=qid, question_index=0)
        tx = [_make_transcript_entry(0, qid)]
        tl = [_make_timeline_entry(0, qid)]
        sh = _build_session(sid, cid, [qr], tx, tl)
        state = _make_state(sid)
        loader = _loader_for(sh)
        out1 = replay_node(state, session_loader=loader)
        out2 = replay_node(state, session_loader=loader)
        # The timestamps may differ (non-deterministic); assert_deterministic must not fail on them.
        assert_deterministic(out1["result"], out2["result"])
        # Verify the field exists and is a datetime.
        assert isinstance(out1["result"].manifest.replay_timestamp, datetime)
        assert isinstance(out2["result"].manifest.replay_timestamp, datetime)


class TestDeterminismFailureClassification:
    """P0/P1/P2 classification logic is present and correct."""

    def test_identity_field_is_p0(self) -> None:
        assert classify_determinism_failure("session_id") == DeterminismFailureClass.P0
        assert classify_determinism_failure("candidate_identity_id") == DeterminismFailureClass.P0
        assert classify_determinism_failure("schema_version") == DeterminismFailureClass.P0

    def test_knowledge_field_is_p1(self) -> None:
        assert classify_determinism_failure("profile_snapshot") == DeterminismFailureClass.P1
        assert classify_determinism_failure("question_results") == DeterminismFailureClass.P1
        assert classify_determinism_failure("scoring_snapshot") == DeterminismFailureClass.P1
        assert classify_determinism_failure("session_metadata") == DeterminismFailureClass.P1

    def test_manifest_non_deterministic_fields_are_p2(self) -> None:
        assert classify_determinism_failure("replay_timestamp") == DeterminismFailureClass.P2
        assert classify_determinism_failure("replay_engine_version") == DeterminismFailureClass.P2
