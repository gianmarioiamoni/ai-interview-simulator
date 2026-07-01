# tests/services/interview_reasoner/pattern_detection/detectors/collaboration/test_signal_factory.py
"""Tests for CollaborationSignalFactory."""

from __future__ import annotations

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.pattern_detection.detectors.collaboration.analyzer import (
    CollaborationStats,
)
from services.interview_reasoner.pattern_detection.detectors.collaboration.scorer import (
    CollaborationVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.collaboration.signal_factory import (
    CollaborationSignalFactory,
)

FACTORY = CollaborationSignalFactory()


def _stats(
    team: int = 0,
    sharing: int = 0,
    feedback: int = 0,
    total: int = 5,
) -> CollaborationStats:
    return CollaborationStats(
        team_orientation_count=team,
        knowledge_sharing_count=sharing,
        feedback_acceptance_count=feedback,
        total_behavioral_signals=total,
    )


# ---- NEUTRAL → None ----------------------------------------------------------

def test_neutral_returns_none():
    result = FACTORY.create(CollaborationVerdict.NEUTRAL, _stats(), 1, "area")
    assert result is None


# ---- STRONG_COLLABORATOR -----------------------------------------------------

def test_strong_collaborator_signal_type():
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    sig = FACTORY.create(CollaborationVerdict.STRONG_COLLABORATOR, stats, 2, "collab")
    assert sig is not None
    assert sig.signal_type == EvidenceType.COLLABORATION_STRONG


def test_strong_collaborator_positive_polarity():
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    sig = FACTORY.create(CollaborationVerdict.STRONG_COLLABORATOR, stats, 2, "collab")
    assert sig.polarity == EvidencePolarity.POSITIVE


def test_strong_collaborator_dimension_communication():
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    sig = FACTORY.create(CollaborationVerdict.STRONG_COLLABORATOR, stats, 2, "collab")
    assert sig.dimension == ProfileDimension.COMMUNICATION


def test_strong_collaborator_strength_clamped_to_one():
    # ratio = 6/8 = 0.75, strength = min(1.0, 0.75 * 1.6) = 1.0
    stats = _stats(team=3, sharing=2, feedback=1, total=8)
    sig = FACTORY.create(CollaborationVerdict.STRONG_COLLABORATOR, stats, 1, "area")
    assert sig.strength <= 1.0


def test_strong_collaborator_strength_formula():
    # ratio = 4/10 = 0.4, strength = min(1.0, 0.4 * 1.6) = 0.64
    stats = _stats(team=2, sharing=1, feedback=1, total=10)
    sig = FACTORY.create(CollaborationVerdict.STRONG_COLLABORATOR, stats, 1, "area")
    assert sig.strength == pytest.approx(0.64, abs=0.01)


# ---- EFFECTIVE_COLLABORATOR --------------------------------------------------

def test_effective_collaborator_signal_type():
    stats = _stats(team=2, total=5)
    sig = FACTORY.create(CollaborationVerdict.EFFECTIVE_COLLABORATOR, stats, 3, "area")
    assert sig.signal_type == EvidenceType.COLLABORATION_EFFECTIVE


def test_effective_collaborator_positive_polarity():
    stats = _stats(team=2, total=5)
    sig = FACTORY.create(CollaborationVerdict.EFFECTIVE_COLLABORATOR, stats, 3, "area")
    assert sig.polarity == EvidencePolarity.POSITIVE


def test_effective_collaborator_strength_equals_ratio():
    stats = _stats(team=2, total=5)
    sig = FACTORY.create(CollaborationVerdict.EFFECTIVE_COLLABORATOR, stats, 3, "area")
    assert sig.strength == pytest.approx(stats.collaboration_ratio, abs=0.01)


# ---- COLLABORATION_DEFICIT ---------------------------------------------------

def test_collaboration_deficit_signal_type():
    stats = CollaborationStats(total_behavioral_signals=5)
    sig = FACTORY.create(CollaborationVerdict.COLLABORATION_DEFICIT, stats, 4, "area")
    assert sig.signal_type == EvidenceType.COLLABORATION_DEFICIT


def test_collaboration_deficit_negative_polarity():
    stats = CollaborationStats(total_behavioral_signals=5)
    sig = FACTORY.create(CollaborationVerdict.COLLABORATION_DEFICIT, stats, 4, "area")
    assert sig.polarity == EvidencePolarity.NEGATIVE


def test_collaboration_deficit_fixed_strength():
    stats = CollaborationStats(total_behavioral_signals=5)
    sig = FACTORY.create(CollaborationVerdict.COLLABORATION_DEFICIT, stats, 4, "area")
    assert sig.strength == pytest.approx(0.45)


# ---- source and metadata -----------------------------------------------------

def test_signal_source_is_pattern_detector():
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    sig = FACTORY.create(CollaborationVerdict.STRONG_COLLABORATOR, stats, 2, "area")
    assert sig.source == EvidenceSource.PATTERN_DETECTOR


def test_signal_ids_are_unique():
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    sig1 = FACTORY.create(CollaborationVerdict.STRONG_COLLABORATOR, stats, 2, "area")
    sig2 = FACTORY.create(CollaborationVerdict.STRONG_COLLABORATOR, stats, 2, "area")
    assert sig1.id != sig2.id


def test_signal_question_index_correct():
    stats = _stats(team=2, total=5)
    sig = FACTORY.create(CollaborationVerdict.EFFECTIVE_COLLABORATOR, stats, 7, "area")
    assert sig.question_index == 7
    assert sig.timestamp_question_index == 7


def test_signal_area_correct():
    stats = _stats(team=2, total=5)
    sig = FACTORY.create(CollaborationVerdict.EFFECTIVE_COLLABORATOR, stats, 3, "collab_area")
    assert sig.question_area == "collab_area"


def test_never_generates_leadership_signals():
    stats = _stats(team=3, sharing=2, feedback=1, total=10)
    for verdict in [
        CollaborationVerdict.STRONG_COLLABORATOR,
        CollaborationVerdict.EFFECTIVE_COLLABORATOR,
        CollaborationVerdict.COLLABORATION_DEFICIT,
    ]:
        sig = FACTORY.create(verdict, stats, 1, "area")
        if sig is not None:
            assert sig.signal_type not in (
                EvidenceType.LEADERSHIP_STRONG,
                EvidenceType.LEADERSHIP_EMERGING,
                EvidenceType.LEADERSHIP_ABSENT,
            )
