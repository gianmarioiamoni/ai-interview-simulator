# domain/contracts/session_history/session_history_builder.py
# ADR-022 — SessionHistoryBuilder (sole creation path for SessionHistory)

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot
from domain.contracts.language.language_profile import LanguageProfile
from domain.contracts.session_history.session_history import (
    InterviewMetadata,
    QuestionTimelineEntry,
    ReplayMetadata,
    SessionHistory,
    TranscriptEntry,
)


class SessionHistoryBuilder:
    """Sole permitted constructor path for SessionHistory (ADR-022 §E).

    Fluent builder — enforces all structural invariants before build().

    Constraints:
    - All mandatory components must be set before build().
    - build() raises ValueError if any mandatory field is missing.
    - No business logic — construction only.
    - No persistence, no replay logic, no storage.
    - candidate_identity_id must match knowledge_snapshot.candidate_identity_id.
    - session_id must match knowledge_snapshot.session_id.
    - session_id must match language_profile.session_id.

    Usage::

        history = (
            SessionHistoryBuilder()
            .with_session_id(session_id)
            .with_candidate_identity_id(candidate_id)
            .with_interview_index(0)
            .with_knowledge_snapshot(knowledge_snapshot)
            .with_interview_metadata(interview_metadata)
            .with_language_profile(language_profile)
            .build()
        )
    """

    def __init__(self) -> None:
        self._session_id: str | None = None
        self._candidate_identity_id: str | None = None
        self._interview_index: int | None = None
        self._knowledge_snapshot: KnowledgeSnapshot | None = None
        self._transcript: list[TranscriptEntry] = []
        self._question_timeline: list[QuestionTimelineEntry] = []
        self._evaluation_result: Optional[InterviewEvaluation] = None
        self._interview_metadata: InterviewMetadata | None = None
        self._language_profile: LanguageProfile | None = None
        self._replay_metadata: ReplayMetadata = ReplayMetadata()
        self._schema_version: str = "1.0"
        self._created_at: datetime | None = None
        self._metadata: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Fluent setters — mandatory
    # ------------------------------------------------------------------

    def with_session_id(self, session_id: str) -> "SessionHistoryBuilder":
        self._session_id = session_id
        return self

    def with_candidate_identity_id(self, candidate_identity_id: str) -> "SessionHistoryBuilder":
        self._candidate_identity_id = candidate_identity_id
        return self

    def with_interview_index(self, interview_index: int) -> "SessionHistoryBuilder":
        self._interview_index = interview_index
        return self

    def with_knowledge_snapshot(
        self, knowledge_snapshot: KnowledgeSnapshot
    ) -> "SessionHistoryBuilder":
        self._knowledge_snapshot = knowledge_snapshot
        return self

    def with_interview_metadata(
        self, interview_metadata: InterviewMetadata
    ) -> "SessionHistoryBuilder":
        self._interview_metadata = interview_metadata
        return self

    def with_language_profile(self, language_profile: LanguageProfile) -> "SessionHistoryBuilder":
        self._language_profile = language_profile
        return self

    # ------------------------------------------------------------------
    # Fluent setters — optional
    # ------------------------------------------------------------------

    def with_transcript(
        self, transcript: list[TranscriptEntry]
    ) -> "SessionHistoryBuilder":
        self._transcript = list(transcript)
        return self

    def with_question_timeline(
        self, question_timeline: list[QuestionTimelineEntry]
    ) -> "SessionHistoryBuilder":
        self._question_timeline = list(question_timeline)
        return self

    def with_evaluation_result(
        self, evaluation_result: InterviewEvaluation
    ) -> "SessionHistoryBuilder":
        self._evaluation_result = evaluation_result
        return self

    def with_replay_metadata(
        self, replay_metadata: ReplayMetadata
    ) -> "SessionHistoryBuilder":
        self._replay_metadata = replay_metadata
        return self

    def with_schema_version(self, schema_version: str) -> "SessionHistoryBuilder":
        self._schema_version = schema_version
        return self

    def with_created_at(self, created_at: datetime) -> "SessionHistoryBuilder":
        self._created_at = created_at
        return self

    def with_metadata(self, metadata: dict[str, str]) -> "SessionHistoryBuilder":
        self._metadata = metadata
        return self

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------

    def build(self) -> SessionHistory:
        """Produce an immutable SessionHistory. Sole creation path.

        Raises:
            ValueError: if any mandatory field is missing or cross-aggregate
                        identity/session consistency fails.
        """
        missing: list[str] = []
        if self._session_id is None:
            missing.append("session_id")
        if self._candidate_identity_id is None:
            missing.append("candidate_identity_id")
        if self._interview_index is None:
            missing.append("interview_index")
        if self._knowledge_snapshot is None:
            missing.append("knowledge_snapshot")
        if self._interview_metadata is None:
            missing.append("interview_metadata")
        if self._language_profile is None:
            missing.append("language_profile")

        if missing:
            raise ValueError(
                f"SessionHistoryBuilder is missing mandatory fields: {missing}. "
                "All components are required (ADR-022 §E)."
            )

        assert self._session_id is not None
        assert self._candidate_identity_id is not None
        assert self._knowledge_snapshot is not None
        assert self._language_profile is not None

        if self._knowledge_snapshot.candidate_identity_id != self._candidate_identity_id:
            raise ValueError(
                f"knowledge_snapshot.candidate_identity_id="
                f"'{self._knowledge_snapshot.candidate_identity_id}' "
                f"does not match builder candidate_identity_id='{self._candidate_identity_id}'."
            )

        if self._knowledge_snapshot.session_id != self._session_id:
            raise ValueError(
                f"knowledge_snapshot.session_id='{self._knowledge_snapshot.session_id}' "
                f"does not match builder session_id='{self._session_id}'."
            )

        if self._language_profile.session_id != self._session_id:
            raise ValueError(
                f"language_profile.session_id='{self._language_profile.session_id}' "
                f"does not match builder session_id='{self._session_id}'."
            )

        created_at = self._created_at or datetime.now(tz=timezone.utc)

        assert self._interview_metadata is not None
        assert self._interview_index is not None

        return SessionHistory(
            session_id=self._session_id,
            candidate_identity_id=self._candidate_identity_id,
            interview_index=self._interview_index,
            knowledge_snapshot=self._knowledge_snapshot,
            transcript=tuple(self._transcript),
            question_timeline=tuple(self._question_timeline),
            evaluation_result=self._evaluation_result,
            interview_metadata=self._interview_metadata,
            language_profile=self._language_profile,
            replay_metadata=self._replay_metadata,
            schema_version=self._schema_version,
            created_at=created_at,
            metadata=self._metadata,
        )
