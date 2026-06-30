# tests/domain/contracts/reasoning/test_dimension_trace.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.trend import Trend


def test_defaults():
    dt = DimensionTrace()
    assert dt.average_score == 0.0
    assert dt.last_score is None
    assert dt.trend == Trend.INSUFFICIENT_DATA
    assert dt.confidence == 0.0
    assert dt.evidence_count == 0
    assert dt.last_updated_question == -1


def test_immutable():
    dt = DimensionTrace()
    with pytest.raises((ValidationError, TypeError)):
        dt.average_score = 50.0


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        DimensionTrace(scores=[1, 2, 3])


def test_average_score_bounds():
    with pytest.raises(ValidationError):
        DimensionTrace(average_score=101.0)
    with pytest.raises(ValidationError):
        DimensionTrace(average_score=-1.0)


def test_confidence_bounds():
    with pytest.raises(ValidationError):
        DimensionTrace(confidence=1.1)
    with pytest.raises(ValidationError):
        DimensionTrace(confidence=-0.01)


def test_valid_populated():
    dt = DimensionTrace(
        average_score=75.0,
        last_score=80.0,
        trend=Trend.IMPROVING,
        confidence=0.6,
        evidence_count=3,
        last_updated_question=4,
    )
    assert dt.trend == Trend.IMPROVING
    assert dt.evidence_count == 3
