# domain/contracts/replay/replay_session_metadata.py
# EPIC-03 Phase 2b — ReplaySessionMetadata: session-level context for Replay UI.
# Field specification per EPIC-03-DATA-MODEL.md §3 (source corrections applied).

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReplaySessionMetadata(BaseModel, frozen=True, extra="forbid"):
    """Session-level context assembled by ReplaySessionBuilder for Replay UI rendering.

    Fields sourced from SessionHistory top-level and InterviewMetadata per
    EPIC-03-DATA-MODEL.md §3. Source corrections from Data Model §1.1 are applied:
    - interview_index  ← session_history.interview_index (not InterviewMetadata)
    - session_date     ← session_history.created_at (RG-01)
    - seniority_level  ← interview_metadata.seniority (field rename projection, not stored)
    - question_count   ← len(session_history.question_results) (not transcript length)
    - company          ← interview_metadata.company (added per Data Model §3)
    """

    interview_index: int = Field(..., ge=1)
    session_date: datetime
    role: str = Field(..., min_length=1)
    seniority_level: str = Field(..., min_length=1)
    interview_mode: str = Field(..., min_length=1)
    question_count: int = Field(..., ge=0)
    session_duration_seconds: Optional[float] = None
    company: Optional[str] = None
