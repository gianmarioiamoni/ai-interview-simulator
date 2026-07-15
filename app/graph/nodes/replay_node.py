# app/graph/nodes/replay_node.py
# EPIC-03 Phase 4a — replay_node: sole LangGraph node of the Replay Graph.
# Responsibilities per EPIC-03-IMPLEMENTATION-PLAN.md §2 Phase 4a:
#   - Load SessionHistory from persistence (read-only, via injected loader)
#   - Instantiate ReplayFeatureEngine
#   - Call ReplaySessionBuilder
#   - Produce ReplaySession (V1.3) — sole writer
#   - Handle non-fatal failures via ReplaySessionBuilder.as_failed()
#   - Emit structured logs
#
# Architecture invariants:
#   I-R01: replay_node is the sole writer of ReplaySession.
#   I-R07: zero persistence writes (read-only).
#   I-11:  zero LLM calls.
#   I-R03: no import of live session node or InterviewState.

from __future__ import annotations

from typing import Callable, Optional

from domain.contracts.replay.replay_feature_engine import ReplayFeatureEngine
from domain.contracts.replay.replay_graph_state import ReplayGraphState
from domain.contracts.replay.replay_session_builder import ReplaySessionBuilder
from domain.contracts.replay.replay_session_v13 import ReplaySessionV13
from domain.contracts.session_history.session_history import SessionHistory
from app.core.logger import get_logger

logger = get_logger(__name__)

# Type alias for the session loader callable (read-only persistence access).
SessionLoader = Callable[[str], Optional[SessionHistory]]


def replay_node(
    state: ReplayGraphState,
    *,
    session_loader: SessionLoader,
) -> ReplayGraphState:
    """LangGraph node — sole writer of ReplaySession.

    Loads SessionHistory, instantiates ReplayFeatureEngine, delegates construction
    to ReplaySessionBuilder, and returns an updated ReplayGraphState with result set.

    Non-fatal: any failure produces ReplaySession(is_successful=False) via as_failed().
    No LLM calls. No persistence writes. No live session imports (I-11, I-R07, I-R03).

    Args:
        state: ReplayGraphState carrying the ReplayRequest.
        session_loader: Read-only callable(session_id) -> Optional[SessionHistory].

    Returns:
        Updated ReplayGraphState with result populated.
    """
    request = state["request"]
    session_id = request.session_id
    candidate_identity_id: str = ""

    try:
        logger.info(
            "replay_node: loading session | session_id=%s replay_mode=%s replay_level=%s",
            session_id,
            request.replay_mode.value,
            request.replay_level.value,
        )

        session_history: Optional[SessionHistory] = session_loader(session_id)

        if session_history is None:
            logger.warning(
                "replay_node: SessionHistory not found — producing failed ReplaySession | "
                "session_id=%s",
                session_id,
            )
            result = ReplaySessionBuilder.as_failed(
                session_id=session_id,
                candidate_identity_id=session_id,
                failure_reason=f"SessionHistory not found for session_id={session_id!r}.",
                replay_mode=request.replay_mode,
                replay_level=request.replay_level,
            )
            return {**state, "result": result}

        candidate_identity_id = session_history.candidate_identity_id

        # Instantiate ReplayFeatureEngine (read-only adapter, no computation).
        _feature_engine = ReplayFeatureEngine(
            profile_snapshot=session_history.knowledge_snapshot.profile_snapshot
        )

        # Delegate construction to ReplaySessionBuilder (sole construction path).
        result: ReplaySessionV13 = (
            ReplaySessionBuilder()
            .with_session_history(session_history)
            .with_replay_mode(request.replay_mode)
            .with_replay_level(request.replay_level)
            .with_operator_id(request.operator_id)
            .build()
        )

        logger.info(
            "replay_node: ReplaySession produced | session_id=%s candidate_id=%s "
            "question_count=%d is_successful=%s",
            session_id,
            candidate_identity_id,
            result.question_count,
            result.is_successful,
        )

        return {**state, "result": result}

    except Exception as exc:
        logger.warning(
            "replay_node: exception during reconstruction — producing failed ReplaySession | "
            "session_id=%s candidate_id=%s error_type=%s error=%s",
            session_id,
            candidate_identity_id or session_id,
            type(exc).__name__,
            str(exc),
        )
        fallback_candidate_id = candidate_identity_id or session_id
        result = ReplaySessionBuilder.as_failed(
            session_id=session_id,
            candidate_identity_id=fallback_candidate_id,
            failure_reason=f"{type(exc).__name__}: {exc}",
            replay_mode=request.replay_mode,
            replay_level=request.replay_level,
        )
        return {**state, "result": result}
