# tests/performance/profiling_reasoner_kp.py
# EPIC-V13-09 C5 — reasoner + KP stage profiling under stubbed written cycle
# (AR-11, AR-12, PROF-01/02/04/05). Harness-only; no topology/state schema changes.

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any, TypeVar
from unittest.mock import MagicMock

from app.graph import interview_graph as interview_graph_module
from app.graph.interview_graph import build_interview_graph
from app.graph.nodes import reasoner_node as reasoner_node_module
from domain.contracts.interview_state import InterviewState
from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
from services.knowledge_pipeline.knowledge_pipeline_result import KnowledgePipelineResult
from tests.factories.interview_state_factory import build_written_question_state
from tests.performance.helpers import measure_wall_clock_ms
from tests.performance.stub_llm import DeterministicStubLLM

T = TypeVar("T")

# Shallow-band score so EvaluationSignalWriter emits signals (score < 80).
# Strong-pass stubs (score ≥ 80) skip EVALUATION signals → KP has no work.
_PROFILING_WRITTEN_EVALUATION_JSON = json.dumps(
    {
        "score": 60.0,
        "feedback": "Partial written answer; depth is limited.",
        "strengths": ["Addresses the prompt"],
        "weaknesses": ["Shallow coverage"],
        "clarification_needed": False,
        "follow_up_question": None,
    }
)


@dataclass(frozen=True)
class KpStageTimings:
    """Per-question KnowledgePipeline timings (PROF-02 / AR-12)."""

    total_ms: float
    feature_engine_ms: float
    profile_build_ms: float
    question_index: int
    feature_count: int
    is_successful: bool


@dataclass(frozen=True)
class ReasonerKpProfileEvidence:
    """Profiling evidence for reasoner_node whole + stages (PROF-01/05)."""

    whole_node_ms: float
    detectors_ms: float
    observation_extract_ms: float
    knowledge_pipeline_ms: float
    kp_stages: KpStageTimings | None
    question_index: int
    written_cycle_ms: float
    observation_count: int
    profile_built: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def build_profiling_stub_llm() -> DeterministicStubLLM:
    """Deterministic stub that exercises EVALUATION → observation → KP path."""
    return DeterministicStubLLM(scripted_responses=[_PROFILING_WRITTEN_EVALUATION_JSON])


def prepare_written_state_for_reasoner_profiling() -> InterviewState:
    """
    Harness wiring (AR-22): seed fields required for eval-signal bridge + KP.

    Does not alter InterviewState schema — only values on a test fixture.
    """
    state = build_written_question_state()
    qid = state.questions[0].id
    return state.model_copy(
        update={
            "asked_question_ids": [qid],
            "candidate_identity_id": "epic09-c5-candidate",
        }
    )


def _timed_call(label: str, bucket: dict[str, float], fn: Callable[[], T]) -> T:
    result, elapsed_ms = measure_wall_clock_ms(fn)
    bucket[label] = elapsed_ms
    return result


