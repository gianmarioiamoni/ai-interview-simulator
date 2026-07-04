# tests/domain/profile/test_candidate_profile_derivation_service.py
# Focused tests for CandidateProfileDerivationService (MIG-06 S-02)

import pytest

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile._derivation_rules import (
    CandidateProfileDerivationRules,
    FeatureDimensionMapping,
    ValueProxyEntry,
)
from domain.profile.candidate_profile_derivation_service import (
    CandidateProfileDerivationService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SVC = CandidateProfileDerivationService()
_DEFAULT_RULES = CandidateProfileDerivationRules.default()


def _feature(
    feature_type: FeatureType,
    value: str = "HIGH",
    computed_at: int = 0,
    confidence: float = 0.8,
    maturity_count: int = 3,
    candidate_id: str = "cand-001",
) -> ProfileFeature:
    identity = FeatureIdentity.for_type(feature_type)
    return ProfileFeature(
        feature_identity=identity,
        value=value,
        quality=FeatureQuality(
            confidence=FeatureConfidence(value=confidence),
            stability=FeatureStability(state="stable"),
            maturity=FeatureMaturity.from_observation_count(maturity_count),
        ),
        provenance=FeatureProvenance(
            feature_identity=identity,
            computed_at_question_index=computed_at,
            feature_engine_version="1.0",
            updater_id="test_updater",
        ),
        computed_at_question_index=computed_at,
        candidate_identity_id=candidate_id,
    )


# ---------------------------------------------------------------------------
# Empty feature set
# ---------------------------------------------------------------------------


class TestEmptyInput:
    def test_empty_returns_zero_questions_answered(self) -> None:
        result = _SVC.derive(())
        assert result.questions_answered == 0

    def test_empty_returns_empty_dimension_scores(self) -> None:
        result = _SVC.derive(())
        assert result.dimension_scores == {}

    def test_empty_returns_zero_coverage_ratio(self) -> None:
        result = _SVC.derive(())
        assert result.coverage_ratio == 0.0

    def test_empty_returns_no_dominant_or_weakest(self) -> None:
        result = _SVC.derive(())
        assert result.dominant_dimension is None
        assert result.weakest_dimension is None

    def test_empty_last_updated_is_minus_one(self) -> None:
        result = _SVC.derive(())
        assert result.last_updated_at_question_index == -1

    def test_empty_source_features_preserved(self) -> None:
        result = _SVC.derive(())
        assert result.source_features == ()


# ---------------------------------------------------------------------------
# Single feature
# ---------------------------------------------------------------------------


class TestSingleFeature:
    def test_technical_skill_maps_to_technical_depth(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0)
        result = _SVC.derive((f,))
        assert ProfileDimension.TECHNICAL_DEPTH in result.dimension_scores

    def test_single_feature_score_is_proxy_value(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0, confidence=1.0)
        result = _SVC.derive((f,))
        trace = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH]
        # conf=1.0, weight=1.0, proxy=85.0 → avg = 85.0
        assert trace.average_score == pytest.approx(85.0, abs=0.01)

    def test_single_feature_evidence_count_is_one(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, computed_at=0)
        result = _SVC.derive((f,))
        assert result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].evidence_count == 1

    def test_single_feature_trend_is_insufficient_data(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, computed_at=0)
        result = _SVC.derive((f,))
        assert result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].trend == Trend.INSUFFICIENT_DATA

    def test_single_feature_questions_answered_is_one(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, computed_at=3)
        result = _SVC.derive((f,))
        assert result.questions_answered == 1

    def test_single_feature_source_features_preserved(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, computed_at=0)
        result = _SVC.derive((f,))
        assert result.source_features == (f,)

    def test_single_feature_last_updated_correct(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, computed_at=7)
        result = _SVC.derive((f,))
        assert result.last_updated_at_question_index == 7


# ---------------------------------------------------------------------------
# Weighted / split feature mappings
# ---------------------------------------------------------------------------


