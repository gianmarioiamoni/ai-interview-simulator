# services/interview_reasoner/pattern_detection/detectors/default_registry.py
"""Factory function that builds the default PatternDetectorRegistry
with all M2 detectors registered in dependency order."""

from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern_detector import BehavioralPatternDetector
from services.interview_reasoner.pattern_detection.detectors.communication_detector import CommunicationDetector
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview_detector import ConsistencyAcrossInterviewDetector
from services.interview_reasoner.pattern_detection.detectors.coverage_detector import CoverageDetector
from services.interview_reasoner.pattern_detection.detectors.consistency_detector import ConsistencyDetector
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment_detector import EngineeringJudgmentDetector
from services.interview_reasoner.pattern_detection.detectors.evaluation_signal_detector import EvaluationSignalDetector
from services.interview_reasoner.pattern_detection.detectors.adaptability_detector import AdaptabilityDetector
from services.interview_reasoner.pattern_detection.detectors.collaboration_detector import CollaborationDetector
from services.interview_reasoner.pattern_detection.detectors.leadership_detector import LeadershipDetector
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth_detector import ReasoningDepthDetector
from services.interview_reasoner.pattern_detection.detectors.trend_detector import TrendDetector
from services.interview_reasoner.pattern_detection.registry import PatternDetectorRegistry


def build_default_registry() -> PatternDetectorRegistry:
    """Return a PatternDetectorRegistry pre-loaded with all M2 detectors.

    Registration order respects dependency constraints:
      EvaluationSignalDetector         (priority=5,  no deps)                [M2-7B]
      → CoverageDetector               (priority=10, no deps)
      → ConsistencyDetector            (priority=20, depends on Coverage)
      → TrendDetector                  (priority=30, depends on Consistency)
      → ReasoningDepthDetector         (priority=40, depends on Trend)        [M2-7B]
      → EngineeringJudgmentDetector    (priority=50, depends on ReasoningDepth) [M2-7C]
      → CommunicationDetector          (priority=60, depends on Consistency)  [M2-7C]
      → BehavioralPatternDetector      (priority=70, depends on Communication) [M2-7D]
      → ConsistencyAcrossInterviewDetector (priority=80, depends on Behavioral) [M2-7D]
      → LeadershipDetector             (priority=100, depends on ConsistencyAcrossInterview) [M2-7H]
      → CollaborationDetector          (priority=110, depends on Leadership) [M2-7I]
      → AdaptabilityDetector           (priority=120, depends on Collaboration) [M2-7J]
    """
    registry = PatternDetectorRegistry()
    registry.register(EvaluationSignalDetector())
    registry.register(CoverageDetector())
    registry.register(ConsistencyDetector())
    registry.register(TrendDetector())
    registry.register(ReasoningDepthDetector())
    registry.register(EngineeringJudgmentDetector())
    registry.register(CommunicationDetector())
    registry.register(BehavioralPatternDetector())
    registry.register(ConsistencyAcrossInterviewDetector())
    registry.register(LeadershipDetector())
    registry.register(CollaborationDetector())
    registry.register(AdaptabilityDetector())
    return registry
