# tests/services/interview_reasoner/pattern_detection/detectors/engineering_judgment/test_analyzer.py
"""Tests for EngineeringJudgmentAnalyzer."""

from __future__ import annotations

import uuid

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.analyzer import (
    EngineeringJudgmentAnalyzer,
    JudgmentStats,
    JUDGMENT_POSITIVE_TYPES,
    JUDGMENT_NEGATIVE_TYPES,
)


def _sig(
    signal_type: EvidenceType,
    polarity: EvidencePolarity,
    dim: ProfileDimension = ProfileDimension.ENGINEERING_JUDGMENT,
    source: EvidenceSource = EvidenceSource.EVALUATION,
    q_idx: int = 1,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=str(uuid.uuid4()),
        question_index=q_idx,
        question_area="system_design",
        dimension=dim,
        polarity=polarity,
        signal_type=signal_type,
        strength=0.7,
        source=source,
        timestamp_question_index=q_idx,
    )


ANALYZER = EngineeringJudgmentAnalyzer()


# ---- empty / no signals -------------------------------------------------------

def test_empty_signals_returns_neutral_stats():
    result = ANALYZER.analyze([])
    assert result.positive_count == 0
    assert result.negative_count == 0
    assert result.evaluation_signal_count == 0
    assert result.judgment_ratio == 0.5


def test_signals_wrong_dimension_ignored():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE, dim=ProfileDimension.TECHNICAL_DEPTH),
        _sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE, dim=ProfileDimension.COMMUNICATION),
    ]
    result = ANALYZER.analyze(sigs)
    assert result.positive_count == 0
    assert result.negative_count == 0
    assert result.evaluation_signal_count == 0


# ---- positive signals -------------------------------------------------------

def test_engineering_judgment_articulated_positive_counted():
    sigs = [_sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE)]
    result = ANALYZER.analyze(sigs)
    assert result.positive_count == 1
    assert result.negative_count == 0


def test_demonstrated_depth_positive_counted():
    sigs = [_sig(EvidenceType.DEMONSTRATED_DEPTH, EvidencePolarity.POSITIVE)]
    result = ANALYZER.analyze(sigs)
    assert result.positive_count == 1


def test_positive_type_with_negative_polarity_not_counted():
    sigs = [_sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.NEGATIVE)]
    result = ANALYZER.analyze(sigs)
    assert result.positive_count == 0
    assert result.negative_count == 0


# ---- negative signals -------------------------------------------------------

def test_shallow_answer_negative_counted():
    sigs = [_sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE)]
    result = ANALYZER.analyze(sigs)
    assert result.negative_count == 1
    assert result.positive_count == 0


def test_reasoning_gap_negative_counted():
    sigs = [_sig(EvidenceType.REASONING_GAP, EvidencePolarity.NEGATIVE)]
    result = ANALYZER.analyze(sigs)
    assert result.negative_count == 1


def test_knowledge_gap_negative_counted():
    sigs = [_sig(EvidenceType.KNOWLEDGE_GAP, EvidencePolarity.NEGATIVE)]
    result = ANALYZER.analyze(sigs)
    assert result.negative_count == 1


def test_negative_type_with_positive_polarity_not_counted():
    sigs = [_sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.POSITIVE)]
    result = ANALYZER.analyze(sigs)
    assert result.negative_count == 0
    assert result.positive_count == 0


# ---- evaluation signal count ------------------------------------------------

def test_evaluation_source_counted():
    sigs = [_sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE, source=EvidenceSource.EVALUATION)]
    result = ANALYZER.analyze(sigs)
    assert result.evaluation_signal_count == 1


def test_pattern_detector_source_not_counted_as_eval():
    sigs = [_sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE, source=EvidenceSource.PATTERN_DETECTOR)]
    result = ANALYZER.analyze(sigs)
    assert result.evaluation_signal_count == 0


def test_multiple_eval_signals_all_counted():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE, source=EvidenceSource.EVALUATION),
        _sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE, source=EvidenceSource.EVALUATION),
    ]
    result = ANALYZER.analyze(sigs)
    assert result.evaluation_signal_count == 2


# ---- judgment_ratio ---------------------------------------------------------

def test_judgment_ratio_neutral_no_signals():
    stats = JudgmentStats()
    assert stats.judgment_ratio == 0.5


def test_judgment_ratio_all_positive():
    stats = JudgmentStats(positive_count=3, negative_count=0)
    assert stats.judgment_ratio == 1.0


def test_judgment_ratio_all_negative():
    stats = JudgmentStats(positive_count=0, negative_count=3)
    assert stats.judgment_ratio == 0.0


def test_judgment_ratio_mixed():
    stats = JudgmentStats(positive_count=2, negative_count=2)
    assert stats.judgment_ratio == 0.5


def test_judgment_ratio_high():
    stats = JudgmentStats(positive_count=4, negative_count=1)
    assert stats.judgment_ratio == pytest.approx(0.8)


# ---- mixed / multi-question -----------------------------------------------

def test_mixed_positive_and_negative():
    sigs = [
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED, EvidencePolarity.POSITIVE),
        _sig(EvidenceType.SHALLOW_ANSWER, EvidencePolarity.NEGATIVE),
    ]
    result = ANALYZER.analyze(sigs)
    assert result.positive_count == 2
    assert result.negative_count == 1
    assert result.judgment_ratio == pytest.approx(2 / 3)


def test_irrelevant_signal_types_on_correct_dim_not_counted():
    sigs = [
        _sig(EvidenceType.COMMUNICATION_GAP, EvidencePolarity.NEGATIVE),
        _sig(EvidenceType.REPEATED_WEAKNESS, EvidencePolarity.NEGATIVE),
    ]
    result = ANALYZER.analyze(sigs)
    assert result.positive_count == 0
    assert result.negative_count == 0
