# tests/domain/plugins/feature/updaters/test_updater_integration.py

import pytest

from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.plugins.feature.updaters.technical_skill_feature_updater import TechnicalSkillFeatureUpdater
from domain.plugins.feature.updaters.reasoning_feature_updater import ReasoningFeatureUpdater
from domain.plugins.feature.updaters.confidence_feature_updater import ConfidenceFeatureUpdater
from domain.plugins.feature.updaters.coverage_feature_updater import CoverageFeatureUpdater
from domain.plugins.feature.updaters.trend_feature_updater import TrendFeatureUpdater
from services.feature_engine.feature_engine import FeatureEngine
from services.feature_engine.feature_engine_context import FeatureEngineContext
from tests.domain.plugins.feature.updaters.conftest import make_obs
from tests.services.feature_engine.conftest import PassthroughComposer, make_snapshot, make_context

ALL_UPDATERS = [
    TechnicalSkillFeatureUpdater(),
    ReasoningFeatureUpdater(),
    ConfidenceFeatureUpdater(),
    CoverageFeatureUpdater(),
    TrendFeatureUpdater(),
]
COMPOSER = PassthroughComposer()


# --- Registration compatibility ---

def test_all_updater_ids_unique():
    ids = [u.updater_id for u in ALL_UPDATERS]
    assert len(ids) == len(set(ids))


def test_invocation_orders_unique():
    orders = [u.invocation_order for u in ALL_UPDATERS]
    assert len(orders) == len(set(orders))


def test_invocation_orders_sorted():
    orders = [u.invocation_order for u in ALL_UPDATERS]
    assert orders == sorted(orders)


def test_feature_engine_accepts_all_updaters():
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    assert set(engine.registered_updater_ids) == {
        "technical_skill_updater", "reasoning_updater",
        "confidence_updater", "coverage_updater", "trend_updater",
    }


# --- FeatureEngine integration: run with technical skill observations ---

def test_engine_run_technical_skill():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, question_index=0),
        make_obs(ObservationType.TECHNICAL_DEPTH, question_index=1),
        make_obs(ObservationType.TECHNICAL_STRENGTH, question_index=2),
    ]
    snap = ObservationSnapshot.from_observations("sess", obs)
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=2, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    result = engine.run(ctx)
    assert result.is_successful
    type_ids = {f.feature_identity.feature_type_id for f in result.features}
    assert "technical_skill_feature" in type_ids


def test_engine_run_reasoning():
    obs = [
        make_obs(ObservationType.REASONING_DEPTH_HIGH, question_index=0),
        make_obs(ObservationType.REASONING_IMPROVING, question_index=1),
    ]
    snap = ObservationSnapshot.from_observations("sess", obs)
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=1, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    result = engine.run(ctx)
    assert result.is_successful
    type_ids = {f.feature_identity.feature_type_id for f in result.features}
    assert "reasoning_feature" in type_ids


def test_engine_run_confidence():
    obs = [
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, question_index=0),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, question_index=1),
    ]
    snap = ObservationSnapshot.from_observations("sess", obs)
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=1, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    result = engine.run(ctx)
    assert result.is_successful
    type_ids = {f.feature_identity.feature_type_id for f in result.features}
    assert "confidence_feature" in type_ids


def test_engine_run_coverage():
    obs = [
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, question_index=0),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, question_index=1),
        make_obs(ObservationType.KNOWLEDGE_CROSS_AREA_CONSISTENT, question_index=2),
    ]
    snap = ObservationSnapshot.from_observations("sess", obs)
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=2, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    result = engine.run(ctx)
    assert result.is_successful
    type_ids = {f.feature_identity.feature_type_id for f in result.features}
    assert "coverage_feature" in type_ids