class TestWeightedMappings:
    def test_reasoning_contributes_to_two_dimensions(self) -> None:
        f = _feature(FeatureType.REASONING, value="HIGH", computed_at=0, confidence=1.0)
        result = _SVC.derive((f,))
        assert ProfileDimension.PROBLEM_SOLVING in result.dimension_scores
        assert ProfileDimension.ENGINEERING_JUDGMENT in result.dimension_scores

    def test_reasoning_problem_solving_weight_0_7(self) -> None:
        f = _feature(FeatureType.REASONING, value="MODERATE", computed_at=0, confidence=1.0)
        result = _SVC.derive((f,))
        # proxy("MODERATE") = 55.0, weight=0.7 → contribution = 0.7*55 / 0.7 = 55.0
        ps_score = result.dimension_scores[ProfileDimension.PROBLEM_SOLVING].average_score
        assert ps_score == pytest.approx(55.0, abs=0.01)

    def test_reasoning_engineering_judgment_weight_0_3(self) -> None:
        f = _feature(FeatureType.REASONING, value="MODERATE", computed_at=0, confidence=1.0)
        result = _SVC.derive((f,))
        # weight=0.3, proxy=55.0 → avg = 55.0 (same proxy, different weight dimension)
        ej_score = result.dimension_scores[ProfileDimension.ENGINEERING_JUDGMENT].average_score
        assert ej_score == pytest.approx(55.0, abs=0.01)

    def test_learning_splits_to_problem_solving_and_technical_depth(self) -> None:
        f = _feature(FeatureType.LEARNING, value="HIGH", computed_at=0, confidence=1.0)
        result = _SVC.derive((f,))
        assert ProfileDimension.PROBLEM_SOLVING in result.dimension_scores
        assert ProfileDimension.TECHNICAL_DEPTH in result.dimension_scores

    def test_coverage_feature_not_in_dimension_scores(self) -> None:
        f = _feature(FeatureType.COVERAGE, value="HIGH", computed_at=0)
        result = _SVC.derive((f,))
        assert result.dimension_scores == {}

    def test_trend_feature_not_in_dimension_scores(self) -> None:
        f = _feature(FeatureType.TREND, value="IMPROVING", computed_at=0)
        result = _SVC.derive((f,))
        assert result.dimension_scores == {}

    def test_confidence_feature_not_in_dimension_scores(self) -> None:
        f = _feature(FeatureType.CONFIDENCE, value="HIGH", computed_at=0)
        result = _SVC.derive((f,))
        assert result.dimension_scores == {}


# ---------------------------------------------------------------------------
# Confidence adjustment
# ---------------------------------------------------------------------------


class TestConfidenceAdjustment:
    def test_confidence_weighted_mean(self) -> None:
        # Two TECHNICAL_SKILL features with different confidences
        f1 = _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0, confidence=0.8)
        f2 = _feature(FeatureType.TECHNICAL_SKILL, value="LOW", computed_at=1, confidence=0.2)
        result = _SVC.derive((f1, f2))
        trace = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH]
        # weight=1.0 for both
        # avg = (0.8*1.0*85 + 0.2*1.0*20) / (0.8*1.0 + 0.2*1.0) = (68+4)/1.0 = 72.0
        assert trace.average_score == pytest.approx(72.0, abs=0.01)

    def test_low_confidence_modifier_reduces_max_evidence(self) -> None:
        # CONFIDENCE feature with low quality confidence activates modifier
        # max_evidence drops from 10 to 8
        conf_feature = _feature(
            FeatureType.CONFIDENCE, value="LOW", computed_at=0, confidence=0.1
        )
        # 8 TECHNICAL_SKILL features → without modifier confidence = 8/10 = 0.8
        # with modifier confidence = 8/8 = 1.0
        features = tuple(
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=i)
            for i in range(8)
        ) + (conf_feature,)
        result = _SVC.derive(features)
        trace = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH]
        assert trace.confidence == pytest.approx(1.0)

    def test_zero_confidence_feature_excluded(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0, confidence=0.0)
        result = _SVC.derive((f,))
        assert ProfileDimension.TECHNICAL_DEPTH not in result.dimension_scores


# ---------------------------------------------------------------------------
# Trend derivation
# ---------------------------------------------------------------------------


