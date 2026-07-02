# tests/services/feature_engine/test_replay_feature_engine.py

import pytest

from domain.contracts.feature.feature_type import FeatureType
from services.feature_engine.feature_engine import FeatureEngineError
from services.feature_engine.replay_feature_engine import ReplayFeatureEngine
from tests.services.feature_engine.conftest import (
    PassthroughComposer,
    StubUpdater,
    make_candidate,
    make_context,
    make_snapshot,
)


def _make_replay_engine(value: str = "HIGH") -> ReplayFeatureEngine:
    replay_updater = StubUpdater(
        updater_id="replay_updater",
        invocation_order=1,
        candidates_to_produce=[make_candidate(FeatureType.REASONING, value)],
    )
    return ReplayFeatureEngine([replay_updater], PassthroughComposer())


class TestReplayFeatureEngineConstruction:
    def test_valid_construction(self) -> None:
        engine = _make_replay_engine()
        assert engine is not None

    def test_no_replay_updater_rejected(self) -> None:
        non_replay_updater = StubUpdater(updater_id="obs_updater", invocation_order=1)
        with pytest.raises(FeatureEngineError, match="replay_updater"):
            ReplayFeatureEngine([non_replay_updater], PassthroughComposer())


class TestReplayFeatureEngineRun:
    def test_replay_context_accepted(self) -> None:
        engine = _make_replay_engine()
        ctx = make_context(is_replay=True)
        result = engine.run(ctx)
        assert result.is_successful is True

    def test_live_context_rejected(self) -> None:
        engine = _make_replay_engine()
        ctx = make_context(is_replay=False)
        with pytest.raises(FeatureEngineError, match="is_replay"):
            engine.run(ctx)

    def test_produces_profile_features(self) -> None:
        engine = _make_replay_engine()
        ctx = make_context(is_replay=True)
        result = engine.run(ctx)
        assert result.feature_count >= 1

    def test_result_marks_is_replay(self) -> None:
        engine = _make_replay_engine()
        result = engine.run(make_context(is_replay=True))
        assert result.diagnostics.is_replay is True

    def test_feature_value_correct(self) -> None:
        engine = _make_replay_engine("MODERATE")
        result = engine.run(make_context(is_replay=True))
        assert result.features[0].value == "MODERATE"

    def test_session_id_propagated(self) -> None:
        engine = _make_replay_engine()
        result = engine.run(make_context(session_id="replay-session", is_replay=True))
        assert result.session_id == "replay-session"


class TestReplayFeatureEngineWithComparison:
    def test_no_delta_when_matching(self) -> None:
        engine = _make_replay_engine("HIGH")
        ctx = make_context(is_replay=True)
        base_result = engine.run(ctx)
        stored = base_result.features
        result = engine.run_with_comparison(ctx, stored)
        diag = result.diagnostics
        assert "no_delta" in (diag.reconstruction_delta_summary or "")

    def test_delta_detected_when_values_differ(self) -> None:
        engine = _make_replay_engine("HIGH")
        ctx = make_context(is_replay=True)

        # Make a "stored" feature with a different value
        from domain.contracts.feature.feature_identity import FeatureIdentity
        from domain.contracts.feature.feature_provenance import FeatureProvenance
        from domain.contracts.feature.feature_quality import (
            FeatureConfidence, FeatureMaturity, FeatureQuality, FeatureStability,
        )
        from domain.contracts.feature.profile_feature import ProfileFeature
        identity = FeatureIdentity.for_type(FeatureType.REASONING)
        prov = FeatureProvenance(
            feature_identity=identity,
            source_observation_ids=("obs-1",),
            computed_at_question_index=0,
            feature_engine_version="1.0.0",
            updater_id="replay_updater",
        )
        quality = FeatureQuality(
            confidence=FeatureConfidence(value=0.9),
            stability=FeatureStability(state="stable"),
            maturity=FeatureMaturity.from_observation_count(3),
        )
        stored_feature = ProfileFeature(
            feature_identity=identity,
            value="LOW",  # differs from "HIGH"
            quality=quality,
            provenance=prov,
            computed_at_question_index=0,
            candidate_identity_id="cand-001",
        )
        result = engine.run_with_comparison(ctx, (stored_feature,))
        assert result.diagnostics.reconstruction_delta_summary is not None
        assert "no_delta" not in (result.diagnostics.reconstruction_delta_summary or "")

    def test_delta_summary_shows_new_feature(self) -> None:
        engine = _make_replay_engine("HIGH")
        ctx = make_context(is_replay=True)
        # Stored has NO features — reconstructed has one
        result = engine.run_with_comparison(ctx, ())
        delta = result.diagnostics.reconstruction_delta_summary or ""
        assert "+" in delta

    def test_live_context_rejected_in_comparison(self) -> None:
        engine = _make_replay_engine()
        ctx = make_context(is_replay=False)
        with pytest.raises(FeatureEngineError):
            engine.run_with_comparison(ctx, ())
