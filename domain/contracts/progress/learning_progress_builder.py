# domain/contracts/progress/learning_progress_builder.py
# ADR-016A + ADR-022 — LearningProgressBuilder (sole creation path for LearningProgress)

from __future__ import annotations

from datetime import datetime, timezone

from domain.contracts.progress.learning_progress import (
    DimensionalScore,
    LearningProgress,
    SessionProgressEntry,
)
from domain.contracts.session_history.session_history import SessionHistory


class LearningProgressBuilder:
    """Sole permitted constructor for LearningProgress.

    Derives LearningProgress from a list of SessionHistory records.
    Never modifies SessionHistory, KnowledgeSnapshot, or CandidateProfile.
    All derivation is pure read.

    Rules:
    - All SessionHistory records must share the same candidate_identity_id.
    - SessionHistory records are not required to be pre-sorted.
    - builder orders entries by interview_index ascending.
    - build() raises ValueError if candidate_identity_id is missing or inconsistent.

    Usage::

        progress = (
            LearningProgressBuilder()
            .with_candidate_identity_id(candidate_id)
            .with_session_histories(histories)
            .build()
        )
    """

    def __init__(self) -> None:
        self._candidate_identity_id: str | None = None
        self._session_histories: list[SessionHistory] = []
        self._computed_at: datetime | None = None
        self._schema_version: str = "1.0"
        self._metadata: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Fluent setters
    # ------------------------------------------------------------------

    def with_candidate_identity_id(self, candidate_identity_id: str) -> "LearningProgressBuilder":
        self._candidate_identity_id = candidate_identity_id
        return self

    def with_session_histories(
        self, histories: list[SessionHistory]
    ) -> "LearningProgressBuilder":
        self._session_histories = list(histories)
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
        """Derive and produce an immutable LearningProgress.

        Raises:
            ValueError: if candidate_identity_id is missing or if any SessionHistory
                        belongs to a different candidate.
        """
        if not self._candidate_identity_id:
            raise ValueError(
                "LearningProgressBuilder requires candidate_identity_id."
            )

        for history in self._session_histories:
            if history.candidate_identity_id != self._candidate_identity_id:
                raise ValueError(
                    f"SessionHistory '{history.session_id}' belongs to "
                    f"candidate '{history.candidate_identity_id}', not "
                    f"'{self._candidate_identity_id}'."
                )

        sorted_histories = sorted(
            self._session_histories, key=lambda h: h.interview_index
        )

        entries = tuple(
            self._derive_session_entry(h) for h in sorted_histories
        )

        knowledge_epoch = (
            self._session_histories[0].knowledge_epoch
            if self._session_histories
            else "1"
        )

        return LearningProgress(
            candidate_identity_id=self._candidate_identity_id,
            session_entries=entries,
            schema_version=self._schema_version,
            computed_at=self._computed_at or datetime.now(tz=timezone.utc),
            knowledge_epoch=knowledge_epoch,
            metadata=self._metadata,
        )

    # ------------------------------------------------------------------
    # Private derivation helpers — pure read, no mutation
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_session_entry(history: SessionHistory) -> SessionProgressEntry:
        snapshot = history.knowledge_snapshot
        profile = snapshot.profile_snapshot
        features = profile.features

        mean_confidence = (
            sum(f.quality.confidence.value for f in features) / len(features)
            if features else 0.0
        )

        dimensional_scores = tuple(
            DimensionalScore(
                feature_type_id=f.feature_identity.feature_type_id,
                semantic_category=f.feature_identity.semantic_category,
                confidence=f.quality.confidence.value,
                session_index=history.interview_index,
            )
            for f in features
        )

        coaching_stats = snapshot.coaching_snapshot.statistics

        return SessionProgressEntry(
            session_id=history.session_id,
            session_index=history.interview_index,
            created_at=history.created_at,
            role=history.interview_metadata.role,
            seniority=history.interview_metadata.seniority,
            interview_type=history.interview_metadata.interview_type,
            question_count=history.question_count,
            knowledge_epoch=history.knowledge_epoch,
            dimensional_scores=dimensional_scores,
            mean_confidence=mean_confidence,
            total_features=profile.total_feature_count,
            total_objectives=coaching_stats.total_objectives,
            total_narrative_insights=snapshot.narrative.insight_count,
        )
