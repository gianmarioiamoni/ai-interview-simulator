# domain/contracts/knowledge_snapshot/__init__.py
# KnowledgeSnapshot Layer — ADR-022 + ADR-032 contracts (EPIC-03/04, Sprint 9A)

from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import (
    KnowledgeSnapshot,
    PolicyVersions,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_builder import (
    KnowledgeSnapshotBuilder,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_statistics import (
    KnowledgeSnapshotStatistics,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_summary import (
    KnowledgeSnapshotSummary,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_validator import (
    KnowledgeSnapshotValidationResult,
    KnowledgeSnapshotValidator,
)

__all__ = [
    "CandidateProfileSnapshot",
    "KnowledgeSnapshot",
    "PolicyVersions",
    "KnowledgeSnapshotBuilder",
    "KnowledgeSnapshotStatistics",
    "KnowledgeSnapshotSummary",
    "KnowledgeSnapshotValidator",
    "KnowledgeSnapshotValidationResult",
]
