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
from services.interview_reasoner.reasoning_context_builder import ReasoningContextBuilder
from services.interview_reasoner.reasoner_service import ReasonerService

logger = get_logger(__name__)

_registry = build_default_registry()
_service = ReasonerService(_registry)
_builder = ReasoningContextBuilder()


def reasoner_node(state: InterviewState) -> InterviewState:
    """Execute one reasoning cycle and return the updated InterviewState."""
    t0 = time.perf_counter()
    try:
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

        return state.model_copy(
            update={
                "interview_memory": updated_memory,
                "current_reasoning_decision": decision,
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
            break  # capacity reached

    return InterviewMemory(
        candidate_profile=decision.candidate_profile_snapshot,
        evidence_store=store,
        coverage_state=memory.coverage_state,
        reasoning_history=new_history,
        session_metrics=memory.session_metrics,
        schema_version=memory.schema_version,
    )
