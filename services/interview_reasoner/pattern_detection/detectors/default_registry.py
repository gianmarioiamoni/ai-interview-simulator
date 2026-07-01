# services/interview_reasoner/pattern_detection/detectors/default_registry.py
"""Factory function that builds the default PatternDetectorRegistry
with all M2 detectors registered in dependency order."""

from services.interview_reasoner.pattern_detection.detectors.coverage_detector import CoverageDetector
from services.interview_reasoner.pattern_detection.detectors.consistency_detector import ConsistencyDetector
from services.interview_reasoner.pattern_detection.detectors.evaluation_signal_detector import EvaluationSignalDetector
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth_detector import ReasoningDepthDetector
from services.interview_reasoner.pattern_detection.detectors.trend_detector import TrendDetector
from services.interview_reasoner.pattern_detection.registry import PatternDetectorRegistry


def build_default_registry() -> PatternDetectorRegistry:
    """Return a PatternDetectorRegistry pre-loaded with all M2 detectors.

    Registration order respects dependency constraints:
      EvaluationSignalDetector (priority=5,  no deps)       [M2-7B replaces Bridge]
      → CoverageDetector        (priority=10, no deps)
      → ConsistencyDetector     (priority=20, depends on CoverageDetector)
      → TrendDetector           (priority=30, depends on ConsistencyDetector)
      → ReasoningDepthDetector  (priority=40, depends on TrendDetector)   [M2-7B]
    """
    registry = PatternDetectorRegistry()
    registry.register(EvaluationSignalDetector())
    registry.register(CoverageDetector())
    registry.register(ConsistencyDetector())
    registry.register(TrendDetector())
    registry.register(ReasoningDepthDetector())
    return registry
