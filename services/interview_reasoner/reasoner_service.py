# services/interview_reasoner/reasoner_service.py
"""ReasonerService — central orchestrator of the Interview Reasoner (ADR-034, ADR-038).

Responsibilities:
1. Accept a ReasonerInput snapshot.
2. Run all enabled PatternDetectors in priority order.
3. Aggregate DetectorResult → PatternDetectionResult.
4. Propagate new EvidenceSignals to InterviewMemory.evidence_store (immutable update).
5. Update CandidateProfile via CandidateProfileEngine (M2-6C).
6. Build a ReasonerDecision with full ReasoningBasis.
7. Produce an internal ReasoningTrace for debuggability (ADR-041, ADR-047).

No LLM calls. Fully deterministic. O(n) per detector call.
"""

from __future__ import annotations

import time
import uuid

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.data_sufficiency import DataSufficiency
from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.follow_up_recommendation import FollowUpRecommendation
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.navigation_recommendation import NavigationRecommendation
from domain.contracts.reasoning.pattern_match import PatternDetectionResult, PatternMatch
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_decision import ReasonerDecision
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.reasoning_basis import ReasoningBasis
from domain.contracts.reasoning.reasoning_confidence import ReasoningConfidence
from domain.contracts.reasoning.reasoning_trace import ReasoningTrace, ReasoningTraceStep
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.pattern_detection.registry import PatternDetectorRegistry
from services.interview_reasoner.profile.candidate_profile_engine import CandidateProfileEngine

_MIN_RELIABLE_EVIDENCE = 3
_FOLLOW_UP_TRIGGER_TYPES = {
    EvidenceType.KNOWLEDGE_GAP,
    EvidenceType.SHALLOW_ANSWER,
    EvidenceType.REASONING_GAP,
}
_NAVIGATION_TRIGGER_TYPES = {
    EvidenceType.MISSING_EVIDENCE,
    EvidenceType.REPEATED_WEAKNESS,
}


