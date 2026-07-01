# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry.py
"""Integration tests for default_registry ordering and dependency resolution."""

import pytest
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry


def test_registry_contains_nine_detectors():
    reg = build_default_registry()
    assert len(reg.all()) == 11  # M2-7I: +CollaborationDetector


def test_registry_ordering():
    reg = build_default_registry()
    names = [d.metadata.name for d in reg.ordered()]
    assert names == [
        "EvaluationSignalDetector",
        "CoverageDetector",
        "ConsistencyDetector",
        "TrendDetector",
        "ReasoningDepthDetector",
        "EngineeringJudgmentDetector",
        "CommunicationDetector",
        "BehavioralPatternDetector",
        "ConsistencyAcrossInterviewDetector",
        "LeadershipDetector",
        "CollaborationDetector",
    ]


def test_all_detectors_enabled():
    reg = build_default_registry()
    assert len(reg.enabled()) == 11


def test_dependency_chain_valid():
    reg = build_default_registry()
    consistency = reg.by_name("ConsistencyDetector")
    assert consistency is not None
    assert "CoverageDetector" in consistency.metadata.dependencies

    trend = reg.by_name("TrendDetector")
    assert trend is not None
    assert "ConsistencyDetector" in trend.metadata.dependencies

    depth = reg.by_name("ReasoningDepthDetector")
    assert depth is not None
    assert "TrendDetector" in depth.metadata.dependencies


def test_fresh_registry_on_each_call():
    reg1 = build_default_registry()
    reg2 = build_default_registry()
    assert reg1 is not reg2


def test_evaluation_signal_detector_exists():
    assert build_default_registry().exists("EvaluationSignalDetector")


def test_coverage_detector_exists():
    assert build_default_registry().exists("CoverageDetector")


def test_consistency_detector_exists():
    assert build_default_registry().exists("ConsistencyDetector")


def test_trend_detector_exists():
    assert build_default_registry().exists("TrendDetector")


def test_reasoning_depth_detector_exists():
    assert build_default_registry().exists("ReasoningDepthDetector")


def test_evaluation_bridge_detector_removed():
    """EvaluationBridgeDetector must no longer be in the default registry."""
    assert not build_default_registry().exists("EvaluationBridgeDetector")
