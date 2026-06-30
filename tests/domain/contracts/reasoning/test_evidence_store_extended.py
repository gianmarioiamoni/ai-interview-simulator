# tests/domain/contracts/reasoning/test_evidence_store_extended.py
"""Tests for EvidenceStore extensions: append, by_question, recent, statistics."""

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.evidence_store import EvidenceStore, EvidenceStoreStatistics, _MAX_SIGNALS
from domain.contracts.reasoning.profile_dimension import ProfileDimension


def _sig(
    idx: int = 0,
    polarity: EvidencePolarity = EvidencePolarity.NEGATIVE,
    signal_type: EvidenceType = EvidenceType.SHALLOW_ANSWER,
    dimension: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    strength: float = 0.7,
    ts: int | None = None,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=f"id-{idx}-{polarity.value}-{signal_type.value}",
        question_index=idx,
        question_area="area",
        dimension=dimension,
        polarity=polarity,
        signal_type=signal_type,
        strength=strength,
        source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=ts if ts is not None else idx,
    )


# --- append ---

def test_append_returns_new_store():
    store = EvidenceStore()
    s = _sig()
    new_store = store.append(s)
    assert len(new_store.signals) == 1
    assert len(store.signals) == 0  # original unchanged


def test_append_preserves_existing():
    s1, s2 = _sig(0), _sig(1)
    store = EvidenceStore(signals=[s1])
    new_store = store.append(s2)
    assert len(new_store.signals) == 2
    assert new_store.signals[0] == s1
    assert new_store.signals[1] == s2


def test_append_at_capacity_raises():
    signals = [_sig(i) for i in range(_MAX_SIGNALS)]
    store = EvidenceStore(signals=signals)
    with pytest.raises(ValueError, match="capacity"):
        store.append(_sig(_MAX_SIGNALS))


def test_append_original_immutable():
    s = _sig()
    store = EvidenceStore()
    store.append(s)
    assert len(store.signals) == 0


# --- by_question ---

def test_by_question_returns_matching():
    s0, s1a, s1b = _sig(0), _sig(1), _sig(1, polarity=EvidencePolarity.POSITIVE, signal_type=EvidenceType.REPEATED_STRENGTH)
    store = EvidenceStore(signals=[s0, s1a, s1b])
    result = store.by_question(1)
    assert len(result) == 2
    assert s1a in result
    assert s1b in result


def test_by_question_no_match():
    store = EvidenceStore(signals=[_sig(0)])
    assert store.by_question(99) == []


def test_by_question_empty_store():
    assert EvidenceStore().by_question(0) == []


# --- recent ---

def test_recent_returns_n_most_recent():
    signals = [_sig(i, ts=i) for i in range(5)]
    store = EvidenceStore(signals=signals)
    result = store.recent(3)
    assert len(result) == 3
    assert result[0].timestamp_question_index == 4
    assert result[1].timestamp_question_index == 3
    assert result[2].timestamp_question_index == 2


def test_recent_n_larger_than_total():
    store = EvidenceStore(signals=[_sig(0), _sig(1)])
    assert len(store.recent(100)) == 2


def test_recent_zero():
    store = EvidenceStore(signals=[_sig(0)])
    assert store.recent(0) == []


def test_recent_negative():
    store = EvidenceStore(signals=[_sig(0)])
    assert store.recent(-1) == []


def test_recent_empty_store():
    assert EvidenceStore().recent(5) == []


def test_recent_preserves_original():
    store = EvidenceStore(signals=[_sig(0)])
    store.recent(1)
    assert len(store.signals) == 1


# --- statistics ---

def test_statistics_empty_store():
    stats = EvidenceStore().statistics()
    assert stats.total == 0
    assert stats.positive == 0
    assert stats.negative == 0
    assert stats.mean_strength == 0.0
    assert stats.per_dimension == {}
    assert stats.per_type == {}


def test_statistics_counts():
    pos = _sig(0, polarity=EvidencePolarity.POSITIVE, signal_type=EvidenceType.REPEATED_STRENGTH, strength=0.8)
    neg = _sig(1, polarity=EvidencePolarity.NEGATIVE, signal_type=EvidenceType.SHALLOW_ANSWER, strength=0.6)
    store = EvidenceStore(signals=[pos, neg])
    stats = store.statistics()
    assert stats.total == 2
    assert stats.positive == 1
    assert stats.negative == 1


def test_statistics_mean_strength():
    s1 = _sig(0, strength=0.8)
    s2 = _sig(1, strength=0.4)
    store = EvidenceStore(signals=[s1, s2])
    stats = store.statistics()
    assert abs(stats.mean_strength - 0.6) < 0.001


def test_statistics_per_dimension():
    s1 = _sig(0, dimension=ProfileDimension.TECHNICAL_DEPTH)
    s2 = _sig(1, dimension=ProfileDimension.COMMUNICATION)
    s3 = _sig(2, dimension=ProfileDimension.TECHNICAL_DEPTH)
    store = EvidenceStore(signals=[s1, s2, s3])
    stats = store.statistics()
    assert stats.per_dimension["technical_depth"] == 2
    assert stats.per_dimension["communication"] == 1


def test_statistics_per_type():
    s1 = _sig(0, signal_type=EvidenceType.SHALLOW_ANSWER)
    s2 = _sig(1, signal_type=EvidenceType.SHALLOW_ANSWER)
    s3 = _sig(2, signal_type=EvidenceType.KNOWLEDGE_GAP)
    store = EvidenceStore(signals=[s1, s2, s3])
    stats = store.statistics()
    assert stats.per_type["shallow_answer"] == 2
    assert stats.per_type["knowledge_gap"] == 1


def test_statistics_mean_strength_by_polarity():
    pos = _sig(0, polarity=EvidencePolarity.POSITIVE, signal_type=EvidenceType.REPEATED_STRENGTH, strength=1.0)
    neg = _sig(1, polarity=EvidencePolarity.NEGATIVE, signal_type=EvidenceType.KNOWLEDGE_GAP, strength=0.5)
    store = EvidenceStore(signals=[pos, neg])
    stats = store.statistics()
    assert stats.mean_strength_positive == 1.0
    assert stats.mean_strength_negative == 0.5


def test_statistics_is_frozen():
    stats = EvidenceStore().statistics()
    assert isinstance(stats, EvidenceStoreStatistics)
    with pytest.raises((ValidationError, TypeError)):
        stats.total = 99
