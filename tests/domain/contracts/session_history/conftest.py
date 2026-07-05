# tests/domain/contracts/session_history/conftest.py
# Shared fixtures for SessionHistory contract tests — reuses KnowledgeSnapshot fixtures

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.contracts.language.execution_policy import ExecutionPolicy
from domain.contracts.language.language_policy import LanguagePolicy
from domain.contracts.language.language_profile import LanguageProfile, SessionMode
from domain.contracts.language.language_selection_strategy import LanguageSelectionStrategy
from domain.contracts.language.programming_language import ProgrammingLanguage
from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    ReplayMetadata,
    SessionHistory,
    TranscriptEntry,
)
from domain.contracts.session_history.session_history_builder import SessionHistoryBuilder

# Reuse KnowledgeSnapshot fixture helpers
from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    FIXED_DT,
    make_knowledge_snapshot,
)

HISTORY_ID = "hist-test-001"
INTERVIEW_INDEX = 0
FIXED_HISTORY_DT = datetime(2026, 7, 3, 0, 0, 0, tzinfo=timezone.utc)

PYTHON_LANG = ProgrammingLanguage(
    language_id="python",
    display_name="Python",
    language_version="3.12",
    language_family="python",
)


def make_language_profile(session_id: str = SESSION_ID) -> LanguageProfile:
    return LanguageProfile(
        session_id=session_id,
        session_mode=SessionMode.SINGLE,
        primary_language=PYTHON_LANG,
        active_languages=[PYTHON_LANG],
        selection_strategy=LanguageSelectionStrategy.DETERMINISTIC_ALTERNATING,
        language_sequence=["python"],
        execution_policies=[
            ExecutionPolicy(language_id="python")
        ],
        language_policies=[
            LanguagePolicy(language_id="python", policy_version="1.0")
        ],
    )


def make_interview_metadata() -> InterviewMetadata:
    return InterviewMetadata(
        role="backend_engineer",
        seniority="Senior",
        interview_type="technical",
        interview_mode="written",
        session_language="en",
        question_count=5,
        company="Acme Corp",
    )


def make_transcript() -> list[TranscriptEntry]:
    return [
        TranscriptEntry(
            question_index=0,
            question_id="q-001",
            question_prompt="Describe REST principles.",
            answer_content="REST stands for...",
            answer_attempt=1,
        ),
        TranscriptEntry(
            question_index=1,
            question_id="q-002",
            question_prompt="Explain Big-O notation.",
            answer_content="Big-O describes...",
            answer_attempt=1,
        ),
    ]


def make_question_timeline() -> list[QuestionTimelineEntry]:
    return [
        QuestionTimelineEntry(
            question_index=0,
            question_id="q-001",
            question_type="written",
            question_difficulty="medium",
            duration_seconds=120.0,
        ),
        QuestionTimelineEntry(
            question_index=1,
            question_id="q-002",
            question_type="written",
            question_difficulty="hard",
            duration_seconds=180.0,
        ),
    ]


def make_session_history(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
    interview_index: int = INTERVIEW_INDEX,
) -> SessionHistory:
    snapshot = make_knowledge_snapshot(
        session_id=session_id,
        candidate_id=candidate_id,
    )
    return (
        SessionHistoryBuilder()
        .with_session_id(session_id)
        .with_candidate_identity_id(candidate_id)
        .with_interview_index(interview_index)
        .with_knowledge_snapshot(snapshot)
        .with_interview_metadata(make_interview_metadata())
        .with_language_profile(make_language_profile(session_id=session_id))
        .with_transcript(make_transcript())
        .with_question_timeline(make_question_timeline())
        .with_replay_metadata(ReplayMetadata(snapshot_is_complete=True))
        .with_created_at(FIXED_HISTORY_DT)
        .build()
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def candidate_id() -> str:
    return CANDIDATE_ID


@pytest.fixture
def session_id() -> str:
    return SESSION_ID


@pytest.fixture
def language_profile() -> LanguageProfile:
    return make_language_profile()


@pytest.fixture
def interview_metadata() -> InterviewMetadata:
    return make_interview_metadata()


@pytest.fixture
def session_history() -> SessionHistory:
    return make_session_history()
