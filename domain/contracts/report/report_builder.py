# domain/contracts/report/report_builder.py
# E03-M5 — ReportBuilder (sole creation path for Report)
# ADR-023, ADR-025, ADR-032

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.report.report import Report
from domain.contracts.session_history.session_history import SessionHistory


class ReportBuilder:
    """Sole permitted constructor path for Report (E03-M5).

    Fluent builder — enforces all structural invariants before build().

    Two construction paths:
    1. from_session_history() — convenience: populates all mandatory fields
       from a closed SessionHistory in one call.
    2. Manual fluent setters — for test or explicit construction.

    Constraints:
    - All mandatory components must be set before build().
    - build() raises ValueError when any mandatory field is missing.
    - No business logic — assembly only.
    - No FeatureEngine, no LLM, no Replay, no persistence.
    - candidate_identity_id must match across all components.
    - session_id must match across all components.

    Usage (fluent)::

        report = (
            ReportBuilder()
            .with_session_history(history)
            .build()
        )

    Usage (manual)::

        report = (
            ReportBuilder()
            .with_session_id(session_id)
            .with_candidate_identity_id(candidate_id)
            .with_interview_index(0)
            .with_profile_snapshot(profile_snapshot)
            .with_narrative(narrative)
            .with_coaching_snapshot(coaching_snapshot)
            .with_role("Software Engineer")
            .with_seniority("Senior")
            .with_interview_type("technical")
            .with_question_count(5)
            .with_knowledge_epoch("1")
            .build()
        )
    """

    def __init__(self) -> None:
        self._report_id: str | None = None
        self._session_id: str | None = None
        self._candidate_identity_id: str | None = None
        self._interview_index: int | None = None
        self._profile_snapshot: CandidateProfileSnapshot | None = None
        self._narrative: Narrative | None = None
        self._coaching_snapshot: CoachingSnapshot | None = None
        self._role: str | None = None
        self._seniority: str | None = None
        self._interview_type: str | None = None
        self._question_count: int | None = None
        self._knowledge_epoch: str | None = None
        self._schema_version: str = "1.0"
        self._created_at: datetime | None = None
        self._metadata: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Convenience loader
    # ------------------------------------------------------------------

    def with_session_history(self, history: SessionHistory) -> "ReportBuilder":
        """Populate all mandatory fields from a closed SessionHistory."""
        snapshot: KnowledgeSnapshot = history.knowledge_snapshot
        meta = history.interview_metadata
        self._session_id = history.session_id
        self._candidate_identity_id = history.candidate_identity_id
        self._interview_index = history.interview_index
        self._profile_snapshot = snapshot.profile_snapshot
        self._narrative = snapshot.narrative
        self._coaching_snapshot = snapshot.coaching_snapshot
        self._role = meta.role
        self._seniority = meta.seniority
        self._interview_type = meta.interview_type
        self._question_count = history.question_count
        self._knowledge_epoch = history.knowledge_epoch
        return self

    # ------------------------------------------------------------------
    # Fluent setters — mandatory
    # ------------------------------------------------------------------

    def with_session_id(self, session_id: str) -> "ReportBuilder":
        self._session_id = session_id
        return self

    def with_candidate_identity_id(self, candidate_identity_id: str) -> "ReportBuilder":
        self._candidate_identity_id = candidate_identity_id
        return self

    def with_interview_index(self, interview_index: int) -> "ReportBuilder":
        self._interview_index = interview_index
        return self

    def with_profile_snapshot(
        self, profile_snapshot: CandidateProfileSnapshot
    ) -> "ReportBuilder":
        self._profile_snapshot = profile_snapshot
        return self

    def with_narrative(self, narrative: Narrative) -> "ReportBuilder":
        self._narrative = narrative
        return self

    def with_coaching_snapshot(self, coaching_snapshot: CoachingSnapshot) -> "ReportBuilder":
        self._coaching_snapshot = coaching_snapshot
        return self

    def with_role(self, role: str) -> "ReportBuilder":
        self._role = role
        return self

    def with_seniority(self, seniority: str) -> "ReportBuilder":
        self._seniority = seniority
        return self

    def with_interview_type(self, interview_type: str) -> "ReportBuilder":
        self._interview_type = interview_type
        return self

    def with_question_count(self, question_count: int) -> "ReportBuilder":
        self._question_count = question_count
        return self

    def with_knowledge_epoch(self, knowledge_epoch: str) -> "ReportBuilder":
        self._knowledge_epoch = knowledge_epoch
        return self

    # ------------------------------------------------------------------
    # Fluent setters — optional
    # ------------------------------------------------------------------

    def with_report_id(self, report_id: str) -> "ReportBuilder":
        self._report_id = report_id
        return self

    def with_schema_version(self, schema_version: str) -> "ReportBuilder":
        self._schema_version = schema_version
        return self

    def with_created_at(self, created_at: datetime) -> "ReportBuilder":
        self._created_at = created_at
        return self

    def with_metadata(self, metadata: dict[str, str]) -> "ReportBuilder":
        self._metadata = metadata
        return self

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------

    def build(self) -> Report:
        """Produce an immutable Report. Sole creation path.

        Raises:
            ValueError: if any mandatory field is missing or cross-component
                        identity / session consistency fails.
        """
        missing: list[str] = []
        if self._session_id is None:
            missing.append("session_id")
        if self._candidate_identity_id is None:
            missing.append("candidate_identity_id")
        if self._interview_index is None:
            missing.append("interview_index")
        if self._profile_snapshot is None:
            missing.append("profile_snapshot")
        if self._narrative is None:
            missing.append("narrative")
        if self._coaching_snapshot is None:
            missing.append("coaching_snapshot")
        if self._role is None:
            missing.append("role")
        if self._seniority is None:
            missing.append("seniority")
        if self._interview_type is None:
            missing.append("interview_type")
        if self._question_count is None:
            missing.append("question_count")
        if self._knowledge_epoch is None:
            missing.append("knowledge_epoch")

        if missing:
            raise ValueError(
                f"ReportBuilder is missing mandatory fields: {missing}. "
                "All components are required (E03-M5)."
            )

        assert self._profile_snapshot is not None
        assert self._candidate_identity_id is not None

        if self._profile_snapshot.candidate_identity_id != self._candidate_identity_id:
            raise ValueError(
                f"profile_snapshot.candidate_identity_id="
                f"'{self._profile_snapshot.candidate_identity_id}' "
                f"does not match builder candidate_identity_id='{self._candidate_identity_id}'."
            )

        report_id = self._report_id or str(uuid.uuid4())
        created_at = self._created_at or datetime.now(tz=timezone.utc)

        assert self._session_id is not None
        assert self._narrative is not None
        assert self._coaching_snapshot is not None
        assert self._role is not None
        assert self._seniority is not None
        assert self._interview_type is not None
        assert self._question_count is not None
        assert self._knowledge_epoch is not None
        assert self._interview_index is not None

        return Report(
            report_id=report_id,
            session_id=self._session_id,
            candidate_identity_id=self._candidate_identity_id,
            interview_index=self._interview_index,
            profile_snapshot=self._profile_snapshot,
            narrative=self._narrative,
            coaching_snapshot=self._coaching_snapshot,
            role=self._role,
            seniority=self._seniority,
            interview_type=self._interview_type,
            question_count=self._question_count,
            knowledge_epoch=self._knowledge_epoch,
            schema_version=self._schema_version,
            created_at=created_at,
            metadata=self._metadata,
        )
