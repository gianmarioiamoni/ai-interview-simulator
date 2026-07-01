# services/interview_reasoner/pattern_detection/detectors/reasoning_depth_detector.py
"""ReasoningDepthDetector — first reasoning-quality detector (M2-7B, DET-05).

Detects reasoning maturity based on:
  - Per-dimension depth ratio (deep vs. shallow signals in EvidenceStore)
  - Session-scoped trend derived from ReasoningHistory detected_patterns

priority = 40  (after TrendDetector at 30)
dependencies = ["TrendDetector"]

Signals emitted:
  REASONING_DEPTH_HIGH   — high depth ratio on a dimension
  REASONING_DEPTH_LOW    — low depth ratio on a dimension
  REASONING_IMPROVING    — depth trend is increasing
  REASONING_STAGNATING   — depth trend is low/flat despite multiple signals

Deterministic; O(n); no LLM; no NLP.
"""

from __future__ import annotations

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.analyzer import (
    ReasoningDepthAnalyzer,
)
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.scorer import (
    DepthVerdict,
    ReasoningDepthScorer,
)
from services.interview_reasoner.pattern_detection.detectors.reasoning_depth.signal_factory import (
    ReasoningDepthSignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="ReasoningDepthDetector",
    version="1.0.0",
    priority=40,
    enabled=True,
    dependencies=["TrendDetector"],
)

# EvidenceTypes that relate to reasoning depth — used for PatternMatch labels.
_DEPTH_POSITIVE_TYPES = frozenset({EvidenceType.REASONING_DEPTH_HIGH, EvidenceType.REASONING_IMPROVING})
_DEPTH_NEGATIVE_TYPES = frozenset({EvidenceType.REASONING_DEPTH_LOW, EvidenceType.REASONING_STAGNATING})


class ReasoningDepthDetector(PatternDetector):
    """Detect reasoning maturity via depth ratio and session trend."""

    def __init__(self) -> None:
        self._analyzer = ReasoningDepthAnalyzer()
        self._scorer = ReasoningDepthScorer()
        self._factory = ReasoningDepthSignalFactory()

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        profile = reasoner_input.interview_memory.candidate_profile
        history = reasoner_input.interview_memory.reasoning_history
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        # --- 1. Per-dimension depth analysis ---
        depth_stats = self._analyzer.analyze(store.signals)

        candidates = []
        matches: list[PatternMatch] = []
        warnings: list[str] = []

        for dim, stats in depth_stats.items():
            verdict = self._scorer.score(stats)
            sig = self._factory.make_depth_signal(verdict, stats, q_idx, area)
            if sig is None:
                continue
            candidates.append(sig)
            matches.append(PatternMatch(
                pattern_type=sig.signal_type,
                evidence_signals=[sig],
                label=(
                    f"{dim.value}: depth_ratio={stats.depth_ratio:.2f} "
                    f"({stats.depth_count}d/{stats.shallow_count}s)"
                ),
            ))

        # --- 2. Session-scoped trend via ReasoningHistory ---
        trend_dim, trend_verdicts = self._compute_history_trend(history, q_idx, area, candidates)
        for trend_sig, pattern_type in trend_verdicts:
            matches.append(PatternMatch(
                pattern_type=pattern_type,
                evidence_signals=[trend_sig],
                label=f"session depth trend: {pattern_type.value}",
            ))
            candidates.append(trend_sig)

        # --- 3. Idempotency ---
        new_signals = filter_new_signals(candidates, store)

        if not matches:
            return DetectorResult(detector_name=_METADATA.name, warnings=warnings)

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
            warnings=warnings,
        )

    def _compute_history_trend(
        self,
        history,
        q_idx: int,
        area: str,
        current_candidates,
    ):
        """Compute session-scoped depth trend from ReasoningHistory.

        Builds a per-cycle depth_ratio proxy from detected_patterns in each
        ReasoningEntry, then delegates to ReasoningDepthScorer.trend_verdict.
        """
        if not history.entries:
            return None, []

        # Build per-cycle depth ratio from detected_patterns in history.
        history_ratios: list[float] = []
        for entry in history.entries:
            deep = sum(
                1 for pt in entry.detected_patterns if pt in _DEPTH_POSITIVE_TYPES
            )
            shallow = sum(
                1 for pt in entry.detected_patterns if pt in _DEPTH_NEGATIVE_TYPES
            )
            total = deep + shallow
            ratio = (deep / total) if total > 0 else 0.5
            history_ratios.append(ratio)

        trend = self._scorer.trend_verdict(history_ratios)
        if trend == DepthVerdict.NEUTRAL:
            return None, []

        # Determine dimension for trend signal (use dominant dim from profile if available).
        dim = self._pick_trend_dimension(q_idx, current_candidates)
        sig = self._factory.make_trend_signal(trend, dim, q_idx, area)
        if sig is None:
            return None, []

        pattern_type = (
            EvidenceType.REASONING_IMPROVING
            if trend == DepthVerdict.IMPROVING
            else EvidenceType.REASONING_STAGNATING
        )
        return dim, [(sig, pattern_type)]

    def _pick_trend_dimension(self, q_idx: int, candidates) -> ProfileDimension:
        """Pick a representative dimension for the trend signal.

        Prefer the dimension with the most depth-related candidates; fall back
        to TECHNICAL_DEPTH as the canonical reasoning dimension.
        """
        if not candidates:
            return ProfileDimension.TECHNICAL_DEPTH
        # Count candidates per dimension.
        counts: dict[ProfileDimension, int] = {}
        for sig in candidates:
            counts[sig.dimension] = counts.get(sig.dimension, 0) + 1
        return max(counts, key=lambda d: counts[d])
