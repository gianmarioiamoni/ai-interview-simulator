# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry_m2_6a.py
"""Tests for updated default_registry after M2-7B (EvaluationSignalDetector + ReasoningDepthDetector)."""

from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry


def test_registry_contains_five_detectors():
    reg = build_default_registry()
    assert len(reg.all()) == 5


def test_priority_order():
    reg = build_default_registry()
    names = [d.metadata.name for d in reg.ordered()]
    assert names == [
        "EvaluationSignalDetector",
        "CoverageDetector",
        "ConsistencyDetector",
        "TrendDetector",
        "ReasoningDepthDetector",
    ]


def test_evaluation_signal_is_first():
    reg = build_default_registry()
    assert reg.ordered()[0].metadata.name == "EvaluationSignalDetector"
    assert reg.ordered()[0].metadata.priority == 5


def test_all_detectors_enabled():
    assert len(build_default_registry().enabled()) == 5
