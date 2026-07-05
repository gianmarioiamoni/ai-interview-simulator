# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry.py
"""Canonical registry tests for build_default_registry().

Verifies the final, stable state of the default detector registry:
- all 13 detectors are registered
- priority ordering is correct and strictly monotonic
- dependency chain is valid
- each detector is the correct type
- each detector has the correct priority value
- no legacy detector (EvaluationBridgeDetector) is present
- registry isolation (fresh instance per call)
"""

from services.interview_reasoner.pattern_detection.detectors.adaptability_detector import (
    AdaptabilityDetector,
)
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern_detector import (
    BehavioralPatternDetector,
)
from services.interview_reasoner.pattern_detection.detectors.collaboration_detector import (
    CollaborationDetector,
)
from services.interview_reasoner.pattern_detection.detectors.communication_detector import (
    CommunicationDetector,
)
from services.interview_reasoner.pattern_detection.detectors.confidence_calibration_detector import (
    ConfidenceCalibrationDetector,
)
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview_detector import (
    ConsistencyAcrossInterviewDetector,
)
from services.interview_reasoner.pattern_detection.detectors.default_registry import (
    build_default_registry,
)
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment_detector import (
    EngineeringJudgmentDetector,
)
from services.interview_reasoner.pattern_detection.detectors.evaluation_signal_detector import (
    EvaluationSignalDetector,
)
from services.interview_reasoner.pattern_detection.detectors.leadership_detector import (
    LeadershipDetector,
)
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth_detector import (
    ReasoningDepthDetector,
)


_EXPECTED_ORDER = [
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
]

_EXPECTED_PRIORITIES = {
    "EvaluationSignalDetector": 5,
    "CoverageDetector": 10,
    "ConsistencyDetector": 20,
    "TrendDetector": 30,
    "ReasoningDepthDetector": 40,
    "EngineeringJudgmentDetector": 50,
    "CommunicationDetector": 60,
    "BehavioralPatternDetector": 70,
    "ConsistencyAcrossInterviewDetector": 80,
    "ConfidenceCalibrationDetector": 90,
    "LeadershipDetector": 100,
    "CollaborationDetector": 110,
    "AdaptabilityDetector": 120,
}


# ---------------------------------------------------------------------------
# Registration and count
# ---------------------------------------------------------------------------

def test_registry_contains_thirteen_detectors():
    assert len(build_default_registry().all()) == 13


def test_all_detectors_enabled():
    assert len(build_default_registry().enabled()) == 13


def test_all_expected_detectors_registered():
    reg = build_default_registry()
    for name in _EXPECTED_ORDER:
        assert reg.exists(name), f"{name} is not registered"


def test_no_legacy_bridge_detector():
    assert not build_default_registry().exists("EvaluationBridgeDetector")


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

def test_registry_ordering_matches_expected():
    names = [d.metadata.name for d in build_default_registry().ordered()]
    assert names == _EXPECTED_ORDER


def test_order_is_strictly_monotonic_by_priority():
    priorities = [d.metadata.priority for d in build_default_registry().ordered()]
    assert priorities == sorted(priorities)


def test_evaluation_signal_is_first():
    ordered = build_default_registry().ordered()
    assert ordered[0].metadata.name == "EvaluationSignalDetector"


def test_adaptability_is_last():
    ordered = build_default_registry().ordered()
    assert ordered[-1].metadata.name == "AdaptabilityDetector"


# ---------------------------------------------------------------------------
# Priority values
# ---------------------------------------------------------------------------

def test_each_detector_has_correct_priority():
    reg = build_default_registry()
    for name, expected_priority in _EXPECTED_PRIORITIES.items():
        detector = reg.by_name(name)
        assert detector is not None, f"{name} not found"
        assert detector.metadata.priority == expected_priority, (
            f"{name}: expected priority {expected_priority}, got {detector.metadata.priority}"
        )


# ---------------------------------------------------------------------------
# Type verification
# ---------------------------------------------------------------------------

def test_detector_types_are_correct():
    reg = build_default_registry()
    type_map = {
        "EvaluationSignalDetector": EvaluationSignalDetector,
        "ReasoningDepthDetector": ReasoningDepthDetector,
        "EngineeringJudgmentDetector": EngineeringJudgmentDetector,
        "CommunicationDetector": CommunicationDetector,
        "BehavioralPatternDetector": BehavioralPatternDetector,
        "ConsistencyAcrossInterviewDetector": ConsistencyAcrossInterviewDetector,
        "ConfidenceCalibrationDetector": ConfidenceCalibrationDetector,
        "LeadershipDetector": LeadershipDetector,
        "CollaborationDetector": CollaborationDetector,
        "AdaptabilityDetector": AdaptabilityDetector,
    }
    for name, expected_type in type_map.items():
        detector = reg.by_name(name)
        assert isinstance(detector, expected_type), (
            f"{name}: expected {expected_type.__name__}, got {type(detector).__name__}"
        )


# ---------------------------------------------------------------------------
# Dependency chain
# ---------------------------------------------------------------------------

def test_dependency_chain_core():
    reg = build_default_registry()
    consistency = reg.by_name("ConsistencyDetector")
    assert "CoverageDetector" in consistency.metadata.dependencies

    trend = reg.by_name("TrendDetector")
    assert "ConsistencyDetector" in trend.metadata.dependencies

    depth = reg.by_name("ReasoningDepthDetector")
    assert "TrendDetector" in depth.metadata.dependencies


def test_dependency_chain_extended():
    reg = build_default_registry()
    assert "ReasoningDepthDetector" in reg.by_name("EngineeringJudgmentDetector").metadata.dependencies
    assert "ConsistencyDetector" in reg.by_name("CommunicationDetector").metadata.dependencies
    assert "CommunicationDetector" in reg.by_name("BehavioralPatternDetector").metadata.dependencies
    assert "BehavioralPatternDetector" in reg.by_name("ConsistencyAcrossInterviewDetector").metadata.dependencies
    assert "ConsistencyAcrossInterviewDetector" in reg.by_name("ConfidenceCalibrationDetector").metadata.dependencies
    assert "ConsistencyAcrossInterviewDetector" in reg.by_name("LeadershipDetector").metadata.dependencies
    assert "LeadershipDetector" in reg.by_name("CollaborationDetector").metadata.dependencies
    assert "CollaborationDetector" in reg.by_name("AdaptabilityDetector").metadata.dependencies


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------

def test_fresh_registry_on_each_call():
    reg1 = build_default_registry()
    reg2 = build_default_registry()
    assert reg1 is not reg2
