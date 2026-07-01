# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry_m2_7k.py
"""Registry integration tests specific to M2-7K (ConfidenceCalibrationDetector)."""

from services.interview_reasoner.pattern_detection.detectors.confidence_calibration_detector import (
    ConfidenceCalibrationDetector,
)
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry


def test_confidence_calibration_registered():
    assert build_default_registry().by_name("ConfidenceCalibrationDetector") is not None


def test_confidence_calibration_priority():
    d = build_default_registry().by_name("ConfidenceCalibrationDetector")
    assert d.metadata.priority == 90


def test_confidence_calibration_dependency():
    d = build_default_registry().by_name("ConfidenceCalibrationDetector")
    assert "ConsistencyAcrossInterviewDetector" in d.metadata.dependencies


def test_confidence_calibration_is_correct_type():
    d = build_default_registry().by_name("ConfidenceCalibrationDetector")
    assert isinstance(d, ConfidenceCalibrationDetector)


def test_confidence_calibration_after_consistency_across():
    names = [d.metadata.name for d in build_default_registry().ordered()]
    assert names.index("ConfidenceCalibrationDetector") > names.index("ConsistencyAcrossInterviewDetector")


def test_confidence_calibration_before_leadership():
    names = [d.metadata.name for d in build_default_registry().ordered()]
    assert names.index("ConfidenceCalibrationDetector") < names.index("LeadershipDetector")


def test_confidence_calibration_version():
    d = build_default_registry().by_name("ConfidenceCalibrationDetector")
    assert d.metadata.version == "1.0.0"


def test_thirteen_detectors_present():
    names = {d.metadata.name for d in build_default_registry().ordered()}
    expected = {
        "EvaluationSignalDetector", "CoverageDetector", "ConsistencyDetector",
        "TrendDetector", "ReasoningDepthDetector", "EngineeringJudgmentDetector",
        "CommunicationDetector", "BehavioralPatternDetector",
        "ConsistencyAcrossInterviewDetector", "ConfidenceCalibrationDetector",
        "LeadershipDetector", "CollaborationDetector", "AdaptabilityDetector",
    }
    assert expected.issubset(names)


def test_registry_order_strictly_by_priority():
    priorities = [d.metadata.priority for d in build_default_registry().ordered()]
    assert priorities == sorted(priorities)
