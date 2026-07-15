# domain/contracts/replay/replay_session.py
# EPIC-03 Phase 6b — ReplaySession (V1.3 Projection Artifact, final name after migration).
# Canonical, immutable replay artifact per ADR-037 Decision 1.
# Field specification per EPIC-03-DATA-MODEL.md §2 (18 fields).

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import CandidateProfileSnapshot
from domain.contracts.knowledge_snapshot.knowledge_snapshot import PolicyVersions
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_manifest import ReplayManifest
from domain.contracts.replay.replay_question_record import ReplayQuestionRecord
from domain.contracts.replay.replay_session_metadata import ReplaySessionMetadata
from domain.contracts.replay.replay_timeline import ReplayTimeline
from domain.contracts.report.scoring_snapshot import ScoringSnapshot


class ReplaySession(BaseModel, frozen=True, extra="forbid"):
    """V1.3 canonical, immutable Replay Projection Artifact.

    Produced exclusively by ReplaySessionBuilder (sole construction path).
    Written exclusively by replay_node (sole writer — I-R01).
    Never persisted (ADR-037 D1 §1.4).
    LLM-free (I-11): no LLM call may occur during construction.

    18 fields per EPIC-03-DATA-MODEL.md §2. Validators V-RS-01 through V-RS-06
    per EPIC-03-DOMAIN-CONTRACTS.md §1.4.
    """

    model_config = {
        "frozen": True,
        "extra": "forbid",
        "arbitrary_types_allowed": True,
    }

    # Identity
    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    schema_version: str = Field(default="1.0", min_length=1)

    # Replay intent (from ReplayRequest)
    replay_mode: ReplayMode = ReplayMode.STANDARD
    replay_level: ReplayLevel = ReplayLevel.PRESENTATION

    # Knowledge components (object identity from KnowledgeSnapshot)
    profile_snapshot: CandidateProfileSnapshot
    narrative: Narrative
    coaching_snapshot: CoachingSnapshot
    scoring_snapshot: Optional[ScoringSnapshot] = None

    # Question-level replay data
    question_results: tuple[ReplayQuestionRecord, ...] = Field(default_factory=tuple)

    # Derived navigation view
    timeline: ReplayTimeline

    # Session-level metadata
    session_metadata: ReplaySessionMetadata

    # Policy provenance
    policy_versions: PolicyVersions
    knowledge_epoch: str = Field(..., min_length=1)

    # Audit record
    manifest: ReplayManifest

    # Outcome
    is_successful: bool = True
    failure_reason: Optional[str] = None

    # KNOWLEDGE-level only
    observation_store_snapshot: Optional[object] = None

    # ------------------------------------------------------------------
    # Model validators V-RS-01 through V-RS-06
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _v_rs_01(self) -> "ReplaySession":
        """V-RS-01: is_successful=False requires non-empty failure_reason."""
        if not self.is_successful and not self.failure_reason:
            raise ValueError(
                "V-RS-01: is_successful=False requires a non-empty failure_reason."
            )
        return self

    @model_validator(mode="after")
    def _v_rs_02(self) -> "ReplaySession":
        """V-RS-02: is_successful=True requires failure_reason is None."""
        if self.is_successful and self.failure_reason is not None:
            raise ValueError(
                "V-RS-02: is_successful=True requires failure_reason to be None."
            )
        return self

    @model_validator(mode="after")
    def _v_rs_03(self) -> "ReplaySession":
        """V-RS-03: manifest.session_id must equal session_id."""
        if self.manifest.session_id != self.session_id:
            raise ValueError(
                f"V-RS-03: manifest.session_id ({self.manifest.session_id!r}) "
                f"must equal session_id ({self.session_id!r})."
            )
        return self

    @model_validator(mode="after")
    def _v_rs_04(self) -> "ReplaySession":
        """V-RS-04: manifest.candidate_identity_id must equal candidate_identity_id."""
        if self.manifest.candidate_identity_id != self.candidate_identity_id:
            raise ValueError(
                f"V-RS-04: manifest.candidate_identity_id ({self.manifest.candidate_identity_id!r}) "
                f"must equal candidate_identity_id ({self.candidate_identity_id!r})."
            )
        return self

    @model_validator(mode="after")
    def _v_rs_05(self) -> "ReplaySession":
        """V-RS-05: replay_level must not be REASONING."""
        if self.replay_level == ReplayLevel.REASONING:
            raise ValueError(
                "V-RS-05: replay_level REASONING is reserved and not available in V1.3."
            )
        return self

    @model_validator(mode="after")
    def _v_rs_06(self) -> "ReplaySession":
        """V-RS-06: observation_store_snapshot must be None for PRESENTATION level."""
        if (
            self.replay_level == ReplayLevel.PRESENTATION
            and self.observation_store_snapshot is not None
        ):
            raise ValueError(
                "V-RS-06: observation_store_snapshot must be None for PRESENTATION replay level."
            )
        return self

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_standard(self) -> bool:
        return self.replay_mode == ReplayMode.STANDARD

    @property
    def has_scoring(self) -> bool:
        return self.scoring_snapshot is not None

    @property
    def has_provenance(self) -> bool:
        return self.replay_level == ReplayLevel.KNOWLEDGE

    @property
    def question_count(self) -> int:
        return len(self.question_results)
