# tests/app/graph/nodes/test_reasoner_node.py
"""Tests for ReasonerNode (M2-5)."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.interview_state import InterviewState
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.reasoner_decision import ReasonerDecision
from domain.contracts.reasoning.reasoning_basis import ReasoningBasis
from domain.contracts.reasoning.reasoning_confidence import ReasoningConfidence
from domain.contracts.reasoning.reasoning_trace import ReasoningTrace
from app.graph.nodes.reasoner_node import reasoner_node, _append_reasoning_entry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_state() -> InterviewState:
    return InterviewState.create_empty()


def _make_decision(
    session_id: str = "s",
    q_idx: int = 0,
    skip: bool = False,
    new_evidence: list | None = None,
    follow_up_rec=None,
    navigation_rec=None,
) -> ReasonerDecision:
    return ReasonerDecision(
        session_id=session_id,
        question_index=q_idx,
        skip=skip,
        new_evidence=new_evidence or [],
        follow_up_recommendation=follow_up_rec,
        navigation_recommendation=navigation_rec,
        reasoning_basis=ReasoningBasis(
            reasoning_confidence=ReasoningConfidence()
        ),
    )


# ---------------------------------------------------------------------------
# Node execution — happy path
# ---------------------------------------------------------------------------

def test_node_returns_interview_state():
    state = _empty_state()
    result = reasoner_node(state)
    assert isinstance(result, InterviewState)


def test_node_updates_current_reasoning_decision():
    state = _empty_state()
    result = reasoner_node(state)
    assert result.current_reasoning_decision is not None


def test_node_updates_interview_memory():
    state = _empty_state()
    result = reasoner_node(state)
    assert isinstance(result.interview_memory, InterviewMemory)


def test_node_does_not_mutate_original_state():
    state = _empty_state()
    original_q_idx = state.current_question_index
    reasoner_node(state)
    assert state.current_question_index == original_q_idx
    assert state.current_reasoning_decision is None


def test_node_appends_reasoning_entry():
    state = _empty_state()
    result = reasoner_node(state)
    assert len(result.interview_memory.reasoning_history.entries) == 1


def test_node_reasoning_entry_question_index():
    state = _empty_state().model_copy(update={"current_question_index": 3})
    result = reasoner_node(state)
    entry = result.interview_memory.reasoning_history.entries[-1]
    assert entry.question_index == 3


# ---------------------------------------------------------------------------
# Failure policy
# ---------------------------------------------------------------------------

def test_node_survives_builder_failure():
    state = _empty_state()
    with patch(
        "app.graph.nodes.reasoner_node._builder.build",
        side_effect=RuntimeError("builder boom"),
    ):
        result = reasoner_node(state)
    assert isinstance(result, InterviewState)
    assert result.current_reasoning_decision is None


def test_node_survives_service_failure():
    state = _empty_state()
    with patch(
        "app.graph.nodes.reasoner_node._service.reason",
        side_effect=ValueError("service boom"),
    ):
        result = reasoner_node(state)
    assert result.current_reasoning_decision is None


def test_node_returns_original_state_fields_on_failure():
    state = _empty_state().model_copy(update={"current_question_index": 5})
    with patch(
        "app.graph.nodes.reasoner_node._builder.build",
        side_effect=Exception("any error"),
    ):
        result = reasoner_node(state)
    assert result.current_question_index == 5


def test_node_logs_warning_on_failure(caplog):
    with caplog.at_level(logging.WARNING, logger="app.graph.nodes.reasoner_node"):
        with patch(
            "app.graph.nodes.reasoner_node._builder.build",
            side_effect=RuntimeError("oops"),
        ):
            reasoner_node(_empty_state())
    assert any("reasoner_node failed" in r.message for r in caplog.records)


def test_node_logs_info_on_success(caplog):
    with caplog.at_level(logging.INFO, logger="app.graph.nodes.reasoner_node"):
        reasoner_node(_empty_state())
    assert any("reasoner_node completed" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Logging content (never logs candidate data)
# ---------------------------------------------------------------------------

def test_log_contains_detector_count(caplog):
    with caplog.at_level(logging.INFO, logger="app.graph.nodes.reasoner_node"):
        reasoner_node(_empty_state())
    assert any("detectors=" in r.message for r in caplog.records)


def test_log_contains_signal_count(caplog):
    with caplog.at_level(logging.INFO, logger="app.graph.nodes.reasoner_node"):
        reasoner_node(_empty_state())
    assert any("signals=" in r.message for r in caplog.records)


def test_log_contains_pattern_count(caplog):
    with caplog.at_level(logging.INFO, logger="app.graph.nodes.reasoner_node"):
        reasoner_node(_empty_state())
    assert any("patterns=" in r.message for r in caplog.records)


def test_log_contains_elapsed_ms(caplog):
    with caplog.at_level(logging.INFO, logger="app.graph.nodes.reasoner_node"):
        reasoner_node(_empty_state())
    assert any("elapsed_ms=" in r.message for r in caplog.records)


def test_log_does_not_contain_answer_content(caplog):
    with caplog.at_level(logging.DEBUG, logger="app.graph.nodes.reasoner_node"):
        reasoner_node(_empty_state())
    for record in caplog.records:
        assert "answer_content" not in record.message
        assert "prompt" not in record.message


# ---------------------------------------------------------------------------
# _append_reasoning_entry helper
# ---------------------------------------------------------------------------

def test_append_entry_creates_entry():
    state = _empty_state()
    decision = _make_decision(session_id=state.interview_id)
    memory = _append_reasoning_entry(state, decision, state.interview_memory)
    assert len(memory.reasoning_history.entries) == 1


def test_append_entry_records_correct_q_idx():
    state = _empty_state().model_copy(update={"current_question_index": 7})
    decision = _make_decision(session_id=state.interview_id)
    memory = _append_reasoning_entry(state, decision, state.interview_memory)
    assert memory.reasoning_history.entries[-1].question_index == 7


def test_append_entry_follow_up_flag():
    from domain.contracts.reasoning.follow_up_recommendation import FollowUpRecommendation
    from domain.contracts.reasoning.evidence_type import EvidenceType
    rec = FollowUpRecommendation(recommended=True, trigger_types=[EvidenceType.KNOWLEDGE_GAP])
    state = _empty_state()
    decision = _make_decision(session_id=state.interview_id, follow_up_rec=rec)
    memory = _append_reasoning_entry(state, decision, state.interview_memory)
    assert memory.reasoning_history.entries[-1].follow_up_recommended is True


def test_append_entry_navigation_flag():
    from domain.contracts.reasoning.navigation_recommendation import NavigationRecommendation
    nav = NavigationRecommendation(deepen_current=True)
    state = _empty_state()
    decision = _make_decision(session_id=state.interview_id, navigation_rec=nav)
    memory = _append_reasoning_entry(state, decision, state.interview_memory)
    assert memory.reasoning_history.entries[-1].navigation_recommended is True


def test_append_entry_caps_at_max_entries():
    from domain.contracts.reasoning.reasoning_history import ReasoningHistory, ReasoningEntry, _MAX_ENTRIES
    entries = [ReasoningEntry(question_index=i) for i in range(_MAX_ENTRIES)]
    history = ReasoningHistory(entries=entries)
    memory = InterviewMemory(reasoning_history=history)
    state = _empty_state().model_copy(update={"interview_memory": memory})
    decision = _make_decision(session_id=state.interview_id)
    new_memory = _append_reasoning_entry(state, decision, state.interview_memory)
    assert len(new_memory.reasoning_history.entries) == _MAX_ENTRIES


def test_append_entry_evidence_propagated():
    import uuid
    from domain.contracts.reasoning.evidence_signal import EvidenceSignal
    from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
    from domain.contracts.reasoning.evidence_source import EvidenceSource
    from domain.contracts.reasoning.evidence_type import EvidenceType
    from domain.contracts.reasoning.profile_dimension import ProfileDimension
    sig = EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=0,
        question_area="area",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=EvidenceType.KNOWLEDGE_GAP,
        strength=0.7,
        source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=0,
    )
    state = _empty_state()
    decision = _make_decision(session_id=state.interview_id, new_evidence=[sig])
    memory = _append_reasoning_entry(state, decision, state.interview_memory)
    assert len(memory.evidence_store.signals) == 1


# ---------------------------------------------------------------------------
# session_metrics persistence (ADR-038 regression)
# ---------------------------------------------------------------------------


def test_session_metrics_persisted_from_memory_with_metrics():
    """session_metrics from memory_with_metrics must survive _append_reasoning_entry."""
    from domain.contracts.reasoning.session_metrics import SessionMetrics

    pre_metrics = SessionMetrics(questions_answered=3, total_evidence_signals=7)
    memory_with_metrics = InterviewMemory(session_metrics=pre_metrics)
    state = _empty_state()
    decision = _make_decision(session_id=state.interview_id)

    result = _append_reasoning_entry(state, decision, memory_with_metrics)

    assert result.session_metrics.questions_answered == 3
    assert result.session_metrics.total_evidence_signals == 7


def test_session_metrics_stale_base_not_used():
    """Stale session_metrics on state.interview_memory must NOT overwrite the updated ones."""
    from domain.contracts.reasoning.session_metrics import SessionMetrics

    stale_metrics = SessionMetrics(questions_answered=0)
    state = _empty_state().model_copy(
        update={"interview_memory": InterviewMemory(session_metrics=stale_metrics)}
    )
    updated_metrics = SessionMetrics(questions_answered=5, total_evidence_signals=10)
    memory_with_metrics = InterviewMemory(session_metrics=updated_metrics)
    decision = _make_decision(session_id=state.interview_id)

    result = _append_reasoning_entry(state, decision, memory_with_metrics)

    assert result.session_metrics.questions_answered == 5
    assert result.session_metrics.total_evidence_signals == 10


def test_no_other_interview_memory_field_lost():
    """coverage_state, schema_version, reasoning_history must come from memory_with_metrics."""
    from domain.contracts.reasoning.coverage_state import CoverageState

    cov = CoverageState(covered_areas=["technical_background"])
    memory_with_metrics = InterviewMemory(
        coverage_state=cov,
        schema_version="2.0",
    )
    state = _empty_state()
    decision = _make_decision(session_id=state.interview_id)

    result = _append_reasoning_entry(state, decision, memory_with_metrics)

    assert result.coverage_state == cov
    assert result.schema_version == "2.0"


def test_reasoner_node_session_metrics_survive_cycle():
    """Full reasoner_node integration: session_metrics must not reset after one cycle."""
    state = _empty_state()
    result = reasoner_node(state)
    # session_metrics must not regress to empty default after the node runs
    assert isinstance(result.interview_memory.session_metrics.questions_answered, int)


# ---------------------------------------------------------------------------
# Graph integration
# ---------------------------------------------------------------------------

def test_graph_has_reasoner_node():
    from app.graph.interview_graph import build_interview_graph
    from unittest.mock import MagicMock
    llm = MagicMock()
    graph = build_interview_graph(llm)
    node_names = set(graph.get_graph().nodes)
    assert "reasoner" in node_names


def test_reasoner_between_feedback_and_decision():
    from app.graph.interview_graph import build_interview_graph
    from unittest.mock import MagicMock
    llm = MagicMock()
    graph = build_interview_graph(llm)
    edges = {(e.source, e.target) for e in graph.get_graph().edges}
    assert ("feedback", "reasoner") in edges
    assert ("reasoner", "decision") in edges
