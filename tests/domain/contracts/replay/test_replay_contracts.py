# tests/domain/contracts/replay/test_replay_contracts.py
# V1.3 migration — ReplayResult, ReplayOrchestrator, validate_result, from_result deleted.
# Tests retained: ReplayContext contracts, ReplayManifest contracts, ReplayValidator.validate_context.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.contracts.replay.replay_context import ReplayContext
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode, ReplaySourcePriority
from domain.contracts.replay.replay_manifest import ReplayManifest
from domain.contracts.replay.replay_validator import ReplayValidator

from .conftest import CANDIDATE_ID, SESSION_ID, make_knowledge_snapshot


# =============================================================================
# CONTRACT TESTS — ReplayContext
# =============================================================================

class TestReplayContextContracts:

    def test_standard_context_construction(self, standard_context):
        assert standard_context.session_id == SESSION_ID
        assert standard_context.candidate_identity_id == CANDIDATE_ID
        assert standard_context.replay_mode == ReplayMode.STANDARD
        assert standard_context.replay_level == ReplayLevel.PRESENTATION

    def test_context_immutable(self, standard_context):
        with pytest.raises((ValidationError, TypeError)):
            standard_context.session_id = "mutated"

    def test_context_rejects_session_id_mismatch(self, knowledge_snapshot):
        with pytest.raises(ValidationError, match="RC-CTX-01"):
            ReplayContext(
                session_id="wrong-session",
                candidate_identity_id=CANDIDATE_ID,
                knowledge_snapshot=knowledge_snapshot,
            )

    def test_context_rejects_candidate_id_mismatch(self, knowledge_snapshot):
        with pytest.raises(ValidationError, match="RC-CTX-01"):
            ReplayContext(
                session_id=SESSION_ID,
                candidate_identity_id="wrong-candidate",
                knowledge_snapshot=knowledge_snapshot,
            )

    def test_context_rejects_reasoning_level(self, knowledge_snapshot):
        with pytest.raises(ValidationError, match="RC-CTX-04"):
            ReplayContext(
                session_id=SESSION_ID,
                candidate_identity_id=CANDIDATE_ID,
                knowledge_snapshot=knowledge_snapshot,
                replay_level=ReplayLevel.REASONING,
            )

    def test_migration_mode_requires_operator_id(self, knowledge_snapshot):
        with pytest.raises(ValidationError, match="RC-CTX-03"):
            ReplayContext(
                session_id=SESSION_ID,
                candidate_identity_id=CANDIDATE_ID,
                knowledge_snapshot=knowledge_snapshot,
                replay_mode=ReplayMode.MIGRATION,
            )

    def test_migration_mode_accepts_operator_id(self, knowledge_snapshot):
        ctx = ReplayContext(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            knowledge_snapshot=knowledge_snapshot,
            replay_mode=ReplayMode.MIGRATION,
            operator_id="op-001",
        )
        assert ctx.operator_id == "op-001"
        assert ctx.replay_mode == ReplayMode.MIGRATION


# =============================================================================
# CONTRACT TESTS — ReplayManifest
# =============================================================================

class TestReplayManifestContracts:

    def test_manifest_factory_standard(self):
        source_map = {
            "profile": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "narrative": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "coaching": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "policy_versions": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
        }
        manifest = ReplayManifest.for_standard_replay(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            replay_level=ReplayLevel.PRESENTATION,
            replay_engine_version="1.0",
            source_per_component=source_map,
        )
        assert manifest.replay_mode == ReplayMode.STANDARD
        assert manifest.migration_metadata is None
        assert manifest.source_per_component["profile"] == ReplaySourcePriority.KNOWLEDGE_SNAPSHOT

    def test_manifest_immutable(self):
        source_map = {
            "profile": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "narrative": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "coaching": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "policy_versions": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
        }
        manifest = ReplayManifest.for_standard_replay(
            session_id=SESSION_ID,
            candidate_identity_id=CANDIDATE_ID,
            replay_level=ReplayLevel.PRESENTATION,
            replay_engine_version="1.0",
            source_per_component=source_map,
        )
        with pytest.raises((ValidationError, TypeError)):
            manifest.session_id = "mutated"


# =============================================================================
# VALIDATE_CONTEXT TESTS
# =============================================================================

class TestReplayValidatorContext:

    def test_validate_context_accepts_valid(self, standard_context):
        result = ReplayValidator.validate_context(standard_context)
        assert result.is_valid is True

    def test_validate_context_accepts_knowledge_level(self, knowledge_context):
        result = ReplayValidator.validate_context(knowledge_context)
        assert result.is_valid is True
