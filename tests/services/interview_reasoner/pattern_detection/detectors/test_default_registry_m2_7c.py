# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry_m2_7c.py
"""Registry integration tests specific to M2-7C additions."""

from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry
from services.interview_reasoner.pattern_detection.detectors.communication_detector import (
    CommunicationDetector,
)
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment_detector import (
    EngineeringJudgmentDetector,
)


def test_engineering_judgment_detector_registered():
    reg = build_default_registry()
    d = reg.by_name("EngineeringJudgmentDetector")
    assert d is not None


def test_communication_detector_registered():
    reg = build_default_registry()
    d = reg.by_name("CommunicationDetector")
    assert d is not None


def test_engineering_judgment_priority():
    reg = build_default_registry()
    d = reg.by_name("EngineeringJudgmentDetector")
    assert d is not None
    assert d.metadata.priority == 50


def test_communication_priority():
    reg = build_default_registry()
    d = reg.by_name("CommunicationDetector")
    assert d is not None
    assert d.metadata.priority == 60


def test_engineering_judgment_after_reasoning_depth():
    reg = build_default_registry()
    names = [d.metadata.name for d in reg.ordered()]
    depth_idx = names.index("ReasoningDepthDetector")
    judgment_idx = names.index("EngineeringJudgmentDetector")
    assert judgment_idx > depth_idx


def test_communication_after_consistency():
    reg = build_default_registry()
    names = [d.metadata.name for d in reg.ordered()]
    cons_idx = names.index("ConsistencyDetector")
    comm_idx = names.index("CommunicationDetector")
    assert comm_idx > cons_idx


def test_communication_after_engineering_judgment():
    reg = build_default_registry()
    names = [d.metadata.name for d in reg.ordered()]
    judgment_idx = names.index("EngineeringJudgmentDetector")
    comm_idx = names.index("CommunicationDetector")
    assert comm_idx > judgment_idx


def test_engineering_judgment_is_correct_type():
    reg = build_default_registry()
    d = reg.by_name("EngineeringJudgmentDetector")
    assert isinstance(d, EngineeringJudgmentDetector)


def test_communication_is_correct_type():
    reg = build_default_registry()
    d = reg.by_name("CommunicationDetector")
    assert isinstance(d, CommunicationDetector)


def test_engineering_judgment_depends_on_reasoning_depth():
    reg = build_default_registry()
    d = reg.by_name("EngineeringJudgmentDetector")
    assert d is not None
    assert "ReasoningDepthDetector" in d.metadata.dependencies


def test_communication_depends_on_consistency():
    reg = build_default_registry()
    d = reg.by_name("CommunicationDetector")
    assert d is not None
    assert "ConsistencyDetector" in d.metadata.dependencies


def test_all_m2_detectors_count():
    reg = build_default_registry()
    names = {d.metadata.name for d in reg.ordered()}
    expected = {
        "EvaluationSignalDetector",
        "CoverageDetector",
        "ConsistencyDetector",
        "TrendDetector",
        "ReasoningDepthDetector",
        "EngineeringJudgmentDetector",
        "CommunicationDetector",
    }
    assert expected.issubset(names)


def test_registry_order_is_strictly_by_priority():
    reg = build_default_registry()
    priorities = [d.metadata.priority for d in reg.ordered()]
    assert priorities == sorted(priorities)
