# tests/services/interview_reasoner/pattern_detection/detectors/engineering_judgment/test_signal_factory.py
"""Tests for EngineeringJudgmentSignalFactory."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.analyzer import (
    JudgmentStats,
)
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.scorer import (
    JudgmentVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.signal_factory import (
    EngineeringJudgmentSignalFactory,
)

FACTORY = EngineeringJudgmentSignalFactory()


def _stats(positive: int, negative: int, eval_count: int = 1) -> JudgmentStats:
    return JudgmentStats(
        positive_count=positive,
        negative_count=negative,
        evaluation_signal_count=eval_count,
    )


def test_high_verdict_produces_positive_signal():
    sig = FACTORY.make_signal(JudgmentVerdict.HIGH, _stats(4, 1), 3, "system_design")
    assert sig is not None
    assert sig.signal_type == EvidenceType.ENGINEERING_JUDGMENT_HIGH
    assert sig.polarity == EvidencePolarity.POSITIVE
    assert sig.dimension == ProfileDimension.ENGINEERING_JUDGMENT
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_low_verdict_produces_negative_signal():
    sig = FACTORY.make_signal(JudgmentVerdict.LOW, _stats(1, 4), 2, "architecture")
    assert sig is not None
    assert sig.signal_type == EvidenceType.ENGINEERING_JUDGMENT_LOW
    assert sig.polarity == EvidencePolarity.NEGATIVE
    assert sig.dimension == ProfileDimension.ENGINEERING_JUDGMENT
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_neutral_verdict_returns_none():
    sig = FACTORY.make_signal(JudgmentVerdict.NEUTRAL, _stats(2, 2), 1, "area")
    assert sig is None


def test_high_signal_strength_from_ratio():
    stats = _stats(4, 1)  # ratio = 0.8
    sig = FACTORY.make_signal(JudgmentVerdict.HIGH, stats, 1, "area")
    assert sig is not None
    assert sig.strength == pytest.approx(0.8)


def test_low_signal_strength_inverted():
    stats = _stats(1, 4)  # ratio = 0.2, strength = 1 - 0.2 = 0.8
    sig = FACTORY.make_signal(JudgmentVerdict.LOW, stats, 1, "area")
    assert sig is not None
    assert sig.strength == pytest.approx(0.8)


def test_signal_question_index_set_correctly():
    sig = FACTORY.make_signal(JudgmentVerdict.HIGH, _stats(3, 0), 5, "area")
    assert sig is not None
    assert sig.question_index == 5
    assert sig.timestamp_question_index == 5


def test_signal_area_set_correctly():
    sig = FACTORY.make_signal(JudgmentVerdict.HIGH, _stats(3, 0), 1, "concurrency")
    assert sig is not None
    assert sig.question_area == "concurrency"


def test_signal_id_is_unique():
    stats = _stats(3, 0)
    sig1 = FACTORY.make_signal(JudgmentVerdict.HIGH, stats, 1, "area")
    sig2 = FACTORY.make_signal(JudgmentVerdict.HIGH, stats, 1, "area")
    assert sig1 is not None and sig2 is not None
    assert sig1.id != sig2.id


def test_strength_clamped_to_one():
    stats = _stats(10, 0)  # ratio = 1.0
    sig = FACTORY.make_signal(JudgmentVerdict.HIGH, stats, 1, "area")
    assert sig is not None
    assert sig.strength <= 1.0