class ReasonerService:
    """Orchestrates the PatternDetectionPipeline and produces ReasonerDecision.

    Stateless between calls — all session state flows through ReasonerInput.
    """

    def __init__(self, registry: PatternDetectorRegistry) -> None:
        self._registry = registry
        self._profile_engine = CandidateProfileEngine()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reason(
        self, reasoner_input: ReasonerInput
    ) -> tuple[ReasonerDecision, ReasoningTrace]:
        """Execute one reasoning cycle.

        Returns:
            (ReasonerDecision, ReasoningTrace) — decision is the primary output;
            trace is an internal audit record (ADR-041).
        """
        if self._should_skip(reasoner_input):
            return self._skip_decision(reasoner_input), ReasoningTrace()

        pipeline_start = time.perf_counter()
        detector_results, trace_steps = self._run_detectors(reasoner_input)
        pipeline_ms = (time.perf_counter() - pipeline_start) * 1000.0

        aggregated = self._aggregate(detector_results, pipeline_ms)
        updated_memory = self._propagate_evidence(
            reasoner_input.interview_memory, aggregated.generated_signals,
            reasoner_input.question_index,
        )
        decision = self._build_decision(reasoner_input, aggregated, updated_memory)
        trace = ReasoningTrace(steps=trace_steps)

        return decision, trace

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _should_skip(self, inp: ReasonerInput) -> bool:
        return inp.question_index == 0 and inp.current_feedback_quality is None

    def _run_detectors(
        self, reasoner_input: ReasonerInput
    ) -> tuple[list[DetectorResult], list[ReasoningTraceStep]]:
        results: list[DetectorResult] = []
        steps: list[ReasoningTraceStep] = []

        for detector in self._registry.enabled():
            t0 = time.perf_counter()
            try:
                result = detector.detect(reasoner_input)
            except Exception as exc:  # isolation: one failing detector must not break cycle
                elapsed = (time.perf_counter() - t0) * 1000.0
                steps.append(ReasoningTraceStep(
                    step_id=str(uuid.uuid4()),
                    component=detector.metadata.name,
                    rule_name="detect",
                    execution_time_ms=elapsed,
                    summary=f"detector_error: {type(exc).__name__}",
                ))
                continue

            elapsed = (time.perf_counter() - t0) * 1000.0
            # Stamp timing on result (immutable-friendly replacement)
            result = DetectorResult(
                detector_name=result.detector_name,
                matches=result.matches,
                generated_signals=result.generated_signals,
                confidence=result.confidence,
                execution_time_ms=elapsed,
                warnings=result.warnings,
            )
            results.append(result)
            steps.append(ReasoningTraceStep(
                step_id=str(uuid.uuid4()),
                component=detector.metadata.name,
                rule_name="detect",
                execution_time_ms=elapsed,
                summary=(
                    f"matches={len(result.matches)} "
                    f"signals={len(result.generated_signals)}"
                ),
            ))

        return results, steps

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def _aggregate(
        self,
        results: list[DetectorResult],
        pipeline_ms: float,
    ) -> PatternDetectionResult:
        all_matches: list[PatternMatch] = []
        all_signals: list[EvidenceSignal] = []
        all_warnings: list[str] = []

        for r in results:
            all_matches.extend(r.matches)
            all_signals.extend(r.generated_signals)
            all_warnings.extend(r.warnings)

        return PatternDetectionResult(
            matches=all_matches,
            generated_signals=all_signals,
            execution_time_ms=pipeline_ms,
            warnings=all_warnings,
        )

    # ------------------------------------------------------------------
    # Evidence propagation (immutable)
    # ------------------------------------------------------------------

    def _propagate_evidence(
        self,
        memory: InterviewMemory,
        new_signals: list[EvidenceSignal],
        question_index: int,
    ) -> InterviewMemory:
        store = memory.evidence_store
        for sig in new_signals:
            try:
                store = store.append(sig)
            except ValueError:
                break  # capacity reached; stop silently (ADR-046)

        # Update CandidateProfile incrementally via CandidateProfileEngine (M2-6C).
        updated_profile = self._profile_engine.update(
            memory.candidate_profile, new_signals, question_index
        )

        return InterviewMemory(
            candidate_profile=updated_profile,
            evidence_store=store,
            coverage_state=memory.coverage_state,
            reasoning_history=memory.reasoning_history,
            session_metrics=memory.session_metrics,
            schema_version=memory.schema_version,
        )

    # ------------------------------------------------------------------
    # Decision construction
    # ------------------------------------------------------------------

    def _build_decision(
        self,
        inp: ReasonerInput,
        aggregated: PatternDetectionResult,
        updated_memory: InterviewMemory,
    ) -> ReasonerDecision:
        detected_types = aggregated.detected_types
        reasoning_confidence = self._compute_confidence(inp, aggregated)

        # Session-scoped dominant dimension from full profile (M2-6C).
        dominant_dim = self._profile_engine.dominant_dimension(
            updated_memory.candidate_profile
        )
        session_trend = self._session_trend(updated_memory)

        follow_up_triggers = [t for t in detected_types if t in _FOLLOW_UP_TRIGGER_TYPES]
        navigation_triggers = [t for t in detected_types if t in _NAVIGATION_TRIGGER_TYPES]

        basis = ReasoningBasis(
            detected_patterns=detected_types,
            dominant_dimension=dominant_dim,
            session_quality_trend=session_trend,
            follow_up_triggers=follow_up_triggers,
            navigation_triggers=navigation_triggers,
            reasoning_confidence=reasoning_confidence,
        )

        follow_up_rec = self._build_follow_up_recommendation(
            inp, follow_up_triggers, dominant_dim
        )
        navigation_rec = self._build_navigation_recommendation(
            inp, navigation_triggers
        )

        return ReasonerDecision(
            session_id=inp.session_id,
            question_index=inp.question_index,
            follow_up_recommendation=follow_up_rec,
            navigation_recommendation=navigation_rec,
            new_evidence=aggregated.generated_signals,
            candidate_profile_snapshot=updated_memory.candidate_profile,
            reasoning_basis=basis,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compute_confidence(
        self,
        inp: ReasonerInput,
        aggregated: PatternDetectionResult,
    ) -> ReasoningConfidence:
        q_answered = inp.interview_memory.session_metrics.questions_answered
        reasoning_conf = min(q_answered / _MIN_RELIABLE_EVIDENCE, 1.0)

        signals = aggregated.generated_signals
        evidence_strength = (
            sum(s.strength for s in signals) / len(signals) if signals else 0.0
        )

        if q_answered == 0:
            sufficiency = DataSufficiency.INSUFFICIENT
        elif q_answered < _MIN_RELIABLE_EVIDENCE:
            sufficiency = DataSufficiency.TENTATIVE
        elif q_answered < 6:
            sufficiency = DataSufficiency.CONFIDENT
        else:
            sufficiency = DataSufficiency.STRONG

        return ReasoningConfidence(
            reasoning_confidence=round(reasoning_conf, 4),
            evidence_strength=round(evidence_strength, 4),
            data_sufficiency=sufficiency,
        )

    @staticmethod
    def _dominant_dimension(
        signals: list[EvidenceSignal],
    ) -> ProfileDimension | None:
        if not signals:
            return None
        counts: dict[ProfileDimension, int] = {}
        for s in signals:
            counts[s.dimension] = counts.get(s.dimension, 0) + 1
        return max(counts, key=lambda d: counts[d])

    @staticmethod
    def _session_trend(memory: InterviewMemory) -> Trend:
        entries = memory.reasoning_history.entries
        if len(entries) < 3:
            return Trend.INSUFFICIENT_DATA
        recent_confs = [e.reasoning_confidence for e in entries[-3:]]
        if recent_confs[-1] > recent_confs[0] + 0.05:
            return Trend.IMPROVING
        if recent_confs[-1] < recent_confs[0] - 0.05:
            return Trend.DECLINING
        return Trend.STABLE

    @staticmethod
    def _build_follow_up_recommendation(
        inp: ReasonerInput,
        follow_up_triggers: list[EvidenceType],
        dominant_dim: ProfileDimension | None,
    ) -> FollowUpRecommendation | None:
        can_follow_up = (
            inp.follow_up_count < inp.max_follow_ups
            and inp.question_index in inp.follow_up_eligible_indices
        )
        if not can_follow_up:
            return None
        if not follow_up_triggers:
            return None
        return FollowUpRecommendation(
            recommended=True,
            target_dimension=dominant_dim,
            trigger_types=follow_up_triggers,
            priority=1 if EvidenceType.KNOWLEDGE_GAP in follow_up_triggers else 2,
        )

    @staticmethod
    def _build_navigation_recommendation(
        inp: ReasonerInput,
        navigation_triggers: list[EvidenceType],
    ) -> NavigationRecommendation | None:
        if not navigation_triggers:
            return None
        return NavigationRecommendation(
            deepen_current=EvidenceType.REPEATED_WEAKNESS in navigation_triggers,
            trigger_types=navigation_triggers,
        )

    # ------------------------------------------------------------------
    # Skip path
    # ------------------------------------------------------------------

    def _skip_decision(self, inp: ReasonerInput) -> ReasonerDecision:
        return ReasonerDecision(
            session_id=inp.session_id,
            question_index=inp.question_index,
            skip=True,
        )
