# domain/contracts/replay/replay_graph_state.py
# EPIC-03 Phase 2f — ReplayGraphState: LangGraph state container for the Replay Graph.
# Specification per EPIC-03-DOMAIN-CONTRACTS.md §7.

from __future__ import annotations

from typing import Optional

from typing_extensions import TypedDict

from domain.contracts.replay.replay_request import ReplayRequest
from domain.contracts.replay.replay_session_v13 import ReplaySessionV13


class ReplayGraphState(TypedDict, total=False):
    """LangGraph state container for the Replay Graph.

    Does NOT extend the live session state container (I-R03 isolation invariant).
    Contains no live session data.

    request is set at graph entry and never overwritten.
    result is None until replay_node completes; written exactly once.

    Not frozen — LangGraph state containers are mutable by design (§7.2).
    """

    request: ReplayRequest
    result: Optional[ReplaySessionV13]
