# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry_m2_7d.py
"""Registry integration tests specific to M2-7D additions."""

from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern_detector import (
    BehavioralPatternDetector,
)
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview_detector import (
    ConsistencyAcrossInterviewDetector,
)
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry


def test_behavioral_pattern_detector_registered():
    reg = build_default_registry()
    assert reg.by_name("BehavioralPatternDetector") is not None


def test_consistency_across_interview_detector_registered():
    reg = build_default_registry()
    assert reg.by_name("ConsistencyAcrossInterviewDetector") is not None


def test_behavioral_pattern_priority():
    d = build_default_registry().by_name("BehavioralPatternDetector")
    assert d is not None
    assert d.metadata.priority == 70


def test_consistency_across_interview_priority():
    d = build_default_registry().by_name("ConsistencyAcrossInterviewDetector")
    assert d is not None
    assert d.metadata.priority == 80


def test_behavioral_after_communication():
    names = [d.metadata.name for d in build_default_registry().ordered()]
    assert names.index("BehavioralPatternDetector") > names.index("CommunicationDetector")


def test_consistency_across_after_behavioral():
    names = [d.metadata.name for d in build_default_registry().ordered()]
    assert names.index("ConsistencyAcrossInterviewDetector") > names.index("BehavioralPatternDetector")


def test_behavioral_depends_on_communication():
    d = build_default_registry().by_name("BehavioralPatternDetector")
    assert d is not None
    assert "CommunicationDetector" in d.metadata.dependencies


def test_consistency_across_depends_on_behavioral():
    d = build_default_registry().by_name("ConsistencyAcrossInterviewDetector")
    assert d is not None
    assert "BehavioralPatternDetector" in d.metadata.dependencies


def test_behavioral_is_correct_type():
    d = build_default_registry().by_name("BehavioralPatternDetector")
    assert isinstance(d, BehavioralPatternDetector)


def test_consistency_across_is_correct_type():
    d = build_default_registry().by_name("ConsistencyAcrossInterviewDetector")
    assert isinstance(d, ConsistencyAcrossInterviewDetector)


def test_all_nine_detectors_present():
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
    }
    assert expected.issubset(names)


def test_registry_order_strictly_by_priority():
    priorities = [d.metadata.priority for d in build_default_registry().ordered()]
    assert priorities == sorted(priorities)
