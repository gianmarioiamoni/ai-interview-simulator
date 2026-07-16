# tests/ui/replay/fixtures/session_history_20q.py
# EPIC-04 Phase 6 — 20-question SessionHistory fixture for AA-08 profiling.

from __future__ import annotations

from domain.contracts.session_history.question_result_record import QuestionResultRecord
from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    ReplayMetadata,
    SessionHistory,
    TranscriptEntry,
)
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder
from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_knowledge_snapshot,
)
from tests.domain.contracts.session_history.conftest import (
    FIXED_HISTORY_DT,
    make_language_profile,
)

QUESTION_COUNT_20 = 20
SESSION_ID_20Q = f"{SESSION_ID}-20q"


def _question_result(index: int) -> QuestionResultRecord:
    return QuestionResultRecord(
        question_id=f"q-{index:03d}",
        question_index=index,
        question_type="written",
        area_label="Algorithms",
        question_prompt=f"Describe approach for question {index}.",
        score=60.0 + (index % 30),
        max_score=100.0,
        feedback=f"Feedback for question {index}.",
        strengths=("Clear structure.",),
        weaknesses=("Missed edge cases.",),
        attempts=1,
    )


def _transcript_entry(index: int) -> TranscriptEntry:
    return TranscriptEntry(
        question_index=index,
        question_id=f"q-{index:03d}",
        question_prompt=f"Describe approach for question {index}.",
        answer_content=f"Candidate answer for question {index}.",
        answer_attempt=1,
    )


def _timeline_entry(index: int) -> QuestionTimelineEntry:
    return QuestionTimelineEntry(
        question_index=index,
        question_id=f"q-{index:03d}",
        question_type="written",
        question_difficulty="medium",
        duration_seconds=90.0,
    )


def make_interview_metadata_20q() -> InterviewMetadata:
    return InterviewMetadata(
        role="backend_engineer",
        seniority="Senior",
        interview_type="technical",
        interview_mode="written",
        session_language="en",
        question_count=QUESTION_COUNT_20,
        company="Acme Corp",
    )


def make_session_history_20q(
    session_id: str = SESSION_ID_20Q,
    candidate_id: str = CANDIDATE_ID,
) -> SessionHistory:
    """Build a 20-question SessionHistory from domain contracts (AA-08 fixture)."""
    snapshot = make_knowledge_snapshot(session_id=session_id, candidate_id=candidate_id)
    results = [_question_result(i) for i in range(QUESTION_COUNT_20)]
    transcript = [_transcript_entry(i) for i in range(QUESTION_COUNT_20)]
    timeline = [_timeline_entry(i) for i in range(QUESTION_COUNT_20)]

    return (
        SessionHistoryBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_id)
        .with_interview_index(0)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata_20q())
        .with_language_profile(make_language_profile(session_id=session_id))
        .with_transcript(transcript)
        .with_question_timeline(timeline)
        .with_question_results(results)
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_HISTORY_DT)
        .build()
    )
