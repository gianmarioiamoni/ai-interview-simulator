# tests/domain/contracts/reasoning/test_evidence_store.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.profile_dimension import ProfileDimension


def _sig(
    idx: int = 0,
    polarity: EvidencePolarity = EvidencePolarity.NEGATIVE,
    signal_type: EvidenceType = EvidenceType.SHALLOW_ANSWER,
    source: EvidenceSource = EvidenceSource.PATTERN_DETECTOR,
    dimension: ProfileDimension = ProfileDimension.TECHNICAL_DEPTH,
    strength: float = 0.7,
) -> EvidenceSignal:
    return EvidenceSignal(
        id=f"id-{idx}",
        question_index=idx,
        question_area="area",
        dimension=dimension,
        polarity=polarity,
        signal_type=signal_type,
        strength=strength,
        source=source,
        timestamp_question_index=idx,
    )


def test_empty_store():
    store = EvidenceStore()
    assert store.signals == []
    assert store.positive() == []
    assert store.negative() == []


def test_immutable():
    store = EvidenceStore()
    with pytest.raises((ValidationError, TypeError)):
        store.signals = []


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        EvidenceStore(unknown="x")


def test_positive_filter():
    pos = _sig(polarity=EvidencePolarity.POSITIVE, signal_type=EvidenceType.REPEATED_STRENGTH)
    neg = _sig(idx=1)
    store = EvidenceStore(signals=[pos, neg])
    assert store.positive() == [pos]
    assert store.negative() == [neg]


def test_by_dimension():
    s1 = _sig(dimension=ProfileDimension.TECHNICAL_DEPTH)
    s2 = _sig(idx=1, dimension=ProfileDimension.COMMUNICATION)
    store = EvidenceStore(signals=[s1, s2])
    assert store.by_dimension(ProfileDimension.TECHNICAL_DEPTH) == [s1]
    assert store.by_dimension(ProfileDimension.COMMUNICATION) == [s2]


def test_by_type():
    s1 = _sig(signal_type=EvidenceType.SHALLOW_ANSWER)
    s2 = _sig(idx=1, signal_type=EvidenceType.KNOWLEDGE_GAP)
    store = EvidenceStore(signals=[s1, s2])
    assert store.by_type(EvidenceType.SHALLOW_ANSWER) == [s1]


def test_by_source():
    s1 = _sig(source=EvidenceSource.EVALUATION)
    s2 = _sig(idx=1, source=EvidenceSource.FEEDBACK)
    store = EvidenceStore(signals=[s1, s2])
    assert store.by_source(EvidenceSource.EVALUATION) == [s1]


def test_strength_above():
    s_low = _sig(strength=0.3)
    s_high = _sig(idx=1, strength=0.9)
    store = EvidenceStore(signals=[s_low, s_high])
    assert store.strength_above(0.5) == [s_high]
    assert store.strength_above(0.0) == [s_low, s_high]


def test_capacity_limit():
    from domain.contracts.reasoning.evidence_store import _MAX_SIGNALS
    signals = [_sig(idx=i) for i in range(_MAX_SIGNALS)]
    store = EvidenceStore(signals=signals)
    assert len(store.signals) == _MAX_SIGNALS
    with pytest.raises(ValidationError):
        EvidenceStore(signals=signals + [_sig(idx=_MAX_SIGNALS)])
