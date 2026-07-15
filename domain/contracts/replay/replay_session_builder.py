# domain/contracts/replay/replay_session_builder.py
# EPIC-03 Phase 3b — ReplaySessionBuilder: sole construction path for ReplaySession.
# Specification per EPIC-03-DOMAIN-CONTRACTS.md §5 and EPIC-03-DATA-MODEL.md §2–§4.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import CandidateProfileSnapshot
from domain.contracts.knowledge_snapshot.knowledge_snapshot import PolicyVersions
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode, ReplaySourcePriority
from domain.contracts.replay.replay_manifest import ReplayManifest
from domain.contracts.replay.replay_question_record import ReplayQuestionRecord
from domain.contracts.replay.replay_session_metadata import ReplaySessionMetadata
from domain.contracts.replay.replay_session import ReplaySession
from domain.contracts.replay.replay_timeline import ReplayTimeline, ReplayTimelineEntry
from domain.contracts.report.scoring_snapshot import ScoringSnapshot
from domain.contracts.session_history.session_history import SessionHistory

_REPLAY_ENGINE_VERSION = "1.3"


class ReplaySessionBuilder:
    """Sole construction path for ReplaySession.

    Assembles a ReplaySession from a SessionHistory by mapping each persisted
    field to its authoritative source per EPIC-03-DATA-MODEL.md §2–§4.

    SRP: object construction only. No business logic, no orchestration, no LLM calls.
    Not a Pydantic model — plain class per EPIC-03-DOMAIN-CONTRACTS.md §5.1.

    Build-time invariants RC-B-01 through RC-B-07 enforced in build().
    Failure path: as_failed() class method for non-fatal construction failures.
    """

    def __init__(self) -> None:
        self._session_history: Optional[SessionHistory] = None
        self._replay_mode: ReplayMode = ReplayMode.STANDARD
        self._replay_level: ReplayLevel = ReplayLevel.PRESENTATION
        self._operator_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Builder interface
    # ------------------------------------------------------------------

    def with_session_history(self, session_history: SessionHistory) -> ReplaySessionBuilder:
        self._session_history = session_history
        return self

    def with_replay_mode(self, replay_mode: ReplayMode) -> ReplaySessionBuilder:
        self._replay_mode = replay_mode
        return self

    def with_replay_level(self, replay_level: ReplayLevel) -> ReplaySessionBuilder:
        self._replay_level = replay_level
        return self

    def with_operator_id(self, operator_id: Optional[str]) -> ReplaySessionBuilder:
        self._operator_id = operator_id
        return self

    # ------------------------------------------------------------------
    # build() — enforces RC-B-01 through RC-B-07
    # ------------------------------------------------------------------

    def build(self) -> ReplaySession:
        """Assemble and return a frozen ReplaySession.

        Raises:
            ValueError: when any RC-B invariant is violated.
        """
        # RC-B-01: All required fields present (Reconstruction Completeness).
        if self._session_history is None:
            raise ValueError("RC-B-01: session_history is required.")

        sh = self._session_history

        # RC-B-04: replay_level must not be REASONING.
        if self._replay_level == ReplayLevel.REASONING:
            raise ValueError("RC-B-04: replay_level REASONING is reserved and not permitted.")

        # Assemble sub-artifacts.
        question_results = self._build_question_results(sh)
        session_metadata = self._build_session_metadata(sh)
        timeline = self._build_timeline(question_results)

        # RC-B-05: question_results ordered by question_index ascending.
        if question_results != tuple(sorted(question_results, key=lambda r: r.question_index)):
            raise ValueError(
                "RC-B-05: question_results must be ordered by question_index ascending."
            )

        # RC-B-06: timeline.total_positions == len(question_results).
        if timeline.total_positions != len(question_results):
            raise ValueError(
                f"RC-B-06: timeline.total_positions ({timeline.total_positions}) "
                f"must equal len(question_results) ({len(question_results)})."
            )

        manifest = self._build_manifest(sh)

        # RC-B-02 and RC-B-03 are enforced by ReplaySession validators V-RS-03/V-RS-04.
        # RC-B-07 is enforced by ReplaySession validators V-RS-01/V-RS-02.

        return ReplaySession(
            session_id=sh.session_id,
            candidate_identity_id=sh.candidate_identity_id,
            schema_version="1.0",
            replay_mode=self._replay_mode,
            replay_level=self._replay_level,
            profile_snapshot=sh.knowledge_snapshot.profile_snapshot,
            narrative=sh.knowledge_snapshot.narrative,
            coaching_snapshot=sh.knowledge_snapshot.coaching_snapshot,
            scoring_snapshot=sh.scoring_snapshot,
            question_results=question_results,
            timeline=timeline,
            session_metadata=session_metadata,
            policy_versions=sh.knowledge_snapshot.policy_versions,
            knowledge_epoch=sh.knowledge_snapshot.knowledge_epoch,
            manifest=manifest,
            is_successful=True,
            failure_reason=None,
            observation_store_snapshot=None,
        )

    # ------------------------------------------------------------------
    # Failure path (RC-B: as_failed)
    # ------------------------------------------------------------------

    @classmethod
    def as_failed(
        cls,
        session_id: str,
        candidate_identity_id: str,
        failure_reason: str,
        replay_mode: ReplayMode = ReplayMode.STANDARD,
        replay_level: ReplayLevel = ReplayLevel.PRESENTATION,
    ) -> ReplaySession:
        """Produce a minimal failed ReplaySession.

        Only permitted alternate construction path per EPIC-03-DOMAIN-CONTRACTS.md §5.5.
        Used by replay_node when SessionHistory is not found or reconstruction fails.
        """
        from domain.contracts.feature.profile_feature import ProfileFeature

        now = datetime.now(tz=timezone.utc)

        # Build a minimal manifest for the failed session.
        manifest = ReplayManifest(
            session_id=session_id,
            candidate_identity_id=candidate_identity_id,
            replay_mode=replay_mode,
            replay_level=replay_level,
            replay_timestamp=now,
            replay_engine_version=_REPLAY_ENGINE_VERSION,
            source_per_component={},
        )

        # Minimal frozen sub-artifacts required for type-safe construction.
        from domain.contracts.coaching.coaching_builder import CoachingBuilder
        from domain.contracts.feature.feature_identity import FeatureIdentity
        from domain.contracts.feature.feature_type import FeatureType
        from domain.contracts.narrative.narrative_builder import NarrativeBuilder
        from domain.contracts.narrative.narrative_section import NarrativeSection
        from domain.contracts.narrative.narrative_section_type import NarrativeSectionType

        empty_profile = CandidateProfileSnapshot(
            candidate_identity_id=candidate_identity_id,
            features=(),
            closed_at_question_index=0,
            total_feature_count=0,
            mean_confidence=0.0,
        )
        _placeholder_identity = FeatureIdentity.for_type(FeatureType.REASONING)

        def _placeholder_section(section_type: NarrativeSectionType) -> NarrativeSection:
            return NarrativeSection(
                section_type=section_type,
                prose="Session reconstruction failed.",
                feature_references=(_placeholder_identity,),
                confidence_context="N/A",
            )

        empty_narrative = (
            NarrativeBuilder()
            .with_overview_section(_placeholder_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
            .with_strengths(_placeholder_section(NarrativeSectionType.STRENGTHS))
            .with_weaknesses(_placeholder_section(NarrativeSectionType.WEAKNESSES))
            .with_growth_areas(_placeholder_section(NarrativeSectionType.GROWTH))
            .with_recommendations(_placeholder_section(NarrativeSectionType.RECOMMENDATIONS))
            .build()
        )
        empty_coaching = CoachingBuilder.empty(session_id=session_id, question_index=0)
        empty_policy = PolicyVersions(
            feature_engine_version="unknown",
            language_policy_version="unknown",
            ttl_policy_version="unknown",
            evaluation_policy_version="unknown",
            narrative_schema_version="unknown",
            coaching_schema_version="unknown",
            profile_schema_version="unknown",
        )
        empty_timeline = ReplayTimeline(
            entries=(),
            total_positions=0,
            first_position=-1,
            last_position=-1,
            is_empty=True,
        )
        empty_metadata = ReplaySessionMetadata(
            interview_index=1,
            session_date=now,
            role="unknown",
            seniority_level="unknown",
            interview_mode="unknown",
            question_count=0,
        )

        return ReplaySession(
            session_id=session_id,
            candidate_identity_id=candidate_identity_id,
            schema_version="1.0",
            replay_mode=replay_mode,
            replay_level=replay_level,
            profile_snapshot=empty_profile,
            narrative=empty_narrative,
            coaching_snapshot=empty_coaching,
            scoring_snapshot=None,
            question_results=(),
            timeline=empty_timeline,
            session_metadata=empty_metadata,
            policy_versions=empty_policy,
            knowledge_epoch="unknown",
            manifest=manifest,
            is_successful=False,
            failure_reason=failure_reason,
            observation_store_snapshot=None,
        )

    # ------------------------------------------------------------------
    # Private assembly helpers
    # ------------------------------------------------------------------

    def _build_question_results(self, sh: SessionHistory) -> tuple[ReplayQuestionRecord, ...]:
        """Assemble ReplayQuestionRecord tuple from question_results + transcript join."""
        # Build lookup: question_id → candidate_answer from transcript.
        answer_by_question_id: dict[str, str] = {
            entry.question_id: entry.answer_content for entry in sh.transcript
        }

        records = []
        for qr in sh.question_results:
            candidate_answer = answer_by_question_id.get(qr.question_id, "")
            records.append(
                ReplayQuestionRecord(
                    question_id=qr.question_id,
                    question_index=qr.question_index,
                    question_type=qr.question_type,
                    area_label=qr.area_label,
                    question_prompt=qr.question_prompt,
                    candidate_answer=candidate_answer,
                    score=qr.score,
                    max_score=qr.max_score,
                    feedback=qr.feedback,
                    strengths=qr.strengths,
                    weaknesses=qr.weaknesses,
                    follow_up_question=qr.follow_up_question,
                    execution_status=qr.execution_status,
                    passed_tests=qr.passed_tests,
                    total_tests=qr.total_tests,
                    ai_hint_explanation=qr.ai_hint_explanation,
                    ai_hint_suggestion=qr.ai_hint_suggestion,
                    attempts=qr.attempts,
                )
            )

        # Sort by question_index ascending (RC-B-05).
        records.sort(key=lambda r: r.question_index)
        return tuple(records)

    def _build_session_metadata(self, sh: SessionHistory) -> ReplaySessionMetadata:
        """Assemble ReplaySessionMetadata per Data Model §3 source corrections."""
        im = sh.interview_metadata

        # RG-02: session_duration_seconds = sum of question_timeline durations when all non-None.
        durations = [e.duration_seconds for e in sh.question_timeline]
        if durations and all(d is not None for d in durations):
            session_duration_seconds: Optional[float] = sum(d for d in durations if d is not None)
        else:
            session_duration_seconds = None

        return ReplaySessionMetadata(
            interview_index=sh.interview_index
            + 1,  # Data Model §3: ge=1; SessionHistory uses 0-based
            session_date=sh.created_at,  # RG-01: session_history.created_at
            role=im.role,
            seniority_level=im.seniority,  # field rename: seniority → seniority_level
            interview_mode=im.interview_mode,
            question_count=len(sh.question_results),  # source correction §1.6
            session_duration_seconds=session_duration_seconds,
            company=im.company,
        )

    def _build_timeline(self, question_results: tuple[ReplayQuestionRecord, ...]) -> ReplayTimeline:
        """Derive ReplayTimeline from ordered question_results."""
        entries = tuple(
            ReplayTimelineEntry(
                position=idx,
                question_id=qr.question_id,
                question_index=qr.question_index,
                area_label=qr.area_label,
                question_type=qr.question_type,
            )
            for idx, qr in enumerate(question_results)
        )
        n = len(entries)
        return ReplayTimeline(
            entries=entries,
            total_positions=n,
            first_position=0 if n > 0 else -1,
            last_position=n - 1 if n > 0 else -1,
            is_empty=(n == 0),
        )

    def _build_manifest(self, sh: SessionHistory) -> ReplayManifest:
        """Build the ReplayManifest for this reconstruction."""
        source_map: dict[str, ReplaySourcePriority] = {
            "profile": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "narrative": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "coaching": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
            "policy_versions": ReplaySourcePriority.KNOWLEDGE_SNAPSHOT,
        }
        if self._replay_level == ReplayLevel.KNOWLEDGE:
            source_map["observation_store_snapshot"] = ReplaySourcePriority.KNOWLEDGE_SNAPSHOT

        return ReplayManifest(
            session_id=sh.session_id,
            candidate_identity_id=sh.candidate_identity_id,
            replay_mode=self._replay_mode,
            replay_level=self._replay_level,
            replay_timestamp=datetime.now(tz=timezone.utc),
            replay_engine_version=_REPLAY_ENGINE_VERSION,
            source_per_component=source_map,
            migration_metadata=None,
        )
