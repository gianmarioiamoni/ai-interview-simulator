# tests/domain/contracts/reasoning/test_evidence_signal.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension


def _make_signal(**overrides) -> EvidenceSignal:
    defaults = dict(
        id="abc-123",
        question_index=1,
        question_area="technical_technical_knowledge",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=EvidenceType.SHALLOW_ANSWER,
        strength=0.8,
        source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=1,
    )
    defaults.update(overrides)
    return EvidenceSignal(**defaults)


def test_valid_signal_created():
    s = _make_signal()
    assert s.id == "abc-123"
    assert s.schema_version == "1.0"
    assert s.polarity == EvidencePolarity.NEGATIVE


def test_immutable():
    s = _make_signal()
    with pytest.raises((ValidationError, TypeError)):
        s.strength = 0.1


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        _make_signal(unknown_field="x")


def test_strength_bounds():
    with pytest.raises(ValidationError):
        _make_signal(strength=1.1)
    with pytest.raises(ValidationError):
        _make_signal(strength=-0.1)


def test_question_index_non_negative():
    with pytest.raises(ValidationError):
        _make_signal(question_index=-1)


def test_id_non_empty():
    with pytest.raises(ValidationError):
        _make_signal(id="")


def test_schema_version_default():
    s = _make_signal()
    assert s.schema_version == "1.0"


def test_derived_source_accepted():
    s = _make_signal(source=EvidenceSource.DERIVED)
    assert s.source == EvidenceSource.DERIVED


def test_positive_signal():
    s = _make_signal(
        polarity=EvidencePolarity.POSITIVE,
        signal_type=EvidenceType.REPEATED_STRENGTH,
    )
    assert s.polarity == EvidencePolarity.POSITIVE


def test_serialization_roundtrip():
    s = _make_signal()
    data = s.model_dump()
    s2 = EvidenceSignal(**data)
    assert s == s2
