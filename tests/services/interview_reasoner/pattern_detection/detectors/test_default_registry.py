# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry.py
"""Integration tests for default_registry ordering and dependency resolution."""

import pytest
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry


def test_registry_contains_three_detectors():
    reg = build_default_registry()
    assert len(reg.all()) == 4  # Bridge + Coverage + Consistency + Trend (M2-6A)


def test_registry_ordering():
    reg = build_default_registry()
    names = [d.metadata.name for d in reg.ordered()]
    assert names == ["EvaluationBridgeDetector", "CoverageDetector", "ConsistencyDetector", "TrendDetector"]


def test_all_detectors_enabled():
    reg = build_default_registry()
    assert len(reg.enabled()) == 4  # M2-6A: +1 EvaluationBridgeDetector


def test_dependency_chain_valid():
    reg = build_default_registry()
    consistency = reg.by_name("ConsistencyDetector")
    assert consistency is not None
    assert "CoverageDetector" in consistency.metadata.dependencies

    trend = reg.by_name("TrendDetector")
    assert trend is not None
    assert "ConsistencyDetector" in trend.metadata.dependencies


def test_fresh_registry_on_each_call():
    reg1 = build_default_registry()
    reg2 = build_default_registry()
    assert reg1 is not reg2


def test_coverage_detector_exists():
    assert build_default_registry().exists("CoverageDetector")


def test_consistency_detector_exists():
    assert build_default_registry().exists("ConsistencyDetector")


def test_trend_detector_exists():
    assert build_default_registry().exists("TrendDetector")
