# app/graph/nodes/reasoner_node.py
"""ReasonerNode — thin graph node integrating the Interview Reasoner (ADR-029).

Responsibilities (orchestration only):
1. Build ReasonerInput via ReasoningContextBuilder.
2. Call ReasonerService.reason().
3. Update InterviewState with the new interview_memory and
   current_reasoning_decision.
4. Append a ReasoningEntry to reasoning_history.
5. Return the new state.

This node contains NO reasoning logic. All domain logic lives in:
  - ReasoningContextBuilder  (input construction)
  - ReasonerService          (orchestration + decision)
  - PatternDetectors         (detection)

Failure policy (ADR-029, advisory):
  Any exception is caught, logged with structured context, and the original
  state is returned with current_reasoning_decision = None.
  The interview NEVER stops due to a Reasoner failure.
"""

from __future__ import annotations

import time

from domain.contracts.interview_state import InterviewState
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.reasoning_history import ReasoningEntry, ReasoningHistory
from app.core.logger import get_logger
from services.interview_reasoner.pattern_detection.detectors.default_registry import (
    build_default_registry,
)
from services.interview_reasoner.evaluation_signal_writer import write_evaluation_signals
from services.interview_reasoner.reasoning_context_builder import ReasoningContextBuilder
from services.interview_reasoner.reasoner_service import ReasonerService

# MIG-02: Phase C imports — ObservationExtractor pipeline
from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.extraction.observation_extraction_context import (
    ObservationExtractionContext,
)
from domain.observation.runtime.in_memory_observation_store import InMemoryObservationStore
from domain.observation.runtime.default_observation_registry import build_default_observation_registry

logger = get_logger(__name__)

_registry = build_default_registry()
_service = ReasonerService(_registry)
_builder = ReasoningContextBuilder()

# MIG-02: shared frozen rule registry for ObservationExtractor (one per process).
_observation_rule_registry = build_default_observation_registry()


def reasoner_node(state: InterviewState) -> InterviewState:
    """Execute one reasoning cycle and return the updated InterviewState."""
    t0 = time.perf_counter()
    try:
        # P0-1 fix: inject EVALUATION-source signals from the current question's
        # QuestionEvaluation into EvidenceStore before reasoning, so that
        # EvaluationSignalDetector can bridge them (ADR-052).
        state = _inject_evaluation_signals(state)
        reasoner_input = _builder.build(state)
        decision, trace = _service.reason(reasoner_input)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        logger.info(
            "reasoner_node completed | "
            "q_idx=%d detectors=%d signals=%d patterns=%d elapsed_ms=%.1f skip=%s",
            state.current_question_index,
            len(trace.steps),
            len(decision.new_evidence),
            len(decision.reasoning_basis.detected_patterns),
            elapsed_ms,
            decision.skip,
        )

        updated_memory = _append_reasoning_entry(state, decision)

        # ------------------------------------------------------------------
        # Phase C — MIG-02: ObservationExtractor pipeline
        # Reads all EvidenceSignals for the current question from the updated
        # EvidenceStore and appends typed Observations to the session-scoped
        # ObservationStore.  Failures are non-fatal (interview continues).
        # ------------------------------------------------------------------
        updated_observation_store = _run_observation_extraction(
            state=state,
            updated_memory=updated_memory,
        )

        return state.model_copy(
            update={
                "interview_memory": updated_memory,
                "current_reasoning_decision": decision,
                "observation_store": updated_observation_store,
            }
        )

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        logger.warning(
            "reasoner_node failed — interview continues unaffected | "
            "q_idx=%d error=%s elapsed_ms=%.1f",
            state.current_question_index,
            type(exc).__name__,
            elapsed_ms,
        )
        return state.model_copy(update={"current_reasoning_decision": None})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _inject_evaluation_signals(state: InterviewState) -> InterviewState:
    """Return state with EVALUATION-source signals written to EvidenceStore.

    Reads the current question's QuestionEvaluation and writes evaluation
    signals via EvaluationSignalWriter (P0-1 fix, ADR-052).
    Returns state unchanged if no evaluation is available.
    """
    if state.interview_memory is None:
        return state
    if not state.asked_question_ids:
        return state
    last_qid = state.asked_question_ids[-1]
    result = state.results_by_question.get(last_qid)
    if result is None or result.evaluation is None:
        return state

    memory = state.interview_memory
    q_idx = state.current_question_index
    question_area = (
        state.last_question_context.question_area
        if state.last_question_context is not None
        else "unknown"
    )
    updated_store = write_evaluation_signals(
        evaluation=result.evaluation,
        question_index=q_idx,
        question_area=question_area,
        store=memory.evidence_store,
    )
    if updated_store is memory.evidence_store:
        return state

    updated_memory = memory.model_copy(update={"evidence_store": updated_store})
    return state.model_copy(update={"interview_memory": updated_memory})


