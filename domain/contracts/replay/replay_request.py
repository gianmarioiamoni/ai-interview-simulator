# domain/contracts/replay/replay_request.py
# EPIC-03 Phase 2a — ReplayRequest: immutable input contract for replay_node.
# Frozen per ADR-037 Decision 4; field specification per EPIC-03-DOMAIN-CONTRACTS.md §6.

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, model_validator

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode


class ReplayRequest(BaseModel, frozen=True, extra="forbid"):
    """Immutable input contract for replay_node.

    Carries the caller's intent (which session to replay and at which depth).
    Contains no session-resident data — it is a pure input descriptor.

    ADR-037 Decision 4: ReplayRequest is the sole entry point into the Replay Graph.
    """

    session_id: str
    replay_mode: ReplayMode = ReplayMode.STANDARD
    replay_level: ReplayLevel = ReplayLevel.PRESENTATION
    operator_id: Optional[str] = None

    @model_validator(mode="after")
    def _validate_invariants(self) -> ReplayRequest:
        """Enforce V-RRQ-01 and V-RRQ-02 (EPIC-03-DOMAIN-CONTRACTS.md §6.3)."""
        # V-RRQ-01: ReplayLevel.REASONING is reserved and never activated in V1.3.
        if self.replay_level == ReplayLevel.REASONING:
            raise ValueError(
                "V-RRQ-01: ReplayLevel.REASONING is reserved and not available in V1.3."
            )

        # V-RRQ-02: MIGRATION and RECOVERY modes require a non-empty operator_id.
        if self.replay_mode in (ReplayMode.MIGRATION, ReplayMode.RECOVERY):
            if not self.operator_id:
                raise ValueError(
                    f"V-RRQ-02: replay_mode={self.replay_mode.value!r} requires a non-empty operator_id."
                )

        return self
