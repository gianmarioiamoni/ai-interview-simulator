# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry_m2_7h.py
"""Registry integration tests specific to M2-7H (LeadershipDetector)."""

from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview_detector import (
    ConsistencyAcrossInterviewDetector,
)
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry
from services.interview_reasoner.pattern_detection.detectors.leadership_detector import (
    LeadershipDetector,
)


def test_leadership_detector_registered():
    reg = build_default_registry()
    assert reg.by_name("LeadershipDetector") is not None


def test_leadership_priority_is_100():
    d = build_default_registry().by_name("LeadershipDetector")
    assert d is not None
    assert d.metadata.priority == 100


def test_leadership_depends_on_consistency_across_interview():
    d = build_default_registry().by_name("LeadershipDetector")
    assert d is not None
    assert "ConsistencyAcrossInterviewDetector" in d.metadata.dependencies


def test_leadership_is_correct_type():
    d = build_default_registry().by_name("LeadershipDetector")
    assert isinstance(d, LeadershipDetector)


def test_leadership_after_consistency_across_interview():
    names = [d.metadata.name for d in build_default_registry().ordered()]
    assert names.index("LeadershipDetector") > names.index("ConsistencyAcrossInterviewDetector")


def test_leadership_version_is_1_0_0():
    d = build_default_registry().by_name("LeadershipDetector")
    assert d is not None
    assert d.metadata.version == "1.0.0"


def test_ten_detectors_present():
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
        "LeadershipDetector",
    }
    assert expected.issubset(names)


def test_registry_order_strictly_by_priority():
    priorities = [d.metadata.priority for d in build_default_registry().ordered()]
    assert priorities == sorted(priorities)


def test_leadership_is_last_registered():
    ordered = list(build_default_registry().ordered())
    names = [d.metadata.name for d in ordered]
    assert names[-1] == "LeadershipDetector"
