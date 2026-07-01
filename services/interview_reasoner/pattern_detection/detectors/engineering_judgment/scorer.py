# services/interview_reasoner/pattern_detection/detectors/engineering_judgment/scorer.py
"""EngineeringJudgmentScorer — threshold verdicts for judgment stats (M2-7C).

Thresholds (TDS §18.2, DET-06):
  HIGH : judgment_ratio ≥ HIGH_THRESHOLD AND total ≥ MIN_EVIDENCE
  LOW  : judgment_ratio ≤ LOW_THRESHOLD  AND total ≥ MIN_EVIDENCE
  NEUTRAL: otherwise (no signal emitted)

Pre-fire guard: evaluation_signal_count ≥ MIN_EVAL_SIGNALS required.
"""

from __future__ import annotations

from enum import Enum

from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.analyzer import (
    JudgmentStats,
)

HIGH_THRESHOLD = 0.60
LOW_THRESHOLD = 0.30
MIN_EVIDENCE = 2        # minimum total judgment signals to emit a verdict
MIN_EVAL_SIGNALS = 1   # guard: at least 1 evaluation-origin signal required


class JudgmentVerdict(str, Enum):
    HIGH = "high"
    LOW = "low"
    NEUTRAL = "neutral"


class EngineeringJudgmentScorer:
    """Converts JudgmentStats into JudgmentVerdict."""

    def score(self, stats: JudgmentStats) -> JudgmentVerdict:
        """Return verdict; NEUTRAL when guard conditions are not met."""
        if stats.evaluation_signal_count < MIN_EVAL_SIGNALS:
            return JudgmentVerdict.NEUTRAL
        if stats.total < MIN_EVIDENCE:
            return JudgmentVerdict.NEUTRAL
        if stats.judgment_ratio >= HIGH_THRESHOLD:
            return JudgmentVerdict.HIGH
        if stats.judgment_ratio <= LOW_THRESHOLD:
            return JudgmentVerdict.LOW
        return JudgmentVerdict.NEUTRAL
