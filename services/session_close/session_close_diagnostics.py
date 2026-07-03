# services/session_close/session_close_diagnostics.py
# SessionCloseDiagnostics — observability record for one pipeline run

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from services.session_close.session_close_metrics import SessionCloseMetrics


class SessionCloseDiagnostics(BaseModel):
    """Observability record produced by one SessionClosePipeline run.

    Mirrors FeatureEngineDiagnostics / ReplayStatistics patterns — pure
    data record, no computation logic.

    is_successful reflects whether the pipeline completed without error.
    stages_completed lists each stage that ran ('snapshot', 'history').
    failure_stage is non-None only when is_successful is False.
    failure_reason is non-None only when is_successful is False.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    interview_index: int = Field(..., ge=0)

    is_successful: bool = Field(default=True)
    stages_completed: tuple[str, ...] = Field(default_factory=tuple)
    failure_stage: Optional[str] = Field(default=None)
    failure_reason: Optional[str] = Field(default=None)

    metrics: SessionCloseMetrics = Field(...)

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def stage_count(self) -> int:
        return len(self.stages_completed)
