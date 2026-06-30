# tests/services/interview_reasoner/pattern_detection/test_detector_metadata.py

import pytest
from pydantic import ValidationError

from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata


def test_defaults():
    m = DetectorMetadata(name="TestDetector")
    assert m.version == "1.0.0"
    assert m.priority == 100
    assert m.enabled is True
    assert m.dependencies == []


def test_immutable():
    m = DetectorMetadata(name="X")
    with pytest.raises((ValidationError, TypeError)):
        m.enabled = False


def test_extra_forbidden():
    with pytest.raises(ValidationError):
        DetectorMetadata(name="X", unknown="y")


def test_name_empty_rejected():
    with pytest.raises(ValidationError):
        DetectorMetadata(name="")


def test_priority_non_negative():
    with pytest.raises(ValidationError):
        DetectorMetadata(name="X", priority=-1)
    m = DetectorMetadata(name="X", priority=0)
    assert m.priority == 0


def test_with_dependencies():
    m = DetectorMetadata(name="B", dependencies=["A"])
    assert "A" in m.dependencies


def test_disabled():
    m = DetectorMetadata(name="X", enabled=False)
    assert m.enabled is False


def test_serialization_roundtrip():
    m = DetectorMetadata(name="D", priority=5, dependencies=["A", "B"])
    data = m.model_dump()
    m2 = DetectorMetadata(**data)
    assert m == m2