def test_engine_run_trend():
    obs = [
        make_obs(ObservationType.PERFORMANCE_IMPROVING, question_index=0),
        make_obs(ObservationType.BEHAVIORAL_GROWTH, question_index=1),
        make_obs(ObservationType.PERFORMANCE_IMPROVING, question_index=2),
    ]
    snap = ObservationSnapshot.from_observations("sess", obs)
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=2, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    result = engine.run(ctx)
    assert result.is_successful
    type_ids = {f.feature_identity.feature_type_id for f in result.features}
    assert "trend_feature" in type_ids


# --- Engine with empty snapshot ---

def test_engine_run_empty_snapshot():
    snap = ObservationSnapshot.from_observations("sess", [])
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=0, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    result = engine.run(ctx)
    assert result.is_successful
    assert len(result.features) == 0


# --- Observation filtering: updater only receives its types ---

def test_technical_updater_not_polluted_by_other_types():
    obs_tech = [make_obs(ObservationType.TECHNICAL_CORRECTNESS, question_index=0)]
    obs_reasoning = [make_obs(ObservationType.REASONING_DEPTH_HIGH, question_index=0)]
    updater = TechnicalSkillFeatureUpdater()
    result_mixed = updater.produce(obs_tech + obs_reasoning)
    result_pure = updater.produce(obs_tech)
    # Both should produce a candidate for technical skill
    assert len(result_mixed) == 1
    assert len(result_pure) == 1
    assert result_mixed[0].candidate_value == result_pure[0].candidate_value


# --- Determinism across repeated engine runs ---

def test_engine_deterministic():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, question_index=0),
        make_obs(ObservationType.REASONING_DEPTH_HIGH, question_index=1),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, question_index=2),
    ]
    snap = ObservationSnapshot.from_observations("sess", obs)
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=2, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    r1 = engine.run(ctx)
    r2 = engine.run(ctx)
    values1 = {f.feature_identity.feature_type_id: f.value for f in r1.features}
    values2 = {f.feature_identity.feature_type_id: f.value for f in r2.features}
    assert values1 == values2


# --- All candidates have proper updater_id ---

def test_candidates_have_correct_updater_id():
    obs = [make_obs(ObservationType.TECHNICAL_CORRECTNESS, question_index=0)]
    updater = TechnicalSkillFeatureUpdater()
    candidates = updater.produce(obs)
    for c in candidates:
        assert c.updater_id == "technical_skill_updater"


# --- Invocation order in engine ---

def test_engine_invokes_in_order():
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    orders = [u.invocation_order for u in engine._updaters]
    assert orders == sorted(orders)


# --- Mixed observations: multiple features produced ---

def test_engine_produces_multiple_feature_types():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, question_index=0),
        make_obs(ObservationType.REASONING_DEPTH_HIGH, question_index=1),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, question_index=2),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, question_index=3),
        make_obs(ObservationType.KNOWLEDGE_DEMONSTRATED, question_index=4),
        make_obs(ObservationType.PERFORMANCE_IMPROVING, question_index=5),
        make_obs(ObservationType.PERFORMANCE_IMPROVING, question_index=6),
    ]
    snap = ObservationSnapshot.from_observations("sess", obs)
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=6, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    result = engine.run(ctx)
    assert result.is_successful
    assert len(result.features) >= 4


# --- Confidence valid in produced features ---

def test_all_feature_confidences_valid():
    obs = [
        make_obs(ObservationType.TECHNICAL_CORRECTNESS, question_index=0),
        make_obs(ObservationType.REASONING_DEPTH_HIGH, question_index=1),
        make_obs(ObservationType.CONFIDENCE_WELL_CALIBRATED, question_index=2),
    ]
    snap = ObservationSnapshot.from_observations("sess", obs)
    ctx = FeatureEngineContext(
        session_id="sess", candidate_identity_id="cand",
        current_question_index=2, snapshot=snap,
    )
    engine = FeatureEngine(updaters=ALL_UPDATERS, composer=COMPOSER)
    result = engine.run(ctx)
    for f in result.features:
        assert 0.0 <= f.quality.confidence.value <= 1.0
