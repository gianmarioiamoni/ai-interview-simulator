# tests/domain/contracts/replay/test_replay_session.py
# EPIC-03 Phase 2e — ReplaySession contract tests.
# Validates frozen immutability, extra=forbid, 18-field set, and validators V-RS-01 to V-RS-06.

from __future__ import annotations

import sys
import os
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

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
from domain.contracts.replay.replay_manifest import ReplayManifest, ReplaySourcePriority
from domain.contracts.replay.replay_session_metadata import ReplaySessionMetadata
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.replay.replay_timeline import ReplayTimeline


SESSION_DATE = datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc)


def _make_manifest(
    session_id: str = SESSION_ID,
    candidate_identity_id: str = CANDIDATE_ID,
    replay_mode: ReplayMode = ReplayMode.STANDARD,
    replay_level: ReplayLevel = ReplayLevel.PRESENTATION,
) -> ReplayManifest:
    return ReplayManifest.for_standard_replay(
        session_id=session_id,
        candidate_identity_id=candidate_identity_id,
        replay_level=replay_level,
        replay_engine_version="1.0",
        source_per_component={
            "profile": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "narrative": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "coaching": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "policy_versions": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
        },
    )


def _make_metadata() -> ReplaySessionMetadata:
    return ReplaySessionMetadata(
        interview_index=1,
        session_date=SESSION_DATE,
        role="Software Engineer",
        seniority_level="Senior",
        interview_mode="technical",
        question_count=0,
    )


def _make_timeline() -> ReplayTimeline:
    return ReplayTimeline(
        entries=(),
        total_positions=0,
        first_position=-1,
        last_position=-1,
        is_empty=True,
    )


def _make(**overrides) -> ReplaySession:
    defaults = dict(
        session_id=SESSION_ID,
        candidate_identity_id=CANDIDATE_ID,
        profile_snapshot=make_candidate_profile_snapshot(),
        narrative=make_narrative(),
        coaching_snapshot=make_coaching_snapshot(),
        policy_versions=make_policy_versions(),
        knowledge_epoch="1",
        manifest=_make_manifest(),
        session_metadata=_make_metadata(),
        timeline=_make_timeline(),
        question_results=(),
        is_successful=True,
        failure_reason=None,
    )
    defaults.update(overrides)
    return ReplaySession(**defaults)


class TestReplaySessionConstruction:

    def test_minimal_construction(self):
        s = _make()
        assert s.session_id == SESSION_ID
        assert s.candidate_identity_id == CANDIDATE_ID
        assert s.schema_version == "1.0"
        assert s.replay_mode == ReplayMode.STANDARD
        assert s.replay_level == ReplayLevel.PRESENTATION
        assert s.is_successful is True
        assert s.failure_reason is None
        assert s.scoring_snapshot is None
        assert s.observation_store_snapshot is None
        assert s.question_results == ()
        assert s.question_count == 0

    def test_properties(self):
        s = _make()
        assert s.is_standard is True
        assert s.has_scoring is False
        assert s.has_provenance is False

    def test_knowledge_level_has_provenance(self):
        s = _make(
            replay_level=ReplayLevel.KNOWLEDGE,
            manifest=_make_manifest(replay_level=ReplayLevel.KNOWLEDGE),
        )
        assert s.has_provenance is True

    def test_failed_session_construction(self):
        s = _make(is_successful=False, failure_reason="SessionHistory not found.")
        assert s.is_successful is False
        assert s.failure_reason == "SessionHistory not found."


class TestReplaySessionImmutability:

    def test_frozen_raises_on_session_id_mutation(self):
        s = _make()
        with pytest.raises((ValidationError, TypeError)):
            s.session_id = "mutated"

    def test_frozen_raises_on_is_successful_mutation(self):
        s = _make()
        with pytest.raises((ValidationError, TypeError)):
            s.is_successful = False


class TestReplaySessionExtraForbid:

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            _make(unknown_field="bad")  # type: ignore[call-arg]


class TestReplaySessionValidatorVRS01:
    """V-RS-01: is_successful=False requires non-empty failure_reason."""

    def test_failed_without_reason_rejected(self):
        with pytest.raises(ValidationError, match="V-RS-01"):
            _make(is_successful=False, failure_reason=None)

    def test_failed_with_empty_reason_rejected(self):
        with pytest.raises(ValidationError, match="V-RS-01"):
            _make(is_successful=False, failure_reason="")

    def test_failed_with_reason_accepted(self):
        s = _make(is_successful=False, failure_reason="Error occurred.")
        assert s.is_successful is False


class TestReplaySessionValidatorVRS02:
    """V-RS-02: is_successful=True requires failure_reason is None."""

    def test_successful_with_reason_rejected(self):
        with pytest.raises(ValidationError, match="V-RS-02"):
            _make(is_successful=True, failure_reason="some reason")

    def test_successful_without_reason_accepted(self):
        s = _make(is_successful=True, failure_reason=None)
        assert s.is_successful is True


class TestReplaySessionValidatorVRS03:
    """V-RS-03: manifest.session_id must equal session_id."""

    def test_manifest_session_id_mismatch_rejected(self):
        wrong_manifest = _make_manifest(session_id="wrong-session")
        with pytest.raises(ValidationError, match="V-RS-03"):
            _make(manifest=wrong_manifest)


class TestReplaySessionValidatorVRS04:
    """V-RS-04: manifest.candidate_identity_id must equal candidate_identity_id."""

    def test_manifest_candidate_id_mismatch_rejected(self):
        wrong_manifest = _make_manifest(candidate_identity_id="wrong-candidate")
        with pytest.raises(ValidationError, match="V-RS-04"):
            _make(manifest=wrong_manifest)


class TestReplaySessionValidatorVRS05:
    """V-RS-05: replay_level must not be REASONING."""

    def test_reasoning_level_rejected(self):
        with pytest.raises(ValidationError, match="V-RS-05"):
            _make(
                replay_level=ReplayLevel.REASONING,
                manifest=_make_manifest(replay_level=ReplayLevel.REASONING),
            )


class TestReplaySessionValidatorVRS06:
    """V-RS-06: observation_store_snapshot must be None for PRESENTATION level."""

    def test_observation_store_in_presentation_rejected(self):
        with pytest.raises(ValidationError, match="V-RS-06"):
            _make(observation_store_snapshot=object())

    def test_observation_store_in_knowledge_accepted(self):
        s = _make(
            replay_level=ReplayLevel.KNOWLEDGE,
            manifest=_make_manifest(replay_level=ReplayLevel.KNOWLEDGE),
            observation_store_snapshot=object(),
        )
        assert s.observation_store_snapshot is not None
