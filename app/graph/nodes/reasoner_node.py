# app/graph/nodes/reasoner_node.py
"""ReasonerNode — thin graph node integrating the Interview Reasoner (ADR-029).

Responsibilities (orchestration only):
1. Build ReasonerInput via ReasoningContextBuilder.
2. Call ReasonerService.reason().
3. Update InterviewState with the new interview_memory (and observation /
   profile pipeline outputs).
4. Append a ReasoningEntry to reasoning_history.
5. Return the new state.

This node contains NO reasoning logic. All domain logic lives in:
  - ReasoningContextBuilder  (input construction)
  - ReasonerService          (orchestration + decision)
  - PatternDetectors         (detection)

Failure policy (ADR-029, advisory):
  Any exception is caught, logged with structured context, and the original
  state is returned unchanged.
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

from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.extraction.observation_extraction_context import (
    ObservationExtractionContext,
)
from domain.observation.runtime.in_memory_observation_store import InMemoryObservationStore
from domain.observation.runtime.default_observation_registry import build_default_observation_registry
from services.knowledge_pipeline.default_knowledge_pipeline_factory import (
    build_default_knowledge_pipeline,
)
from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext

logger = get_logger(__name__)

_registry = build_default_registry()
_service = ReasonerService(_registry)
_builder = ReasoningContextBuilder()

# Shared frozen rule registry for ObservationExtractor (one per process).
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
        decision, trace, memory_with_metrics = _service.reason(reasoner_input)
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

        updated_memory = _append_reasoning_entry(state, decision, memory_with_metrics)

        # ------------------------------------------------------------------
        # ObservationExtractor pipeline
        # Reads all EvidenceSignals for the current question from the updated
        # EvidenceStore and appends typed Observations to the session-scoped
        # ObservationStore.  Failures are non-fatal (interview continues).
        # ------------------------------------------------------------------
        updated_observation_store = _run_observation_extraction(
            state=state,
            updated_memory=updated_memory,
        )

        # ------------------------------------------------------------------
        # KnowledgePipeline: FeatureEngine → CandidateProfileBuilder → CandidateProfile
        # Uses the already-populated ObservationStore (extraction skipped).
        # Failures are non-fatal.
        # ------------------------------------------------------------------
        updated_candidate_profile_v2 = _run_knowledge_pipeline(
            state=state,
            updated_observation_store=updated_observation_store,
        )

        return state.model_copy(
            update={
                "interview_memory": updated_memory,
                "observation_store": updated_observation_store,
                "candidate_profile_v2": updated_candidate_profile_v2,
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
        return state


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
# ObservationExtractor helper
# ---------------------------------------------------------------------------

def _resolve_candidate_identity_id(state: InterviewState) -> str:
    """Return the candidate identity id for pipeline context construction.

    Reads state.candidate_identity_id (set by create_initial / create_empty).
    Raises RuntimeError for states where the field was never populated — this
    should never occur in production (all factory paths populate it).
    """
    if state.candidate_identity_id is None:
        raise RuntimeError(
            "candidate_identity_id is None — state was not created via "
            "InterviewState.create_initial or create_empty"
        )
    return state.candidate_identity_id


# ---------------------------------------------------------------------------
# KnowledgePipeline helper
# ---------------------------------------------------------------------------

def _run_knowledge_pipeline(
    state: InterviewState,
    updated_observation_store,
) -> object:
    """Run KnowledgePipeline to produce CandidateProfile.

    Uses the session-scoped ObservationStore (already populated by ObservationExtractor).
    Extraction is skipped (skip_extraction_if_store_populated=True).
    Returns the new CandidateProfile, or the prior candidate_profile_v2
    (unchanged) if the pipeline fails.  Never raises.
    """
    try:
        if updated_observation_store is None or updated_observation_store.count() == 0:
            logger.debug(
                "knowledge_pipeline skipped — no observations in store | q_idx=%d",
                state.current_question_index,
            )
            return state.candidate_profile_v2

        pipeline = build_default_knowledge_pipeline(store=updated_observation_store)

        ctx = KnowledgePipelineContext(
            session_id=state.interview_id,
            candidate_identity_id=_resolve_candidate_identity_id(state),
            question_index=state.current_question_index,
            signals=(),
            prior_profile=state.candidate_profile_v2,
        )

        result = pipeline.run(ctx)

        if result.is_successful and result.profile is not None:
            logger.debug(
                "knowledge_pipeline completed | "
                "q_idx=%d features=%d profile_built=True",
                state.current_question_index,
                result.feature_count,
            )
            return result.profile

        logger.debug(
            "knowledge_pipeline produced no profile | "
            "q_idx=%d reason=%s",
            state.current_question_index,
            result.failure_reason,
        )
        return state.candidate_profile_v2

    except Exception as exc:
        logger.warning(
            "knowledge_pipeline failed — candidate_profile_v2 unchanged | "
            "q_idx=%d error=%s",
            state.current_question_index,
            type(exc).__name__,
        )
        return state.candidate_profile_v2


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
    memory_with_metrics: InterviewMemory,
) -> InterviewMemory:
    """Return updated InterviewMemory with a new ReasoningEntry appended.

    Uses memory_with_metrics (returned by ReasonerService.reason) so that
    session_metrics updated by _propagate_evidence are preserved (ADR-038).
    """
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

    # Propagate new_evidence into evidence_store (immutable append).
    # Use memory_with_metrics as base so session_metrics are already updated.
    store = memory_with_metrics.evidence_store
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
        evidence_store=store,
        coverage_state=memory_with_metrics.coverage_state,
        reasoning_history=new_history,
        session_metrics=memory_with_metrics.session_metrics,
        schema_version=memory_with_metrics.schema_version,
    )
