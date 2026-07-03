# tests/services/session_close/conftest.py
# Shared fixtures for SessionClosePipeline tests — reuses domain contract fixtures

from __future__ import annotations

import pytest

from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    ReplayMetadata,
    TranscriptEntry,
)
from services.session_close.session_close_configuration import SessionCloseConfiguration
from services.session_close.session_close_context import SessionCloseContext
from services.session_close.session_close_pipeline import SessionClosePipeline

from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_knowledge_snapshot,
)
from tests.domain.contracts.session_history.conftest import (
    make_language_profile,
    make_interview_metadata,
    make_transcript,
    make_question_timeline,
)

INTERVIEW_INDEX = 0


def make_context(
    session_id: str = SESSION_ID,
    candidate_id: str = CANDIDATE_ID,
    interview_index: int = INTERVIEW_INDEX,
) -> SessionCloseContext:
    ks = make_knowledge_snapshot(session_id=session_id, candidate_id=candidate_id)
    return SessionCloseContext(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        interview_index=interview_index,
        knowledge_snapshot=ks,
        interview_metadata=make_interview_metadata(),
        language_profile=make_language_profile(session_id=session_id),
        transcript=tuple(make_transcript()),
        question_timeline=tuple(make_question_timeline()),
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def context() -> SessionCloseContext:
    return make_context()


@pytest.fixture
def pipeline() -> SessionClosePipeline:
    return SessionClosePipeline()


@pytest.fixture
def default_config() -> SessionCloseConfiguration:
    return SessionCloseConfiguration()
