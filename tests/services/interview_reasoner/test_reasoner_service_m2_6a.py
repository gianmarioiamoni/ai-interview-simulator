# tests/services/interview_reasoner/test_reasoner_service_m2_6a.py
"""ReasonerService integration tests for M2-6A fixes (P0 + P1)."""

import uuid

import pytest

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.session_metrics import SessionMetrics
from services.interview_reasoner.pattern_detection.detectors.default_registry import build_default_registry
from services.interview_reasoner.reasoner_service import ReasonerService


def _uid() -> str:
    return str(uuid.uuid4())


def _eval_sig(stype: EvidenceType = EvidenceType.KNOWLEDGE_GAP, q: int = 1) -> EvidenceSignal:
    return EvidenceSignal(
        id=_uid(), question_index=q, question_area="api",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=stype, strength=0.7,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=q,
    )


def _inp(
    signals: list[EvidenceSignal] | None = None,
    q_idx: int = 3,
    questions_answered: int = 3,
    follow_up_count: int = 0,
    eligible: frozenset[int] | None = None,
) -> ReasonerInput:
    store = EvidenceStore(signals=signals or [])
    metrics = SessionMetrics(questions_answered=questions_answered)
    memory = InterviewMemory(evidence_store=store, session_metrics=metrics)
    return ReasonerInput(
        session_id="s",
        question_index=q_idx,
        interview_memory=memory,
        current_feedback_quality="incorrect",
        follow_up_count=follow_up_count,
        max_follow_ups=2,
        follow_up_eligible_indices=eligible if eligible is not None else frozenset({q_idx}),
        current_question_area="api",
    )


def _svc() -> ReasonerService:
    return ReasonerService(build_default_registry())


# ---------------------------------------------------------------------------
# P0: follow_up now fires when evaluation evidence exists
# ---------------------------------------------------------------------------

def test_follow_up_fires_on_knowledge_gap():
    inp = _inp(signals=[_eval_sig(EvidenceType.KNOWLEDGE_GAP)])
    d, _, _ = _svc().reason(inp)
    assert d.follow_up_recommendation is not None
    assert d.follow_up_recommendation.recommended is True


def test_follow_up_fires_on_shallow_answer():
    inp = _inp(signals=[_eval_sig(EvidenceType.SHALLOW_ANSWER)])
    d, _, _ = _svc().reason(inp)
    assert d.follow_up_recommendation is not None
    assert d.follow_up_recommendation.recommended is True


def test_follow_up_fires_on_reasoning_gap():
    inp = _inp(signals=[_eval_sig(EvidenceType.REASONING_GAP)])
    d, _, _ = _svc().reason(inp)
    assert d.follow_up_recommendation is not None
    assert d.follow_up_recommendation.recommended is True


def test_follow_up_not_fired_when_limit_reached():
    inp = _inp(signals=[_eval_sig(EvidenceType.KNOWLEDGE_GAP)], follow_up_count=2)
    d, _, _ = _svc().reason(inp)
    assert d.follow_up_recommendation is None


def test_follow_up_not_fired_when_not_eligible():
    inp = _inp(signals=[_eval_sig(EvidenceType.KNOWLEDGE_GAP)], eligible=frozenset({99}))
    d, _, _ = _svc().reason(inp)
    assert d.follow_up_recommendation is None


def test_knowledge_gap_priority_1():
    inp = _inp(signals=[_eval_sig(EvidenceType.KNOWLEDGE_GAP)])
    d, _, _ = _svc().reason(inp)
    assert d.follow_up_recommendation.priority == 1


def test_shallow_answer_priority_2():
    # Provide an EJ eval signal to suppress KNOWLEDGE_GAP on ENGINEERING_JUDGMENT dim;
    # only SHALLOW_ANSWER should drive the follow-up recommendation.
    ej_sig = EvidenceSignal(
        id=_uid(), question_index=1, question_area="api",
        dimension=ProfileDimension.ENGINEERING_JUDGMENT,
        polarity=EvidencePolarity.POSITIVE,
        signal_type=EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED,
        strength=0.7,
        source=EvidenceSource.EVALUATION,
        timestamp_question_index=1,
    )
    inp = _inp(signals=[_eval_sig(EvidenceType.SHALLOW_ANSWER), ej_sig])
    d, _, _ = _svc().reason(inp)
    assert d.follow_up_recommendation.priority == 2


# ---------------------------------------------------------------------------
# P1a: navigation no longer always fires
# ---------------------------------------------------------------------------

def test_navigation_not_fired_at_early_questions():
    # questions_answered=0 → CoverageDetector silent → no MISSING_EVIDENCE trigger
    inp = _inp(signals=[], questions_answered=0, q_idx=0)
    # Override skip guard: need feedback present
    from domain.contracts.reasoning.session_metrics import SessionMetrics
    from domain.contracts.reasoning.interview_memory import InterviewMemory
    from domain.contracts.reasoning.evidence_store import EvidenceStore
    metrics = SessionMetrics(questions_answered=0)
    memory = InterviewMemory(evidence_store=EvidenceStore(), session_metrics=metrics)
    inp2 = ReasonerInput(
        session_id="s", question_index=1,
        interview_memory=memory,
        current_feedback_quality="correct",
        follow_up_eligible_indices=frozenset(),
        current_question_area="api",
    )
    d, _, _ = _svc().reason(inp2)
    assert d.navigation_recommendation is None


def test_navigation_fired_after_threshold_when_dims_uncovered():
    inp = _inp(signals=[], questions_answered=3, q_idx=3)
    d, _, _ = _svc().reason(inp)
    assert d.navigation_recommendation is not None


# ---------------------------------------------------------------------------
# P1b: evidence idempotency across cycles
# ---------------------------------------------------------------------------

def test_no_new_signals_on_second_cycle_same_question():
    # Build a store that already has the derived PATTERN_DETECTOR signal
    eval_sig = _eval_sig(EvidenceType.KNOWLEDGE_GAP, q=3)
    derived = EvidenceSignal(
        id=_uid(), question_index=3, question_area="api",
        dimension=ProfileDimension.TECHNICAL_DEPTH,
        polarity=EvidencePolarity.NEGATIVE,
        signal_type=EvidenceType.KNOWLEDGE_GAP,
        strength=0.7, source=EvidenceSource.PATTERN_DETECTOR,
        timestamp_question_index=3,
    )
    store = EvidenceStore(signals=[eval_sig, derived])
    metrics = SessionMetrics(questions_answered=3)
    memory = InterviewMemory(evidence_store=store, session_metrics=metrics)
    inp = ReasonerInput(
        session_id="s", question_index=3,
        interview_memory=memory,
        current_feedback_quality="incorrect",
        follow_up_count=0, max_follow_ups=2,
        follow_up_eligible_indices=frozenset({3}),
        current_question_area="api",
    )
    d, _, _ = _svc().reason(inp)
    # Bridge should produce 0 new derived signals for TECHNICAL_DEPTH (key already in store)
    bridge_new = [s for s in d.new_evidence
                  if s.signal_type == EvidenceType.KNOWLEDGE_GAP
                  and s.source == EvidenceSource.PATTERN_DETECTOR
                  and s.dimension == ProfileDimension.TECHNICAL_DEPTH]
    assert bridge_new == []
