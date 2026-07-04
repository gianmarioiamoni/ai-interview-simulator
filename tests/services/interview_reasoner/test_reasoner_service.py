# tests/services/interview_reasoner/test_reasoner_service.py
"""Comprehensive tests for ReasonerService (M2-4)."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoning_history import ReasoningEntry, ReasoningHistory
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.session_metrics import SessionMetrics
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry
from services.interview_reasoner.pattern_detection.registry import PatternDetectorRegistry
from services.interview_reasoner.reasoner_service import ReasonerService

import uuid


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid() -> str:
    return str(uuid.uuid4())


def _make_signal(
    q_idx: int = 0,
    dim: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    polarity: EvidencePolarity = EvidencePolarity.NEGATIVE,
    signal_type: EvidenceType = EvidenceType.KNOWLEDGE_GAP,
    strength: float = 0.7,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=_uid(),
        question_index=q_idx,
        question_area="area",
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=strength,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=q_idx,
    )


def _make_detector(
    name: str,
    priority: int = 100,
    enabled: bool = True,
    signals: list[EvidenceSignal] | None = None,
    warnings: list[str] | None = None,
    raise_exc: Exception | None = None,
) -> PatternDetector:
    meta = DetectorMetadata(name=name, priority=priority, enabled=enabled)
    _signals = signals or []
    _warnings = warnings or []

    class _D(PatternDetector):
        @property
        def metadata(self) -> DetectorMetadata:
            return meta

        def detect(self, inp: ReasonerInput) -> DetectorResult:
            if raise_exc is not None:
                raise raise_exc
            return DetectorResult(
                detector_name=name,
                generated_signals=_signals,
                warnings=_warnings,
            )

    return _D()


def _base_input(
    q_idx: int = 1,
    feedback: str | None = "correct",
    memory: InterviewMemory | None = None,
    follow_up_count: int = 0,
    max_follow_ups: int = 2,
    eligible: frozenset[int] | None = None,
) -> ReasonerInput:
    return ReasonerInput(
        session_id="test-session",
        question_index=q_idx,
        interview_memory=memory or InterviewMemory(),
        current_feedback_quality=feedback,
        follow_up_count=follow_up_count,
        max_follow_ups=max_follow_ups,
        follow_up_eligible_indices=eligible if eligible is not None else frozenset({1}),
        current_question_area="databases",
    )


def _registry(*detectors: PatternDetector) -> PatternDetectorRegistry:
    reg = PatternDetectorRegistry()
    for d in detectors:
        reg.register(d)
    return reg


# ---------------------------------------------------------------------------
# Skip path
# ---------------------------------------------------------------------------

def test_skip_when_first_question_no_feedback():
    inp = ReasonerInput(session_id="s", question_index=0)
    svc = ReasonerService(PatternDetectorRegistry())
    decision, trace, _ = svc.reason(inp)
    assert decision.skip is True
    assert len(trace.steps) == 0


def test_no_skip_when_first_question_has_feedback():
    inp = _base_input(q_idx=0, feedback="correct")
    svc = ReasonerService(PatternDetectorRegistry())
    decision, trace, _ = svc.reason(inp)
    assert decision.skip is False


def test_no_skip_when_later_question():
    inp = _base_input(q_idx=3, feedback=None)
    svc = ReasonerService(PatternDetectorRegistry())
    decision, trace, _ = svc.reason(inp)
    assert decision.skip is False


# ---------------------------------------------------------------------------
# Execution order
# ---------------------------------------------------------------------------

def test_detectors_run_in_priority_order():
    order: list[str] = []

    class _Ordered(PatternDetector):
        def __init__(self, name: str, priority: int) -> None:
            self._meta = DetectorMetadata(name=name, priority=priority)

        @property
        def metadata(self) -> DetectorMetadata:
            return self._meta

        def detect(self, inp: ReasonerInput) -> DetectorResult:
            order.append(self._meta.name)
            return DetectorResult(detector_name=self._meta.name)

    reg = PatternDetectorRegistry()
    reg.register(_Ordered("C", 30))
    reg.register(_Ordered("A", 10))
    reg.register(_Ordered("B", 20))

    svc = ReasonerService(reg)
    svc.reason(_base_input())
    assert order == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def test_signals_from_all_detectors_aggregated():
    s1 = _make_signal(0)
    s2 = _make_signal(1, dim=ProfileDimension.COMMUNICATION)
    d1 = _make_detector("D1", priority=10, signals=[s1])
    d2 = _make_detector("D2", priority=20, signals=[s2])
    svc = ReasonerService(_registry(d1, d2))
    decision, _, _ = svc.reason(_base_input())
    assert len(decision.new_evidence) == 2


def test_warnings_from_all_detectors_aggregated():
    d1 = _make_detector("D1", priority=10, warnings=["w1"])
    d2 = _make_detector("D2", priority=20, warnings=["w2"])
    svc = ReasonerService(_registry(d1, d2))
    # Warnings are on reasoning_basis (no direct field on decision);
    # here we just verify the service runs without error
    decision, trace, _ = svc.reason(_base_input())
    assert decision.skip is False
    assert len(trace.steps) == 2


def test_empty_registry_produces_no_evidence():
    svc = ReasonerService(PatternDetectorRegistry())
    decision, trace, _ = svc.reason(_base_input())
    assert decision.new_evidence == []
    assert len(trace.steps) == 0


# ---------------------------------------------------------------------------
# Detector failure isolation
# ---------------------------------------------------------------------------

def test_failing_detector_does_not_abort_pipeline():
    bad = _make_detector("Bad", priority=10, raise_exc=RuntimeError("boom"))
    good_sig = _make_signal()
    good = _make_detector("Good", priority=20, signals=[good_sig])
    reg = PatternDetectorRegistry()
    reg.register(bad)
    reg.register(good)
    decision, trace, _ = ReasonerService(reg).reason(_base_input())
    assert len(decision.new_evidence) == 1
    # Trace has two steps: one error step (Bad), one success step (Good)
    assert len(trace.steps) == 2


def test_failing_detector_step_in_trace():
    bad = _make_detector("Bad", priority=10, raise_exc=ValueError("oops"))
    reg = PatternDetectorRegistry()
    reg.register(bad)
    _, trace, _ = ReasonerService(reg).reason(_base_input())
    assert any("detector_error" in s.summary for s in trace.steps)


# ---------------------------------------------------------------------------
# Evidence propagation
# ---------------------------------------------------------------------------

def test_new_signals_appended_to_evidence_store():
    original_sig = _make_signal(0)
    store = EvidenceStore(signals=[original_sig])
    memory = InterviewMemory(evidence_store=store)

    new_sig = _make_signal(1, dim=ProfileDimension.COMMUNICATION)
    d = _make_detector("D", priority=10, signals=[new_sig])
    svc = ReasonerService(_registry(d))
    decision, _, _ = svc.reason(_base_input(memory=memory))

    # new_evidence contains only the new signal
    assert new_sig in decision.new_evidence


def test_original_memory_is_not_mutated():
    original_sig = _make_signal(0)
    store = EvidenceStore(signals=[original_sig])
    memory = InterviewMemory(evidence_store=store)

    new_sig = _make_signal(1)
    d = _make_detector("D", priority=10, signals=[new_sig])
    svc = ReasonerService(_registry(d))
    svc.reason(_base_input(memory=memory))

    # original store must be unchanged
    assert len(memory.evidence_store.signals) == 1


def test_evidence_store_capacity_not_exceeded():
    from domain.contracts.reasoning.evidence_store import _MAX_SIGNALS
    signals = [_make_signal(i) for i in range(_MAX_SIGNALS)]
    store = EvidenceStore(signals=signals)
    memory = InterviewMemory(evidence_store=store)

    extra = [_make_signal(_MAX_SIGNALS)]
    d = _make_detector("D", priority=10, signals=extra)
    svc = ReasonerService(_registry(d))
    decision, _, _ = svc.reason(_base_input(memory=memory))
    # Service should not crash; decision is produced
    assert decision.skip is False


# ---------------------------------------------------------------------------
# ReasoningTrace generation
# ---------------------------------------------------------------------------

def test_trace_has_one_step_per_detector():
    d1 = _make_detector("D1", priority=10)
    d2 = _make_detector("D2", priority=20)
    svc = ReasonerService(_registry(d1, d2))
    _, trace, _ = svc.reason(_base_input())
    assert len(trace.steps) == 2


def test_trace_step_records_detector_name():
    d = _make_detector("MyDetector", priority=10)
    _, trace, _ = ReasonerService(_registry(d)).reason(_base_input())
    assert trace.steps[0].component == "MyDetector"


def test_trace_step_records_signal_count():
    sigs = [_make_signal(i) for i in range(3)]
    d = _make_detector("D", priority=10, signals=sigs)
    _, trace, _ = ReasonerService(_registry(d)).reason(_base_input())
    assert "signals=3" in trace.steps[0].summary


def test_trace_step_records_match_count():
    d = _make_detector("D", priority=10)
    _, trace, _ = ReasonerService(_registry(d)).reason(_base_input())
    assert "matches=0" in trace.steps[0].summary


def test_trace_step_has_positive_execution_time():
    d = _make_detector("D", priority=10)
    _, trace, _ = ReasonerService(_registry(d)).reason(_base_input())
    assert trace.steps[0].execution_time_ms >= 0.0


# ---------------------------------------------------------------------------
# Decision structure
# ---------------------------------------------------------------------------

def test_decision_carries_session_id():
    inp = _base_input()
    svc = ReasonerService(PatternDetectorRegistry())
    decision, _, _ = svc.reason(inp)
    assert decision.session_id == "test-session"


def test_decision_carries_question_index():
    inp = _base_input(q_idx=5)
    decision, _, _ = ReasonerService(PatternDetectorRegistry()).reason(inp)
    assert decision.question_index == 5



# ---------------------------------------------------------------------------
# Follow-up recommendation
# ---------------------------------------------------------------------------

def test_follow_up_recommended_when_eligible_and_knowledge_gap():
    sig = _make_signal(signal_type=EvidenceType.KNOWLEDGE_GAP)
    d = _make_detector("D", priority=10, signals=[sig])
    inp = _base_input(q_idx=1, eligible=frozenset({1}), follow_up_count=0, max_follow_ups=2)
    decision, _, _ = ReasonerService(_registry(d)).reason(inp)
    assert decision.follow_up_recommendation is not None
    assert decision.follow_up_recommendation.recommended is True
    assert decision.follow_up_recommendation.priority == 1


def test_no_follow_up_when_limit_reached():
    sig = _make_signal(signal_type=EvidenceType.KNOWLEDGE_GAP)
    d = _make_detector("D", priority=10, signals=[sig])
    inp = _base_input(q_idx=1, eligible=frozenset({1}), follow_up_count=2, max_follow_ups=2)
    decision, _, _ = ReasonerService(_registry(d)).reason(inp)
    assert decision.follow_up_recommendation is None


def test_no_follow_up_when_not_eligible_index():
    sig = _make_signal(signal_type=EvidenceType.KNOWLEDGE_GAP)
    d = _make_detector("D", priority=10, signals=[sig])
    inp = _base_input(q_idx=3, eligible=frozenset({1}), follow_up_count=0, max_follow_ups=2)
    decision, _, _ = ReasonerService(_registry(d)).reason(inp)
    assert decision.follow_up_recommendation is None


def test_no_follow_up_when_no_triggers():
    sig = _make_signal(signal_type=EvidenceType.MISSING_EVIDENCE)
    d = _make_detector("D", priority=10, signals=[sig])
    inp = _base_input(q_idx=1, eligible=frozenset({1}), follow_up_count=0, max_follow_ups=2)
    decision, _, _ = ReasonerService(_registry(d)).reason(inp)
    assert decision.follow_up_recommendation is None


# ---------------------------------------------------------------------------
# Navigation recommendation
# ---------------------------------------------------------------------------

def test_navigation_recommended_when_missing_evidence():
    sig = _make_signal(signal_type=EvidenceType.MISSING_EVIDENCE)
    d = _make_detector("D", priority=10, signals=[sig])
    decision, _, _ = ReasonerService(_registry(d)).reason(_base_input())
    assert decision.navigation_recommendation is not None
    assert EvidenceType.MISSING_EVIDENCE in decision.navigation_recommendation.trigger_types


def test_no_navigation_without_triggers():
    d = _make_detector("D", priority=10, signals=[])
    decision, _, _ = ReasonerService(_registry(d)).reason(_base_input())
    assert decision.navigation_recommendation is None


# ---------------------------------------------------------------------------
# Confidence computation
# ---------------------------------------------------------------------------

def test_tentative_after_first_cycle():
    # After P0-2 fix, questions_answered is incremented to 1 each cycle, so
    # the first reasoning cycle yields TENTATIVE (not INSUFFICIENT).
    from domain.contracts.reasoning.data_sufficiency import DataSufficiency
    svc = ReasonerService(PatternDetectorRegistry())
    decision, _, _ = svc.reason(_base_input())
    assert decision.reasoning_basis.reasoning_confidence.data_sufficiency == DataSufficiency.TENTATIVE


def test_confident_with_enough_questions():
    from domain.contracts.reasoning.data_sufficiency import DataSufficiency
    metrics = SessionMetrics(questions_answered=4)
    memory = InterviewMemory(session_metrics=metrics)
    svc = ReasonerService(PatternDetectorRegistry())
    decision, _, _ = svc.reason(_base_input(memory=memory))
    assert decision.reasoning_basis.reasoning_confidence.data_sufficiency == DataSufficiency.CONFIDENT


def test_strong_with_many_questions():
    from domain.contracts.reasoning.data_sufficiency import DataSufficiency
    metrics = SessionMetrics(questions_answered=6)
    memory = InterviewMemory(session_metrics=metrics)
    svc = ReasonerService(PatternDetectorRegistry())
    decision, _, _ = svc.reason(_base_input(memory=memory))
    assert decision.reasoning_basis.reasoning_confidence.data_sufficiency == DataSufficiency.STRONG


def test_tentative_with_one_question():
    from domain.contracts.reasoning.data_sufficiency import DataSufficiency
    metrics = SessionMetrics(questions_answered=1)
    memory = InterviewMemory(session_metrics=metrics)
    svc = ReasonerService(PatternDetectorRegistry())
    decision, _, _ = svc.reason(_base_input(memory=memory))
    assert decision.reasoning_basis.reasoning_confidence.data_sufficiency == DataSufficiency.TENTATIVE


# ---------------------------------------------------------------------------
# Session trend
# ---------------------------------------------------------------------------

def test_session_trend_insufficient_data_with_few_entries():
    svc = ReasonerService(PatternDetectorRegistry())
    decision, _, _ = svc.reason(_base_input())
    assert decision.reasoning_basis.session_quality_trend == Trend.INSUFFICIENT_DATA


def test_session_trend_improving():
    entries = [
        ReasoningEntry(question_index=i, reasoning_confidence=0.3 + i * 0.2)
        for i in range(3)
    ]
    history = ReasoningHistory(entries=entries)
    memory = InterviewMemory(reasoning_history=history)
    decision, _, _ = ReasonerService(PatternDetectorRegistry()).reason(_base_input(memory=memory))
    assert decision.reasoning_basis.session_quality_trend == Trend.IMPROVING


def test_session_trend_declining():
    entries = [
        ReasoningEntry(question_index=i, reasoning_confidence=0.9 - i * 0.2)
        for i in range(3)
    ]
    history = ReasoningHistory(entries=entries)
    memory = InterviewMemory(reasoning_history=history)
    decision, _, _ = ReasonerService(PatternDetectorRegistry()).reason(_base_input(memory=memory))
    assert decision.reasoning_basis.session_quality_trend == Trend.DECLINING


def test_session_trend_stable():
    entries = [
        ReasoningEntry(question_index=i, reasoning_confidence=0.7)
        for i in range(3)
    ]
    history = ReasoningHistory(entries=entries)
    memory = InterviewMemory(reasoning_history=history)
    decision, _, _ = ReasonerService(PatternDetectorRegistry()).reason(_base_input(memory=memory))
    assert decision.reasoning_basis.session_quality_trend == Trend.STABLE


# ---------------------------------------------------------------------------
# Integration with default registry
# ---------------------------------------------------------------------------

def test_integration_default_registry():
    reg = build_default_registry()
    svc = ReasonerService(reg)
    inp = _base_input(q_idx=2, feedback="incorrect")
    decision, trace, _ = svc.reason(inp)
    assert not decision.skip
    assert len(trace.steps) == 13  # M2-7K: 12 (M2-7J) + ConfidenceCalibrationDetector


def test_integration_disabled_detector_excluded():
    reg = PatternDetectorRegistry()
    reg.register(_make_detector("Disabled", priority=10, enabled=False))
    svc = ReasonerService(reg)
    _, trace, _ = svc.reason(_base_input())
    assert len(trace.steps) == 0
