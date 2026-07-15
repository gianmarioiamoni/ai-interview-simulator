# tests/domain/contracts/replay/test_replay_feature_engine.py
# EPIC-03 Phase 3a — ReplayFeatureEngine unit tests.
# Verifies read-pass contract per EPIC-03-DOMAIN-CONTRACTS.md §8 and ADR-037 Decision 2.

from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "knowledge_snapshot"))
from conftest import (  # noqa: E402
    CANDIDATE_ID,
    make_candidate_profile_snapshot,
    make_profile_feature,
)

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.replay.replay_feature_engine import ReplayFeatureEngine


class TestReplayFeatureEngineGetFeatures:

    def test_returns_all_stored_features(self):
        snapshot = make_candidate_profile_snapshot()
        engine = ReplayFeatureEngine(snapshot)
        result = engine.get_features()
        assert result == snapshot.features

    def test_returns_tuple(self):
        snapshot = make_candidate_profile_snapshot()
        engine = ReplayFeatureEngine(snapshot)
        assert isinstance(engine.get_features(), tuple)

    def test_empty_snapshot_returns_empty_tuple(self):
        from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import CandidateProfileSnapshot
        empty_snap = CandidateProfileSnapshot(
            candidate_identity_id=CANDIDATE_ID,
            features=(),
            closed_at_question_index=0,
            total_feature_count=0,
            mean_confidence=0.0,
        )
        engine = ReplayFeatureEngine(empty_snap)
        assert engine.get_features() == ()

    def test_features_are_object_identity_from_snapshot(self):
        """RC-03 analog: features are exact object references from snapshot."""
        snapshot = make_candidate_profile_snapshot()
        engine = ReplayFeatureEngine(snapshot)
        assert engine.get_features() is snapshot.features


class TestReplayFeatureEngineGetFeature:

    def test_returns_feature_for_known_identity(self):
        feature = make_profile_feature(feature_type=FeatureType.REASONING)
        snapshot = make_candidate_profile_snapshot(features=(feature,))
        engine = ReplayFeatureEngine(snapshot)
        identity = FeatureIdentity.for_type(FeatureType.REASONING)
        result = engine.get_feature(identity)
        assert result is feature

    def test_returns_none_for_unknown_identity(self):
        snapshot = make_candidate_profile_snapshot(
            features=(make_profile_feature(feature_type=FeatureType.REASONING),)
        )
        engine = ReplayFeatureEngine(snapshot)
        identity = FeatureIdentity.for_type(FeatureType.COMMUNICATION)
        result = engine.get_feature(identity)
        assert result is None

    def test_returns_none_for_empty_snapshot(self):
        from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import CandidateProfileSnapshot
        empty_snap = CandidateProfileSnapshot(
            candidate_identity_id=CANDIDATE_ID,
            features=(),
            closed_at_question_index=0,
            total_feature_count=0,
            mean_confidence=0.0,
        )
        engine = ReplayFeatureEngine(empty_snap)
        identity = FeatureIdentity.for_type(FeatureType.REASONING)
        assert engine.get_feature(identity) is None


class TestReplayFeatureEngineProhibitedOperations:
    """ADR-037 D2: prohibited methods must raise RuntimeError."""

    def test_compute_feature_raises_runtime_error(self):
        engine = ReplayFeatureEngine(make_candidate_profile_snapshot())
        with pytest.raises(RuntimeError, match="compute_feature"):
            engine.compute_feature()

    def test_update_feature_raises_runtime_error(self):
        engine = ReplayFeatureEngine(make_candidate_profile_snapshot())
        with pytest.raises(RuntimeError, match="update_feature"):
            engine.update_feature()

    def test_accumulate_raises_runtime_error(self):
        engine = ReplayFeatureEngine(make_candidate_profile_snapshot())
        with pytest.raises(RuntimeError, match="accumulate"):
            engine.accumulate()


class TestReplayFeatureEngineArchitecturalInvariants:

    def test_no_live_feature_engine_import(self):
        """ADR-037 D2: ReplayFeatureEngine must not import live FeatureEngine."""
        import domain.contracts.replay.replay_feature_engine as module
        source = open(module.__file__).read()
        assert "from domain.contracts.feature.feature_engine" not in source
        assert "from app." not in source

    def test_no_longitudinal_profile_import(self):
        """I-R06: No LongitudinalProfile cross-reference."""
        import domain.contracts.replay.replay_feature_engine as module
        source = open(module.__file__).read()
        assert "LongitudinalProfile" not in source

    def test_stateless_across_instances(self):
        """Two engines on the same snapshot return identical feature sets."""
        snapshot = make_candidate_profile_snapshot()
        e1 = ReplayFeatureEngine(snapshot)
        e2 = ReplayFeatureEngine(snapshot)
        assert e1.get_features() == e2.get_features()
        assert e1.get_features() is e2.get_features()
