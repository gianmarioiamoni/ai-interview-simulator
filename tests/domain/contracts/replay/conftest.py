# tests/domain/contracts/replay/conftest.py
# Shared fixtures for Replay contract tests — reuse KnowledgeSnapshot fixtures

from __future__ import annotations

import sys
import os

import pytest

# Reuse knowledge_snapshot conftest helpers directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    SNAPSHOT_ID,
    make_knowledge_snapshot,
)

from domain.contracts.replay.replay_context import ReplayContext
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_session import ReplaySession


@pytest.fixture
def knowledge_snapshot():
    return make_knowledge_snapshot()


@pytest.fixture
def standard_context(knowledge_snapshot):
    return ReplayContext(
        session_id=SESSION_ID,
        candidate_identity_id=CANDIDATE_ID,
        knowledge_snapshot=knowledge_snapshot,
        replay_mode=ReplayMode.STANDARD,
        replay_level=ReplayLevel.PRESENTATION,
    )


@pytest.fixture
def knowledge_context(knowledge_snapshot):
    return ReplayContext(
        session_id=SESSION_ID,
        candidate_identity_id=CANDIDATE_ID,
        knowledge_snapshot=knowledge_snapshot,
        replay_mode=ReplayMode.STANDARD,
        replay_level=ReplayLevel.KNOWLEDGE,
    )


@pytest.fixture
def replay_session():
    return ReplaySession(validate_on_run=True)
