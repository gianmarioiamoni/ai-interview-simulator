# domain/contracts/replay/replay_feature_engine.py
# EPIC-03 Phase 3a — ReplayFeatureEngine: read-only replay-layer feature adapter.
# Specification per EPIC-03-DOMAIN-CONTRACTS.md §8 and ADR-037 Decision 2.

from __future__ import annotations

from typing import Optional

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import CandidateProfileSnapshot


class ReplayFeatureEngine:
    """Read-only adapter exposing stored ProfileFeature values from CandidateProfileSnapshot.

    ADR-037 Decision 2: ReplayFeatureEngine is a strict read-pass component.
    It performs no derivation, recomputation, or LLM augmentation.

    Permitted operations: read stored features from CandidateProfileSnapshot.
    Prohibited operations: compute, update, accumulate, or LLM-augment features
        — any such call raises RuntimeError (P-06).

    Lifecycle: instantiated by replay_node with a CandidateProfileSnapshot;
    discarded after ReplaySessionBuilder.build() completes. Stateless across
    replay operations.
    """

    def __init__(self, profile_snapshot: CandidateProfileSnapshot) -> None:
        self._snapshot = profile_snapshot

    # ------------------------------------------------------------------
    # Permitted read operations (ADR-037 D2 — read-pass only)
    # ------------------------------------------------------------------

    def get_features(self) -> tuple[ProfileFeature, ...]:
        """Return all stored ProfileFeature values from CandidateProfileSnapshot."""
        return self._snapshot.features

    def get_feature(self, identity: FeatureIdentity) -> Optional[ProfileFeature]:
        """Return stored feature by FeatureIdentity; None if not present."""
        for feature in self._snapshot.features:
            if feature.feature_identity == identity:
                return feature
        return None

    # ------------------------------------------------------------------
    # Prohibited operations — raise RuntimeError (P-06)
    # ------------------------------------------------------------------

    def compute_feature(self, *args, **kwargs) -> None:  # type: ignore[override]
        raise RuntimeError(
            "ReplayFeatureEngine.compute_feature() is prohibited. "
            "ReplayFeatureEngine is a read-pass component — no computation allowed (ADR-037 D2)."
        )

    def update_feature(self, *args, **kwargs) -> None:  # type: ignore[override]
        raise RuntimeError(
            "ReplayFeatureEngine.update_feature() is prohibited. "
            "ReplayFeatureEngine is a read-pass component — no mutation allowed (ADR-037 D2)."
        )

    def accumulate(self, *args, **kwargs) -> None:  # type: ignore[override]
        raise RuntimeError(
            "ReplayFeatureEngine.accumulate() is prohibited. "
            "ReplayFeatureEngine is a read-pass component — no accumulation allowed (ADR-037 D2)."
        )
