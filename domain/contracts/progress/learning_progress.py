# domain/contracts/progress/learning_progress.py
# ADR-016A + ADR-022 + EPIC-02/P2-C1 — LearningProgress (derived, never persisted, immutable)

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from domain.contracts.longitudinal.longitudinal_profile import CrossSessionLanguageCapability


class DimensionalScore(BaseModel):
    """Score for one knowledge dimension at one point in time.

    Derived from a CandidateProfileSnapshot.features entry.
    feature_type_id is the stable cross-session key (ADR-020 §F).
    """

    feature_type_id: str = Field(..., min_length=1)
    semantic_category: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    session_index: int = Field(..., ge=0, description="interview_index of the source session")

    model_config = {"frozen": True, "extra": "forbid"}


class BehavioralScore(BaseModel):
    """Behavioral dimension score for one feature at one session (EPIC-02 §2.7).

    Immutable per-session snapshot of a single feature's confidence value.
    """

    feature_type_id: str = Field(..., min_length=1)
    semantic_category: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    session_index: int = Field(..., ge=0)

    model_config = {"frozen": True, "extra": "forbid"}


class FeatureTrend(BaseModel):
    """Cross-session trend for one behavioral feature dimension (EPIC-02 §2.6).

    trend_direction rule (builder responsibility):
      "improving"  — latest_confidence > earliest_confidence + 0.05
      "declining"  — latest_confidence < earliest_confidence - 0.05
      "stable"     — otherwise
      "insufficient_data" — sessions_observed < 2
    """

    feature_type_id: str = Field(..., min_length=1)
    semantic_category: str = Field(..., min_length=1)
    trend_direction: str = Field(default="stable")
    earliest_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    latest_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    sessions_observed: int = Field(..., ge=1)

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _validate_trend_direction_allowed(self) -> "FeatureTrend":
        allowed = {"improving", "declining", "stable", "insufficient_data"}
        if self.trend_direction not in allowed:
            raise ValueError(
                f"trend_direction must be one of {allowed}, got {self.trend_direction!r}"
            )
        return self


class BehavioralTrend(BaseModel):
    """Cross-session behavioral feature trend summary (EPIC-02 §2.5).

    Derived from LongitudinalProfile.session_snapshots by LearningProgressBuilder.
    Invariant LP-LP-04: sessions_analysed == len(LearningProgress.session_entries).
    Invariant LP-LP-05: all feature_type_id values within feature_trends are unique.
    """

    candidate_identity_id: str = Field(..., min_length=1)
    feature_trends: tuple[FeatureTrend, ...] = Field(default=())
    overall_trend_direction: str = Field(default="stable")
    sessions_analysed: int = Field(..., ge=0)
    schema_version: str = Field(default="1.0", min_length=1)

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _validate_overall_trend_direction_allowed(self) -> "BehavioralTrend":
        allowed = {"improving", "declining", "stable", "insufficient_data"}
        if self.overall_trend_direction not in allowed:
            raise ValueError(
                f"overall_trend_direction must be one of {allowed}, "
                f"got {self.overall_trend_direction!r}"
            )
        return self

    @model_validator(mode="after")
    def _validate_lp_lp_05(self) -> "BehavioralTrend":
        ids = [ft.feature_type_id for ft in self.feature_trends]
        if len(ids) != len(set(ids)):
            raise ValueError(
                "LP-LP-05: all feature_type_id values within feature_trends must be unique"
            )
        return self


class SessionProgressEntry(BaseModel):
    """Progress snapshot derived from one LongitudinalSessionEntry (EPIC-02 P2-C1).

    Immutable projection of a single session's contribution to LearningProgress.
    Derived exclusively from LongitudinalProfile — never from SessionHistory directly.
    """

    session_id: str = Field(..., min_length=1)
    session_index: int = Field(..., ge=0)
    created_at: datetime = Field(...)
    role: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)
    interview_type: str = Field(..., min_length=1)
    question_count: int = Field(..., ge=0)
    knowledge_epoch: str = Field(..., min_length=1)
    dimensional_scores: tuple[DimensionalScore, ...] = Field(default_factory=tuple)
    mean_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    total_features: int = Field(default=0, ge=0)
    total_objectives: int = Field(default=0, ge=0)
    total_narrative_insights: int = Field(default=0, ge=0)
    behavioral_scores: tuple[BehavioralScore, ...] = Field(default=())
    language_ids_present: tuple[str, ...] = Field(default=())

    model_config = {"frozen": True, "extra": "forbid"}


class LearningProgress(BaseModel):
    """Derived, read-only, never-persisted cross-session progress view (ADR-016A + EPIC-02/P2-C1).

    Computed on demand from LongitudinalProfile (ADR-034 Decision 5).
    Never modifies LongitudinalProfile, SessionHistory, KnowledgeSnapshot, or CandidateProfile.

    EPIC-02 invariants:
    - Derived exclusively from LongitudinalProfile (ADR-034 Decision 5).
    - session_entries length equals LongitudinalProfile.session_count (LP-LP-01).
    - session_entries ordered by session_index ascending (LP-LP-02).
    - has_sufficient_data == (len(session_entries) >= 2) (LP-LP-03).
    - BehavioralTrend.sessions_analysed == len(session_entries) (LP-LP-04).
    - All FeatureTrend.feature_type_id values within behavioral_trend are unique (LP-LP-05).
    - Never persisted (LP-LP-06).

    Sole creation path: LearningProgressBuilder.
    """

    candidate_identity_id: str = Field(
        ..., min_length=1, description="Owning candidate (ADR-016A)"
    )
    session_entries: tuple[SessionProgressEntry, ...] = Field(
        default_factory=tuple,
        description="Ordered progress entries — one per LongitudinalSessionEntry, by session_index"
    )
    schema_version: str = Field(default="1.0", min_length=1)
    computed_at: datetime = Field(description="UTC timestamp of derivation")
    knowledge_epoch: str = Field(
        default="1",
        description="KnowledgeEpoch from source sessions (ADR-022 §I)"
    )
    metadata: dict[str, str] = Field(default_factory=dict)
    behavioral_trend: Optional[BehavioralTrend] = Field(
        default=None,
        description="Cross-session behavioral feature trend summary (EPIC-02 §2.5)"
    )
    language_capability_summary: tuple[CrossSessionLanguageCapability, ...] = Field(
        default=(),
        description="Propagated from LongitudinalProfile.language_capability_summary"
    )
    has_sufficient_data: bool = Field(
        default=False,
        description="True when session_count >= 2 (LP-LP-03)"
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def session_count(self) -> int:
        return len(self.session_entries)

    @property
    def is_empty(self) -> bool:
        return self.session_count == 0

    @property
    def latest_entry(self) -> Optional[SessionProgressEntry]:
        if not self.session_entries:
            return None
        return max(self.session_entries, key=lambda e: e.session_index)

    @property
    def earliest_entry(self) -> Optional[SessionProgressEntry]:
        if not self.session_entries:
            return None
        return min(self.session_entries, key=lambda e: e.session_index)

    @property
    def total_questions_answered(self) -> int:
        return sum(e.question_count for e in self.session_entries)
