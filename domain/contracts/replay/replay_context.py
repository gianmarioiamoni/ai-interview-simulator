# domain/contracts/replay/replay_context.py
# ADR-026 §B6 — ReplayContext (runtime input to a replay operation)

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode


class ReplayContext(BaseModel):
    """Immutable input contract for a single replay operation (ADR-026 §B6).

    Encapsulates all inputs needed for the Replay subsystem to produce a
    ReplayResult without invoking any live pipeline component.

    Invariants:
    - RC-CTX-01: session_id and candidate_identity_id must be non-empty.
    - RC-CTX-02: knowledge_snapshot is always the first source queried (SP-01).
    - RC-CTX-03: replay_mode MIGRATION requires operator_id present (MP-06).
    - RC-CTX-04: replay_level REASONING is reserved — never used in V1.2.
    """

    session_id: str = Field(..., min_length=1, description="Session being replayed")
    candidate_identity_id: str = Field(..., min_length=1, description="Owning candidate")
    knowledge_snapshot: KnowledgeSnapshot = Field(
        ...,
        description="Primary source: the immutable closure artifact (ADR-022, ADR-026 SP-01)"
    )
    replay_mode: ReplayMode = Field(
        default=ReplayMode.STANDARD,
        description="Operation mode: standard, migration, or recovery (ADR-026 §D)"
    )
    replay_level: ReplayLevel = Field(
        default=ReplayLevel.PRESENTATION,
        description="Depth level requested by the consumer (ADR-026 §B3)"
    )
    operator_id: str | None = Field(
        default=None,
        description="Required when replay_mode is MIGRATION or RECOVERY (MP-06)"
    )
    replay_engine_version: str = Field(
        default="1.0",
        min_length=1,
        description="Version of the Replay subsystem processing this operation"
    )

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def _validate_migration_requires_operator(self) -> "ReplayContext":
        if self.replay_mode in (ReplayMode.MIGRATION, ReplayMode.RECOVERY):
            if not self.operator_id:
                raise ValueError(
                    f"RC-CTX-03: replay_mode={self.replay_mode.value} requires operator_id (MP-06)."
                )
        return self

    @model_validator(mode="after")
    def _validate_reasoning_level_reserved(self) -> "ReplayContext":
        if self.replay_level == ReplayLevel.REASONING:
            raise ValueError(
                "RC-CTX-04: ReplayLevel.REASONING is reserved for V1.3+. "
                "Use PRESENTATION or KNOWLEDGE."
            )
        return self

    @model_validator(mode="after")
    def _validate_session_id_consistency(self) -> "ReplayContext":
        if self.knowledge_snapshot.session_id != self.session_id:
            raise ValueError(
                f"RC-CTX-01: ReplayContext.session_id='{self.session_id}' "
                f"does not match knowledge_snapshot.session_id="
                f"'{self.knowledge_snapshot.session_id}'."
            )
        return self

    @model_validator(mode="after")
    def _validate_candidate_id_consistency(self) -> "ReplayContext":
        if self.knowledge_snapshot.candidate_identity_id != self.candidate_identity_id:
            raise ValueError(
                f"RC-CTX-01: ReplayContext.candidate_identity_id='{self.candidate_identity_id}' "
                f"does not match knowledge_snapshot.candidate_identity_id="
                f"'{self.knowledge_snapshot.candidate_identity_id}'."
            )
        return self
