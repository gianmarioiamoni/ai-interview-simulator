# domain/contracts/session_history/session_history.py
# ADR-022 Section E — SessionHistory (immutable historical record of a completed session)

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_setup import InterviewSetup
from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot
from domain.contracts.language.language_profile import LanguageProfile


class TranscriptEntry(BaseModel):
    """One question-and-answer exchange in the session transcript.

    Immutable record — ordered by question_index.
    """

    question_index: int = Field(..., ge=0)
    question_id: str = Field(..., min_length=1)
    question_prompt: str = Field(..., min_length=1)
    answer_content: str = Field(..., min_length=1)
    answer_attempt: int = Field(..., ge=1)

    model_config = {"frozen": True, "extra": "forbid"}


class QuestionTimelineEntry(BaseModel):
    """Per-question metadata: language, category, difficulty, timing.

    Invariant: question_index matches the corresponding TranscriptEntry.
    """

    question_index: int = Field(..., ge=0)
    question_id: str = Field(..., min_length=1)
    question_type: str = Field(..., min_length=1)
    question_difficulty: str = Field(..., min_length=1)
    language_id: Optional[str] = Field(
        default=None,
        description="Active language_id for coding questions; None for written/HR"
    )
    duration_seconds: Optional[float] = Field(
        default=None, ge=0.0, description="Time spent on this question"
    )

    model_config = {"frozen": True, "extra": "forbid"}


class ReplayMetadata(BaseModel):
    """Replay access hints embedded in SessionHistory (ADR-022 §E, RF-01–RF-05).

    snapshot_is_complete: True when KnowledgeSnapshot fully satisfies replay
    without any live pipeline invocation.
    recomputation_available: True when ObservationStore snapshot is embedded
    and ReplayUpdater can reconstruct the profile if needed (RF-02/RF-05).
    """

    snapshot_is_complete: bool = Field(default=True)
    recomputation_available: bool = Field(default=False)
    replay_schema_version: str = Field(default="1.0", min_length=1)

    model_config = {"frozen": True, "extra": "forbid"}


class InterviewMetadata(BaseModel):
    """Session configuration captured at session close (ADR-022 §E).

    Immutable descriptor of how the session was configured — not the live result.
    """

    role: str = Field(..., min_length=1, description="Role title for this interview")
    seniority: str = Field(..., min_length=1, description="Seniority / level")
    interview_type: str = Field(..., min_length=1)
    interview_mode: str = Field(..., min_length=1, description="Written / Coding / SQL / Mixed")
    session_language: str = Field(..., min_length=1, description="UI language code (e.g. 'en')")
    question_count: int = Field(..., ge=1)
    company: Optional[str] = Field(default=None, description="Target company if provided")

    model_config = {"frozen": True, "extra": "forbid"}


class SessionHistory(BaseModel):
    """Immutable historical memory of one completed interview session (ADR-022 §E).

    Write-once. Self-contained. The authoritative historical record.

    ADR-022 invariants enforced:
    - K-01: Write-once — frozen=True
    - K-07: schema_version always preserved
    - K-08: KnowledgeEpoch is always recorded in the embedded KnowledgeSnapshot
    - K-10: No references to live runtime objects

    Ownership: CandidateIdentity (via candidate_identity_id foreign key — ADR-016A).
    Creator: SessionHistoryBuilder (sole creation path).
    """

    session_id: str = Field(..., min_length=1, description="Unique session identifier (uuid4)")
    candidate_identity_id: str = Field(
        ..., min_length=1, description="Owning candidate (ADR-016A)"
    )
    interview_index: int = Field(
        ..., ge=0, description="Sequential session number for this CandidateIdentity (0-based)"
    )

    knowledge_snapshot: KnowledgeSnapshot = Field(
        ..., description="Immutable KnowledgeSnapshot for this session (ADR-022 §C)"
    )

    transcript: tuple[TranscriptEntry, ...] = Field(
        default_factory=tuple,
        description="Ordered question-and-answer sequence"
    )
    question_timeline: tuple[QuestionTimelineEntry, ...] = Field(
        default_factory=tuple,
        description="Per-question metadata: language, type, difficulty, timing"
    )
    evaluation_result: Optional[InterviewEvaluation] = Field(
        default=None,
        description="Session-level evaluation aggregate (ADR-022 §E)"
    )

    interview_metadata: InterviewMetadata = Field(
        ..., description="Session configuration: role, seniority, mode, language, question count"
    )
    language_profile: LanguageProfile = Field(
        ..., description="LanguageProfile frozen at session start (ADR-019, ADR-022 §E)"
    )
    replay_metadata: ReplayMetadata = Field(
        default_factory=ReplayMetadata,
        description="Replay access hints (ADR-022 §F)"
    )

    schema_version: str = Field(
        default="1.0",
        min_length=1,
        description="Schema version of the SessionHistory record itself (ADR-022 §G)"
    )
    created_at: datetime = Field(description="UTC timestamp of session close")
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Reserved extensibility metadata (ADR-029 extension point)"
    )

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}

    @property
    def question_count(self) -> int:
        return len(self.transcript)

    @property
    def knowledge_epoch(self) -> str:
        return self.knowledge_snapshot.knowledge_epoch

    @property
    def is_replay_ready(self) -> bool:
        return self.replay_metadata.snapshot_is_complete