class TestTrendDerivation:
    def test_improving_trend_when_last_much_higher(self) -> None:
        # Need >= 3 evidence; last score >> average
        # 2 LOW features at q=0,1 then 1 HIGH at q=2
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, value="LOW", computed_at=0, confidence=1.0),
            _feature(FeatureType.TECHNICAL_SKILL, value="LOW", computed_at=1, confidence=1.0),
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=2, confidence=1.0),
        )
        result = _SVC.derive(features)
        trend = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].trend
        assert trend == Trend.IMPROVING

    def test_declining_trend_when_last_much_lower(self) -> None:
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0, confidence=1.0),
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=1, confidence=1.0),
            _feature(FeatureType.TECHNICAL_SKILL, value="LOW", computed_at=2, confidence=1.0),
        )
        result = _SVC.derive(features)
        trend = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].trend
        assert trend == Trend.DECLINING

    def test_stable_trend_when_last_near_average(self) -> None:
        features = tuple(
            _feature(FeatureType.TECHNICAL_SKILL, value="MODERATE", computed_at=i, confidence=1.0)
            for i in range(4)
        )
        result = _SVC.derive(features)
        trend = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].trend
        assert trend == Trend.STABLE

    def test_insufficient_data_below_min_evidence(self) -> None:
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0),
            _feature(FeatureType.TECHNICAL_SKILL, value="LOW", computed_at=1),
        )
        result = _SVC.derive(features)
        trend = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].trend
        assert trend == Trend.INSUFFICIENT_DATA

    def test_trend_override_applied_when_conditions_met(self) -> None:
        # Provide enough evidence for STABLE trend, then a TREND feature says IMPROVING
        features = tuple(
            _feature(FeatureType.TECHNICAL_SKILL, value="MODERATE", computed_at=i, confidence=1.0)
            for i in range(4)
        ) + (
            _feature(FeatureType.TREND, value="IMPROVING", computed_at=3),
        )
        result = _SVC.derive(features)
        trend = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].trend
        assert trend == Trend.IMPROVING

    def test_trend_override_ignored_when_evidence_below_min(self) -> None:
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, value="MODERATE", computed_at=0, confidence=1.0),
            _feature(FeatureType.TREND, value="IMPROVING", computed_at=0),
        )
        result = _SVC.derive(features)
        trend = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].trend
        assert trend == Trend.INSUFFICIENT_DATA

    def test_trend_override_not_applied_to_strong_computed_trend(self) -> None:
        # Strong IMPROVING computed trend — override_max_delta = 8.0
        # last=85 (HIGH), avg ≈ 20 → delta=65 > 8 → override rejected
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, value="LOW", computed_at=0, confidence=1.0),
            _feature(FeatureType.TECHNICAL_SKILL, value="LOW", computed_at=1, confidence=1.0),
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=2, confidence=1.0),
            _feature(FeatureType.TREND, value="DECLINING", computed_at=2),
        )
        result = _SVC.derive(features)
        trend = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].trend
        assert trend == Trend.IMPROVING


# ---------------------------------------------------------------------------
# Dominant / weakest
# ---------------------------------------------------------------------------


class TestDominantWeakest:
    def test_single_dimension_dominant_and_weakest_are_same(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0)
        result = _SVC.derive((f,))
        assert result.dominant_dimension == ProfileDimension.TECHNICAL_DEPTH
        assert result.weakest_dimension == ProfileDimension.TECHNICAL_DEPTH

    def test_dominant_is_dimension_with_most_evidence(self) -> None:
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0),
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=1),
            _feature(FeatureType.COMMUNICATION, value="HIGH", computed_at=2),
        )
        result = _SVC.derive(features)
        assert result.dominant_dimension == ProfileDimension.TECHNICAL_DEPTH

    def test_weakest_is_dimension_with_lowest_score(self) -> None:
        # Give TECHNICAL_DEPTH more evidence so dominant is unambiguous,
        # then weakest should be COMMUNICATION with lower score.
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0, confidence=1.0),
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=1, confidence=1.0),
            _feature(FeatureType.COMMUNICATION, value="LOW", computed_at=2, confidence=1.0),
        )
        result = _SVC.derive(features)
        assert result.dominant_dimension == ProfileDimension.TECHNICAL_DEPTH
        assert result.weakest_dimension == ProfileDimension.COMMUNICATION

    def test_empty_has_no_dominant_or_weakest(self) -> None:
        result = _SVC.derive(())
        assert result.dominant_dimension is None
        assert result.weakest_dimension is None


# ---------------------------------------------------------------------------
# Coverage and areas_covered
# ---------------------------------------------------------------------------


