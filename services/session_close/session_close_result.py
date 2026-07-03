# services/session_close/session_close_result.py
# SessionCloseResult — immutable output of SessionClosePipeline

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from domain.contracts.session_history.session_history import SessionHistory
from services.session_close.session_close_diagnostics import SessionCloseDiagnostics


class SessionCloseResult(BaseModel):
    """Immutable output produced by SessionClosePipeline.

    On success:
    - is_successful=True
    - session_history is populated
    - diagnostics.is_successful=True

    On failure:
    - is_successful=False
    - session_history is None
    - diagnostics.failure_reason is set

    No persistence. No repository. Caller decides what to do with session_history.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)

    is_successful: bool = Field(default=True)
    session_history: Optional[SessionHistory] = Field(default=None)
    diagnostics: SessionCloseDiagnostics = Field(...)

    failure_reason: Optional[str] = Field(default=None)
    schema_version: str = Field(default="1.0", min_length=1)

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}
