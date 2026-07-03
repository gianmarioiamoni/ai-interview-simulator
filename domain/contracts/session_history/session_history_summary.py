# domain/contracts/session_history/session_history_summary.py
# ADR-022 — SessionHistorySummary (lightweight read-only view of a SessionHistory)

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from domain.contracts.session_history.session_history import SessionHistory


class SessionHistorySummary(BaseModel):
    """Lightweight, immutable summary view of a SessionHistory.

    Provides key aggregate properties without carrying full transcript,
    knowledge payloads, or coaching data. Suitable for session lists,
    progress display, logging, and monitoring.

    Mirrors KnowledgeSnapshotSummary pattern at the session layer.
    Constraints:
    - No LLM, no business logic, no mutation.
    - Immutable after construction (frozen=True).
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    interview_index: int = Field(..., ge=0)

    role: str = Field(..., min_length=1)
    interview_type: str = Field(..., min_length=1)
    question_count: int = Field(..., ge=0)

    knowledge_epoch: str = Field(..., min_length=1)
    schema_version: str = Field(..., min_length=1)
    created_at: datetime = Field(...)

    total_features: int = Field(..., ge=0)
    total_objectives: int = Field(..., ge=0)
    total_narrative_insights: int = Field(..., ge=0)
    mean_feature_confidence: float = Field(..., ge=0.0, le=1.0)

    is_replay_ready: bool = Field(default=True)
    has_evaluation: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_history(cls, history: SessionHistory) -> "SessionHistorySummary":
        """Produce a lightweight summary from a SessionHistory. Pure derivation."""
        snapshot = history.knowledge_snapshot
        profile_snapshot = snapshot.profile_snapshot
        features = profile_snapshot.features
        mean_feature_conf = (
            sum(f.quality.confidence.value for f in features) / len(features)
            if features else 0.0
        )

        return cls(
            session_id=history.session_id,
            candidate_identity_id=history.candidate_identity_id,
            interview_index=history.interview_index,
            role=history.interview_metadata.role,
            interview_type=history.interview_metadata.interview_type,
            question_count=history.question_count,
            knowledge_epoch=history.knowledge_epoch,
            schema_version=history.schema_version,
            created_at=history.created_at,
            total_features=profile_snapshot.total_feature_count,
            total_objectives=snapshot.coaching_snapshot.statistics.total_objectives,
            total_narrative_insights=snapshot.narrative.insight_count,
            mean_feature_confidence=mean_feature_conf,
            is_replay_ready=history.is_replay_ready,
            has_evaluation=history.evaluation_result is not None,
        )
