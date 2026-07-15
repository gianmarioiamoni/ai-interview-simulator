# tests/domain/contracts/replay/test_replay_request.py
# EPIC-03 Phase 2a — ReplayRequest contract tests.
# Validates frozen immutability, extra=forbid, and model validators V-RRQ-01, V-RRQ-02.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_request import ReplayRequest


SESSION_ID = "session-abc-001"


class TestReplayRequestConstruction:

    def test_minimal_construction_uses_defaults(self):
        req = ReplayRequest(session_id=SESSION_ID)
        assert req.session_id == SESSION_ID
        assert req.replay_mode == ReplayMode.STANDARD
        assert req.replay_level == ReplayLevel.PRESENTATION
        assert req.operator_id is None

    def test_explicit_standard_mode(self):
        req = ReplayRequest(
            session_id=SESSION_ID,
            replay_mode=ReplayMode.STANDARD,
            replay_level=ReplayLevel.PRESENTATION,
        )
        assert req.replay_mode == ReplayMode.STANDARD

    def test_knowledge_level_accepted(self):
        req = ReplayRequest(session_id=SESSION_ID, replay_level=ReplayLevel.KNOWLEDGE)
        assert req.replay_level == ReplayLevel.KNOWLEDGE

    def test_migration_mode_with_operator_id(self):
        req = ReplayRequest(
            session_id=SESSION_ID,
            replay_mode=ReplayMode.MIGRATION,
            operator_id="op-001",
        )
        assert req.operator_id == "op-001"
        assert req.replay_mode == ReplayMode.MIGRATION

    def test_recovery_mode_with_operator_id(self):
        req = ReplayRequest(
            session_id=SESSION_ID,
            replay_mode=ReplayMode.RECOVERY,
            operator_id="op-002",
        )
        assert req.operator_id == "op-002"
        assert req.replay_mode == ReplayMode.RECOVERY


class TestReplayRequestImmutability:

    def test_frozen_raises_on_session_id_mutation(self):
        req = ReplayRequest(session_id=SESSION_ID)
        with pytest.raises((ValidationError, TypeError)):
            req.session_id = "mutated"

    def test_frozen_raises_on_mode_mutation(self):
        req = ReplayRequest(session_id=SESSION_ID)
        with pytest.raises((ValidationError, TypeError)):
            req.replay_mode = ReplayMode.MIGRATION

    def test_frozen_raises_on_level_mutation(self):
        req = ReplayRequest(session_id=SESSION_ID)
        with pytest.raises((ValidationError, TypeError)):
            req.replay_level = ReplayLevel.KNOWLEDGE


class TestReplayRequestExtraForbid:

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            ReplayRequest(session_id=SESSION_ID, unknown_field="value")  # type: ignore[call-arg]


class TestReplayRequestValidatorVRRQ01:
    """V-RRQ-01: ReplayLevel.REASONING is reserved."""

    def test_reasoning_level_raises(self):
        with pytest.raises(ValidationError, match="V-RRQ-01"):
            ReplayRequest(session_id=SESSION_ID, replay_level=ReplayLevel.REASONING)

    def test_reasoning_level_in_migration_mode_raises(self):
        with pytest.raises(ValidationError, match="V-RRQ-01"):
            ReplayRequest(
                session_id=SESSION_ID,
                replay_mode=ReplayMode.MIGRATION,
                replay_level=ReplayLevel.REASONING,
                operator_id="op-001",
            )


class TestReplayRequestValidatorVRRQ02:
    """V-RRQ-02: MIGRATION and RECOVERY modes require non-empty operator_id."""

    def test_migration_without_operator_id_raises(self):
        with pytest.raises(ValidationError, match="V-RRQ-02"):
            ReplayRequest(session_id=SESSION_ID, replay_mode=ReplayMode.MIGRATION)

    def test_migration_with_empty_operator_id_raises(self):
        with pytest.raises(ValidationError, match="V-RRQ-02"):
            ReplayRequest(
                session_id=SESSION_ID,
                replay_mode=ReplayMode.MIGRATION,
                operator_id="",
            )

    def test_recovery_without_operator_id_raises(self):
        with pytest.raises(ValidationError, match="V-RRQ-02"):
            ReplayRequest(session_id=SESSION_ID, replay_mode=ReplayMode.RECOVERY)

    def test_recovery_with_empty_operator_id_raises(self):
        with pytest.raises(ValidationError, match="V-RRQ-02"):
            ReplayRequest(
                session_id=SESSION_ID,
                replay_mode=ReplayMode.RECOVERY,
                operator_id="",
            )

    def test_standard_mode_without_operator_id_accepted(self):
        req = ReplayRequest(session_id=SESSION_ID, replay_mode=ReplayMode.STANDARD)
        assert req.operator_id is None
