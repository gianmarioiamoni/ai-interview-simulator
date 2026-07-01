# tests/services/interview_reasoner/profile/test_coverage_updater.py
"""Tests for CoverageUpdater (M2-6C)."""

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.profile.coverage_updater import CoverageUpdater

from tests.services.interview_reasoner.profile.conftest import empty_profile, mk_sig

_upd = CoverageUpdater()
TD = ProfileDimension.TECHNICAL_DEPTH


def test_empty_signals_returns_same():
    p = empty_profile()
    assert _upd.update(p, [], 1, prev_last_updated=-1) is p


def test_increments_questions_answered_on_new_question():
    p = empty_profile()
    sig = mk_sig(1, TD, area="databases")
    result = _upd.update(p, [sig], 1, prev_last_updated=-1)
    assert result.questions_answered == 1


def test_does_not_double_count_same_question():
    p = empty_profile()
    sig = mk_sig(1, TD, area="databases")
    p = _upd.update(p, [sig], 1, prev_last_updated=-1)
    # Same question again (prev_last_updated=1, question_index=1 → not new)
    sig2 = mk_sig(1, TD, area="databases")
    result = _upd.update(p, [sig2], 1, prev_last_updated=1)
    assert result.questions_answered == 1


def test_new_area_appended():
    p = empty_profile()
    sig = mk_sig(1, TD, area="system-design")
    result = _upd.update(p, [sig], 1, prev_last_updated=-1)
    assert "system-design" in result.areas_covered


def test_duplicate_area_not_added():
    from domain.contracts.reasoning.candidate_profile import CandidateProfile
    p = CandidateProfile(areas_covered=["api"], questions_answered=1)
    sig = mk_sig(2, TD, area="api")
    result = _upd.update(p, [sig], 2, prev_last_updated=1)
    assert result.areas_covered.count("api") == 1


def test_multiple_areas_in_same_cycle():
    p = empty_profile()
    sigs = [
        mk_sig(1, TD, area="databases"),
        mk_sig(1, ProfileDimension.COMMUNICATION, area="system-design"),
    ]
    result = _upd.update(p, sigs, 1, prev_last_updated=-1)
    assert "databases" in result.areas_covered
    assert "system-design" in result.areas_covered


def test_questions_answered_grows_monotonically():
    p = empty_profile()
    prev = -1
    for q in range(1, 6):
        sig = mk_sig(q, TD, area="api")
        p = _upd.update(p, [sig], q, prev_last_updated=prev)
        prev = q
    assert p.questions_answered == 5


def test_immutability():
    p = empty_profile()
    sig = mk_sig(1, TD, area="api")
    _ = _upd.update(p, [sig], 1, prev_last_updated=-1)
    assert p.questions_answered == 0
    assert p.areas_covered == []
