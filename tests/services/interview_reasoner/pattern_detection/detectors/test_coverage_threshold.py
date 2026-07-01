# tests/services/interview_reasoner/pattern_detection/detectors/test_coverage_threshold.py
"""Tests for CoverageDetector threshold guard (M2-6A, P1a)."""

import uuid
import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.session_metrics import SessionMetrics
from services.interview_reasoner.pattern_detection.detectors.coverage_detector import CoverageDetector


def _inp(questions_answered: int = 0, q_idx: int = 1) -> ReasonerInput:
    metrics = SessionMetrics(questions_answered=questions_answered)
    memory = InterviewMemory(session_metrics=metrics)
    return ReasonerInput(
        session_id="s", question_index=q_idx,
        interview_memory=memory, current_question_area="area"
    )


def test_silent_at_zero_questions():
    result = CoverageDetector().detect(_inp(questions_answered=0))
    assert result.generated_signals == []
    assert result.matches == []
    assert result.warnings == []


def test_silent_at_one_question():
    result = CoverageDetector().detect(_inp(questions_answered=1))
    assert result.generated_signals == []


def test_active_at_threshold_default_2():
    result = CoverageDetector().detect(_inp(questions_answered=2))
    assert len(result.generated_signals) > 0


def test_active_above_threshold():
    result = CoverageDetector().detect(_inp(questions_answered=5))
    assert len(result.generated_signals) > 0


def test_threshold_configurable(monkeypatch):
    from services.interview_reasoner.pattern_detection.detectors import coverage_detector as mod
    mock_settings = type("S", (), {"reasoner_coverage_min_questions": 0})()
    monkeypatch.setattr(mod, "_settings", mock_settings)
    # With threshold=0, even 0 questions_answered should emit signals
    result = CoverageDetector().detect(_inp(questions_answered=0))
    assert len(result.generated_signals) > 0


def test_idempotency_no_duplicate_on_second_cycle():
    # Seed 2 signals per dimension → all dims above _LOW_COVERAGE_THRESHOLD (2).
    # CoverageDetector should emit 0 signals on this cycle.
    metrics = SessionMetrics(questions_answered=2)
    sigs_from_cycle1 = []
    for dim in ProfileDimension:
        for i in range(2):
            sigs_from_cycle1.append(EvidenceSignal(
                id=str(uuid.uuid4()), question_index=i, question_area="a",
                dimension=dim, polarity=EvidencePolarity.NEGATIVE,
                signal_type=EvidenceType.SHALLOW_ANSWER, strength=0.6,
                source=EvidenceSource.PATTERN_DETECTOR, timestamp_question_index=i,
            ))
    store = EvidenceStore(signals=sigs_from_cycle1)
    memory = InterviewMemory(evidence_store=store, session_metrics=metrics)
    inp = ReasonerInput(session_id="s", question_index=2, interview_memory=memory, current_question_area="a")
    result = CoverageDetector().detect(inp)
    assert result.generated_signals == []
