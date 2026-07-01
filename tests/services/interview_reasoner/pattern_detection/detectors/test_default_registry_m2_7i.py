# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry_m2_7i.py
"""Registry integration tests specific to M2-7I (CollaborationDetector)."""

from services.interview_reasoner.pattern_detection.detectors.collaboration_detector import (
    CollaborationDetector,
)
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry


def test_collaboration_detector_registered():
    reg = build_default_registry()
    assert reg.by_name("CollaborationDetector") is not None


def test_collaboration_priority_is_110():
    d = build_default_registry().by_name("CollaborationDetector")
    assert d is not None
    assert d.metadata.priority == 110


def test_collaboration_depends_on_leadership():
    d = build_default_registry().by_name("CollaborationDetector")
    assert d is not None
    assert "LeadershipDetector" in d.metadata.dependencies


def test_collaboration_is_correct_type():
    d = build_default_registry().by_name("CollaborationDetector")
    assert isinstance(d, CollaborationDetector)


def test_collaboration_after_leadership():
    names = [d.metadata.name for d in build_default_registry().ordered()]
    assert names.index("CollaborationDetector") > names.index("LeadershipDetector")


def test_collaboration_version_is_1_0_0():
    d = build_default_registry().by_name("CollaborationDetector")
    assert d is not None
    assert d.metadata.version == "1.0.0"


def test_eleven_detectors_present():
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
        "CollaborationDetector",
    }
    assert expected.issubset(names)


def test_registry_order_strictly_by_priority():
    priorities = [d.metadata.priority for d in build_default_registry().ordered()]
    assert priorities == sorted(priorities)


def test_collaboration_is_last_registered():
    ordered = list(build_default_registry().ordered())
    names = [d.metadata.name for d in ordered]
    assert names[-1] == "CollaborationDetector"