def _install_reasoner_stage_timers(
    stage_ms: dict[str, float],
    kp_results: list[KnowledgePipelineResult],
) -> Callable[[], None]:
    """Wrap reasoner internals; return restore callable (PROF-04 harness timers)."""
    original_reason = reasoner_node_module._service.reason
    original_obs = reasoner_node_module._run_observation_extraction
    original_kp = reasoner_node_module._run_knowledge_pipeline
    original_node = reasoner_node_module.reasoner_node
    original_pipeline_run = KnowledgePipeline.run

    def timed_reason(reasoner_input: object) -> object:
        return _timed_call(
            "detectors",
            stage_ms,
            lambda: original_reason(reasoner_input),
        )

    def timed_obs(*args: object, **kwargs: object) -> object:
        return _timed_call(
            "observation_extract",
            stage_ms,
            lambda: original_obs(*args, **kwargs),
        )

    def timed_kp(*args: object, **kwargs: object) -> object:
        return _timed_call(
            "knowledge_pipeline",
            stage_ms,
            lambda: original_kp(*args, **kwargs),
        )

    def timed_node(state: InterviewState) -> InterviewState:
        return _timed_call(
            "whole_node",
            stage_ms,
            lambda: original_node(state),
        )

    def timed_pipeline_run(
        self: KnowledgePipeline,
        context: object,
    ) -> KnowledgePipelineResult:
        result = original_pipeline_run(self, context)
        kp_results.append(result)
        return result

    # interview_graph binds reasoner_node at import time; patch both so
    # build_interview_graph registers the timed wrapper (whole-node PROF-01).
    original_graph_node = interview_graph_module.reasoner_node

    reasoner_node_module._service.reason = timed_reason  # type: ignore[method-assign]
    reasoner_node_module._run_observation_extraction = timed_obs  # type: ignore[assignment]
    reasoner_node_module._run_knowledge_pipeline = timed_kp  # type: ignore[assignment]
    reasoner_node_module.reasoner_node = timed_node  # type: ignore[assignment]
    interview_graph_module.reasoner_node = timed_node  # type: ignore[assignment]
    KnowledgePipeline.run = timed_pipeline_run  # type: ignore[method-assign]

    def restore() -> None:
        reasoner_node_module._service.reason = original_reason  # type: ignore[method-assign]
        reasoner_node_module._run_observation_extraction = original_obs  # type: ignore[assignment]
        reasoner_node_module._run_knowledge_pipeline = original_kp  # type: ignore[assignment]
        reasoner_node_module.reasoner_node = original_node  # type: ignore[assignment]
        interview_graph_module.reasoner_node = original_graph_node  # type: ignore[assignment]
        KnowledgePipeline.run = original_pipeline_run  # type: ignore[method-assign]

    return restore


def _kp_stage_timings(
    kp_results: list[KnowledgePipelineResult],
) -> KpStageTimings | None:
    if not kp_results:
        return None
    result = kp_results[-1]
    metrics = result.diagnostics.metrics
    return KpStageTimings(
        total_ms=metrics.total_duration_ms,
        feature_engine_ms=metrics.feature_engine_duration_ms,
        profile_build_ms=metrics.profile_build_duration_ms,
        question_index=result.question_index,
        feature_count=result.feature_count,
        is_successful=result.is_successful,
    )


def _coerce_state(result: object) -> InterviewState:
    if isinstance(result, InterviewState):
        return result
    if isinstance(result, dict):
        return InterviewState.model_validate(result)
    raise TypeError(f"Unexpected graph.invoke result type: {type(result)!r}")


def profile_reasoner_kp_under_written_cycle(
    *,
    llm: DeterministicStubLLM | None = None,
) -> tuple[ReasonerKpProfileEvidence, InterviewState, DeterministicStubLLM]:
    """
    Profile reasoner_node whole + stages during one stubbed written cycle.

    Measurement ownership: harness timers around existing compute surfaces
    (PROF-04). Path: written → feedback → reasoner → decision (AR-01 / PROF-05).
    """
    stub = llm if llm is not None else build_profiling_stub_llm()
    stage_ms: dict[str, float] = {}
    kp_results: list[KnowledgePipelineResult] = []
    restore = _install_reasoner_stage_timers(stage_ms, kp_results)

    try:
        graph = build_interview_graph(llm=stub, hint_service=MagicMock())
        state = prepare_written_state_for_reasoner_profiling()
        result, written_cycle_ms = measure_wall_clock_ms(lambda: graph.invoke(state))
        final_state = _coerce_state(result)
    finally:
        restore()

    required = ("whole_node", "detectors", "observation_extract", "knowledge_pipeline")
    missing = [name for name in required if name not in stage_ms]
    if missing:
        raise RuntimeError(
            f"Reasoner stage timers missing after written cycle: {missing}"
        )

    obs_store = final_state.observation_store
    observation_count = obs_store.count() if obs_store is not None else 0
    evidence = ReasonerKpProfileEvidence(
        whole_node_ms=stage_ms["whole_node"],
        detectors_ms=stage_ms["detectors"],
        observation_extract_ms=stage_ms["observation_extract"],
        knowledge_pipeline_ms=stage_ms["knowledge_pipeline"],
        kp_stages=_kp_stage_timings(kp_results),
        question_index=final_state.current_question_index,
        written_cycle_ms=written_cycle_ms,
        observation_count=observation_count,
        profile_built=final_state.candidate_profile_v2 is not None,
    )
    return evidence, final_state, stub
