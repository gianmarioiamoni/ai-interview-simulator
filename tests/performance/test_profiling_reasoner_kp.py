# tests/performance/test_profiling_reasoner_kp.py
# EPIC-V13-09 C5 — PROF-01/02/05: reasoner + KP stage timings under stubbed written cycle.

from __future__ import annotations

from app.graph import interview_graph as interview_graph_module
from app.graph.nodes import reasoner_node as reasoner_node_module
from services.knowledge_pipeline.knowledge_pipeline import KnowledgePipeline
from tests.performance.profiling_reasoner_kp import (
    ReasonerKpProfileEvidence,
    build_profiling_stub_llm,
    prepare_written_state_for_reasoner_profiling,
    profile_reasoner_kp_under_written_cycle,
)


def test_reasoner_whole_and_stages_are_profiled() -> None:
    """PROF-01 / AR-11: whole-node + detectors + observation extract + KP timings."""
    evidence, state, stub = profile_reasoner_kp_under_written_cycle()

    assert isinstance(evidence, ReasonerKpProfileEvidence)
    assert evidence.whole_node_ms >= 0.0
    assert evidence.detectors_ms >= 0.0
    assert evidence.observation_extract_ms >= 0.0
    assert evidence.knowledge_pipeline_ms >= 0.0
    assert evidence.written_cycle_ms >= evidence.whole_node_ms
    assert stub.invoke_call_count >= 1
    assert state.current_reasoning_decision is not None


def test_knowledge_pipeline_is_per_question_cost() -> None:
    """PROF-02 / AR-12: KP profiled as per-question cost inside reasoner."""
    evidence, state, _ = profile_reasoner_kp_under_written_cycle()

    assert evidence.kp_stages is not None
    assert evidence.kp_stages.question_index == evidence.question_index
    assert evidence.kp_stages.total_ms >= 0.0
    assert evidence.kp_stages.feature_engine_ms >= 0.0
    assert evidence.kp_stages.profile_build_ms >= 0.0
    assert evidence.kp_stages.is_successful is True
    assert evidence.observation_count > 0
    assert evidence.profile_built is True
    assert state.candidate_profile_v2 is not None


def test_written_cycle_reasoner_contribution_evidence() -> None:
    """PROF-05: highest-latency path evidence includes written-cycle reasoner contribution."""
    evidence, _, stub = profile_reasoner_kp_under_written_cycle(
        llm=build_profiling_stub_llm()
    )

    payload = evidence.to_dict()
    assert "whole_node_ms" in payload
    assert "detectors_ms" in payload
    assert "observation_extract_ms" in payload
    assert "knowledge_pipeline_ms" in payload
    assert "written_cycle_ms" in payload
    assert payload["kp_stages"] is not None
    assert stub.invoke_call_count == 1
    # Reasoner contribution is a measurable slice of the written cycle.
    assert 0.0 <= evidence.whole_node_ms <= evidence.written_cycle_ms


def test_profiling_harness_restores_reasoner_wrappers() -> None:
    """Harness timers must not leave production callables patched."""
    original_node = reasoner_node_module.reasoner_node
    original_graph_node = interview_graph_module.reasoner_node
    original_obs = reasoner_node_module._run_observation_extraction
    original_kp = reasoner_node_module._run_knowledge_pipeline
    original_reason = reasoner_node_module._service.reason
    original_pipeline_run = KnowledgePipeline.run

    profile_reasoner_kp_under_written_cycle()

    assert reasoner_node_module.reasoner_node is original_node
    assert interview_graph_module.reasoner_node is original_graph_node
    assert reasoner_node_module._run_observation_extraction is original_obs
    assert reasoner_node_module._run_knowledge_pipeline is original_kp
    assert reasoner_node_module._service.reason == original_reason
    assert KnowledgePipeline.run is original_pipeline_run


def test_prepare_state_seeds_harness_wiring_only() -> None:
    """AR-22 wiring: asked_question_ids + candidate_identity_id for eval/KP path."""
    state = prepare_written_state_for_reasoner_profiling()
    assert state.asked_question_ids == [state.questions[0].id]
    assert state.candidate_identity_id == "epic09-c5-candidate"
    assert state.questions[0].type.value == "written"