# ---------------------------------------------------------------------------
# Phase C — MIG-02: ObservationExtractor helper
# ---------------------------------------------------------------------------

# MIG-02.5 hook: candidate_identity_id is required by KnowledgePipelineContext
# (MIG-03).  InterviewState does not yet expose a candidate_identity_id field
# (pending MIG-03 or a future InterviewState evolution).  Until that field is
# available, the session interview_id is used as a stable surrogate.
# When MIG-03 wires KnowledgePipeline, replace _resolve_candidate_identity_id()
# with a direct read of state.candidate_identity_id (once added to InterviewState).
def _resolve_candidate_identity_id(state: InterviewState) -> str:
    """Return the candidate identity id for pipeline context construction.

    Surrogate: uses interview_id until InterviewState exposes a dedicated field
    (MIG-03 hook — do not remove until that migration is complete).
    """
    return state.interview_id


def _run_observation_extraction(
    state: InterviewState,
    updated_memory: InterviewMemory,
) -> "InMemoryObservationStore | None":
    """Extract Observations from the current cycle's EvidenceSignals.

    Retrieves or creates the session-scoped ObservationStore, builds an
    ObservationExtractor, and runs one extraction cycle for the signals
    belonging to the current question index.

    Returns the updated ObservationStore, or the prior store (unchanged) if no
    signals are available for the current question.  Never raises.
    """
    try:
        q_idx = state.current_question_index
        store = state.observation_store

        # Initialise store on first cycle (session start).
        if store is None:
            store = InMemoryObservationStore(session_id=state.interview_id)

        # Collect signals for the current question index only.
        # ObservationExtractionContext requires all signals to share the same
        # question_index (ADR-016 §3 context validator).
        current_signals = tuple(
            sig
            for sig in updated_memory.evidence_store.signals
            if sig.question_index == q_idx
        )

        if not current_signals:
            logger.debug(
                "observation_extraction skipped — no signals for q_idx=%d", q_idx
            )
            return store

        extractor = ObservationExtractor(
            registry=_observation_rule_registry,
            store=store,
        )

        context = ObservationExtractionContext(
            signals=current_signals,
            question_index=q_idx,
            session_id=state.interview_id,
        )

        result = extractor.extract(context)

        logger.debug(
            "observation_extraction completed | "
            "q_idx=%d signals=%d observations=%d store_count=%d",
            q_idx,
            len(current_signals),
            len(result.observations) if result is not None else 0,
            store.count(),
        )

        return store

    except Exception as exc:
        logger.warning(
            "observation_extraction failed — store unchanged | "
            "q_idx=%d error=%s",
            state.current_question_index,
            type(exc).__name__,
        )
        return state.observation_store


def _append_reasoning_entry(
    state: InterviewState,
    decision,
) -> InterviewMemory:
    """Return updated InterviewMemory with a new ReasoningEntry appended."""
    memory = state.interview_memory
    basis = decision.reasoning_basis

    entry = ReasoningEntry(
        question_index=state.current_question_index,
        dominant_dimension=basis.dominant_dimension,
        detected_patterns=basis.detected_patterns,
        follow_up_recommended=(
            decision.follow_up_recommendation is not None
            and decision.follow_up_recommendation.recommended
        ),
        navigation_recommended=decision.navigation_recommendation is not None,
        reasoning_confidence=basis.reasoning_confidence.reasoning_confidence,
    )

    existing_entries = list(memory.reasoning_history.entries)
    # Cap at _MAX_ENTRIES (20) — drop oldest when full
    from domain.contracts.reasoning.reasoning_history import _MAX_ENTRIES
    new_entries = (existing_entries + [entry])[-_MAX_ENTRIES:]
    new_history = ReasoningHistory(entries=new_entries)

    # Propagate new_evidence into evidence_store (immutable append)
    store = memory.evidence_store
    for sig in decision.new_evidence:
        try:
            store = store.append(sig)
        except ValueError:
            logger.warning(
                "evidence_store_capacity_exceeded in reasoner_node | "
                "q_idx=%d store_size=%d",
                state.current_question_index,
                len(store.signals),
            )
            break

    return InterviewMemory(
        candidate_profile=decision.candidate_profile_snapshot,
        evidence_store=store,
        coverage_state=memory.coverage_state,
        reasoning_history=new_history,
        session_metrics=memory.session_metrics,
        schema_version=memory.schema_version,
    )
