# domain/contracts/knowledge_snapshot/knowledge_snapshot_builder.py
# ADR-022 — KnowledgeSnapshotBuilder (sole creator of KnowledgeSnapshot)

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import (
    KnowledgeSnapshot,
    PolicyVersions,
)
from domain.contracts.narrative.narrative import Narrative


class KnowledgeSnapshotBuilder:
    """Sole permitted constructor path for KnowledgeSnapshot (ADR-022 §E).

    Fluent builder — enforces all structural invariants before build().

    Constraints:
    - All mandatory components must be set before build().
    - build() raises ValueError if any mandatory field is missing.
    - No business logic — construction only.
    - No persistence, no SessionHistory, no Replay.

    Usage::

        snapshot = (
            KnowledgeSnapshotBuilder()
            .with_session_id(session_id)
            .with_candidate_identity_id(candidate_id)
            .with_profile_snapshot(profile_snapshot)
            .with_narrative(narrative)
            .with_coaching_snapshot(coaching_snapshot)
            .with_policy_versions(policy_versions)
            .build()
        )
    """

    def __init__(self) -> None:
        self._session_id: str | None = None
        self._candidate_identity_id: str | None = None
        self._profile_snapshot: CandidateProfileSnapshot | None = None
        self._narrative: Narrative | None = None
        self._coaching_snapshot: CoachingSnapshot | None = None
        self._policy_versions: PolicyVersions | None = None
        self._knowledge_epoch: str = "1"
        self._snapshot_id: str | None = None
        self._created_at: datetime | None = None
        self._metadata: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Fluent setters — mandatory
    # ------------------------------------------------------------------

    def with_session_id(self, session_id: str) -> "KnowledgeSnapshotBuilder":
        self._session_id = session_id
        return self

    def with_candidate_identity_id(self, candidate_identity_id: str) -> "KnowledgeSnapshotBuilder":
        self._candidate_identity_id = candidate_identity_id
        return self

    def with_profile_snapshot(
        self, profile_snapshot: CandidateProfileSnapshot
    ) -> "KnowledgeSnapshotBuilder":
        self._profile_snapshot = profile_snapshot
        return self

    def with_narrative(self, narrative: Narrative) -> "KnowledgeSnapshotBuilder":
        self._narrative = narrative
        return self

    def with_coaching_snapshot(
        self, coaching_snapshot: CoachingSnapshot
    ) -> "KnowledgeSnapshotBuilder":
        self._coaching_snapshot = coaching_snapshot
        return self

    def with_policy_versions(self, policy_versions: PolicyVersions) -> "KnowledgeSnapshotBuilder":
        self._policy_versions = policy_versions
        return self

    # ------------------------------------------------------------------
    # Fluent setters — optional
    # ------------------------------------------------------------------

    def with_knowledge_epoch(self, epoch: str) -> "KnowledgeSnapshotBuilder":
        self._knowledge_epoch = epoch
        return self

    def with_snapshot_id(self, snapshot_id: str) -> "KnowledgeSnapshotBuilder":
        self._snapshot_id = snapshot_id
        return self

    def with_created_at(self, created_at: datetime) -> "KnowledgeSnapshotBuilder":
        self._created_at = created_at
        return self

    def with_metadata(self, metadata: dict[str, str]) -> "KnowledgeSnapshotBuilder":
        self._metadata = metadata
        return self

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------

    def build(self) -> KnowledgeSnapshot:
        """Produce an immutable KnowledgeSnapshot. Sole creation path.

        Raises:
            ValueError: if any mandatory field is missing or if candidate_identity_id
                        does not match between profile_snapshot and the builder.
        """
        missing: list[str] = []
        if self._session_id is None:
            missing.append("session_id")
        if self._candidate_identity_id is None:
            missing.append("candidate_identity_id")
        if self._profile_snapshot is None:
            missing.append("profile_snapshot")
        if self._narrative is None:
            missing.append("narrative")
        if self._coaching_snapshot is None:
            missing.append("coaching_snapshot")
        if self._policy_versions is None:
            missing.append("policy_versions")

        if missing:
            raise ValueError(
                f"KnowledgeSnapshotBuilder is missing mandatory fields: {missing}. "
                "All components are required (ADR-022 §E)."
            )

        # Guard: profile_snapshot must belong to the same candidate
        assert self._profile_snapshot is not None
        assert self._candidate_identity_id is not None
        if self._profile_snapshot.candidate_identity_id != self._candidate_identity_id:
            raise ValueError(
                f"profile_snapshot.candidate_identity_id="
                f"'{self._profile_snapshot.candidate_identity_id}' "
                f"does not match builder candidate_identity_id='{self._candidate_identity_id}'."
            )

        snapshot_id = self._snapshot_id or str(uuid.uuid4())
        created_at = self._created_at or datetime.now(tz=timezone.utc)

        assert self._narrative is not None
        assert self._coaching_snapshot is not None
        assert self._policy_versions is not None

        return KnowledgeSnapshot(
            snapshot_id=snapshot_id,
            session_id=self._session_id,  # type: ignore[arg-type]
            candidate_identity_id=self._candidate_identity_id,
            profile_snapshot=self._profile_snapshot,
            narrative=self._narrative,
            coaching_snapshot=self._coaching_snapshot,
            policy_versions=self._policy_versions,
            knowledge_epoch=self._knowledge_epoch,
            created_at=created_at,
            metadata=self._metadata,
        )
