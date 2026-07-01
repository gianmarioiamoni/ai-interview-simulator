# tests/services/interview_reasoner/profile/test_dimension_trace_updater.py
"""Tests for DimensionTraceUpdater (M2-6C)."""

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.profile.dimension_trace_updater import DimensionTraceUpdater

from tests.services.interview_reasoner.profile.conftest import (
    empty_profile, mk_sig, mk_trace, profile_with_trace,
)

_upd = DimensionTraceUpdater()
TD = ProfileDimension.TECHNICAL_DEPTH
PS = ProfileDimension.PROBLEM_SOLVING


def test_empty_signals_returns_same_profile():
    p = empty_profile()
    assert _upd.update(p, [], 1) is p


def test_single_negative_signal_creates_trace():
    p = empty_profile()
    sig = mk_sig(1, TD, EvidencePolarity.NEGATIVE, EvidenceType.KNOWLEDGE_GAP, strength=0.8)
    result = _upd.update(p, [sig], 1)
    assert TD in result.dimension_scores
    tr = result.dimension_scores[TD]
    assert tr.evidence_count == 1
    assert tr.last_score == pytest.approx(20.0, abs=1.0)  # 100 - 0.8*100


def test_single_positive_signal_creates_trace():
    p = empty_profile()
    sig = mk_sig(1, TD, EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH, strength=0.8)
    result = _upd.update(p, [sig], 1)
    tr = result.dimension_scores[TD]
    assert tr.last_score == pytest.approx(80.0, abs=1.0)  # 0.8*100


def test_incremental_average_correct():
    # First signal: strength=0.9 positive → score=90
    p = empty_profile()
    sig1 = mk_sig(1, TD, EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH, strength=0.9)
    p = _upd.update(p, [sig1], 1)
    # Second signal: strength=0.5 negative → score=50
    sig2 = mk_sig(2, TD, EvidencePolarity.NEGATIVE, EvidenceType.SHALLOW_ANSWER, strength=0.5)
    p = _upd.update(p, [sig2], 2)
    tr = p.dimension_scores[TD]
    # avg = (90 + 50) / 2 = 70
    assert tr.average_score == pytest.approx(70.0, abs=1.0)
    assert tr.evidence_count == 2


def test_multiple_cycles_accumulate():
    p = empty_profile()
    for i in range(5):
        sig = mk_sig(i, TD, EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH, strength=0.6)
        p = _upd.update(p, [sig], i)
    tr = p.dimension_scores[TD]
    assert tr.evidence_count == 5


def test_only_affected_dimension_changes():
    p = CandidateProfile(dimension_scores={
        TD: mk_trace(avg=60.0, ev=2),
        PS: mk_trace(avg=40.0, ev=2),
    })
    sig = mk_sig(3, TD, EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH, strength=0.8)
    result = _upd.update(p, [sig], 3)
    assert result.dimension_scores[PS] == p.dimension_scores[PS]
    assert result.dimension_scores[TD].evidence_count == 3


def test_excludes_missing_evidence_type():
    p = empty_profile()
    sig = mk_sig(1, TD, EvidencePolarity.NEGATIVE, EvidenceType.MISSING_EVIDENCE, strength=0.6)
    result = _upd.update(p, [sig], 1)
    # MISSING_EVIDENCE is excluded from score computation
    assert TD not in result.dimension_scores


def test_excludes_confidence_drop_type():
    p = empty_profile()
    sig = mk_sig(1, TD, EvidencePolarity.NEGATIVE, EvidenceType.CONFIDENCE_DROP, strength=0.6)
    result = _upd.update(p, [sig], 1)
    assert TD not in result.dimension_scores


def test_last_updated_question_stamped():
    p = empty_profile()
    sig = mk_sig(5, TD, EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH, strength=0.7)
    result = _upd.update(p, [sig], 5)
    assert result.last_updated_at_question_index == 5


def test_immutability_original_unchanged():
    p = empty_profile()
    sig = mk_sig(1, TD, EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH, strength=0.7)
    _ = _upd.update(p, [sig], 1)
    assert p.dimension_scores == {}


def test_confidence_grows_with_evidence():
    p = empty_profile()
    for i in range(5):
        sig = mk_sig(i, TD, EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH, strength=0.7)
        p = _upd.update(p, [sig], i)
    assert p.dimension_scores[TD].confidence > 0.0
    assert p.dimension_scores[TD].confidence <= 1.0