class TestCoverageAndAreas:
    def test_coverage_ratio_one_of_five_dimensions(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, computed_at=0)
        result = _SVC.derive((f,))
        assert result.coverage_ratio == pytest.approx(round(1 / 5, 4))

    def test_coverage_ratio_all_five_dimensions(self) -> None:
        # Cover all 5 ProfileDimensions:
        # TECHNICAL_SKILL → TECHNICAL_DEPTH
        # COMMUNICATION   → COMMUNICATION
        # REASONING       → PROBLEM_SOLVING + ENGINEERING_JUDGMENT
        # LEADERSHIP      → ENGINEERING_JUDGMENT + PROBLEM_SOLVING
        # We still need SYSTEM_DESIGN — no direct mapping in default rules.
        # Use 4 covered dimensions (0.8) as realistic maximum with current rules.
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, computed_at=0, confidence=1.0),
            _feature(FeatureType.COMMUNICATION, computed_at=1, confidence=1.0),
            _feature(FeatureType.REASONING, computed_at=2, confidence=1.0),
        )
        result = _SVC.derive(features)
        # TECHNICAL_DEPTH, COMMUNICATION, PROBLEM_SOLVING, ENGINEERING_JUDGMENT = 4 of 5
        assert result.coverage_ratio == pytest.approx(round(4 / 5, 4))

    def test_areas_covered_sorted(self) -> None:
        features = (
            _feature(FeatureType.COMMUNICATION, computed_at=0, confidence=1.0, maturity_count=3),
            _feature(FeatureType.TECHNICAL_SKILL, computed_at=1, confidence=1.0, maturity_count=3),
        )
        result = _SVC.derive(features)
        assert result.areas_covered == sorted(result.areas_covered)

    def test_nascent_below_min_confidence_excluded_from_areas(self) -> None:
        # maturity_count=1 → nascent; confidence=0.1 < 0.3 → excluded
        f = _feature(FeatureType.TECHNICAL_SKILL, computed_at=0, confidence=0.1, maturity_count=1)
        result = _SVC.derive((f,))
        assert "technical_knowledge" not in result.areas_covered

    def test_nascent_above_min_confidence_included_in_areas(self) -> None:
        # maturity_count=1 → nascent; confidence=0.5 >= 0.3 → included
        f = _feature(FeatureType.TECHNICAL_SKILL, computed_at=0, confidence=0.5, maturity_count=1)
        result = _SVC.derive((f,))
        assert "technical_knowledge" in result.areas_covered

    def test_areas_covered_unique(self) -> None:
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, computed_at=0, confidence=1.0, maturity_count=3),
            _feature(FeatureType.TECHNICAL_SKILL, computed_at=1, confidence=1.0, maturity_count=3),
        )
        result = _SVC.derive(features)
        assert len(result.areas_covered) == len(set(result.areas_covered))


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_input_produces_equal_output(self) -> None:
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0),
            _feature(FeatureType.REASONING, value="MODERATE", computed_at=1),
        )
        r1 = _SVC.derive(features)
        r2 = _SVC.derive(features)
        assert r1 == r2

    def test_list_and_tuple_produce_same_result(self) -> None:
        features = [_feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0)]
        r1 = _SVC.derive(features)
        r2 = _SVC.derive(tuple(features))
        assert r1 == r2


# ---------------------------------------------------------------------------
# Rules injection
# ---------------------------------------------------------------------------


class TestRulesInjection:
    def test_custom_rules_override_proxy_values(self) -> None:
        custom_rules = CandidateProfileDerivationRules(
            rules_version="test",
            feature_dimension_map=(
                FeatureDimensionMapping(
                    feature_type=FeatureType.TECHNICAL_SKILL,
                    dimension=ProfileDimension.TECHNICAL_DEPTH,
                    weight=1.0,
                ),
            ),
            value_proxy_table=(
                ValueProxyEntry(value_string="HIGH", numeric_score=99.0),
                ValueProxyEntry(value_string="*", numeric_score=10.0),
            ),
            min_evidence_for_trend=2,
            trend_threshold=5.0,
            max_evidence_confidence=5,
            low_confidence_max_evidence_modifier=4,
            low_confidence_threshold=0.3,
            areas_covered_min_confidence=0.3,
            areas_covered_allow_nascent=False,
            trend_override_eligible_features=frozenset(),
            trend_override_max_delta=5.0,
        )
        f = _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0, confidence=1.0)
        result = _SVC.derive((f,), rules=custom_rules)
        score = result.dimension_scores[ProfileDimension.TECHNICAL_DEPTH].average_score
        assert score == pytest.approx(99.0, abs=0.01)

    def test_default_rules_applied_when_none_passed(self) -> None:
        f = _feature(FeatureType.TECHNICAL_SKILL, value="HIGH", computed_at=0, confidence=1.0)
        result_default = _SVC.derive((f,))
        result_explicit = _SVC.derive((f,), rules=_DEFAULT_RULES)
        assert result_default == result_explicit

    def test_questions_answered_counts_unique_indices(self) -> None:
        features = (
            _feature(FeatureType.TECHNICAL_SKILL, computed_at=0),
            _feature(FeatureType.TECHNICAL_SKILL, computed_at=0),
            _feature(FeatureType.COMMUNICATION, computed_at=1),
        )
        result = _SVC.derive(features)
        assert result.questions_answered == 2
