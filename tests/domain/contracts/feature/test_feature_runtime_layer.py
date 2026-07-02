# tests/domain/contracts/feature/test_feature_runtime_layer.py
# E01-M4 — FeatureBatch, FeatureCollection, FeatureStatistics, FeatureDelta,
#           FeatureFilter, FeatureOrdering, FeatureComparison, FeatureSnapshotBuilder

import pytest

from domain.contracts.feature.feature_batch import FeatureBatch
from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.feature_comparison import FeatureCollectionComparison, FeatureComparison
from domain.contracts.feature.feature_delta import DeltaDirection, FeatureDelta, FeatureDeltaSet
from domain.contracts.feature.feature_filter import FeatureFilter
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_ordering import FeatureOrdering
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
    MATURITY_MATURE,
    MATURITY_DEVELOPING,
    MATURITY_NASCENT,
    STABILITY_STABLE,
    STABILITY_UNSTABLE,
    STABILITY_EMERGING,
)
from domain.contracts.feature.feature_snapshot_builder import FeatureSnapshotBuilder
from domain.contracts.feature.feature_statistics import FeatureStatistics
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_feature(
    feature_type: FeatureType = FeatureType.REASONING,
    value: str = "HIGH",
    confidence: float = 0.8,
    stability: str = STABILITY_STABLE,
    obs_count: int = 4,
    question_index: int = 3,
    candidate_id: str = "cand-1",
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
    quality = FeatureQuality(
        confidence=FeatureConfidence(value=confidence),
        stability=FeatureStability(state=stability),
        maturity=FeatureMaturity.from_observation_count(obs_count),
    )
    provenance = FeatureProvenance(
        feature_identity=identity,
        source_observation_ids=("obs-1",),
        computed_at_question_index=question_index,
        feature_engine_version="1.0.0",
        updater_id="test_updater",
    )
    return ProfileFeature(
        feature_identity=identity,
        value=value,
        quality=quality,
        provenance=provenance,
        computed_at_question_index=question_index,
        candidate_identity_id=candidate_id,
    )


@pytest.fixture()
def reasoning_feature() -> ProfileFeature:
    return _make_feature(FeatureType.REASONING, value="HIGH", confidence=0.8)


@pytest.fixture()
def confidence_feature() -> ProfileFeature:
    return _make_feature(
        FeatureType.CONFIDENCE, value="MODERATE", confidence=0.5, stability=STABILITY_UNSTABLE, obs_count=2
    )


@pytest.fixture()
def technical_feature() -> ProfileFeature:
    return _make_feature(
        FeatureType.TECHNICAL_SKILL, value="HIGH", confidence=0.9, stability=STABILITY_STABLE, obs_count=7
    )


@pytest.fixture()
def collection(reasoning_feature, confidence_feature, technical_feature) -> FeatureCollection:
    return FeatureCollection.from_iterable([reasoning_feature, confidence_feature, technical_feature])


# ===========================================================================
# FeatureBatch
# ===========================================================================


class TestFeatureBatch:
    def test_size_and_is_empty(self, reasoning_feature):
        batch = FeatureBatch(key="reasoning", items=(reasoning_feature,))
        assert batch.size == 1
        assert not batch.is_empty

    def test_empty_batch(self):
        batch = FeatureBatch(key="empty")
        assert batch.is_empty
        assert batch.size == 0

    def test_feature_type_ids(self, reasoning_feature, confidence_feature):
        batch = FeatureBatch(key="mixed", items=(reasoning_feature, confidence_feature))
        ids = batch.feature_type_ids()
        assert "reasoning_feature" in ids
        assert "confidence_feature" in ids

    def test_frozen(self, reasoning_feature):
        batch = FeatureBatch(key="test", items=(reasoning_feature,))
        with pytest.raises(Exception):
            batch.key = "changed"  # type: ignore[misc]


# ===========================================================================
# FeatureCollection
# ===========================================================================


class TestFeatureCollection:
    def test_from_iterable(self, reasoning_feature, confidence_feature):
        col = FeatureCollection.from_iterable([reasoning_feature, confidence_feature])
        assert col.size == 2

    def test_empty_collection(self):
        col = FeatureCollection()
        assert col.is_empty
        assert col.size == 0

    def test_get_by_type(self, collection, reasoning_feature):
        result = collection.get_by_type(FeatureType.REASONING)
        assert result is not None
        assert result.feature_identity.feature_type_id == "reasoning_feature"

    def test_get_by_type_missing(self, collection):
        result = collection.get_by_type(FeatureType.LEADERSHIP)
        assert result is None

    def test_filter_by_type(self, collection):
        filtered = collection.filter_by_type(FeatureType.REASONING)
        assert filtered.size == 1
        assert filtered.features[0].feature_identity.feature_type_id == "reasoning_feature"

    def test_filter_by_min_confidence(self, collection):
        filtered = collection.filter_by_min_confidence(0.8)
        assert all(f.quality.confidence.value >= 0.8 for f in filtered.features)

    def test_filter_by_maturity(self, collection):
        filtered = collection.filter_by_maturity(MATURITY_MATURE)
        assert all(f.quality.maturity.stage == MATURITY_MATURE for f in filtered.features)

    def test_filter_by_stability(self, collection):
        filtered = collection.filter_by_stability(STABILITY_STABLE)
        assert all(f.quality.stability.state == STABILITY_STABLE for f in filtered.features)

    def test_sorted_by_confidence_desc(self, collection):
        ordered = collection.sorted_by_confidence(descending=True)
        confidences = [f.quality.confidence.value for f in ordered.features]
        assert confidences == sorted(confidences, reverse=True)

    def test_group_by_type_id(self, collection):
        groups = collection.group_by_type_id()
        assert "reasoning_feature" in groups
        assert "confidence_feature" in groups
        assert "technical_skill_feature" in groups

    def test_group_by_maturity(self, collection):
        groups = collection.group_by_maturity()
        assert all(isinstance(v, FeatureBatch) for v in groups.values())


# ===========================================================================
# FeatureStatistics
# ===========================================================================


class TestFeatureStatistics:
    def test_from_empty_collection(self):
        stats = FeatureStatistics.from_collection(FeatureCollection())
        assert stats.total_count == 0
        assert stats.mean_confidence == 0.0

    def test_total_count(self, collection):
        stats = FeatureStatistics.from_collection(collection)
        assert stats.total_count == 3

    def test_mean_confidence(self, collection):
        stats = FeatureStatistics.from_collection(collection)
        expected = (0.8 + 0.5 + 0.9) / 3
        assert abs(stats.mean_confidence - expected) < 1e-9

    def test_min_max_confidence(self, collection):
        stats = FeatureStatistics.from_collection(collection)
        assert stats.min_confidence == pytest.approx(0.5)
        assert stats.max_confidence == pytest.approx(0.9)

    def test_maturity_distribution(self, collection):
        stats = FeatureStatistics.from_collection(collection)
        dist = stats.maturity_distribution
        assert sum(dist.values()) == 3

    def test_stability_distribution(self, collection):
        stats = FeatureStatistics.from_collection(collection)
        dist = stats.stability_distribution
        assert sum(dist.values()) == 3

    def test_low_confidence_count(self):
        f_low = _make_feature(FeatureType.COMMUNICATION, confidence=0.2)
        f_high = _make_feature(FeatureType.REASONING, confidence=0.9)
        col = FeatureCollection.from_iterable([f_low, f_high])
        stats = FeatureStatistics.from_collection(col)
        assert stats.low_confidence_count == 1


# ===========================================================================
# FeatureDelta / FeatureDeltaSet
# ===========================================================================


class TestFeatureDelta:
    def test_added(self, reasoning_feature):
        delta = FeatureDelta.between(None, reasoning_feature, question_index=5)
        assert delta.direction == DeltaDirection.ADDED
        assert delta.before_value is None
        assert delta.after_value == "HIGH"

    def test_removed(self, reasoning_feature):
        delta = FeatureDelta.between(reasoning_feature, None, question_index=5)
        assert delta.direction == DeltaDirection.REMOVED
        assert delta.after_value is None

    def test_improved(self):
        before = _make_feature(FeatureType.REASONING, confidence=0.5)
        after = _make_feature(FeatureType.REASONING, confidence=0.8)
        delta = FeatureDelta.between(before, after, question_index=4)
        assert delta.direction == DeltaDirection.IMPROVED
        assert delta.confidence_delta == pytest.approx(0.3)

    def test_degraded(self):
        before = _make_feature(FeatureType.REASONING, confidence=0.9)
        after = _make_feature(FeatureType.REASONING, confidence=0.5)
        delta = FeatureDelta.between(before, after, question_index=4)
        assert delta.direction == DeltaDirection.DEGRADED

    def test_unchanged(self):
        f = _make_feature(FeatureType.REASONING, confidence=0.7, value="HIGH")
        delta = FeatureDelta.between(f, f, question_index=4)
        assert delta.direction == DeltaDirection.UNCHANGED
        assert not delta.value_changed

    def test_both_none_raises(self):
        with pytest.raises(ValueError):
            FeatureDelta.between(None, None, question_index=0)


class TestFeatureDeltaSet:
    def test_compute_added_and_kept(self, reasoning_feature, confidence_feature):
        before = FeatureCollection.from_iterable([reasoning_feature])
        after = FeatureCollection.from_iterable([reasoning_feature, confidence_feature])
        ds = FeatureDeltaSet.compute(before, after, question_index=5)
        assert len(ds.deltas) == 2
        added = ds.by_direction(DeltaDirection.ADDED)
        assert len(added) == 1
        assert added[0].after_value == "MODERATE"

    def test_changed_excludes_unchanged(self, reasoning_feature):
        before = FeatureCollection.from_iterable([reasoning_feature])
        after = FeatureCollection.from_iterable([reasoning_feature])
        ds = FeatureDeltaSet.compute(before, after, question_index=3)
        assert len(ds.changed) == 0


# ===========================================================================
# FeatureFilter
# ===========================================================================


class TestFeatureFilter:
    def test_by_type(self, reasoning_feature, confidence_feature):
        pred = FeatureFilter.by_type(FeatureType.REASONING)
        assert pred(reasoning_feature)
        assert not pred(confidence_feature)

    def test_min_confidence(self, reasoning_feature, confidence_feature):
        pred = FeatureFilter.min_confidence(0.7)
        assert pred(reasoning_feature)
        assert not pred(confidence_feature)

    def test_is_low_confidence(self):
        low = _make_feature(FeatureType.COMMUNICATION, confidence=0.2)
        high = _make_feature(FeatureType.REASONING, confidence=0.8)
        pred = FeatureFilter.is_low_confidence()
        assert pred(low)
        assert not pred(high)

    def test_all_of(self, reasoning_feature):
        pred = FeatureFilter.all_of(
            FeatureFilter.by_type(FeatureType.REASONING),
            FeatureFilter.min_confidence(0.5),
        )
        assert pred(reasoning_feature)

    def test_any_of(self, reasoning_feature, confidence_feature):
        pred = FeatureFilter.any_of(
            FeatureFilter.by_type(FeatureType.REASONING),
            FeatureFilter.by_type(FeatureType.CONFIDENCE),
        )
        assert pred(reasoning_feature)
        assert pred(confidence_feature)

    def test_not_of(self, reasoning_feature):
        pred = FeatureFilter.not_of(FeatureFilter.by_type(FeatureType.REASONING))
        assert not pred(reasoning_feature)

    def test_by_value(self, reasoning_feature):
        pred = FeatureFilter.by_value("HIGH")
        assert pred(reasoning_feature)

    def test_compose_with_collection_filter(self, collection):
        pred = FeatureFilter.all_of(
            FeatureFilter.min_confidence(0.7),
            FeatureFilter.by_stability(STABILITY_STABLE),
        )
        result = collection.filter(pred)
        assert all(f.quality.confidence.value >= 0.7 for f in result.features)
        assert all(f.quality.stability.state == STABILITY_STABLE for f in result.features)


# ===========================================================================
# FeatureOrdering
# ===========================================================================


class TestFeatureOrdering:
    def test_confidence_asc(self, collection):
        ordered = collection.sorted_by(FeatureOrdering.by_confidence_asc())
        vals = [f.quality.confidence.value for f in ordered.features]
        assert vals == sorted(vals)

    def test_confidence_desc(self, collection):
        ordered = collection.sorted_by(FeatureOrdering.by_confidence_desc())
        vals = [f.quality.confidence.value for f in ordered.features]
        assert vals == sorted(vals, reverse=True)

    def test_maturity_asc(self, collection):
        ordered = collection.sorted_by(FeatureOrdering.by_maturity_asc())
        stages = [f.quality.maturity.stage for f in ordered.features]
        rank = {MATURITY_NASCENT: 0, MATURITY_DEVELOPING: 1, MATURITY_MATURE: 2}
        assert [rank[s] for s in stages] == sorted(rank[s] for s in stages)

    def test_composite_key(self, collection):
        key = FeatureOrdering.composite(
            FeatureOrdering.by_maturity_desc(),
            FeatureOrdering.by_confidence_desc(),
        )
        ordered = collection.sorted_by(key)
        assert ordered.size == collection.size


# ===========================================================================
# FeatureComparison / FeatureCollectionComparison
# ===========================================================================


class TestFeatureComparison:
    def test_compare_same_feature(self, reasoning_feature):
        result = FeatureComparison.compare(reasoning_feature, reasoning_feature, question_index=3)
        assert result.values_equal
        assert result.confidence_delta == pytest.approx(0.0)

    def test_compare_improved(self):
        before = _make_feature(FeatureType.REASONING, confidence=0.5, value="LOW")
        after = _make_feature(FeatureType.REASONING, confidence=0.9, value="HIGH")
        result = FeatureComparison.compare(before, after, question_index=4)
        assert result.delta.direction == DeltaDirection.IMPROVED
        assert result.right_has_higher_confidence

    def test_compare_different_identity_raises(self, reasoning_feature, confidence_feature):
        with pytest.raises(ValueError, match="Cannot compare"):
            FeatureComparison.compare(reasoning_feature, confidence_feature, question_index=3)


class TestFeatureCollectionComparison:
    def test_shared_and_only(self, reasoning_feature, confidence_feature, technical_feature):
        left = FeatureCollection.from_iterable([reasoning_feature, confidence_feature])
        right = FeatureCollection.from_iterable([reasoning_feature, technical_feature])
        result = FeatureCollectionComparison.compare(left, right, question_index=5)
        assert "reasoning_feature" in result.shared_type_ids
        assert "confidence_feature" in result.left_only_type_ids
        assert "technical_skill_feature" in result.right_only_type_ids

    def test_improved_and_degraded(self):
        before_r = _make_feature(FeatureType.REASONING, confidence=0.5)
        after_r = _make_feature(FeatureType.REASONING, confidence=0.9)
        before_c = _make_feature(FeatureType.CONFIDENCE, confidence=0.9)
        after_c = _make_feature(FeatureType.CONFIDENCE, confidence=0.4)
        left = FeatureCollection.from_iterable([before_r, before_c])
        right = FeatureCollection.from_iterable([after_r, after_c])
        result = FeatureCollectionComparison.compare(left, right, question_index=6)
        assert len(result.improved) == 1
        assert len(result.degraded) == 1


# ===========================================================================
# FeatureSnapshotBuilder
# ===========================================================================


class TestFeatureSnapshotBuilder:
    def test_build_from_tuple(self, reasoning_feature, confidence_feature):
        snapshot = FeatureSnapshotBuilder.build(
            features=(reasoning_feature, confidence_feature),
            session_id="session-1",
            question_index=3,
        )
        assert snapshot.session_id == "session-1"
        assert snapshot.question_index == 3
        assert snapshot.collection.size == 2
        assert snapshot.statistics.total_count == 2

    def test_empty_snapshot(self):
        snapshot = FeatureSnapshotBuilder.empty(session_id="s", question_index=0)
        assert snapshot.collection.is_empty
        assert snapshot.statistics.total_count == 0

    def test_repr(self, reasoning_feature):
        snapshot = FeatureSnapshotBuilder.build(
            features=(reasoning_feature,),
            session_id="s-1",
            question_index=2,
        )
        assert "s-1" in repr(snapshot)
        assert "q=2" in repr(snapshot)
