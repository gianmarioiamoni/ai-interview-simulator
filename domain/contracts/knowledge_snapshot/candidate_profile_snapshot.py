# domain/contracts/knowledge_snapshot/candidate_profile_snapshot.py
# ADR-032 — CandidateProfileSnapshot (certified historical knowledge state)

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from domain.contracts.feature.profile_feature import ProfileFeature


class CandidateProfileSnapshot(BaseModel):
    """Certified historical knowledge state at session close (ADR-032).

    Not a serialised CandidateProfile — a distinct, complete closure artifact.

    ADR-032 principles enforced:
    - Immutable (frozen=True) — EI-01
    - Complete — carries full ProfileFeature set at closure time
    - Versioned — profile_schema_version always present
    - Auditable — candidate_identity_id, closed_at_question_index present
    - Self-contained — no references back to live CandidateProfile

    OWNERSHIP (ADR-032 §D — Single-Writer Invariant):
    - Sole producer: FeatureEngine, during the final feature computation cycle
      at session close. No other component may construct a CandidateProfileSnapshot
      that enters a KnowledgeSnapshot.
    - Construction for tests uses direct Pydantic instantiation; this is
      permitted only in the test layer and must never be replicated in services.
    - A dedicated CandidateProfileSnapshotBuilder will be introduced as part of
      the session-close pipeline sprint (TCP — future roadmap, not Technical Debt).
    - Read-only consumers: KnowledgeSnapshotBuilder, ReplayOrchestrator, ReportBuilder,
      LearningProgressBuilder. None of these may modify the snapshot once created.
    """

    candidate_identity_id: str = Field(
        ..., min_length=1, description="Owning candidate (ADR-016A)"
    )
    features: tuple[ProfileFeature, ...] = Field(
        ..., description="Full ProfileFeature set at closure — immutable"
    )
    closed_at_question_index: int = Field(
        ..., ge=0, description="Session position at which snapshot was taken"
    )
    source_observation_ids: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Observation IDs that contributed to this snapshot (provenance)"
    )
    total_feature_count: int = Field(
        ..., ge=0, description="Computed count — must equal len(features)"
    )
    mean_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Mean confidence across all features at closure"
    )
    profile_schema_version: str = Field(
        default="1.0",
        description="Profile schema version for ADR-022 KnowledgeSnapshot compatibility"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Reserved metadata dict (ADR-032)"
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _total_feature_count_invariant(self) -> "CandidateProfileSnapshot":
        if self.total_feature_count != len(self.features):
            raise ValueError(
                f"total_feature_count={self.total_feature_count} "
                f"does not match len(features)={len(self.features)}."
            )
        return self

    @model_validator(mode="after")
    def _all_features_same_candidate(self) -> "CandidateProfileSnapshot":
        for feature in self.features:
            if feature.candidate_identity_id != self.candidate_identity_id:
                raise ValueError(
                    f"Feature '{feature.feature_identity.feature_type_id}' "
                    f"belongs to candidate '{feature.candidate_identity_id}' "
                    f"but snapshot is for '{self.candidate_identity_id}'."
                )
        return self

    @property
    def feature_type_ids(self) -> frozenset[str]:
        return frozenset(f.feature_identity.feature_type_id for f in self.features)

    @property
    def is_empty(self) -> bool:
        return self.total_feature_count == 0
