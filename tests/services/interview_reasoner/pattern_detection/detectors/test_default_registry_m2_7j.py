# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry_m2_7j.py
"""Registry integration tests specific to M2-7J (AdaptabilityDetector)."""

from services.interview_reasoner.pattern_detection.detectors.adaptability_detector import (
    AdaptabilityDetector,
)
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry


def test_adaptability_detector_registered():
    reg = build_default_registry()
    assert reg.by_name("AdaptabilityDetector") is not None


def test_adaptability_priority_is_120():
    d = build_default_registry().by_name("AdaptabilityDetector")
    assert d is not None
    assert d.metadata.priority == 120


def test_adaptability_depends_on_collaboration():
    d = build_default_registry().by_name("AdaptabilityDetector")
    assert d is not None
    assert "CollaborationDetector" in d.metadata.dependencies


def test_adaptability_is_correct_type():
    d = build_default_registry().by_name("AdaptabilityDetector")
    assert isinstance(d, AdaptabilityDetector)


def test_adaptability_after_collaboration():
    names = [d.metadata.name for d in build_default_registry().ordered()]
    assert names.index("AdaptabilityDetector") > names.index("CollaborationDetector")


def test_adaptability_version_is_1_0_0():
    d = build_default_registry().by_name("AdaptabilityDetector")
    assert d is not None
    assert d.metadata.version == "1.0.0"


def test_twelve_detectors_present():
    names = {d.metadata.name for d in build_default_registry().ordered()}
    expected = {
        "EvaluationSignalDetector",
        "CoverageDetector",
        "ConsistencyDetector",
        "TrendDetector",
        "ReasoningDepthDetector",
        "EngineeringJudgmentDetector",
        "CommunicationDetector",
        "BehavioralPatternDetector",
        "ConsistencyAcrossInterviewDetector",
        "ConfidenceCalibrationDetector",
        "LeadershipDetector",
        "CollaborationDetector",
        "AdaptabilityDetector",
    }
    assert expected.issubset(names)


def test_registry_order_strictly_by_priority():
    priorities = [d.metadata.priority for d in build_default_registry().ordered()]
    assert priorities == sorted(priorities)


def test_adaptability_is_last_registered():
    ordered = list(build_default_registry().ordered())
    names = [d.metadata.name for d in ordered]
    assert names[-1] == "AdaptabilityDetector"
