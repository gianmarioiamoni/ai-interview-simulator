# tests/services/interview_reasoner/profile/test_candidate_profile_engine.py
"""Tests for CandidateProfileEngine (M2-6C)."""

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.profile.candidate_profile_engine import CandidateProfileEngine

from tests.services.interview_reasoner.profile.conftest import (
    empty_profile, mk_sig, mk_trace, profile_with_trace,
)

TD = ProfileDimension.TECHNICAL_DEPTH
PS = ProfileDimension.PROBLEM_SOLVING
PL = EvidencePolarity.POSITIVE
N = EvidencePolarity.NEGATIVE
_engine = CandidateProfileEngine()


def test_empty_signals_returns_same_profile():
    p = empty_profile()
    assert _engine.update(p, [], 1) is p


def test_profile_evolves_on_signal():
    p = empty_profile()
    sig = mk_sig(1, TD, N, EvidenceType.KNOWLEDGE_GAP, strength=0.7)
    result = _engine.update(p, [sig], 1)
    assert TD in result.dimension_scores
    assert result.dimension_scores[TD].evidence_count == 1


def test_questions_answered_increments():
    p = empty_profile()
    sig = mk_sig(1, TD, N, EvidenceType.KNOWLEDGE_GAP)
    result = _engine.update(p, [sig], 1)
    assert result.questions_answered == 1


def test_areas_covered_populated():
    p = empty_profile()
    sig = mk_sig(1, TD, N, EvidenceType.KNOWLEDGE_GAP, area="distributed-systems")
    result = _engine.update(p, [sig], 1)
    assert "distributed-systems" in result.areas_covered


def test_incremental_accumulation():
    p = empty_profile()
    for i in range(1, 6):
        sig = mk_sig(i, TD, N, EvidenceType.KNOWLEDGE_GAP)
        p = _engine.update(p, [sig], i)
    assert p.dimension_scores[TD].evidence_count == 5
    assert p.questions_answered == 5


def test_trend_updates_after_3_signals():
    p = empty_profile()
    # 3 negative signals → low avg
    for i in range(1, 4):
        sig = mk_sig(i, TD, N, EvidenceType.KNOWLEDGE_GAP, strength=0.8)
        p = _engine.update(p, [sig], i)
    # Now strong positive
    sig = mk_sig(4, TD, PL, EvidenceType.REPEATED_STRENGTH, strength=0.95)
    p = _engine.update(p, [sig], 4)
    tr = p.dimension_scores[TD]
    assert tr.trend in (Trend.IMPROVING, Trend.STABLE, Trend.DECLINING)
    assert tr.trend != Trend.INSUFFICIENT_DATA


def test_dominant_dimension_session_scoped():
    p = empty_profile()
    # TD has more evidence
    for i in range(1, 6):
        sig = mk_sig(i, TD, N, EvidenceType.KNOWLEDGE_GAP)
        p = _engine.update(p, [sig], i)
    sig_ps = mk_sig(6, PS, PL, EvidenceType.REPEATED_STRENGTH)
    p = _engine.update(p, [sig_ps], 6)
    dominant = _engine.dominant_dimension(p)
    assert dominant == TD  # TD has more evidence (5 vs 1)


def test_immutability():
    p = empty_profile()
    sig = mk_sig(1, TD, N, EvidenceType.KNOWLEDGE_GAP)
    _ = _engine.update(p, [sig], 1)
    assert p.dimension_scores == {}
    assert p.questions_answered == 0


def test_multiple_dimensions_in_same_cycle():
    p = empty_profile()
    sigs = [
        mk_sig(1, TD, N, EvidenceType.KNOWLEDGE_GAP),
        mk_sig(1, PS, N, EvidenceType.SHALLOW_ANSWER),
    ]
    result = _engine.update(p, sigs, 1)
    assert TD in result.dimension_scores
    assert PS in result.dimension_scores


def test_no_change_on_missing_evidence_only():
    # MISSING_EVIDENCE is excluded from DimensionTrace
    p = empty_profile()
    sig = mk_sig(1, TD, N, EvidenceType.MISSING_EVIDENCE)
    result = _engine.update(p, [sig], 1)
    assert TD not in result.dimension_scores
    # But coverage should still update (area)
    assert "api" in result.areas_covered


def test_engine_under_150_loc():
    import inspect
    from services.interview_reasoner.profile import candidate_profile_engine as mod
    source = inspect.getsource(mod)
    lines = [l for l in source.splitlines() if l.strip()]
    assert len(lines) < 150


def test_profile_never_frozen_across_cycles():
    p = empty_profile()
    snapshots = [p]
    for i in range(1, 6):
        sig = mk_sig(i, TD, N if i <= 2 else PL,
                     EvidenceType.KNOWLEDGE_GAP if i <= 2 else EvidenceType.REPEATED_STRENGTH)
        p = _engine.update(p, [sig], i)
        snapshots.append(p)
    # Each snapshot must differ from the previous (profile always evolves)
    for a, b in zip(snapshots, snapshots[1:]):
        assert a != b
