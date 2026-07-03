# domain/contracts/progress/learning_progress.py
# ADR-016A + ADR-022 — LearningProgress (derived, never persisted, immutable)

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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


class SessionProgressEntry(BaseModel):
    """Progress snapshot derived from one SessionHistory.

    Immutable projection of a single session's contribution to LearningProgress.
    Never modifies SessionHistory — pure read.
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

    model_config = {"frozen": True, "extra": "forbid"}


class LearningProgress(BaseModel):
    """Derived, read-only, never-persisted cross-session progress view (ADR-016A + ADR-022).

    Always computed on demand from SessionHistory[].
    Never modifies SessionHistory, KnowledgeSnapshot, or CandidateProfile.

    ADR-022 invariants:
    - Derived exclusively from SessionHistory[].knowledge_snapshot.profile_snapshot
    - FeatureIdentity is the stable cross-session comparison key (ADR-020)
    - candidate_identity_id matches all source SessionHistory records
    - session_entries are ordered by session_index ascending

    Sole creation path: LearningProgressBuilder.
    """

    candidate_identity_id: str = Field(
        ..., min_length=1, description="Owning candidate (ADR-016A)"
    )
    session_entries: tuple[SessionProgressEntry, ...] = Field(
        default_factory=tuple,
        description="Ordered progress entries — one per SessionHistory, by session_index"
    )
    schema_version: str = Field(default="1.0", min_length=1)
    computed_at: datetime = Field(description="UTC timestamp of derivation")
    knowledge_epoch: str = Field(
        default="1",
        description="KnowledgeEpoch from source sessions (ADR-022 §I)"
    )
    metadata: dict[str, str] = Field(default_factory=dict)

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
