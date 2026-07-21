# domain/contracts/reasoning/candidate_profile.py

from __future__ import annotations

from pydantic import BaseModel, Field, PrivateAttr

from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.profile_signal import ProfileSignal
from domain.contracts.reasoning.signal_trace import SignalTrace


class CandidateProfile(BaseModel):
    """Evolving candidate assessment updated by InterviewReasoner each cycle.

    Owned exclusively by InterviewReasoner (single-writer, ADR-037).
    Lives inside InterviewMemory (ADR-038).

    Raw per-question scores are NOT stored here — they exist in
    `state.results_by_question`. Only derived aggregates are kept.

    Single authoritative knowledge representation (TD-EP10-001):
    ``features`` (ProfileFeature[] from FeatureEngine). ``dimension_scores``
    is a derived read projection — not a peer stored model field.
    """

    features: tuple[ProfileFeature, ...] = Field(default_factory=tuple)
    signals: dict[ProfileSignal, SignalTrace] = Field(default_factory=dict)
    questions_answered: int = Field(default=0, ge=0)
    areas_covered: list[str] = Field(default_factory=list)
    last_updated_at_question_index: int = Field(default=-1)

    _derived_dimension_scores: dict[ProfileDimension, DimensionTrace] = PrivateAttr(
        default_factory=dict
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def dimension_scores(self) -> dict[ProfileDimension, DimensionTrace]:
        """Derived ProfileDimension → DimensionTrace projection of ``features``."""
        if self._derived_dimension_scores:
            return self._derived_dimension_scores
        if not self.features:
            return {}
        from domain.profile.candidate_profile_derivation_service import (
            CandidateProfileDerivationService,
        )

        return CandidateProfileDerivationService().derive(self.features).dimension_scores
