# domain/contracts/progress/learning_progress_builder.py
# EPIC-02/P2-C2 — LearningProgressBuilder migrated to LongitudinalProfile input
# ADR-034 Decision 5: reads exclusively from LongitudinalProfile; SessionHistory[] forbidden.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from domain.contracts.longitudinal.longitudinal_profile import (
    LongitudinalProfile,
    LongitudinalSessionEntry,
)
from domain.contracts.progress.learning_progress import (
    BehavioralScore,
    BehavioralTrend,
    DimensionalScore,
    FeatureTrend,
    LearningProgress,
    SessionProgressEntry,
)


class LearningProgressBuilder:
    """Sole permitted constructor for LearningProgress (ADR-034 Decision 5, EPIC-02/P2-C2).

    Derives LearningProgress exclusively from a LongitudinalProfile.
    Never reads SessionHistory[], KnowledgeSnapshot, or CandidateProfile directly.

    If profile is None, returns an empty LearningProgress with has_sufficient_data=False.

    Usage::

        progress = (
            LearningProgressBuilder()
            .with_longitudinal_profile(profile)
            .build()
        )

    Builder responsibilities:
    - Derive SessionProgressEntry for each LongitudinalSessionEntry.
    - Compute BehavioralTrend (FeatureTrend per feature_type_id; overall direction).
    - Propagate language_capability_summary from profile.
    - Set has_sufficient_data = (session_count >= 2).
    - Order session_entries by session_index ascending (LP-LP-02).
    - Enforce LP-LP-01 through LP-LP-07.
    """

    _TREND_THRESHOLD: float = 0.05

    def __init__(self) -> None:
        self._profile: Optional[LongitudinalProfile] = None
        self._candidate_identity_id: Optional[str] = None
        self._computed_at: Optional[datetime] = None
        self._schema_version: str = "1.0"
        self._metadata: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Fluent setters
    # ------------------------------------------------------------------

    def with_candidate_identity_id(self, candidate_identity_id: str) -> "LearningProgressBuilder":
        """Supply candidate_identity_id for the None-profile empty path only."""
        self._candidate_identity_id = candidate_identity_id
        return self

    def with_longitudinal_profile(
        self, profile: Optional[LongitudinalProfile]
    ) -> "LearningProgressBuilder":
        self._profile = profile
        return self

    def with_computed_at(self, computed_at: datetime) -> "LearningProgressBuilder":
        self._computed_at = computed_at
        return self

    def with_schema_version(self, schema_version: str) -> "LearningProgressBuilder":
        self._schema_version = schema_version
        return self

    def with_metadata(self, metadata: dict[str, str]) -> "LearningProgressBuilder":
        self._metadata = metadata
        return self

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------

    def build(self) -> LearningProgress:
        """Derive and produce an immutable LearningProgress from LongitudinalProfile.

        Returns an empty LearningProgress with has_sufficient_data=False when profile is None.

        Raises:
            ValueError: if profile.candidate_identity_id is blank.
        """
        computed_at = self._computed_at or datetime.now(tz=timezone.utc)

        if self._profile is None:
            candidate_id = self._candidate_identity_id or "unknown"
            return LearningProgress(
                candidate_identity_id=candidate_id,
                session_entries=(),
                schema_version=self._schema_version,
                computed_at=computed_at,
                knowledge_epoch="1",
                metadata=self._metadata,
                behavioral_trend=None,
                language_capability_summary=(),
                has_sufficient_data=False,
            )

        profile = self._profile

        if not profile.candidate_identity_id or not profile.candidate_identity_id.strip():
            raise ValueError(
                "LearningProgressBuilder requires a non-blank candidate_identity_id."
            )

        # session_snapshots are already ordered by interview_index ascending (LP-V-04)
        entries = tuple(
            self._derive_session_entry(entry) for entry in profile.session_snapshots
        )

        behavioral_trend = self._derive_behavioral_trend(profile, entries)
        has_sufficient_data = len(entries) >= 2

        knowledge_epoch = (
            profile.session_snapshots[-1].session_metadata.knowledge_epoch
            if profile.session_snapshots
            else "1"
        )

        return LearningProgress(
            candidate_identity_id=profile.candidate_identity_id,
            session_entries=entries,
            schema_version=self._schema_version,
            computed_at=computed_at,
            knowledge_epoch=knowledge_epoch,
            metadata=self._metadata,
            behavioral_trend=behavioral_trend,
            language_capability_summary=profile.language_capability_summary,
            has_sufficient_data=has_sufficient_data,
        )

    # ------------------------------------------------------------------
    # Private derivation helpers — pure read, no mutation
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_session_entry(entry: LongitudinalSessionEntry) -> SessionProgressEntry:

        profile_snapshot = entry.profile_snapshot
        metadata = entry.session_metadata
        features = profile_snapshot.features

        mean_confidence = (
            sum(f.quality.confidence.value for f in features) / len(features)
            if features
            else 0.0
        )

        dimensional_scores = tuple(
            DimensionalScore(
                feature_type_id=f.feature_identity.feature_type_id,
                semantic_category=f.feature_identity.semantic_category,
                confidence=f.quality.confidence.value,
                session_index=entry.interview_index,
            )
            for f in features
        )

        behavioral_scores = tuple(
            BehavioralScore(
                feature_type_id=f.feature_identity.feature_type_id,
                semantic_category=f.feature_identity.semantic_category,
                confidence=f.quality.confidence.value,
                session_index=entry.interview_index,
            )
            for f in features
        )

        language_ids_present = tuple(
            lc.language_id for lc in metadata.language_capabilities
        )

        return SessionProgressEntry(
            session_id=entry.session_id,
            session_index=entry.interview_index,
            created_at=entry.contributed_at,
            role=metadata.role,
            seniority=metadata.seniority,
            interview_type=metadata.interview_type,
            question_count=metadata.question_count,
            knowledge_epoch=metadata.knowledge_epoch,
            dimensional_scores=dimensional_scores,
            mean_confidence=mean_confidence,
            total_features=profile_snapshot.total_feature_count,
            total_objectives=metadata.total_objectives,
            total_narrative_insights=metadata.total_narrative_insights,
            behavioral_scores=behavioral_scores,
            language_ids_present=language_ids_present,
        )

    def _derive_behavioral_trend(
        self,
        profile: LongitudinalProfile,
        entries: tuple[SessionProgressEntry, ...],
    ) -> BehavioralTrend:
        sessions_analysed = len(entries)

        if sessions_analysed < 2:
            return BehavioralTrend(
                candidate_identity_id=profile.candidate_identity_id,
                feature_trends=(),
                overall_trend_direction="insufficient_data",
                sessions_analysed=sessions_analysed,
            )

        # per-feature: (semantic_category, first_confidence, last_confidence, count)
        feature_data: dict[str, tuple[str, float, float, int]] = {}

        for snap_entry in profile.session_snapshots:
            for feature in snap_entry.profile_snapshot.features:
                fid = feature.feature_identity.feature_type_id
                confidence = feature.quality.confidence.value
                if fid not in feature_data:
                    feature_data[fid] = (
                        feature.feature_identity.semantic_category,
                        confidence,
                        confidence,
                        1,
                    )
                else:
                    cat, first, _last, count = feature_data[fid]
                    feature_data[fid] = (cat, first, confidence, count + 1)

        feature_trends = tuple(
            FeatureTrend(
                feature_type_id=fid,
                semantic_category=cat,
                trend_direction=self._compute_trend_direction(first, last, count),
                earliest_confidence=first,
                latest_confidence=last,
                sessions_observed=count,
            )
            for fid, (cat, first, last, count) in feature_data.items()
        )

        overall_direction = self._compute_overall_trend_direction(feature_trends)

        return BehavioralTrend(
            candidate_identity_id=profile.candidate_identity_id,
            feature_trends=feature_trends,
            overall_trend_direction=overall_direction,
            sessions_analysed=sessions_analysed,
        )

    def _compute_trend_direction(
        self, earliest: float, latest: float, sessions_observed: int
    ) -> str:
        if sessions_observed < 2:
            return "insufficient_data"
        delta = latest - earliest
        if delta > self._TREND_THRESHOLD:
            return "improving"
        if delta < -self._TREND_THRESHOLD:
            return "declining"
        return "stable"

    @staticmethod
    def _compute_overall_trend_direction(
        feature_trends: tuple[FeatureTrend, ...],
    ) -> str:
        if not feature_trends:
            return "insufficient_data"

        counts: dict[str, int] = {"improving": 0, "declining": 0, "stable": 0}
        for ft in feature_trends:
            direction = ft.trend_direction
            if direction in counts:
                counts[direction] += 1

        if counts["improving"] > counts["declining"]:
            return "improving"
        if counts["declining"] > counts["improving"]:
            return "declining"
        return "stable"
