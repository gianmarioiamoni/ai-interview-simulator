# tests/services/interview_reasoner/pattern_detection/detectors/test_default_registry_m2_7b.py
"""Registry integration tests specific to M2-7B additions."""

from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry
from services.interview_reasoner.pattern_detection.detectors.evaluation_signal_detector import (
    EvaluationSignalDetector,
)
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth_detector import (
    ReasoningDepthDetector,
)


def test_evaluation_signal_detector_priority():
    reg = build_default_registry()
    d = reg.by_name("EvaluationSignalDetector")
    assert d is not None
    assert d.metadata.priority == 5


def test_reasoning_depth_detector_priority():
    reg = build_default_registry()
    d = reg.by_name("ReasoningDepthDetector")
    assert d is not None
    assert d.metadata.priority == 40


def test_reasoning_depth_after_trend():
    reg = build_default_registry()
    names = [d.metadata.name for d in reg.ordered()]
    trend_idx = names.index("TrendDetector")
    depth_idx = names.index("ReasoningDepthDetector")
    assert depth_idx > trend_idx


def test_evaluation_signal_before_coverage():
    reg = build_default_registry()
    names = [d.metadata.name for d in reg.ordered()]
    eval_idx = names.index("EvaluationSignalDetector")
    cov_idx = names.index("CoverageDetector")
    assert eval_idx < cov_idx


def test_no_bridge_detector_registered():
    reg = build_default_registry()
    assert not reg.exists("EvaluationBridgeDetector")


def test_detectors_are_correct_types():
    reg = build_default_registry()
    eval_det = reg.by_name("EvaluationSignalDetector")
    depth_det = reg.by_name("ReasoningDepthDetector")
    assert isinstance(eval_det, EvaluationSignalDetector)
    assert isinstance(depth_det, ReasoningDepthDetector)
