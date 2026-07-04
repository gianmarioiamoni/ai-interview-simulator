# domain/profile/candidate_profile_derivation_service.py
# INTERNAL — do NOT export from domain/profile/__init__.py
# CandidateProfileDerivationService — deterministic derivation engine (ADS-04, ADS-05, MIG-06 S-02)

from __future__ import annotations

from collections import defaultdict

from domain.contracts.feature.feature_quality import MATURITY_NASCENT
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile._derived_profile_data import DerivedProfileData
from domain.profile._derivation_rules import CandidateProfileDerivationRules


class CandidateProfileDerivationService:
    """Stateless deterministic engine: ProfileFeature[] → DerivedProfileData.

    ALL domain semantics (mappings, weights, thresholds, proxy values) come
    exclusively from CandidateProfileDerivationRules. No constant may be
    duplicated here (ADS-05 invariant).

    Sole entry point: derive(features, rules).
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def derive(
        self,
        features: tuple[ProfileFeature, ...] | list[ProfileFeature],
        rules: CandidateProfileDerivationRules | None = None,
    ) -> DerivedProfileData:
        """Transform a ProfileFeature collection into DerivedProfileData.

        Args:
            features: All ProfileFeatures available for this candidate.
            rules:    Domain rules to apply. Defaults to V1.2 canonical rules.

        Returns:
            Immutable DerivedProfileData capturing the full derivation output.
        """
        _rules = rules if rules is not None else CandidateProfileDerivationRules.default()
        feature_tuple = tuple(features)

        if not feature_tuple:
            return self._empty_result(feature_tuple)

        proxy_map = self._build_proxy_map(_rules)
        feature_type_map = self._build_feature_type_map(_rules)
        low_confidence_active = self._has_low_confidence_signal(feature_tuple, _rules)
        max_evidence = (
            _rules.low_confidence_max_evidence_modifier
            if low_confidence_active
            else _rules.max_evidence_confidence
        )

        dimension_scores = self._derive_dimension_scores(
            feature_tuple, _rules, proxy_map, feature_type_map, max_evidence
        )
        trend_features = self._collect_trend_features(feature_tuple, _rules)
        dimension_scores = self._apply_trend_overrides(
            dimension_scores, trend_features, _rules
        )

        questions_answered = len({f.computed_at_question_index for f in feature_tuple})
        areas_covered = self._derive_areas_covered(feature_tuple, _rules)
        coverage_ratio = self._derive_coverage_ratio(dimension_scores)
        dominant = self._derive_dominant(dimension_scores)
        weakest = self._derive_weakest(dimension_scores, dominant)
        last_updated = max(f.computed_at_question_index for f in feature_tuple)

        return DerivedProfileData(
            dimension_scores=dimension_scores,
            questions_answered=questions_answered,
            areas_covered=areas_covered,
            coverage_ratio=coverage_ratio,
            dominant_dimension=dominant,
            weakest_dimension=weakest,
            source_features=feature_tuple,
            last_updated_at_question_index=last_updated,
        )

    # ------------------------------------------------------------------
    # Step 1 — proxy map and feature type index
    # ------------------------------------------------------------------

    def _build_proxy_map(
        self, rules: CandidateProfileDerivationRules
    ) -> dict[str, float]:
        """Build value_string → numeric_score lookup from rules."""
        proxy: dict[str, float] = {}
        for entry in rules.value_proxy_table:
            proxy[entry.value_string] = entry.numeric_score
        return proxy

    def _build_feature_type_map(
        self, rules: CandidateProfileDerivationRules
    ) -> dict[FeatureType, list[tuple[ProfileDimension, float]]]:
        """Build FeatureType → [(dimension, weight)] from rules."""
        mapping: dict[FeatureType, list[tuple[ProfileDimension, float]]] = defaultdict(list)
        for entry in rules.feature_dimension_map:
            mapping[entry.feature_type].append((entry.dimension, entry.weight))
        return dict(mapping)

    # ------------------------------------------------------------------
    # Step 2 — dimension score aggregation
    # ------------------------------------------------------------------

    def _resolve_feature_type(self, feature: ProfileFeature) -> FeatureType | None:
        """Resolve FeatureType from feature_identity.feature_type_id. Returns None if unknown."""
        try:
            return FeatureType(feature.feature_identity.feature_type_id)
        except ValueError:
            return None

    def _resolve_proxy_score(self, value: str, proxy_map: dict[str, float]) -> float:
        return proxy_map.get(value, proxy_map["*"])

    def _derive_dimension_scores(
        self,
        features: tuple[ProfileFeature, ...],
        rules: CandidateProfileDerivationRules,
        proxy_map: dict[str, float],
        feature_type_map: dict[FeatureType, list[tuple[ProfileDimension, float]]],
        max_evidence: int,
    ) -> dict[ProfileDimension, DimensionTrace]:
        # Accumulators per dimension
        weighted_score_sum: dict[ProfileDimension, float] = defaultdict(float)
        weight_sum: dict[ProfileDimension, float] = defaultdict(float)
        evidence_count: dict[ProfileDimension, int] = defaultdict(int)
        # Track last score by (dimension, question_index) for trend
        last_by_dim: dict[ProfileDimension, tuple[int, float]] = {}

        for feature in features:
            ft = self._resolve_feature_type(feature)
            if ft is None or ft not in feature_type_map:
                continue
            conf = feature.quality.confidence.value
            if conf <= 0.0:
                continue
            numeric = self._resolve_proxy_score(feature.value, proxy_map)
            q_idx = feature.computed_at_question_index

            for dimension, weight in feature_type_map[ft]:
                contribution = conf * weight * numeric
                w_contribution = conf * weight
                weighted_score_sum[dimension] += contribution
                weight_sum[dimension] += w_contribution
                evidence_count[dimension] += 1

                # Track the most recent score for this dimension
                current = last_by_dim.get(dimension)
                if current is None or q_idx >= current[0]:
                    last_by_dim[dimension] = (q_idx, conf * numeric / conf if conf else numeric)
                    # simplified: just the weighted score for last_score tracking
                    last_by_dim[dimension] = (q_idx, numeric)

        result: dict[ProfileDimension, DimensionTrace] = {}
        for dim in weighted_score_sum:
            wsum = weight_sum[dim]
            if wsum <= 0.0:
                continue
            avg = round(weighted_score_sum[dim] / wsum, 2)
            ev = evidence_count[dim]
            confidence_d = min(ev / max_evidence, 1.0)
            last_q_idx, last_score_val = last_by_dim[dim]
            trend = self._compute_trend(avg, last_score_val, ev, rules)

            result[dim] = DimensionTrace(
                average_score=avg,
                last_score=last_score_val,
                trend=trend,
                confidence=round(confidence_d, 4),
                evidence_count=ev,
                last_updated_question=last_q_idx,
            )

        return result

    # ------------------------------------------------------------------
    # Step 3 — trend computation
    # ------------------------------------------------------------------

    def _compute_trend(
        self,
        average_score: float,
        last_score: float,
        evidence_count: int,
        rules: CandidateProfileDerivationRules,
    ) -> Trend:
        if evidence_count < rules.min_evidence_for_trend or last_score is None:
            return Trend.INSUFFICIENT_DATA
        delta = last_score - average_score
        if delta > rules.trend_threshold:
            return Trend.IMPROVING
        if delta < -rules.trend_threshold:
            return Trend.DECLINING
        return Trend.STABLE

    # ------------------------------------------------------------------
    # Step 4 — TREND feature overrides
    # ------------------------------------------------------------------

    def _collect_trend_features(
        self,
        features: tuple[ProfileFeature, ...],
        rules: CandidateProfileDerivationRules,
    ) -> list[ProfileFeature]:
        eligible = rules.trend_override_eligible_features
        result = []
        for f in features:
            ft = self._resolve_feature_type(f)
            if ft is not None and ft in eligible:
                result.append(f)
        return result

    def _apply_trend_overrides(
        self,
        dimension_scores: dict[ProfileDimension, DimensionTrace],
        trend_features: list[ProfileFeature],
        rules: CandidateProfileDerivationRules,
    ) -> dict[ProfileDimension, DimensionTrace]:
        if not trend_features or not dimension_scores:
            return dimension_scores

        _TREND_VALUE_MAP: dict[str, Trend] = {
            "IMPROVING": Trend.IMPROVING,
            "DECLINING": Trend.DECLINING,
            "STABLE": Trend.STABLE,
        }

        updated = dict(dimension_scores)
        for tf in trend_features:
            override_trend = _TREND_VALUE_MAP.get(tf.value)
            if override_trend is None:
                continue
            for dim, trace in updated.items():
                if trace.evidence_count < rules.min_evidence_for_trend:
                    continue
                if trace.last_score is None or trace.average_score is None:
                    continue
                delta = abs(trace.last_score - trace.average_score)
                if delta > rules.trend_override_max_delta:
                    continue
                if trace.trend in (Trend.STABLE, Trend.INSUFFICIENT_DATA):
                    updated[dim] = DimensionTrace(
                        average_score=trace.average_score,
                        last_score=trace.last_score,
                        trend=override_trend,
                        confidence=trace.confidence,
                        evidence_count=trace.evidence_count,
                        last_updated_question=trace.last_updated_question,
                    )
        return updated

    # ------------------------------------------------------------------
    # Step 5 — aggregate fields
    # ------------------------------------------------------------------

    def _has_low_confidence_signal(
        self,
        features: tuple[ProfileFeature, ...],
        rules: CandidateProfileDerivationRules,
    ) -> bool:
        """True if any CONFIDENCE-type feature has low confidence quality."""
        for f in features:
            ft = self._resolve_feature_type(f)
            if ft == FeatureType.CONFIDENCE:
                if f.quality.confidence.value < rules.low_confidence_threshold:
                    return True
        return False

    def _derive_areas_covered(
        self,
        features: tuple[ProfileFeature, ...],
        rules: CandidateProfileDerivationRules,
    ) -> list[str]:
        seen: set[str] = set()
        for f in features:
            is_nascent = f.quality.maturity.stage == MATURITY_NASCENT
            conf = f.quality.confidence.value
            if is_nascent and not rules.areas_covered_allow_nascent:
                if conf < rules.areas_covered_min_confidence:
                    continue
            seen.add(f.feature_identity.semantic_category)
        return sorted(seen)

    def _derive_coverage_ratio(
        self, dimension_scores: dict[ProfileDimension, DimensionTrace]
    ) -> float:
        scored = sum(1 for t in dimension_scores.values() if t.evidence_count >= 1)
        total = len(ProfileDimension)
        return round(scored / total, 4) if total > 0 else 0.0

    def _derive_dominant(
        self, dimension_scores: dict[ProfileDimension, DimensionTrace]
    ) -> ProfileDimension | None:
        if not dimension_scores:
            return None
        return max(
            dimension_scores,
            key=lambda d: (
                dimension_scores[d].evidence_count,
                -dimension_scores[d].average_score,
            ),
        )

    def _derive_weakest(
        self,
        dimension_scores: dict[ProfileDimension, DimensionTrace],
        dominant: ProfileDimension | None = None,
    ) -> ProfileDimension | None:
        if not dimension_scores:
            return None
        candidates = sorted(
            dimension_scores,
            key=lambda d: (
                dimension_scores[d].average_score,
                -dimension_scores[d].evidence_count,
            ),
        )
        if len(candidates) == 1:
            return candidates[0]
        # When more than one dimension exists, weakest must differ from dominant.
        for candidate in candidates:
            if candidate != dominant:
                return candidate
        return candidates[0]

    # ------------------------------------------------------------------
    # Empty input fast-path
    # ------------------------------------------------------------------

    def _empty_result(
        self, features: tuple[ProfileFeature, ...]
    ) -> DerivedProfileData:
        return DerivedProfileData(
            dimension_scores={},
            questions_answered=0,
            areas_covered=[],
            coverage_ratio=0.0,
            dominant_dimension=None,
            weakest_dimension=None,
            source_features=features,
            last_updated_at_question_index=-1,
        )
