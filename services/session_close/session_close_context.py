# services/session_close/session_close_context.py
# SessionCloseContext — all inputs required to close an interview session

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.generation_metadata import GenerationMetadata
from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot
from domain.contracts.language.language_profile import LanguageProfile
from domain.contracts.report.scoring_narrative import ScoringNarrative
from domain.contracts.report.scoring_snapshot import ScoringSnapshot
from domain.contracts.session_history.question_result_record import QuestionResultRecord
from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    TranscriptEntry,
)


class SessionCloseContext(BaseModel):
    """Input contract for SessionClosePipeline.

    Carries all pre-computed domain artifacts needed to assemble SessionHistory.
    Pipeline owns orchestration only — no business logic lives here.

    Required:
    - session_id, candidate_identity_id, interview_index: identity
    - knowledge_snapshot: already built by KnowledgeSnapshotBuilder upstream
    - interview_metadata: role/seniority/mode config
    - language_profile: language context frozen at session start
    - transcript + question_timeline: session content

    Optional:
    - evaluation_result: present when evaluation completed successfully
    - close_reason: why the session was closed (normal / timeout / error)
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    interview_index: int = Field(..., ge=0)

    knowledge_snapshot: KnowledgeSnapshot = Field(...)
    interview_metadata: InterviewMetadata = Field(...)
    language_profile: LanguageProfile = Field(...)

    transcript: tuple[TranscriptEntry, ...] = Field(default_factory=tuple)
    question_timeline: tuple[QuestionTimelineEntry, ...] = Field(default_factory=tuple)
    evaluation_result: Optional[InterviewEvaluation] = Field(default=None)

    # Phase 7B (ADR-033): new scoring artifacts — bridge fields alongside evaluation_result.
    scoring_snapshot: ScoringSnapshot | None = Field(default=None)
    scoring_narrative: ScoringNarrative | None = Field(default=None)
    question_results: tuple[QuestionResultRecord, ...] = Field(default_factory=tuple)
    context_profile: InterviewContextProfile | None = Field(default=None)
    generation_metadata: GenerationMetadata | None = Field(default=None)

    close_reason: str = Field(
        default="normal",
        description="Why the session was closed: 'normal' | 'timeout' | 'error'"
    )
    schema_version: str = Field(default="1.0", min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}
