# services/session_close/session_close_configuration.py
# SessionCloseConfiguration — pipeline behaviour knobs

from __future__ import annotations

from pydantic import BaseModel, Field


class SessionCloseConfiguration(BaseModel):
    """Pipeline behaviour configuration for SessionClosePipeline.

    Carries feature flags and version overrides — no business logic.
    Defaults represent the V1.2 standard close behaviour.
    """

    schema_version: str = Field(default="1.0", min_length=1)
    replay_snapshot_is_complete: bool = Field(
        default=True,
        description="Mark ReplayMetadata.snapshot_is_complete=True (V1.2 standard)"
    )
    recomputation_available: bool = Field(
        default=False,
        description="Mark ReplayMetadata.recomputation_available (V1.2: False)"
    )
    replay_schema_version: str = Field(default="1.0", min_length=1)

    model_config = {"frozen": True, "extra": "forbid"}
