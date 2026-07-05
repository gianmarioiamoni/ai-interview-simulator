# domain/contracts/report/report_builder.py
# E03-M5 — ReportBuilder v2.0 (sole creation path for Report)
# ADR-023, ADR-025, ADR-032, ADR-033

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.interview.generation_metadata import GenerationMetadata
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.report.question_assessment_record import QuestionAssessmentRecord
from domain.contracts.report.report import Report
from domain.contracts.session_history.session_history import SessionHistory

if TYPE_CHECKING:
    from domain.contracts.report.scoring_narrative import ScoringNarrative
    from domain.contracts.report.scoring_snapshot import ScoringSnapshot


class ReportBuilder:
    """Sole permitted constructor path for Report v2.0 (E03-M5 — ADR-033 Phase 8).

    Fluent builder — enforces all structural invariants before build().

    Two construction paths:
    1. with_session_history() — convenience: populates all mandatory fields
       from a closed SessionHistory in one call (reads v2.0 scoring artefacts).
    2. Manual fluent setters — for test or explicit construction.

    Constraints:
    - All mandatory components must be set before build().
    - build() raises ValueError when any mandatory field is missing.
    - build() raises ValueError if scoring or scoring_narrative is not set (R-04).
    - build() raises ValueError if len(question_assessments) != question_count (V-R-01).
    - No business logic — assembly only.
    - candidate_identity_id must match across all components.

    Usage (fluent)::

        report = (
            ReportBuilder()
            .with_session_history(history)
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
        # Phase 8 — new scoring artefacts (ADR-033)
        self._scoring: ScoringSnapshot | None = None
        self._scoring_narrative: ScoringNarrative | None = None
        self._question_assessments: tuple[QuestionAssessmentRecord, ...] = ()
        self._context_profile: InterviewContextProfile | None = None
        self._generation_metadata: GenerationMetadata | None = None
        self._role: str | None = None
        self._seniority: str | None = None
        self._interview_type: str | None = None
        self._question_count: int | None = None
        self._knowledge_epoch: str | None = None
        self._schema_version: str = "2.0"
        self._created_at: datetime | None = None
        self._metadata: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Convenience loader — reads SessionHistory v2.0 fields
    # ------------------------------------------------------------------

    def with_session_history(self, history: SessionHistory) -> "ReportBuilder":
        """Populate all mandatory fields from a closed SessionHistory v2.0."""
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
        self._knowledge_epoch = history.knowledge_epoch

        # Phase 8 — read new v2.0 scoring artefacts from SessionHistory
        if history.scoring_snapshot is not None:
            self._scoring = history.scoring_snapshot
        if history.scoring_narrative is not None:
            self._scoring_narrative = history.scoring_narrative
        if history.question_results:
            self._question_assessments = tuple(
                self._qrr_to_qar(r) for r in history.question_results
            )
        # question_count reflects assessed questions (question_results count),
        # not session transcript length, to satisfy V-R-01 when evaluation
        # is absent for some or all questions (e.g. sessions without scoring).
        self._question_count = len(self._question_assessments)
        self._context_profile = history.context_profile
        self._generation_metadata = history.generation_metadata

        return self

    @staticmethod
    def _qrr_to_qar(record: object) -> QuestionAssessmentRecord:
        """Copy QuestionResultRecord → QuestionAssessmentRecord (direct field copy, R-15)."""
        from domain.contracts.session_history.question_result_record import QuestionResultRecord

        assert isinstance(record, QuestionResultRecord)
        return QuestionAssessmentRecord(
            question_id=record.question_id,
            question_index=record.question_index,
            question_type=record.question_type,
            area_label=record.area_label,
            question_prompt=record.question_prompt,
            score=record.score,
            max_score=record.max_score,
            feedback=record.feedback,
            strengths=record.strengths,
            weaknesses=record.weaknesses,
            follow_up_question=record.follow_up_question,
            passed_tests=record.passed_tests,
            total_tests=record.total_tests,
            execution_status=record.execution_status,
            attempts=record.attempts,
            ai_hint_explanation=record.ai_hint_explanation,
            ai_hint_suggestion=record.ai_hint_suggestion,
            schema_version=record.schema_version,
        )

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

    # Phase 8 — new scoring setters (ADR-033)

    def with_scoring(self, scoring: "ScoringSnapshot") -> "ReportBuilder":
        """Set ScoringSnapshot (required for build to succeed — R-04)."""
        self._scoring = scoring
        return self

    def with_scoring_narrative(self, scoring_narrative: "ScoringNarrative") -> "ReportBuilder":
        """Set ScoringNarrative (required for build to succeed — R-04)."""
        self._scoring_narrative = scoring_narrative
        return self

    def with_question_assessments(
        self, question_assessments: tuple[QuestionAssessmentRecord, ...]
    ) -> "ReportBuilder":
        """Set QuestionAssessmentRecord tuple."""
        self._question_assessments = question_assessments
        return self

    def with_context_profile(self, context_profile: InterviewContextProfile) -> "ReportBuilder":
        """Set InterviewContextProfile (required for build to succeed)."""
        self._context_profile = context_profile
        return self

    def with_generation_metadata(
        self, generation_metadata: GenerationMetadata | None
    ) -> "ReportBuilder":
        """Set GenerationMetadata (optional — None renders token count as 0, R-14)."""
        self._generation_metadata = generation_metadata
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
        """Produce an immutable Report v2.0. Sole creation path.

        Raises:
            ValueError: if any mandatory field is missing, scoring/scoring_narrative
                        not set (R-04), V-R-01 count mismatch, or cross-component
                        identity consistency fails.
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
        # Phase 8 mandatory fields (R-04, ADR-033)
        if self._scoring is None:
            missing.append("scoring")
        if self._scoring_narrative is None:
            missing.append("scoring_narrative")
        if self._context_profile is None:
            missing.append("context_profile")

        if missing:
            raise ValueError(
                f"ReportBuilder is missing mandatory fields: {missing}. "
                "All components are required (E03-M5, ADR-033)."
            )

        assert self._profile_snapshot is not None
        assert self._candidate_identity_id is not None

        if self._profile_snapshot.candidate_identity_id != self._candidate_identity_id:
            raise ValueError(
                f"profile_snapshot.candidate_identity_id="
                f"'{self._profile_snapshot.candidate_identity_id}' "
                f"does not match builder candidate_identity_id='{self._candidate_identity_id}'."
            )

        # V-R-01: question_assessments count must equal question_count
        assert self._question_count is not None
        if len(self._question_assessments) != self._question_count:
            raise ValueError(
                f"V-R-01: len(question_assessments)={len(self._question_assessments)} "
                f"does not match question_count={self._question_count}."
            )

        report_id = self._report_id or str(uuid.uuid4())
        created_at = self._created_at or datetime.now(tz=timezone.utc)

        assert self._session_id is not None
        assert self._narrative is not None
        assert self._coaching_snapshot is not None
        assert self._role is not None
        assert self._seniority is not None
        assert self._interview_type is not None
        assert self._interview_index is not None
        assert self._knowledge_epoch is not None
        assert self._scoring is not None
        assert self._scoring_narrative is not None
        assert self._context_profile is not None

        return Report(
            report_id=report_id,
            session_id=self._session_id,
            candidate_identity_id=self._candidate_identity_id,
            interview_index=self._interview_index,
            profile_snapshot=self._profile_snapshot,
            narrative=self._narrative,
            coaching_snapshot=self._coaching_snapshot,
            question_assessments=self._question_assessments,
            scoring=self._scoring,
            scoring_narrative=self._scoring_narrative,
            context_profile=self._context_profile,
            generation_metadata=self._generation_metadata,
            role=self._role,
            seniority=self._seniority,
            interview_type=self._interview_type,
            question_count=self._question_count,
            knowledge_epoch=self._knowledge_epoch,
            schema_version=self._schema_version,
            created_at=created_at,
            metadata=self._metadata,
        )
