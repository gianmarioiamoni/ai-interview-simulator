# services/interview_reasoner/pattern_detection/detectors/default_registry.py
"""Factory function that builds the default PatternDetectorRegistry
with the three M2-3 detectors registered in dependency order."""

from services.interview_reasoner.pattern_detection.detectors.coverage_detector import CoverageDetector
from services.interview_reasoner.pattern_detection.detectors.consistency_detector import ConsistencyDetector
from services.interview_reasoner.pattern_detection.detectors.trend_detector import TrendDetector
from services.interview_reasoner.pattern_detection.registry import PatternDetectorRegistry


def build_default_registry() -> PatternDetectorRegistry:
    """Return a PatternDetectorRegistry pre-loaded with all M2-3 detectors.

    Registration order respects dependency constraints:
      CoverageDetector (priority=10, no deps)
      → ConsistencyDetector (priority=20, depends on CoverageDetector)
      → TrendDetector (priority=30, depends on ConsistencyDetector)
    """
    registry = PatternDetectorRegistry()
    registry.register(CoverageDetector())
    registry.register(ConsistencyDetector())
    registry.register(TrendDetector())
    return registry
