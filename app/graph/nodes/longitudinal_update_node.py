# app/graph/nodes/longitudinal_update_node.py
# EPIC-02 — P4/C1 — LongitudinalUpdateNode (PAT-06: LangGraph sole orchestrator)
#
# Governing: ADR-034 Decision 1 (sole writer), Decision 6 (non-fatal failure semantics),
#            EPIC-02-IMPLEMENTATION-PLAN.md §10, EPIC-02-DATA-MODEL.md §4.
#
# Responsibilities:
#   1. Guard: return immediately if state.session_history is None (no session to accumulate).
#   2. Idempotency guard: return immediately if this interview_index is already present
#      in the prior profile (LP-07).
#   3. Load prior LongitudinalProfile from repository (may be None for first session).
#   4. Call LongitudinalProfileBuilder to produce an updated profile.
#   5. Write the updated profile via repository.save() (sole caller of save()).
#   6. Non-fatal failure: any exception is caught, WARNING is logged, state returned unchanged.
#
# Sole writer of LongitudinalProfile: this node only (ADR-034 Decision 1, LP-01).
# No LLM calls. No FeatureEngine. No NarrativeGenerator. No KnowledgePipeline (LP-03).
# Not in LongitudinalProfile. Not in InterviewState as a field.
#
# SR-01 note (Appendix A): InterviewState carries no language_capabilities field in V1.3.
# LanguageCapability is transient and not preserved in SessionHistory (OI-03 resolved).
# The node passes language_capabilities=() in V1.3 — architecturally correct per the
# frozen data model (DATA-MODEL.md §6.3 reconstruction gap — accepted for V1.3).
# FIC-03 is NOT triggered: no InterviewState field addition is made in this commit.

from __future__ import annotations

from datetime import datetime, timezone

from domain.contracts.interview_state import InterviewState
from domain.contracts.language.language_capability import LanguageCapability
from domain.contracts.longitudinal.longitudinal_profile_builder import (
    LongitudinalProfileBuilder,
)
from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)
from app.core.logger import get_logger

logger = get_logger(__name__)


class LongitudinalUpdateNode:
    """Graph node that accumulates session history into a LongitudinalProfile.

    Injected with a LongitudinalProfileRepository at construction time.
    Callable as a LangGraph node: receives InterviewState, returns InterviewState.

    Non-fatal: any exception during profile construction or persistence is caught,
    a WARNING is logged, and the state is returned unchanged. The session close
    sequence is unaffected by any longitudinal update failure.

    Sole writer of LongitudinalProfile (ADR-034 Decision 1, LP-01).
    """

    def __init__(self, repository: LongitudinalProfileRepository) -> None:
        self._repository = repository

    def __call__(self, state: InterviewState) -> InterviewState:
        """Accumulate the closed session into the LongitudinalProfile.

        Idempotent: re-execution for the same interview_index is a no-op (LP-07).
        Non-fatal: persistence failures log WARNING and return state unchanged.
        """
        if state.session_history is None:
            logger.debug(
                "longitudinal_update_node: session_history not set — skipping"
            )
            return state

        session_history = state.session_history
        candidate_id = session_history.candidate_identity_id
        interview_index = session_history.interview_index

        try:
            prior_profile = self._repository.get(candidate_id)

            # LP-07: idempotency guard — if interview_index already in prior profile,
            # the builder will return the prior unchanged, so the save is a no-op too.
            # Check here explicitly to short-circuit the builder call.
            if prior_profile is not None:
                existing_indices = {
                    e.interview_index for e in prior_profile.session_snapshots
                }
                if interview_index in existing_indices:
                    logger.debug(
                        "longitudinal_update_node: interview_index=%d already present "
                        "in profile for candidate=%s — skipping (idempotency LP-07)",
                        interview_index,
                        candidate_id,
                    )
                    return state

            # V1.3: language_capabilities are transient and not available on InterviewState
            # (OI-03 resolved — DATA-MODEL.md §6.3). Empty tuple is correct for V1.3.
            language_capabilities: tuple[LanguageCapability, ...] = ()

            updated_profile = (
                LongitudinalProfileBuilder()
                .with_prior_profile(prior_profile)
                .with_session_history(session_history)
                .with_language_capabilities(language_capabilities)
                .with_current_timestamp(datetime.now(tz=timezone.utc))
                .build()
            )

            self._repository.save(updated_profile)

            logger.info(
                "longitudinal_update_node completed | candidate=%s session=%s "
                "interview_index=%d session_count=%d",
                candidate_id,
                session_history.session_id,
                interview_index,
                updated_profile.session_count,
            )

        except Exception as exc:
            logger.warning(
                "longitudinal_update_node failed — profile not updated | "
                "candidate=%s interview_index=%s session=%s timestamp=%s error=%s",
                candidate_id,
                interview_index,
                session_history.session_id,
                datetime.now(tz=timezone.utc).isoformat(),
                type(exc).__name__,
            )

        return state
