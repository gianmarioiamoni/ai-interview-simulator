# domain/contracts/longitudinal/longitudinal_profile.py
# EPIC-02 — P1/C1 — Immutable domain contracts (ADR-034, ADR-035, ADR-036)
# frozen=True, extra="forbid" on all models; tuple instead of list for all sequences.

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import CandidateProfileSnapshot
from domain.contracts.language.language_capability import LanguageCapability


class CrossSessionLanguageCapability(BaseModel):
    """Accumulated cross-session language capability for one language (EPIC-02 §1.6).

    Domain invariants:
    - LC-V-02: session_count_in_language >= 1.
    - LC-V-03: trend_direction == "insufficient_data" when session_count_in_language < 2.
    - LC-V-04: all scores in [0.0, 1.0].
    - LC-V-01/LC-V-05 are enforced at LongitudinalProfile level.
    """

    language_id: str = Field(..., min_length=1)
    session_count_in_language: int = Field(..., ge=1)
    total_questions_answered: int = Field(..., ge=0)
    mean_composite_score: float = Field(..., ge=0.0, le=1.0)
    mean_idiomatic_score: float = Field(..., ge=0.0, le=1.0)
    mean_type_error_rate: float = Field(..., ge=0.0, le=1.0)
    trend_direction: str = Field(default="stable")
    schema_version: str = Field(default="1.0", min_length=1)

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _validate_trend_direction_allowed(self) -> "CrossSessionLanguageCapability":
        allowed = {"improving", "declining", "stable", "insufficient_data"}
        if self.trend_direction not in allowed:
            raise ValueError(
                f"trend_direction must be one of {allowed}, got {self.trend_direction!r}"
            )
        return self

    @model_validator(mode="after")
    def _validate_lc_v03(self) -> "CrossSessionLanguageCapability":
        if self.session_count_in_language < 2 and self.trend_direction != "insufficient_data":
            raise ValueError(
                "LC-V-03: trend_direction must be 'insufficient_data' when "
                f"session_count_in_language < 2, got {self.trend_direction!r}"
            )
        return self


class LongitudinalSessionMetadata(BaseModel):
    """Session configuration captured at contribution time (EPIC-02 §1.5).

    Carries the scalar summary fields needed to produce SessionProgressEntry
    without re-reading SessionHistory.
    """

    role: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)
    interview_type: str = Field(..., min_length=1)
    question_count: int = Field(..., ge=0)
    session_language: str = Field(..., min_length=1)
    knowledge_epoch: str = Field(..., min_length=1)
    total_objectives: int = Field(default=0, ge=0)
    total_narrative_insights: int = Field(default=0, ge=0)
    language_capabilities: tuple[LanguageCapability, ...] = Field(default=())

    model_config = {"frozen": True, "extra": "forbid"}


class LongitudinalSessionEntry(BaseModel):
    """Per-session contribution record within a LongitudinalProfile (EPIC-02 §1.4).

    Each entry represents one closed session's contribution to the profile.
    Ordered by interview_index ascending within the parent LongitudinalProfile.
    """

    session_id: str = Field(..., min_length=1)
    interview_index: int = Field(..., ge=0)
    profile_snapshot: CandidateProfileSnapshot
    session_metadata: LongitudinalSessionMetadata
    contributed_at: datetime = Field(...)

    model_config = {"frozen": True, "extra": "forbid"}


class LongitudinalProfile(BaseModel):
    """Authoritative cross-session accumulation record for a candidate (EPIC-02 §1.1–§1.8).

    Persistent, candidate-scoped, immutable-at-instantiation.
    Produced exclusively by LongitudinalProfileBuilder (P1/C2).
    Written exclusively by longitudinal_update_node (P4/C1).

    Validation invariants LP-V-01 through LP-V-08 are enforced here.
    Cross-session invariants LC-V-01 and LC-V-05 are enforced here.
    """

    candidate_identity_id: str = Field(..., min_length=1)
    session_snapshots: tuple[LongitudinalSessionEntry, ...] = Field(...)
    session_count: int = Field(..., ge=0)
    language_capability_summary: tuple[CrossSessionLanguageCapability, ...] = Field(default=())
    knowledge_epoch: str = Field(default="1", min_length=1)
    schema_version: str = Field(default="1.0", min_length=1)
    created_at: datetime = Field(...)
    last_updated_at: datetime = Field(...)
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}

    @model_validator(mode="after")
    def _validate_lp_v01(self) -> "LongitudinalProfile":
        if self.session_count != len(self.session_snapshots):
            raise ValueError(
                f"LP-V-01: session_count ({self.session_count}) must equal "
                f"len(session_snapshots) ({len(self.session_snapshots)})"
            )
        return self

    @model_validator(mode="after")
    def _validate_lp_v02(self) -> "LongitudinalProfile":
        for entry in self.session_snapshots:
            if entry.profile_snapshot.candidate_identity_id != self.candidate_identity_id:
                raise ValueError(
                    "LP-V-02: all session_snapshots[*].profile_snapshot.candidate_identity_id "
                    f"must equal {self.candidate_identity_id!r}, found "
                    f"{entry.profile_snapshot.candidate_identity_id!r}"
                )
        return self

    @model_validator(mode="after")
    def _validate_lp_v03(self) -> "LongitudinalProfile":
        indices = [e.interview_index for e in self.session_snapshots]
        if len(indices) != len(set(indices)):
            raise ValueError(
                "LP-V-03: all interview_index values in session_snapshots must be unique"
            )
        return self

    @model_validator(mode="after")
    def _validate_lp_v04(self) -> "LongitudinalProfile":
        indices = [e.interview_index for e in self.session_snapshots]
        if indices != sorted(indices):
            raise ValueError(
                "LP-V-04: session_snapshots must be ordered by interview_index ascending"
            )
        return self

    @model_validator(mode="after")
    def _validate_lp_v05(self) -> "LongitudinalProfile":
        lang_ids = [c.language_id for c in self.language_capability_summary]
        if len(lang_ids) != len(set(lang_ids)):
            raise ValueError(
                "LP-V-05: all language_id values in language_capability_summary must be unique"
            )
        return self

    @model_validator(mode="after")
    def _validate_lp_v06(self) -> "LongitudinalProfile":
        if self.last_updated_at < self.created_at:
            raise ValueError(
                f"LP-V-06: last_updated_at ({self.last_updated_at}) must be >= "
                f"created_at ({self.created_at})"
            )
        return self

    @model_validator(mode="after")
    def _validate_lp_v07(self) -> "LongitudinalProfile":
        if not self.session_snapshots:
            return self
        highest_index = max(self.session_snapshots, key=lambda e: e.interview_index)
        expected_epoch = highest_index.session_metadata.knowledge_epoch
        if self.knowledge_epoch != expected_epoch:
            raise ValueError(
                f"LP-V-07: knowledge_epoch ({self.knowledge_epoch!r}) must equal the epoch "
                f"of the session with the highest interview_index ({expected_epoch!r})"
            )
        return self

    @model_validator(mode="after")
    def _validate_lp_v08(self) -> "LongitudinalProfile":
        if self.session_count == 0 and self.language_capability_summary:
            raise ValueError(
                "LP-V-08: language_capability_summary must be empty when session_count == 0"
            )
        return self
