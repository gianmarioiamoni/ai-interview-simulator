# services/session_close/session_close_metrics.py
# SessionCloseMetrics — timing and counts for one pipeline run

from __future__ import annotations

from pydantic import BaseModel, Field


class SessionCloseMetrics(BaseModel):
    """Timing and size metrics for one SessionClosePipeline execution.

    Pure data record. No computation logic.
    All times are in milliseconds (float).
    """

    session_id: str = Field(..., min_length=1)

    total_elapsed_ms: float = Field(default=0.0, ge=0.0)
    snapshot_assembly_ms: float = Field(default=0.0, ge=0.0)
    history_assembly_ms: float = Field(default=0.0, ge=0.0)

    transcript_entry_count: int = Field(default=0, ge=0)
    timeline_entry_count: int = Field(default=0, ge=0)
    feature_count: int = Field(default=0, ge=0)

    model_config = {"frozen": True, "extra": "forbid"}
