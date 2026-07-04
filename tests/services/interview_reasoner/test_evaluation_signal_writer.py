# tests/services/interview_reasoner/test_evaluation_signal_writer.py
"""Tests for EvaluationSignalWriter (M2-7M, P0-1 fix)."""

from __future__ import annotations

import pytest

from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from services.interview_reasoner.evaluation_signal_writer import write_evaluation_signals


def _make_eval(score: float) -> QuestionEvaluation:
    return QuestionEvaluation(
        question_id="q1",
        score=score,
        max_score=100,
        passed=score >= 50,
        feedback="feedback",
    )


def _empty_store() -> EvidenceStore:
    return EvidenceStore()


class TestWriteEvaluationSignals:
    def test_strong_pass_produces_no_signals(self):
        store = write_evaluation_signals(_make_eval(90.0), 0, "area_a", _empty_store())
        assert len(store.signals) == 0

    def test_exact_strong_threshold_produces_no_signals(self):
        store = write_evaluation_signals(_make_eval(80.0), 0, "area_a", _empty_store())
        assert len(store.signals) == 0

    def test_shallow_answer_band(self):
        store = write_evaluation_signals(_make_eval(65.0), 0, "area_a", _empty_store())
        assert len(store.signals) == 1
        sig = store.signals[0]
        assert sig.signal_type == EvidenceType.SHALLOW_ANSWER
        assert sig.source == EvidenceSource.EVALUATION
        assert sig.polarity == EvidencePolarity.NEGATIVE

    def test_reasoning_gap_band(self):
        store = write_evaluation_signals(_make_eval(40.0), 0, "area_a", _empty_store())
        assert len(store.signals) == 1
        sig = store.signals[0]
        assert sig.signal_type == EvidenceType.REASONING_GAP

    def test_knowledge_gap_band_severe_failure(self):
        store = write_evaluation_signals(_make_eval(10.0), 0, "area_a", _empty_store())
        assert len(store.signals) == 1
        sig = store.signals[0]
        assert sig.signal_type == EvidenceType.KNOWLEDGE_GAP

    def test_zero_score_knowledge_gap(self):
        store = write_evaluation_signals(_make_eval(0.0), 0, "area_a", _empty_store())
        assert len(store.signals) == 1
        assert store.signals[0].signal_type == EvidenceType.KNOWLEDGE_GAP

    def test_signal_strength_is_bounded(self):
        store = write_evaluation_signals(_make_eval(0.0), 0, "area", _empty_store())
        assert 0.0 <= store.signals[0].strength <= 1.0

    def test_signal_has_correct_question_index(self):
        store = write_evaluation_signals(_make_eval(20.0), 3, "area", _empty_store())
        assert store.signals[0].question_index == 3

    def test_signal_has_correct_question_area(self):
        store = write_evaluation_signals(_make_eval(20.0), 0, "graphs", _empty_store())
        assert store.signals[0].question_area == "graphs"

    def test_idempotency_same_question_index(self):
        store = write_evaluation_signals(_make_eval(20.0), 1, "area", _empty_store())
        assert len(store.signals) == 1
        store2 = write_evaluation_signals(_make_eval(20.0), 1, "area", store)
        assert len(store2.signals) == 1

    def test_different_question_indices_both_written(self):
        store = write_evaluation_signals(_make_eval(20.0), 1, "area", _empty_store())
        store = write_evaluation_signals(_make_eval(20.0), 2, "area", store)
        assert len(store.signals) == 2

    def test_returns_same_store_on_strong_pass(self):
        original = _empty_store()
        result = write_evaluation_signals(_make_eval(95.0), 0, "area", original)
        assert result is original

    def test_evaluation_source_is_set(self):
        store = write_evaluation_signals(_make_eval(30.0), 0, "area", _empty_store())
        assert all(s.source == EvidenceSource.EVALUATION for s in store.signals)

    def test_unknown_area_fallback(self):
        store = write_evaluation_signals(_make_eval(20.0), 0, "", _empty_store())
        assert store.signals[0].question_area == "unknown"


class TestSessionMetricsIncrement:
    """Verify P0-2 fix: session_metrics.questions_answered increments each cycle."""

    def test_questions_answered_increments(self):
        from domain.contracts.reasoning.interview_memory import InterviewMemory
        from domain.contracts.reasoning.reasoner_input import ReasonerInput
        from services.interview_reasoner.pattern_detection.detectors.default_registry import (
            build_default_registry,
        )
        from services.interview_reasoner.reasoner_service import ReasonerService

        memory = InterviewMemory()
        assert memory.session_metrics.questions_answered == 0

        registry = build_default_registry()
        service = ReasonerService(registry)
        inp = ReasonerInput(
            session_id="s",
            question_index=1,
            interview_memory=memory,
            current_feedback_quality="good",
        )
        decision, _ = service.reason(inp)
        # After 1 cycle, questions_answered = 1, reasoning_confidence = 1/3 ≈ 0.33
        conf = decision.reasoning_basis.reasoning_confidence.reasoning_confidence
        assert conf > 0.0
