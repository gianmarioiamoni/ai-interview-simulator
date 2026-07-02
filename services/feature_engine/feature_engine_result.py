# services/feature_engine/feature_engine_result.py
# FeatureEngineResult — immutable output of one computation cycle (ADR-020 §C, §E)

from pydantic import BaseModel, Field

from domain.contracts.feature.profile_feature import ProfileFeature
from services.feature_engine.feature_engine_diagnostics import FeatureEngineDiagnostics


class FeatureEngineResult(BaseModel):
    """Immutable output of a single FeatureEngine computation cycle.

    Contains the complete ProfileFeature set to be committed to CandidateProfile,
    plus the diagnostics record for observability.

    ADR-020 §E (Pipeline), §K (Observability):
    - features: the resolved ProfileFeature[] ready for CandidateProfile commit.
    - diagnostics: the full observability record for this cycle.
    - is_successful: False when the cycle aborted (e.g. empty Updater registry,
      unrecoverable Updater exception). In that case features is empty.
    - failure_reason: non-None when is_successful is False.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    current_question_index: int = Field(..., ge=0)
    features: tuple[ProfileFeature, ...] = Field(
        default_factory=tuple,
        description="Resolved ProfileFeatures ready for CandidateProfile commit"
    )
    diagnostics: FeatureEngineDiagnostics = Field(
        ..., description="Full observability record for this cycle"
    )
    is_successful: bool = Field(default=True)
    failure_reason: str | None = Field(
        default=None,
        description="Non-None when is_successful is False"
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def feature_count(self) -> int:
        return len(self.features)

    @property
    def feature_type_ids(self) -> frozenset[str]:
        return frozenset(f.feature_identity.feature_type_id for f in self.features)
