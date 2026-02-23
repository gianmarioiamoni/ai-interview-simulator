# tests/domain/contracts/test_confidence.py

# confidence 0-1 range

import pytest
from pydantic import ValidationError

from domain.contracts.confidence import Confidence


def test_confidence_valid() -> None:
    confidence = Confidence(base=0.7, final=0.8)
    assert confidence.base == 0.7
    assert confidence.final == 0.8


def test_confidence_invalid_over_1() -> None:
    with pytest.raises(ValidationError):
        Confidence(base=1.2, final=0.8)


def test_confidence_invalid_negative() -> None:
    with pytest.raises(ValidationError):
        Confidence(base=-0.1, final=0.5)
