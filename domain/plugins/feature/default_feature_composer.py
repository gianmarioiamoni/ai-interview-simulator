# domain/plugins/feature/default_feature_composer.py
# DefaultFeatureComposer — production FeatureComposer for the V1.2 live session path.
# ADR-020 §C: resolves FeatureCandidates into ProfileFeatures.
#
# Strategy: first-wins per FeatureIdentity (stateless, deterministic).
# For a given feature_type_id, the first FeatureCandidate (in registration order)
# is accepted; subsequent candidates for the same type are discarded.
#
# This is sufficient for Phase D (MIG-03A) where each Updater produces at most
# one candidate per feature type.  A merge/replacement policy can be layered in
# a future ADR without changing the contract.

from __future__ import annotations

from domain.contracts.feature.feature_candidate import FeatureCandidate
from domain.contracts.feature.feature_composer import FeatureComposer
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.profile_feature import ProfileFeature


class DefaultFeatureComposer(FeatureComposer):
    """Production FeatureComposer — first-wins composition strategy.

    Invariants (ADR-020 §C):
    - Stateless per invocation.
    - Returns exactly one ProfileFeature per distinct FeatureIdentity.
    - Provenance is assembled from each accepted FeatureCandidate.
    - No LLM, no I/O, no shared mutable state.
    """

    def compose(
        self,
        candidates: list[FeatureCandidate],
        candidate_identity_id: str,
        feature_engine_version: str,
    ) -> list[ProfileFeature]:
        seen: dict[str, ProfileFeature] = {}
        for candidate in candidates:
            tid = candidate.feature_identity.feature_type_id
            if tid in seen:
                continue
            provenance = FeatureProvenance(
                feature_identity=candidate.feature_identity,
                source_observation_ids=candidate.source_observation_ids,
                computed_at_question_index=candidate.computed_at_question_index,
                feature_engine_version=feature_engine_version,
                updater_id=candidate.updater_id,
            )
            quality = FeatureQuality(
                confidence=FeatureConfidence(value=candidate.candidate_confidence),
                stability=FeatureStability(state="emerging"),
                maturity=FeatureMaturity.from_observation_count(
                    max(1, len(candidate.source_observation_ids))
                ),
            )
            seen[tid] = ProfileFeature(
                feature_identity=candidate.feature_identity,
                value=candidate.candidate_value,
                quality=quality,
                provenance=provenance,
                computed_at_question_index=candidate.computed_at_question_index,
                candidate_identity_id=candidate_identity_id,
            )
        return list(seen.values())
