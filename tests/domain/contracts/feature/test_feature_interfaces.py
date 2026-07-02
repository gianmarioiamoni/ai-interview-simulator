# tests/domain/contracts/feature/test_feature_interfaces.py
# Tests for FeatureComposer, FeatureUpdater, FeatureMergePolicy, FeatureReplacementPolicy interfaces

import pytest
from abc import ABC

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_composer import FeatureComposer
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_merge_policy import FeatureMergePolicy
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_replacement_policy import FeatureReplacementPolicy
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.feature_updater import FeatureUpdater
from domain.contracts.feature.profile_feature import ProfileFeature


# ---------------------------------------------------------------------------
# Minimal concrete implementations for contract testing
# ---------------------------------------------------------------------------


class ConcreteComposer(FeatureComposer):
    def compose(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> list[ProfileFeature]:
        result = []
        for c in candidates:
            prov = FeatureProvenance(
                feature_identity=c.feature_identity,
                source_observation_ids=c.source_observation_ids,
                computed_at_question_index=c.computed_at_question_index,
                feature_engine_version=feature_engine_version,
                updater_id=c.updater_id,
                language_context=c.language_context,
            )
            quality = FeatureQuality(
                confidence=FeatureConfidence(value=c.candidate_confidence),
                stability=FeatureStability(state="emerging"),
                maturity=FeatureMaturity.from_observation_count(len(c.source_observation_ids)),
            )
            pf = ProfileFeature(
                feature_identity=c.feature_identity,
                value=c.candidate_value,
                quality=quality,
                provenance=prov,
                computed_at_question_index=c.computed_at_question_index,
                candidate_identity_id=candidate_identity_id,
            )
            result.append(pf)
        return result


class ConcreteUpdater(FeatureUpdater):
    @property
    def updater_id(self) -> str:
        return "test_updater"

    @property
    def observation_type_set(self) -> frozenset[str]:
        return frozenset({"REASONING_DEEP", "REASONING_SHALLOW"})

    @property
    def feature_identity_set(self) -> frozenset[str]:
        return frozenset({"reasoning_feature"})

    @property
    def invocation_order(self) -> int:
        return 1

    def produce(self, observations: list) -> list[FeatureCandidate]:
        return [
            FeatureCandidate(
                feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
                candidate_value="HIGH",
                candidate_confidence=0.85,
                source_observation_ids=("obs-1",),
                computed_at_question_index=2,
                updater_id=self.updater_id,
            )
        ]


class ConcreteMergePolicy(FeatureMergePolicy):
    def merge(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> ProfileFeature:
        c = candidates[0]
        all_obs = tuple(oid for candidate in candidates for oid in candidate.source_observation_ids)
        avg_conf = sum(ca.candidate_confidence for ca in candidates) / len(candidates)
        prov = FeatureProvenance(
            feature_identity=c.feature_identity,
            source_observation_ids=all_obs,
            computed_at_question_index=c.computed_at_question_index,
            feature_engine_version=feature_engine_version,
            updater_id=c.updater_id,
        )
        quality = FeatureQuality(
            confidence=FeatureConfidence(value=avg_conf),
            stability=FeatureStability(state="stable"),
            maturity=FeatureMaturity.from_observation_count(len(all_obs)),
        )
        return ProfileFeature(
            feature_identity=c.feature_identity,
            value=c.candidate_value,
            quality=quality,
            provenance=prov,
            computed_at_question_index=c.computed_at_question_index,
            candidate_identity_id=candidate_identity_id,
        )

    def are_compatible(self, a: FeatureCandidate, b: FeatureCandidate) -> bool:
        return a.candidate_value == b.candidate_value


class ConcreteReplacementPolicy(FeatureReplacementPolicy):
    def replace(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> ProfileFeature:
        winner = candidates[0]
        for c in candidates[1:]:
            winner = self.select_winner(winner, c)
        discarded_ids = tuple(
            oid
            for c in candidates
            if c is not winner
            for oid in c.source_observation_ids
        )
        prov = FeatureProvenance(
            feature_identity=winner.feature_identity,
            source_observation_ids=winner.source_observation_ids,
            computed_at_question_index=winner.computed_at_question_index,
            feature_engine_version=feature_engine_version,
            updater_id=winner.updater_id,
            superseded_observation_ids=discarded_ids,
        )
        quality = FeatureQuality(
            confidence=FeatureConfidence(value=winner.candidate_confidence),
            stability=FeatureStability(state="emerging"),
            maturity=FeatureMaturity.from_observation_count(len(winner.source_observation_ids)),
        )
        return ProfileFeature(
            feature_identity=winner.feature_identity,
            value=winner.candidate_value,
            quality=quality,
            provenance=prov,
            computed_at_question_index=winner.computed_at_question_index,
            candidate_identity_id=candidate_identity_id,
        )

    def select_winner(self, a: FeatureCandidate, b: FeatureCandidate) -> FeatureCandidate:
        if len(a.source_observation_ids) > len(b.source_observation_ids):
            return a
        if len(b.source_observation_ids) > len(a.source_observation_ids):
            return b
        return a if a.computed_at_question_index >= b.computed_at_question_index else b


# ---------------------------------------------------------------------------
# Interface contract tests
# ---------------------------------------------------------------------------


class TestFeatureComposerInterface:
    def test_is_abstract(self) -> None:
        assert issubclass(FeatureComposer, ABC)

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            FeatureComposer()  # type: ignore[abstract]

    def test_compose_returns_profile_features(self) -> None:
        composer = ConcreteComposer()
        candidate = FeatureCandidate(
            feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
            candidate_value="HIGH",
            candidate_confidence=0.8,
            source_observation_ids=("obs-1",),
            computed_at_question_index=2,
            updater_id="test_updater",
        )
        results = composer.compose([candidate], "c-001", "1.0.0")
        assert len(results) == 1
        assert isinstance(results[0], ProfileFeature)

    def test_compose_empty_candidates_returns_empty(self) -> None:
        composer = ConcreteComposer()
        assert composer.compose([], "c-001", "1.0.0") == []

    def test_compose_result_is_immutable(self) -> None:
        composer = ConcreteComposer()
        candidate = FeatureCandidate(
            feature_identity=FeatureIdentity.for_type(FeatureType.TREND),
            candidate_value="IMPROVING",
            candidate_confidence=0.7,
            source_observation_ids=("obs-2",),
            computed_at_question_index=4,
            updater_id="test_updater",
        )
        pf = composer.compose([candidate], "c-001", "1.0.0")[0]
        with pytest.raises(Exception):
            pf.value = "DECLINING"  # type: ignore[misc]


class TestFeatureUpdaterInterface:
    def test_is_abstract(self) -> None:
        assert issubclass(FeatureUpdater, ABC)

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            FeatureUpdater()  # type: ignore[abstract]

    def test_updater_id_non_empty(self) -> None:
        updater = ConcreteUpdater()
        assert updater.updater_id != ""

    def test_observation_type_set_is_frozenset(self) -> None:
        updater = ConcreteUpdater()
        assert isinstance(updater.observation_type_set, frozenset)

    def test_feature_identity_set_is_frozenset(self) -> None:
        updater = ConcreteUpdater()
        assert isinstance(updater.feature_identity_set, frozenset)

    def test_invocation_order_is_int(self) -> None:
        updater = ConcreteUpdater()
        assert isinstance(updater.invocation_order, int)

    def test_produce_returns_candidates(self) -> None:
        updater = ConcreteUpdater()
        results = updater.produce([])
        assert all(isinstance(c, FeatureCandidate) for c in results)

    def test_produce_candidates_have_matching_updater_id(self) -> None:
        updater = ConcreteUpdater()
        candidates = updater.produce([])
        for c in candidates:
            assert c.updater_id == updater.updater_id

    def test_produce_does_not_mutate_input(self) -> None:
        updater = ConcreteUpdater()
        observations: list = [{"type": "REASONING_DEEP"}]
        original_len = len(observations)
        updater.produce(observations)
        assert len(observations) == original_len


class TestFeatureMergePolicyInterface:
    def test_is_abstract(self) -> None:
        assert issubclass(FeatureMergePolicy, ABC)

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            FeatureMergePolicy()  # type: ignore[abstract]

    def _make_candidate(self, value: str, conf: float, obs: tuple, qidx: int = 3) -> FeatureCandidate:
        return FeatureCandidate(
            feature_identity=FeatureIdentity.for_type(FeatureType.REASONING),
            candidate_value=value,
            candidate_confidence=conf,
            source_observation_ids=obs,
            computed_at_question_index=qidx,
            updater_id="test_updater",
        )

    def test_merge_returns_profile_feature(self) -> None:
        policy = ConcreteMergePolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1",))
        b = self._make_candidate("HIGH", 0.7, ("obs-2",))
        pf = policy.merge([a, b], "c-001", "1.0.0")
        assert isinstance(pf, ProfileFeature)

    def test_merge_unions_provenance(self) -> None:
        policy = ConcreteMergePolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1",))
        b = self._make_candidate("HIGH", 0.7, ("obs-2",))
        pf = policy.merge([a, b], "c-001", "1.0.0")
        assert "obs-1" in pf.provenance.source_observation_ids
        assert "obs-2" in pf.provenance.source_observation_ids

    def test_are_compatible_same_value(self) -> None:
        policy = ConcreteMergePolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1",))
        b = self._make_candidate("HIGH", 0.7, ("obs-2",))
        assert policy.are_compatible(a, b) is True

    def test_are_compatible_different_value(self) -> None:
        policy = ConcreteMergePolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1",))
        b = self._make_candidate("LOW", 0.7, ("obs-2",))
        assert policy.are_compatible(a, b) is False

    def test_merged_result_is_immutable(self) -> None:
        policy = ConcreteMergePolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1",))
        pf = policy.merge([a], "c-001", "1.0.0")
        with pytest.raises(Exception):
            pf.value = "LOW"  # type: ignore[misc]


class TestFeatureReplacementPolicyInterface:
    def test_is_abstract(self) -> None:
        assert issubclass(FeatureReplacementPolicy, ABC)

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            FeatureReplacementPolicy()  # type: ignore[abstract]

    def _make_candidate(self, value: str, conf: float, obs: tuple, qidx: int = 3) -> FeatureCandidate:
        return FeatureCandidate(
            feature_identity=FeatureIdentity.for_type(FeatureType.TECHNICAL_SKILL),
            candidate_value=value,
            candidate_confidence=conf,
            source_observation_ids=obs,
            computed_at_question_index=qidx,
            updater_id="test_updater",
        )

    def test_replace_returns_profile_feature(self) -> None:
        policy = ConcreteReplacementPolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1", "obs-2"))
        b = self._make_candidate("LOW", 0.8, ("obs-3",))
        pf = policy.replace([a, b], "c-001", "1.0.0")
        assert isinstance(pf, ProfileFeature)

    def test_winner_by_observation_count(self) -> None:
        policy = ConcreteReplacementPolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1", "obs-2"))
        b = self._make_candidate("LOW", 0.8, ("obs-3",))
        pf = policy.replace([a, b], "c-001", "1.0.0")
        assert pf.value == "HIGH"

    def test_discarded_ids_in_superseded(self) -> None:
        policy = ConcreteReplacementPolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1", "obs-2"))
        b = self._make_candidate("LOW", 0.8, ("obs-3",))
        pf = policy.replace([a, b], "c-001", "1.0.0")
        assert "obs-3" in pf.provenance.superseded_observation_ids

    def test_tie_break_by_question_index(self) -> None:
        policy = ConcreteReplacementPolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1",), qidx=5)
        b = self._make_candidate("LOW", 0.8, ("obs-2",), qidx=3)
        winner = policy.select_winner(a, b)
        assert winner is a

    def test_replacement_result_is_immutable(self) -> None:
        policy = ConcreteReplacementPolicy()
        a = self._make_candidate("HIGH", 0.8, ("obs-1",))
        pf = policy.replace([a], "c-001", "1.0.0")
        with pytest.raises(Exception):
            pf.value = "LOW"  # type: ignore[misc]
