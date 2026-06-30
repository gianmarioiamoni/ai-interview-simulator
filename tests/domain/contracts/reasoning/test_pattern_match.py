# tests/domain/contracts/reasoning/test_pattern_match.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.pattern_match import PatternMatch, PatternDetectionResult
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.profile_dimension import ProfileDimension


def _sig(idx: int = 0) -> EvidenceSignal:
    return EvidenceSignal(
        id=f"id-{idx}",
        question_index=idx,
        question_area="area",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=EvidenceType.SHALLOW_ANSWER,
        strength=0.5,
        source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=idx,
    )


def test_pattern_match_defaults():
    pm = PatternMatch(pattern_type=EvidenceType.SHALLOW_ANSWER)
    assert pm.evidence_signals == []
    assert pm.label == ""


def test_pattern_match_immutable():
    pm = PatternMatch(pattern_type=EvidenceType.SHALLOW_ANSWER)
    with pytest.raises((ValidationError, TypeError)):
        pm.label = "x"


def test_pattern_match_extra_forbidden():
    with pytest.raises(ValidationError):
        PatternMatch(pattern_type=EvidenceType.SHALLOW_ANSWER, unknown="x")


def test_detection_result_all_evidence():
    s1, s2 = _sig(0), _sig(1)
    result = PatternDetectionResult(generated_signals=[s1, s2])
    assert len(result.all_evidence) == 2


def test_detection_result_detected_types():
    m = PatternMatch(pattern_type=EvidenceType.SHALLOW_ANSWER)
    result = PatternDetectionResult(matches=[m])
    assert EvidenceType.SHALLOW_ANSWER in result.detected_types


def test_detection_result_empty():
    result = PatternDetectionResult()
    assert result.all_evidence == []
    assert result.detected_types == []
